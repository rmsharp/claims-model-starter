"""Enforce §6 of docs/architecture-history/wiki-citation-symbol-references-plan.md: no
fragile line-number citations in the wiki.

Sessions 138-141 migrated every ``file:line`` citation on the wiki pages to
grep-locatable symbol/anchor references (plan §3). This guard keeps the
fragile forms from silently reappearing: it scans every page under
``docs/wiki/claims-model-starter/`` and fails with ``page:line: match`` for
any hit outside the allowlist.

Guarded forms (each one recurred during the migration sweeps):

- ``path.ext:N`` / ``path.ext:N-M`` for code, config, CI, fixture, and doc
  extensions (the plan's core pattern, widened with ``json``/``md`` — both
  occurred on live pages before migration);
- prose ``(line N)`` / ``(lines N-M)`` references;
- self-referential file-length counts ``(N lines)``, which drift just like
  line citations do.

Matches inside fenced code blocks count too, deliberately: example output
that embeds a real-looking ``path.py:N`` would drift identically. Bare
backticked ``:N`` references (historical Worked-Examples fixture form) are
NOT guarded — zero remain and the false-positive surface in inline code
spans is too large.

ALLOWLIST: empty since the Session 143 Evolution.md rewrite (plan §5.2 /
Phase 5) — the invariant is now enforced on every page. The set remains so
a future deliberate exception has a documented mechanism; a stale entry (an
allowlisted page with no matches left) fails the companion test so the
allowlist shrinks back to empty.
"""

from __future__ import annotations

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
WIKI_DIR = REPO_ROOT / "docs" / "wiki" / "claims-model-starter"

ALLOWLIST: frozenset[str] = frozenset()

FRAGILE_PATTERNS = (
    re.compile(r"[A-Za-z0-9_./-]+\.(?:py|toml|ya?ml|json|md):[0-9]+(?:-[0-9]+)?"),
    re.compile(r"\(lines? [0-9]+(?:-[0-9]+)?\)"),
    re.compile(r"\([0-9]+ lines\)"),
)


def _scan_page(path: pathlib.Path) -> list[str]:
    """Return one ``page:line: match`` string per fragile citation found."""
    offenders: list[str] = []
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        for pattern in FRAGILE_PATTERNS:
            for match in pattern.findall(line):
                offenders.append(f"{path.name}:{lineno}: {match!r}")
    return offenders


def _wiki_pages() -> list[pathlib.Path]:
    assert WIKI_DIR.is_dir(), f"wiki source directory missing: {WIKI_DIR}"
    pages = sorted(WIKI_DIR.glob("*.md"))
    assert pages, f"expected markdown pages under {WIKI_DIR}"
    return pages


def test_wiki_has_no_fragile_line_citations() -> None:
    offenders: list[str] = []
    for page in _wiki_pages():
        if page.name in ALLOWLIST:
            continue
        offenders.extend(_scan_page(page))
    assert not offenders, (
        "Fragile line-number citation(s) found on wiki page(s) — these drift "
        "as the cited files change. Replace each with a grep-locatable "
        "symbol/anchor reference per "
        "docs/architecture-history/wiki-citation-symbol-references-plan.md §3:\n  - "
        + "\n  - ".join(offenders)
    )


def test_allowlist_entries_are_still_needed() -> None:
    pages_by_name = {page.name: page for page in _wiki_pages()}
    stale: list[str] = []
    for name in sorted(ALLOWLIST):
        page = pages_by_name.get(name)
        if page is None:
            stale.append(f"{name}: page no longer exists")
        elif not _scan_page(page):
            stale.append(f"{name}: no fragile citations remain")
    assert not stale, (
        "Stale ALLOWLIST entry/entries in "
        f"{pathlib.Path(__file__).name} — remove them so the no-line-citation "
        "invariant is enforced on these pages too:\n  - " + "\n  - ".join(stale)
    )
