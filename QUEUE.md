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
4a. **Loss-type and policy-number vocabulary substitution across `triage.feature` and
    `duplicates.feature`.** *(Done — see below.)* Pure example-data rename, no rule changes: `auto_collision` ->
    `lightning`, `auto_comprehensive` -> `smoke`, `AU-7654321` -> `HO-7654321`. Credibility and
    scope fit, not correctness — sequenced first of the three-way split because it is the purely
    mechanical piece, with nothing for a human to decide beyond the replacement values themselves.
    *Blast radius, two different questions. 21 of the 42 current acceptance-mutant approvals are
    keyed to rows containing a loss_type or policy_number value at all (11 on `triage.feature`'s
    end-to-end scenario, 10 on `duplicates.feature`'s "Matching against a single existing claim") —
    that answers "how much of the ledger is sensitive to this vocabulary in general," not "how much
    goes stale from this specific rename," and it stays here rather than being deleted because it's
    the number 4b or 4c would restale if either changed a different value the same rows contain.
    The narrower question — what 4a itself stales — has a different, smaller answer, measured
    against the actual keys rather than assumed from the row inventory: `triage.feature` restales
    nothing, because no approval anywhere names `auto_collision` or `auto_comprehensive` — all 11
    end-to-end keys embed `theft`, `fire`, or `water_damage`, and the 2 theft-threshold keys embed
    only amounts, no loss type at all. On `duplicates.feature`, 2 approvals restale mechanically —
    the two whose locator keys embed `AU-7654321` (both on the policy-mismatch row, one mutating its
    loss_date, one mutating its loss_type). But all 10 approvals on "Matching against a single
    existing claim" share one combined reason, and that reason's prose names `AU-7654321` explicitly;
    eight of the ten have keys that don't change, so nothing will flag them automatically, and
    they'll keep citing a value the file no longer contains until someone reads the reason text
    itself rather than trusting the digest. All ten need re-approving for the prose, not just the two
    for the key. That re-review is mine, not the implementer's. `duplicates.feature`'s three
    standalone scenarios that also carry this vocabulary in their own `Given` steps ("Two existing
    claims both match the candidate", "A loss assessment notice is never compared...", "An INITIAL
    notice is still compared normally") sit at zero approvals today — not because they are
    unmutated, but because every mutant generated against them was already killed. A rename
    re-exercises mutation there fresh, with no guarantee of the same kill rate; that part of the
    blast radius is unbounded, not merely deferred.*
4b. **The recognized policy-number prefix set is a business rule, not example data.** *(Done — see
    below.)*
    `POLICY_NUMBER_PATTERN` accepts `HO`, `AU`, `CP`, `CA`, `GL`, so `AU`/`CP`/`CA`/`GL` currently
    *pass* validation. Removing them flips four rows in `validation.feature`'s "Policy number
    format" outline from no-blockers to `POLICY_NUMBER_MALFORMED` and requires changing
    `validation.py`'s regex alongside the spec — a change to what the spec asserts, not a rename, so
    it gets its own spec lock and its own reopening, sequenced after 4a because it touches code and
    not only examples. *Open question for that item, not to be answered now: what the recognized set
    becomes. Policy numbering is carrier-specific with no industry standard. Candidates are `HO`
    plus `DP` (dwelling fire, common on Florida residential books for landlord and
    non-owner-occupied risks), possibly `MH` if the estate writes manufactured housing. Note that
    `LOSS_ASSESSMENT` notices already imply condo risks are in this book whether or not a prefix
    distinguishes them.*
4c. **Missing perils (`hurricane`, `sinkhole`, `roof_leak`) merged with the severity-rule thresholds
    formerly at item 5, decided 2026-08-13 not to be sequential.** *(Done — see below.)*
    Originally sequenced with 4c
    last of the three-way split because each new peril forces a severity decision, which was item
    5's territory — adding perils without deciding their severity would push them silently through
    the standard fallthrough, which is the defaulting `CLAUDE.md`'s first constraint forbids. That
    reasoning turned out to argue for merging, not just ordering: assigning the new perils' severity
    under a scheme item 5 was about to change would mean doing the work twice, once under the old
    rule and once under the new one. One reopening, one spec lock. Item 5's own reasoning for sitting
    behind items 1–2 still holds and carries over: real gaps, but none with 1–2's legal exposure, so
    the merged item stays behind everything above.

    A completeness gap, not a rename — the one a claims manager would actually stop at: a Florida
    residential intake system with no way to code a hurricane or a sinkhole claim. See
    `STATUTORY_REGISTER.md` for why hurricane and sinkhole are statutorily distinct, not just missing
    labels. *All four decisions this item needs are now made — see `ASSUMPTIONS.md`: the new perils'
    severities (`sinkhole` `HIGH`, `roof_leak` and `hurricane` `STANDARD`, with catastrophe handling
    recorded as a deliberate non-goal rather than a severity concern); loss amount removed from the
    severity rule entirely rather than re-thresholded; `policy_inception_date` now available at
    intake via a phase-2 adapter lookup, reversing the earlier "no source until phase 3" assumption;
    and, decided 2026-08-13, the lookup returns the policy's ORIGINAL inception date — the date
    continuous coverage on the risk began — never the current term's effective date, since the
    indicator exists to surface new business and a renewal effective date would fire it across a
    lawful book every twelve months, the same defect item 2 removed from the reporting gate; see
    `ASSUMPTIONS.md`'s "Data we do not have at intake." How the adapter derives that date, and that
    "on the risk" survives a rewrite but not a genuine lapse, is now also decided (2026-08-14, same
    document) — what remains unverified is per-system mechanics only: which identifier resolves to
    the party/risk in each of the three policy administration systems, needed before the phase-2
    adapter is wired, not before this spec is written. Also see `ASSUMPTIONS.md`'s open decision on
    `loss_type` conflating perils with Section II coverage categories — this item should not assume
    an answer to that question either. Note for whoever writes the spec: re-review scope is
    **decided at 7 acceptance-mutant approvals**, not the two this entry previously named — the
    end-to-end outline keeps its `loss_amount` column (advisor-recommended, human-ratified,
    2026-08-14; see `ASSUMPTIONS.md`'s "Carried requirements"), so the 13-approval branch of the
    fork this entry used to carry does not apply. The two on "Theft severity by loss amount"
    (`500.00`, `500.01`) are gone with the rule. A mutant's locator is the mutated column's header
    plus every value in its row (`docs/harness-findings.md`), so once the three theft rows in the
    end-to-end outline have their `severity`/`queue` cells flip from `low`/`fast_track` to
    `standard`/`standard`, every approval keyed to one of those rows goes stale with them — 5 more,
    regardless of which column was originally mutated (2 on `inception_date`, 3 on `loss_amount`),
    for 7 total. Re-review is the human's, not automatic.*
4d. **`siu_indicators.feature` reopening: everything the recent-inception lookup decision (4c) leaves
    stale in that file, taken together.** *(Done — see below.)* Two comments used to say
    `policy_inception_date` has no source at intake (lines 79-81, 125-129); the Rule and Scenario
    both named "Neither indicator is evaluated in the shipped configuration" and the
    NOT_EVALUATED-becomes-an-exception-path framing both need reconciling with the decided lookup
    (`ASSUMPTIONS.md`'s "Data we do not have at intake"). **Advisor-recommended, human-ratified,
    2026-08-14: the vocabulary rename is decided, and it is surgical** — rename the input date only
    ("the policy inception date" -> "the continuous coverage date"; column header `inception_date`
    -> `coverage_start`). Do NOT rename the indicator or the threshold: "recent policy inception" is
    a correct indicator name and is what SIU reads, and stays as-is. Measured costs, both counted the
    same way as 4c's (locator = mutated column's header plus every row value): a full rename
    (indicator and threshold included) would touch 8 approvals; the surgical rename decided here
    touches 3, all three on `triage.feature`'s `inception_date` column — none on
    `siu_indicators.feature`, since none of its 7 current approvals are keyed to a step mentioning
    the date itself, only to the threshold steps this rename leaves untouched. Of those 3: 2 are the
    end-to-end outline's theft-row approvals, already re-reviewed once under 4c for their
    `severity`/`queue` flip and re-reviewed again here for the column-header rename — re-reviewed
    twice, not double-counted as new; the third is the water_damage-row approval, untouched by 4c,
    new to this item alone. This stays its own item rather than riding inside 4c's lock specifically
    to avoid that scope creep, at the recorded cost of those 2 approvals being re-reviewed twice
    instead of once. `triage.feature`'s copy of that stale claim was corrected inside 4c's lock
    (`b3b986a`) and now reads "a real path once the phase-2 adapter's lookup can miss, not the
    configuration this system ships with (see siu_indicators.feature)." That correction created a
    broken cross-reference this item must close: `triage.feature` now points at
    `siu_indicators.feature` for the shipped-configuration claim, and `siu_indicators.feature` still
    asserts the opposite. A reader following the pointer lands on the contradiction rather than the
    explanation.
4f. **`features/siu_indicators.feature:126` names a function, and names a dead
    one.** *(Done — see below.)* The comment on the Rule "A continuous coverage date after the loss date
    does not indicate recent policy inception" reads "Specifies the existing 0 <=
    guard in `_is_recent_inception`" — a symbol that has not existed since
    2026-08-09, when `33d602b` renamed it `_evaluate_recent_inception` in the same
    commit that created it. `CLAUDE.md` forbids a Gherkin scenario naming a
    function, and the surrounding sentence carries its meaning without the symbol,
    so the fix is deleting the reference rather than correcting the name.
    Spec-only and comment-only: comment edits leave mutant counts unchanged
    (established in `d344ab3`), so this costs one spec approve and lock and
    produces zero ledger churn. Its own reopening because it is a spec edit.
    Sequenced before 4e only because it is smaller.

    **Correction, made while closing this item:** "costs one spec approve and
    lock" above is wrong about what `gauntlet lock` does. `lock` approves the
    verified config paths the protect gate checks (`.claude/settings.json`,
    `gauntlet.toml`, `pyproject.toml`) — it has nothing to do with specs.
    `gauntlet spec approve` writes the spec digest by itself; there is no
    second, `lock` step for a spec. Running `lock` here would have
    re-baselined an unrelated gate. Left in place rather than deleted so the
    mistake stays visible, per this file's own convention.

    Note for whoever does this: `gauntlet.lock.json`'s remaining occurrences of
    `_is_recent_inception` are deliberate — they are the correction record inside the
    triage approval reason, marked dead with a date. They are not part of this sweep.
    The ledger is never hand-edited (`CLAUDE.md`), and rewriting an approval reason is
    a re-approval, not a documentation fix.
4e. **Close the loss-type vocabulary in `validation.feature`: an unrecognized loss type should be a
    blocker, not a silent `standard`.** Sequenced after 4f, not started. Motivation, as fact, not
    conjecture: `validation.py`'s `_check_loss_type` tests only for non-empty (`.strip()`), with no
    closed-set check behind it; `triage.py`'s `assign_severity` falls through to `standard` for
    anything not in the high-severity set. `sinkhole` sat in exactly this gap until item 4c gave it
    its own row and its own `HIGH` severity — before that, nothing in the codebase would have
    distinguished a `sinkhole` loss from a typo, and nothing would have failed either way, because
    nothing checked. *Considered and rejected: adding an "unrecognized loss type resolves standard"
    scenario to `triage.feature` instead of closing the gap in `validation.feature`.* That would spec
    the fallthrough as intended behavior — hash-lock the default rather than close the gap it exists
    because of. The fix belongs at intake validation, where an unrecognized value already becomes a
    blocker for every other required field, not inside severity assignment, which has no way to
    refuse a record at all.
5. **Phase 2 build.** Sequenced last deliberately — it should be built on a domain that's already
   been swept for the defects above, not on top of ones still waiting to be found. Full design for
   what phase 2 actually is: `PHASE2_DESIGN.md`.

## What to read

`CLAUDE.md`, this file, and `docs/harness-findings.md` every session. The rest is
per item — a document the current item does not need costs context the work needs
later.

| Working on | Also read |
|---|---|
| 4a, 4b | `ASSUMPTIONS.md` — the vocabulary and policy-prefix entries |
| 4c (merged with former item 5) | `ASSUMPTIONS.md` and `STATUTORY_REGISTER.md` |
| 4d | `ASSUMPTIONS.md` — "Data we do not have at intake" |
| 4f | this item's own entry; no other document needed |
| 4e | this item's own entry; no other document needed |
| 5 (phase 2) | everything, `PHASE2_DESIGN.md` first |
| A regulatory value, anywhere | `STATUTORY_REGISTER.md` |
| A record state, the audit log, idempotency, or the HTTP surface | `PHASE2_DESIGN.md` |

`docs/decisions.md` is a dated historical record, not current guidance. Read it
only when tracing why a phase-1 rule exists, and read `ASSUMPTIONS.md`'s audit of
it alongside — several of its entries are recorded there as unfounded.

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
stale approvals). Item 4 has been split into 4a, 4b, and 4c (see above, 2026-08-12) — the loss-type
and policy-number vocabulary pass turned out to bundle a pure rename, a business-rule change to
`validation.py`'s regex, and a completeness gap behind one number, and each needed its own spec lock
and its own reopening. Item 4b is next.

**Item 4a is done and merged to `main`** (merge commit `a0983ef`, 2026-08-13). `auto_collision` ->
`lightning`, `auto_comprehensive` -> `smoke` in `triage.feature`'s severity outline; `AU-7654321` ->
`HO-7654321` in `duplicates.feature`'s policy-mismatch row and its "Two existing claims both match
the candidate" scenario. Spec locked at `84d6c33`. No `src/` change was required, verified rather
than assumed from the spec: neither `validation.py` nor `triage.py` enumerates loss types as a closed
set — `_check_loss_type` only checks presence via `.strip()`, `_check_injury_fields` branches on a
single `== "injury"` comparison, and `assign_severity` checks membership in the 2-element
`{"injury", "fire"}` plus a single `!= "theft"` comparison, with every other value —
`lightning`/`smoke` exactly like `auto_collision`/`auto_comprehensive` before them — falling through
to `standard`; `HO-7654321` matches `POLICY_NUMBER_PATTERN` directly. `validation.feature` was not
touched. The implementation commit (`a1b4d5e`) turned out to be `tests/unit/test_triage.py` and
`tests/unit/test_duplicates.py`: they mirrored the pre-reopening example data exactly and stayed
green throughout the spec-lock-to-merge window because unit tests call the domain functions directly
and never read feature files — a live instance of `docs/harness-findings.md`'s "A green gate
sometimes means nothing was checked," invisible to every gate until someone read the two files by
hand and changed them. Mutant re-review (`690d8b1`) re-approved all ten stale approvals on
`duplicates.feature`'s "Matching against a single existing claim" — the two whose keys embedded
`AU-7654321` and the eight whose keys were unchanged but whose shared reason's prose did — rewritten
to describe rows by role rather than by contents, per the sharper convention
`docs/harness-findings.md` now states. The three standalone scenarios carrying this vocabulary in
their own `Given` steps were re-exercised by the rename with no guarantee of the same kill rate; none
produced a new survivor. `gauntlet check` passes on `main` post-merge (169/169 tests, mutation
100%/213 killed, 42 reviewed-equivalent — the same figure as before the rename, confirming no new
acceptance survivors and no remaining stale approvals). This merge also carried two documentation
commits (`8b3fba9`, `d5f14e9`) that had landed on the reopening branch instead of `main`, contrary to
this file's own documentation-lands-on-main convention — not unpicked, just carried forward and
recorded here so the merge doesn't misdescribe itself as 4a alone.

**Item 4b is done and merged to `main`** (merge commit `f78ba74`, 2026-08-13). `POLICY_NUMBER_PATTERN`
narrows from `HO|AU|CP|CA|GL` to `HO` alone; `AU-1234567`, `CP-1234567`, `CA-1234567`, and
`GL-1234567` now resolve `POLICY_NUMBER_MALFORMED` instead of passing. Spec locked at `eda826b`.
HO-only is a carrier scope decision, not a value with statutory or industry-standard support behind
it — policy numbering is carrier-specific, and `HO` is what's confirmed today. `DP` (dwelling fire,
common on Florida residential books for landlord and non-owner-occupied risk) is the next candidate
if the estate turns out to write that line, and `MH` (manufactured housing) after that — both
excluded now for want of evidence, not by a judgment against them. An unrecognized prefix is a
blocker like any other malformed policy number, not a refusal: the notice still lands `PENDED`,
never a rejected or discarded state, per `CLAUDE.md`'s state-model constraint. `validation.feature`'s
"Policy number format" outline keeps its `AU-1234567`/`CP-1234567`/`CA-1234567`/`GL-1234567` rows
rather than collapsing them into the existing `XX-1234567` catch-all — deliberately, because they
document which lines this book does not write, not merely that malformed prefixes are rejected. The
implementation commit (`6eb403a`) was `src/claimgate/domain/validation.py`'s regex plus
`tests/unit/test_validation.py`'s four AU/CP/CA/GL rows, the same blind spot 4a found: unit tests
never read feature files, so they needed their own update to match the locked spec rather than
catching the gap themselves. `gauntlet check` passes on `main` post-merge (169/169 tests, mutation
100%/213 killed, 42 reviewed-equivalent — the same figure as after 4a, confirming no new acceptance
survivors on the "Policy number format" outline and no stale approvals). Item 4c is next in the
numbered list above, but its own entry already says it waits for item 5 or merges with it, because
each new peril forces a severity decision that's item 5's territory — that decision is the human's to
make, not a pickup for the next session.

**Items 4c and 5 are merged into one item.** They were never sequential: 4c would have assigned
severity to `hurricane`, `sinkhole`, and `roof_leak` under the severity rule item 5 was about to
change. Former item 5's own numbered slot is retired; the old item 6 (phase 2 build) is renumbered 5
— nothing outside `QUEUE.md` referenced it by number. Every decision the merged item needs is made
and recorded in `ASSUMPTIONS.md`: new-peril severities (`sinkhole` `HIGH`, `roof_leak` and
`hurricane` `STANDARD`, catastrophe handling a deliberate non-goal); loss amount removed from the
severity rule entirely, and the `low` severity band and `fast_track` queue retired with it — the
theft-amount rule was their only producer and no peril is a credible fast-track feeder;
`Candidate.loss_amount` stays on the model captured-not-used rather than removed, so the end-to-end
outline's surviving mutants on that column can keep demonstrating the independence rather than the
spec merely not contradicting it; `policy_inception_date` is available at intake via a phase-2
adapter lookup returning the policy's ORIGINAL inception date — continuous coverage on the risk, not
with any one carrier, surviving an administrative rewrite but not a genuine lapse — never the
current term's effective date; see `ASSUMPTIONS.md`'s "Data we do not have at intake" and "Carried
requirements." Only per-system party/risk identifier resolution remains unverified, needed before
the phase-2 adapter is wired, not before this spec.

**Item 4c is complete and merged.** Branch `reopening/severity-and-perils`, merged to `main` at
`81f5865`. Five commits: `3875f34` the assertion and table changes, `b3b986a` two explanatory
comments (structurally inert — 90 mutants before and after, confirmed by calling gauntlet's mutation
engine directly rather than assumed), `8812493` the spec lock, `def8b2a` the implementation,
`4f4204b` the prune and re-approval. `features/triage.feature`: `hurricane|standard`,
`roof_leak|standard`, `sinkhole|high` added to "Severity by loss type"; "Theft severity depends on
the loss amount" deleted entirely, Rule and Scenario Outline both; `low|fast_track` dropped from
"Queue routing"; the end-to-end outline's three theft rows now assert `standard|standard`, every
column including `loss_amount` kept. `src/claimgate/domain/triage.py`: `sinkhole` added to the
high-severity set, `_is_low_severity_theft` and `THEFT_LOW_SEVERITY_THRESHOLD` deleted,
`assign_severity` down to one parameter, `low`/`fast_track` out of `_SEVERITY_QUEUES`.
`Candidate.loss_amount` stays on the model, captured but unused.

**The predicted ledger outcome held exactly, and was measured rather than accepted.** 7 of
`triage.feature`'s 13 approvals needed re-review: the 2 keyed to the deleted "Theft severity by loss
amount" scenario pruned as dangling, and 5 — 2 `inception_date`- and 3 `loss_amount`-mutated, all on
the three theft rows — resurfacing as unreviewed survivors under new locators. Zero beyond those 5.
`triage.feature` now carries 11 approvals (8 `loss_amount`, 3 `inception_date`), 40 project-wide.
Green before merge: 166/166 tests, code mutation 100%/197 killed — down from 213 because the
theft-amount branch and its constant were deleted, not because coverage weakened — acceptance 4
specs, 40 reviewed-equivalent.

**One thing the re-approval fixed that no gate could have caught.** `gauntlet mutant approve` applies
a single reason to every survivor in scope and overwrites the existing ones, and all 11 survivors sit
in one scenario — so `--scenario` cannot isolate the new ones, and the 6 previously-approved were
necessarily re-stamped too. Their inherited reason carried four inaccuracies: a $500 threshold that
no longer exists; a claim that the `0 <=` lower bound in `_evaluate_recent_inception` was undocumented,
false since item 2 added the scenario on 2026-08-09; a claim that nothing else in the suite would
catch that bound's removal, false for the same reason; and a late-reporting threshold given as 30
where the scenario uses 45. All four are corrected in the reason now on all 11 entries. This was the
third occasion that text would have carried forward unchanged — locator and digest were identical
each time, so nothing in the harness could have flagged it. Recorded here because it is the concrete
cost of the ledger having no per-mutant reason.

**Item 4d is done and merged to `main`** (merge commit `36ae5b3`, 2026-08-15). `siu_indicators.feature`
and `triage.feature` say "the continuous coverage date" (step text) and `coverage_start` (Examples
column) everywhere they used to say "the policy inception date" / `inception_date`.
`Candidate.policy_inception_date` is `continuous_coverage_date`; the reason code
`NO_POLICY_INCEPTION_DATE` is `NO_CONTINUOUS_COVERAGE_DATE`, matching the locked
`siu_indicators.feature` assertion exactly. The indicator name "recent policy inception" and the
function `_evaluate_recent_inception` were deliberately left alone, per this item's own
surgically-scoped-rename decision above — only the input date moved. Spec locked at `631f679`;
implementation at `9f4b4ad` carried the rename into step definitions, the `tests/api/` wrappers, and
`tests/unit/` (unit tests call the domain functions directly and never read feature files, the same
gap items 4a and 4b found — `docs/harness-findings.md`). Ledger at `d7ab0bb`: exactly the 6 approvals
measured stale before the lock — `siu_indicators.feature`'s three renamed scenario titles,
`triage.feature`'s renamed `inception_date`-now-`coverage_start` column — pruned, and the same 6
signatures re-approved under their new locators (confirmed by matching digest before commit, not
assumed from the rename), plus 8 `loss_amount`-keyed `triage.feature` entries re-stamped by the
unscoped approve. Project-wide reviewed-equivalent: **40 -> 34 -> 40**, exactly the predicted movement.
Green on the reopening branch before merge: 166/166 tests, code mutation 100%/197 killed, acceptance 4
specs / 0 surviving / 40 reviewed-equivalent / 0 stale.

**Item 4f is done and merged to `main`** (merge commit `26d9b21`, 2026-08-15). The Rule comment at
`siu_indicators.feature:126` no longer names `_is_recent_inception` (dead since `33d602b` renamed it
`_evaluate_recent_inception`) or the literal `0 <=` expression alongside it — both are the same
category of problem, a spec comment describing the implementation's shape rather than the behavior it
specifies. Spec locked at `f803abd`. Comment-only, spec-only, no `src/` change. The prediction this
item was written against is now confirmed rather than assumed: `features/siu_indicators.feature`
yields the same 38 mutants before and after, every locator byte-identical (not just the count), and
`gauntlet.lock.json`'s diff touches exactly one entry — `spec:features/siu_indicators.feature`,
digest moved — with zero ledger churn, no mutant or config entry added, removed, or reworded. `gauntlet
check` passes on `main` post-merge (166/166 tests, mutation 100%/197 killed, 4 specs / 0 surviving /
40 reviewed-equivalent / 0 stale). See this item's own entry above for a correction made while closing
it: the entry said the fix "costs one spec approve and lock," which conflates two unrelated gates —
`gauntlet lock` approves config paths for the protect gate, not specs.

Item 4e (close the loss-type vocabulary gap in `validation.feature`) is next — see its own entry
above.
