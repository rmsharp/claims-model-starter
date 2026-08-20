# Contributing

This is a single-maintainer project (see `CODEOWNERS`). This file covers the baseline contribution
process; the project's wiki has deeper detail on conventions, testing, and the session-based
development methodology this repo follows — see the
[Contributing](https://github.com/rmsharp/model_project_constructor/wiki/Contributing) wiki page.

## Getting started

See `README.md` for environment setup (`uv sync`) and how to run the test suite.

## Making changes

- Open an issue or discuss the change before a large PR — see `BACKLOG.md` for current priorities.
- Follow the existing commit message conventions (`feat:`, `fix:`, `docs:`, etc. — see `git log`
  for examples).
- New dependencies should be justified in the PR description; prefer zero-new-dependency solutions
  when the standard library or an existing dependency can do the job.
- Run `ruff check`, `mypy`, and the test suite before opening a PR.

## Licensing of contributions

This project is MIT-licensed (`LICENSE`). By submitting a contribution, you agree it is licensed
under the same terms.

**Signed commits / DCO / CLA:** not currently required for this repository. **This section is a
placeholder, not a final policy** — if/when this codebase moves into a corporate environment, the
target host's policy on signed commits and contributor agreements (see
`docs/planning/enterprise-migration.md` §3, decisions D3, D4, D9) will determine whether a formal
DCO or CLA mechanism is required there. That determination is out of scope for this repository and
is deliberately deferred; this file will be updated here only if this repository's own contribution
policy changes independently of that migration.

## Security

For security-sensitive reports, do not open a public issue — see `SECURITY.md`.

## Dependency licenses

See `THIRD-PARTY-LICENSES` for the full per-dependency license table. As of Session 193, zero
direct dependencies are LGPL — the two former LGPL SDKs (`python-gitlab`, `PyGithub`) were both
replaced with direct `httpx` calls (`docs/planning/httpx-adapter-migration.md`).

## AI-assisted development

Portions of this codebase were developed with AI assistance (Claude/Claude Code) under human
review — see `NOTICE` for the full provenance statement.
