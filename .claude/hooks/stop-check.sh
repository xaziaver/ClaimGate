#!/usr/bin/env bash
# Stop hook wrapper: run the full gauntlet stop-check, or skip it when the
# gated tree is byte-identical to the tree of the last green stop-check.
#
# Nothing any gate measures can change on a turn that touched only documents,
# so such a turn ends in seconds instead of a full acceptance run.
#
# Safety properties, both of which must survive any edit to this file:
#   1. Any byte in a gated or config path (the list in GATED_PATHS, tracked or
#      untracked) changes the hash and forces a full run.
#   2. Every failure of this wrapper — no git, no hash, a deleted tracked file,
#      a missing or corrupt saved record — is a full run. It never skips on an
#      error.
#
# The saved record, .gauntlet/last-green-tree, is three lines: the tree hash,
# the run id and the `at` of the acceptance gate.finished line that run wrote.
# It is written only after a stop-check that exited 0 AND left a new, passing
# acceptance gate.finished line in .gauntlet/events.jsonl — exit 0 alone is not
# enough, because stop-check also exits 0 when its retry cap is reached.
#
# GAUNTLET_STOP_DRY=1 echoes the command a full run would issue instead of
# running it, for testing the wrapper by hand.

set -u
set -o pipefail

payload=$(cat)

GATED_PATHS=(
  src
  tests
  features
  mutants
  gauntlet.toml
  gauntlet.lock.json
  pyproject.toml
  .claude/settings.json
  .claude/hooks
)
SAVED=.gauntlet/last-green-tree
EVENTS=.gauntlet/events.jsonl

last_acceptance_line() {
  grep '"kind": "gate.finished"' "$EVENTS" 2>/dev/null | grep '"gate": "acceptance"' | tail -n 1
}

json_field() {
  # json_field <line> <key> — the string value of a top-level key on one line.
  printf '%s' "$1" | sed -n 's/.*"'"$2"'": *"\([^"]*\)".*/\1/p'
}

run_full() {
  if [ "${GAUNTLET_STOP_DRY:-}" = "1" ]; then
    echo "gauntlet stop-check dry run: would run 'gauntlet stop-check --max-attempts 1' with ${#payload} bytes of stdin"
    return 0
  fi
  printf '%s' "$payload" | gauntlet stop-check --max-attempts 1
}

# --- locate the repository root; failure is a full run ----------------------
root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null) || root=""
if [ -z "$root" ] || ! cd "$root"; then
  run_full
  exit $?
fi

# --- hash the gated tree; failure is a full run ------------------------------
hash=$(git ls-files -z -c -o --exclude-standard -- "${GATED_PATHS[@]}" \
  | LC_ALL=C sort -z \
  | xargs -0 sha256sum \
  | sha256sum) || hash=""
hash=${hash%% *}
if ! [[ "$hash" =~ ^[0-9a-f]{64}$ ]]; then
  run_full
  exit $?
fi

# --- skip when the saved record names this exact tree ------------------------
if [ -f "$SAVED" ]; then
  saved_hash=$(sed -n '1p' "$SAVED")
  saved_run=$(sed -n '2p' "$SAVED")
  saved_at=$(sed -n '3p' "$SAVED")
  if [ "$saved_hash" = "$hash" ] && [ -n "$saved_run" ] && [ -n "$saved_at" ]; then
    echo "gauntlet stop-check skipped: gated tree unchanged since green run ${saved_run}, ${saved_at}"
    exit 0
  fi
fi

# --- full run; record the tree only on a fresh green -------------------------
before=$(last_acceptance_line)
run_full
code=$?
if [ "$code" -eq 0 ]; then
  after=$(last_acceptance_line)
  run_id=$(json_field "$after" run)
  at=$(json_field "$after" at)
  passed=$(printf '%s' "$after" | grep -c '"passed": true')
  if [ "$after" != "$before" ] && [ "$passed" -eq 1 ] && [ -n "$run_id" ] && [ -n "$at" ]; then
    printf '%s\n%s\n%s\n' "$hash" "$run_id" "$at" > "$SAVED.tmp" && mv "$SAVED.tmp" "$SAVED"
  fi
fi
exit "$code"
