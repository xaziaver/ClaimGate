# Harness findings

Findings about Gauntlet and the development process itself, discovered by using them across this
project's phase-1 and phase-2 design work — not assumed, not designed in from the start. A harness
with a documented findings log is more credible than one presented as flawless. Each entry: what
happened, why it matters, what would address it.

## Retry loop burns attempts on non-agent-actionable failures

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

## Interrupted mutation runs leave corrupted source

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

## Tool timeouts silently change state

**What happened.** Two occurrences across two sessions of this project: a tool-level timeout killed
an in-progress `gauntlet check` run, and in at least one case that left the working tree in a
different state than before the run started (see above).

**Why it matters.** A timeout reads, superficially, like "nothing happened" — the command just
didn't finish. It is not the same as "nothing happened." Treating it as a no-op invites exactly the
kind of silent corruption found above.

**What would address it.** Treat timeouts as a category with a known recovery procedure — diff the
working tree, check for a partially-written state, re-run — rather than as one-off accidents to be
individually rediscovered each time.

## Gates cannot check a specification against the world

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

## No gate catches inherited framing

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

## Ordering assertions can pass without a sort existing

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

## Spec approval cannot verify the human read the spec

**What happened.** `gauntlet spec approve` hashes a feature file's content and records that hash as
approved. It has no way to know whether the approver read the file, read a summary of it, or
skimmed the diff.

**Why it matters.** The hash-lock mechanism guarantees the *content* hasn't silently drifted from
what was approved. It cannot and does not guarantee that approval reflected genuine review — that
guarantee, to the extent one exists, comes entirely from the human's own diligence, not from the
tool.

**What would address it.** Nothing — this is a process boundary, not a fixable gap. Worth naming
explicitly so it isn't mistaken for a guarantee the mechanism doesn't actually provide.

## Unverified rules silently do nothing

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
