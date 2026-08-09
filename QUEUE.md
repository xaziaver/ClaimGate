# Work queue

Ordered by domain severity, not by effort. One line each on why that position.

1. **`triage.feature` SIU queue override.** Highest severity found in the project: a claim parked
   in `siu_review` never reaches an adjuster, and the Fla. Stat. 627.70131(7)(a) 60-day pay-or-deny
   clock keeps running regardless of which queue it sits in — this is a statutory-time defect, not
   a routing preference. *(Draft in progress — see below.)*
2. **`siu_flags.feature` thresholds and framing, together.** Legally sensitive: the 30-day
   late-reporting indicator flags a large share of a lawful Florida property book against a 1-year
   statutory notice window, and fixing the threshold alone while leaving the fraud-conclusion
   framing in place would still leave the other half of the same exposure standing. *Also carries an
   undocumented rule found while fixing item 1: `compute_siu_flags` already guards against a policy
   inception date after the loss date (`recent_policy_inception` resolves `False` rather than being
   computed on a negative interval), but no scenario anywhere asserts it. Whoever resolves this item
   should decide whether that guard is the right rule and, if so, give it a scenario — see
   `ASSUMPTIONS.md`.*
3. **`duplicates.feature` framing, `notice_type` interaction, sort proof, and the now-orphaned
   3-day window.** Real correctness and framing gaps, plus a threshold whose own rationale stopped
   holding the moment duplicates became non-blocking evidence instead of a gate — lower severity
   than 1–2 because nothing here carries statutory exposure.
4. **Coordinated loss type and policy format pass across all four feature files.** A credibility
   and scope-fit problem (a multi-line liability book's vocabulary in a system designed for
   Florida residential property only), not a correctness defect — sequenced after 1–3 and done as one pass because
   `loss_type` vocabulary is shared across every file; fixing it in one file first would leave the
   others visibly incoherent with it. *Scope note: item 1's reopening added a second `water_damage`
   example (standard severity, both SIU flags firing) to `triage.feature`'s end-to-end scenario,
   while `auto_collision`/`auto_comprehensive` remain untouched in the severity rule in the
   meantime. That's item 1 reusing in-scope vocabulary it already had on hand for a needed
   standard-severity example — the file is temporarily inconsistent (residential vocabulary sitting
   next to auto vocabulary this book doesn't write) until this item's pass reconciles it. Intentional,
   not a defect.*
5. **`triage.feature` thresholds** ($500 theft threshold with no provenance, loss amount affecting
   severity only for theft, `policy_inception_date` availability at intake). Real gaps, but none
   carries the legal exposure of 1–2, so they sit behind everything above.
6. **Phase 2 build.** Sequenced last deliberately — it should be built on a domain that's already
   been swept for the defects above, not on top of ones still waiting to be found. Full design for
   what phase 2 actually is: `PHASE2_DESIGN.md`.

## Status as of this handoff

Item 1 has a Gherkin draft on branch `reopening/triage-siu-queue`, now committed to the branch in
its own right rather than surviving only as an artifact of shared ancestry with `main` (see the
harness finding below). Not yet approved — `route_queue` no longer takes SIU flags and
`SIU_QUEUE`/`"siu_review"` is removed; none of that is implemented in `src/` yet. `TriageOutcome`
does **not** grow a `siu_flags` field — SIU indicators and severity/queue are different access
classifications (operational vs. restricted-read) and shouldn't share one struct even before phase
2's separate table exists; step definitions call `compute_siu_flags()` independently instead. It is
not on `main` — see the "main is always green" constraint in `CLAUDE.md`; the draft moves back to
`main` only once its spec is locked and its implementation is complete. `features/validation.feature`
is fully implemented, gated, and on `main` — it belongs to an earlier reopening (accumulation,
`blockers`, `notice_type`, `LOSS_DATE_IN_FUTURE`) that isn't part of this numbered queue.

## Open instructions

Anything issued but not yet completed, cleared as each is done. This tracks in-flight instructions;
the numbered queue above tracks reopenings.

Nothing currently open. `main` and `reopening/triage-siu-queue` are both pushed to
`https://github.com/xaziaver/ClaimGate`.
