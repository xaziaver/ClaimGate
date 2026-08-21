# ClaimGate

ClaimGate is a First Notice of Loss (FNOL) intake service, configured per carrier and designed to
sit in front of a policy administration system. A managing agency running several carriers on
several systems runs several configurations in parallel; a single carrier or MGA runs one. Its
business rules are written against Florida residential property insurance statute, and it ships
configured for a Florida residential property book.

The core design commitment: regulatory rules vary by **jurisdiction**, not by carrier, and carrier
identity is data, never behavior. A policy administration system is a replaceable adapter behind
one interface. Nothing in the domain should need to change to add a second carrier, a second
jurisdiction, or a second policy admin system — see the swappability tests described in
[`PHASE2_DESIGN.md`](PHASE2_DESIGN.md) for how that claim is proven rather than argued.

Inside the domain, that commitment is now literal rather than aspirational. Every rule that varies
by carrier is a required parameter with **no default and no fallback** — the SIU thresholds, the
duplicate-detection window, whether a claimant's name and contact details block intake, and which
policy-number prefixes are recognized. A caller must state each one on every call. A configurable
value carrying a shipped default would be a rule nobody approved, reached by omission, so there
isn't one.

## How this is built

- **Specifications before code.** Every business rule starts as a Gherkin specification under
  `features/`, is reviewed and hash-locked by a human (`gauntlet spec approve`) before any
  implementation exists, and stays hash-locked afterward — a spec cannot silently drift from what
  was approved.
- **Deterministic quality gates.** Gauntlet enforces static analysis, complexity and size limits,
  line coverage ≥90% and branch coverage ≥80% (both are at 100% today), zero duplication, and a
  mutation-proof acceptance suite on every change to the domain layer (`src/claimgate/domain/`),
  which itself contains no I/O, no framework code, no clock reads, and no carrier-specific logic —
  carrier and jurisdiction differences live in configuration and adapters, never in a conditional
  buried in a business rule.
- **Mutation testing, not just coverage.** Coverage measures whether a line ran; mutation testing
  measures whether a test would fail if the code were wrong. Every domain change ships with a
  mutation score, and any mutant judged genuinely equivalent — one no assertion at that layer could
  ever catch — is recorded with a dated, reasoned approval in `gauntlet.lock.json`, not silently
  ignored. There are 67 such approvals today, each carrying its own argument and its own revisit
  trigger.
- **Implementation is written by an AI coding agent.** Specifications, thresholds, business rules,
  and mutant approvals are human decisions the agent cannot make or override — the gate harness
  exists to enforce that boundary, not merely to imply it.

## Status

**Phase 1 — the pure domain core: validation, triage, SIU indicators, and duplicate detection — is
complete and gated.** Four specifications under `features/`, all hash-locked; every gate green.

A structured design review of that domain surfaced a series of defects and framing issues, all of
which have now been corrected: SIU indicators became a parallel attribute rather than a queue
override, both SIU thresholds and the duplicate-detection window lost their domain defaults, the
reason-code vocabulary was reconciled across files, Section II required fields became carrier
configuration covering liability as well as injury, and the recognized policy-number prefix set
became configuration rather than a constant. [`QUEUE.md`](QUEUE.md) carries the full record with the
reasoning behind each, and the remaining open items.

Phase 2 — the HTTP and persistence shell — is fully designed but not yet built. Every decision
behind it, with its reasoning, is in [`PHASE2_DESIGN.md`](PHASE2_DESIGN.md).

## Documents

| File | What it's for |
|---|---|
| [`PHASE2_DESIGN.md`](PHASE2_DESIGN.md) | Every phase-2 design decision — record states, audit log, HTTP surface, idempotency, jurisdiction handling, SIU handling — written as decisions with reasons, not a task list. |
| [`ASSUMPTIONS.md`](ASSUMPTIONS.md) | Every unverified assumption this design rests on, every undocumented phase-1 threshold, and every domain defect found but not yet fixed, each with what was assumed and what would correct it. |
| [`STATUTORY_REGISTER.md`](STATUTORY_REGISTER.md) | Every regulatory value referenced by the design, with citation, verification date, and source — because Florida amends these statutes nearly every session. |
| [`QUEUE.md`](QUEUE.md) | The ordered record of known domain defects and gaps, closed and open, in severity order, with one line of reasoning each for why it sits where it does. |
| [`docs/decisions.md`](docs/decisions.md) | Phase-1 business rule decisions as originally recorded — see `ASSUMPTIONS.md`'s audit of this file for which entries are well-founded and which aren't. |
| [`docs/harness-findings.md`](docs/harness-findings.md) | What using the Gauntlet gate with Claude Code harness surfaced; notes for agents working on this project |
| [`CLAUDE.md`](CLAUDE.md) | The instructions and standing constraints governing how this project's implementation work is done — one of the more interesting artifacts here for anyone evaluating how the work was governed. |

## Disclaimer

**Every carrier name, carrier code, NAIC identifier, notice, policy number, name, contact detail,
and loss description in this repository is fabricated or a placeholder.** No real claim data, of any
kind, from any source, appears anywhere in this project, and no affiliation with or endorsement by
any insurer, managing general agency, or policy administration vendor is claimed or implied. Read
[`DISCLAIMER.md`](DISCLAIMER.md) in full before treating anything here as authoritative about any
real insurer, and note that statutory citations were verified on a specific date and may be stale by
the time you're reading this.
