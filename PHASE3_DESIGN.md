# Phase 3 design decisions — the core-system ports

Decided 2026-09-01 with the advisor, from reading the phase-2 shell as built rather than as
described. **Status: ratified 2026-09-01 by the human, from the committed file at `ee8b4b3` (256
lines, sha256 `5373264f02e7debe`).** Phase-3 implementation items are queued against this file.
Scope is what `ROADMAP.md` assigns to phase 3 and nothing more: the read side. The write operation
is named where the interface has to be designed with it in view, and is not built.

Written as decisions with reasons and stated costs. Where a decision reverses closed phase-1 or
phase-2 work it says so by item number, because the reversal is the point of recording it.

## What the code actually does today, which this design is built against

Established from `src/claimgate/shell/` at `4a42d2f`, 2026-09-01. Treat as measurements.

- **Intake path.** `notice_intake._decide`: rule evaluation runs holding no transaction. The
  receipt transaction commits; `apply_domain_rules` runs; a second transaction writes the decision
  and, on `TRIAGED`, the SIU indicator events. An exception in evaluation leaves the notice at
  `RECEIVED` for the client's retry to replay.
- **Resolution path.** `resolution.resolve_notice` opens one transaction and `_judge` runs
  `apply_domain_rules` inside it. The two paths have different transaction shapes.
- **`Candidate.continuous_coverage_date` has no producer in the shell.** The recent-inception
  indicator is `NOT_EVALUATED` on every real notice.
- **`find_duplicates` has no caller in the shell.** Its callers are `tests/api/duplicates.py` and
  `tests/unit/test_duplicates.py`. `window_days` is already carrier configuration
  (`carrier_configuration.py`) and is loaded on every call and used by nothing.
- **Notice content** (`shell/messages.py`, `NoticeFields`): `policy_number`, `loss_date`,
  `loss_type`, `notice_type`, `property_state`, `claimant_name`, `claimant_contact`,
  `incident_description`. No insured name and no risk address beyond the state.
- **Attribute storage pattern.** `siu_indicator_events` is an append-only table keyed
  `(notice_id, ordinal)`, one row per indicator per evaluation, with `ruleset_version` and
  `evaluated_at`, and `BEFORE UPDATE`/`BEFORE DELETE` triggers. `jurisdiction_marking` is a
  nullable column on `notices`.

## Two ports, not one adapter

**Decision.** Phase 3 defines two independent port protocols: a **policy port** and a **claims
port**. Each is implemented and configured separately; a deployment binds each per `carrier_code`.

**Why.** In two of the three exemplar shapes — synchronous policy API with term history;
synchronous API with a separate claims module; periodic extract with no live query — policy and
claims are separate systems with separate interfaces. A deployment can have a live policy API and
a nightly claims extract at the same time. One interface would force one implementation to serve
both, which is the coupling "fit any target" forbids. Two ports also make the third exemplar
shape a *configuration* (a live policy port beside an extract claims port) rather than a third
implementation.

**Cost.** Two things to configure, two to swap-test, two contract suites.

**Vocabulary.** "Policy administration system" in earlier documents means the whole core system
(`ASSUMPTIONS.md`, 2026-09-01). This file says "policy port" and "claims port". Exemplar
*shapes* are named; vendors are not — no module, fixture, or scenario carries a vendor's name.
Anything vendor-specific is a mapping a real integration writes; this design never claims to be
one.

### Policy port operations

1. **`search`** — inputs: whatever identifiers the notice carries (policy number, insured name,
   risk address). Returns zero, one, or several candidate policies, each with a **policy
   reference** (the source system's own identifier, which is not necessarily the policy number
   the reporter gave), the named insureds, and a match basis.
2. **`term_history`** — for a policy reference: every term with effective and expiration dates,
   plus dated status events — cancellation (with effective date), non-renewal, reinstatement
   (with effective date and whether retroactive), pending cancellation. Raw history; no
   derivation.

### Claims port operations

3. **`existing_claims`** — for a policy reference: the claims on that policy as
   `ExistingClaim` records (`domain/models.py`), which is what `find_duplicates` already takes.

**Carried into phase 6, not built:** `register_claim` on the claims port — hand the notice over,
receive a claim number. Named so the claims port is designed knowing a write is coming; any
phase-3 shape that would make it awkward is the wrong shape.

## Every port answer is three-valued, carries an as-of instant, and never raises

**Decision.** Each operation returns a result whose value is `FOUND`/`NOT_FOUND`/`NOT_EVALUATED`
(search), or the data/`NOT_EVALUATED` (history, claims), with a reason code on `NOT_EVALUATED`
from a closed enumeration this feature owns — `SOURCE_UNAVAILABLE`, `SOURCE_TIMEOUT`,
`SOURCE_MALFORMED`, `IDENTIFIERS_INSUFFICIENT` — and an **`as_of`**: the instant the answer
reflects. For a live query that is the call instant; for an extract it is the extract's
generation instant, which may be a day old. **A port implementation catches everything and
returns `NOT_EVALUATED`; nothing propagates into the shell.**

**Why never raise.** `_decide`'s contract is that an exception means "the rules could not be
evaluated, leave the notice at `RECEIVED`, the retry replays." A port fault is not that: the
notice must still be decided, and the retry would meet the same outage. The standing rule — a
result not computed is never reported as a negative — is why the fault is a value, not an
exception.

**Why `as_of` is on every answer.** Policy systems process backdated transactions. "In force on
2026-06-01?" can answer differently on two days. A stored answer with no as-of instant is
indefensible in a coverage dispute later; this is `RULESET_VERSION`'s discipline applied to data
the system did not compute itself. The extract shape makes it visible: a policy bound after the
extract ran is `NOT_FOUND` as of last night, and the reviewer who sees the pend sees the as-of.

**Cost.** A new closed reason-code enumeration, scoped to this feature per `CLAUDE.md`, not
merged with duplicate detection's or SIU's. Extract-shape deployments will pend a notice on a
policy newer than the extract — accepted; a loss within a day of binding is rare and is itself
what the recent-inception indicator exists for.

**Timeouts** are per-binding configuration with no default. The decision transaction is delayed
by at most the sum of the configured budgets; receipt is already committed and the acknowledgment
clock already running before any port is called.

## Where the calls sit

**Intake path.** Between the receipt transaction and the decision transaction, where
`apply_domain_rules` already runs, holding no lock. Order: `search` → `term_history` (needs the
reference) → `existing_claims` (needs the reference) → domain rules over everything. Then the
decision transaction writes the decision, the SIU events, the coverage-verification row and the
duplicate-evaluation row together, so a notice never rests `TRIAGED` with half its attributes.

**Resolution path — restructured to match.** `_judge` currently runs inside the write transaction.
With port I/O there, a staff action holds the single-writer lock for an external round trip, or a
full timeout budget during an outage, against the intake path — a statutory duty waiting on an
internal one. **Decision:** the resolution path reads the merged view in one transaction,
evaluates outside any transaction, and writes in a second, re-checking inside that transaction
that the notice is still `PENDED` and answering `409` if it has moved. Behaviour on
`resolution.feature`'s surface is unchanged; the re-check is a unit-tested guard, since Gherkin
cannot express the race. **Cost:** a phase-2 module is reopened for structure, and a concurrent
resolution of one notice becomes a real path where it was previously excluded by the lock.

Both paths evaluate on every transition into `TRIAGED`, on the merged view — item 5f's precedent.

## Coverage verification as an intake outcome

Two questions, two different kinds of answer. **Verification is clerical; determination is not
ClaimGate's** (`ROADMAP.md`, "Out of scope permanently").

**Policy identification.** From `search`:

| result | outcome | why |
|---|---|---|
| exactly one candidate | matched; proceed | |
| zero candidates | **blocker** `POLICY_NOT_MATCHED` → `PENDED` | intake has nothing actionable; a reviewer can correct identifiers through resolution, which is what `PENDED` is for |
| several candidates | **blocker** `POLICY_AMBIGUOUS` → `PENDED` | a reviewer chooses; intake must not |
| `NOT_EVALUATED` | **not a blocker** → `TRIAGED`, verification `NOT_EVALUATED` with reason | a reviewer cannot resolve an outage, and pending a book's worth of notices on infrastructure asks humans to clear a machine fault one notice at a time |
| identifiers insufficient to search | **blocker** `POLICY_IDENTIFIERS_INSUFFICIENT` → `PENDED` | see the sufficiency rule below |

The `NOT_EVALUATED`-lands-`TRIAGED` row has a consequence for phase 6: a notice cannot be
registered downstream with an unverified policy, so phase 6 owns a **system re-evaluation** path
— the `SYSTEM`-actor transition `PHASE2_DESIGN.md` describes as carried and unbuilt. Named here;
not built here.

**Term in force at the loss date.** A pure domain rule over the term history and the loss date,
never a blocker, always an attribute on the `TRIAGED` notice:

- `IN_FORCE` — a term is active on the loss date with no cancellation effective on or before it,
  or a cancellation followed by a retroactive reinstatement.
- `NOT_IN_FORCE` — no term covers the date; or a cancellation is effective on or before it with
  no reinstatement, or with a reinstatement that leaves the date in the lapse.
- `BOUNDARY_DAY` — the loss date equals a term's effective or expiration date, or a cancellation
  or reinstatement effective date. Residential terms conventionally run from 12:01 a.m. standard
  time at the described property, and intake holds a date, not an instant. The third value is the
  honest one; downstream resolves it with the loss time.
- `NOT_EVALUATED` — with the port's reason.

A pending cancellation not yet effective on the loss date is `IN_FORCE`. Coverage attaches to a
term, not a policy: the result records *which* term — its effective and expiration dates — and
the status that produced the value.

**Continuous-coverage date.** Derived in the domain from the same term history, under the
2026-08-14 semantics unchanged: continuous coverage on the risk, surviving administrative rewrite
and retroactive reinstatement, reset by a genuine lapse. **Decision:** the derivation is a gated
domain rule, not port logic — the 2026-08-14 entry said "the adapter derives"; the location moves
so the lapse rule has a specification and a mutation score. The port supplies history and nothing
else. This gives `Candidate.continuous_coverage_date` its first producer.

## Identifiers: search, not fetch — and policy identification leaves the domain

**Decision.** Notice content gains `insured_name` and a structured risk address — `risk_address`,
`risk_city`, `risk_postal_code` — with `property_state` serving as the address's state component;
there is no second state field. **Sufficiency rule**, a pure domain rule: the notice can be
searched if it carries a policy number, or an insured name together with a risk postal code.
Otherwise `POLICY_IDENTIFIERS_INSUFFICIENT`. **Annotation 2026-09-05: this design omitted that
`policy_number` is a required field in `validation.py`, asserted by two locked `validation.feature`
scenarios and a `notice_intake.feature` row, so the second arm is unreachable at intake until that
requirement is retired. Retired at item 7g, with the wiring, not at 7c or 7d — see `QUEUE.md`.**

**`POLICY_NUMBER_MALFORMED` and `recognized_policy_number_prefixes` are retired.** This reverses
items 4b and 4j. A malformed or wrong number is one weak identifier among several: a contractor's
mistyped number beside a correct insured name and address is a match, not a pend. Today that
notice pends on the number before any search could run — the exact defect the search exists to
fix. `ASSUMPTIONS.md` already recorded that with no named estate the domain prefix check had
nothing left justifying it and the pattern belonged to the adapter layer; this is that decision
carried out. **Cost:** a `validation.feature` reopening. Measured floor at `4a42d2f`: the prefix
scenario carries 3 of the file's 31 approvals and is deleted with them; the other 28 sit on rows
whose subject does not change and are re-measured against the lock at the item, not assumed.
`carrier_configuration.feature` loses a required key, and the carrier rules files lose it too.
**Annotation 2026-09-05: the reopening is five specs, not two. The prefix configuration was also a
Background step in `notice_intake.feature`, `idempotency.feature` and `resolution.feature`, and
`resolution.feature`'s partial-clearance row depended on `POLICY_NUMBER_MALFORMED`; a rule
retirement changes what a column elsewhere can discriminate. Measured against the lock at
`e29410e`: 3 approvals deleted, 37 untouched, 5 file approvals to re-issue.**

## Duplicate detection gets its caller

`existing_claims` from the claims port feeds `find_duplicates` with the `window_days` the carrier
rules already supply. The result is recorded and returned as its own field, not in
`reason_codes` (decided 2026-08-22, `ASSUMPTIONS.md`). Evaluated on every transition into
`TRIAGED`, on both paths. `duplicates.feature` does not change; the shell finally reaches it.
Confirming a duplicate is phase 6's `SUPERSEDED` and is not here.

## Persistence

Two new append-only tables on `siu_indicator_events`' pattern — `(notice_id, ordinal)`,
`ruleset_version`, `evaluated_at`, update and delete triggers:

- `coverage_verifications`: identification value and reason, matched policy reference, term value
  and reason, the term's effective and expiration dates, the status that produced the value, the
  port's `as_of`, the binding that answered.
- `duplicate_evaluations`: the `DuplicateMatchResult` — value, reason, matched claim ids.

Not columns on `notices`; the notice row stays narrow and each evaluation is a dated fact. Store
only what the outcome needs — the matched reference, the deciding term, the status — never the
full history the port returned: it is another system's PII held for no purpose ClaimGate has.
Both tables are ordinary, unrestricted attributes: they are on the allow-list serializers for
`GET /notices/{id}`; SIU stays where it is.

## Configuration

A third per-carrier file beside identity and rules: **bindings** — which policy port
implementation and which claims port implementation serve this `carrier_code`, with each
binding's parameters and timeout budget. Looking a binding up by `carrier_code` is a lookup,
exactly as the rules lookup is, not a branch. An unresolvable binding is a deployment fault on
item 5i's pattern: `500`, a new code in `shell/faults.py`, nothing past receipt persisted.

## Swappability proof

Two conforming implementations per port, the same contract suite and the same acceptance
scenarios run against each:

- **Live-query shape**: answers at call time from an in-process fixture service, exercising the
  timeout and unavailability paths.
- **Extract shape**: reads a generated file set carrying an `as_of` instant, exercising staleness
  — a policy bound after the extract is `NOT_FOUND` as of that instant.

Neither talks to a real system, and this document does not pretend otherwise. What they prove is
narrower and real: the shell holds no branch on which implementation it was given, the two
shapes' failure modes both arrive as `NOT_EVALUATED` with distinct reasons, and a live policy port
beside an extract claims port is a configuration rather than code. If either proves hard to
write, the difficulty is the finding to report (`PHASE2_DESIGN.md`, "Swappability proofs").

## Persistence engine, revisited as scheduled

SQLite stays. With evaluation outside every transaction on both paths, no port I/O is ever held
under the write lock, which was the only phase-3 pressure `ASSUMPTIONS.md` named. Revisit again
at phase 5 if the deployment story needs more than one process.

## Rules of the road for the items this produces

- Every new rule is a domain function taking data, gated: term-in-force, continuous-coverage
  derivation, identifier sufficiency. The ports are shell; no port code is under mutation scope,
  and that is a known gap (`docs/harness-findings.md`), not a surprise.
- `RULESET_VERSION` bumps: new rules change decisions.
- No scenario names a port, a table, or a column. Step definitions reach ports through
  `tests/api/`; the boundary gate enforces only the `claimgate` import root, so review holds the
  rest.
- Item order is dependency order: the pure rules first, each with its spec; then the port
  protocols and the live-query implementation; then intake wiring and persistence; then the
  resolution restructure; then the extract implementation and the swap proof. The
  `validation.feature` reopening is its own item with its own measured blast radius.
