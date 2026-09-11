<!-- gauntlet:begin -->
## Quality gates (Gauntlet)

This project is gated. Implementation code is yours; thresholds and approvals are
the human's.

- Run `gauntlet check` yourself before you say you are done. Do not wait for the
  Stop hook to tell you.
- **When a protected path has changed and the human has not yet run `gauntlet lock`, do
  not run `gauntlet check` and do not wait for a stop-check to run.** The protected paths
  are `.claude/settings.json`, `gauntlet.toml`, and `pyproject.toml`; the protect gate
  is red until the lock, so nothing the full run measures can pass. Instead run
  `gauntlet check --gates protect` to confirm the one red is the protected path, then
  `gauntlet check --gates static,size,complexity,boundary,tests,coverage,crap,duplication,mutation --fail-fast`
  for the cheap evidence, report both, and hand the lock to the human.
- Gate failures come back as JSON with a file, a symbol, a line, and a remedy.
  Act on the remedy rather than guessing.
- Never edit `gauntlet.toml`, `gauntlet.lock.json`, `.claude/settings.json`, or
  anything under `.gauntlet/`. Weakening a threshold is not a way to pass a gate.
  If you believe a threshold is genuinely wrong, say so and let the human decide.
- Write tests that would fail if the behavior were wrong. Coverage of code that
  asserts nothing is worthless and later gates are designed to catch it.
- Prefer extracting functions over suppressing a finding. `# noqa` and
  `# type: ignore` are last resorts, not shortcuts.
<!-- gauntlet:end -->

## Context discipline

A session spends most of its context before doing any work. These are the levers,
in order of what they actually cost.

- **Read only what the current queue item needs.** This file, `QUEUE.md`, and
  `docs/harness-findings.md` every session. Everything else is conditional, and
  `QUEUE.md`'s reading table says which per item. Reading a document the current
  item does not need is not thoroughness.
- **Pipe gate output.** `gauntlet check 2>&1 | tail -25` shows what failed. The
  full output on a red run is thousands of tokens and the Stop hook will dump it
  again whether or not you asked. Never re-read or re-quote a hook dump you have
  already seen — say what changed since the last one instead.
- **Grep before you read.** Locate the lines you need, then read a range. Whole
  files are for files you are about to edit.
- **Report what changed, not what you looked at.** A report that replays the
  investigation costs as much as the investigation did.
- **Use the skills instead of reading the harness source.** `.claude/skills/`
  carries `gauntlet-gates` (what each gate checks, whose commands are whose, why
  a gate is red), `gherkin-specs` (spec conventions, the shape constraints that
  decide whether a mutant dies, and `measure_mutants.py`), and `repo-edits`
  (anchor-based splicing, per-file handoff verification). Scanning
  `agent-gauntlet/src` to learn how the harness works costs a large share of a
  session every time and the answer is almost always in one of those three or one
  command away. When a skill turns out to be wrong, the source wins — fix the
  skill in the same commit.

## Standing constraints (ClaimGate domain, decided in design conversation)

These survive context loss even when the conversation that produced them doesn't.
Full reasoning for each lives in `PHASE2_DESIGN.md`, `ASSUMPTIONS.md`, and
`STATUTORY_REGISTER.md` — read those when the current item needs them, but check
this list before proposing anything that would violate one.

- Never default a threshold, state name, status code, or retention behaviour. Escalate instead. A
  defaulted rule is a rule nobody approved.
- There is no rejected, invalid, or discarded state anywhere in the record state model. A notice
  cannot be refused.
- SIU output records factual indicators only — never a conclusion, never the word "fraud" as a
  system-generated value — and is never a state or a routing destination.
- Claim lifecycle (open, reserved, in suit, closed, reopened) belongs to the policy administration
  system, not ClaimGate. ClaimGate does not mint claim numbers.
- No Gherkin scenario may name a function, class, table, or column.
- Every threshold needs a scenario on each side of the boundary.
- Regulatory values cite primary sources only — the Florida Legislature's statute text, enrolled
  bill text, FLOIR, or DFS — with a verified-on date. Never a law firm summary, a consumer blog, or
  a ratings site.
- When a recommendation follows from what the code currently does rather than from an independent
  judgment, say so explicitly instead of proposing around it.
- Spec approval, mutant approval, and mutant pruning are the human's calls, not something to run
  unprompted.
- **If an operation crosses an approval boundary by accident, reverse it and escalate. Do not
  correct it in place.** An accurate reason on an unauthorized approval is still an unauthorized
  approval.
- **Commit granularity is what makes the log worth reading, not a record of it having happened.**
  One commit per reopening, or a small series within one — never a batch spanning several
  reopenings. Spec lock and implementation are separate commits, in that order, so the sequence is
  visible in the log itself rather than only asserted in a document. Commit messages carry the
  reasoning, not just the change: one line of what, one line of why. Shape to match — "remove
  365-day reporting gate: late notice is a coverage determination made downstream on prejudice and
  tolling, not an intake rule" — not "update validation.py."
- **Main is always green.** Spec lock and implementation being separate commits means there is a
  legitimately red state between them — a spec drafted ahead of its approval or implementation.
  That state lives on a branch, never on `main`: `reopening/<name>` when an
  already-approved spec is being reopened, `phase2/<item>` for new construction
  such as a first feature file for a queue item. The prefix records which kind of
  work it is; the rules below apply to both. A branch merges to
  `main` only when its spec is locked, its implementation is complete, and `gauntlet check` is
  green. This follows directly from the commit-granularity rule above, not a separate policy.
- **Working branches stay a superset of main.** Documentation commits land on main; item work
  stays on its branch. **Corrected 2026-09-08: documents for an item go on the item's branch, and
  `main` moves only by the human's merge after a verified run.** `da76610`, item 7g's opening
  paragraph, went to `main` directly and stays where it is; it is the instance, not the rule.
  After any commit to main, **push `main` first**, then merge it into the
  open branch so the branch remains a superset. A checked-out working branch should always show
  current documentation. Pushing first is not housekeeping: the superset check below compares
  against `origin/main`, so an unpushed commit on local `main` makes that check pass while the
  branch is missing it.
- **A commit that changes a rule's behaviour under `src/claimgate/domain/` bumps
  `RULESET_VERSION`.** The label is declared once, in `domain/ruleset.py`, and the shell copies
  it onto every audit entry and every SIU indicator event, so a stored decision names the code
  that made it. No gate can enforce this; a stale label makes every row written after it a claim
  about rules that were not the ones applied.
- **A result that was not computed is never reported as a negative.** An indicator whose input is
  missing, or a comparison that was deliberately not run, resolves to a distinct not-evaluated
  value with a reason code — never to false, never to an empty result. Two reopenings have turned
  on this (`siu_indicators.feature`'s three-valued indicators, `duplicates.feature`'s notice-type
  rule). It applies to anything phase 2 serializes, not only to these two.
- **Reason-code enumerations are closed and scoped to one feature.** Duplicate detection's codes
  are not SIU's, even though both use the same not-evaluated-plus-reason convention; the two sets
  grow independently and neither file's "complete set" claim constrains the other. Escalate before
  adding a code to any of them, and never merge two enumerations to avoid editing a locked spec.
- **A gate failure awaiting a human decision is not a failure to retry.** A spec drafted or
  awaiting approval, a stale or unreviewed mutant approval, a dangling approval key — none of these
  clear from your side, and the separate-commits rule above guarantees the first one on every
  reopening. Report the condition and stop on the first occurrence.
- **Exporting a file at a ref means `git show <ref>:<path> > <file> && wc -l`.** Reading the
  working tree and reporting it as the export is not the same operation. They agree exactly when
  the tree is clean, which is when the protocol is least needed, and diverge in precisely the case
  it exists to catch.
- **Gauntlet's commands are split by owner, and the split is not guessable from the CLI.** Yours:
  `gauntlet check`, `verify`, `status`, `doctor`, `events`. Mine, never run unprompted: `gauntlet
  spec approve`, `mutant approve`, `mutant prune`, `review`, and `lock`. Note that `gauntlet lock`
  does not approve a specification — see "Command ownership" in `docs/harness-findings.md`.
- **"Act on the remedy" stops at the approval boundary.** If a remedy names a command from my list,
  the remedy is addressed to me: report it and stop. A remedy you cannot run is not an instruction
  to find something adjacent that you can. The acceptance gate's remedy for a modified spec is
  currently wrong in exactly this way.

## Session save-point

When asked for a save-point, the current session's context is about to be
discarded. The test is not "summarise what I did" — it is: **could a session
with no memory of this conversation resume from the repository alone?**

Work through it in this order, and stop at the first honest answer:

1. Is anything committed but not pushed? Push it. Quote `git log --oneline -1`
   alongside `git ls-remote --heads origin <branch>` for every branch touched.
2. Is the working tree clean? If a spec file shows a diff, check whether an
   acceptance run is live before assuming it is a defect — the gate mutates
   specs in place for the duration of its run.
3. Is an open reopening branch still a superset of `main`? Merge and push if not.
4. Does `QUEUE.md`'s status section describe the state that now exists? It must
   name: the branch and tip ref of any work in progress, whether a spec is
   drafted or locked and who owns the next action, any gate failure that is
   currently expected and why it is guaranteed rather than a defect, and what
   remains before the item closes. At every close it also records the acceptance
   gate's duration, from the last green `gate.finished` line in
   `.gauntlet/events.jsonl`, beside the Stop hook budget in `.claude/settings.json`,
   as a pair, so the race between them is visible. Rewrite it if it does not. If it
   already does, say so and change nothing.
5. Is anything you learned this session recorded nowhere? Decisions go to
   `ASSUMPTIONS.md` with provenance and a date. Harness behaviour and technique
   go to `docs/harness-findings.md`, established from source or an observed run,
   never from inference. A gap you cannot place in one of these is itself the
   finding — say so rather than dropping it.
6. Report what you changed and what you deliberately left alone.

Do not run `gauntlet spec approve`, `mutant approve`, `mutant prune`, `review`,
or `lock` as part of a save-point. Those are human actions and a save-point is
not the moment to take them.


## Session start-up

Before any work, orient and verify. Report before acting.

1. Read `QUEUE.md`'s status section, then follow its reading table for the item
   named there. Do not load documents the table does not list for that item.
2. `git fetch origin`, then confirm every ref is where the status section says it
   is. If work is on a branch, `git log --oneline origin/main ^HEAD` must print
   0 — a working branch stays a superset of `main`. Confirm local `main` is
   pushed before trusting that: the check compares against `origin/main`, and an
   unpushed commit on local `main` makes it pass vacuously. If it does not,
   STOP: you are reading a `QUEUE.md` older than the handoff written for you.
   Merge `origin/main`, push, re-read, then continue.
3. Confirm the working tree is clean and local matches remote for every branch
   the status section names. If any file under `features/` is modified, a mutation
   run was likely killed mid-flight — this is routine, not exceptional: a
   stop-check runs the full gauntlet after every turn, and any human reply inside
   its window kills it. The window is the acceptance gate's wall time, last measured at
   3690.978 s on sixteen specs (run `20260911T100212-1991987`, 2026-09-11, the verified run; the
   turn-end stop-check `20260911T110451-2238600` measured 3736.757 s), against a Stop hook
   budget of 7200 s in `.claude/settings.json`. Both figures move — the duration is recorded in
   `QUEUE.md`'s status paragraph at each close — and when the run outgrows the budget the hook
   kills its own run at every turn end without any human reply (events eleven to thirteen in
   `docs/harness-findings.md`). The strand takes one of the engine's substitution
   shapes — a value swapped for a sibling cell's value (including an empty one), a number
   incremented at its own precision, a boolean flipped, or a string literal with `_gauntlet`
   appended — and only the last carries a marker, so never identify a strand by its text; the
   digest against `gauntlet.lock.json` is the only test.
   Confirm by comparing the file against its copy under
   `.gauntlet/mutation-backup/`, restore with `git checkout --`, confirm the
   sha256 against `gauntlet.lock.json`, and report it. Do not edit the file and do
   not treat the acceptance gate's "changed since it was approved" as true until
   you have. First check no gauntlet run is alive using `ps -eo pid,etime,cmd`
   read by eye — a bare `pgrep -af gauntlet` matches its own command string and
   reads as a live run.
4. Read the last `gate.finished` line for the `acceptance` gate from
   `.gauntlet/events.jsonl` and report its verdict, duration and run id. A passing
   `stop-check` prints nothing, so the previous turn's outcome is confirmed from
   that line, never from silence.
   The stop-check is skipped when the gated tree is byte-identical to the last
   green run's, and a skip prints a line naming that run; a documents-only turn
   therefore ends in seconds, and that line is then the turn's outcome.
5. For any item inside a phase, check each claim in the phase design document's
   "what the code actually does today" section against source before item work,
   and annotate stale claims in place, dated, in the documentation commit that
   opens the item. Two such claims have been found in `PHASE3_DESIGN.md` already.
6. If a spec is described as drafted-not-locked, confirm with `gauntlet spec list`
   whether it has since been approved. The lock is the human's action and may have
   happened after the handoff was written.
7. State what you understand the current state to be and what you propose to do
   next. If the status section and the repository disagree, say which you are
   believing and why. Then wait — do not start work on your own reading of the
   queue unless the task you were given says otherwise.

### Environment notes

- The acceptance gate's wall time is the Stop hook's window: 3690.978 s at the last verified
  run (`20260911T100212-1991987`, 2026-09-11) and 3736.757 s at the turn-end stop-check,
  varying 2.52–2.96 s per mutant on near-identical trees, under a 7200 s hook budget. Run `gauntlet check`
  in the background, never under a foreground timeout; the current pair is in
  `QUEUE.md`'s status paragraph. (Corrected 2026-09-07 from "over 300s".)
  The hook runs `.claude/hooks/stop-check.sh`, which skips the stop-check when the
  gated tree is byte-identical to the last green run's and prints a line naming
  that run, so a documents-only turn ends in seconds.
- `gauntlet check` signals pass/fail by exit status, and the piped form returns
  tail's status. Read the printed verdict, never `$?`.
- A concurrent `gauntlet check` exits 0 having executed zero gates. Never relaunch
  one while another may still be alive.
- Never interrupt a run, with one exception: interrupting is acceptable only when the run
  is known to end red on a protected-path change awaiting the human's lock, because its
  acceptance stage would spend the whole window on a verdict already red. The recovery
  after that interrupt: `git checkout -- features/` restores every spec to its locked
  text; `sha256sum` the file the run had open against `gauntlet.lock.json`;
  `rm -rf .gauntlet/mutation-backup`; `.gauntlet/run.lock` is an OS flock released when
  the process died and needs nothing. The interrupted run's partial `gate.finished` lines
  stay in the events log and are not a green.
- The acceptance mutation engine is importable and pure-stdlib
  (`gauntlet.acceptance.gherkin`, `gauntlet.acceptance.mutation`). Measure mutant
  counts and ledger impact directly instead of predicting them, and compare
  against `gauntlet.lock.json` at the ref you are measuring.
- A spec file showing a diff during a live acceptance run is the gate's in-place
  mutation, not a defect. Check whether a run is alive before restoring anything.
