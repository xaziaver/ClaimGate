# Phase 3 design measurements

Moved verbatim from `PHASE3_DESIGN.md` on 2026-09-11, clean-up stage C2d, and not to be edited:
the section "What the code actually does today, which this design is built against". It is six
measurements of the phase-2 shell taken at `4a42d2f` on 2026-09-01, and the four annotations that
items 7f, 7g and 7h added as the work overturned them. Every present-tense statement is true as
of its own date and none is true at `prototype-1`. The design it was written for is
`PHASE3_DESIGN.md`; the code is the authority on the code.

---

## What the code actually does today, which this design is built against

Established from `src/claimgate/shell/` at `4a42d2f`, 2026-09-01. Treat as measurements.

- **Intake path.** `notice_intake._decide`: rule evaluation runs holding no transaction. The
  receipt transaction commits; `apply_domain_rules` runs; a second transaction writes the decision
  and, on `TRIAGED`, the SIU indicator events. An exception in evaluation leaves the notice at
  `RECEIVED` for the client's retry to replay.
- **Resolution path.** `resolution.resolve_notice` opens one transaction and `_judge` runs
  `apply_domain_rules` inside it. The two paths have different transaction shapes.
  **Annotation 2026-09-08 (item 7g, structural commit `ce62f3d`): no longer true.
  `shell/resolution_evaluation.py` reads the notice, its arrival sequence and its latest
  verification in one transaction, judges holding no lock, and writes in a second transaction that
  re-reads the notice and answers 409 if it is no longer `PENDED`; `resolution.py` keeps the 400
  and the 500. The two paths now have the same shape, evaluation between two transactions. The 7f
  annotation's "the resolution path searches nothing and re-asserts the stored match" still holds
  until 7g's port calls land.**
- **`Candidate.continuous_coverage_date` has no producer in the shell.** The recent-inception
  indicator is `NOT_EVALUATED` on every real notice. **Annotation 2026-09-07 (item 7f): no longer
  true. `domain/continuous_coverage.py`'s `carry_onto_candidate` is the producer, called on the
  intake path from `shell/notice_intake.py` with the derivation the policy port's history yields
  and on the resolution path from `shell/resolution_evaluation.py` with the stored verification's
  date; the indicator reads it. The intake-path bullet above still holds in shape - two
  transactions, evaluation between them - with the policy search now running before the rules
  in that gap (`shell/policy_match.py`).**
- **`find_duplicates` has no caller in the shell.** Its callers are `tests/api/duplicates.py` and
  `tests/unit/test_duplicates.py`. `window_days` is already carrier configuration
  (`carrier_configuration.py`) and is loaded on every call and used by nothing.
  **Annotation 2026-09-10 (item 7h closed at merge `fc479e3`, implementation `a1e3e28`, green run
  `20260910T112652-904083`): no longer true. `shell/duplicate_evaluations.py` calls
  `find_duplicates` with the carrier's `window_days` on both transitions into `TRIAGED`, against
  the claims port that `shell/bindings.py`'s `resolve_port_bindings` resolves at receipt and on
  resolution, and the result persists to `duplicate_evaluations` and shows on the notice. The
  claims-port half of the "still as measured" sentences in the 7f and 7g annotations below falls
  with it. Checked against source at `fc479e3`, 2026-09-10, at item 7i's opening; the other
  bullets stand as annotated.**
- **Notice content** (`shell/messages.py`, `NoticeFields`): `policy_number`, `loss_date`,
  `loss_type`, `notice_type`, `property_state`, `claimant_name`, `claimant_contact`,
  `incident_description`. No insured name and no risk address beyond the state.
  **Annotation 2026-09-07 (item 7f): `NoticeFields` has carried `insured_name`, `risk_address`,
  `risk_city` and `risk_postal_code` since item 7c (`e75f5dd`, 2026-09-05), with `property_state`
  serving as the address's state component, so the last sentence no longer holds. The other five
  bullets were checked against source at `56419cf` and hold; since that commit the receipt
  transaction lives in `shell/receipt.py` and `_judge` in `shell/resolution_evaluation.py`, a
  split with no behaviour change.**
- **Attribute storage pattern.** `siu_indicator_events` is an append-only table keyed
  `(notice_id, ordinal)`, one row per indicator per evaluation, with `ruleset_version` and
  `evaluated_at`, and `BEFORE UPDATE`/`BEFORE DELETE` triggers. `jurisdiction_marking` is a
  nullable column on `notices`.

**Annotation 2026-09-07 (item 7f closed, green run `20260907T214626-43332`):** the policy port is
wired at intake — `shell/receipt.py` resolves the carrier's binding beside its rules and
jurisdiction, and `shell/policy_match.py` runs sufficiency, search and term history between the two
transactions — and `coverage_verifications` exists (`shell/coverage_verifications.py`, on
`siu_indicator_events`' pattern, shown on `GET /notices/{id}` through an allow-list of its own).
`Candidate.continuous_coverage_date` has its producer, `carry_onto_candidate`. Still as measured
above: the claims port is resolved by nothing and `find_duplicates` has no shell caller (7h); the
insured-name search and `POLICY_IDENTIFIERS_INSUFFICIENT` are unreachable at intake while validation
requires a policy number, and the resolution path searches nothing and re-asserts the stored match
(7g).

**Annotation 2026-09-08 (item 7g implemented, `828ded3`, green run `20260908T124244-462219`):** validation no
longer requires a policy number, so the insured-name search and `POLICY_IDENTIFIERS_INSUFFICIENT`
are reachable at intake — `shell/policy_match.py::check_policy` runs the sufficiency rule first on
both paths — and the resolution path re-searches on the merged identifiers in
`resolution_evaluation.py::judge`, with the last answering row's match and derivation standing
where the re-search cannot answer, and records every search that ran. The verification row and
the view carry `identified_on`, the port's match basis. Still as measured above: the claims port
is resolved by nothing and `find_duplicates` has no shell caller (7h).

**Annotation 2026-09-08 (item 7g closed at the close-out on `phase3/7g-resolution-research`):**
the paragraph above is the state at close, confirmed by run `20260908T124244-462219` and the
stop-check `20260908T133307-609373` after it. Two bullets of the measured list are now stale in
full — the resolution-path bullet, since `ce62f3d`, and the intake-path bullet's "no policy number
pends on validation" reading — and the claims-port bullet holds until 7h. One consequence the
identification table above does not state: `POLICY_AMBIGUOUS` cannot clear through the re-search,
which takes identifiers, so a reviewer's choice among candidates is a proposed item beside phase 6.

