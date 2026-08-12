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
   3-day window.** *(Done — see below.)* Real correctness and
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
   not a defect. Correction now that item 3 has landed: this note should not be read as identifying
   `triage.feature` as the only file in that state.
   `duplicates.feature`'s "Two existing claims both match the candidate" scenario also carries auto
   vocabulary (`AU-7654321`, `auto_collision`) alongside the file's otherwise-residential examples —
   present since the original phase-1 spec (`fc86add`), not introduced by item 3's reopening, which
   left that scenario's data untouched. The mechanism differs (item 1 mixed a new example into an
   otherwise-auto rule; `duplicates.feature`'s auto and residential vocabulary sit in separate,
   internally-consistent scenarios, never mixed within one), but both files are in scope for this
   item, and `duplicates.feature` has been in this state longer.*
   *Stale-reason note: `triage.feature`'s eleven-survivor mutant approval (`gauntlet.lock.json`,
   approved 2026-08-10) gives as part of its reason that the `0 <=` lower-bound guard in
   `_is_recent_inception` is undocumented because "no scenario in siu_indicators.feature,
   triage.feature, or any unit test exercises an inception date later than a loss date." Item 2 added
   exactly that scenario the same day (`siu_indicators.feature`'s "An inception date later than the
   loss date does not fire the indicator"). The approval is probably still valid — the new scenario
   lives in `siu_indicators.feature`, not `triage.feature`, so the mutant on `triage.feature`'s own
   row may still be unkillable at that layer for the structural reason the rest of the approval
   describes — but its stated reason is now factually wrong about what's documented where. This
   item's vocabulary pass will restale these approvals anyway; that re-review is the moment to
   rewrite the reason, not before. Do not hand-edit the ledger to fix this now.*
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

**Item 3 is done and merged to `main`** (merge commit `0b4e315`, 2026-08-12). `find_duplicates`
returns `DuplicateMatchResult` (`EVALUATED`/`NOT_EVALUATED`, `matches`, `reason`) instead of a bare
list, so a candidate that was never compared can't be read as compared-and-clean. `notice_type` is
matched explicitly, with no fall-through case: `INITIAL` runs the window comparison;
`SUPPLEMENTAL`/`REOPENED` resolve `NOT_EVALUATED`/`FOLLOW_ON_NOTICE_TYPE` regardless of timing,
because a declared follow-on already answers the question duplicate detection asks;
`LOSS_ASSESSMENT` resolves `NOT_EVALUATED`/`NO_EXISTING_CLAIM_NOTICE_TYPE`, because telling a unit
owner's own loss apart from an association claim needs the existing claim's coverage type,
unavailable until phase 3. These two reason codes are their own closed enumeration, deliberately not
shared with `siu_indicators.feature`'s — duplicate candidates are an ordinary, unrestricted
attribute, SIU indicators are restricted-read in a separate table, and the two enumerations grow
independently. Any other `notice_type` raises `ValueError` — the first raise in the domain layer —
rather than adding a third reason code: `validation.feature` already resolves an unrecognized value
to `NOTICE_TYPE_UNRECOGNIZED`, and `PHASE2_DESIGN.md`'s transition table never lets a notice with a
blocker reach `TRIAGED`, so `find_duplicates` is never called with one on the designed path — an
unreachable value is a caller contract violation, not a business outcome to record. The match window
is a required `window_days` parameter with no domain default, mirroring item 2's thresholds;
`DUPLICATE_WINDOW_DAYS` is removed rather than changed to 60, since a carrier policy value belongs to
the caller on every call, and 60 itself — a carrier policy decision, symmetric on reported loss date
— has no statutory or industry-standard basis. `EVALUATED` as the positive value's spelling is a
human decision, not spec text: unlike `NOT_EVALUATED` and both reason codes, it appears nowhere in
`duplicates.feature`, and it will likely resurface when phase 2's serializer settles the still-open
question of whether these reason codes belong in `reason_codes` (`PHASE2_DESIGN.md`). `gauntlet
check` passes on `main` post-merge (42 reviewed-equivalent, no unreviewed acceptance survivors, no
stale approvals). Item 4 is next.

## Open instructions

Anything issued but not yet completed, cleared as each is done. This tracks in-flight instructions;
the numbered queue above tracks reopenings.

Nothing open as of this handoff.

`main` is pushed to `https://github.com/xaziaver/ClaimGate`
