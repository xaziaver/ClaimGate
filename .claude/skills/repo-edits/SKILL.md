---
name: repo-edits
description: Editing repository documents safely and verifying that work actually landed — anchor-based splicing instead of retyping, verification by outcome instead of by phrase, and per-file handoff checks at a named ref. Use when changing a long document like QUEUE.md, ASSUMPTIONS.md, CLAUDE.md, or harness-findings.md, when handing work back, or when confirming that a change reached origin.
---

# Editing documents and proving the change landed

## Never retype a document to change part of it

Retyping silently paraphrases the parts you were not changing, and the
paraphrase reads fine in review, so nothing catches it. A whole-file rewrite has
already deleted two unrelated entries in this repository once.

    scripts/splice.py --file ASSUMPTIONS.md --anchor-file anchor.txt \
        --insert-after --content-file new-entries.md

The script asserts the anchor appears **exactly once**, refuses otherwise, and
reports the hunk count and the resulting sha256. Report both.

**Locate a block by an anchor string, never by a line range.** A range taken from
a view of a file that a later commit shifted is how the two entries above were
lost.

## Verify by outcome, not by absence of a phrase

A grep for the phrase you just removed will also match your own correction of it,
and a grep for the phrase you just added proves only that you added it. Check
something that would change if the edit went wrong:

- a **count** — entries in the section before and after
- a **numstat** — insertions and deletions, per file
- a **context** — the line number of a known neighbouring heading
- a **hash** — sha256 of the file the human is about to approve

A purely additive edit must show `N 0` in `git diff --numstat`. A nonzero
deletion count on an edit you believed additive means something was overwritten.

## Handing work back

    scripts/handoff.sh <ref> [<ref> ...]

Prints, for each ref, the per-file numstat and the sha256 of every changed file,
plus whether the ref exists on origin. **Run it after pushing, not before.**

Three failure modes this catches, all of which have happened here:

- Work reported as done that was never pushed. `git log --oneline -1` on a local
  branch proves nothing about origin.
- A multi-file change where one file was missed. Confirming that *a push
  happened* does not confirm that *every file landed* — count occurrences per
  file, not per commit.
- A superset check that passes vacuously. `git log --oneline origin/main ^HEAD`
  compares against **origin's** main. If local `main` has unpushed commits, the
  check succeeds while the branch is missing them. Push `main` first, then check.

## When a human must approve what you produced

Export the file at a named ref rather than summarising it, and give the sha256
prefix so the human can confirm they are approving what you measured:

    git show <ref>:<path> > ~/claimgate-review/<ref>--<n> && wc -l

The `wc -l` matters: a failed redirect writes an empty file silently.
