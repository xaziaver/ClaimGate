#!/usr/bin/env bash
# Per-file proof that a ref landed. Run AFTER pushing.
# Usage: handoff.sh <ref> [<ref> ...]
set -uo pipefail
[ $# -ge 1 ] || { echo "usage: handoff.sh <ref> [<ref> ...]"; exit 2; }
git fetch -q origin --prune
for ref in "$@"; do
  echo "=== $ref ==="
  if ! git rev-parse --verify -q "$ref" >/dev/null; then echo "  no such ref"; continue; fi
  echo "  tip:    $(git log -1 --format='%h %ad %s' --date=short "$ref" | cut -c1-72)"
  base=$(git merge-base "$ref" origin/main 2>/dev/null || echo "")
  if [ -n "$base" ]; then
    echo "  files changed vs merge-base with origin/main:"
    git diff --numstat "$base" "$ref" | while read -r add del path; do
      printf "    %-6s %-6s %-40s sha256=%s\n" "$add" "$del" "$path" \
        "$(git show "$ref:$path" 2>/dev/null | sha256sum | cut -c1-16)"
    done
  fi
  short="${ref#origin/}"
  if git ls-remote --heads origin "$short" | grep -q .; then
    echo "  on origin: yes  ($(git ls-remote --heads origin "$short" | cut -c1-8))"
  else
    echo "  on origin: NO — this work exists only locally"
  fi
done
