#!/usr/bin/env bash
# Assert the load-bearing claims in SKILL.md against the real gauntlet package.
#
# Runs under the PROJECT interpreter, not the system one: this project pins
# requires-python >= 3.12, and a system python3 older than 3.11 fails on
# `import tomllib` with what looks like a missing dependency but is a wrong
# interpreter.
#
# Usage: verify.sh [path-to-agent-gauntlet-src]
#        (omit the path to verify the installed package, which is what runs)
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SRC="${1:-}"

resolve_python() {
  if [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/python" ]; then
    printf '%s' "$VIRTUAL_ENV/bin/python"; return 0
  fi
  for candidate in "$ROOT/.venv/bin/python" "$ROOT/venv/bin/python"; do
    [ -x "$candidate" ] && { printf '%s' "$candidate"; return 0; }
  done
  return 1
}

if PY="$(resolve_python)"; then
  RUN=("$PY")
else
  echo "No project interpreter found (looked at \$VIRTUAL_ENV, $ROOT/.venv, $ROOT/venv)." >&2
  echo "Activate the project venv and re-run. If the venv is missing entirely," >&2
  echo "creating one is your call, not this script's:  uv sync --project $ROOT" >&2
  exit 2
fi

if ! "${RUN[@]}" -c 'import sys; raise SystemExit(0 if sys.version_info>=(3,12) else 1)'; then
  echo "Interpreter is older than the project's floor (requires-python >= 3.12)." >&2
  "${RUN[@]}" --version >&2
  echo "This is an interpreter problem, not a missing package." >&2
  exit 2
fi

"${RUN[@]}" - "$SRC" <<'PY'
import sys, inspect, pathlib
src = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else ""
if src:
    sys.path.insert(0, src)
fails = []
def check(label, cond):
    print(("ok   " if cond else "FAIL ") + label)
    if not cond:
        fails.append(label)

import gauntlet
from gauntlet import config, registry
from gauntlet.acceptance import mutation
from gauntlet.gates import acceptance, boundary

print("interpreter:", sys.version.split()[0])
print("gauntlet:   ", pathlib.Path(gauntlet.__file__).parent)

stages = inspect.getsource(acceptance._stages)
check("approval stage precedes baseline stage",
      stages.index("_approval_stage") < stages.index("_baseline_stage"))

check("unapproved/modified remedy still names the wrong command",
      "gauntlet lock" in inspect.getsource(registry.describe)
      and "spec approve" not in inspect.getsource(registry.describe))

check("Background is never mutated",
      "background" not in inspect.getsource(mutation.mutants).lower())

check("boolean substitution map unchanged",
      mutation.BOOLEANS == {"true":"false","false":"true","yes":"no","no":"yes","on":"off","off":"on"})

check("protect has two distinct lists (paths blocks, verify is gate-checked)",
      set(config.DEFAULT_PROTECTED_PATHS) != set(config.DEFAULT_VERIFIED_PATHS))

check("pyproject.toml is content-verified (this is what pins the toolchain)",
      "pyproject.toml" in config.DEFAULT_VERIFIED_PATHS)

check("no skills path is protected or verified by default",
      not any("skills" in p for p in
              tuple(config.DEFAULT_PROTECTED_PATHS) + tuple(config.DEFAULT_VERIFIED_PATHS)))

check("boundary gate walks only the steps dir",
      "steps_dir.rglob" in inspect.getsource(boundary))

sys.exit(1 if fails else 0)
PY
