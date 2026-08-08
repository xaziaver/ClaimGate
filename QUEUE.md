# Work queue

Ordered by domain severity, not by effort. One line each on why that position.

1. **`triage.feature` SIU queue override.** Highest severity found in the project: a claim parked
   in `siu_review` never reaches an adjuster, and the Fla. Stat. 627.70131(7)(a) 60-day pay-or-deny
   clock keeps running regardless of which queue it sits in — this is a statutory-time defect, not
   a routing preference. *(Draft in progress — see below.)*
2. **`siu_flags.feature` thresholds and framing, together.** Legally sensitive: the 30-day
   late-reporting indicator flags a large share of a lawful Florida property book against a 1-year
   statutory notice window, and fixing the threshold alone while leaving the fraud-conclusion
   framing in place would still leave the other half of the same exposure standing.
3. **`duplicates.feature` framing, `notice_type` interaction, sort proof, and the now-orphaned
   3-day window.** Real correctness and framing gaps, plus a threshold whose own rationale stopped
   holding the moment duplicates became non-blocking evidence instead of a gate — lower severity
   than 1–2 because nothing here carries statutory exposure.
4. **Coordinated loss type and policy format pass across all four feature files.** A credibility
   and scope-fit problem (a multi-line liability book's vocabulary in a system designed for
   Florida residential property only), not a correctness defect — sequenced after 1–3 and done as one pass because
   `loss_type` vocabulary is shared across every file; fixing it in one file first would leave the
   others visibly incoherent with it.
5. **`triage.feature` thresholds** ($500 theft threshold with no provenance, loss amount affecting
   severity only for theft, `policy_inception_date` availability at intake). Real gaps, but none
   carries the legal exposure of 1–2, so they sit behind everything above.
6. **Phase 2 build.** Sequenced last deliberately — it should be built on a domain that's already
   been swept for the defects above, not on top of ones still waiting to be found. Full design for
   what phase 2 actually is: `PHASE2_DESIGN.md`.

## Status as of this handoff

Item 1 has a Gherkin draft in `features/triage.feature` (not yet approved — `route_queue` no longer
takes SIU flags, `SIU_QUEUE`/`"siu_review"` is removed, `TriageOutcome` needs a `siu_flags` field;
none of that is implemented in `src/` yet). `features/validation.feature` is fully implemented and
gated — it belongs to an earlier reopening (accumulation, `blockers`, `notice_type`,
`LOSS_DATE_IN_FUTURE`) that isn't part of this numbered queue.
