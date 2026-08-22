"""Tests for scripts/check_published_site.py — the live half of the Session 237 guard.

``check_site_assets.py`` proves the built artifact is intact; this script proves
the deployment of it worked. The failures it exists to catch are the ones a green
workflow cannot see: Session 236 measured that Publish Tutorial "reports success
in 11-15s while dropping 43 files."

No network: ``check()`` takes injectable ``fetch``/``sleep``/``now`` so the
polling logic — which is the part most likely to be broken by a future edit — is
exercised deterministically and instantly.

Loaded via importlib, matching test_run_pipeline_adapter.py.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_published_site.py"

BASE = "https://example.invalid/repo/"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("_s237_check_published_site", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def site(tmp_path: Path) -> Path:
    root = tmp_path / "site"
    root.mkdir()
    (root / "index.html").write_text(
        '<link href="assets/stylesheets/main.css" rel="stylesheet">'
        '<script src="assets/javascripts/bundle.js"></script>'
        '<img src="assets/images/favicon.png">'
        '<a href="https://example.com/other.css">external</a>',
        encoding="utf-8",
    )
    return root


class Clock:
    """Monotonic clock that only advances when the code under test sleeps."""

    def __init__(self) -> None:
        self.t = 0.0
        self.slept: list[float] = []

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.t += seconds


# --- which URLs get probed ------------------------------------------------


def test_asset_refs_selects_local_css_and_js_only(mod, site):
    refs = mod.asset_refs((site / "index.html").read_text(encoding="utf-8"))
    assert refs == ["assets/stylesheets/main.css", "assets/javascripts/bundle.js"]


def test_probed_urls_are_the_base_plus_each_asset(mod, site):
    seen: list[str] = []
    problems = mod.check(BASE, site, 60, 10, fetch=lambda u: seen.append(u) or 200)
    assert problems == []
    assert seen == [
        BASE,
        f"{BASE}assets/stylesheets/main.css",
        f"{BASE}assets/javascripts/bundle.js",
    ]


def test_site_url_without_trailing_slash_still_joins_correctly(mod, site):
    seen: list[str] = []
    mod.check(BASE.rstrip("/"), site, 60, 10, fetch=lambda u: seen.append(u) or 200)
    assert seen[1] == f"{BASE}assets/stylesheets/main.css"


# --- the regression this exists to catch ----------------------------------


def test_a_404_stylesheet_fails(mod, site):
    """The live symptom from 2026-07-27: page 200, assets 404."""
    clock = Clock()

    def fetch(url: str) -> int:
        return 200 if url == BASE else 404

    problems = mod.check(BASE, site, 30, 10, fetch=fetch, sleep=clock.sleep, now=clock.now)
    assert len(problems) == 2
    assert all("returned 404" in p for p in problems)


def test_main_exits_one_when_assets_are_missing(mod, site, monkeypatch):
    monkeypatch.setattr(mod, "probe", lambda url, timeout=15.0: 404)
    code = mod.main(
        ["--site-url", BASE, "--site-dir", str(site), "--timeout", "0", "--interval", "1"]
    )
    assert code == 1


def test_main_exits_zero_when_everything_serves(mod, site, monkeypatch, capsys):
    monkeypatch.setattr(mod, "probe", lambda url, timeout=15.0: 200)
    # --timeout 0 on purpose: if `check` ever goes back to binding `probe` as a
    # default argument, this patch stops taking effect and the test must fail
    # fast against the real network rather than poll a dead host for 300s.
    assert mod.main(["--site-url", BASE, "--site-dir", str(site), "--timeout", "0"]) == 0
    assert "OK:" in capsys.readouterr().out


def test_check_resolves_probe_at_call_time(mod, site, monkeypatch):
    """`fetch=probe` as a default would capture the original and hit the network."""
    monkeypatch.setattr(mod, "probe", lambda url, timeout=15.0: 200)
    assert mod.check(BASE, site, 0, 10) == []


# --- polling: Pages builds asynchronously, so the first probe may 404 -----


def test_it_keeps_polling_until_pages_finishes_publishing(mod, site):
    clock = Clock()
    calls = {"n": 0}

    def fetch(url: str) -> int:
        calls["n"] += 1
        return 200 if calls["n"] > 3 else 404

    problems = mod.check(BASE, site, 300, 10, fetch=fetch, sleep=clock.sleep, now=clock.now)
    assert problems == []
    assert clock.slept, "expected at least one retry before succeeding"


def test_only_urls_still_failing_are_re_probed(mod, site):
    """A URL that has already returned 200 must not be asked again."""
    clock = Clock()
    seen: list[str] = []
    css = f"{BASE}assets/stylesheets/main.css"

    def fetch(url: str) -> int:
        seen.append(url)
        return 404 if url == css and seen.count(css) == 1 else 200

    assert mod.check(BASE, site, 300, 10, fetch=fetch, sleep=clock.sleep, now=clock.now) == []
    assert seen.count(BASE) == 1
    assert seen.count(css) == 2


def test_polling_stops_at_the_timeout(mod, site):
    clock = Clock()
    problems = mod.check(BASE, site, 25, 10, fetch=lambda u: 404, sleep=clock.sleep, now=clock.now)
    assert problems
    assert sum(clock.slept) <= 25


def test_a_zero_timeout_probes_exactly_once(mod, site):
    clock = Clock()
    calls: list[str] = []
    problems = mod.check(
        BASE, site, 0, 10, fetch=lambda u: calls.append(u) or 404, sleep=clock.sleep, now=clock.now
    )
    assert len(calls) == 3
    assert clock.slept == []
    assert len(problems) == 3


def test_unreachable_host_is_reported_as_no_response(mod, site):
    clock = Clock()
    problems = mod.check(BASE, site, 0, 10, fetch=lambda u: 0, sleep=clock.sleep, now=clock.now)
    assert all("no response" in p for p in problems)


# --- degenerate inputs ----------------------------------------------------


def test_missing_index_html_is_a_problem(mod, tmp_path):
    problems = mod.check(BASE, tmp_path, 0, 10, fetch=lambda u: 200)
    assert len(problems) == 1
    assert "does not exist" in problems[0]


def test_index_linking_no_assets_is_a_problem(mod, tmp_path):
    root = tmp_path / "site"
    root.mkdir()
    (root / "index.html").write_text("<p>bare</p>", encoding="utf-8")
    problems = mod.check(BASE, root, 0, 10, fetch=lambda u: 200)
    assert len(problems) == 1
    assert "references no stylesheet or script" in problems[0]


def test_probe_maps_transport_failure_to_zero(mod):
    assert mod.probe("http://127.0.0.1:1/nothing", timeout=0.2) == 0
