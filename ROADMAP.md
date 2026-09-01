# Roadmap

What "done" means for ClaimGate as a product, which phase carries each missing piece, and what is
out of scope permanently. Drafted 2026-09-01 with the advisor. **Status: ratified 2026-09-01 by the
human, from the committed file at `42c6903` (186 lines, sha256 `296b3a8a6f8b`), not from a
summary.** Implementation items may now be queued against phase 3 once `PHASE3_DESIGN.md` is
ratified on the same terms; no item is queued against any later phase until that phase's own design
document is (`QUEUE.md`, item 6).

Provenance for every decision here: advisor-recommended, human-ratified 2026-09-01. The one fact
this file rests on that could not come from reasoning: **there is no target deployment.** ClaimGate
is built to fit any policy administration system; the human named Duck Creek as one example
(2026-09-01). If a real target appears, re-read "Why phase 3 ships two implementations" first,
because it is the section a target would change.

**Amended 2026-09-01, after ratification.** The existing-claims read was added to phase 3. The
ratified text placed duplicate-detection wiring in no phase while phase 6 referred to confirming
a duplicate candidate; the gap was found by reading the shell for `PHASE3_DESIGN.md`, not by any
document. The human re-ratifies the amended paragraph from the committed file; the rest of the
ratification stands.

## Target state: pilotable

A claims manager at a Florida residential property carrier or MGA could put ClaimGate in front of
one live intake channel, for one carrier configuration, with real notices flowing to a real policy
administration system, and defend it to their compliance officer. Concretely, all of:

1. Every notice received is durably recorded before any rule runs, with an immutable receipt
   instant — built, phase 2.
2. Every notice is verified against the policy administration system — a policy found or not, the
   term in force at the loss date or not — with the as-of provenance to defend the answer later.
   Phase 3.
3. Every statutory clock that starts at intake is computed and recorded against the notice, and
   none of them gates anything. Phase 4.
4. No PII-bearing surface is reachable without an authenticated, authorized identity, and the
   service runs as a deployed process rather than a set of handler functions. Phase 5.
5. A triaged notice reaches the claim system and carries the claim number back. Phase 6.
6. Someone is told when a pended notice is aging. Phase 7.

The pilot channel is the API itself — an integrating call-centre or agency system posting
notices. Direct reporter channels and attachments are the first post-pilot expansion (phase 8),
not a pilot precondition.

## Phases

Ordered by dependency first, then by risk to the central design claim. One design document per
phase, ratified before that phase's first queue item, on phase 2's precedent.

### Phase 3 — Policy administration adapter, read side

The central design claim — a policy administration system is a replaceable adapter behind one
interface — is unproven today because no adapter exists. Phase 3 proves it.

- **The adapter interface**, designed against three named exemplar system shapes: Duck Creek,
  Guidewire, and a legacy system integrated by periodic flat-file extract with no API at all.
- **Two conforming implementations**, not one. Argued below.
- **Policy search**: resolve a policy from named insured, risk address and loss date, not only from
  a policy number. `POLICY_NUMBER_PATTERN`'s status as an intake blocker is reopened here, and the
  pattern moves to the adapter layer, closing `ASSUMPTIONS.md`'s open decision.
- **Term in force at the loss date**: the term, its effective and expiration dates, and its status
  at that date — active, cancelled effective a date, non-renewed, expired, reinstated — with the
  adapter's as-of instant recorded on the answer. Coverage attaches to a term, never to a policy.
- **Existing claims on the policy**, so that duplicate detection runs. `duplicates.feature` is
  locked, bound and fully killed, and its function's only callers in the repository are tests:
  the acceptance test API and the unit tests. Nothing in the shell calls it, because the
  existing-claims list has no source until an adapter exists (measured 2026-09-01 at `4a42d2f`).
  This read comes from the claims side of the core system, not the policy side; whether phase 3's
  interface is one adapter with a policy port and a claims port, or two adapters, is
  `PHASE3_DESIGN.md`'s decision. A pilot shipping a gated duplicate rule that never runs is a
  defect, which is why this is not deferred to phase 6.
- **Continuous-coverage date**, with the semantics already decided (`ASSUMPTIONS.md`, "Data we do
  not have at intake", 2026-08-13 and 2026-08-14). The recent-inception indicator's `NOT_EVALUATED`
  becomes a real exception path rather than the steady state.
- **Coverage verification as an intake outcome.** Whether an unmatched policy is a blocker
  (`PENDED`) and an out-of-force term is an attribute (`TRIAGED`) is a phase-3 design decision;
  the advisor's recommendation, recorded in `ASSUMPTIONS.md` dated 2026-09-01, is exactly that
  split.
- **Adapter faults resolve `NOT_EVALUATED` with a reason**, never a negative, and never delay or
  erase receipt — the receipt-first design already guarantees the second half.
- **Persistence revisited**, as `ASSUMPTIONS.md` scheduled: the adapter call is external I/O inside
  or beside the decision transaction, and single-writer SQLite must be shown to survive that or be
  replaced. A decision, not a default.
- **`loss_type`'s conflation of perils with Section II coverage categories** is revisited here,
  because the adapter is the first thing that can return the policy's actual coverage parts.

Carried into phase 6 and named here so the interface is designed with it in view, **not built**:
the adapter's write operation — register a claim, receive a claim number.

Not in phase 3: coverage *determination*. See "Out of scope permanently."

#### Why phase 3 ships two implementations

An adapter interface designed against zero real systems comes out shaped like ClaimGate's own
domain model, and every later integration then needs the translation layer the interface was
supposed to be. One implementation cannot show that has not happened; it shows only that the
interface fits the one system it was written against. Two implementations against systems whose
data models genuinely differ are the minimum evidence, and the third exemplar shape — an extract
with no live query — is what stops the interface assuming a synchronous answer exists, an
assumption that would exclude a large share of the actual market.

**Cost, stated:** phase 3 roughly doubles against a single-adapter plan, and the second
implementation has no customer asking for it. It buys the only evidence that the README's central
claim is true rather than asserted — the argument `PHASE2_DESIGN.md` already makes for the
jurisdiction fixture, applied where the claim matters most. If a real target appears, the second
implementation becomes that target's and the argument survives.

### Phase 4 — Statutory clocks: computed and recorded, never gating

Pure domain work with no external dependency. It could have been phase 3 and is not, because the
adapter is the risk and this is not. Sequenced before exposure because it is the last purely
domain phase, and because a Florida pilot without a catastrophe date field does not survive its
first hurricane season.

- **Notice window status** under 627.70132(2): 1 year for `INITIAL` and `REOPENED`, 18 months for
  `SUPPLEMENTAL`, calendar intervals from the loss date; `LOSS_ASSESSMENT` resolves
  `window_not_computable` with a reason (`PHASE2_DESIGN.md`, "Notice type and window selection").
  Recorded as a notice attribute for downstream coverage review. This is the jurisdiction axis;
  the late-reporting SIU indicator is the carrier axis and stays separate.
- **Acknowledgment deadline** under 627.70131(1)(a): receipt instant plus 7 calendar days, recorded.
  Whether ClaimGate *issues* the acknowledgment is phase 6's decision.
- **Weather date-of-loss capture** under 627.70132(3): a field for the named event and its
  statutory date, distinct from `reported_loss_date`. Capture only; ClaimGate does not derive the
  statutory date. This is the whole of the catastrophe handling ClaimGate ever does.
- **Pended-notice age**, from the `pended_at` instant phase 2 already stores.

Every citation above is re-verified against the Legislature's text before any spec is drafted.
`STATUTORY_REGISTER.md`'s verification dates are 2026-08-05 and 2026-08-12; nothing in this file
re-verifies them.

### Phase 5 — Exposure: server binding, authentication, authorization, deployment, retention

Nothing in phases 2–4 may be shown to anyone outside a test harness until this phase closes.

- An HTTP server binding for the phase-2 handlers. The framework is a decision, not a default.
- Authentication for staff surfaces; `actor_authenticated` becomes `true` for the first time, and
  phase-2 rows stay distinguishable from it.
- Authorization: the SIU restricted-read boundary becomes enforced, and the SIU read-side access
  log `PHASE2_DESIGN.md` deferred until an identity exists is built here.
- The reporter-facing view, as a separate resource with its own coarser vocabulary — never an alias
  for the staff endpoints.
- Deployment: process, configuration injection for the carrier reference and rules files, secrets,
  health and readiness.
- **Retention.** The audit log and payload store are append-only with no deletion path, which is
  itself a retention behaviour nobody approved — the one kind of default `CLAUDE.md`'s first
  constraint names explicitly. Phase 5 decides it against a primary source for the Florida
  claim-file retention duty. No period is proposed here because none has been verified.

### Phase 6 — Handoff: `ROUTED`, `SUPERSEDED`, `WITHDRAWN`

- The adapter's write operation: register the claim, store the claim number as a separate nullable
  field (`PHASE2_DESIGN.md`, "`notice_id`, not `claim_id`").
- `ROUTED` reachable from `TRIAGED`; `SUPERSEDED` when a reviewer confirms a duplicate candidate;
  `WITHDRAWN` on reporter withdrawal. None is a refusal state.
- The state set becomes a declared constraint. At `3afdfb2` the `state` column is unconstrained
  `TEXT` and none of the three names appears under `src/`; `PHASE2_DESIGN.md`'s "defined now" was
  corrected on 2026-09-01.
- Acknowledgment issuance: ClaimGate emits an event the carrier's communication system consumes, or
  the claim system acknowledges after registration. Decided here, not defaulted.

### Phase 7 — Operability

Alerting on pended-notice age and adapter fault rate; run books; the metrics a claims supervisor
actually watches. `PHASE2_DESIGN.md`'s "carried requirement for phase 5" is this phase; that
sentence predates this numbering.

### Phase 8 — Reporter channels and attachments

Web form, agency portal, call-centre UI, email or SMS ingestion, mortgagee and vendor feeds;
photographs and documents at first notice, with the storage, scanning and retention that implies.
First post-pilot expansion. Every channel here is a client of the API, not a second intake path.

## Not in any planned phase, not excluded

A second real jurisdiction. The structure supports it (`PHASE2_DESIGN.md`, "Jurisdiction axis"); a
book requiring it triggers a phase. Not planned because no book requires it.

## Out of scope permanently

Justified structurally, not by any customer's absence of need: each belongs to a system ClaimGate
sits in front of or behind, and building it into ClaimGate would make the swappability claim
false. Most are already standing constraints in `CLAUDE.md`; gathered here so the boundary is one
visible line rather than six rules a reader assembles.

- **Coverage determination.** Whether this policy covers this loss — perils, exclusions,
  endorsements, limits, insurable interest. ClaimGate verifies that a policy and a term exist; it
  never decides what they cover. That is an adjuster and coverage-counsel function with
  investigation behind it, and an intake system that performs it is the most common route into
  bad-faith exposure.
- **Claim lifecycle** — open, reserved, in suit, closed, reopened — and **claim numbering.** The
  claim system's.
- **Reserving and payments.** The claim system's.
- **Adjuster assignment** beyond queue routing. Workforce management's.
- **Tolling determination.** Legal. ClaimGate records the instants (`PHASE2_DESIGN.md`).
- **SIU investigation and any fraud conclusion.** The SIU unit's. ClaimGate records indicators.
- **Policy issuance, endorsement, cancellation, reinstatement.** The policy administration
  system's. ClaimGate reads policy data through the adapter and never writes it.
- **Acting on a statutory clock.** ClaimGate computes and records deadlines and window status;
  denying, delaying or gating a notice on any of them is downstream's decision, never intake's.
- **Catastrophe response operations** — CAT declaration, surge routing, CAT deductible application.
  ClaimGate captures the event and its statutory date (phase 4) and nothing more.
