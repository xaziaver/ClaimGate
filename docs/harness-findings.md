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

### What a locked spec cannot see is found by breaking the implementation on purpose

Item 5e had a rule no phrase in its spec could read — the notice's resolution timestamp must stay
null after a refused resolution — and a decision asserted only in a fixed `Given` inside an
outline, which the engine never mutates. The implementing session stamped the timestamp on
refusals deliberately and counted which scenarios noticed: **none of 21.** That number is the
evidence that the rule needs a unit test, and three other deliberate breakages confirmed the
scenarios do bite where they should. Do this for every rule the design states that the spec's
step vocabulary cannot express, and record the count.

### A mutation score is only meaningful from a cold run when the commit adds or removes code

Gauntlet re-executes `mutmut run` as a fresh subprocess on every invocation, but
mutmut's own `mutants/` cache is separate and can be stale in both directions. On
a test-only change it has reported a false PASS — better than reality. On a
commit adding a new function it has reported false *survivors* — worse than
reality, on mutants it had never actually evaluated. Only the second direction
gets noticed, because someone eventually asks why an implausible mutant
survived. Clear `mutants/` and rerun before quoting a score on any commit that
adds or deletes a function or a test.

**First measured instance of the false-PASS direction, 2026-08-27 (item 5h).** The paragraph above
says that direction is the one nobody notices; this is the run that caught it, and only because a
survivor on a line a scenario already asserted looked wrong. A full `gauntlet check` on the
implementation reported `mutation … score 98.58%, 416 killed, 6 unresolved` and **PASSED** - 98.58%
is far above the 90% floor, so the six were printed as diagnostics on a green gate and nothing asked
for a second look. Clearing `mutants/` and re-running cold showed the warm figure understated the
damage by half: on that same tree, before the guarding unit test existed, the true count is **12
survivors - 6 in `_check_loss_date_present` and 6 in `_determine_future_dated_loss`**, score 97.16%,
410 killed. With the test, cold: **0 survivors, 422 killed, 100%**. Verified by removing the test,
clearing `mutants/`, re-running, then restoring the file from a copy, so both figures are cold runs
over the same source differing only in the test. The commit added both a function and a test, which
is exactly the case this entry names. What is new is the direction and its consequence: **a passing
mutation gate is not evidence the cache was fresh**, so "clear `mutants/` and rerun" applies to a
green run as much as to a red one.

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

**Corrected 2026-08-24: "generated from one code path covering both conditions" is wrong; the
operational conclusion above it is not.** Verified against `registry.describe` in the gauntlet
repo itself (`src/gauntlet/registry.py`), not reproduced from the harness's own output:
`describe()` is a three-way branch on `Finding.status` — `MODIFIED`, `MISSING`, and everything else
(the not-approved case) — and each branch returns its own distinct prose, not a shared one.
`MODIFIED` and not-approved both happen to end by naming `gauntlet lock`, which is why the two
observations above read as "identical" at the level of "which command it wrongly tells you to
run" — but they are two separate branches producing two different sentences, not one code path
producing one. The quoted text above already shows this, read closely: the not-approved sentence
("is not approved. A human must review it and run `gauntlet lock`...") is not the modified
sentence ("changed since it was approved... revert the change, or explain why it should change and
let the human re-approve it with `gauntlet lock`") word for word. A third branch, `MISSING`, was
never checked before this correction and is not like either: "was approved but no longer exists.
Restore it, or ask the human to remove its approval" — no mention of `gauntlet lock` at all,
because there is nothing to re-lock.

**What stands, unchanged:** the operational advice — the acceptance gate's remedy names the wrong
command for a human to approve a spec with, in both the modified and the not-approved case, and
the correct command is `gauntlet spec approve`. What's corrected is only the reasoning for why the
two observations matched: two branches that happen to share a word, reasoned here from two
observations, not one branch producing one text.

### `pyproject.toml` is verified, not protected — an escalation that said otherwise was wrong

An escalation during item 5b's session asserted that `pyproject.toml` could not be edited because it
is a protected path. It is not. Gauntlet's `DEFAULT_PROTECTED_PATHS` (`src/gauntlet/config.py`) —
the files an agent must not touch at all, which is what the `PreToolUse` guard blocks — is
`gauntlet.toml`, `.gauntlet/`, `.claude/settings.json`, and the lock file. `pyproject.toml` appears
only in `DEFAULT_VERIFIED_PATHS`, which the protect gate content-hashes each run rather than blocking
outright: an agent can write it, and the gate then fails with `N-1/N paths unchanged` until a human
re-locks with `gauntlet lock`. Extending `[tool.mutmut] source_paths` to reach a module outside
`src/claimgate/domain/` was therefore always available as a proposal routed through a human, not a
blocked action. Verified by reading `src/gauntlet/config.py` directly, 2026-08-23.

### Acceptance mutation does not see everything

`Feature.background` is never passed to `mutants()`, so Background steps are
never mutation targets in any scenario. `_literal_mutants` returns early for
outline scenarios, so a value hardcoded in a fixed `Given` above an `Examples`
table is never a target either. The consequence is counterintuitive: the values
a feature file leans on hardest are often the ones nothing checks. Both facts
matter when estimating what a change will disturb — they are the difference
between a naive blast-radius count and a real one.

A step's data table is a third blind spot, and a worse one:
`gauntlet.acceptance.gherkin.Step` has only `keyword`, `text`, `line` and
`column`, so a table written under a step is discarded during parsing and
never reaches the IR. Measured 2026-08-22: `carrier_configuration.feature`'s
"Several missing and malformed values in the same entry are all named in one
refusal" yields 5 mutants, all `"AAAA"` literals, none from its three-row
assertion table; each of `validation.feature`'s four standalone
`Then the blockers are:` scenarios yields exactly one mutant, on its `Given`'s
quoted literal. Nine expectations in that file sit outside mutation. An
assertion that has to be structured belongs in an `Examples` column in compact
form - `validation.feature`'s own `the blockers are <compact>` step parses
`CODE:field` pairs joined by `;` - with the data-table form kept only where the
shape genuinely needs it.

**Correction, 2026-08-22, to the paragraph above.** An `Examples` column is
not the only mutable carrier, and reaching for it reflexively cost five
mutants the same day that advice was written. `_literal_mutants` returns early
for outlines, so converting a plain scenario into a one-row outline in order
to move an assertion into an `Examples` cell forfeits every step literal in
that scenario and gains only what a one-row table yields - one
`value+_gauntlet` substitution per column. Measured on item 5a's multi-value
refusal scenario: 5 mutants as a plain scenario with the assertion in a data
table, 1 as a one-row outline with the assertion in an `Examples` cell, 6 as a
plain scenario with the assertion **quoted in the step text**, because
`LITERAL_PATTERN` matches a quoted string in a step. A quoted literal in a
plain scenario is mutable, and a one-row outline is strictly worse than the
plain scenario it replaces.

**Correction, 2026-08-23, and it reverses the correction above.** A quoted
literal in a plain scenario is mutable but the mutant is vacuous.
`LITERAL_PATTERN` captures the surrounding quotes, and `_swap` with no
alternatives appends `_gauntlet` after the closing quote, so the mutated line
reads `the loss date is "2026-01-15"_gauntlet`. `pytest_bdd.parsers.re`
matches with `regex.fullmatch` and every step pattern in this project
terminates its captured value with a quote, so the line binds to no step
definition: pytest-bdd raises at step resolution, the test fails, the mutant
scores as killed, and no domain code ever runs. A wrong implementation kills
it identically. Measured 2026-08-23 by rendering every mutated line against
all 45 step patterns: of 82 literal mutants across the four features that have
step definitions, 7 bind and 75 do not, and all 7 that bind are numeric, where
`_mutate_number` produces a well-formed value. Of the same four features' 366
acceptance mutants, roughly a fifth are killed at step lookup. All 284
rendered outline substitutions bind, because a sibling cell value is
well-formed. **Prefer a multi-row outline. A plain scenario's quoted literal
is a vacuous kill; only its numeric literals are real tests.**

A ragged `Examples` row, one whose cell count differs from the header's,
parses with no error and no diagnostic and silently yields fewer mutants than
its siblings. Verified 2026-08-22 by construction: a three-row two-column table
with one cell omitted produced 5 mutants instead of 6, and the short row's
locator was well formed. A mutant count is this project's unit of blast-radius
estimation, so check table widths when a count comes in lower than expected.

**A pair of possessive apostrophes on one step line is parsed as a quoted
literal, confirmed from source rather than from reproduced behavior.**
`LITERAL_PATTERN` in `gauntlet/acceptance/mutation.py` is
`"[^"]*"|'[^']*'|\b\d+\.\d+\b|\b\d+\b` — the single-quote alternative matches
any span between two apostrophes, with no check that either one is actually a
string delimiter rather than an English possessive. A step reading "the
notice's audit trail's first entry" carries two apostrophes, in "notice's" and
"trail's," and the pattern matches `'s audit trail'` as if it were a quoted
value: the mutant appends the marker outside what it takes for the closing
quote, producing a malformed line that binds to no step pattern — a vacuous
kill by the same mechanism as a real quoted literal in a plain scenario, but
on text nobody meant to quote at all. Found and rephrased before it shipped in
`features/notice_intake.feature` (`QUEUE.md` item 5c); confirmed against this
project's own `LITERAL_PATTERN` source on 2026-08-24 rather than left as an
observed-but-unexplained pattern. **Rule: at most one apostrophe per step
line.**

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

### Mutant counts and locator counts are different numbers, and only one of them is the ledger's

Two mutants can share a locator, and then the ledger cannot tell them apart. `Mutant.locator` is
`scenario|kind|context`; for `example` kind the context carries the column header and the whole
row, so it is unique, but for `literal` kind it is the step line and nothing else — and the
engine's literal pattern matches quoted strings *and* bare numbers. **A step line carrying two
literals produces two mutants under one key.**

Measured on `main` at `96a5e9e`, all ten specs: **708 mutants, 681 unique locators — 27 mutants the
ledger has no way to address.** `duplicates.feature` 57/42, worst case four mutants on one locator
(a `Given` naming a claim id, a policy number, a date and a peril, all quoted);
`carrier_configuration.feature` 84/75; `siu_separation.feature` 53/50. The other seven are clean.

**One live approval already sits on a colliding locator, and a future session should not be
surprised by it.** `features/carrier_configuration.feature`, scenario "A recognized carrier's rules
load with neither SIU threshold configured", step `And "AAAA" configures a duplicate match window
of 60 days`: the mutants `"AAAA"->"AAAA"_gauntlet` and `60->61` share one key, and the stored
digest pairs to `60->61`. It is stable today only because the marker mutant dies vacuously at step
resolution, so just one survivor exists there. If that scenario's step definitions ever change
shape and the entry starts reporting `MODIFIED`, the cause is this, not a lapsed judgment.

**Technique that follows, in three parts.** Measure unique locators alongside mutants — item 5c did
this once for `notice_intake.feature` ("48 mutants, 48 unique locators") and it should be standard,
because equal totals across two refs already hide moved locators and now also hide collapsed ones.
Prefer one literal per step line in a plain scenario, the same shape as the existing
one-apostrophe-per-line rule and for a related reason. And before approving any `literal`-kind
survivor, check whether its locator is shared.

**What this project must not do about it.** Reshape a locked spec to work around it. This is a
Gauntlet defect, the specs are correct, and letting the tool's addressing scheme drive Gherkin
shape is the influence running the wrong way — the same objection recorded against approval scope
doing exactly that. It is written up for Gauntlet with a ready patch that is deliberately withheld
until this project is done.

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

Four distinct instances, all real:

- The coverage gate reads `.gauntlet/coverage.json` off disk and runs no
  subprocess. When the tests gate errors at collection, coverage can still
  report 100% from an artifact several commits old.
- The acceptance gate's approval stage returns early on failure and skips
  mutation entirely, for every spec — including specs with no approval problem.
  A single dangling key hides the mutation result for the whole suite.
- Unit tests never read feature files. A vocabulary change to a spec leaves the
  unit suite green while it still asserts the values the spec abandoned. No gate
  compares example data across the two layers.

- The code-mutation gate's source scope is not Gauntlet's. Every structural gate
  scopes to `gauntlet.toml`'s `[project] src` — `gates/tests.py` builds coverage
  with `--cov={ctx.src}` — but the mutation gate shells out to mutmut, which
  scopes to `[tool.mutmut] source_paths` in `pyproject.toml`, a file the protect
  gate only content-verifies. A module outside that path yields no mutants at all.
  Because every mutation run here is full-scope, its zero contribution disappears
  into a total dominated by the domain's: the score stays healthy and nothing on
  screen indicates a module stopped being checked.

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

**Correction, 2026-08-24: the maximum is no longer 260.3s.** A run against
`features/notice_intake.feature` approved with no bound step definitions took
423.622s — every one of its 24 mutants ran a full suite pass before scoring
surviving, not a bigger suite taking proportionally longer. Read this new
maximum as the cost of that specific defect (see "An approved spec that no
test module binds reports every mutant as surviving," above), not as ordinary
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

### A zero-mutant scope leaves no on-screen tell in the runs this project actually issues

A claim made during item 5b's session, that a zero-mutant mutation run would show `0 killed` as a
visible tell, is wrong for this project as it is actually run. That tell would only appear on a
`--changed` run that included the mutation gate, and — per the entry above — none of this project's
`--changed` invocations ever do; they are all scoped to `static`, `size`, and `complexity`. In the
full, non-`--changed` runs this project actually issues, an out-of-scope module contributes zero
mutants to a `killed` total dominated by the domain's, and there is no signature distinguishing "this
module had zero mutants" from "this module had mutants, all killed" — both read as the same aggregate
number. Corrected by re-reading this document before reasoning about gate behaviour, which is the
argument for doing so.

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

**A third shape produces the same symptom for a different reason, and this
one is fixable.** Measured on item 5a's first redraft, 2026-08-22. An outline
whose rows carry genuinely different expected outcomes is still fully inert if
the expectation is not one of its columns - if the `Then` step builds it from a
placeholder that also appears in a `Given`, as in
`Then the load is CODE:<field>`. `_row_distance` scores only `Examples`
columns, so it cannot see the expectation, and because the placeholder feeds
the input and the assertion together a swap moves both and stays correct.
Measured 12 mutants, simulated 12 survivors, against a structurally identical
sibling outline in the same file that kept its expectation as a column and
simulated 1 of 10. **Before drafting any outline, check that its expectation is
a column.** That test is cheaper than counting survivors and it catches this
shape every time.

Survivor counts in this entry are simulated against the rule, not measured — survivors cannot be
measured until the implementation exists.

**A loading row is not free, and in a mixed-outcome table it is a regression.** Measured on
`carrier_configuration.feature` at `3ebea71`, 2026-08-23. `_discriminating_alternatives` prefers
the most-different row, and an all-blank row differs from every other row in every column, so once
one exists every cell in the table substitutes to blank and none ever substitutes to a sibling
value again. With the blank row: 33 mutants, 30 substituting to blank, 1 or 2 surviving. Without
it: 30 mutants, all substituting to sibling values - `claimant name -> claimant contact` and the
like - every one killed by the outcome column, none surviving. A blank substitution asks whether
the rule fires when nothing is named; a sibling substitution asks whether the implementation
attributes the right outcome to the right input, which is the question a mixed-outcome table
exists to ask. Diagnose which table you have before adding a loading row: it manufactures the
discriminating row a same-outcome table lacks, and destroys the discrimination a mixed-outcome
table already had.

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

### The acceptance gate's approval stage short-circuits everything after it

`_stages` runs approval, then baseline, then mutation, returning on the first
failure. An unapproved or modified spec fails at approval, so **the scenarios
never run and mutation never runs**. A newly drafted spec produces
`N unapproved or modified spec(s)` and no information about whether it works.

Compounding this: a feature file joins the suite only through an explicit
`scenarios("../../features/x.feature")` call in a test module, so an unbound new
file is not collected by pytest either. Between drafting and approval a new spec
is invisible to every gate and to the test suite — the only check available is
running the mutation engine directly for counts, which needs no approval.

This first mattered at item 5a. Every item before it modified an already-approved
spec; the four phase-1 features were added and approved together in one commit
before the discipline existed, so 5a is the first spec in the project's history
that no gate could see.

### Approving the spec turns the Stop hook's check from instant to a full acceptance run

A consequence of the short-circuit above, and worth knowing in advance because it changes
what every turn costs for the rest of a reopening. While a spec is modified-since-approved,
the acceptance gate fails at its approval stage and the Stop hook's check returns almost
immediately. The moment the human approves the spec, the same hook starts paying the whole
mutation stage — and if the only thing left red is an unreviewed survivor, it pays that cost
to re-report a red that nothing the agent can run will clear.

Measured from `.gauntlet/events.jsonl` over item 5j, same repository, consecutive runs:

| acceptance gate state | duration | verdict |
|---|---|---|
| `1 unapproved or modified spec(s)` | 0.003s, 0.003s, 0.004s | fail at approval |
| 11 specs, 1 surviving mutant, 75 reviewed-equivalent | 1512.704s | fail at mutation |
| the Stop hook's own re-run of the same state | 1384.778s | fail, then `agent.escalated attempts=3` |

So the expensive window is bounded and predictable: it opens at spec approval and closes at
`gauntlet mutant approve`, and every turn taken inside it — including a turn that only writes
a document — pays roughly twenty minutes at the current suite size. This is a description of
when the wait occurs, not an argument for changing anything: the gate is doing exactly what
it is configured to do, and the alternative shapes all involve weakening a threshold.

### An approved spec that no test module binds reports every mutant as surviving

Approval clears the gate past the short-circuit above, but binding is still a
separate fact the approval stage never checks. Confirmed against
`gauntlet/gates/acceptance.py`: `survivors_for`'s own docstring says it returns
"mutants of one feature that the bound scenarios fail to kill," naming the
concept without the code ever testing for it. `_survivors` writes each mutant
into the feature file in place and calls `python_adapter.run_acceptance` over
the whole steps directory, appending the mutant to `survived` whenever that run
still passes. If no step module's `scenarios(...)` call collects the mutated
file, the run is not exercising it at all, so it passes regardless of what was
written — every mutant appended, unconditionally. `_baseline_stage`, run just
before, only checks that the suite passes as a whole; it has no check that this
feature's own scenarios were among what ran, so an approved-but-unbound file
sails through it too.

The tell, confirmed 2026-08-24: `tests` and code-mutation totals stay exactly
what they were before the new spec existed — a spec's own scenario count never
enters either figure, because pytest never collected it. Measured on
`features/notice_intake.feature`, approved before any step definition existed:
274/274 tests and 330 killed, identical to `main` pre-item-5c, against 24 of 24
mutants scored surviving — not a partial figure, all of them, because nothing
distinguishes "the assertion failed to catch this" from "nothing ran the
assertion at all."

`_scenario_diagnostic`'s own remedy text — "have a human review them with
`gauntlet mutant approve`" — is the worst available action on this particular
diagnostic: it stamps 24 equivalence judgments that were never made, over
assertions nobody has verified even run.

**Operational rule:** lock a spec at the start of the session that implements
it, not at the end of the session that drafts it. The gap between the two is
spent in this gate's expensive, misleading red state — a full mutation pass
scoring everything as failing — rather than the cheap, honest one (`N unapproved
or modified spec(s)` at the approval stage, ~0.001s). That inverts this file's
own preference for the loop to repeat on its cheapest failure.

### How a specification value is actually mutated

Read from `mutation.py` rather than inferred from samples, because inertness is
predictable only if the substitution rule is known:

- `true`/`false`, `yes`/`no`, `on`/`off` are negated.
- Numbers are incremented by one at matching decimal precision — `60` becomes
  `61`, not some other value from the column.
- Everything else is swapped for a value from the same column in another row,
  ordered **most-different row first**, on the stated theory that a row differing
  elsewhere expects a different outcome. With no alternative, the marker
  `_gauntlet` is appended.
- An empty cell takes the marker.

This is the mechanism behind the same-outcome-table finding: the engine is
already trying to pick a discriminating swap, and in a table where every row
shares an outcome there is none to pick, so every swap is inert by construction.
The lever is the table's shape, not the engine's.

**Correction, 2026-08-27.** The empty-cell line above used to read "has no
alternative of its own and takes the marker," which describes the wrong cause and
hides a usable lever. `mutate_value`'s first branch is `if not stripped: return
MARKER` — it returns before the boolean check, before the numeric check, and
before `_swap` is ever reached. The column's alternatives are not absent; they are
never consulted. This is the same preemptive-return shape as the boolean finding
below it, and it has the same consequence: **an empty cell is unprotected by
mutation even in a table full of discriminating siblings**, because the marker it
takes is a value no step can read, so the mutant dies at step resolution having
tested nothing.

**Technique, and it is cheap: spell absence as a token, not as an empty cell,
wherever the field's absent value is not the empty string.** Measured while
drafting item 5h's amendment to `features/validation.feature`, by running
`mutation.mutants()` over two candidate tables identical but for that one cell:
`absent` and `""` both produce 192 mutants over 192 locators, and the only
difference is which class one of them lands in — 81 marker-class for the token
form against 82 for the empty one. The token is swapped for a sibling date, which
changes the row's outcome from a missing field to a past one and is a real kill;
the empty cell takes `_gauntlet`, which is not a date at all. One mutant moves
from vacuous to real for the cost of a word. `features/jurisdiction_selection.feature`
already spells `property_state`'s absence this way.

This does **not** argue for replacing the empty cells already in these specs. An
empty `loss_type` or `policy_number` cell *is* that field's absent value, and
`blockers` cells are empty because the row asserts no blocker — spelling either as
a token would state something the field cannot hold. The lever applies only where
the empty string is standing in for a value the field's type has no room for.

### The boolean substitution is lowercase and preemptive, so an upper-case enumeration is unprotected

`mutate_value` looks up `BOOLEANS.get(value.strip().lower())` but returns the *dictionary's*
lowercase flip, and it returns before `_swap` is ever reached. Both halves matter, and only the
second one is obvious from the entry above:

- In a specification whose enumeration is upper-case — this project's `TRUE`/`FALSE`/`NOT_EVALUATED`
  — the substituted token is `true` or `false`, which is outside the enumeration. No implementation,
  correct or wrong, can produce it, so an exact-string step assertion kills it unconditionally. It
  is scored as a kill and tests nothing, the same class as the parse-error kills recorded below.
- The sibling swap that *would* have discriminated is never generated at all. `TRUE` in
  `triage.feature`'s `recent_inception` column has `NOT_EVALUATED` sitting in the same column and
  would have been swapped for it; the boolean branch returns first, so that mutant does not exist.

**Measured 2026-08-26 against `main` at `ca0dc3a`, by calling `mutation.mutants()` over every file
in `features/` at that ref and matching each mutant against `BOOLEANS`: 30 of the ledger's 708
mutants are this class** — `triage.feature` 15, `siu_indicators.feature` 10,
`siu_separation.feature` 5. All 30 counted as killed; none tested anything; and the
`TRUE`/`FALSE`-versus-`NOT_EVALUATED` confusion that queue item 2 exists to prevent has never once
been exercised by acceptance mutation.

**Technique: treat any `TRUE`/`FALSE` `Examples` cell as unprotected by mutation until the step that
reads it parses its expected token case-insensitively.** With a case-insensitive read, `true` matches
an actual `TRUE` and the mutant becomes a real test of the value; the fix converts kills to kills, so
it moves no locator and no ledger entry.

### The boundary gate is narrower than its name

It walks only the steps directory and flags absolute imports whose top-level root
matches a top-level importable name under `src/` — here exactly one name,
`claimgate`. `tests/api/` is not walked at all, and an import of anything not
named `claimgate` is invisible to it. A step file that imports an HTTP client
library and constructs its own client passes the gate cleanly while binding the
acceptance suite to transport detail.

This matters from phase 2 onward, where there is a transport to bind to. The rule
that keeps step definitions behavioural is enforced against one package name;
everything else about it is held by review.

### CLAUDE.md's top block is tool-managed and will be overwritten

Lines between `<!-- gauntlet:begin -->` and `<!-- gauntlet:end -->` are generated
by gauntlet's scaffolding. Anything edited there is lost the next time the
scaffold runs, silently and without a gate noticing. Every project edit to
`CLAUDE.md` belongs below the end marker.

This is a live trap rather than a theoretical one: the managed block contains the
instruction to act on a gate's remedy rather than guessing, and one remedy in the
harness names the wrong command. The correction cannot live where the instruction
is. It lives in the `gauntlet-gates` skill instead.

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

### A markdown list can swallow the paragraph after it, invisibly in a diff

An entry spliced into "A green gate sometimes means nothing was checked" at `79d7461` was inserted
without the blank line its closing sentence needed before the next paragraph. CommonMark's lazy-
continuation rule folded that following paragraph into the list item as a result; fixed at `12dbb48`.
Verify a splice by outcome, not by grepping for the phrase just written — that only proves the text
landed, not that it landed as its own block. Check something that would change if the splice went
wrong: a line-count delta on the file, or the emptiness of a specific adjacent line. A list swallowing
the paragraph after it is invisible in a diff and reads correctly in review, because the rendered
prose still makes sense — only the structure is wrong.

### A backgrounded `gauntlet check` reports "completed" when its launcher exits, not when the gate does

Observed 2026-08-29. `nohup gauntlet check > log 2>&1 &` issued through the agent's Bash tool
returns as soon as the *launcher* exits, and the harness reports the task completed with exit
code 0. The gate is still running. The notification arrived **39 seconds into a run that took
1512.7 seconds**, and the log file it was writing to was zero bytes at the moment the success
was reported. An exit status from that shape says nothing about the gate — it is the status of
the shell that spawned it.

Reading the log instead of the status does not save you either: an empty log is
indistinguishable from a gate that printed nothing, and the tail of a partial log looks like a
run that stopped early.

**Wait on the gate's own pid.** `while kill -0 <pid> 2>/dev/null; do sleep 20; done` in a
background command notifies on the real completion. Two cautions found the same day: capture
the pid from `ps`/`pgrep` *after* the process has actually exec'd, because the first match can
be the shell wrapper that is about to disappear — a pid captured immediately was gone seconds
later while the real gate ran under a different one — and never use `pgrep -af gauntlet`, which
matches its own command string, the same trap the start-up check already warns about.

This composes with the entry above: once the spec is approved, every such run is twenty minutes
long, so mistaking the launcher's exit for the gate's is the difference between reporting a
verdict and inventing one.

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

### Removing an Examples row rewrites the surviving rows' swap targets, so locators hold still while digests move

The exact inverse of the pairing above, and worth stating beside it because the two
failure modes look identical in a count and are opposites underneath. A rename moves
every locator and leaves each digest alone. **Removing a row leaves the locators alone
and moves digests** — a sibling swap is generated against whatever *other* rows offer in
that column, so deleting one row silently re-aims the mutants of the rows that remain.

Measured on item 5i's `RECEIVED` removal, `321b3a2` -> `079a346`, one row out of
`resolution.feature` Rule 1, whole file:

| identity compared | lost | gained | net |
|---|---|---|---|
| `locator` alone | 6 | 0 | −6 |
| `locator` + `mutated` | 10 | 4 | −6 |
| full mutant, including `line` | 12 | 6 | −6 |

All three are correct; they answer different questions, and quoting one without saying
which is how a number like this goes wrong. The net is −6 in every case and is the
removed row's own mutants. **The 4 that matter are mutants that kept their locator and
changed what they substitute** — the ledger's key held still while the mutation under it
became a different question:

- `state_before`: `PENDED->RECEIVED` became `PENDED->TRIAGED`. The swap target rotated to
  the nearest surviving sibling.
- `state_after`: `TRIAGED->TRIAGED_gauntlet`, twice. That column had two distinct values
  while the `RECEIVED` row existed; with both surviving rows reading `TRIAGED` there is no
  differing sibling left, so the engine falls back to the literal `_gauntlet` strand. **A
  column can lose its sibling swap entirely and still report a mutant** — the same strand
  the start-up check tells you to look for after an interrupted run.
- `audit_effect`: re-aimed onto the surviving row's phrasing.

**Consequence for the ledger.** Approval keys are content-addressed on the locator, so
none of these four would have been reported stale: the key still resolves, and the
approved reason would now be attached to a substitution nobody approved. It was harmless
here only because `resolution.feature` carried zero approvals at the time — measured, not
assumed, and the reason the row removal was safe to schedule before the lock rather than
after. **Where a file with approvals loses an Examples row, pair by digest and expect the
locator to be useless for it.**

**Correction, 2026-08-28, to the "Consequence for the ledger" paragraph above: it
inverts the truth, and it was reasoned from the key's shape instead of read from the
verifier.** The measured mechanics and the three-identity table above are correct and
stand unchanged; only the consequence drawn from them was wrong.

What the paragraph got right is that the ledger key is the locator —
`mutants.key_for` is `f"{subject_key}#{mutant.locator}"`. What it missed is that the key
is not the only thing compared. `mutants.subjects` stores each approval's digest over
`m.signature`, and for an acceptance mutant `signature` is
`f"{self.original}->{self.mutated}"` (`acceptance/mutation.py`) — **the substitution
itself, not the key.** So a re-aimed survivor resolves its key and then fails the digest
comparison: `registry.verify` returns `MODIFIED` when an entry exists and the digests
differ, `mutants._bucket_for` puts `MODIFIED` in `changed`, and `Classification.failing`
is `unreviewed + changed`. `gates/acceptance.py` builds its diagnostics from
`verdict.failing` and passes only on `not outcome.diagnostics`, so **the gate goes red and
names the mutant.** Nothing is silently mis-attributed; that was the paragraph's central
claim and it is false.

The other direction surfaces too, and `verify_all` is what makes it free: it verifies
"every subject, plus every approved key the subjects omit," so an approval whose mutant no
longer survives verifies with `content=None`, returns `MISSING`, and `_place` files it in
`stale`. **The two are not symmetric, and the asymmetry is deliberate.** A `MODIFIED`
mutant fails the gate; a `MISSING` one is counted in the summary as "N stale approval(s)"
and appended as a diagnostic *after* the pass/fail boolean is computed, under the comment
"Stale approvals are housekeeping, not a defect: report, do not fail." One goes red, the
other is reported.

**So the real consequence of removing an `Examples` row from a file carrying approvals is a
re-approval ceremony, not a silent wrong reason.** Every re-aimed survivor comes back
unapproved-in-effect and has to be judged again on what it now substitutes, and every
mutant the removal eliminated is named stale for pruning. That is a cost to schedule, and a
larger one than "harmless" — but it is a cost the gate collects for you rather than one that
escapes it. The closing advice above still stands: pair by digest when a row moves. The
reason is not that the locator is useless — it resolves fine — but that the locator is
exactly what *cannot* tell you which of these two things happened, and the digest is the
field the verifier actually compares.

### Adding an `Examples` row moves every locator in the scenario and re-aims the survivors' swaps

The mirror of the entry above, and the two belong together because the directions are
not symmetric. A locator is `scenario|kind|context`, and for an example mutant the
context carries the mutated column's header plus **every value in that row**. Removing a
row leaves the surviving rows' locators alone and moves their digests. **Adding one moves
both** — every locator in the scenario is re-keyed, because each carries a row that now
sits in a wider table or beside a new sibling, and the swap targets re-aim at the same
time.

Measured on item 5j's drafting, `features/jurisdiction_selection.feature` at `120ebd7` ->
`4f554f4`: one row added to Rule 3's first scenario, with that scenario's loss date moved
out of a fixed `Given` into a column. 48 mutants over 48 locators before, 55 over 55
after — 8 lost, 15 gained, 40 kept, and the 8 lost and 15 gained are the whole of that
one scenario, counted per scenario rather than inferred from the totals.

**A raised count is not evidence that nothing moved underneath it.** The addition also
re-aimed an existing mutant: row 2's determination swap went from
`NOT_EVALUATED:NO_JURISDICTION_DATE->TRUE` to
`NOT_EVALUATED:NO_JURISDICTION_DATE->NOT_EVALUATED:NO_LOSS_DATE`, because
`_discriminating_alternatives` prefers the most-different row and the new row is now the
most different. Both substitutions are killed here, so nothing was lost in fact. The
hazard the measurement exposes is that a re-aim can equally land on a sibling that shares
the row's outcome — turning a discriminating mutant inert — and the count reads +7 either
way.

It was free on this file only because it carries zero approvals, measured against
`gauntlet.lock.json` rather than assumed. Where a file with approvals gains a row, every
re-keyed locator is a `MISSING` stale approval and every re-aimed survivor a `MODIFIED`
one: the report-versus-red pair the correction above describes, and here both halves fire
at once rather than only the second.

**Technique: when adding a row to a scenario that carries approvals, diff signatures
against the locked ref, not counts.** A +7 is consistent with "seven added" and with
"seven added and one silently re-aimed," and only the signature diff separates them. Same
advice as the removal entry for the opposite reason — there the locator is what cannot
tell you, here it is the count.

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

### Read the session prompts from a clone, never from the raw CDN

An advisor session opened by fetching `ADVISOR.md` through
`raw.githubusercontent.com` and received a cached copy shorter than the file at
`origin/main` — missing, among other things, the instruction to produce document
edits programmatically rather than by retyping. The session ran most of the way
through on an out-of-date prompt and only noticed when an unrelated command
printed the real file's length.

The CDN caches independently of the repository, so a raw fetch can be stale
without any signal. Read session prompts from a clone at a named ref. Nothing in
that session contradicted the current text, but that was luck: the one
instruction it happened to follow correctly was in the part it never read.

### A superset check against `origin/main` is vacuous when `main` is unpushed

The startup and save-point checklists verify that a working branch is a superset
of `main` with `git log --oneline origin/main ^HEAD`, expecting 0. That compares
against **origin's** main. When a documentation commit has landed on local `main`
but was not pushed, the check passes while the branch may be missing it — the
comparison succeeds against a ref that has not moved.

Observed at item 5a, where a docs commit to `main` and a spec commit on the
branch were both unpushed and the cited check reported success. Push `main`
first, or compare against local `main`, before the check means anything.

### Verifying a multi-file change means counting per file, not per commit

A four-document edit was handed over and three documents landed. The push
succeeded, the commit message described all four, and `git log` looked correct;
the fourth file was simply absent from the commit. What caught it was
`git diff --numstat` per path, not any check on the push.

The failure leaves no trace in the gates, because no gate reads these documents.
It surfaced as four cross-references on `main` pointing at entries that did not
exist — including the one standing between a phase-2 agent and a placeholder
value it must not invent. When an edit spans files, verify each file
independently: occurrences per file, or numstat per path.

### A session that pushes a branch records it in `QUEUE.md`'s status section before stopping

Observed 2026-08-28: item 5j's drafting session pushed
`reopening/5j-both-absent-precedence` at 09:14 and stopped without touching the
status section, whose most recent paragraph — written truthfully by the prior
session — said no open branch existed. The disagreement was found only by running
`git branch -r` from outside; a memoryless session reading the documents alone
would have concluded nothing was in flight.

The status section is the memoryless-session contract, and a truthful-when-written
paragraph that has silently become false is worse than a stale-marked one: nothing
about it invites checking, so the next session inherits a confident wrong answer
instead of a doubtful one. Scoping a session to "drafting only" does not exempt it.
Documentation lands on `main`, so the paragraph could always have been written.

The rule: a session that pushes a branch records it in `QUEUE.md`'s status section
in the same work period, before stopping.

### A splice that normalises trailing newlines is wrong for in-line replacement

Observed 2026-09-01, on the README approval-count edit. `splice.py` appended a
newline to any content file lacking one, in every mode, so a mid-sentence
`--replace` came back `+1/−0` where a `1/1` was expected. The `wc -l` check on
the content file passed, because the content was one line; only the numstat
showed the break. Line-oriented modes want the newline; verbatim replacement
must not touch the content at all, and the script now distinguishes them. The
check that caught it is the one to keep: predict the numstat before the splice
and compare after, since a one-line content file cannot reveal what the splice
added to it.

### A shipped script must resolve the project interpreter, not `python3`

A skill script invoked bare `python3`. On a machine whose system Python is 3.10
it died on `import tomllib` — a standard-library module since 3.11 — inside
gauntlet's own `config.py`. The message names a module, so it reads as a missing
dependency, and the reasonable next move is to install a newer Python
system-wide. That does not fix it: the project's venv already satisfies
`requires-python >= 3.12`, and the script simply was not using it.

Two things follow. Any script shipped alongside the project resolves its
interpreter explicitly — `$VIRTUAL_ENV`, then `.venv/bin/python` — and fails with
a message that says *interpreter*, not *module*, when it cannot. And a
verification script must not create anything: `uv run` provisions a virtual
environment as a side effect even with `--no-sync`, which is a surprising thing
for a command whose only job is to read source and report.

### A commit message passed with `-m` executes its own backticks

An advisor handed over a multi-paragraph commit message as a `git commit -m`
string. It contained backticked command names, as prose about a build system
naturally does. The shell ran every one of them as command substitution before
git ever saw the message: two failed harmlessly, and one was `gauntlet lock` —
a human-only command that re-approves the verified config paths. Its output was
spliced into the commit message, which is the visible symptom; the invisible one
is a re-approval entry in the ledger that no human decided to make.

Nothing was weakened, because the verified files had not changed and the
re-approval recorded the same hashes. The cost is an audit-trail falsehood in
the one artifact whose entire purpose is recording that a human approved
something, and it was recoverable only because the commit had not been pushed.

**Write commit messages to a file and use `git commit -F`.** Never paste prose
about a command-line tool into `-m`. The same hazard applies to any long text
handed between a session and a shell: if it contains backticks, `$`, or `!`, it
needs a file or a quoted heredoc, not a double-quoted argument.

### `mutmut`'s source scope and its test selection disagree, and only one of them is enforced

`[tool.mutmut] source_paths = ["src/claimgate/domain/"]` restricts which files mutmut copies into
its isolated `mutants/` sandbox to `domain/` alone, but `pytest_add_cli_args_test_selection =
["tests/unit/"]` still hands the whole `tests/unit/` directory to pytest inside that sandbox on every
run. Nothing reconciles the two: a unit test under `tests/unit/` that imports anything outside
`claimgate.domain` (a new `claimgate.shell` package, in this instance, item 5c's first orchestration
code) fails to import inside the sandbox, because that package was never copied there. The failure
surfaces as `ModuleNotFoundError` during collection and aborts the whole run before any mutant
executes. The code-mutation gate reports this as `actual=None` with an error field that is just the
progress spinner's frames repeated, not the real traceback — the real one has to be read from a
direct `mutmut run` invocation, not from the gate's own captured output.

A second trap compounds the first: `mutmut` does not clean its `mutants/` artifact directory between
runs. Moving the offending test file to fix the import did not fix the failure on the next attempt,
because a stale copy of the old file was still sitting in `mutants/tests/unit/` from the prior run.
`mutants/` and `.mutmut-cache` are both gitignored and safe to delete outright; deleting them forced
a clean re-copy that picked up the move.

**A unit test for code outside `src/claimgate/domain/` does not belong under `tests/unit/`** — that
directory is implicitly scoped to whatever `[tool.mutmut] source_paths` names, not to "unit test" as
a category. This item's shell-layer tests moved to a sibling `tests/shell/` directory instead;
`gauntlet`'s own `tests`/`coverage` gates run the whole `tests/` tree regardless of subdirectory name
(confirmed by the passing-test count, which included every new test in both locations), so nothing
was lost by moving them, and mutmut's internal `tests/unit/` selection stopped choking on an import
it was never going to reach anyway.

### The code-mutation killed count is inert for a shell-only item, and that is a useful signal rather than a gap

A corollary of the scope above, worth stating separately because it looks like a
missing result rather than a correct one. `source_paths = ["src/claimgate/domain/"]`
means the mutation gate's `killed` figure counts mutants of the domain layer and
nothing else. An item whose whole implementation is shell-side therefore finishes
with the count exactly where it started, even though it added a module, two
endpoint answers and a database column.

Measured on item 5i, 2026-08-28: `422 killed` before the implementation commit and
`422 killed` after it, score 100.0% both times, against a change of 493 added lines
across sixteen files. The item's brief predicted the figure would rise; it did not,
and the reason is the same one the item's own ruling 6 gives for not bumping
`RULESET_VERSION` — the two new error codes are shell vocabulary and no rule under
`domain/` computes either.

**Read a flat count as evidence, not as a null result.** For an item ruled to be
shell-only, a *risen* count is the finding: it would mean something landed in
`domain/` that the ruling said would not. Predicting the direction before the run
and comparing is what makes the number say anything at all; the count alone,
unanchored, says nothing either way.

### A mutant killed by a step definition's own parse error is scored identically to one killed by an assertion

The mutation gate's kill/survive verdict comes from the test run's exit status, not from which line
raised. A mutant that reaches an `assert` and fails it is indistinguishable, in the gate's report,
from a mutant that never reaches an assert at all because a helper function it flows through raises
first. `features/notice_intake.feature`'s marker mutants are the concrete case: an empty Examples
cell has no sibling row value to swap against, so the engine appends `_gauntlet` instead (see "How a
specification value is actually mutated," above). `the notice's blockers are <blockers>`'s step
reads

    expected = _parse_compact_blockers(value)
    actual = [(b.code, b.field) for b in context["response"].blockers]
    assert actual == expected

and `_parse_compact_blockers("_gauntlet")` raises `ValueError: not enough values to unpack (expected
2, got 1)` inside `pair.split(":", 1)`, on the first line, before `actual` is ever computed —
confirmed by calling the function directly, not inferred from the gate's report. The mutant is
killed without `context["response"].blockers` ever being read, so this particular kill proves
nothing about whether the implementation's blockers are correct; it only proves the marker string
doesn't parse as `CODE:field`. Three of `notice_intake.feature`'s 48 mutants are this exact case —
Rule 1's and both of Rule 4's empty-blockers cells, the only cells in the file with no differing
sibling value in their column.

**Read a mutation score of 100% as "nothing survived," not as "every assertion fired."** A
parse-error kill and an assertion kill count identically toward the total, and only reading the step
code — not the score — tells them apart. This doesn't make the marker mutants worthless: a step that
silently accepted `_gauntlet` as a valid blockers rendering would be a real step-definition bug, and
this is the mechanism that would have caught it. It does mean the 100% figure overstates how many of
the 48 mutants were caught by a domain assertion actually being wrong, for exactly the three that
were never real row-swaps to begin with.

### Two locked specs sharing a Background can only share step definitions through `conftest.py`

`features/idempotency.feature` restates `features/notice_intake.feature`'s Background word for word.
Neither rewording is available once both are approved, and copying the definitions into a second
step module is a duplicate block well past `min_lines = 6`, which `max_duplicate_blocks = 0`
refuses.

**Correction, 2026-08-24.** The sentence above is false: the duplication gate does not read the test
tree. `gates/base.py::tool_targets` and `python_files()` scope `static`, `size`, `complexity` and
`duplication` to `src` only — read from source after the move landed, not before. The advisor's
instruction asserted the gate's scope from `gauntlet.toml`'s `tests` key, and this entry recorded the
assertion as the mechanism. The consolidation is still correct, for a reason this entry should have
led with: two locked specs that say the same words must mean the same thing, and one definition per
phrase is how that is kept true. The two pytest-bdd behaviours below are unaffected and remain the
thing that makes the consolidation work. Another instance of the pattern this document keeps
finding — a claim about how a gate behaves, written from configuration rather than from its source,
wrong on first check.

`tests/acceptance/conftest.py` is the only remaining place, and two pytest-bdd behaviours that make
that work were confirmed by running them in an isolated project, not inferred:

- **A step definition in a test module overrides one of the same text in `conftest.py`.** Ordinary
  pytest fixture precedence — pytest-bdd registers each step as a fixture keyed by its parsed text,
  so the nearer definition wins. This is what lets `test_carrier_configuration_acceptance.py` keep
  its own `"{carrier}" requires the claimant name` pointed at `context["rules_source"]` while the
  shared one in `conftest.py` writes `context["carrier_rules_source"]` for everyone else. Without
  it, moving a step to `conftest.py` would silently redirect every other spec that says the same
  words.
- **`@given` and `@when` stack on one function.** A step whose text appears under `Given` in one
  scenario and under `When` in another needs both decorators; pytest-bdd matches on keyword, so a
  `@given`-only definition is invisible to a `When` line with identical text. `idempotency.feature`
  needs this for six steps, including `the notice is submitted for intake`, which its rules use as
  a `Given` to set up the original submission and as a `When` for the replay.

The isolated-project check cost about two minutes and would have cost a debugging session had
either assumption been wrong in the direction of "quietly does something else."

### A value imported from `conftest.py` is not the same object the fixtures use

`tests/shell/` has no `__init__.py`, so pytest imports its `conftest.py` under its own module name
and `from tests.shell.conftest import ...` produces a **second** module object. Both exist for the
rest of the run. Constants survive that — a dataclass compares equal across the two copies — but a
class does not: an exception defined in `conftest.py` and raised by a fixture is
`conftest.TheError`, while the test's `pytest.raises(TheError)` names `tests.shell.conftest.TheError`,
and the two do not match. Observed 2026-08-25 as `DID NOT RAISE` on an exception that had plainly
been raised, with the traceback showing the other spelling of the same name.

**Shared values belong in a plain module next to `conftest.py`, not in it** — `tests/shell/support.py`
here. `conftest.py` then imports from that module like everything else, one object exists, and
`except`/`isinstance` behave. The failure mode is worth knowing because it is silent for the cheap
cases (constants, type aliases) and only appears once something identity-sensitive crosses the line.

### A swappability proof can pass without the thing being swapped

Written for item 5g's jurisdiction proof and found by breaking it on purpose, which is
the only reason it was found at all. The test submitted one notice under `FL` and one
under a fictional `ZZ` whose entry holds a timezone that puts the same instant on a
different calendar day, and asserted the two outcomes that follow: `PENDED` with
`LOSS_DATE_IN_FUTURE` under Florida, `TRIAGED` with no blockers under the second
jurisdiction. Replacing the injected map with the shipped one — the exact hardcoding the
test exists to forbid — left it green.

The reason is that "judged under a calendar that had already reached the loss date" and
"not judged at all" produce the same two observable values. With no entry for `ZZ` there
is no jurisdiction, so no today, so no future-dated-loss determination and therefore no
blocker: `TRIAGED`, blockers `()`. The assertion could not tell the swap from its own
absence.

What fixed it was asserting a value only the presence of an entry can produce — the
recorded determination, `FALSE` where a calendar answered and `NOT_EVALUATED` /
`NO_JURISDICTION_DATE` where none did — plus the jurisdiction marking, which is `None`
only when the lookup hit. With both, hardcoding the map fails the test.

**Technique: for any test whose subject is "configuration X was really consulted", find
the observable that differs between *X supplied* and *X absent*, not between *X* and
*some other X*.** The absent case is usually the one that silently agrees. Verify by
substituting the hardcoded value and confirming the test goes red; a swappability proof
that has never been run against the hardcoding it forbids is an assertion about the
fixture, not about the seam.

### A reason code shared by two enumerations defeats a text-scanning leak negative

`features/siu_separation.feature`'s leak negatives serialize a whole surface, lower-case
it, and assert that no SIU indicator name and no SIU reason code appears anywhere in the
text. That is deliberately name-blind, so a field added later is caught by the assertion
rather than by someone remembering to list it.

Item 5g's ratification put `NO_JURISDICTION_DATE` into two closed enumerations as two
codes of one spelling — the future-dated-loss determination's reasons and the SIU
indicator reasons. The two are different codes and `CLAUDE.md` keeps them apart, but a
serialized surface is text, and text has no room for the distinction. Measured rather
than argued: a notice view carrying the determination's reason for an unsupported
jurisdiction matches `no_jurisdiction_date` in the leak negatives' exclusion list, so an
entirely legitimate value would fail the check that exists to catch a leak.

It does not bite today only because both leak scenarios use `FL`, where the determination
is `FALSE` and carries no reason at all — an accident of the fixture, not a property of
the design. The determination was therefore kept off every ordinary surface (item 5g,
`serialization.py`), which is also where `NoticeRecord.pended_at` and `resolved_at`
already sit.

**The general shape: a text-scanning negative cannot distinguish two enumerations that
share a spelling, so a spelling shared across a restricted and an unrestricted
enumeration is a design decision about that negative, not only about the two
enumerations.** The pressure, when it lands, is on the negative to get looser.

### The acceptance gate reports no per-spec kill count; `apply()` plus the step file gives one

Observed 2026-09-03 on item 7a's first full run. The gate's printed line, the `actual` in
`gauntlet check --json`, `gauntlet status`, and every `gate.finished` event carry only the summary
— `12 spec(s), 76 reviewed-equivalent` — and diagnostics list survivors alone. A spec that killed
everything leaves two traces and no count: its file in `.gauntlet/mutation-backup/` with the run's
timestamp, which proves the gate mutated it, and a reviewed-equivalent figure unchanged from the
previous run, which with zero diagnostics proves no survivor. For a kill list with locators, apply
each mutant with `mutation.apply(text, mutant)`, write the result over the spec, run the spec's
step file with pytest, and count a non-zero exit as a kill; restore the spec in a `finally` and
verify its digest after. Report the result as a measurement outside the gate, not the gate's
figure. 78 mutants took about a minute, against the gate's twenty-odd for all twelve specs.

### A `key=` lambda on `max` over tuples breeds equivalent code mutants

Observed 2026-09-03. `max(pairs, key=lambda pair: pair[0])` over `(date, term)` tuples survived two
mutmut mutants — the `key=` argument dropped, and `key=None` — because tuples already compare on
their first element and no test had a tie on it. Both were equivalent, and approving them would
have carried that argument into the ledger. Restructure instead: take `max` over the plain key
values and select the pair by equality. Nothing is left to drop, and the selection's `==` becomes
a mutant that any test with two candidates kills.
