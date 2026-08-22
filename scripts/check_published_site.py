#!/usr/bin/env python3
"""Assert the LIVE published site serves the assets its built HTML links.

``scripts/check_site_assets.py`` proves the *artifact* is intact before it is
deployed. This proves the *deployment* worked, which is a different claim and a
different set of failures: ``ghp-import`` dropping files, a missing ``.nojekyll``
letting Jekyll swallow directories, Pages serving a stale build, or Pages not
being wired to the branch at all. Session 236 measured the shape of the problem
directly — the Publish Tutorial workflow "reports success in 11-15s while
dropping 43 files" — so the green check is not evidence and the live site is.

Polling is deliberate: a ``gh-pages`` push starts an asynchronous Pages build, so
the first probe after a deploy legitimately 404s. The script keeps asking until
the timeout, then fails.

Stdlib only, so CI's test job (``--extra agents --extra ui --extra dev``, never
``docs``) can unit-test it.

Usage::

    python scripts/check_published_site.py \\
        --site-url https://rmsharp.github.io/model_project_constructor/ --site-dir site

Exit status is 0 when every probed URL returns 200, 1 otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from urllib.parse import urljoin, urlsplit

_REF = re.compile(r"""(?:href|src)\s*=\s*["']([^"']*)["']""", re.IGNORECASE)
_EXTERNAL_PREFIXES = ("http://", "https://", "//", "data:", "mailto:", "tel:", "javascript:")
_ASSET_SUFFIXES = (".css", ".js")


def asset_refs(html: str) -> list[str]:
    """Local stylesheet/script references in ``html``, de-duplicated, in order."""
    out: list[str] = []
    for ref in _REF.findall(html):
        if not ref or ref.startswith("#") or ref.lower().startswith(_EXTERNAL_PREFIXES):
            continue
        if urlsplit(ref).path.endswith(_ASSET_SUFFIXES) and ref not in out:
            out.append(ref)
    return out


def probe(url: str, timeout: float = 15.0) -> int:
    """Return the HTTP status for ``url``; 0 when the request could not be made."""
    request = urllib.request.Request(url, method="GET")  # noqa: S310 - fixed https site URL
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return int(response.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except (urllib.error.URLError, OSError, ValueError):
        return 0


def check(
    site_url: str,
    site_dir: Path,
    timeout: float,
    interval: float,
    fetch: Callable[[str], int] | None = None,
    sleep: Callable[[float], object] = time.sleep,
    now: Callable[[], float] = time.monotonic,
) -> list[str]:
    """Poll until every URL derived from the built index page returns 200.

    Returns a list of problems; empty means the live site is serving what it links.

    ``fetch`` defaults to :func:`probe` but is resolved at call time, not bound as
    a default argument — a default would capture the original function object and
    make module-level patching silently fall through to the real network.
    """
    fetch = probe if fetch is None else fetch
    index = site_dir / "index.html"
    if not index.is_file():
        return [f"{index} does not exist — nothing to derive live URLs from"]

    refs = asset_refs(index.read_text(encoding="utf-8", errors="replace"))
    if not refs:
        return [
            f"{index} references no stylesheet or script — the published site would render "
            "unstyled, which is the regression this check exists to catch"
        ]

    base = site_url if site_url.endswith("/") else f"{site_url}/"
    urls = [base] + [urljoin(base, ref) for ref in refs]

    deadline = now() + timeout
    pending = list(urls)
    statuses: dict[str, int] = {}
    attempt = 0
    while True:
        attempt += 1
        still: list[str] = []
        for url in pending:
            status = fetch(url)
            statuses[url] = status
            if status != 200:
                still.append(url)
        if not still:
            for url in urls:
                print(f"  200  {url}")
            return []
        pending = still
        remaining = deadline - now()
        if remaining <= 0:
            break
        print(
            f"  attempt {attempt}: {len(pending)} of {len(urls)} URL(s) not yet 200, "
            f"retrying in {interval:.0f}s ({remaining:.0f}s left)"
        )
        sleep(min(interval, remaining))

    for url in urls:
        print(f"  {statuses.get(url, 0) or '---'}  {url}")
    return [
        f"{url} returned {statuses.get(url, 0) or 'no response'} after {timeout:.0f}s"
        for url in pending
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--site-url", required=True, help="published base URL, with scheme")
    parser.add_argument(
        "--site-dir", default="site", help="built site directory (default: site)"
    )
    parser.add_argument(
        "--timeout", type=float, default=300.0, help="seconds to keep polling (default: 300)"
    )
    parser.add_argument(
        "--interval", type=float, default=10.0, help="seconds between attempts (default: 10)"
    )
    args = parser.parse_args(argv)

    problems = check(args.site_url, Path(args.site_dir), args.timeout, args.interval)
    sys.stdout.flush()
    if problems:
        print("\nFAIL: the published site is not serving what it links:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"OK: {args.site_url} and every asset it links return 200.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
