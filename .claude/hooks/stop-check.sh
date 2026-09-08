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
# The saved record, .gauntlet/last-green-tree, is four lines: the tree hash,
# the run id, the `at` of that run's acceptance gate.finished line, and the
# number of distinct gates that run finished. It is written only after a
# stop-check that exited 0 AND whose run — the run id on the newest acceptance
# gate.finished line in .gauntlet/events.jsonl — is green: no gate.finished
# line for that run id has "passed": false, the run finished as many distinct
# gates as the previous record's run (at least eleven on the first run), and
# the run id is newer than the record's. Exit 0 alone is not enough: stop-check
# also exits 0 at its retry cap with a gate red, and exit 0 with the newest
# acceptance line passing is not enough either — that was the first version of
# this file, and it recorded a run with protect red and acceptance green.
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
saved_hash=""; saved_run=""; saved_at=""; saved_gates=""
if [ -f "$SAVED" ]; then
  saved_hash=$(sed -n '1p' "$SAVED")
  saved_run=$(sed -n '2p' "$SAVED")
  saved_at=$(sed -n '3p' "$SAVED")
  saved_gates=$(sed -n '4p' "$SAVED")
  if [ "$saved_hash" = "$hash" ] && [ -n "$saved_run" ] && [ -n "$saved_at" ]; then
    echo "gauntlet stop-check skipped: gated tree unchanged since green run ${saved_run}, ${saved_at}"
    exit 0
  fi
fi

# --- full run; record the tree only on a fresh, wholly green run -------------
before=$(last_acceptance_line)
run_full
code=$?
if [ "$code" -eq 0 ]; then
  after=$(last_acceptance_line)
  run_id=$(json_field "$after" run)
  at=$(json_field "$after" at)
  if [ "$after" != "$before" ] && [ -n "$run_id" ] && [ -n "$at" ]; then
    run_lines=$(grep "\"run\": \"${run_id}\"" "$EVENTS" 2>/dev/null | grep '"kind": "gate.finished"')
    failed=$(printf '%s\n' "$run_lines" | grep -c '"passed": false')
    gates=$(printf '%s\n' "$run_lines" | sed -n 's/.*"gate": *"\([^"]*\)".*/\1/p' | sort -u | grep -c .)
    if [ -n "$saved_gates" ] && [[ "$saved_gates" =~ ^[0-9]+$ ]]; then
      gates_ok=$([ "$gates" -eq "$saved_gates" ] && echo 1 || echo 0)
    else
      gates_ok=$([ "$gates" -ge 11 ] && echo 1 || echo 0)
    fi
    newer=1
    if [ -n "$saved_run" ] && ! [[ "$run_id" > "$saved_run" ]]; then newer=0; fi
    if [ "$failed" -eq 0 ] && [ "$gates_ok" -eq 1 ] && [ "$newer" -eq 1 ]; then
      printf '%s\n%s\n%s\n%s\n' "$hash" "$run_id" "$at" "$gates" > "$SAVED.tmp" && mv "$SAVED.tmp" "$SAVED"
    fi
  fi
fi
exit "$code"
