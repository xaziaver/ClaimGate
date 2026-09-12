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
duplicate-detection window, and whether a claimant's name and contact details block intake. A
caller must state each one on every call. A configurable
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
  ignored. As of 2026-09-01 there are 76 such approvals, each carrying its own argument and its own revisit
  trigger.
- **Implementation is written by an AI coding agent.** Specifications, thresholds, business rules,
  and mutant approvals are human decisions the agent cannot make or override — the gate harness
  exists to enforce that boundary, not merely to imply it.

## Status

**Phase 1 — the pure domain core: validation, triage, SIU indicators, and duplicate detection — is
complete and gated.** A structured design review of that domain surfaced defects and framing
issues, all since corrected: SIU indicators became a parallel attribute rather than a queue
override, both SIU thresholds and the duplicate-detection window lost their domain defaults, the
reason-code vocabulary was reconciled across files, Section II required fields became carrier
configuration covering liability as well as injury. The recognized policy-number prefix set, made
configuration in that pass, was retired outright in phase 3 (item 7d) with the shape check it served.

**Phase 2 — the HTTP and persistence shell — is complete and gated, merged 2026-08-30.** Notice
intake, idempotency, pended-notice resolution, the append-only audit log, SIU separation, and
jurisdiction selection are built against the decisions in [`PHASE2_DESIGN.md`](PHASE2_DESIGN.md).
Eleven specifications under `features/`, all hash-locked; every gate green. What phase 2
deliberately does not include — a server binding, authentication, a policy administration adapter
— is stated there rather than discovered later.

**Phase 3 — the policy administration adapter, read side — is complete and gated, merged
2026-09-11.** Two ports behind one interface, two implementations of each (a live binding and a
periodic extract), coverage verification as an intake outcome with as-of provenance, and duplicate
detection wired to its caller, built against [`PHASE3_DESIGN.md`](PHASE3_DESIGN.md). Sixteen
specifications under `features/`, all hash-locked; 966 tests; every gate green.

**`main` is tagged `prototype-1` at `be87d38`, and the build is paused there.** The tag is the
frozen subject for improving the test harness that gated it: every finding about that harness is
in [`docs/harness-findings.md`](docs/harness-findings.md) and, for the tool's own repository, in
agent-gauntlet's `gauntlet-findings.md`. The clean-up stage that followed the tag — the queue,
assumptions and harness history moved to `docs/queue-history/`, the live documents reduced to what
is in force — closed 2026-09-12 with no gated file changed. Phase 4 opens on the improved harness.
[`ROADMAP.md`](ROADMAP.md) states what "pilotable" means, which phase carries each missing piece,
and what is out of scope permanently; [`QUEUE.md`](QUEUE.md) is the live queue and says where
things stand.

## Documents

| File | What it's for |
|---|---|
| [`ROADMAP.md`](ROADMAP.md) | What "done" means for ClaimGate as a product, which phase carries each missing piece, and what is permanently out of scope — with the reasoning, and with its ratification status stated in the file. |
| [`PHASE2_DESIGN.md`](PHASE2_DESIGN.md) | Every phase-2 design decision — record states, audit log, HTTP surface, idempotency, jurisdiction handling, SIU handling — written as decisions with reasons, not a task list. |
| [`PHASE3_DESIGN.md`](PHASE3_DESIGN.md) | Every phase-3 design decision — the two ports, three-valued answers with as-of instants, coverage verification, identification by search, the swappability proof — ratified 2026-09-01. |
| [`ASSUMPTIONS.md`](ASSUMPTIONS.md) | The index of every assumption and decision by status at `prototype-1` — in force, open, settled or record — with provenance and a pointer to its full text in the history. New decisions go at its end. |
| [`STATUTORY_REGISTER.md`](STATUTORY_REGISTER.md) | Every regulatory value referenced by the design, with citation, verification date, and source — because Florida amends these statutes nearly every session. |
| [`QUEUE.md`](QUEUE.md) | The live queue: the open items, a memoryless status section, the baseline every change is checked against, and a reading table per item. |
| [`docs/queue-history/`](docs/queue-history/) | Everything the build produced, moved out of the live documents byte for byte: the phase-1–3 queue and its status log, the full assumptions text and its classification, the harness chronology, the phase-3 design measurements, and the events log as it stood at the tag. |
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
