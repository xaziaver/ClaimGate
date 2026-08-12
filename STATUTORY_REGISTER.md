# Statutory register

Every regulatory value referenced anywhere in ClaimGate's design, with citation, verification
provenance, and source. Florida amends property-insurance statutes nearly every session — 627.70132
alone has been amended five times in thirteen years (chapter-law history below) — so a bare number
with no citation and no verified-on date is not a fact, it's a guess with confidence attached.

**Verification provenance, stated once here rather than per row:** the six values in the table below,
plus the tolling and claim-recordkeeping citations under "Referenced elsewhere" further down, were
verified in this project's design conversation, dated **2026-08-05**, against the Florida
Legislature's official statute text at leg.state.fl.us and DFS Insurance Consumer Advocate session
summaries. That verification was performed by the project's human reviewer; I (the agent maintaining
this file) have not independently re-fetched the live statute text in this session, and this file
should not be read as claiming that independent re-verification. **This scoping statement does not
cover the hurricane and sinkhole citations added 2026-08-12** — see their own, explicitly weaker
provenance line under "Referenced elsewhere." **None of these values gate intake in phase 2** — no
threshold below blocks or delays a notice; see `PHASE2_DESIGN.md` for why (the no-rejected-state
rule, and the late-notice attribute being non-blocking).

| Value | Amount | Citation | Notes |
|---|---|---|---|
| Notice window, initial or reopened | **1 year** after date of loss | 627.70132(2) | Calendar interval, not a day count — leap years shift the boundary if expressed as days. |
| Notice window, supplemental | **18 months** after date of loss | 627.70132(2) | Calendar interval, not a day count, for the same reason. |
| Notice window, loss assessment | **not computable at intake** | 627.70132(4) | Needs the condominium association's assessment-vote date, which intake doesn't have. See `PHASE2_DESIGN.md`'s Notice Type section — stored, not silently defaulted to the 1-year window. |
| Acknowledgment deadline | **7 calendar days** from receipt of a claim communication | 627.70131(1)(a) | Calendar days, explicitly not business days. Downstream consequence: the receipt timestamp must be immutable, since this clock starts there. |
| Pay-or-deny deadline | **60 days** from notice | 627.70131(7)(a) | Downstream of ClaimGate — not implemented, recorded for completeness because it's the reason a claim parked in the wrong queue (the triage defect in `QUEUE.md`) is a live statutory-time problem, not just a UX one. |
| Weather date of loss | **date of hurricane landfall, or date NOAA verifies the event** — not the date the insured noticed damage | 627.70132(3) | Applies to hurricanes, tornadoes, windstorms, severe rain, or other weather-related events. Not implemented — ClaimGate captures only what the reporter asserts (`reported_loss_date`); deriving the statutory date needs named-catastrophe capture, a later-phase feature. See the loss-date field-naming decision in `ASSUMPTIONS.md`. |

**Statutory amendment history**, recorded because the amendment frequency is itself the argument for
this file existing:

- **627.70132:** s. 10 ch. 2011-39; s. 10 ch. 2021-77; s. 16 ch. 2022-271; s. 22 ch. 2023-172; s. 8
  ch. 2024-139.
- **627.70131:** s. 23 ch. 2005-111; s. 27 ch. 2007-1; s. 18 ch. 2007-90; s. 20 ch. 2011-39; s. 18
  ch. 2021-104; s. 15 ch. 2022-268; s. 15 ch. 2022-271.

**Not independently confirmed:** a specific effective date distinct from "most recent amending
chapter law" was not pinned down for either section during verification. The chapter-law history
above is the best available provenance; treat "effective date" as an open item if a compliance
context needs it stated more precisely than "current as of the most recent chapter law listed."

## Referenced elsewhere, not full register entries

Four more statutory provisions are load-bearing elsewhere in the project but weren't part of the
six-value list this register was scoped to: two in `PHASE2_DESIGN.md`, two in `QUEUE.md`'s item 4c.
Recording their citations here so nothing referenced elsewhere is an orphaned citation:

- **Tolling** — 627.70131(8)(b): the section's deadlines toll when a policyholder fails to supply
  requested material information within 10 days of the request, ending on receipt of that
  information; applies only to requests sent at least 15 days before the pay-or-deny deadline.
  ClaimGate does not compute this — see "Pending resolution and tolling" in `PHASE2_DESIGN.md`.
- **Claim recordkeeping duty** — 627.70131(4)(b), with scope defined by (5)(b) and (9): the audit
  log's statutory grounding. See "Audit log" in `PHASE2_DESIGN.md`.
- **Hurricane deductible** — 627.701: a separate hurricane deductible applies to personal lines
  residential property, with hurricane coverage itself defined by cross-reference at 627.4025.
  627.701(7) separately requires an offer of a $500 deductible applicable to losses from perils
  other than hurricane, and recent amendments add a separate roof deductible. The point for
  ClaimGate: hurricane is a statutorily distinct peril with its own deductible math, so a book that
  codes hurricane damage as `wind_hail` cannot compute its own deductible.
- **Catastrophic ground cover collapse and sinkhole loss** — 627.706: every insurer authorized to
  transact property insurance in Florida must provide catastrophic ground cover collapse coverage,
  and must make sinkhole loss coverage available for additional premium — two distinct coverages
  with different tests.

**Provenance on the two entries directly above (hurricane, sinkhole) is weaker than this file's usual
standard, and is stated separately rather than folded into the blanket paragraph at the top of this
file — do not read the two as the same class of claim.** The six-value table and the
tolling/recordkeeping entries above were verified by the project's human reviewer, dated
**2026-08-05**, against the Florida Legislature's official statute text. The hurricane and sinkhole
citations were checked by the advisor session dated **2026-08-12** against flsenate.gov, from
search-result excerpts rather than a direct fetch of the full section text. **Re-verification against
the full statute text is required before either value is hash-locked or used as the basis for a
locked spec.**
