# Harness findings

Findings about Gauntlet and the development process itself, discovered by using them across this
project's phase-1 and phase-2 design work — not assumed, not designed in from the start. A harness
with a documented findings log is more credible than one presented as flawless. Each entry: what
happened, why it matters, what would address it.

Organized into three sections by what kind of finding it is, so the ones a separate v1 effort could
act on don't have to be sorted out from the ones that would mislead them: **Proposed changes to
Gauntlet** (act on these), **Designed boundaries** (do not act on these — they exist so nobody
mistakes them for gaps), and **Process and technique** (lessons about working with the harness, not
requests to change it).

## Proposed changes to Gauntlet

Findings that describe something the harness should do differently. Each carries what happened, why
it matters, what would address it, a concrete proposed change, what the gap actually cost us, and a
status. Sorted by cost, highest first.

**Gauntlet is deliberately NOT modified during this project.** The harness and the work it gates
should not move at the same time, or the gate results stop meaning what they appear to mean. These
findings are recorded for a separate effort. If one of them becomes genuinely blocking rather than
merely annoying, escalate it rather than working around it quietly.

### Interrupted mutation runs leave corrupted source

**What happened.** The acceptance gate mutates spec files in place during mutation testing and
restores them afterward. A `gauntlet check` run killed mid-mutation (a tool timeout, exit 143) left
a literal `"_gauntlet"` string injected into a step definition in `features/validation.feature`.
Caught by `git diff` before the next commit, but only because someone thought to look.

**Why it matters.** A corrupted spec file is indistinguishable, at a glance, from a real edit. If a
human trusts an approved-spec's hash without diffing after any interrupted run, a self-inflicted
mutation can slip through as if it were intentional.

**What would address it.** A clean working tree before any gate run, so a subsequent diff is
diagnostic rather than ambiguous; a longer default timeout for the acceptance gate specifically,
since it's the slowest gate by a wide margin; and ideally a restore-on-interrupt guarantee inside
the harness itself, so a killed process can't leave mutated content behind.

**Proposed change.** A restore-on-interrupt guarantee in the acceptance gate: if mutation testing is
killed (timeout, signal, crash) before completing, the harness restores every mutated file to its
pre-mutation content before exiting, rather than leaving partially-mutated content in the working
tree for the next `git status` to discover by chance. Pair with a longer default timeout for the
acceptance gate specifically, since it's the slowest gate by a wide margin and the most likely to be
killed mid-run.

**What it cost us.** A real corruption, not a hypothetical one — a literal `"_gauntlet"` string
landed inside a step definition in an already-approved spec file. It was caught only because a human
happened to run `git diff` before the next commit; nothing in the harness itself flagged it.

**Status.** Open.

### Retry loop burns attempts on non-agent-actionable failures

**What happened.** The Stop hook's retry-capped `gauntlet stop-check` fired repeatedly against an
acceptance-gate failure caused by a spec sitting unapproved, awaiting human review — observed at
12 attempts remaining, then 7, then 5, then 4, across separate stop events, with no change in the
underlying cause between them.

**Why it matters.** An unapproved spec is a queue state, not a gate failure the agent can act on.
No number of retries clears it — only a human running `gauntlet spec approve` does. Spending the
retry budget on a condition that can't change from the agent side wastes it against the failures
that actually are agent-actionable.

**What would address it.** Gates should distinguish failures an agent can fix from failures
awaiting a human, and the retry loop should stop immediately on the latter rather than counting
down toward it.

**Proposed change.** The stop-check should classify each gate failure as agent-actionable or
human-blocked — "spec awaiting `gauntlet spec approve`" is always human-blocked — and stop retrying
immediately on the latter, rather than counting down a shared retry budget that treats both
categories the same.

**What it cost us.** Confirmed twice, in two separate sessions, against the same underlying cause:
12 retries burned in one session (12 → 7 → 5 → 4, no change in cause between firings), and a further
twelve firings in a second session. Both times the loop stopped only because an agent recognized the
documented pattern and refused to keep retrying — not because the retry budget ran out safely or the
harness intervened.

**Status.** Open.

### A gate requiring human review must show the human what to review

**What happened.** The acceptance gate refused to pass until a human judged each of 11 surviving
mutants on `features/triage.feature` equivalent or not. Its own terminal output truncated the list at
six examples plus "+5 more"; `--json` truncated the same message string identically; `gauntlet mutant
list` showed only mutants already reviewed, not the current unreviewed set. There was no CLI path to
the full eleven. Recovering it required reading the gate's own source
(`gauntlet.acceptance.mutation`) and re-deriving the mutant set by running the real algorithm against
the real feature file and the real domain code — not something a review step should require of its
reviewer.

**Why it matters.** The gate demands a judgment it will not supply the evidence for. The path of
least resistance in that position is to approve the whole block on the strength of a six-item sample
— which is exactly the failure the human-approval step exists to prevent, and in this case would have
approved a mutant (line 71) that was not equivalent and that pointed at real, previously-undocumented
behavior (see "Mutation testing can find unspecified implementation behavior" below). A gate that
requires review should make complete review possible; truncating the review material converts a
safeguard into a rubber stamp.

**What would address it.** The acceptance gate should either print the complete surviving-mutant list
(not a capped sample) or write it to a file in `.gauntlet/` the way `coverage.json` and `junit.xml`
already do, so `--json` and disk output aren't both subject to the same truncation. Until that exists,
treat a truncated mutant list as incomplete evidence, not as "the interesting ones" — the ones left
out are exactly as capable of hiding a non-equivalent mutant as the ones shown.

**Proposed change.** The acceptance gate should print the complete surviving-mutant list — not a
capped sample — or write it to a file under `.gauntlet/` the same way `coverage.json` and
`junit.xml` already are, so neither terminal output nor `--json` truncates the material a human is
required to sign off on.

**What it cost us.** The truncated six-of-eleven list nearly produced a wrong approval. The path of
least resistance — approving the whole block on the visible sample — would have signed off on a
mutant that was not actually equivalent and that concealed real, previously-undocumented behavior in
`_is_recent_inception`. Recovering the true set required reading the gate's own source code and
re-deriving the mutant algorithm by hand.

**Status.** Open.

### No cross-spec impact check

**What happened.** Making SIU indicator results three-valued invalidates `triage.feature`, whose
step definitions assert a boolean against the same shared function. This was caught by an agent
tracing the shared function across a spec boundary it had not been asked to examine.

**Why it matters.** Gauntlet would have caught it eventually — the tests gate goes red once the
change lands — but it presents as a broken test inside one spec's step definitions, not as one
spec's change invalidating another. The diagnosis points at the symptom, and it arrives after
implementation rather than at design time, when the scope decision is still cheap. With four specs a
human can hold the coupling in their head. Phase 2 adds surface, and this does not scale.

**What would address it.** Given a changed spec file, report which other spec files share step
definitions or test-API surface with it, before implementation rather than after. A warning, not a
gate — the point is to make the scope decision visible while it is still a decision.

**Proposed change.** Given a changed spec file, report which other spec files share step
definitions or test-API surface with it, before implementation rather than after. A warning, not a
gate — the point is to make the scope decision visible while it is still a decision.

**What it cost us.** Nothing this time, because it was caught by hand. The cost is the near miss:
shipping item 2 alone would have left `main` red between two reopenings, breaking the constraint the
branch discipline exists to protect.

**Status.** Open.

### Mutant approval defaults to the widest scope

**What happened.** `gauntlet mutant approve` without `--scenario` applies to every surviving mutant in
the file. Running it that way swept two mutants from an unrelated scenario into an approval batch and
stamped them with reason text that did not describe them. Caught and corrected, but the default is
the dangerous direction: the narrow, explicit scope should be the default and the file-wide sweep
should require an explicit flag, because the failure mode is approving things nobody reviewed with a
justification that does not apply to them — precisely what the human-approval step exists to prevent.

**Why it matters.** A tool whose unscoped invocation is also its most dangerous one invites exactly
this mistake: reaching for the plain command and getting more than intended. The cost of that mistake
here was a wrong reason string, caught by a human reading the output; it could as easily have been a
mutant nobody actually reviewed getting the same rubber-stamp reason as ones that were.

**What would address it.** Invert the default: `gauntlet mutant approve` with no `--scenario` should
require an explicit `--all-scenarios` (or equivalent) to touch more than one scenario's survivors, so
the narrow, safe invocation is the one that requires no extra thought.

**Proposed change.** Invert the default: `gauntlet mutant approve` with no `--scenario` should
require an explicit `--all-scenarios` flag to touch more than one scenario's survivors, so the safe,
narrow invocation is the one requiring no extra thought, not the dangerous, wide one.

**What it cost us.** Running the unscoped command once swept two mutants from an unrelated scenario
into an approval batch, stamping them with a reason that didn't describe them. Caught and corrected
by a human reading the output, but the same mechanism could as easily have rubber-stamped a mutant
nobody had actually reviewed.

**Status.** Open.

### The approval ledger has no per-mutant reason

**What happened.** `gauntlet mutant approve` applies one `--reason` to every currently-surviving
mutant matching its filter, and a second call overwrites rather than adds. Two mutants in one
scenario surviving for genuinely different reasons cannot be recorded separately without hand-editing
`gauntlet.lock.json`, which `CLAUDE.md` forbids. The workaround is one combined reason covering both,
with each mutant's justification scoped inside the text — which works, but means a reader must parse
prose to learn why any individual mutant was approved, and a revisit trigger attached to one mutant is
not machine-associated with it.

**Why it matters.** The ledger's data model is coarser than the judgments it's asked to hold. A
reviewer relying on `gauntlet mutant list` output to answer "why is *this specific* mutant equivalent"
gets a paragraph that may address several mutants at once, with no structural marker for which
sentence belongs to which locator.

**What would address it.** A `--reason` keyed per mutant locator, or at minimum a CLI warning when a
call's survivor set spans mutants that received different reasons in the same invocation — something
short of hand-editing the lock file, which stays off-limits.

**Proposed change.** Support a `--reason` keyed per mutant locator, or at minimum have the CLI warn
when a call's survivor set spans mutants that previously received different reasons — something
short of requiring hand-editing `gauntlet.lock.json`, which stays off-limits per project policy.

**What it cost us.** Two mutants surviving in the same scenario for genuinely different reasons could
only be recorded with one combined reason covering both, scoped inside the prose. A reader relying on
`gauntlet mutant list` to learn why any individual mutant was approved has to parse a paragraph, and
a revisit trigger attached to one mutant isn't machine-associated with it.

**Status.** Open.

## Designed boundaries

Things the harness deliberately does not do. These are not work items — recorded so nobody mistakes
them for gaps and tries to close them.

### Gates cannot check a specification against the world

**What happened.** The 365-day reporting window, the 30-day SIU late-reporting threshold, and the
$500 theft severity threshold passed every configured gate — including 100% mutation score — for
the entire life of the project, while being, respectively: internally contradictory, orphaned
against a rule that no longer exists, and unsourced.

**Why it matters.** This is the most useful finding in this document, stated plainly: Gauntlet
verifies that code matches specification. Nothing in it verifies that the specification matches
reality. A gate can only be as correct as the human judgment that wrote the spec it's checking
against — a 100% mutation score on a wrong rule is 100% confidence in the wrong thing.

**What would address it.** Nothing about the harness — this is a designed boundary, not a defect.
It's the argument for the human review step existing at all, not a gap to close.

### Spec approval cannot verify the human read the spec

**What happened.** `gauntlet spec approve` hashes a feature file's content and records that hash as
approved. It has no way to know whether the approver read the file, read a summary of it, or
skimmed the diff.

**Why it matters.** The hash-lock mechanism guarantees the *content* hasn't silently drifted from
what was approved. It cannot and does not guarantee that approval reflected genuine review — that
guarantee, to the extent one exists, comes entirely from the human's own diligence, not from the
tool.

**What would address it.** Nothing — this is a process boundary, not a fixable gap. Worth naming
explicitly so it isn't mistaken for a guarantee the mechanism doesn't actually provide.

### Code mutation cannot find a guard no test exercises

**What happened.** The `0 <=` lower bound in `_is_recent_inception` has never been exercised with a
negative interval — every real row in every spec and unit test has an inception date on or before its
loss date. Code mutation still scores 100%, because standard mutation operators alter a comparison
(`<=` to `<`, `0` to `1`) rather than deleting a clause, and those variants are killed by the existing
inception-on-loss-date scenario. Removing the lower bound entirely is not a mutation the tool
generates, so nothing would catch it.

**Why it matters.** A 100% code mutation score does not mean every branch of a condition is defended
— only that the mutations the tool knows how to generate are caught. A guard against inputs no test
produces is invisible to it. This one was found by a mutant surviving in the spec layer, not the code
layer, which is a useful direction of travel to note: spec-level mutation surfaced a code-level gap
that code-level mutation could not.

**What would address it.** Nothing about this project's configuration — this is a property of what
mutation testing structurally can and can't generate, not a misconfiguration. Worth remembering as a
standing caveat on any 100% code-mutation score: it certifies the mutations tried, not the space of
inputs the code was never asked to handle.

## Process and technique

Lessons about working with the harness rather than about the harness itself.

### Tool timeouts silently change state

**What happened.** Two occurrences across two sessions of this project: a tool-level timeout killed
an in-progress `gauntlet check` run, and in at least one case that left the working tree in a
different state than before the run started (see "Interrupted mutation runs leave corrupted source"
above).

**Why it matters.** A timeout reads, superficially, like "nothing happened" — the command just
didn't finish. It is not the same as "nothing happened." Treating it as a no-op invites exactly the
kind of silent corruption found above.

**What would address it.** Treat timeouts as a category with a known recovery procedure — diff the
working tree, check for a partially-written state, re-run — rather than as one-off accidents to be
individually rediscovered each time.

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

**What happened.** Four occurrences now, across two sessions: two tool timeouts that killed a
`gauntlet check` run mid-mutation and left corrupted source; a `git checkout <branch> -- .` that
pulled branch files onto `main`'s working tree while still checked out on `main`; and, in the same
session as the branch-pointing-at-an-old-commit finding above, a `git merge` that resolved one whole
Gherkin rule to `main`'s reverted (buggy) content with **no conflict marker at all**, while a
different rule in the same file conflicted normally two lines later. Each was caught only because
someone — human or agent — thought to look afterward; none announced itself.

**Why it matters.** The fourth occurrence is the sharpest version of this finding so far: it shows
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
report is not a complete report.

### An unapproved spec is a queue state, confirmed in practice

**What happened.** The Stop hook's `gauntlet stop-check` fired twelve times across a session against
an acceptance-gate failure caused by `features/triage.feature` sitting unapproved, awaiting human
review, with no change in the underlying cause between firings. Citing the existing entry above
(rather than re-running the check, or trying to work around the failure) was what stopped the loop
— not a twelfth attempt succeeding.

**Why it matters.** This is the same finding already recorded in this document under "Retry loop
burns attempts on non-agent-actionable failures," observed again rather than newly discovered. Worth
recording that the mitigation in practice wasn't a harness change — none has shipped — but an agent
recognizing the documented pattern and refusing to keep spending retries against it. The finding
holds up under a second, independent occurrence.

**What would address it.** Unchanged from the original entry: gates should distinguish
agent-actionable failures from failures awaiting a human, and stop the retry loop immediately on the
latter. Until that exists, the workaround is procedural — recognize "unapproved spec" from the gate
output and stop retrying, rather than treating every stop-hook firing as a fresh problem to solve.

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

### An approved equivalent mutant is a regression test for its own justification

**What happened.** The line-71 approval depends on the `0 <=` lower bound in `_is_recent_inception`,
which no test exercises. That looked like a guard protected only by a reason string in a ledger. It
is not: removing the bound makes the mutant killable, the gate detects an approved mutant that no
longer survives, and the acceptance gate fails as a stale approval. The approval therefore defends
the code property that makes it valid.

**Why it matters.** This generalizes. Every equivalence approval silently asserts something about the
implementation, and the stale-approval check turns that assertion into a test. It is the strongest
answer this harness has to the question of what stops human judgments from rotting as the code moves
underneath them — stronger than the earlier prune, which only showed stale judgments being detected
after a spec changed.

**What would address it.** Nothing — this is the mechanism working as designed, worth naming so it
isn't mistaken for a coincidence. A revisit trigger written into a reason (see line 71's approval) is
belt-and-suspenders on top of a check the ledger already performs structurally.
