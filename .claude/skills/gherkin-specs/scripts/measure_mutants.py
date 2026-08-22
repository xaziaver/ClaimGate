#!/usr/bin/env python3
"""Mutant count and per-scenario breakdown for one or more feature files.

Needs no approval, no ledger, and no gate run. Counts only: survivors cannot be
known until the spec is approved and step definitions exist.

Usage:  measure_mutants.py features/a.feature [features/b.feature ...]
        GAUNTLET_SRC=/path/to/agent-gauntlet/src measure_mutants.py ...
"""
from __future__ import annotations

import os
import sys
from collections import Counter

if os.environ.get("GAUNTLET_SRC"):
    sys.path.insert(0, os.environ["GAUNTLET_SRC"])

try:
    from gauntlet.acceptance import gherkin, mutation
except ImportError:
    sys.exit(
        "gauntlet not importable. Activate the project venv, or set GAUNTLET_SRC "
        "to the agent-gauntlet src directory."
    )


def main(paths: list[str]) -> int:
    if not paths:
        return int(bool(sys.stderr.write(__doc__)))
    grand = 0
    for path in paths:
        text = open(path, encoding="utf-8").read()
        found = mutation.mutants(gherkin.parse(text, path))
        grand += len(found)
        print(f"{path}: {len(found)} mutants")
        for scenario, count in Counter(m.scenario for m in found).items():
            print(f"  {count:4d}  {scenario}")
    if len(paths) > 1:
        print(f"total: {grand} mutants across {len(paths)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
