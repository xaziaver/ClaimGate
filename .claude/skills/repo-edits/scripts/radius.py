#!/usr/bin/env python3
"""Blast radius of the acceptance specs at a git ref.

For each feature file at REF: the mutant count, the unique-locator count, and
how many of those locators hold an approval in `gauntlet.lock.json` at that same
ref. Then totals. Everything is read through `git show`, never from the working
tree, so the figures describe a commit. The parser and mutation engine are the
harness's own, imported from --gauntlet-src, so this enumeration is the gate's
enumeration; only a survivor model is independent of it. Writes nothing.

Usage:
  radius.py [--ref REF] --gauntlet-src /path/to/agent-gauntlet/src
            [--feature features/x.feature]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

MUTANT_PREFIX = "mutant:"


def _git(root: str, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        sys.exit(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def _show(root: str, ref: str, path: str) -> str:
    return _git(root, "show", f"{ref}:{path}")


def _features_at(root: str, ref: str, only: str | None) -> list[str]:
    if only is not None:
        return [os.path.relpath(os.path.abspath(only), root).replace(os.sep, "/")]
    listing = _git(root, "ls-tree", "-r", "--name-only", "--full-tree", ref, "--", "features/")
    return sorted(line for line in listing.splitlines() if line.endswith(".feature"))


def _approved_locators(root: str, ref: str) -> set[str]:
    entries = json.loads(_show(root, ref, "gauntlet.lock.json"))["entries"]
    return {key[len(MUTANT_PREFIX):] for key in entries if key.startswith(MUTANT_PREFIX)}


def _measure(root: str, ref: str, path: str, approved: set[str], engine) -> tuple[int, int, int]:
    gherkin, mutation = engine
    found = mutation.mutants(gherkin.parse(_show(root, ref, path), path))
    locators = {m.locator for m in found}
    held = sum(1 for locator in locators if f"{path}#{locator}" in approved)
    return len(found), len(locators), held


def _engine(src: str):
    sys.path.insert(0, src)
    try:
        from gauntlet.acceptance import gherkin, mutation
    except ImportError as exc:
        sys.exit(f"gauntlet not importable from {src}: {exc}")
    return gherkin, mutation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--ref", default="HEAD")
    parser.add_argument("--gauntlet-src", required=True)
    parser.add_argument("--feature")
    args = parser.parse_args()
    root = _git(os.getcwd(), "rev-parse", "--show-toplevel").strip()
    engine = _engine(args.gauntlet_src)
    approved = _approved_locators(root, args.ref)
    totals = [0, 0, 0]
    for path in _features_at(root, args.ref, args.feature):
        counts = _measure(root, args.ref, path, approved, engine)
        totals = [a + b for a, b in zip(totals, counts)]
        print(f"{path}: {counts[0]} mutants, {counts[1]} unique locators, {counts[2]} approved")
    print(
        f"total at {args.ref}: {totals[0]} mutants, {totals[1]} unique locators, "
        f"{totals[2]} approved locators"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
