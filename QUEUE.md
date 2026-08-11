# Work queue

Ordered by domain severity, not by effort. One line each on why that position.

1. **`triage.feature` SIU queue override.** Highest severity found in the project: a claim parked
   in `siu_review` never reaches an adjuster, and the Fla. Stat. 627.70131(7)(a) 60-day pay-or-deny
   clock keeps running regardless of which queue it sits in — this is a statutory-time defect, not
   a routing preference. *(Done — see below.)*
2. **`siu_flags.feature` thresholds and framing, together.** *(Done — see below.)* Legally sensitive: the 30-day
   late-reporting indicator flags a large share of a lawful Florida property book against a 1-year
   statutory notice window, and fixing the threshold alone while leaving the fraud-conclusion
   framing in place would still leave the other half of the same exposure standing. *Also carries an
   undocumented rule found while fixing item 1: `compute_siu_flags` already guards against a policy
   inception date after the loss date (`recent_policy_inception` resolves `False` rather than being
   computed on a negative interval), but no scenario anywhere asserts it. Whoever resolves this item
   should decide whether that guard is the right rule and, if so, give it a scenario — see
   `ASSUMPTIONS.md`. The specific scenario needed: `siu_flags.feature` should assert that an
   inception date later than the loss date does not fire `recent_policy_inception` — that specifies
   the existing `0 <=` guard rather than changing behavior. Separately, a loss predating policy
   inception is a coverage question, not an SIU one — the indicator returning `False` is correct for
   the indicator and silent about the larger fact, which connects to the plausibility-floor gap
   already recorded and needs phase-3 policy data. Do not build the coverage rule in item 2; specify
   the guard only.*
3. **`duplicates.feature` framing, `notice_type` interaction, sort proof, and the now-orphaned
   3-day window.** *(Spec locked, implementation not started — see below.)* Real correctness and
   framing gaps, plus a threshold whose own rationale stopped holding the moment duplicates became
   non-blocking evidence instead of a gate — lower severity than 1–2 because nothing here carries
   statutory exposure. *Note for whoever implements this item: ten acceptance-mutant approvals on
   `features/duplicates.feature`'s "Matching against a single existing claim" scenario — all
   equivalence judgments about date/loss-type/policy-number mutations on rows already excluded by a
   policy or loss-type mismatch — are keyed to the pre-reopening row content. Four sit on the exact
   boundary rows that moved from the 3-day window (`2026-06-04`/`2026-05-29` matched,
   `2026-06-05`/`2026-05-28` didn't) to the 60-day one; the other six sit on rows whose dates didn't
   move but whose result column changed shape (`duplicate_ids: [...]` to `matching_claim_id`).
   Approval keys are content-addressed on the whole row, so all ten go stale on implementation, not
   just the four with new dates — the gate will report every one, and re-review against the locked
   spec is mine, not automatic.*
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
   carries the legal exposure of 1–2, so they sit behind everything above. *Note for whoever revisits
   the $500 threshold: two acceptance-mutant approvals on `features/triage.feature`'s "Theft severity
   by loss amount" rule (`500.00->501.00`, `500.01->501.01`) are equivalence judgments about that
   exact threshold. Changing it goes stale automatically — the gate will report it as a stale approval
   — and needs re-review against whatever replaces $500, not a surprise when it happens.*
6. **Phase 2 build.** Sequenced last deliberately — it should be built on a domain that's already
   been swept for the defects above, not on top of ones still waiting to be found. Full design for
   what phase 2 actually is: `PHASE2_DESIGN.md`.

## Status as of this handoff

**Item 1 is done and merged to `main`** (merge commit `7f985e7`, 2026-08-09). Queue routing derives
from severity alone; `SIU_QUEUE`/`"siu_review"` is removed from `src/`. SIU indicators are not a
field on `TriageOutcome` — severity/queue and SIU are different access classifications (operational
vs. restricted-read) and don't share one struct, even before phase 2's separate table exists;
`compute_siu_flags()` stays independently callable and step definitions call it separately for the
end-to-end scenario's assertions. `gauntlet check` passes on `main` post-merge (`27
reviewed-equivalent`, no unreviewed acceptance survivors, no stale approvals). The reopening branch
itself needed its own fix first — it had zero unique commits (a bookmark on `main`'s pre-revert
history, not a real branch); see `docs/harness-findings.md`. `features/validation.feature`,
`features/duplicates.feature`, and `features/siu_indicators.feature` are also fully implemented and
gated on `main`; `validation.feature` belongs to an earlier reopening (accumulation, `blockers`,
`notice_type`, `LOSS_DATE_IN_FUTURE`) that isn't part of this numbered queue, while
`duplicates.feature` and `siu_indicators.feature` are, respectively, this queue's item 3 (next,
below) and item 2 (just closed above).

**Item 2 is done and merged to `main`** (merge commit `9d3fc2d`, 2026-08-10). `siu_flags.feature` is
renamed `siu_indicators.feature`; `SiuFlags(bool, bool)` becomes `SiuIndicators`, each field a
three-valued `TRUE`/`FALSE`/`NOT_EVALUATED` result with a reason code, so an indicator whose input
is missing can never be read as a negative determination. Both thresholds are supplied by the
caller on every call, never a domain default — the late-reporting threshold ships unconfigured, and
the recent-inception threshold stays a real, kept value of 30. Fraud-conclusion framing (title,
narrative, "regardless of whether the claim is otherwise valid") is gone from the spec. `gauntlet
check` passes on `main` post-merge (34 reviewed-equivalent, no unreviewed acceptance survivors, no
stale approvals).

**Item 3's spec is drafted, revised twice under review, and locked** on `reopening/duplicates`
(lock commit `9ebdee1`, 2026-08-11); implementation has not started. `duplicates.feature` moves from
a preventive framing to non-blocking evidence for a human reviewer — "candidate matches," never
"probable duplicates." All three non-`INITIAL` notice types now resolve `NOT_EVALUATED` with a
reason instead of running the window comparison: `SUPPLEMENTAL`/`REOPENED` because a declared
follow-on already answers the question duplicate detection asks (`FOLLOW_ON_NOTICE_TYPE`);
`LOSS_ASSESSMENT`, for a different reason, because telling a unit owner's own loss apart from an
association assessment claim needs the existing claim's coverage type, unavailable at intake until
phase 3 (`NO_EXISTING_CLAIM_NOTICE_TYPE`). These two reason codes are their own closed enumeration,
deliberately not shared with `siu_indicators.feature`'s — duplicate candidates are an ordinary,
unrestricted attribute, SIU indicators are restricted-read in a separate table, and the two
enumerations grow independently without either constraining the other. The match window changes from
3 days to 60, symmetric, on reported loss date: a carrier policy decision with no statutory or
industry-standard basis, set because non-blocking evidence flips the false-positive/false-negative
cost asymmetry the original 3-day window was tuned against.

## Open instructions

Anything issued but not yet completed, cleared as each is done. This tracks in-flight instructions;
the numbered queue above tracks reopenings.

**Item 3's implementation is open, on `reopening/duplicates`.** The spec is locked (`9ebdee1`); the
matcher, step definitions, and any new result type for the `NOT_EVALUATED`-plus-reason outcome still
need writing against it. `gauntlet check` staying red on that branch until then is the expected,
sanctioned pre-implementation state (CLAUDE.md's spec-lock-then-implementation ordering), not a
problem to route around. See item 3's queue entry above for the stale mutant-approval warning
implementation will trigger.

`main` is pushed to `https://github.com/xaziaver/ClaimGate`, current through this handoff's QUEUE.md
update; `reopening/duplicates` is pushed through its merge of that update, on top of the spec lock
(`9ebdee1`). `reopening/siu-indicators` is pushed and kept as history. `reopening/triage-siu-queue` is
deleted, locally and on origin — once item 1 merged it had no commits unique to it, and its content is
fully preserved in `main`'s own history through the merge commit.
