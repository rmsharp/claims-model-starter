#!/usr/bin/env bash
# Publish docs/wiki/model_project_constructor/ to the live GitHub Wiki by syncing
# into a local clone of the wiki repository, committing changes, and pushing
# to origin. Idempotent: exits cleanly with "no changes to publish" when
# source and clone are already in parity.
#
# Usage:
#   scripts/publish_wiki.sh                  # manual invocation (always safe)
#
# Auto-publish (recommended): the .githooks/post-commit hook invokes this
# script automatically when a commit touches docs/wiki/model_project_constructor/.
# Enable it once per clone with:
#   git config core.hooksPath .githooks
# Disable for a single commit with:
#   MPC_SKIP_WIKI_PUBLISH=1 git commit ...
#
# Configuration (via environment variables):
#   WIKI_CLONE  Path to a local clone of the wiki repo.
#               Default: ~/Development/claims-model-starter.wiki
#   MPC_WIKI_ALLOW_MASS_DELETE=1
#               Publish even when the sync would delete a disproportionate
#               share of the live wiki. Off by default: the clone is mirrored
#               with 'rsync --delete', so a source directory that has lost most
#               of its pages publishes those losses, unattended, from a hook.
#
# Prerequisites:
#   * The wiki clone must exist. Create it once with:
#       git clone https://github.com/rmsharp/model_project_constructor.wiki.git \
#           ~/Development/claims-model-starter.wiki
#   * git and rsync must be on PATH.
#   * Ambient git authentication (SSH / credential helper / gh CLI) must be
#     configured so `git push` against the wiki repo succeeds.
#
# Exit codes:
#   0 = published (or no changes to publish)
#   1 = configuration error (clone missing, tool missing, wrong branch, dirty
#       clone, empty source directory, or a refused mass deletion)
#   2 = push failed (local commit is left in place; instructions printed for undo)

set -euo pipefail

if [ "${1:-}" != "" ]; then
    echo "error: unexpected argument: $1" >&2
    echo "usage: $(basename "$0")" >&2
    exit 1
fi

WIKI_CLONE="${WIKI_CLONE:-$HOME/Development/claims-model-starter.wiki}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
SOURCE_DIR="$REPO_ROOT/docs/wiki/model_project_constructor"

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

# Existence is not enough. The sync below mirrors with --delete, so an existing
# but page-less source directory empties the live wiki and pushes the deletion.
# -L: '[ -d ]' and rsync's trailing slash both follow a symlinked source, but
# 'find' does not descend into one given as a path operand, so a bare 'find'
# would count 0 pages in a fully populated directory and abort.
SOURCE_MD_COUNT="$(find -L "$SOURCE_DIR" -type f -name '*.md' | wc -l | tr -d ' ')"
if [ "$SOURCE_MD_COUNT" -eq 0 ]; then
    echo "error: source directory holds no *.md files: $SOURCE_DIR" >&2
    echo "refusing to publish: 'rsync --delete' would empty the live wiki." >&2
    exit 1
fi

if [ ! -d "$WIKI_CLONE/.git" ]; then
    cat >&2 <<EOF
error: wiki clone not found at $WIKI_CLONE

clone it first:
  git clone https://github.com/rmsharp/model_project_constructor.wiki.git "$WIKI_CLONE"

or override the path:
  WIKI_CLONE=/path/to/your/clone $(basename "$0")
EOF
    exit 1
fi

WIKI_REMOTE="$(git -C "$WIKI_CLONE" remote get-url origin 2>/dev/null || echo "")"
if ! echo "$WIKI_REMOTE" | grep -q 'model_project_constructor\.wiki'; then
    echo "error: wiki clone at $WIKI_CLONE does not point to the wiki repo" >&2
    echo "its origin is: ${WIKI_REMOTE:-<unset>}" >&2
    echo "expected origin URL to contain 'model_project_constructor.wiki'" >&2
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

# A page count floor cannot express this guard: hard-code it low and it catches
# nothing, hard-code it high and it goes stale the next time a page is added.
# Measure the damage instead. A dry run reports exactly what --delete would
# remove; refuse only when that is out of proportion to what is published now,
# so retiring a few pages still goes through untouched.
CLONE_FILE_COUNT="$(git -C "$WIKI_CLONE" ls-files | wc -l | tr -d ' ')"
# Capture the dry run and check rsync's own status before counting. Piping it
# straight into 'grep -c ... || true' would turn an rsync failure into "0
# deletions" and publish blind -- the same fail-open shape this guard exists to
# close, one layer down.
if ! DRY_RUN="$(rsync -a --delete --dry-run --itemize-changes \
        --exclude='.git/' "$SOURCE_DIR/" "$WIKI_CLONE/")"; then
    echo "error: rsync dry run failed; refusing to publish without knowing" >&2
    echo "how much of $WIKI_CLONE the real sync would delete." >&2
    exit 1
fi
# Counted in bash rather than with 'grep -c ... || true': that idiom absorbs
# grep's ERROR exit as readily as its zero-match exit, and the empty string it
# leaves behind makes '[ "$PENDING_DELETIONS" -gt 2 ]' fail as a malformed test
# INSIDE an if-condition -- which 'set -e' does not catch, so the guard is
# skipped and the deletion published. This loop cannot fail.
# Directory deletions are itemised too and are skipped here: CLONE_FILE_COUNT
# comes from 'git ls-files', which counts files only, and comparing the two
# would trip the guard on a small subdirectory retirement.
PENDING_DELETIONS=0
while IFS= read -r itemised; do
    case "$itemised" in
        '*deleting '*/) ;;
        '*deleting '*) PENDING_DELETIONS=$((PENDING_DELETIONS + 1)) ;;
    esac
done <<<"$DRY_RUN"

if [ "${MPC_WIKI_ALLOW_MASS_DELETE:-0}" = "1" ] && [ "$PENDING_DELETIONS" -gt 0 ]; then
    echo "warning: MPC_WIKI_ALLOW_MASS_DELETE=1 — deletion guard disabled;" >&2
    echo "  publishing the deletion of $PENDING_DELETIONS file(s) from $WIKI_CLONE" >&2
fi

if [ "${MPC_WIKI_ALLOW_MASS_DELETE:-0}" != "1" ] &&
   [ "$PENDING_DELETIONS" -gt 2 ] &&
   [ "$((PENDING_DELETIONS * 4))" -gt "$CLONE_FILE_COUNT" ]; then
    echo "error: refusing to publish a mass deletion" >&2
    echo "  would delete $PENDING_DELETIONS of $CLONE_FILE_COUNT published files in $WIKI_CLONE" >&2
    echo "  source is $SOURCE_DIR ($SOURCE_MD_COUNT *.md files)" >&2
    echo "check the source directory is complete. If the deletion is intended:" >&2
    echo "  MPC_WIKI_ALLOW_MASS_DELETE=1 $(basename "$0")" >&2
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
