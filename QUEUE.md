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
history, not a real branch); see `docs/harness-findings.md`. `features/validation.feature` remains
the only other fully implemented, gated, `main` feature file; it belongs to an earlier reopening
(accumulation, `blockers`, `notice_type`, `LOSS_DATE_IN_FUTURE`) that isn't part of this numbered
queue.

**Item 2 is done and merged to `main`** (merge commit `9d3fc2d`, 2026-08-10). `siu_flags.feature` is
renamed `siu_indicators.feature`; `SiuFlags(bool, bool)` becomes `SiuIndicators`, each field a
three-valued `TRUE`/`FALSE`/`NOT_EVALUATED` result with a reason code, so an indicator whose input
is missing can never be read as a negative determination. Both thresholds are supplied by the
caller on every call, never a domain default — the late-reporting threshold ships unconfigured, and
the recent-inception threshold stays a real, kept value of 30. Fraud-conclusion framing (title,
narrative, "regardless of whether the claim is otherwise valid") is gone from the spec. `gauntlet
check` passes on `main` post-merge (34 reviewed-equivalent, no unreviewed acceptance survivors, no
stale approvals).

**Item 3 is next.**

## Open instructions

Anything issued but not yet completed, cleared as each is done. This tracks in-flight instructions;
the numbered queue above tracks reopenings.

Nothing currently open. `main` is pushed to `https://github.com/xaziaver/ClaimGate`, including
`reopening/siu-indicators`'s merge; `reopening/siu-indicators` itself is pushed and kept as history.
`reopening/triage-siu-queue` is deleted, locally and on origin — once item 1 merged it had no
commits unique to it, and its content is fully preserved in `main`'s own history through the merge
commit.
