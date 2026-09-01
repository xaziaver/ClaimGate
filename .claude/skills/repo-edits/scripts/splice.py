#!/usr/bin/env python3
"""Anchor-based document edit: insert after, insert before, or replace.

The anchor must appear exactly once or the script refuses. Reports the hunk
count and the resulting sha256 so the change footprint is visible.

Usage:
  splice.py --file DOC --anchor-file A.txt --insert-after  --content-file C.md
  splice.py --file DOC --anchor-file A.txt --insert-before --content-file C.md
  splice.py --file DOC --anchor-file A.txt --replace       --content-file C.md
  splice.py --file DOC --append --content-file C.md
Add --dry-run to see the report without writing.
"""
from __future__ import annotations

import argparse
import hashlib
import sys


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True)
    p.add_argument("--anchor-file")
    p.add_argument("--content-file", required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    for flag in ("insert-after", "insert-before", "replace", "append"):
        mode.add_argument(f"--{flag}", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    original = open(args.file, encoding="utf-8").read()
    content = open(args.content_file, encoding="utf-8").read()
    # Line-oriented modes want a trailing newline; --replace substitutes verbatim.
    if not args.replace and not content.endswith("\n"):
        content += "\n"

    if args.append:
        updated = original + ("" if original.endswith("\n") else "\n") + content
    else:
        if not args.anchor_file:
            return int(bool(sys.stderr.write("--anchor-file required unless --append\n")) or 2)
        anchor = open(args.anchor_file, encoding="utf-8").read()
        seen = original.count(anchor)
        if seen != 1:
            sys.stderr.write(f"REFUSED: anchor appears {seen} times, expected exactly 1\n")
            return 2
        if args.insert_after:
            updated = original.replace(anchor, anchor + content)
        elif args.insert_before:
            updated = original.replace(anchor, content + anchor)
        else:
            updated = original.replace(anchor, content)

    added = len(updated.splitlines()) - len(original.splitlines())
    digest = hashlib.sha256(updated.encode("utf-8")).hexdigest()[:16]
    print(f"hunks: 1   lines: {len(original.splitlines())} -> {len(updated.splitlines())} (+{added})")
    print(f"sha256: {digest}")
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    open(args.file, "w", encoding="utf-8").write(updated)
    print(f"wrote {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
