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

**Measured cost on 2026-08-14, not the round figure it might sound like.**
Three stop-check runs fired that day against conditions no agent action could
clear: two (17:25:25, 17:28:32) against item 4c's post-implementation state —
7 stale approvals, 5 unreviewed survivors — and one (22:14:13) against item
4d's freshly-drafted, unapproved `siu_indicators.feature`. The two stale/
unreviewed runs cost 172.8s and 158.4s of `acceptance` gate time each, because
that condition does not trip the gate's early-return path (see "A green gate
sometimes means nothing was checked" above) — mutation still runs in full.
The unapproved-spec run cost 0.001s, because that condition does. Total
`acceptance` time across all three: 331.2s, not the roughly-twelve-minutes a
flat "~4 minutes × 3 runs" estimate would suggest — the retry cost of this
finding is not uniform across its three qualifying conditions, and a modified
spec is the cheap one to retry against, not the expensive one.

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

**Confirmed on the unapproved case too, not just modified.** A brand-new,
never-approved spec (`features/carrier_configuration.feature`, item 5a, first
new feature file since `fc86add`) produced the identical text: `is not
approved. A human must review it and run \`gauntlet lock\` before it can be
relied on.` The remedy is generated from one code path covering both
conditions, so the wrong command isn't specific to a spec that changed after
approval — any spec the acceptance gate hasn't approved, new or modified,
carries this same incorrect instruction.

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

**Caveat, verified against the log rather than assumed: "no `acceptance`
`gate.finished`" only identifies a kill relative to the gate set configured
at the time, not on its own.** Five of the 100 stop-check runs
(`20260802T193624-77280`, `20260802T200600-79161`, `20260802T203202-80878`,
`20260802T210444-84044`, `20260802T211146-84454`) end at `crap` with no
`duplication`, `mutation`, or `acceptance` — the same shape as a kill, read
naively. They are not: seven `command=check` runs that same evening
(16:24:30 through 21:16:18 on 2026-08-02) share the identical seven-gate
selected list (`protect`, `static`, `size`, `complexity`, `tests`,
`coverage`, `crap`) and every one has a matching `run.finished` — `crap` was
the last gate configured that day. `duplication`, `mutation`, and
`acceptance` first appear together in a run's gate list at 22:10:12 the same
evening; `boundary` follows on 2026-08-04. Applied without this caveat, the
method that correctly found the 2026-08-11T11:17 kill above reports five
more that are not — a stop-check run's completeness has to be checked
against a `command=check` run.started/run.finished pair from the same era,
not against today's gate list.

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

### Mutation cannot see a fixed Given, so a spec can state a rule it never protects

`_literal_mutants` returns `[]` for any scenario where `is_outline` is true, and `LITERAL_PATTERN`
matches only quoted text, single-quoted text, or a bare number. Two consequences that are not
obvious from the outside:

- In a **Scenario Outline**, only Examples cells are mutated. A fixed `Given` line above the table
  is never mutated no matter how it is written — quoting does not help, because the outline branch
  returns before any step is examined.
- In a **plain Scenario**, an unquoted word is invisible. `Given claimant name is required by
  configuration` yields nothing; `Given claimant name is "required" by configuration` yields one
  mutant.

Item 4g's first draft hit both at once. It stated the configuration under test — the entire subject
of the item — as unquoted fixed `Given` lines above an outline. The scenarios read as full coverage
of both configuration states and the engine generated zero mutants against either, so no gate could
ever have reported the gap. The count went up (116 -> 122), which made it look like coverage had
grown.

**Anything a spec intends mutation to protect has to be a quoted Examples cell.** When reviewing a
draft, check the mutants that exist against the values the scenario is *about*, rather than reading
the count. A rising total says nothing about which values moved.

This is the "a green gate sometimes means nothing was checked" failure reached from a new
direction: not a gate skipped, but a gate that ran fully against a target it could not perceive.

### A same-outcome column is sometimes the point of the rule, not a table defect

Item 4e's fix for surviving mutants was to mix outcomes across an outline's rows. That does not
help when the *rule itself* is symmetric across a column's values. Item 4g's combined outline
carried a `loss_type` column holding only `injury` and `liability`, which the rule treats
identically by design, so every mutation in that column was an `injury <-> liability` swap that no
outcome could distinguish — 11 rows, 11 survivors, unavoidable inside that shape.

Two things were measured before choosing:

- **Adding discriminating rows makes it worse.** Adding a Section I row took the outline from 77
  mutants / ~31 survivors to 84 / ~36; adding an unrecognized row as well took it to 91 / ~41. The
  engine kept selecting a Section II value as the substitute, so the extra rows added survivors in
  the other columns without touching the eleven.
- **Splitting the outline removes the column.** Two six-row outlines, one per loss type, with the
  loss type fixed in a `Given`: 72 mutants, ~24 survivors, and the symmetry becomes a visible fact
  of the spec instead of eleven ledger entries.

The deciding argument was not the count. `gauntlet mutant approve` scopes only by feature file and
`--scenario`, so every survivor in one scenario shares one reason and every re-approval overwrites
all of them — item 4c's recorded failure, where one inherited reason carried four inaccuracies
forward invisibly. Thirty-one survivors in one scenario would have needed a single reason spanning
three unrelated equivalence arguments. **When choosing an outline's shape, count the argument types
a shared approval reason would have to cover, not just the survivors.**

Survivor counts in this entry are simulated against the rule, not measured — survivors cannot be
measured until the implementation exists.

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

### `registry.save` is not atomic, and the ledger is the one artifact no gate can rebuild

`registry.save` ends in `path.write_text(...)` — no temp file, no atomic rename. An interrupt during
`gauntlet spec approve` or `gauntlet mutant approve` can leave `gauntlet.lock.json` truncated, and
every other artifact in this project can be regenerated while that one cannot: it is the record of
human judgment.

Procedural mitigation, since the write is not ours to fix: commit the ledger immediately before and
immediately after an approval run, and never invoke an approval from a pasted multi-command block —
a stray interrupt landing between two pasted commands is what makes this reachable at all. If
`json.load` on the ledger raises, `git restore gauntlet.lock.json` recovers to the last commit and
the approvals since then must be re-run.

`mutant approve` prints one line per stamped mutant as it goes. That output is a usable scope check:
the expected count, at the expected line numbers, naming the expected scenario, is the confirmation
that `--scenario` matched what was meant. A short count is a mismatch and a long one is
over-approval.

### A missing project venv reports as a missing module, from an interpreter you did not choose

Gauntlet's `interpreter()` resolves in order: an explicit `python` in `gauntlet.toml`, then the
project's local `.venv`, then `$VIRTUAL_ENV`, then Gauntlet's own interpreter. Every tool the gates
shell out to — `pytest`, `coverage`, `mutmut`, `mypy`, `ruff` — is invoked as `<that interpreter> -m
<tool>`, so all of them must live in whichever one wins.

When ClaimGate's `.venv` went missing on 2026-08-18, resolution fell through to the last entry and
the mutation gate reported:

    ERROR: /home/.../uv/tools/agent-gauntlet/bin/python3: No module named mutmut

The message names the module. The cause is the venv. Nothing in the output says an interpreter
fallback occurred, and the path is only a clue if you already know the resolution order — so the
obvious reading, "mutmut got uninstalled," sends you to fix the wrong environment. Installing mutmut
into Gauntlet's tool venv would even have made the error go away while leaving every other gate
running against the wrong interpreter.

**Diagnose it from the path, not the module.** If the interpreter in the error is Gauntlet's own,
the project venv is the problem regardless of which module is named. `ls .venv/bin/python` settles
it in one command.

The gate failed correctly and that is worth noting separately: it reported `actual=None` and
surfaced the error, rather than scoring zero or skipping. A mutation gate that passed quietly when
its tool was missing would be the "green gate that checked nothing" failure in its purest form.

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

**Annotation, 2026-08-15.** Two names in this entry are dead: `_is_recent_inception`
became `_evaluate_recent_inception` on 2026-08-09 (`33d602b`), and `inception_date`
became `coverage_start` in item 4d. The claim that no scenario anywhere exercises an
inception date after a loss date was true when written and false from 2026-08-09,
when item 2 added exactly that scenario. Left in place as the historical account.

### A revisit trigger keyed on a symbol name goes inert when the symbol is renamed

`_is_recent_inception` became `_evaluate_recent_inception` on 2026-08-09, in
`33d602b`, the same commit that implemented item 2. The old name survived six days
and four queue items: 23 occurrences in `gauntlet.lock.json` including the REVISIT
TRIGGER on all eleven `triage.feature` approvals, plus `features/siu_indicators.feature`,
`ASSUMPTIONS.md`, `QUEUE.md`, and this file. Nothing catches it — the code-mutation
gate does not read approval reasons, and the acceptance gate compares locators and
digests only. Item 4c's re-approval corrected four other inaccuracies in that same
reason text and left the dead symbol standing.

A revisit trigger exists to be found when the thing it guards changes. Keyed on a
name, it is findable only until someone renames the name — and a rename is exactly
the kind of change that should fire it. State the trigger as behaviour ("the
rejection of a coverage-start date later than the loss date"), and name the
implementing symbol only as a locating aid, with a verified-on date.

A second-order cost showed up while verifying this. The check written to confirm the
correction had landed was a string-absence test — "the reason must not contain
`_is_recent_inception`" — authored by whoever wrote the replacement prose. It failed
on the correction itself, because the correction's whole purpose is to name the dead
symbol and mark it dead. An absence test cannot separate a name used as a live
reference from a name recorded as retired. Approval reasons are the one artifact in
this project no gate can validate, and they are prose; a check on them has to be
read, not grepped. Where a mechanical check is wanted, test the ledger's structure —
key churn, digest pairing, which scenarios were re-stamped — and leave the prose to a
human.

### The code-mutation score cannot value a test that guards a cross-module consistency invariant

Item 4h (`QUEUE.md`) added a test asserting that triage's high-severity loss types are a subset of
validation's recognized loss types — `_HIGH_SEVERITY_LOSS_TYPES <= RECOGNIZED_LOSS_TYPES`, two
frozensets in two different modules with no prior relation enforced between them. Killed count was
204 before the test and 204 after, measured by isolating the mutation gate and running it against
both versions rather than reading the number off a gate summary.

Two things cause that, and neither is specific to this test. Killed count counts killed mutants, not
killers: it moves only when a mutant that used to survive gets killed by the new test, or a new
mutant gets generated and killed. A test that duplicates coverage other tests already provide moves
nothing, no matter how meaningful the assertion is on its own terms. And the state this particular
test guards — `RECOGNIZED_LOSS_TYPES` and `_HIGH_SEVERITY_LOSS_TYPES` disagreeing while every
scenario in both `validation.feature` and `triage.feature` keeps passing — is only reachable by a
coordinated edit across two files: drop a value from one frozenset while leaving the other alone.
Single-point mutation, which is what the mutation gate generates, never produces that; it mutates one
site at a time, inside one file, against one spec.

A zero delta on the mutation score is therefore not evidence a test was unnecessary. For a test that
guards a cross-module invariant, it is the expected result, not a signal of anything — the gate
cannot generate the coordinated mutant that would exercise it, so it can never register the test's
value as a killed count. Judge such tests on the coordinated edit they would catch if someone made
it, not on a score built to measure single-point mutants.

### Digest pairing distinguishes a moved mutant from a replaced one

A rename can leave a mutant's count unchanged while every locator under it changes — item 4d's
vocabulary rename moved six approvals to new locators without adding or removing a mutant. Equal
counts before and after cannot show that: six removed and six unrelated ones added would print the
same delta as six moved. What showed it was matching each removed approval's key to an added one by
identical digest (the mutant's `original->mutated` signature, unaffected by the locator's rename),
confirmed before the ledger commit rather than assumed from the rename. Six matched pairs meant six
mutants moved, not six replaced by six different ones. Reusable whenever a rename moves locators:
count parity is consistent with either story, and only digest pairing tells them apart.

### Comment inertness is confirmed by locator identity, not count parity

Item 4f's comment-only edit was scheduled on `d344ab3`'s count match — before and after, the same
number of mutants. Count parity is the weaker claim: it's consistent with the comment edit having
swapped one mutant for a different one at the same total. Measuring the full locator list instead
showed it byte-identical across the edit, not just equal in size — the stronger claim, and the one
actually relied on to schedule the item as comment-only, spec-only, zero ledger churn. Where a count
match is the only thing checked, "unchanged" is an inference; where the locator list matches
element-for-element, it's a fact.

### An advisor's measured number goes stale the moment the thing measured is amended

Three times in one session, a number supplied to this project was correct against an earlier version
of a spec and wrong by the time it was used, because the spec had already moved: 112 quoted where the
current draft had 111, after a scenario deletion proposed in the same message that carried the count;
ten avoided approvals quoted where the number was thirteen, after the recognized loss-type set the
estimate was built on grew from ten values to fourteen before the estimate was finalized; and a step
chosen for a new assertion without first reading the guard already written into its sibling step,
producing a plan built on what the step was assumed to do rather than what it did. None of the three
was caught by the number's author re-reading their own figure — each was caught here, by re-deriving
the number against the spec's current state before acting on it. The number a source supplies is a
floor to check against the artifact as it stands now, not a target to carry forward unchecked. Measure
last, after every amendment, not first and once.

### A failing test's parametrize id does not identify which cell a mutation injected

An interrupted acceptance run on 2026-08-17 left `features/duplicates.feature` carrying
`matching_claim_id: CLM-1001 -> ""` on the first row of "Matching against a single existing claim".
The failure surfaced as `test_matching_against_a_single_existing_claim[HO-1234567-2026-06-01-fire-]`
plus `assert ('CLM-1001',) == ()`.

pytest-bdd builds that id from the example row as it stands *after* mutation, so it is not
one-to-one with a mutant. Two distinct mutants in that scenario produce the identical id: the
first row with its expectation blanked, and the last row (`HO-1234567|2026-06-01|water_damage|`)
with its loss type substituted to `fire`. Reading the id alone, the advisor identified the second
and stated it as a prediction; `git diff` showed the first. The mistake cost nothing here — the
recovery is the same file either way — but the method would misdirect anyone trying to work out
which approval or scenario was implicated before restoring.

Identify an injection from `git diff`, or by matching the signature against
`mutation.mutants()`'s output for that file — never from the test id. A cheap visual tell: the
engine writes the substituted value without re-padding the cell, so an injected empty cell is
narrower than the genuine empty cells in the same column.

Also confirms two documented behaviours in one event: every killed run dies inside `acceptance`
and leaves a corrupted spec, and `_discriminating_alternatives` drew the substitute (`""`) from
other rows in the same column, as specified.

### A long `--reason` belongs in a file, and a smart quote will eat the command silently

Three consecutive `gauntlet mutant approve` invocations failed before anyone noticed why: the
`--scenario` argument had a straight opening quote and a curly closing one (U+201D), so the shell
never saw the string terminate, dropped to its `>` continuation prompt, and swallowed `--reason`
along with everything after it. Nothing was approved and nothing errored — the only symptom was a
prompt that looked like it was waiting for more input.

Two habits remove the whole class:

- **Put the reason in a file** and pass `--reason "$(cat /tmp/reason.txt)"`. This project's approval
  reasons run to a paragraph or more and contain apostrophes, commas, and hyphens; inlining them
  makes quoting the dominant failure mode of an operation that should be routine.
- **Type the quotes around a scenario name by hand.** Anything routed through a document, a chat
  client, or an editor with smart-quote substitution can silently convert them, and the resulting
  failure does not name quoting as the cause.

Verify by outcome rather than by absence of error: `mutant approve` prints one line per stamped
mutant, so a silent command is a command that did not run.

### Predicting a survivor count is a different act from measuring one, and both are useful

Survivors cannot be measured until the implementation exists — the gate has to run the mutated spec
against real code. But they can be *simulated* beforehand by enumerating `mutation.mutants()` and
evaluating each mutated row against a model of the rule the spec describes. Done before a draft is
approved, that turns "how many equivalence judgments will this cost the human" into a number
available while the shape can still change.

Used three times on item 4g and once on 4j, it changed the design each time: a combined outline at
~31 survivors became two outlines at ~24, and a combined policy-number outline at ~13 became a split
at 3 and 0. On implementation the gate reported exactly 24 and exactly 3.

**Label which one a number is.** A simulation and a measurement are equally useful and not
interchangeable: a simulation encodes a model of the rule, so a large gap between prediction and
gate output means the implementation and the specification's intent have diverged — which is
information, but only if the prediction was recorded as a prediction. A guess reported as a
measurement destroys that signal.
