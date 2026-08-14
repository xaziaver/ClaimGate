# Harness findings

How Gauntlet behaves in practice, and what working under it has taught us —
discovered by building ClaimGate end to end under the gates, not assumed.

This file is scoped to what someone *using* the current version of Gauntlet
needs. Proposals to change Gauntlet itself live in `gauntlet-findings.md` in
the agent-gauntlet repository and are deliberately not here: an agent
implementing under the gates needs to know how the harness works today, not how
it might work later.

**Gauntlet is deliberately NOT modified during this project.** The harness and
the work it gates must not move at the same time, or gate results stop meaning
what they appear to mean. If something here becomes genuinely blocking rather
than merely annoying, escalate it — do not work around it quietly.

| Section | What to do with it |
|---|---|
| How the harness behaves | Operational facts about the current version. Act on them rather than rediscovering them |
| Process and technique | Lessons about working under the gates, not about the gates |

A few entries below still carry a **Routes to** line. Those are historical;
routing now happens in `gauntlet-findings.md`.

## How the harness behaves

Facts about the current version, stated as behaviour rather than as complaints.
Each was established by reading Gauntlet's source or by watching it happen, not
by inference — several earlier claims in this document written from reasoning
about how a tool must work turned out to be wrong, and those retractions are
the reason this section exists.

### A mutation score is only meaningful from a cold run when the commit adds or removes code

Gauntlet re-executes `mutmut run` as a fresh subprocess on every invocation, but
mutmut's own `mutants/` cache is separate and can be stale in both directions. On
a test-only change it has reported a false PASS — better than reality. On a
commit adding a new function it has reported false *survivors* — worse than
reality, on mutants it had never actually evaluated. Only the second direction
gets noticed, because someone eventually asks why an implausible mutant
survived. Clear `mutants/` and rerun before quoting a score on any commit that
adds or deletes a function or a test.

### A gate failure awaiting a human decision is not a failure to retry

An unapproved or modified spec, a stale or unreviewed mutant approval, and a
dangling approval key are all conditions no agent action can clear. The Stop
hook re-runs the full gauntlet regardless of what the agent decides — this has
been confirmed with the agent explicitly holding for a human decision and the
loop still spending its budget — so recognising the state and stopping does not
prevent the retries, but it does prevent wasted work. Report the condition once
and stop.

Note that the spec-lock-before-implementation rule in `CLAUDE.md` *guarantees*
this state on every reopening. It is normal, not a signal that something is
wrong.

### Command ownership, and one remedy that names the wrong command

Yours: `gauntlet check`, `verify`, `status`, `doctor`, `events`. The human's:
`gauntlet spec approve`, `mutant approve`, `mutant prune`, `review`, `lock`.

The acceptance gate's failure text for a modified spec instructs the reader to
re-approve with `gauntlet lock`. That is wrong. `gauntlet lock` re-approves the
current content of the protected paths — `gauntlet.toml`,
`gauntlet.lock.json`, `.claude/settings.json` — which is the guardrail against
threshold tampering, not the spec-approval command. The correct command is
`gauntlet spec approve`, and it belongs to the human. Acting on that remedy
literally would not approve the spec and would re-baseline the protection.

### Acceptance mutation does not see everything

`Feature.background` is never passed to `mutants()`, so Background steps are
never mutation targets in any scenario. `_literal_mutants` returns early for
outline scenarios, so a value hardcoded in a fixed `Given` above an `Examples`
table is never a target either. The consequence is counterintuitive: the values
a feature file leans on hardest are often the ones nothing checks. Both facts
matter when estimating what a change will disturb — they are the difference
between a naive blast-radius count and a real one.

### Mutant counts are checkable directly, without a gate run or an approved spec

The acceptance gate's approval stage skips mutation entirely on an unapproved
or modified spec (see "A green gate sometimes means nothing was checked"
below), which blocks the normal path to a mutant count exactly when a
reopening's draft most needs one — before the human has approved it. The
mutation engine needs no gate wrapper, though: `from gauntlet.acceptance
import gherkin, mutation` (importable straight from the `agent-gauntlet`
editable install's `src/`, not through the `gauntlet` CLI) and
`mutation.mutants(gherkin.parse(<feature file text>))` returns every candidate
mutant for that file, group-able by `.scenario` for a per-scenario count —
e.g. `Counter(m.scenario for m in mutation.mutants(...))`. Confirmed a
comment-only spec edit changed nothing structural in under a second this way,
with no gate run and no approval required first.

### A mutant has two identities, and one of them moves when a neighbouring row changes

`locator` is `scenario|kind|context` — for an example mutant, the mutated
column's header plus every value in that row. It is deliberately structural, so
unrelated edits do not lapse approvals. `signature` is `original->mutated`, and
it is the content whose hash an approval records. An approval binds both.

The substituted value is not fixed: `_discriminating_alternatives` picks it from
other rows *in the same column*, preferring the row that differs most elsewhere.
So changing any value in a column changes the signature of every mutant in that
column — re-opening approvals on rows nobody edited. When estimating what a
value change will disturb, the unit is the column, not the row.

### `gauntlet mutant approve` stamps every survivor in scope

Without `--scenario` it applies to every surviving mutant in the file. With
`--scenario` it applies to every survivor in that scenario — including ones
already approved, whose reason it overwrites. Two consequences follow:

- It is the only way to revise an approval reason, since a reason cannot be
  edited in place and prune only drops approvals whose mutants no longer
  survive. Re-approving the scenario rewrites them all.
- The number the gate prints as unapproved is smaller than the number `approve`
  will stamp. A reason sized to the gate's figure will silently mis-describe the
  rest. Size it to every survivor in the scenario.

### Approval reasons decay in ways no key can catch

Two modes, both observed. A reason that quotes example data goes false when a
vocabulary pass changes that data, while its locator stays valid — so describe
a row by its **role** ("the policy-mismatch row"), never by its contents. And a
reason that asserts something about the wider suite ("no scenario anywhere
exercises X") goes false when a different file gains a scenario, outside any
revisit trigger scoped to this one. State what the approval depends on; date any
claim about the rest of the suite.

### A green gate sometimes means nothing was checked

Three distinct instances, all real:

- The coverage gate reads `.gauntlet/coverage.json` off disk and runs no
  subprocess. When the tests gate errors at collection, coverage can still
  report 100% from an artifact several commits old.
- The acceptance gate's approval stage returns early on failure and skips
  mutation entirely, for every spec — including specs with no approval problem.
  A single dangling key hides the mutation result for the whole suite.
- Unit tests never read feature files. A vocabulary change to a spec leaves the
  unit suite green while it still asserts the values the spec abandoned. No gate
  compares example data across the two layers.

When a gate looks clean, say what it actually exercised.

### Check `git diff` after any interrupted mutation run

The acceptance gate mutates spec files in place and restores them afterward. A
run killed mid-mutation has left an injected literal inside a step definition. A
corrupted spec is indistinguishable at a glance from a real edit, so an
interrupted run is followed by a diff before anything else.

### Every event line carries a run correlation id; runs don't nest, and the log has a size-based ceiling

Every line in `.gauntlet/events.jsonl` is stamped with a `run` id —
`YYYYMMDDTHHMMSS-<pid>`, assigned once per process in `Log.__init__` and
written by `build()` (`events.py:60-67`). Runs are separate OS processes and
never nest, so pairing `run.started` to `run.finished` by that id is exact —
no FIFO- or depth-matching heuristic is needed, and none should be trusted
over it. `events.read()` only parses `.gauntlet/events.jsonl` itself; the file
rotates at 5MB to `.jsonl.1`, which `read()` never opens. `gauntlet events
--limit 0` is therefore all of the *current* file, not all history — a
rotation silently drops older runs from anything `events` reports.

### A lock-rejected run and a killed run both orphan `run.started` — `gate.finished` tells them apart

`check` emits `RUN_STARTED` (`cli.py:151`) before entering `_locked_run`. When
another run already holds the project lock, `_locked_run` catches
`RunInProgressError`, echoes a message, and raises `typer.Exit(EXIT_OK)` — so
`_finish` (`cli.py:77`, the only place that emits `RUN_FINISHED`) never runs.
A lock-rejected run therefore looks like: `run.started`, zero `gate.finished`
events, exit 0, having executed nothing. A killed run looks like:
`run.started` plus one `gate.finished` per gate that completed before the
kill. The `gate.finished` count is what tells the two apart — an orphaned
`run.started` alone doesn't say which happened. This project's log has both:
5 lock-rejected runs in 59 seconds on 2026-08-13 (14:16:01-14:17:00), and,
of the runs that emit `run.started` at all, 4 killed runs (2026-08-02T21:53,
2026-08-08T11:14, 2026-08-11T22:44, 2026-08-13T23:14:34) — a 5th, found by a
different method, is recorded below. Commit `9927dda` that same afternoon
("limit repeated gauntlet check attempts") reacted to the lock-rejection
burst without diagnosing which of the two failure shapes it was. A
lock-rejected run is a third way to get a meaningless zero, alongside the
pipe trap below and the `--changed` scoping question further down.

### `stop-check` runs the full gauntlet but never emits `run.started` or `run.finished` — a third run shape, invisible to any pairing keyed on either

Verified against source, not inferred. `events.RUN_STARTED` is emitted in
exactly one place in the whole package: inside `check` (`cli.py:151`), before
`_locked_run`. `stop_check` (`cli.py:220` — the Stop hook's command;
`.claude/settings.json` wires it to `gauntlet stop-check --max-attempts 1`)
calls `_locked_run(root, lambda: runner.run_full_gauntlet(...))` at
`cli.py:235`, under the same project lock `check` uses, but its body never
calls `log.emit(events.RUN_STARTED, ...)`, and it never reaches `_finish`
(`cli.py:74`, the only place `RUN_FINISHED` is emitted — that call is local
to `check`, `cli.py:153`). `run_full_gauntlet` delegates to the same
`runner.run_gates` that `check` uses, so a stop-check run still emits one
`gate.finished` per gate, correctly stamped with the run id `Log.__init__`
assigns per process — it just never brackets them with a `run.started` or
`run.finished`.

This is not the lock-rejected/killed distinction above — both of those
presuppose a `run.started` to anchor the analysis, and a stop-check run has
none at all. It is a complete run with no boundary event on either end,
findable only by grouping `gate.finished` events by `run` id and checking
which ids have no matching `run.started`.

**Measured, not estimated: this project's own run-count entries above
undercounted by exactly this blind spot.** Grouping
`.gauntlet/events.jsonl` by `run` id: 468 distinct runs have at least one
`gate.finished` event; only 373 have a matching `run.started`. The other
100 are stop-check runs — about 21% of every full-gauntlet-shaped execution
in this project's history — invisible to any count built by pairing from
`run.started`. One of the 100, `20260811T111732-289837`, completed 10 gates
(`protect` through `mutation`, `boundary` present) with no `acceptance`
`gate.finished`: a killed run at 2026-08-11T11:17, distinct from the
2026-08-11T22:44 one already on record, uncounted until now because it was
never findable by scanning for orphaned `run.started` events — it never
emitted one to orphan. It is why the killed-run counts in the entry above and
the entry below are five, not the four either would have reported on a
`run.started`-only scan.

### Every killed run died inside the acceptance gate

All five known killed runs in this project's history — the four found by
scanning `run.started`/`gate.finished` pairs (2026-08-02T21:53,
2026-08-08T11:14, 2026-08-11T22:44, 2026-08-13T23:14:34) plus the
stop-check-only kill at 2026-08-11T11:17 found above — died after completing
every other gate through `mutation`, inside `acceptance`. Not coincidence:
acceptance is roughly 98% of a full run's wall time (see below) and the only
gate that mutates spec files in place. A killed `gauntlet check` (or
`stop-check`) corrupts a spec on essentially every occurrence, not
occasionally — treat any killed run as a corrupted-spec event by default,
not a maybe.

### `gauntlet check`'s verdict is an exit status, not its printed text

`gauntlet check` signals pass or fail through its exit code (`cli_support.py:19`:
`EXIT_OK, EXIT_CONFIG_ERROR, EXIT_GATE_FAILURE = 0, 1, 2`; `cli.py:98`:
`raise typer.Exit(code=EXIT_OK if ok else EXIT_GATE_FAILURE)`) — 0 on a passing
gate, 2 on a failing one. `CLAUDE.md`'s own recommended form,
`gauntlet check 2>&1 | tail -25`, pipes that through `tail`, and it is `tail`'s
exit status — always 0 on a normal read — that `$?` reports afterward. A run
reported as "exit code 0" through that pipe says nothing about the gate; only
the printed verdict (`GAUNTLET PASSED` / `GAUNTLET FAILED`) does. `set -o
pipefail` recovers the real status if the exit code specifically is needed;
otherwise read the verdict line, not `$?`.

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

### The acceptance gate's wall time is growing, not fixed at ~150s

Across 162 acceptance-gate runs in the log, the maximum observed is 260.3s,
and the trend is upward, not flat: the four most recent runs measured 186.2s,
174.1s, 208.2s, and 260.3s. Budget 300s as a floor for any tool timeout
wrapping `gauntlet check`, and expect that floor to keep rising as the suite
grows — don't quote a fixed number here again without rechecking the log.
The exposure isn't evenly distributed: the Stop hook already allows 600s, and
the `PostToolUse` hook only ever runs the fast gates (`static`, `size`,
`complexity`) at a 60s budget, neither of which is at risk. Every killed run
in this project's history was an agent-issued `gauntlet check` through `bash`,
cut off at whatever that tool call's own timeout happened to be — that is the
timeout that needs raising, not the hooks'.

### `scope = "changed"` in `gauntlet.toml` never reaches the mutation gate — but not because `--changed` goes unused

`--changed` is passed constantly: `.claude/settings.json`'s `PostToolUse` hook
runs `gauntlet check --gates static,size,complexity --changed` on every edit,
and the log carries 243 such runs. The narrower true claim is about which
gates that hook selects, not about whether `--changed` is ever used: those 243
runs are scoped to `static`, `size`, and `complexity` and never include
`mutation`, so `config.get("scope")` (`gates/mutation.py:55`) is never even
evaluated for them. Every run that *does* include the mutation gate is a
full, non-`--changed` `gauntlet check` (the Stop hook, or an agent-issued
`check`), so the `213 killed` figures quoted throughout this project's history
are full-project for that reason — not because `--changed` is inert. If
`--changed` were ever combined with the mutation gate, its base is still `git
status --porcelain -uall` — working tree against `HEAD`, not commit against
commit — so a run issued straight after a commit, with a clean tree, would
find no changed files and the gate would report passed, vacuously, with
nothing actually mutated.

## Process and technique

Lessons about working with the harness rather than about the harness itself.

### No gate catches inherited framing

**What happened.** `validation.feature`'s original narrative asserted the system exists so that
"only claims the carrier can legally accept enter the queue" — the opposite of the system's actual
behavior. `siu_flags.feature`'s title and narrative characterize its output as fraud conclusions.
Both were written in phase 1, approved, and then carried forward unexamined through every
subsequent gate run until a structured design review looked at the prose rather than the
assertions.

**Why it matters.** Every configured gate checks behavior against assertions. None of them reads a
`Feature:` narrative or a scenario title for whether it accurately describes what the system does.
The inherited, unchanged parts of an approved artifact are the least-scrutinized parts of it,
precisely because nothing flags them as needing a second look.

**What would address it.** No gate mechanism suggests itself here — this is a case for periodic
human re-reading of approved specs' prose, not just their assertions, independent of whether the
assertions still pass.

### Ordering assertions can pass without a sort existing

**What happened.** A specification asserting that output appears in a canonical order is satisfied
by an implementation that performs no sort at all, if the code's natural check-evaluation order
happens to coincide with the declared canonical order.

**Why it matters.** Mutation testing cannot distinguish "correctly sorted" from "coincidentally
already in the right order" unless a test scenario exists where the two orders would actually
differ. Without one, deleting the sort is a mutant nothing catches.

**What would address it.** A general technique, not specific to this project: implement checks in
an order deliberately different from the declared canonical output order, so the sort is the only
thing producing the correct result and a mutant removing it dies. Worth a comment at the point of
implementation, since a future maintainer aligning the two "for clarity" would silently remove the
only thing killing that mutant.

### Unverified rules silently do nothing

**What happened.** `.gitignore` had a trailing comma on every line (`.venv/,` instead of `.venv/`)
from the start of the project. Each pattern's trailing comma became part of the literal pattern
text, so every rule matched nothing. Build artifacts, coverage databases, and a full duplicate
`mutants/` tree were tracked in git for the project's entire history as a result.

**Why it matters.** Same shape as the orphaned thresholds above: a rule that nobody checked,
quietly having no effect, for as long as nobody looked. A `.gitignore` that "looks right" and a
threshold with a rationale that "sounds right" fail the same way — both pass casual inspection and
neither was ever tested against what it was supposed to do.

**What would address it.** Any rule capable of silently matching nothing needs a positive
verification step, not just a visual read. For `.gitignore` specifically: `git check-ignore -v`
against a real target for every pattern, run once and actually inspected, rather than trusted
because the syntax looked plausible.

### A branch pointing at an old commit is not a branch

**What happened.** Work moved off `main` by creating `reopening/triage-siu-queue` at the commit
immediately before `main` reverted `triage.feature` back to its pre-draft content. That commit was
already part of `main`'s own history, so the new branch ref had zero unique commits — the draft
survived only because an ordinary ancestor commit happened to still contain it, not because
anything on the branch asserted it as a change.

**Why it matters.** Nothing in git recorded that a draft was ever made. A branch in that state looks
identical, from `git log <branch>`, to a bookmark on `main`'s own line — because it is one. Any
merge or rebase that pulls `main` forward resolves per-file based on which side actually changed
content since the merge base; a branch with no unique commit for a file has, by definition,
"not changed" it, so a plain merge takes `main`'s side silently, with no conflict and no warning.
That is precisely what an earlier dry-run merge in this session did to this exact file before the
problem was diagnosed.

**What would address it.** Moving work off `main` onto a reopening branch is only complete once the
branch carries a commit that is uniquely its own for the file(s) being protected. A branch cut at a
commit that also exists on `main`'s line, with no subsequent commit, is not yet "off main" in any
sense git can enforce — it's a label on shared history that depends on `main` never being reverted
past that point. Verify with the equivalent of `git log <branch> ^main` before treating a move as
done: an empty result means the branch has nothing of its own yet.

### State-changing operations need verification after, not only before

**What happened.** Seven occurrences now, across multiple sessions. Two tool
timeouts killed a `gauntlet check` run mid-mutation and left corrupted source
(see "Tool timeouts, as their own named sub-case," below); a `git checkout
<branch> -- .` pulled branch files onto `main`'s working tree while still
checked out on `main`; and, in the same session as the branch-pointing-at-an-
old-commit finding above, a `git merge` that resolved one whole Gherkin rule
to `main`'s reverted (buggy) content with **no conflict marker at all**,
while a different rule in the same file conflicted normally two lines later.
Since then: a `git add -A` failed on a stale pathspec after a `git mv`;
`gauntlet.lock.json` was deleted alongside its intended `.bak` in the same
cleanup step (see "Commit the approval ledger before hand-editing it,"
below); and a `git show <ref>:<path> > file` export wrote an empty file on a
non-zero exit with no indication anything had failed (see "A command whose
output you don't read is a command whose failure you won't see," below).
Each was caught only because someone — human or agent — thought to look
afterward; none announced itself.

**Tool timeouts, as their own named sub-case:** a timeout reads, superficially,
like "nothing happened" — the command just didn't finish. It is not the same
as "nothing happened." Treating it as a no-op invites exactly the kind of
silent corruption described above.

**Why it matters.** The git-merge occurrence is the sharpest version of this finding so far: it shows
that even git's own conflict markers cannot be trusted as a complete account of what a merge changed
silently. A merge that reports "CONFLICT" for part of a file can still have resolved a *different*
part of the same file to the wrong side without saying so, because git's line-based diff treated
that region as an unambiguous, non-conflicting change. Trusting "no conflict marker" as "no problem"
in the surviving regions of a partially-conflicted file is exactly as unsafe as trusting a fully
silent auto-merge.

**What would address it.** Run `git status` after any branch, checkout, or gate operation, and treat
an unexplained diff as the finding, not a false alarm — the existing entry in this document said
this. Extending it: after resolving *any* merge conflict, diff the *entire* resolved file against
the intended source (not just the conflict-marked hunks) before staging, since a partial conflict
report is not a complete report. For timeouts specifically: treat them as a category with a known
recovery procedure — diff the working tree, check for a partially-written state, re-run — rather
than as one-off accidents to be individually rediscovered each time.

### A command whose output you don't read is a command whose failure you won't see

**What happened.** `git show <ref>:<path> > file` was used to export a spec for
review. The ref was wrong, so git wrote nothing and exited non-zero — but the
shell redirect created the file regardless. A zero-byte file was uploaded for
review and looked, from the outside, exactly like a successful export.

**Why it matters.** This is the sharpest form of the verify-after finding. The
earlier cases were operations that partially succeeded; this one failed
completely and left an artifact that looked like success. Nothing about an
empty file announces itself.

**What would address it.** Any command whose result is consumed elsewhere gets a
check appended in the same invocation — `&& wc -l <file>` for an export,
`git diff --stat` after an edit, `git log <branch> ^main` after a branch move.
The check costs nothing and converts a silent failure into an obvious one.

**A related substitution.** Asked to export a file at a named ref for review,
an agent instead resolved the ref with `git rev-parse` and read the working
tree, reporting that as the export. The two agree exactly when the tree is
clean — which is exactly when the protocol is least needed — and diverge
precisely in the case it exists to catch. The substitution is invisible in a
transcript unless you notice that `git show <ref>:<path>` never ran. Reading
a file is not exporting it, and appending `&& wc -l` guards only the command
you actually issued.

### Commit the approval ledger before hand-editing it

**What happened.** `gauntlet.lock.json` was hand-edited to remove an orphaned
approval, a `.bak` copy was taken first, and then both the backup and the
ledger itself were deleted in the same cleanup step. Recovery worked only
because the ledger was committed; `git checkout` restored it, and the edit was
redone.

**Why it matters.** A manual edit to the ledger has no undo but git — and the
people making manual edits are by definition doing something the tool has no
operation for, which correlates with being mid-task and not yet committed. The
`.bak` was the right instinct and provided no protection, because it lived in
the same working tree as the thing it was protecting.

**What would address it.** Commit the ledger before hand-editing it, not after.
The commit is the backup; a sibling file in the same directory is not.

### Mutation testing can find unspecified implementation behavior

**What happened.** A surviving mutant on `features/triage.feature` line 71 — set by changing
`inception_date` to a date after `loss_date` — revealed that `_is_recent_inception` guards against a
policy inception date after the loss date (`0 <= days_since_inception <= 30`, not just `<= 30`). No
specification anywhere describes this guard, and no scenario anywhere exercises an inception date
after a loss date; it had been correct by construction, and unasserted, since phase 1.

**Why it matters.** The usual concern this document records is code missing something a specification
requires. This is the inverse: a surviving mutant is not only evidence of a gap in what's asserted, it
can be evidence that the code encodes a rule nobody wrote down — a decision made once, silently, by
whoever first wrote the comparison, that every later reader (human or gate) has taken on faith without
it ever being stated as a rule to agree or disagree with. Approving a surviving mutant as "equivalent"
without checking *why* it survives would have signed off on that silently, not merely skipped a test.

**What would address it.** Treat a surviving mutant's proposed equivalence as a hypothesis to verify
against the code, not a label to accept from the gate's suggestion that one might exist. Where the
mutation crosses a boundary that isn't in the visible example data at all (here: inception after loss,
never inception before loss by a larger margin), that's the case most likely to be hiding an
implementation decision the specification never made — worth tracing to the actual conditional before
approving anything nearby in the same batch.

**Routes to:** Gauntlet's README, "What building this taught us." This is a story about the tool finding something no human and no other gate had, which is what that section is for. Not a work item.
