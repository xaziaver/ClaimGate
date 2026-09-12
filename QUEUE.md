# Work queue

The ClaimGate build is over. `main` was tagged `prototype-1` at `be87d38` on 2026-09-11, with phases
2 and 3 complete, and the clean-up stage in `ROADMAP.md` is open. This file is its live queue.

**Where the build's queue went.** Items 1 through 7i, their closed entries, the reading table as it
stood and the dated status log from 2026-08-09 to 2026-09-11 were moved out of this file unchanged,
byte for byte, on 2026-09-11: items 1–5j and the log to the close of phase 2 are in
`docs/queue-history/phases-1-2.md`; item 6 onward, the reading table and the rest of the log are in
`docs/queue-history/phase-3.md`. A citation such as "`QUEUE.md` item 7c" or "`QUEUE.md`'s 7f
implementation paragraph", in a locked spec, a source comment, an approval reason in
`gauntlet.lock.json` or another document, resolves there by the same item number or paragraph.
Those citations are deliberately not rewritten: most sit in gated or hash-locked files, and editing
one to follow a document move would move the gated tree.

## Clean-up stage

In the order `ROADMAP.md`, "Clean-up stage", gives. During the build the harness was frozen and the
work moved; now the work is frozen and the harness moves.

C1. **Tag.** *(Closed 2026-09-11.)* `prototype-1`, annotated, at `be87d38`. The tag carries
    `gauntlet.lock.json`. It cannot carry `.gauntlet/events.jsonl`, which is ignored, so the log as it
    stood at the tag is archived at `docs/queue-history/events-prototype-1.jsonl` (C2a).

C2. **Document consolidation, with no spec or approval change and the gated tree unchanged
    throughout.** Five parts, in order, each its own commit or small series on `cleanup/documents`,
    each merged to `main` by the human after the advisor has checked it against `origin`.

C2a. *(Closed 2026-09-11 — commits `de2c23a` and `d5f90e8`, merged to `main` at `370a042`.)* The
    events archive; this file cut to the live queue, its history moved verbatim;
    `ROADMAP.md` step 1 annotated; `CLAUDE.md`'s duration figures brought to the last green pair.

C2b. *(Moved 2026-09-11 on `cleanup/documents`; the status section says where it stands.)*
    `ASSUMPTIONS.md` becomes an index of the decisions in force, retired ones dated, with its
    history moved beside the queue history. The index turns on a status per decision (in force,
    retired, superseded), which is a judgment per entry: the first session produces the
    classification as a read-only report, the advisor rules on it, and only then does anything move.
    Its largest section, "Carried requirements — decided, not yet built", is now mostly built.

C2c. *(Open 2026-09-11 on `cleanup/documents`.)* `docs/harness-findings.md` keeps "How the
    harness behaves" as the live document and moves
    the chronology to an appendix. The file is topical, not chronological: the chronology is the
    dated evidence inside entries, so the advisor states the rule per entry before anything moves.

C2d. *(Done 2026-09-11 on `cleanup/documents`.)* Both `PHASE*_DESIGN.md` files lose what
    describes code rather than decides design.
    `PHASE3_DESIGN.md`'s is one section; `PHASE2_DESIGN.md`'s is inline passages, which the advisor
    names by anchor. `CLAUDE.md`'s start-up step 5, which reads that section, changes in the same
    commit.

C2e. *(Done 2026-09-11 on `cleanup/documents`.)* `.gitignore` audited for `mutants/`,
    `.gauntlet/` state and review exports: last, and alone
    in its commit. The Stop hook wrapper hashes the gated paths through `git ls-files
    --exclude-standard`, so a `.gitignore` change is the one edit in C2 that can move the gated-tree
    hash without touching a gated file. The hash is computed before and after.

C3. **The harness moves against the frozen tag.** Not ClaimGate work: it is sequenced in
    agent-gauntlet's `gauntlet-findings.md`, under "Note for the v1 effort", which this repository
    does not read. No Gauntlet change lands here before C2 closes; `prototype-1` is the regression
    subject.

C4. **Phase 4 opens on the new harness**, with a fresh "How the harness behaves".

## What to read

`CLAUDE.md`, this file and `docs/harness-findings.md` every session, as before. Nothing in C2 needs
`docs/queue-history/` read in full; grep it.

| Working on | Also read |
|---|---|
| C2a | `ROADMAP.md`, "Clean-up stage"; nothing else |
| C2b | `ASSUMPTIONS.md` in full; `docs/queue-history/` by grep for any item an entry cites |
| C2c | `docs/harness-findings.md` in full |
| C2d | `PHASE2_DESIGN.md` and `PHASE3_DESIGN.md` in full |
| C2e | `.gitignore`; `.claude/hooks/stop-check.sh` |
| Anything citing a `QUEUE.md` item or paragraph | `docs/queue-history/`, by grep |

## Status as of this handoff

**2026-09-11: C2a and C2b are merged to `main`, at `370a042` and `b24dd48`. `ASSUMPTIONS.md` is
now the index of its 105 entries by status at `prototype-1`; the whole former file is
`docs/queue-history/assumptions.md`, byte for byte; the classification behind every status,
drafted by the agent and ruled on by the advisor, is
`docs/queue-history/assumptions-classification.md`. C2c is merged at `a86c614`: six chronology
entries — fourteen strand events, four hook budget raises and the whole measured wall-time series
— are in `docs/queue-history/harness-findings.md`, and what was live in them was rewritten as
behaviour, including the Stop hook wrapper's first entry of its own. "Process and technique" was
not restructured; it stays live and is where a session's process lessons go. C2d and C2e are
merged: `PHASE3_DESIGN.md`'s measured section is `docs/queue-history/phase-3-design-measurements.md`,
`PHASE2_DESIGN.md` carries a note at its head instead of surgery, `CLAUDE.md`'s start-up step 5
is rewritten, and every `.gitignore` rule says what it hides, with the finding that `mutants/` is
both a gated path and an ignored one. **C2 is closed.** The baseline below held on `main` after
every part; `.gitignore` is the one config path that differs from `prototype-1`, by annotation
alone, and the gated-tree hash is unchanged. Next is C3, in agent-gauntlet, in the seven-item order
under "Note for the v1 effort" in `gauntlet-findings.md`; nothing lands here until it has produced
a harness to open phase 4 on. A date note: the C2c to C2e markers in this file, the history
headers and the `.gitignore` audit line all say 2026-09-11, the day the advisor session that
produced them began; the commits themselves are dated 2026-09-12. Read 2026-09-11 there as the
session, not the calendar day.** No spec, approval, test,
source or configuration file has changed since `prototype-1`, `.gitignore`'s annotation excepted. No gate failure is expected. Every C2
turn touches documents only, so the Stop hook wrapper skips and prints a line naming run
`20260911T110451-2238600`, and that line is the turn's outcome. Do not run `gauntlet check` during
C2: on an unchanged gated tree it can only repeat the verdict below, at a cost of about an hour.

**The baseline every C2 commit is checked against, measured 2026-09-11 at `prototype-1` and at `main`
`be70e91`.** All of it must still hold after each commit; a difference is a stop, not a correction.
The Stop hook wrapper's gated-tree hash, by the pipeline in `.claude/hooks/stop-check.sh`, is
`e41d0a7cf92248ad25b833b95df06caa1721143dade322619090c61ae7da0999` over 128 files, recomputed by the
advisor from a clean clone and equal to line 1 of `.gauntlet/last-green-tree` on the human's
machine. `git diff --name-only prototype-1 HEAD -- src tests features mutants gauntlet.toml
gauntlet.lock.json pyproject.toml .claude .gitignore` prints nothing (C2e excepted, for `.gitignore`
alone). `gauntlet.lock.json` is sha256 `61c2ac4d30025e8c`, 92 entries: 16 spec, 73 mutant, 3 config.
The engine enumerates 1263 acceptance mutants over the sixteen specs at `be87d38` (advisor-measured),
and the specs' sha256 prefixes, each equal to its locked digest, are:

~~~
49f1f2f04b781739  features/carrier_configuration.feature
dc00a588ea216442  features/continuous_coverage.feature
4ce741d06d7f53f7  features/coverage_verification.feature
58a5370b5194531d  features/duplicate_evaluation.feature
29adb2bebdd52819  features/duplicates.feature
2c8b5c234060b523  features/idempotency.feature
595006155edcabdb  features/jurisdiction_date.feature
de726e3120e81c8b  features/jurisdiction_selection.feature
a0619c90ffa2ada7  features/notice_intake.feature
a504421e2c3ef5ed  features/policy_identification.feature
5f4eb8b7ea9495cc  features/policy_match.feature
96dccb0629163d5d  features/resolution.feature
1e7f697ecbcd62cd  features/siu_indicators.feature
0ff72e0de17dd406  features/siu_separation.feature
269a12ba9c697f6d  features/triage.feature
dba16d9635813218  features/validation.feature
~~~

**The last two green runs.** Run `20260911T100212-1991987` ran inside the
turn that committed `be87d38`. Its acceptance line is stamped 11:04:11 UTC and the commit 11:04:35
UTC, so it measured the working tree the commit captured; that is inferred from the times, because
no tree hash is recorded for it. All eleven gates were green: 966/966 tests, line and branch coverage
100.0, mutation 757 killed at 100.0 % (the cold run, 16.698 s), acceptance 16 specs and 73
reviewed-equivalent in 3690.978 s. The turn-end stop-check, run `20260911T110451-2238600`, gave the
same eleven verdicts (mutation 2.444 s) and is the run `.gauntlet/last-green-tree` records. Its
acceptance line, not pasted to the advisor at the turn end, read from the human's log on 2026-09-11:

~~~
{"actual": "16 spec(s), 73 reviewed-equivalent", "at": "2026-09-11T12:07:20+00:00", "diagnostics": 0, "duration": 3736.757, "error": null, "gate": "acceptance", "kind": "gate.finished", "passed": true, "run": "20260911T110451-2238600", "v": 1}
~~~

The pair: 3736.757 s against the 7200 s Stop hook budget, 3463 s to spare. Per mutant on 1263
mutants the two runs cost 2.922 s and 2.959 s, which widens the same-day band recorded at the 7i
close from 2.52–2.92 s to 2.52–2.96 s.

**The events archive.** `docs/queue-history/events-prototype-1.jsonl` is the first 836,642 bytes of
`.gauntlet/events.jsonl`, the file's size when the tag was made, sha256 `49395ea8c36d633f`, 3912
lines, ending on the acceptance line above. It holds every event from 2026-08-21T20:18:33Z to the
tag, not the whole build: events from 2026-08-02 to 2026-08-04 survive as 554 lines at
`8a83839^:.gauntlet/events.jsonl`, from the days the log was tracked, and events from 2026-08-04
to 2026-08-21, spanning items 1 through 4j, are in neither place. No document records why.
*(Corrected 2026-09-11; C2a's text called this archive the only record of every verdict the
build produced.)* Both of the tag's final runs are in it, and C3 compares its regression runs
against them.

**What remains before C2 closes.** Nothing; closed 2026-09-12, all five parts merged and the
baseline held. C3 is agent-gauntlet's; C4 opens phase 4 here on the harness C3 produces.
