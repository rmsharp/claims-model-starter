"""Tests for scripts/check_site_assets.py — the guard added in Session 237.

The regression it exists to catch shipped for four weeks *green*: MkDocs applies
``exclude_docs`` to theme-supplied files as well as to ``docs_dir`` (it re-runs
``set_exclusions()`` after ``add_files_from_theme()``), so ``mkdocs.yml``'s
fail-closed ``/*`` allowlist silently dropped the Material theme's 43-file
``assets/`` tree and ``mkdocs gh-deploy`` still exited 0.

These tests build synthetic site trees rather than invoking MkDocs, so they run
in CI's test job — which installs ``--extra agents --extra ui --extra dev`` and
never the ``docs`` extra. The end-to-end proof (real build, broken config, red;
real build, fixed config, green) is recorded in the session notes; what is
pinned here is the guard's own logic, including the cases a future edit is most
likely to break: root-relative references, directory references, and the
"consistently links nothing" hole that reference-integrity alone cannot see.

Loaded via importlib, matching test_run_pipeline_adapter.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_site_assets.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("_s237_check_site_assets", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def site(tmp_path: Path) -> Path:
    """A minimal intact site: two pages, a stylesheet, a script, a favicon."""
    root = tmp_path / "site"
    _write(
        root / "index.html",
        '<link href="assets/stylesheets/main.css" rel="stylesheet">'
        '<script src="assets/javascripts/bundle.js"></script>'
        '<a href="tutorial/">Tutorial</a>',
    )
    _write(
        root / "tutorial" / "index.html",
        '<link href="../assets/stylesheets/main.css" rel="stylesheet">'
        '<img src="../assets/images/favicon.png">',
    )
    _write(root / "assets" / "stylesheets" / "main.css", "body{color:red}")
    _write(root / "assets" / "javascripts" / "bundle.js", "//js")
    _write(root / "assets" / "images" / "favicon.png", "png")
    return root


# --- the happy path -------------------------------------------------------


def test_intact_site_has_no_problems(mod, site):
    problems, notes = mod.check(site, base_path=None, require_css=True)
    assert problems == []
    assert any("2 HTML page(s)" in n for n in notes)


def test_main_exits_zero_on_intact_site(mod, site, capsys):
    assert mod.main([str(site), "--require-css"]) == 0
    assert "OK:" in capsys.readouterr().out


# --- the regression this guard was built for ------------------------------


def test_missing_stylesheet_is_reported(mod, site):
    (site / "assets" / "stylesheets" / "main.css").unlink()
    problems, _ = mod.check(site, base_path=None, require_css=False)
    assert len(problems) == 2  # referenced from both pages
    assert all("main.css" in p for p in problems)


def test_dropping_the_whole_assets_tree_fails(mod, site):
    """The exact shape of the 2026-07-27 regression: 43 files vanish, HTML unchanged."""
    for path in sorted((site / "assets").rglob("*")):
        if path.is_file():
            path.unlink()
    problems, _ = mod.check(site, base_path=None, require_css=True)
    # 4 dangling asset references (2 CSS, 1 JS, 1 image); the "tutorial/" link still resolves.
    assert len(problems) == 4
    # The stylesheet IS referenced — it is missing. Saying otherwise would be false,
    # and the dangling-reference problems above already report it.
    assert not any("no stylesheet is referenced" in p for p in problems)


def test_main_exits_one_when_a_reference_dangles(mod, site):
    (site / "assets" / "javascripts" / "bundle.js").unlink()
    assert mod.main([str(site)]) == 1


# --- require_css: the hole reference-integrity cannot see ------------------


def test_require_css_catches_a_site_that_links_no_stylesheet(mod, tmp_path):
    """Self-consistent but unstyled: nothing dangles, yet the site renders bare."""
    root = tmp_path / "site"
    _write(root / "index.html", "<p>no stylesheet here</p>")
    problems, _ = mod.check(root, base_path=None, require_css=True)
    assert len(problems) == 1
    assert "no stylesheet is referenced" in problems[0]
    assert mod.check(root, base_path=None, require_css=False)[0] == []


def test_require_css_catches_an_empty_stylesheet(mod, site):
    (site / "assets" / "stylesheets" / "main.css").write_text("", encoding="utf-8")
    problems, _ = mod.check(site, base_path=None, require_css=True)
    assert len(problems) == 1
    assert "empty" in problems[0]


def test_empty_site_directory_is_a_problem(mod, tmp_path):
    root = tmp_path / "site"
    root.mkdir()
    problems, _ = mod.check(root, base_path=None, require_css=True)
    assert len(problems) == 1
    assert "no HTML pages" in problems[0]


# --- root-relative references (MkDocs emits these in 404.html) ------------


def test_root_relative_reference_resolves_under_base_path(mod, site):
    _write(
        site / "404.html",
        '<link href="/model_project_constructor/assets/stylesheets/main.css" rel="stylesheet">',
    )
    problems, _ = mod.check(site, base_path="/model_project_constructor/", require_css=True)
    assert problems == []


def test_root_relative_reference_resolves_without_base_path(mod, site):
    """Inference keeps a zero-argument local run usable."""
    _write(
        site / "404.html",
        '<link href="/model_project_constructor/assets/stylesheets/main.css" rel="stylesheet">',
    )
    problems, _ = mod.check(site, base_path=None, require_css=True)
    assert problems == []


def test_root_relative_reference_to_a_missing_file_still_fails(mod, site):
    """Inference must not become a way for a genuinely absent asset to pass."""
    _write(
        site / "404.html",
        '<link href="/model_project_constructor/assets/stylesheets/gone.css" rel="stylesheet">',
    )
    for base in ("/model_project_constructor/", None):
        problems, _ = mod.check(site, base_path=base, require_css=False)
        assert [p for p in problems if "gone.css" in p], f"base_path={base!r}"


def test_root_relative_directory_reference_resolves(mod, site):
    _write(site / "404.html", '<a href="/model_project_constructor/tutorial/">t</a>')
    problems, _ = mod.check(site, base_path="/model_project_constructor/", require_css=False)
    assert problems == []


# --- reference classification --------------------------------------------


@pytest.mark.parametrize(
    "ref",
    [
        "https://example.com/x.css",
        "http://example.com/x.css",
        "//cdn.example.com/x.css",
        "mailto:someone@example.com",
        "tel:+15550000000",
        "javascript:void(0)",
        "data:image/png;base64,AAAA",
        "#anchor",
        "",
    ],
)
def test_non_local_references_are_ignored(mod, ref):
    assert mod.is_local(ref) is False


@pytest.mark.parametrize("ref", ["assets/x.css", "../assets/x.css", "/abs/x.css", "tutorial/"])
def test_local_references_are_recognised(mod, ref):
    assert mod.is_local(ref) is True


def test_query_and_fragment_are_stripped_before_lookup(mod, site):
    _write(
        site / "index.html",
        '<link href="assets/stylesheets/main.css?v=2#top" rel="stylesheet">',
    )
    problems, _ = mod.check(site, base_path=None, require_css=True)
    assert problems == []


def test_percent_encoding_is_decoded(mod, site):
    _write(site / "assets" / "a b.css", "body{}")
    _write(site / "index.html", '<link href="assets/a%20b.css" rel="stylesheet">')
    problems, _ = mod.check(site, base_path=None, require_css=True)
    assert problems == []


def test_directory_reference_needs_an_index_html(mod, site):
    (site / "tutorial" / "index.html").unlink()
    problems, _ = mod.check(site, base_path=None, require_css=False)
    assert [p for p in problems if "'tutorial/'" in p]


def test_single_quoted_attributes_are_scanned(mod, site):
    _write(site / "index.html", "<link href='assets/stylesheets/gone.css' rel='stylesheet'>")
    problems, _ = mod.check(site, base_path=None, require_css=False)
    assert [p for p in problems if "gone.css" in p]


def test_missing_site_directory_exits_one(mod, tmp_path, capsys):
    assert mod.main([str(tmp_path / "nope")]) == 1
    assert "not a directory" in capsys.readouterr().err
