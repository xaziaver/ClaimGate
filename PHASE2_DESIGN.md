# Phase 2 design decisions

Decided in conversation before any phase-2 code existed. Written as decisions with reasons, not a
task list — the reasons are what stop a future maintainer reversing them without understanding
what they'd be giving up. Nothing in this file is built yet. Phase 1's domain core is: all four
specifications under `features/` — validation, triage, SIU indicators, and duplicate detection — are
hash-locked, implemented, and gated. Where a decision was never pinned down precisely enough to
state with confidence, that's marked rather than guessed at.

**This file predates phase 1's design-review corrections and was reviewed against them on
2026-08-18.** Where a passage described phase-1 code, it now describes what is actually there.
Where a passage's *reasoning* was affected, that is called out inline rather than silently
rewritten, so a reader can see which decisions were re-examined and which were merely restated.

## Record state model

**States reachable in phase 2:** `RECEIVED`, `TRIAGED`, `PENDED`.
**Defined now, not reachable until later phases:** `ROUTED`, `SUPERSEDED`, `WITHDRAWN`. Defining
them now means the state enum doesn't need a breaking migration when later phases need them; they
simply have no transitions into them yet.

**There is no rejected, invalid, or discarded state, and there will not be one.** A notice cannot
be refused — notice given is notice received, and the Fla. Stat. 627.70131(1)(a) acknowledgment
clock (7 calendar days) starts at receipt regardless of data quality. A state that discards a
record is not a smaller version of this system; it's a different, disallowed one. If a future
design seems to need one, that's a signal to escalate, not to add it.

**Transitions in phase 2:**

| From | To | Actor | Condition |
|---|---|---|---|
| (none) | `RECEIVED` | `EXTERNAL` | payload capture |
| `RECEIVED` | `TRIAGED` | `SYSTEM` | domain rules found no blocker |
| `RECEIVED` | `PENDED` | `SYSTEM` | domain rules found a blocker |
| `PENDED` | `TRIAGED` | `USER` only | reviewer resolution clears every blocker |

`PENDED → TRIAGED` is USER-only because resolving a pend means judging whether newly-supplied
information actually satisfies what was missing — that's a human call, not a re-run of the same
deterministic rules that produced the pend in the first place. A `SYSTEM`-actor attempt at this
transition is a **refused** attempt, not an invalid request — it still gets an audit entry with
`outcome=REFUSED`, because "attempted and refused" is itself a fact worth keeping.

**Why `RECEIVED` is persisted, durably, with its receipt timestamp, *before* any domain rule
runs — a deliberate two-write design, not an inefficiency:** the receipt timestamp is the
statutory acknowledgment clock's start. It must not depend on whether validation succeeds, is
implemented correctly, or even runs at all — a bug in rule evaluation must never be able to erase
or delay the fact that a notice was received. The timestamp is set once at capture and never
recomputed on any later transition. **Made concrete 2026-08-25, in item 5d's persistence
port:** the receipt transaction — payload record, notice at `RECEIVED`, `RECEIVED` audit entry,
and the idempotency key row if one was supplied — commits before rule evaluation runs, and the
decision is a second transaction. One transaction spanning both would roll the receipt back on any
exception rule evaluation raised, which is precisely what this paragraph forbids.

**Queue, severity, SIU indicators, and duplicate candidates are attributes, not states.** They are
data carried by a `TRIAGED` notice; none of them is itself a place in the state machine. This
directly reverses the phase-1 defect found in `triage.feature`, where an SIU indicator was a queue
override rather than a parallel attribute. That reopening has since merged: `triage.feature`'s
end-to-end scenario is now titled for the property it asserts — SIU indicators recorded separately
and never affecting routing — so phase 2 inherits the corrected shape rather than having to impose
it (`QUEUE.md` item 1).

## Audit log

**Entry schema** (superseding the schema's original `reason_code` field with `blockers`, per the
amendment below — keeping both would have been redundant):

| Field | Notes |
|---|---|
| `notice_id` | |
| `from_state` | null only on the very first entry for a notice |
| `to_state` | |
| `actor_id` | caller-asserted in phase 2 — see `actor_authenticated` below |
| `actor_type` | one of `SYSTEM`, `USER`, `EXTERNAL`, `SERVICE`; never blank |
| `occurred_at` | UTC |
| `blockers` | the full `{code, field}` list, not just derived `reason_codes` — audit wants maximum fidelity, not the API's coarser view |
| `note` | optional free text |
| `ruleset_version` | hand-declared semantic label (e.g. `1.0.0`) for the domain rules that produced a `SYSTEM` decision |
| `build_sha` | domain package commit SHA, captured once at process startup |
| `outcome` | `APPLIED` or `REFUSED` — every transition *attempt* gets an entry, including refused ones |
| `actor_authenticated` | boolean recording whether the actor's identity was verified by an authentication mechanism. **`false` on every entry, for every actor type, no exceptions — including `SYSTEM` and `SERVICE` actors, with no inferred trust on the grounds that they are deployed code.** Phase 2 has no authentication mechanism at all, so nothing has been verified; this is the same reasoning as "unevaluated is not negative," pointed the other way — never record something as verified when nothing verified it. Phase-2 rows must stay distinguishable from authenticated ones written later. |
| `carrier_code` | attribution only — required by the Carrier reference section, omitted from this table until 2026-08-24; added in item 5d's schema |

**Append-only. No update path and no delete path exist in this schema, in phase 2, at all.**
Corrections are compensating entries, never edits to history.

**The raw inbound payload is stored once, verbatim, immutable, and referenced by hash — never
copied into audit entries.** Audit entries record the transition and the decision, not the data
itself. A resolution's supplemental data gets its own separate immutable payload record with its
own hash, linked to the notice in order (see Pending Resolution below) — the same principle applied
to every write, not just the first one.

**Statutory grounding, worth stating explicitly rather than leaving implicit:** Fla. Stat. 627.70131(4)(b)
requires an insurer to maintain claim records — including dates — of any claim-related
communication between insurer and policyholder, receipt of proof-of-loss, claim-related information
requests, inspections, detailed loss estimates, the start and end of any tolling period under
627.70131(8), and payment/denial. An FNOL is a claim-related communication under (4)(b)1. **This
audit log is the system of record for that specific statutory entry** — not merely "good audit
practice," but the actual recordkeeping duty. 627.70131(5)(b) defines "insurer" for this section as
any residential property insurer; (9) extends it to surplus lines insurers writing residential
coverage. A Florida residential property book is squarely inside that scope.

## HTTP surface

Four endpoints:

- `POST /notices`
- `GET /notices/{notice_id}`
- `GET /notices/{notice_id}/audit`
- `POST /notices/{notice_id}/resolution`

**Status codes, closed:**

| Case | Status |
|---|---|
| `POST /notices`, schema-invalid | `400`, no notice created, submission recorded |
| `POST /notices`, unknown/malformed `carrier_code` | `400`, nothing persisted |
| `POST /notices`, schema-valid, lands straight in `TRIAGED` | **`201 Created`** |
| `POST /notices`, schema-valid, lands in `PENDED` | **`201 Created`** — same code as the row above |
| `POST /notices`, idempotency key replay | **`200 OK`** — nothing was created |
| `POST /notices`, idempotency key reused with a different payload | `409` |
| `POST /notices/{id}/resolution`, notice not currently `PENDED` | `409` |
| `POST /notices/{id}/resolution`, blockers cleared | **`200 OK`** |
| `POST /notices/{id}/resolution`, blockers still present | `422` |

The two `201`s being identical is deliberate, not an oversight: a notice is created and
addressable at `GET /notices/{notice_id}` in both cases, which is what `201` means. `202` would
imply processing is incomplete, but the state is final and present in the body the moment the
response is sent. Differentiating status by state would duplicate what the body already says — the
same two-sources-of-truth problem that removed the standalone `valid` assertion from
`validation.feature` — and a caller branching on status instead of reading the body breaks the
moment a new state is added. `POST /notices` always includes a `Location` header pointing at the
new notice; **state is read from the body, always, never inferred from status.**

The idempotency replay is `200`, not `201`, for the same reason in reverse: nothing was created, so
`201` would be a false statement about what happened. Its body is identical in shape to the original
response — same `notice_id`, same receipt timestamp — but carries the notice's *current* state, not
the state at first processing.

**The asymmetry between `POST /notices` and `POST /notices/{id}/resolution` is deliberate, not an
inconsistency:** `POST /notices` never returns a 4xx once a payload clears the schema boundary,
because accepting a notice is a statutory duty — there is no failure mode past that point that the
system is allowed to refuse. `POST /notices/{id}/resolution` *does* return a 4xx on failure, because
a resolution is an internal staff action, not a notice — refusing it creates no statutory duty, and
telling the reviewer their submission didn't clear the pend is the useful, correct answer.
**Annotated 2026-08-24:** the status-code table's `409` for a reused key with different content does not contradict this — the idempotency lookup is evaluated *before* the schema boundary, alongside the carrier-identity check, so the claim holds as written. Comparison rule, ordering, and the 24-hour tie are decided in `ASSUMPTIONS.md`, "Idempotency: what a repeated key is compared against".

**`notice_id`, not `claim_id`.** ClaimGate does not issue claim numbers. A claim number is assigned
by the policy administration system once phase 3's adapter boundary exists, and will be stored as a
separate, nullable field then. Reusing one identifier for both would silently couple ClaimGate's
identity to a system it's designed to be swappable behind.

**Both `GET` endpoints are internal/staff-facing, and both are unauthenticated in phase 2 — a known
limitation, stated here rather than discovered by a compliance officer during a demo.** No
authentication mechanism exists yet; network-level restriction (e.g. not exposing the service
publicly) is the only access control that exists today. `GET /notices/{notice_id}/audit` in
particular will return PII to anyone who can reach it. This is resolved when an auth system arrives,
not before — it is not something to work around with an ad hoc check in phase 2.

A reporter-facing view, if one is ever added, is a separate resource with its own coarser vocabulary
— not a public alias for this one. The first consumer of an internal endpoint must not freeze
internal state names into a contract nobody meant to publish.

Decided 2026-08-22: they do not — see `ASSUMPTIONS.md`. The question and its reasoning are kept 
below as the record of why it was a real question either way.
**Carried requirement, undecided: whether duplicate-detection `NOT_EVALUATED` reason codes belong in
the notice's `reason_codes` field.** `duplicates.feature`'s notice-type rule (`QUEUE.md` item 3)
resolves a `SUPPLEMENTAL`, `REOPENED`, or `LOSS_ASSESSMENT` candidate to `NOT_EVALUATED` with a
reason code (`FOLLOW_ON_NOTICE_TYPE`, `NO_EXISTING_CLAIM_NOTICE_TYPE`) instead of running the
comparison. This is not settled by the SIU exclusion rule under "SIU handling" below: SIU codes are
kept out of `reason_codes` because SIU is restricted-read, and duplicate candidates are the
opposite — an ordinary, unrestricted `TRIAGED` attribute, not a separate access-controlled table.
Whether these two reason codes surface in the notice's `reason_codes` list alongside validation
blockers, or stay scoped to a duplicate-candidates-specific field, is a real, undecided question
with a real rule behind it either way — resolve before the serializer is written, not after.

## Persistence engine

SQLite, via the stdlib `sqlite3` module, STRICT tables, constraints declared in the schema — not
an ORM, not a separate server process. Decided 2026-08-24, advisor-recommended, human-ratified.
This document decides everything about the writes above and, until now, nothing about what
performs them.

**Why:** the Idempotency section immediately below requires uniqueness on `(carrier_code,
idempotency_key)` "enforced by a database constraint" — a literal `UNIQUE` constraint on those two
columns satisfies that directly, with no new dependency. The two-write receipt (Record state
model, above) becomes a single real transaction rather than two calls into an in-memory dict that
happen to run in the same process, which is what makes `store.py`'s "the raw payload and the
RECEIVED write are one statutory fact" comment an enforced guarantee instead of a comment
describing call order. And the swappability proofs item 5g owes (Swappability proofs, below) are
data-swaps — a different carrier set, a different jurisdiction map — not engine-swaps; nothing in
this design asks persistence itself to be pluggable, so nothing is lost picking one engine now.

**Costs, stated rather than discovered later:** single-writer concurrency, and no server-side
access control beyond what the process itself enforces. Both accepted for phase 2. Both are
revisited at phase 3's adapter boundary — the same boundary that already owns policy
administration and claim-number minting (`CLAUDE.md`) — persistence technology joins it there
rather than getting a phase of its own.

## Idempotency

`POST /notices` accepts an optional `Idempotency-Key` **header**, not a body field — it's
transport-layer, not part of the notice.

- **Uniqueness** is `(carrier_code, idempotency_key)`, enforced by a **database constraint**, not a
  check-then-write. Concurrent identical requests must resolve by constraint violation, not by a
  race condition. The same key from two different carriers is not a collision.
- **Keys expire after 24 hours.** Past that window it isn't a network retry anymore, it's a
  resubmission — and a resubmission should go through business duplicate detection, which is the
  mechanism built for that.
- **A replay returns `200 OK`** (not `201` — nothing was created) with **the original `notice_id`
  and receipt timestamp, but the *current* state**, not the state at first processing — the notice
  may have moved since. See the status code table under HTTP Surface.
- **Replays stay out of the audit trail** — operational logs only, since a replay isn't a state
  transition.
- **Why this has to be distinct from business duplicate detection:** a bare network retry of the
  same request looks, to the duplicate matcher, identical to a genuinely separate loss on the same
  policy within the match window. Without an idempotency key, retries would pollute
  duplicate-candidate matching with technical noise, corrupting a signal meant to catch real
  duplicate losses.

## Jurisdiction axis

**Statutory rules vary by jurisdiction, not by carrier — this is the single most important
structural decision in phase 2 planning.** Several carriers under one administrator are subject to identical
Florida statute; a shared carrier does not imply shared law, and a shared jurisdiction is not
carrier-specific. `carrier_code` and jurisdiction are independent axes: a carrier can write in
several states, and a state governs several carriers.

- `carrier_code` identifies which policy admin system/adapter applies (a phase-3 concept).
- Jurisdiction selects which statutory ruleset applies.

**Jurisdiction is derived from the insured risk's property location — the property's state — never
from the carrier's domicile and never from the reporter's address.** `property_state` is captured
on the notice for this purpose.

**Phase 2 behavior:** statutory config is a real map keyed by jurisdiction code, with exactly one
entry populated (`FL`) — a genuine lookup, not a constant dressed up as one. If `property_state` is
absent, or present but not `FL`, the notice is **not** blocked: it proceeds to `TRIAGED` with a
`jurisdiction_unsupported` attribute for human review. No jurisdiction-based branching exists
anywhere beyond that one config lookup — the requirement is that `FL` is *one entry in a keyed
structure*, not a second jurisdiction, multi-state feature, or any state-specific logic. Do not
build either of those in phase 2.

## Carrier reference

A static, version-controlled file holding **identity only** — no thresholds, no behavior — separate
from the per-carrier rules file that holds the six caller-supplied configuration values. 
**Corrected 2026-08-22: that rules file was originally placed in phase 3, before items 2, 3, 4g, and 4j 
made six domain values caller-supplied with no default. The shell cannot call the domain without them, 
so it is phase-2 work — see `QUEUE.md` item 5a and `ASSUMPTIONS.md`. Identity and rules remain separate files.**

| Code | Carrier | NAIC | NAIC group |
|---|---|---|---|
| `AAAA` | Placeholder Carrier A | 10001 | 4001 |
| `BBBB` | Placeholder Carrier B | 10002 | 4001 |
| `CCCC` | Placeholder Carrier C | 10003 | null |

`carrier_code` is exactly 4 uppercase A–Z characters. **Every value in this table is synthetic** —
codes, NAIC numbers, and group numbers alike — and a real deployment substitutes its own at
integration. The third row's null group code is deliberate and must survive substitution: a
member-owned reciprocal may be grouped by management rather than ownership, so a shared
administrator does not imply a shared group, and the schema has to tolerate the absence.

`carrier_code` is **envelope, not notice content.** It's required on every request, validated
against this reference list, and persisted on every notice and every audit entry — for
attribution only. **It is never branched on.** An unknown or malformed `carrier_code` returns
`400` and persists nothing: a notice for a carrier this deployment isn't configured to administer
creates no statutory duty here, so the always-accept rule doesn't extend to it. There's no notice to attribute
an audit entry to in that case; the rejection is logged operationally, not in the notice audit
trail. This is the concrete form of "carrier identity is data, carrier behavior is configuration" —
if any phase-2 code path reads `carrier_code` to make a decision, that's carrier logic leaking into
the domain, and it should stop and get escalated rather than shipped.

## Notice type and window selection

`notice_type` is **required on every notice, with no default.** An absent value is
`MISSING_REQUIRED_FIELD`; an unrecognized value is the distinct `NOTICE_TYPE_UNRECOGNIZED`, not
collapsed into the missing case (a realistic near-miss like `"SUPPLEMENT"` is a caller/integration
version-skew signal, not the same problem as silence). Both of these are implemented and gated
today in `features/validation.feature` and `src/claimgate/domain/validation.py`.

**Why required rather than inferred or defaulted:** a reopened or supplemental notice looks
identical to a duplicate at intake — the field exists specifically because that ambiguity can't be
resolved by anything else the system knows. `notice_type` must never be inferred from duplicate
matches or any other signal; the reporter has to state it.

Enumeration and window, once window selection is built (not yet — see below): `INITIAL` and
`REOPENED` both get a 1-year window, `SUPPLEMENTAL` gets 18 months, both under 627.70132(2).
`LOSS_ASSESSMENT` (condominium unit-owner loss-assessment coverage under s. 627.714) has a
genuinely different rule under 627.70132(4) — see `STATUTORY_REGISTER.md`.

**`LOSS_ASSESSMENT` is accepted and stored today, but its window is not computed at intake, and
should not be guessed at.** Its window needs the condominium association's assessment-vote date,
which intake doesn't have. When window selection is built, a `LOSS_ASSESSMENT` notice's late-notice
attribute should resolve to a `window_not_computable` outcome with a reason — never a silent
fallback to the 1-year window that applies to the other three types.

**A mutation-testing consequence of this, recorded so it isn't mistaken for a gap later:** the four
recognized `notice_type` values are currently behaviorally identical inside `validate()` — none of
them affects validation outcome, only (eventually) window selection — so a mutation test
substituting one recognized value for another in `features/validation.feature`'s "Recognized notice
types are accepted" scenario cannot be caught by any assertion at that layer. This was reviewed and
approved as a genuine equivalent mutant (`gauntlet mutant approve`, recorded in `gauntlet.lock.json`
under `xaziaver`), with an explicit revisit trigger: **the approval is void the moment required
fields vary by notice type**, and `LOSS_ASSESSMENT` — needing the assessment-vote date and probably
the assessment amount that no other type requires — is the likely first case that voids it. When
that lands, re-run those mutants rather than carrying the approval forward.

**Checked 2026-08-18 and not voided.** `QUEUE.md` item 4g made required fields vary — by *loss
type* and by carrier configuration, not by notice type — so the trigger as written has not fired
and the four approvals stand. Recorded here because the next reader to meet item 4g and then this
trigger would otherwise have to re-derive that, and the axis distinction is the whole of the
answer: notice type still has no effect on validation outcome.

## Swappability proofs

The design's central claim is easy integration across policy administration systems and
jurisdictions; these two tests are how that claim is proven rather than argued, and both are demo
artifacts proving the *absence* of hardcoding, not new features:

- **Carrier set swap.** A test loads an alternative carrier reference fixture with different codes
  and shows intake behaves identically. Proves carrier identity is data.
- **Jurisdiction swap.** A test loads a **fictional** second jurisdiction fixture with different
  statutory values and shows the correct values get selected. Proves the FL ruleset is one config
  entry, not a hardcoded assumption. Fixture only — no second real jurisdiction, no state-specific
  logic, no new feature surface.

If either test turns out to be hard to write, that difficulty is itself the finding to report — the
test must not be bent to make it pass.

**What phase 1 already settled, and what these tests therefore still have to prove.** When this
section was written, "carrier identity is data, never behavior" was a claim the domain had not been
made to honor. It now does: the SIU thresholds, the duplicate-detection window, the Section II
claimant-field requirements, and the recognized policy-number prefix set are each caller-supplied
with no default and no fallback, so a carrier difference cannot reach a domain conditional because
there is nothing in the domain left to condition on. These two tests are consequently no longer the
whole argument — they are the *adapter-layer* half of it. What remains genuinely unproven, and what
they exist to establish, is that the shell can carry a second carrier set and a second jurisdiction
ruleset through to those parameters without a branch of its own.

## Pending resolution and tolling

`POST /notices/{notice_id}/resolution` — body: `actor_id` (required), the supplemental field
values, an optional note.

- Notice not currently `PENDED` → `409`, no state change, no audit entry.
- Supplied data clears every blocker → `PENDED → TRIAGED`, audit `outcome=APPLIED`,
  `actor_type=USER`, response **`200 OK`**.
- Supplied data still leaves a blocker → notice **stays** `PENDED`; an audit entry is still
  written, `from=PENDED`, `to=TRIAGED`, `outcome=REFUSED`, carrying the still-failing blockers.
  Response is `422` with the current blockers, same body shape as the `200` case so a reviewer's
  client parses one shape and lets the status distinguish cleared from still-blocked. A refused
  resolution attempt is itself an audit event, not a non-event.
- Unlike `POST /notices`, this endpoint *does* return 4xx on failure — see the asymmetry note under
  HTTP Surface for why that's the correct, deliberate difference and not an inconsistency.

**Supplemental data never mutates the stored payload.** Each resolution writes its own immutable
payload record with its own hash, linked to the notice in arrival order; the "current" view of a
notice is derived from that ordered sequence, never from an overwrite. Audit has to be able to show
what was known at each point in time — overwriting destroys that, and reconstructing it after the
fact is expensive to impossible.

**Tolling — record precisely, compute nothing.** Fla. Stat. 627.70131(8)(b) tolls the section's
deadlines when a policyholder fails to supply requested material information within 10 days of the
request, ending on receipt of that information, and applies only to requests sent at least 15 days
before the pay-or-deny deadline. A `PENDED` notice with a request for missing information is
potentially exactly this. **ClaimGate does not determine whether tolling applies** — that's a
downstream legal determination — but something downstream will compute it from ClaimGate's
timestamps, so:

- Record the pend timestamp and the resolution-received timestamp precisely, in UTC, on the notice
  and in the audit trail.
- Record *which specific information was requested*, not just that something was — already
  satisfied by the `blockers` list's field-level detail (`{code, field}`), which doubles as this
  record without needing a separate structure.
- 627.70131(4)(b)6 requires records of the start and end of tolling periods; the requirement here
  is that the timestamps feeding that computation are unambiguous and immutable, not that ClaimGate
  performs the computation.
- **No tolling logic, and no field named `tolling`, anywhere in phase 2.**

**Carried requirement for phase 5, not phase 2:** a `PENDED` notice needs an age, and operability
needs an alert on the oldest one outstanding. A pended notice carries a live 7-day acknowledgment
clock and a running 60-day pay-or-deny clock — an unbounded pend queue is a statutory-time problem,
not a backlog metric. Not built now; recorded so phase 5's operability work doesn't have to
rediscover it.

## SIU handling

SIU indicators are **not a state and not a field on the standard record projection.** They are a
restricted-read attribute with their own write-side audit trail (not the same trail as the notice's
transition history).

1. **Store SIU indicators in a table separate from the notice record — not as columns on it.**
   Physical separation is the part that's hard to retrofit; access-control layers can be added on
   top of a separate table later, but columns on the main record are a leak risk in every future
   query and serializer, forever.
2. **Response serializers are allow-list based: explicitly named fields only, never a deny-list.**
   A deny-list leaks every field added after it was written.
3. **SIU codes never appear in `reason_codes`, and SIU indicator detail never appears in a standard
   audit entry.** `GET /notices/{notice_id}/audit` would otherwise become the leak path.
4. **Build the write-side trail now: an append-only `siu_indicator_events` table**, recording which
   indicator fired, under which `ruleset_version`, and when. This is write-side correctness,
   needed regardless of whether auth exists. **Do not build the read-side access log until an auth
   system exists to populate it meaningfully** — a read-access log with no real identity behind it
   would be theater, not a record.
5. **Carried requirement: a scenario for the reason-code precedence when both SIU inputs are
   absent, once thresholds come from jurisdiction config.** `compute_siu_indicators` resolves
   `NO_CONTINUOUS_COVERAGE_DATE` over `NO_THRESHOLD_CONFIGURED` when both the recent-inception
   threshold and the continuous coverage date are missing — the missing input outranks the missing
   rule; see ASSUMPTIONS.md's carried-requirements entry for the full principle. Unreachable and
   unspecified today.

   **Corrected 2026-08-18: it is no longer unreachable, and the scenario is now owed.** The original
   deferral rested on the recent-inception threshold being a fixed, always-supplied value of 30.
   `QUEUE.md` item 2 removed both SIU threshold defaults, so the threshold is caller-supplied and
   may be absent — `siu_indicators.feature`'s "No recent policy inception threshold configured"
   scenario proves it. The both-absent combination is therefore producible by the shipped system
   today, and no scenario exercises it: every existing scenario supplies one of the two inputs.
   The precedence is currently protected by a comment in `siu.py` reading "Do not reorder these
   checks" and by nothing else — a reordering would not fail any test, and mutation testing does not
   generate reorderings, so no gate can see it. This is the same shape as the unasserted lower-bound
   guard that mutation testing caught during the triage reopening, arriving where mutation cannot
   help. Sequenced in `QUEUE.md`, not here.
   
   **Delivered 2026-08-18 (`QUEUE.md` item 4k, merge `7da0bd1`): `siu_indicators.feature` now 
   carries "Neither recent policy inception input is present." This carried requirement is closed. 
   Its "from jurisdiction config" phrasing was also wrong on the axis — SIU thresholds are carrier 
   configuration under `ASSUMPTIONS.md`, with the late-reporting threshold the one possible 
   exception, recorded there.**

A Gherkin scenario asserting SIU indicators are absent from both response bodies is required — a
cheap negative assertion that catches a regression the moment someone adds a field carelessly.

**Indicators are factual observations with codes only. Never a conclusion, and never the literal
word "fraud" as a system-generated value** — a system-generated fraud characterization reaching a
reporter is a defamation and bad-faith exposure, not just a design inelegance. This is a live defect
today. **Both halves of that sentence have since been corrected and it is recorded here as history,
not as an open defect:** the specification was renamed to `siu_indicators.feature` and its narrative
rewritten, and the domain type is now `SiuIndicatorResult`, which carries a value and a reason code
rather than a pair of booleans named for a conclusion (`QUEUE.md` items 1 and 2, both merged). What
remains outstanding is unchanged and is phase-2-shell work that hasn't started: the separate
persisted table and the allow-list serializer described above. The vocabulary discipline itself
still binds — an indicator is a factual observation with a code, never a conclusion.
