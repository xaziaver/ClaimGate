# ClaimGate

ClaimGate is a First Notice of Loss (FNOL) intake service, designed to sit in front of several
different policy administration systems operated by one organization on behalf of multiple
carriers. Its business rules are written against Florida residential property insurance statute,
and the design targets a concrete three-carrier estate — see [`DISCLAIMER.md`](DISCLAIMER.md)
before reading further.

The core design commitment: regulatory rules vary by **jurisdiction**, not by carrier, and carrier
identity is data, never behavior. A policy administration system is a replaceable adapter behind
one interface. Nothing in the domain should need to change to add a second carrier, a second
jurisdiction, or a second policy admin system — see the swappability tests described in
[`PHASE2_DESIGN.md`](PHASE2_DESIGN.md) for how that claim is proven rather than argued.

## How this is built

- **Specifications before code.** Every business rule starts as a Gherkin specification under
  `features/`, is reviewed and hash-locked by a human (`gauntlet spec approve`) before any
  implementation exists, and stays hash-locked afterward — a spec cannot silently drift from what
  was approved.
- **Deterministic quality gates.** Gauntlet enforces static analysis,
  complexity and size limits, 90%+ line and branch coverage, zero duplication, and a mutation-proof
  acceptance suite on every change to the domain layer (`src/claimgate/domain/`).
  `src/claimgate/domain/` contains no I/O, no framework code, no clock reads, and no carrier-
  specific logic — carrier and jurisdiction differences live in configuration and adapters, never
  in a conditional buried in a business rule.
- **Mutation testing, not just coverage.** Coverage measures whether a line ran; mutation testing
  measures whether a test would fail if the code were wrong. Every domain change ships with a
  mutation score, and any mutant judged genuinely equivalent — one no assertion at that layer could
  ever catch — is recorded with a dated, reasoned approval in `gauntlet.lock.json`, not silently
  ignored.

## Status

Phase 1 (the pure domain core: validation, triage, SIU indicators, duplicate detection) is
implemented and gated. A structured design review of that domain surfaced several defects and
framing issues that are queued for correction — see [`QUEUE.md`](QUEUE.md) — before phase 2 (the
HTTP and persistence shell) begins. Phase 2 itself is fully designed but not yet built; every
decision behind it, with its reasoning, is in [`PHASE2_DESIGN.md`](PHASE2_DESIGN.md).

## Documents

| File | What it's for |
|---|---|
| [`PHASE2_DESIGN.md`](PHASE2_DESIGN.md) | Every phase-2 design decision — record states, audit log, HTTP surface, idempotency, jurisdiction handling, SIU handling — written as decisions with reasons, not a task list. |
| [`ASSUMPTIONS.md`](ASSUMPTIONS.md) | Every unverified assumption about the target carrier estate, every undocumented phase-1 threshold, and every domain defect found but not yet fixed, each with what was assumed and what would correct it. |
| [`STATUTORY_REGISTER.md`](STATUTORY_REGISTER.md) | Every regulatory value referenced by the design, with citation, verification date, and source — because Florida amends these statutes nearly every session. |
| [`QUEUE.md`](QUEUE.md) | The ordered list of known domain defects and gaps still to be corrected, in severity order, with one line of reasoning each for why it sits where it does. |
| [`docs/decisions.md`](docs/decisions.md) | Phase-1 business rule decisions as originally recorded — see `ASSUMPTIONS.md`'s audit of this file for which entries are well-founded and which aren't. |

## Disclaimer

Carrier names and NAIC identifiers in this repository are public regulatory information. All claim
data — every notice, policy number, name, and loss description — is fabricated. No affiliation with
or endorsement by any named carrier is claimed or implied. Read
[`DISCLAIMER.md`](DISCLAIMER.md) in full before treating anything in this repository as
authoritative about any real insurer, and note that statutory citations were verified on a specific
date and may be stale by the time you're reading this.
