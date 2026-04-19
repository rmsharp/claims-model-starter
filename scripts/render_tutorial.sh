#!/usr/bin/env bash
# Render docs/tutorial.md (or any GFM markdown) to standalone HTML with inline
# CSS that fixes the readability issues of plain `pandoc foo.md -o foo.html`:
# hr/code-block overlap, unbordered tables, and full-viewport-width body text.
#
# Usage:
#   scripts/render_tutorial.sh                       # docs/tutorial.md -> docs/tutorial.html
#   scripts/render_tutorial.sh INPUT.md              # -> INPUT.html (same dir)
#   scripts/render_tutorial.sh INPUT.md OUTPUT.html  # explicit output
#
# Exit codes:
#   0 = rendered successfully
#   1 = pandoc missing or input not found

set -euo pipefail

INPUT="${1:-docs/tutorial.md}"
OUTPUT="${2:-${INPUT%.md}.html}"

if ! command -v pandoc >/dev/null 2>&1; then
    echo "error: pandoc not found on PATH. Install from https://pandoc.org/installing.html." >&2
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "error: input file not found: $INPUT" >&2
    exit 1
fi

TITLE="$(grep -m1 '^# ' "$INPUT" | sed 's/^# //')"
: "${TITLE:=Tutorial}"

HEADER_FILE="$(mktemp -t render_tutorial.XXXXXX)"
trap 'rm -f "$HEADER_FILE"' EXIT

cat >"$HEADER_FILE" <<'EOF'
<style>
  body {
    max-width: 860px;
    margin: 2em auto;
    padding: 0 1.25em;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #24292f;
  }
  h1, h2, h3, h4 { line-height: 1.25; margin-top: 1.5em; }
  hr {
    margin: 2.5em 0;
    border: 0;
    border-top: 1px solid #d0d7de;
  }
  table {
    border-collapse: collapse;
    margin: 1em 0;
  }
  table th,
  table td {
    border: 1px solid #d0d7de;
    padding: 0.4em 0.8em;
    text-align: left;
    vertical-align: top;
  }
  table th { background-color: #f6f8fa; }
  pre {
    background-color: #f6f8fa;
    padding: 1em;
    border-radius: 6px;
    overflow-x: auto;
  }
  code {
    background-color: #eff1f3;
    padding: 0.1em 0.3em;
    border-radius: 3px;
    font-size: 0.9em;
  }
  pre code {
    background-color: transparent;
    padding: 0;
    font-size: inherit;
  }
  blockquote {
    margin: 1em 0;
    padding: 0.25em 1em;
    border-left: 4px solid #d0d7de;
    color: #57606a;
  }
</style>
EOF

pandoc \
    --from=gfm \
    --to=html5 \
    --standalone \
    --toc \
    --toc-depth=2 \
    --metadata=title="$TITLE" \
    --include-in-header="$HEADER_FILE" \
    --output="$OUTPUT" \
    "$INPUT"

echo "rendered $INPUT -> $OUTPUT"
