#!/usr/bin/env bash
# Publish docs/wiki/claims-model-starter/ to the live GitHub Wiki by syncing
# into a local clone of the wiki repository, committing changes, and pushing
# to origin. Idempotent: exits cleanly with "no changes to publish" when
# source and clone are already in parity.
#
# Usage:
#   scripts/publish_wiki.sh
#
# Configuration (via environment variable):
#   WIKI_CLONE  Path to a local clone of the wiki repo.
#               Default: ~/Development/claims-model-starter.wiki
#
# Prerequisites:
#   * The wiki clone must exist. Create it once with:
#       git clone https://github.com/rmsharp/claims-model-starter.wiki.git \
#           ~/Development/claims-model-starter.wiki
#   * git and rsync must be on PATH.
#   * Ambient git authentication (SSH / credential helper / gh CLI) must be
#     configured so `git push` against the wiki repo succeeds.
#
# Exit codes:
#   0 = published (or no changes to publish)
#   1 = configuration error (clone missing, tool missing, wrong branch, dirty clone)
#   2 = push failed (local commit is left in place; instructions printed for undo)

set -euo pipefail

if [ "${1:-}" != "" ]; then
    echo "error: unexpected argument: $1" >&2
    echo "usage: $(basename "$0")" >&2
    exit 1
fi

WIKI_CLONE="${WIKI_CLONE:-$HOME/Development/claims-model-starter.wiki}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
SOURCE_DIR="$REPO_ROOT/docs/wiki/claims-model-starter"

for cmd in git rsync; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "error: $cmd not found on PATH" >&2
        exit 1
    fi
done

if [ ! -d "$SOURCE_DIR" ]; then
    echo "error: source directory not found: $SOURCE_DIR" >&2
    exit 1
fi

if [ ! -d "$WIKI_CLONE/.git" ]; then
    cat >&2 <<EOF
error: wiki clone not found at $WIKI_CLONE

clone it first:
  git clone https://github.com/rmsharp/claims-model-starter.wiki.git "$WIKI_CLONE"

or override the path:
  WIKI_CLONE=/path/to/your/clone $(basename "$0")
EOF
    exit 1
fi

WIKI_REMOTE="$(git -C "$WIKI_CLONE" remote get-url origin 2>/dev/null || echo "")"
if ! echo "$WIKI_REMOTE" | grep -q 'claims-model-starter\.wiki'; then
    echo "error: wiki clone at $WIKI_CLONE does not point to the wiki repo" >&2
    echo "its origin is: ${WIKI_REMOTE:-<unset>}" >&2
    echo "expected origin URL to contain 'claims-model-starter.wiki'" >&2
    exit 1
fi

CURRENT_BRANCH="$(git -C "$WIKI_CLONE" rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT_BRANCH" != "master" ]; then
    echo "error: wiki clone is on branch '$CURRENT_BRANCH', expected 'master'" >&2
    echo "switch with: git -C \"$WIKI_CLONE\" checkout master" >&2
    exit 1
fi

if [ -n "$(git -C "$WIKI_CLONE" status --porcelain)" ]; then
    echo "error: wiki clone has uncommitted changes at $WIKI_CLONE" >&2
    echo "resolve them first (commit, stash, or discard) and re-run." >&2
    exit 1
fi

rsync -a --delete --exclude='.git/' "$SOURCE_DIR/" "$WIKI_CLONE/"

git -C "$WIKI_CLONE" add -A
if git -C "$WIKI_CLONE" diff --cached --quiet; then
    echo "no changes to publish"
    exit 0
fi

SOURCE_SHA="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"
COMMIT_MSG="docs: sync wiki from model_project_constructor@$SOURCE_SHA"
git -C "$WIKI_CLONE" commit -m "$COMMIT_MSG"

if ! git -C "$WIKI_CLONE" push origin master; then
    echo "error: push failed. Check git auth (SSH / credential helper / gh CLI)." >&2
    echo "to undo the local commit:  git -C \"$WIKI_CLONE\" reset --hard HEAD~1" >&2
    exit 2
fi

echo "published: $COMMIT_MSG"
