# Harness findings history

Moved verbatim from `docs/harness-findings.md` on 2026-09-11, clean-up stage C2c, and not to be
edited: the six entries under "How the harness behaves" whose content was dated record rather than
present behaviour. Between them they carry fourteen strand events, the acceptance gate's whole
measured wall-time series, four Stop hook budget raises, and the claims those measurements
falsified along the way. Every present-tense statement is true as of its paragraph's date. The live
document is `docs/harness-findings.md`, whose behaviour section states what each of these entries
is still evidence for.

---

### The Stop hook's timeout is now shorter than a green acceptance run, and the failure it produces is misdiagnosed

The acceptance gate re-mutates every approved spec on every stop and takes 693–759s at nine specs
and 655 mutants (measured 2026-08-25, item 5e). The Stop hook's timeout was the scaffolded 600s.
A stop-check killed mid-mutation leaves the spec being mutated with a `_gauntlet` line in the
working tree — the restore is a Python `finally`, which a signal skips — and because specs are
mutated in path order the corrupted file is always `validation.feature`. The next stop-check
then fails `tests` on the marker and reports the spec as "changed since it was approved", which
is false and prescribes the wrong remedy.

**Diagnosis, in order:** `git status -s` shows one modified spec; `git diff --stat` shows one line;
`.gauntlet/mutation-backup/<spec>` is newer than the commit and differs from the working tree; in
`.gauntlet/events.jsonl` a run id has `gate.finished` events for every gate before `acceptance`
and none for it. **Do not count `run.started` against `run.finished`** — stop-check emits neither,
so a killed one leaves the counts balanced (237/237 on the day). **Remedy:** `git checkout -- <spec>`,
confirm the sha256 against `gauntlet.lock.json`, then report. Never edit the spec; never run
`gauntlet lock`.

Technique that follows: the start-up check in `CLAUDE.md` now looks for this before anything
else, and the hook timeout is raised. Neither removes the cause, which is Gauntlet's and recorded
for it; they make the symptom visible and rare.

**Correction, 2026-08-26, from a live strand of a class this entry did not name.** A stop-check
was killed by the human's next message, not by a timeout: any reply inside the acceptance gate's
window kills the run, so interruption is the normal case in interactive use and the 1800s raise
does not touch it. Two claims above fall with that. "The corrupted file is always
`validation.feature`" was a property of the fixed 600s instant, not of the file — specs are
mutated in sorted path order (`specs.discover`), the stranded spec is whichever one's mutation
window spans the kill instant, and 600s always fell inside `validation.feature`'s window because
it is the last and largest. Today's interrupt kill landed in `carrier_configuration.feature`
instead, at line 140, `60 days` incremented to `61 days` — which is the second fallen claim: a
numeric mutant strands with no `_gauntlet` marker at all, so the marker is not a shape test,
and `CLAUDE.md`'s start-up rule is corrected accordingly in the same commit as this paragraph.
The `.gauntlet/mutation-backup/` comparison in the diagnosis above is unaffected and is the test
that survives both strand shapes. One trap found while diagnosing: `pgrep -af gauntlet` matches
its own command string, so the liveness check must use `ps` read by eye or it will report every
check as a live run. The stranded mutant happened to be the numeric member of the colliding pair
the locator entry below records; coincidence, no evidence weight, noted so the incident log does
not read as significant.

**Second correction, 2026-09-06: the raised timeout has been overtaken too, so a green stop-check
now kills itself.** A cold green `gauntlet check` at 14 specs and 73 reviewed-equivalent measured
2135.481s for the acceptance gate on 2026-09-06 (item 7e, run `20260906T140237`), past the 1800s
Stop hook timeout in `.claude/settings.json`; the two green runs before it that day measured
1879.917s and 1782.682s. Every stop-check therefore ends the same way whether or not a human
replies: killed inside the acceptance gate, stranding whichever spec's mutation window spans
1800s. The strand at `features/validation.feature:371` found at item 7e's start-up is the first
attributed to the timeout, inferred from the run's shape and the session gap; the strand at
`features/triage.feature:99` found one turn later, from the stop-check that fired on item 7e's
implementation commit, is the second and the measured one — the eleventh and twelfth events under
"A corrupted spec from an interrupted mutation run has a recovery path already on disk" carry the
evidence and its limits. Unit-test growth
does not contribute to this figure: the per-mutant run is `run_acceptance` in
`adapters/python.py`, `pytest <steps>` over the acceptance directory alone (`_survivors` in
`gates/acceptance.py`), so the wall time grows as scenarios times mutants. The hook timeout is not
changed here; that is the human's, at the close-out lock.

### The exit-status pipe trap has a confirmed realized cost, not just a hypothetical one

The run at `2026-08-13T23:16:37` reported `tests 168/169` and `acceptance: 1
unapproved or modified spec(s)`, finishing `passed=False` and exiting 2 — the
gate detected the corruption and named it correctly. That run is the one
reported in-session as "Background command completed (exit code 0)": piped
through `tail`, the real exit status was discarded, and the same corruption
was then independently rediscovered by `git diff` and credited to the diff
rather than to the gate that had already caught it. Recorded here because it
happened, not because it could.

### A corrupted spec from an interrupted mutation run has a recovery path already on disk

The acceptance gate writes a pre-mutation copy of every spec it is about to
mutate to `.gauntlet/mutation-backup/<name>` before mutating it in place
(`gates/acceptance.py`'s `_backup`, called ahead of each mutation pass). That is
the intended recovery path for the corrupted-source finding above ("Check `git
diff` after any interrupted mutation run") — restore from there, not `git`,
once a run is confirmed interrupted.

**Two restore sources, and when they agree.** This entry says restore from the
backup; the diagnosis under "The Stop hook's timeout is now shorter than a green
acceptance run", and `CLAUDE.md`'s start-up step, say `git checkout -- <spec>`.
Both are right whenever every spec is committed at its locked text, which is the
normal state: the backup and `HEAD` then hold the same bytes. They diverge only
when a spec has uncommitted approved edits, and there the backup is the correct
source and `git` would lose the edit. The test is the same either way: the
restored file's sha256 must equal the entry in `gauntlet.lock.json`.

**The backup directory is always there after a completed run.** `_backup` writes
one copy per spec and nothing removes them, so `.gauntlet/mutation-backup/`
holds a full set of files after any run that reached mutation, green or red —
sixteen of them after the last green run at `prototype-1`. Its presence is
therefore not a signal of anything. Only the comparison is: a file newer than
the commit and differing from the working tree. A recovery step that deletes the
directory deletes something the next run recreates.

**Correction, 2026-08-14.** An earlier version of this entry cited a specific
occurrence — a `features/validation.feature` corruption found and `git
restore`d earlier the same session — as "the last time that finding fired."
`gauntlet events --limit 0` shows no `run.started` for `command=check` that
session lacking a matching `run.finished`: both full-gate runs that day
(09:45:21→09:47:55, 10:15:25→10:18:36) completed cleanly, and no run was
killed. The claim was an unverified inference at the time, restated as a
confirmed finding — the exact failure shape this file exists to catch,
happening to this file. Corrected rather than left standing; what actually
produced that corruption is unconfirmed, and is not this entry's finding to
claim.

**Two more events, both 2026-08-27, and the recovery held exactly as written each
time.** The 2026-08-14 correction above says what produced that occurrence is
unconfirmed. These two are better evidenced, and together they make the strand a
recurring condition rather than an anecdote.

- **Second event, found at the session start of the item 5g close-out.** A
  *numeric* in-place strand in `features/siu_indicators.feature`: a late-reporting
  threshold of `45` incremented to `46`. Restored from
  `.gauntlet/mutation-backup/`. This is the class the 2026-08-26 correction above
  named: a numeric strand carries no `_gauntlet` token, so on the page it reads as
  a deliberate threshold edit — a plausible one, on a value this project has
  argued about — and nothing but the digest comparison against
  `gauntlet.lock.json` distinguishes it from intended work.
- **Third event, found at the session start immediately after that one**, and
  measured here rather than inherited: `features/carrier_configuration.feature`,
  scenario "A recognized carrier's rules resolve to every value the domain will
  receive", `And "AAAA" configures a late reporting threshold of 45 days` with
  `"AAAA"` mutated to `"AAAA"_gauntlet` — the marker class, on the same step line
  as the numeric above and therefore on a colliding locator (see "Mutant counts
  and locator counts are different numbers"). `.gauntlet/mutation-backup/` was
  byte-identical to `HEAD`, so the working-tree file was the strand and
  `git checkout --` restored it; all eleven digests then matched the lock.

**What the log shows about the third one, and what it does not.** `gauntlet
events` has a full gate sequence beginning `2026-08-27T13:40:39Z` with no
`gate.finished` for `acceptance` after it and no `run.finished` at all — a
stop-check, per "`stop-check` runs the full gauntlet but never emits
`run.started` or `run.finished`", fired 25 seconds after commit `b67b220` and
killed inside the acceptance gate. Only `carrier_configuration.feature` carries a
`.gauntlet/mutation-backup/` mtime from that run (13:40:47Z); every other spec's
is from the completed 13:01:43Z→13:18:25Z run. Specs are mutated in sorted path
order, so the run died inside the first file it opened. **The cause of the kill is
UNCONFIRMED.** Operator interruption at the terminal is plausible and is what the
timing is consistent with — the kill lands between two agent sessions, not inside
one — but the log records no reason, and this entry does not claim one. What is
worth stating is the standing incentive: that same run's completed predecessor
took **995.9s**. A gate that occupies a terminal for sixteen minutes invites the
interruption that strands a spec, so the strand rate is a property of the gate's
wall time, not of any one person's care.

**The discipline this implies is the operator's as much as the agent's.** The
existing guidance — check `git diff` after an interrupted mutation run — assumes
the interrupter and the diagnoser are the same session. In both events above they
were not: the run was killed in one session and the strand found at the start of
the next, by an agent with no memory that a run had ever been interrupted. Two
rules follow, and neither is conditional on having witnessed a failure:

1. **A clean tree before any gate run, verified rather than assumed.** A gate run
   started over a dirty tree mutates a file that already differs from its
   approved digest, and the backup then preserves the wrong baseline.
2. **A digest check at every session start**, not only after an agent-visible
   failure. It is the only test that catches the numeric class, it costs one
   command, and it has now fired on two consecutive sessions.

**Third strand shape, 2026-09-01.** `features/carrier_configuration.feature`,
the policy-number-prefixes row of "A single value absent or malformed in a
recognized carrier's entry refuses the load, naming it": `absent` replaced by an
empty cell. No marker, not numeric — the sibling-swap branch of `mutate_value`,
the last of that function's four branches. Measured against the installed engine
rather than inferred: the branch fires 30 times in this scenario's 33 mutants,
every one landing on the empty cell of the outline's all-blank final row, and
this exact substitution — `absent` to an empty cell — is four of them, one per
row whose value cell reads `absent`. The diagnosis rule that named two shapes was
incomplete by construction: a strand has as many on-page shapes as the engine has
substitution rules, and every rule added to the engine adds a shape. Restored
from `.gauntlet/mutation-backup/`, digest confirmed. The rule in `CLAUDE.md` now
says so.

**Eleventh and twelfth events, 2026-09-06 — the first strands from the hook's own timeout rather
than from an interrupt.** Events one to ten are logged in the harness's own findings file
(`agent-gauntlet/gauntlet-findings.md`, "Events seven through ten"), where the trigger named for
seven to ten is the operator's next message killing a stop-check. The two found during item 7e
change the trigger. **Eleventh:** `features/validation.feature:371`, `"required"` mutated to
`"required"_gauntlet` in the claimant-contact configuration step, found at 7e's session start. Run
`20260906T115427`, stop-check shape (ten `gate.finished` events, none for `acceptance`, no
`run.started`), fired on the 7d close-out save point; that session had ended and the next opened
about ninety minutes later, so no message was there to kill it, and the day's green runs measured
1782.682s, 1879.917s and 2135.481s against the 1800s hook timeout. Consistent with the timeout, and
the human's reading; the `.gauntlet/mutation-backup/` mtimes that would place the kill were
overwritten by the two later runs, so this one is inferred from the shape and the window, not
measured. **Twelfth:** `features/triage.feature:99`, the loss date `2026-08-01` sibling-swapped to
`2026-06-01` in the severity outline, no marker, found one turn later. Run `20260906T144106`,
stop-check shape, fired on 7e's implementation commit at 14:41:06Z; the backup mtimes show the run
entering `triage.feature` at 15:09:28Z, twenty-eight minutes in, and never reaching
`validation.feature`, whose backup still carries the 14:33:23Z stamp of the previous run. 14:41:06Z
plus 1800s is 15:11:06Z, inside `triage.feature`'s window, and no human message arrived until about
15:58Z. This one is measured. Both restored with `git checkout --`, digests confirmed against the
lock. At 2135s a green run outlives the hook, so every stop-check now strands the tree by itself,
with no operator involved; see "The Stop hook's timeout is now shorter than a green acceptance
run", second correction.

**Thirteenth event, 2026-09-06, and the first stop-check to finish since the raise, 2026-09-07.**
`features/validation.feature`, stranded by the stop-check that fired at 16:05:39Z on item 7e's
ratification commit `4e08b19`: run `20260906T160539`, stop-check shape in `.gauntlet/events.jsonl`
(ten `gate.finished` events, none for `acceptance`, no `run.started`), the 1800s hook still in
force. Found and restored at 7e's close-out, digest confirmed; the "killed 43s after entering that
file" in `QUEUE.md`'s status paragraph is that session's reading of the backup mtimes, since
overwritten, so it is quoted from the record rather than re-measured. Logged here 2026-09-07. The
next stop-check, run `20260907T064859` on the close-out commit that raised the hook to 3600s, is
the first since the raise to reach `acceptance` and finish: eleven `gate.finished` events,
`acceptance` passed in 1993.92s, 14 specs, 73 reviewed-equivalent. A passing stop-check prints
nothing, so that line is the only evidence the turn end completed; `CLAUDE.md`'s start-up step 4
now reads it before anything else.

**Fourteenth event, 2026-09-10: no strand, and the budget raised to 7200 s on a variance
measurement rather than a growth one.** The stop-check `20260910T122219-1111884`, fired on the
7h merge `fc479e3` — a gated tree byte-identical to the one the verified run
`20260910T112652-904083` measured at 3169.29 s — finished `acceptance` green in 3475.182 s,
124.818 s under the 3600 s hook: the same 1257 mutants, the same 882 tests, no change to
anything a gate measures, and 305.9 s (9.65 %) more wall time. The next such variance on a tree
one spec larger strands the tree by the hook's own timeout, the eleventh and twelfth events'
shape. `.claude/settings.json`'s stop-check timeout is therefore 7200 s from this commit, a
protected-path change awaiting the human's `gauntlet lock`, and the stop-check on the commit
stops at `protect` under `--fail-fast` — the `86cd32f` sequence, not a failure. The raise was
deferred from 7i's opening on the human's decision of 2026-09-08 that Gauntlet is not modified
until the end of the ClaimGate build (`agent-gauntlet/gauntlet-findings.md`, "The acceptance
gate runs the entire steps directory once per mutant", status); that per-spec scoping change
remains the real fix, and the raise only buys the room 7i's runs need under the model that
entry prices. It strengthens "The acceptance gate's wall time is growing", fifth measurement:
the variance band is to be budgeted against, not the last figure, and this pair puts the band
at about ten per cent on an identical tree — larger than the 431 s margin 7h's close recorded.

### The acceptance gate's wall time is growing, not fixed at ~150s

Across 162 acceptance-gate runs in the log, the maximum observed is 260.3s,
and the trend is upward, not flat: the four most recent runs measured 186.2s,
174.1s, 208.2s, and 260.3s. Budget 300s as a floor for any tool timeout
wrapping `gauntlet check`, and expect that floor to keep rising as the suite
grows — don't quote a fixed number here again without rechecking the log.
The exposure isn't evenly distributed, and this entry's original claim about
it was falsified: the Stop hook's 600s was overtaken by a green run and had to
be raised to 1800s on 2026-08-25. See "The Stop hook's timeout is now shorter
than a green acceptance run" above for what that cost. The `PostToolUse` hook
only ever runs the fast gates (`static`, `size`, `complexity`) at a 60s
budget and is the only one genuinely not at risk. Every killed run
in this project's history was an agent-issued `gauntlet check` through `bash`,
cut off at whatever that tool call's own timeout happened to be — that is the
timeout that needs raising, not the hooks'.

**That last sentence is false and was already falsified inside this file.** Runs
have since been killed by the Stop hook's own timeout, and by a human's reply
landing inside the acceptance window: see the second correction under "The Stop
hook's timeout is now shorter than a green acceptance run" and the strand events
under "A corrupted spec from an interrupted mutation run has a recovery path
already on disk". Every timeout that wraps the gate needs to clear a green run,
not just the agent's `bash` one.

**Correction, 2026-08-24: the maximum is no longer 260.3s.** A run against
`features/notice_intake.feature` approved with no bound step definitions took
423.622s — every one of its 24 mutants ran a full suite pass before scoring
surviving, not a bigger suite taking proportionally longer. Read this new
maximum as the cost of that specific defect (see "An approved spec that no
test module binds reports every mutant as surviving," below), not as ordinary
growth continuing the trend the four runs above already showed. The 300s floor
this entry recommends is now itself below the observed maximum; raise it, and
keep rechecking the log rather than trusting either number as fixed.

**Second correction, 2026-08-24: 472.803s, and this one is ordinary growth, not
the unbound-spec defect.** Item 5c's implementation commit bound
`features/notice_intake.feature` to real step definitions and merged clean:
7 specs, 69 reviewed-equivalent, no unreviewed survivors. Unlike the 423.622s
run above, every mutant here ran against a genuinely bound, passing suite —
the time is the cost of one more fully-exercised spec file (48 mutants) on top
of the six already there, not a full-suite re-run per mutant. Both figures are
real; they measure different things. Budget past 480s now, and keep
rechecking rather than anchoring on either number.

**Third correction, 2026-08-26: 893.841s, and read it beside 866.202s.** Item
5f's all-green run — 10 specs, 708 mutants, a 397-test suite, 71
reviewed-equivalent — took 893.841s, about 1.26s per mutant. The same ten
specs and the same 708 mutants took 866.202s at the pre-approval run, so the
27.6s is unexplained and inside variance. Neither is evidence that approving a
survivor costs time, because it does not: `_survivors` applies every mutant and
runs the full suite for each before the ledger is read, which is also what
makes a stale approval detectable. Budget past 900s and keep rechecking rather
than anchoring on any of these.

**Fourth correction, 2026-09-06: 2135.481s, and the 300s floor this entry opens with is stale by a
factor of seven.** Item 7e's cold green run — 14 specs, 73 reviewed-equivalent, a 762-test suite,
no spec changed — took 2135.481s in the acceptance gate, with 1879.917s and 1782.682s on the same
day's two earlier green runs. Every budget quoted above, 300s, 480s, 900s, is below the observed
figure; the Stop hook's 1800s has been overtaken as well (see "The Stop hook's timeout is now
shorter than a green acceptance run", second correction). Budget past 2200s for any tool timeout
wrapping `gauntlet check`, run it in the background rather than under a foreground timeout, and
keep rechecking the log.

**Fifth measurement, 2026-09-07: 1993.92s under the 3600s hook, the first green stop-check since
the raise.** Run `20260907T064859`, the stop-check on item 7e's close-out commit: 14 specs, 73
reviewed-equivalent, 763 tests, `acceptance` 1993.92s. Below the 2135.481s above, so the four
green figures at this spec count span 1782–2135s; read that as the variance band to budget
against, not a trend reversal. The 3600s hook clears a green run by about 1600s today.
`CLAUDE.md`'s start-up step 3 carries the pair and `QUEUE.md`'s status paragraph records it at
every close, so the next raise is planned rather than discovered from a strand.

**Sixth measurement, 2026-09-08: 2458.573 s at 15 specs and 1155 mutants, and a model that
calibrates at 1.0.** Run `20260908T085655-217436`, item 7g's structural commit `ce62f3d`, no spec changed; the two
runs before it on the same lock measured 2427.14 s and 2556.762 s. The per-mutant unit is one run
of `pytest tests/acceptance` — `_survivors` in `gates/acceptance.py` calls `run_acceptance` with
the steps *directory*, never the one spec's module — and that run measured 2.210 s at `ce62f3d` on
a quiet machine (2.222, 2.164, 2.244 with the engine's own flags; 291 rows, 1.316 s of testcase
time, the rest interpreter start and collection). 2.210 × 1155 = 2552.6 s, and observed over modelled is 0.951
for the first run, 1.002 for the second and 0.963 for this one. The model a per-module timing suggests — each spec's
standalone module wall time times its mutant count — sums to 612.0 s on the same numbers, a
quarter of the observed, because it prices a scoping the gate does not do. What follows for
pricing a draft: every mutant costs a whole-directory run, and every scenario row costs its
testcase time on every mutant's run — 7.3 ms a row for `resolution.feature`'s shape, 8.4 s a row
at today's count — so the wall time is rows × mutants and grows with the square of the suite,
which is why 8 % more mutants at 7f cost 44 % more time. The 7g status paragraph — in `QUEUE.md`
until C2a moved it to `docs/queue-history/phase-3.md` — carries
the per-spec table.

**Seventh entry, 2026-09-08: four documents-only stop-checks this phase, 42–53 minutes each, and
a wrapper that now skips them.** Each of these turns changed nothing any gate measures, and each
paid a full acceptance run: `4ed3afa` (7f close-out) fired run `20260907T223153-123173`, 2556.762 s;
`da76610` (7g documents) fired `20260908T094021-295714`, 2662.549 s; `813a677` (7g documents)
fired `20260908T133307-609373`, 3149.067 s; `a86b59d` (7g close-out) fired `20260908T211907-15573`,
2660.227 s. The Stop hook now runs `.claude/hooks/stop-check.sh` instead of `gauntlet stop-check`
directly. The wrapper hashes the gated tree — the sha256 over the `sha256sum` lines of every
tracked and untracked, non-ignored file under `src`, `tests`, `features`, `mutants`,
`gauntlet.toml`, `gauntlet.lock.json`, `pyproject.toml`, `.claude/settings.json` and
`.claude/hooks`, sorted under `LC_ALL=C` — and compares it with the hash in
`.gauntlet/last-green-tree`, saved beside the run id and `at` of the last green stop-check's
acceptance `gate.finished` line. Equal means one printed line naming that run and exit 0; anything
else means `gauntlet stop-check --max-attempts 1` with the hook payload passed through on stdin,
and the wrapper exits with its code. Two properties keep this safe. First, any byte in a gated or
config path is a full run: a file added, edited, renamed or deleted under those paths changes the
hash, and a deleted tracked file goes further, making `sha256sum` fail under `pipefail` so no
hash exists at all. Second, every failure of the wrapper is a full run, never a skip: no
repository root, no hash, a missing record, a corrupt record, a record whose hash matches but
whose run id or time is blank. The record is written only after a stop-check that exited 0 *and*
whose run — the run id on the newest acceptance `gate.finished` line — has no `gate.finished`
line with `"passed": false`, finished as many distinct gates as the previous record's run
(eleven on the first run), and is newer than the recorded run id, because `stop-check --help`
says it also exits 0 with a systemMessage once its retry cap is reached. The first version of
this wrapper checked only that the newest acceptance line passed, and the very first stop-check
under it, run `20260908T225412-163184`, protect red and the other ten gates green, was recorded
as green; the record was pasted, deleted, and the condition widened to the whole run. Hand-tested 2026-09-08 with `GAUNTLET_STOP_DRY=1`: no record, a byte in
`src/`, a corrupt record, and a matching hash with blank run fields each run; a matching record
and a byte in `QUEUE.md` only each skip. In a scratch repository with a fake `gauntlet` on PATH:
exit 2 writes nothing, exit 0 with no new acceptance line writes nothing, exit 0 with a new
passing line writes the record, the next call skips naming that run, and deleting a tracked file
runs. One consequence for the pair `CLAUDE.md` carries: the hook budget now bounds only turns
that touched a gated path, and the four runs above are the ones it stops paying for.

### An expensive file-rewriting gate inside an automatic retry loop is the highest-risk state here

The acceptance gate mutates spec files in place and takes ~230s. On a reopening it is *guaranteed*
red between the spec draft and its implementation. The stop hook retries a failing run — observed at
2, 5, and 7 attempts across item 4g and 4j sessions, against states that could not go green.

Whether that is harmful depends entirely on which stage fails. An unapproved-spec failure
short-circuits at the approval check in ~0.001s, before any mutation runs, so retrying it is merely
slow. A failure that reaches the mutation pass rewrites the file once per attempt, and each attempt
is an opportunity to be interrupted mid-mutation — which is exactly how the corrupted spec of
2026-08-17 was produced.

So the hazard is not "the loop retries," it is **"the loop retries something that rewrites files."**
Instructing an agent to run the gate once does not prevent it; the loop is the harness's, not the
agent's. If the attempt limit is configurable, set it to 1 for reopening work. Otherwise, sequence
so the guaranteed-red state fails at the approval stage rather than the mutation stage — draft the
spec, leave it unapproved, and let the cheap failure be the one the loop repeats.

### The toolchain that produces every gate result was undeclared until 2026-08-18

`pyproject.toml` declared no dependencies at all — not `dependencies`, not
`optional-dependencies`. Every tool the gates need had been installed into one venv by hand and
recorded nowhere, so a fresh clone could not run `gauntlet check` and none of this project's
recorded gate results were checkable by anyone, including their author. `gauntlet doctor` does not
cover this: it verifies tooling is present in the current environment, not that the environment can
be rebuilt.

That matters here more than in an ordinary project, because the gate numbers *are* the evidence.
Every figure in `QUEUE.md` — 213/213, 100% / 217 killed, 67 reviewed-equivalent — is a claim about
the domain, and a claim nobody can reproduce is a weaker thing than it looks.

Rebuilding the venv from scratch with current tool versions reproduced all three exactly, which
turned those numbers from recorded into reproduced. Direct tools are now a `dev` extra in
`pyproject.toml` and the exact versions are pinned in `requirements-dev.txt`. **Note that the
package itself is never installed** — the root `conftest.py` puts `src/` on `sys.path` — so the
install path that matches how this project actually runs is `uv pip install -r
requirements-dev.txt`, not an editable install of `claimgate`.

