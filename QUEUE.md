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
    `duplicates.feature`.** Pure example-data rename, no rule changes: `auto_collision` ->
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
4b. **The recognized policy-number prefix set is a business rule, not example data.**
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
4c. **Missing perils: hurricane, sinkhole, and roof_leak.** A completeness gap, not a rename — the
    one a claims manager would actually stop at: a Florida residential intake system with no way to
    code a hurricane or a sinkhole claim. See `STATUTORY_REGISTER.md` for why hurricane and sinkhole
    are statutorily distinct, not just missing labels. Sequenced last of the three because each new
    value forces a severity decision, which is item 5's territory — adding perils without deciding
    their severity would push them silently through the standard fallthrough, which is the
    defaulting `CLAUDE.md`'s first constraint forbids. Either waits for item 5 or merges with it; not
    scoped further here. *Also see `ASSUMPTIONS.md`'s open decision on `loss_type` conflating perils
    with Section II coverage categories — this item should not assume an answer to that question
    either.*
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

## What to read

`CLAUDE.md`, this file, and `docs/harness-findings.md` every session. The rest is
per item — a document the current item does not need costs context the work needs
later.

| Working on | Also read |
|---|---|
| 4a, 4b | `ASSUMPTIONS.md` — the vocabulary and policy-prefix entries |
| 4c, 5 | `ASSUMPTIONS.md` and `STATUTORY_REGISTER.md` |
| 6 (phase 2) | everything, `PHASE2_DESIGN.md` first |
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
and its own reopening. Item 4a is next.

**Item 4a is drafted, not merged.** Branch `reopening/loss-type-vocabulary`, four commits on top of
`main`: `e86ae20` (the substitution itself), `3cde743` (repads `triage.feature`'s "Severity by loss
type" table for the new column width and fixes a header/data pipe offset that predated this branch),
`d793e94` (whitespace-only fix to the end-to-end scenario's NOT_EVALUATED row, also pre-existing,
`git diff -w` empty), and a merge of `main` forward to keep the branch a superset per this file's own
convention. Substitutions: `auto_collision` -> `lightning`, `auto_comprehensive` -> `smoke` in
`triage.feature`'s severity outline; `AU-7654321` -> `HO-7654321` in `duplicates.feature`'s
policy-mismatch row and its "Two existing claims both match the candidate" scenario. **Verified pure,
not assumed:** `HO-7654321` matches `POLICY_NUMBER_PATTERN` (tested directly against the compiled
regex); neither `validation.py` nor `triage.py` enumerates loss types as a closed set — read both
files directly and confirmed `_check_loss_type` only checks presence via `.strip()`,
`_check_injury_fields` branches on a single `== "injury"` comparison, and `triage.py`'s
`assign_severity` checks membership in the 2-element `{"injury", "fire"}` plus a single
`!= "theft"` comparison, with every other value — `lightning`/`smoke` exactly like
`auto_collision`/`auto_comprehensive` before them — falling through to `standard`. No `src/` change
is required. `validation.feature` was not touched. `gauntlet check` on the branch: every gate green
except `acceptance`, which reports both spec files changed since approval — the sanctioned state
between spec draft and implementation, not a defect.

**Blast radius, corrected from an earlier draft of this note that conflated two questions.** 21 of
the 42 current acceptance-mutant approvals sit on rows containing a loss_type or policy_number value
at all (11 on `triage.feature`'s end-to-end scenario, 10 on `duplicates.feature`'s "Matching against
a single existing claim") — that is what 4b or 4c would restale if either changed a different value
those rows contain, not what 4a itself stales. Measured against the actual keys: `triage.feature`
stales nothing (no approval names `auto_collision` or `auto_comprehensive`). `duplicates.feature`
stales 2 mechanically — the two whose locator keys embed `AU-7654321` — but **all 10 approvals on
"Matching against a single existing claim" need pruning and re-approving, not just those two**: the
other 8 keep unchanged keys and digests while their shared reason's prose still names `AU-7654321`,
so nothing in the ledger flags them and they'll cite a value the file no longer contains until someone
reads the text. The re-approval reason must describe rows by role ("the policy-mismatch row," "the
row excluded by loss-date distance"), never by contents — the sharper convention
`docs/harness-findings.md`'s "Approval reasons go stale silently where the key does not" entry now
states, added because this exact case is its second recorded instance. `duplicates.feature`'s three
standalone scenarios carrying this vocabulary in their own `Given` steps sit at zero approvals today
and stay unbounded — not restaged by the rename, but re-exercised by it, with no guarantee of the
same kill rate.

**Test files, for whoever implements.** `tests/unit/test_triage.py` and
`tests/unit/test_duplicates.py` mirror this example data exactly and change with the implementation
commit, not the spec — do not update them now. `tests/api/*.py` and `tests/acceptance/*.py` carry no
hardcoded loss_type or policy_number values (confirmed by grep) and need no changes at all.

## Open instructions

Anything issued but not yet completed, cleared as each is done. This tracks in-flight instructions;
the numbered queue above tracks reopenings.

- **Item 4a's spec draft on `reopening/loss-type-vocabulary` is awaiting spec approval** (`gauntlet
  spec approve`, mine to run) before implementation begins. Once implemented: prune and re-approve
  all 10 stale mutants on `duplicates.feature`'s "Matching against a single existing claim" (see
  above), not just the 2 that restale mechanically.

`main` is pushed to `https://github.com/xaziaver/ClaimGate`
