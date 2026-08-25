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
  if git show-ref --verify -q "refs/heads/$short" \
     || git show-ref --verify -q "refs/remotes/origin/$short"; then
    if git ls-remote --heads origin "$short" | grep -q .; then
      echo "  on origin: yes  ($(git ls-remote --heads origin "$short" | cut -c1-8))"
    else
      echo "  on origin: NO — this work exists only locally"
    fi
  else
    # A commit SHA is not a head, so `ls-remote --heads` matches nothing and
    # reports NO for a commit that is plainly pushed. Ask which remote branches
    # contain it instead. A branch name still takes the branch path above.
    contained=$(git branch -r --contains "$ref" --format='%(refname:short)' 2>/dev/null \
                | paste -sd' ')
    if [ -n "$contained" ]; then
      echo "  on origin: yes  (contained in: $contained)"
    else
      echo "  on origin: NO — no remote branch contains this commit"
    fi
  fi
done
