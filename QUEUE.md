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
    non-owner-occupied risks), possibly `MH` where a configured book writes manufactured housing. Note that
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
    blocker, not a silent `standard`.** *(Done — see below.)* Sequenced after 4f. Motivation, as fact, not
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
4g. **Section II completeness for liability losses.** *(Done — see below.)* `_check_injury_fields` keys on
    `loss_type == "injury"` exactly, so a bare liability notice passes intake with no claimant
    details. Item 4e recognized `liability` and deliberately did not close this; `ASSUMPTIONS.md`
    records the underlying modelling defect. Ready to spec — every decision this item needs is now
    made, 2026-08-16.

    **Required-field sets vary by coverage category.** The universal four — policy number, loss
    date, loss type, notice type — are required regardless of category; everything else is
    category-specific, and injured-party/claimant fields are the first category-specific set this
    project specs. Of the fourteen recognized loss types, twelve are Section I property perils and
    two — `injury` and `liability` — are Section II. Section I adds nothing this item can act on: the
    model has no location or damage-description fields for any Section I peril to require, so this
    item is Section II only. Section I completeness is a separate, later item that has to add model
    fields before it can be specced at all, not a scope this item can absorb.
    
    **The three fields are renamed and two of them become carrier configuration.**
    `injured_party_name`, `injured_party_contact`, and `injury_description` become `claimant_name`,
    `claimant_contact`, and `incident_description` — a liability claim is frequently third-party
    property damage with nobody injured at all, the same wrong-lookup trap `policy_inception_date`
    was in item 4d. `incident_description` is required unconditionally. `claimant_name` and
    `claimant_contact` are each required or not by caller-supplied configuration with no default —
    `ASSUMPTIONS.md`, "Carrier-varying rules are caller-supplied configuration with no domain
    default" and "Item 4g's Section II required-field set is carrier configuration", located by
    those opening words rather than by line number. This supersedes the 2026-08-16 decision that
    contact is non-blocking and name blocks: that fixed a carrier policy choice in the domain.

    **Three things break that the earlier version of this entry did not name.** Measured against
    `main`, not predicted:

    - The `liability` row in "A loss type is recognized, unrecognized, or absent" asserts an empty
      blockers cell, which goes false once a bare liability notice produces blockers. Delete the row:
      `injury` already has none for exactly this reason and the comment above the outline gives the
      argument. Costs 2 mutants, both currently killed, zero approvals, and nothing else in the file
      moves — the other 30 mutants in that scenario keep locator and signature byte-identical.
    - "Multiple missing injury fields all survive as blockers, deduplicated in reason codes" builds
      its two blockers from name and contact. Under a configuration not requiring contact it yields
      one and the scenario's purpose is gone. Its title stays true, so nothing flags it.
    - "A later-canonical subset fires without any earlier code present" uses missing contact as its
      only MISSING_REQUIRED_FIELD. Same problem, same invisibility.

    Also: the comment on the "All blockers are reported together" rule states that the only other
    source of MISSING_REQUIRED_FIELD is the injured-party fields and that those apply only when the
    loss type is exactly "injury". False from this item. Its conclusion survives — `liability` is
    recognized and so never a source of LOSS_TYPE_UNRECOGNIZED — but the wording must move with it.
    And "Non-injury losses do not require injured-party details" needs retitling: its `wind_hail`
    body stays true, its title asserts a rule `liability` now contradicts.

    **Blast radius, measured at `85ed863` and re-verified unchanged at `ef90c77`.** Six scenarios
    carry this vocabulary and hold 40 of `features/validation.feature`'s 116 mutants
    (16 / 8 / 5 / 5 / 5 / 1). **None carries an approval** — all four of the file's approvals sit in
    "Recognized notice types are accepted," untouched. So zero stale approvals, and 40
    currently-killed mutants re-exercised with no guarantee of the same kill rate. Item 4a's shape:
    the restale is nil, the re-exercise is the unbounded part. The estate generalization moved
    `validation.feature`'s digest but not one locator or signature, so this figure survived it
    intact. It is still a floor to re-derive against the draft, not a target
    (`docs/harness-findings.md`, "An advisor's measured number goes stale").

    **Coverage E and Coverage F are not sub-divided,** and the spec comment should say so
    explicitly. MedPay is no-fault where personal liability is fault-based; both land in the same
    required-field set here, a deliberate scope decision rather than an omission.

    **Do not derive the category from a new `_SECTION_II_LOSS_TYPES` frozenset without enforcing its
    relation to the recognized set.** That repeats item 4h's exact shape; reuse 4h's fix — a direct
    unit-test assertion, not a scenario or a shared module.

4h. **The loss-type vocabulary lives in two files with no stated relation.**
    `validation.RECOGNIZED_LOSS_TYPES` holds fourteen values; `triage._HIGH_SEVERITY_LOSS_TYPES` holds
    three. **Correction, 2026-08-16: this item's original failure mode was wrong and is replaced
    below.** It claimed triage would route as severe a notice validation blocks — checked against the
    code rather than assumed: there is no orchestrator in `src/`, `triage_and_route` never consults
    `validate()`, and `PHASE2_DESIGN.md`'s state table (`RECEIVED -> TRIAGED` only "domain rules found
    no blocker"; `RECEIVED -> PENDED` on any blocker) sends a blocked notice to `PENDED`, never
    `TRIAGED` — so the stated failure cannot occur. The real risk runs the other way: if a
    high-severity peril were ever missing from `RECOGNIZED_LOSS_TYPES`, every notice of that loss type
    would resolve `LOSS_TYPE_UNRECOGNIZED` at intake and land `PENDED`, requiring a human resolution
    before it could ever reach `TRIAGED` and be assigned a severity or a queue — the most urgent
    category becomes the one that silently never reaches a queue on its own. That every high-severity
    value is a recognized value is true today, stated nowhere, and enforced by nothing — the same
    shape as the renamed-symbol problem items 4d and 4f dealt with. Not urgent: no current value
    violates it. *(Done — see below.)*

    **Decided, 2026-08-16: the fix is a unit test, not a scenario or a shared vocabulary module.**
    `test_every_high_severity_loss_type_is_recognized_by_validation` asserts
    `_HIGH_SEVERITY_LOSS_TYPES <= RECOGNIZED_LOSS_TYPES` directly. A Gherkin scenario would have to
    name both frozensets to state the relation, which `CLAUDE.md`'s no-symbols-in-scenarios rule
    forbids. A revisit trigger was rejected on this project's own evidence: `docs/harness-findings.md`
    records that a trigger keyed on `_is_recent_inception` sat inert for six days across four queue
    items before anyone caught the rename that broke it (item 4f) — the mechanism that would guard
    this relation is the same one already shown not to. A shared vocabulary module was rejected as
    disproportionate: the invariant is two lines, and a module refactor to enforce it would be sized
    for a problem this isn't. The code-mutation score did not move — 204 killed before and after,
    measured by isolating the mutation gate and running it against both versions — and that zero delta
    is not evidence the test was unneeded. Killed count counts killed mutants, not killers, so a test
    that only kills mutants other tests already kill can't move it; and the state this test guards —
    the two sets disagreeing while each module's own tests still pass — is only reachable by a
    coordinated edit across two files, which single-point mutation never produces. See
    `docs/harness-findings.md`'s "Process and technique" section for the general form of this finding.
4i. **`the reason codes are "..."` cannot express an empty expectation.** *(Done — see below.)* The step splits its
    expected string on `;`; an empty string does not split into an empty list — `"".split(";")` is
    `[""]`, not `[]` — so a scenario asserting zero reason codes against this step would compare a
    one-element list of empty string against the real, empty result and fail on a false mismatch.
    The sibling step, `the blockers are <compact>`, guards for exactly this case: it checks for an
    empty string before splitting and returns `[]` directly. Nothing in the suite currently exercises
    the empty case on `the reason codes are` step — every scenario using it asserts a non-empty
    string — so the gap is latent, not a live failure. Found while drafting item 4e's spec, when an
    outline was drafted against the wrong step and the mismatch was caught only by reading the step
    definition before writing the outline against it, not by any gate.

    **Decided 2026-08-17: the fix is the step definition, and it lands inside item 4g's
    implementation commit.** The sibling step guards for the empty case before splitting; this one
    is simply missing that guard, so the step is wrong and the spec is not. Item 4g's scenarios
    assert notices that are not blocked, so they use `there are no blockers`, which already works —
    4g is not blocked on this, but it is the item that makes the gap reachable, so it closes there
    rather than staying latent. The spec draft commit stays spec-only per `CLAUDE.md`; the step fix
    belongs with the implementation.
4j. **The recognized policy-number prefix set is carrier configuration, not a domain constant.**
    *(Done — see below.)* Item 4b narrowed `POLICY_NUMBER_PATTERN` to `HO` alone, justified as "a carrier scope decision —
    `HO` is what's confirmed today," where what confirmed it was a named carrier estate that is no
    longer this project's target (`ASSUMPTIONS.md`, "ClaimGate is a general product"). The behaviour
    stands as the shipped configuration's scope; the justification does not, and a reader will take
    it as a finding rather than a configuration choice. Under the caller-supplied-configuration
    entry, the recognized prefix set is a configuration value with no default, not a frozenset in
    the domain. Blocked on nothing. Sequenced after 4g so it reuses whatever configuration mechanism
    4g establishes rather than inventing a second one alongside it.

    **This is not the same defect as `POLICY_NUMBER_PATTERN` itself.** `ASSUMPTIONS.md`'s open
    decision concludes the number *shape* — two letters, a hyphen, seven digits — is structural and
    belongs to phase 2's adapter layer, because a bare scalar parameter does not resolve it. The
    prefix *list* is a scalar set and a parameter does resolve it. Do not merge the two: this item
    is the parameter, and the shape stays open for phase 2.

    *Blast radius, not yet measured.* `validation.feature`'s "Policy number format" outline keeps
    its `AU`/`CP`/`CA`/`GL` rows deliberately (item 4b, above) — they document which lines the
    configured book does not write. Whether those rows survive as example data or become
    configuration-dependent is the first question this item's spec has to answer, and it decides
    whether the outline stays mixed-outcome, which is what keeps its mutants killed (item 4e).

4k. **The SIU reason-code precedence when both recent-inception inputs are absent is reachable,
    unasserted, and invisible to every gate.** *(Done — see below.)* `_evaluate_recent_inception` checks the continuous
    coverage date before the threshold, so when both are missing the result is
    `NO_CONTINUOUS_COVERAGE_DATE` rather than `NO_THRESHOLD_CONFIGURED` — the missing input outranks
    the missing rule, because a threshold cannot help without a date. `siu.py` carries a comment
    saying so and ending "Do not reorder these checks." That comment is the only thing protecting
    the ordering.

    **Nothing asserts it.** All nine scenarios in `siu_indicators.feature` supply at least one of
    the two inputs: "No continuous coverage date known" supplies the threshold, "No recent policy
    inception threshold configured" supplies the date, and "No late reporting threshold configured
    and no continuous coverage date known" supplies the recent-inception threshold explicitly. A
    reordering of those two checks would fail no test, and mutation testing does not generate
    statement reorderings, so no gate can see it. Mutation is what caught the comparable unasserted
    lower-bound guard during item 2's reopening; here it cannot help, which is why this needs a
    scenario rather than a stronger threshold.

    **`PHASE2_DESIGN.md` deferred this on a premise that has since expired,** and the entry there is
    corrected as of 2026-08-18. It reasoned that the combination was unreachable because the
    recent-inception threshold was "a fixed, always-supplied value of 30." Item 2 removed both SIU
    threshold defaults, so the threshold is caller-supplied and may be absent — the "No recent
    policy inception threshold configured" scenario proves it — and a caller omitting the threshold
    for a candidate carrying no coverage date reaches this state today.

    **Sequenced before phase 2, not during.** It is a phase-1 domain gap, the specification work is
    one scenario, and phase 2's jurisdiction-config work is specifically what will start producing
    the omitted-threshold case in volume. Inheriting an unasserted precedence rule into the phase
    that begins exercising it is the wrong order. Blocked on nothing.

    *Blast radius, measured.* One added scenario to `siu_indicators.feature`, which holds **seven**
    of the ledger's 67 approvals across **five** scenarios — the advisor's unmeasured estimate of
    "four across three" was taken from `validation.feature`'s count rather than from the ledger and
    was wrong, which is what labelling it unmeasured was for. A new scenario adds locators rather
    than moving existing ones, so no restale: 38 -> 39 mutants, one new, all seven approvals
    byte-identical.

5a. **Carrier configuration: the loader, and the rejection of an unrecognized value.** *(Done — see below.)* Phase 1 moved
    six values out of the domain and made them caller-supplied with no default — `validate`'s
    `claimant_name_required`, `claimant_contact_required`, and `recognized_policy_number_prefixes`
    (items 4g, 4j), `compute_siu_indicators`'s two thresholds (item 2), and `find_duplicates`'s
    `window_days` (item 3). Six, verified against the signatures on `main` rather than counted from
    this file. The shell cannot call the domain at all until something supplies every one, which is
    why this is first: every later item calls it.

    **`PHASE2_DESIGN.md`'s carrier-reference section places the per-carrier rules file in phase 3,
    and that sentence predates all six moves.** Corrected there as of 2026-08-22. The identity
    reference and the rules file stay physically separate as that section requires — identity is
    `carrier_code` to NAIC, rules are the six values — because merging them is what would make
    `carrier_code` look branchable.

    **A lookup keyed by `carrier_code` is not a branch on `carrier_code`, and this entry has to say
    so** or the next reader takes it for the leak the carrier-reference section forbids. The shell
    selects a parameter set by key and passes it through; no code path reads the key to choose
    behaviour. The jurisdiction map (5g) is the same shape, which is the check: if the two end up
    structurally different, one of them is wrong.

    **This is where the rejection `ASSUMPTIONS.md` already names as an unwatched gap lands** — see
    "A carrier configuration crosses into the domain already resolved." That entry records the
    loading boundary as the only thing between a mistyped configuration file and a silently wrong
    required-field set, and records that no gate watches it: mutation cannot, because the engine
    substitutes between values a column already contains. An unrecognized or absent configuration
    value is refused at load and never reaches a domain call. Loading is not intake — refusing a
    malformed configuration file refuses nothing a reporter sent and creates no statutory duty, so
    the always-accept rule does not reach it.

    *Blast radius, unmeasured.* A new feature file and its first `gauntlet spec approve`. Measure
    before drafting, per the technique in `docs/harness-findings.md`.

5b. **Instant-to-jurisdiction-date resolution, as its own named function with its own scenarios.** *(Done — see below.)*
    Specified already in `ASSUMPTIONS.md`'s "Timezone-correct 'now'": the shell receives a
    timezone-aware UTC instant and converts it to a calendar date in the jurisdiction's timezone
    before any domain call, and the domain never receives a date derived from server local time.
    Four scenarios named there — 01:00 and 22:00 Eastern resolving to the Eastern date, and both DST
    transition boundaries, each needing a case on either side per the standing constraint.

    Independent of 5a and sequenced second because it is small, it gates cleanly, and 5c calls it on
    every request. Getting it wrong in either direction produces a wrong `LOSS_DATE_IN_FUTURE`
    determination — false positives from a zone behind Eastern, false negatives from UTC — on a
    field that already blocks intake today.

5c. **Intake: `POST /notices`, `GET /notices/{notice_id}`, the three reachable states, the two-write
    receipt, and the audit entries those transitions produce.** *(Done — see below.)* The core of phase 2 and the largest
    item in this queue. `PHASE2_DESIGN.md`'s record-state model, audit-log schema, and HTTP-surface
    sections are the specification input; the `400` on an unknown or malformed `carrier_code` is
    this item's, while the reference file it validates against is 5a's.

    **The receipt write is two writes deliberately, and the reason is statutory, not architectural.**
    `RECEIVED` and its timestamp persist durably before any domain rule runs, because that timestamp
    starts the Fla. Stat. 627.70131(1)(a) acknowledgment clock and must not depend on whether rule
    evaluation succeeds, is correct, or runs at all. A single write after triage is the defect this
    item most needs a scenario against.

    **SIU is out of scope here.** No SIU computation, no SIU storage, no SIU field — 5f builds all of
    it. Serializers are allow-list based from this item onward regardless, per `PHASE2_DESIGN.md`'s
    SIU rule 2, because a deny-list leaks every field added after it is written and 5f is when
    fields start being added.

    **A boundary-gate fact that shapes this item, read from `gauntlet/gates/boundary.py` rather than
    inferred.** The gate walks only the steps directory (`tests/acceptance` here) and flags absolute
    imports whose top-level root matches a top-level importable name under `src/` — which is exactly
    one name, `claimgate`. `tests/api/` is not walked at all, and an import of anything not named
    `claimgate` is invisible to it. So a step definition that imports an HTTP client library and
    builds its own client passes the gate cleanly while binding the acceptance suite to transport
    detail. The test API layer owns constructing and driving the application; that discipline is
    unenforced here and has to be held by review.

    **Item 5c owes a scenario proving the shell supplies a timezone-aware UTC instant — an obligation
    inherited from item 5b, not a defect in it.** `ASSUMPTIONS.md`'s "An instant that is not a
    timezone-aware UTC instant is out of scope for item 5b" entry puts a naive instant out of scope
    for `resolve_jurisdiction_date` as a caller-contract violation, and that decision stands. But the
    violation is silent rather than loud: `datetime.astimezone()` on a naive value assumes server
    local time and returns a plausible wrong date rather than raising. Measured 2026-08-23 — with the
    server clock on `America/Chicago`, a naive `2026-06-11T01:00` resolves to `2026-06-11`, where the
    correct answer for the aware UTC instant is `2026-06-10`. `[tool.mypy] strict = true` cannot catch
    it, because aware and naive datetimes share one type. 5c is where the instant is obtained, so 5c
    is where this is defended — a guard in `domain/jurisdiction.py` would be behavior no scenario
    describes.

    **Further-split trigger, stated before the cost is incurred rather than after.** Item 4 was one
    number that became 4a through 4k. If this item's spec draft carries more than one Rule per
    endpoint, or its measured mutant count would put more than roughly a dozen survivors in a single
    scenario, split it — the deciding argument is reason granularity, not the count, per item 4g's
    finding that `gauntlet mutant approve` scopes only by feature file and `--scenario`.

5d. **Idempotency on `POST /notices`.** *(Done — see below.)* `Idempotency-Key` as a header, uniqueness on
    `(carrier_code, idempotency_key)` enforced by a database constraint rather than a
    check-then-write, 24-hour expiry, replay returning `200` with the original `notice_id` and
    receipt timestamp but the notice's current state, replays kept out of the audit trail. All
    specified in `PHASE2_DESIGN.md`; this item builds it.

    Sequenced after 5c because the constraint is a real database constraint and there is no schema
    to put it on until 5c exists. Its own reason for being separate from business duplicate
    detection is in `PHASE2_DESIGN.md` and should not be re-litigated here: a bare network retry is
    indistinguishable, to the duplicate matcher, from a genuinely separate loss on the same policy
    inside the match window.

    **The size gate has zero headroom on the function this item's port touches, noted here so
    whoever builds it isn't surprised by it mid-change.** `gauntlet.toml`'s `max_function_lines` is
    25; `store.py`'s `receive_notice` is 25 lines today (measured 2026-08-24, after item 5c's
    payload-persistence fix). The SQLite port (`ASSUMPTIONS.md`, "Persistence engine") rewrites this
    function regardless, so this is a tripwire, not a blocker — but it means the port has to extract
    rather than grow in place from the first line written, not after the gate fails once.

5e. **`POST /notices/{notice_id}/resolution`.** *(Done — see below.)* The `PENDED → TRIAGED` transition, `USER` actor
    only, `409` when the notice is not currently `PENDED`, `200` when the supplied data clears every
    blocker, `422` with the current blockers when it does not — and, in that last case, a notice
    that stays `PENDED` while an audit entry is still written with `outcome=REFUSED`. A refused
    resolution attempt is an audit event, not a non-event.

    **Supplemental data never mutates the stored payload**: each resolution writes its own immutable
    payload record with its own hash, linked in arrival order, and the current view is derived from
    that sequence. Tolling is recorded and never computed — precise UTC pend and resolution-received
    timestamps, no tolling logic, and no field named `tolling` anywhere in phase 2.

    **Carried from item 5d, 2026-08-24:** a scenario that a replay of a notice this endpoint moved
    `PENDED → TRIAGED` reports `TRIAGED` — the "current state, not the state at first processing"
    half of `PHASE2_DESIGN.md`'s replay rule, which 5d can only half-prove.

5f. **SIU separation: the separate table, the write-side event trail, the allow-list serializer's
    negative assertions, and SIU computation wired in at all.** *(Done — see below.)* `PHASE2_DESIGN.md`'s SIU section is
    the specification input. Indicators live in their own table rather than as columns on the notice
    record, because physical separation is the part that cannot be retrofitted; an append-only
    indicator-event trail records which indicator fired, under which `ruleset_version`, and when.
    No read-side access log — with no authentication to populate it, that record would be theater.

    **A scenario asserting SIU indicators are absent from both response bodies is required**, and it
    is meaningful only from this item onward, because before it there is nothing to leak.

    **Every phase-2 notice will carry a not-evaluated recent-inception indicator, and that is
    correct rather than a stub to fill in.** The continuous coverage date arrives by adapter lookup
    in phase 3; phase 2 has no adapter, so the input is genuinely absent and the indicator resolves
    `NOT_EVALUATED` with `NO_CONTINUOUS_COVERAGE_DATE` — see `ASSUMPTIONS.md`, 2026-08-22. An agent
    that supplies a placeholder date here has manufactured a determination nobody made, which is the
    exact failure "unevaluated is not negative" exists to prevent.

5g. **The jurisdiction map, and the two swappability proofs.** *(Closed at merge `e7beee2`,
    2026-08-27 — see below.)* Statutory configuration is a real map
    keyed by jurisdiction code with exactly one entry populated (`FL`) — a genuine lookup, not a
    constant dressed as one. Jurisdiction derives from the insured property's state, never the
    carrier's domicile and never the reporter's address. An absent or non-`FL` `property_state` does
    not block: the notice proceeds to `TRIAGED` carrying an attribute for human review. No
    jurisdiction-based branching anywhere beyond that one lookup, and no second real jurisdiction.

    **The two swappability tests are demo artifacts proving the absence of hardcoding, not
    features** — a carrier-set swap against an alternative reference fixture, and a jurisdiction
    swap against a fictional second-jurisdiction fixture. `PHASE2_DESIGN.md` records what phase 1
    already settled and what these therefore still have to prove: the domain half is done, since a
    carrier difference has nothing left in the domain to condition on, so what remains unproven is
    that the shell carries a second carrier set and a second ruleset through to those parameters
    without a branch of its own. Sequenced last because that is only provable once there is a shell
    to carry them. **If either test is hard to write, the difficulty is the finding — do not bend
    the test to make it pass.**

5h. **An absent loss date passes validation and reaches `TRIAGED` carrying `0001-01-01` as
    today's date.** *(Closed at merge `e8e76c0`, 2026-08-27 — see below.)* `validate()` has no
    presence check for `loss_date`: `_check_loss_date` tests only the future bound, and
    `Candidate.loss_date` defaults to `date.min`. No scenario anywhere
    covers it. A phase-1 reopening — `validation.feature`, `validation.py`, `models.py` — not item
    5c's, even though item 5c's own Rule 3 title ("A notice is created only if its loss date is a
    real date") implies an answer its table does not contain: an absent date is neither "a real
    date" nor tested as "not a real date" there. See `ASSUMPTIONS.md`, "An absent loss date is a
    domain blocker, not a schema refusal," for the resolution — `PENDED` with
    `MISSING_REQUIRED_FIELD:loss_date`, the blank-policy-number case one field over.

5i. **The status code for a carrier present in the identity reference whose rules entry resolves
    `CARRIER_NOT_CONFIGURED` or malformed has no row in `PHASE2_DESIGN.md`'s closed status-code
    table.** *(Closed at merge `5ae5762`, 2026-08-28 — see below.)* Found while drafting item 5c:
    the table's two `400` rows cover an unknown/malformed `carrier_code` and a schema-invalid
    body, neither of which is this case — a carrier this
    deployment's identity reference recognizes but whose rules were never onboarded, or were
    onboarded wrongly. See `ASSUMPTIONS.md`, "A carrier this deployment administers but cannot
    configure is our defect, not the reporter's" — 5xx, not 400, still with a receipted payload
    record. Sequenced as its own item because it adds a row to a table item 5c inherited as closed,
    not a change item 5c's own spec should make.
    **Carried from item 5e, 2026-08-25:** the scenario for a resolution against a notice at rest in
    `RECEIVED` — `409`, body carrying state `RECEIVED`, nothing persisted — belongs here, because
    this item is what makes that state reachable by a specified path. It reopens
    `resolution.feature`'s first rule; cheap while that rule carries no approvals. Two more rows join that
    reopening, decided 2026-08-25: an unknown notice id → `404`, nothing persisted; an
    unparseable loss date in the resolution body → the schema-invalid `400`, nothing persisted,
    checked at the boundary beside `actor_id` so the merged-view parse in
    `shell/resolution.py` becomes unreachable and is removed. Both raise `NotImplementedError`
    until then.

    **Carried from item 5g, 2026-08-27: a fourth escalation, and it changes what "resolving this
    item" means.** Item 5g rebuilt its `NotImplementedError` rather than removing it, in
    `shell/rules.py`, and the rebuilt raise is this item's class of question. It fires when **this
    deployment's own jurisdiction map** holds an entry naming no timezone, or naming one the system
    cannot resolve — `select_jurisdiction`'s `MALFORMED` outcome, a third outcome grown for exactly
    this. Like the two carrier cases above, it is a deployment-configuration defect rather than
    anything the reporter did, so it is the same shape of question: what status code a caller sees
    when the fault is ours. It is undecided, and the raise's own message says so rather than
    implying a resolution. **Resolving item 5i means deciding all four status codes, not the
    original three.**

5j. **The reason-code precedence `NO_LOSS_DATE` > `NO_JURISDICTION_DATE` is ratified, implemented
    by item 5h, and is asserted nowhere.** *(Done — see below.)* The both-absent case — no loss date and no
    jurisdiction date — becomes reachable once item 5h makes the loss date optional, and
    `validation.feature` cannot express it: its scenarios always have a today, and the vocabulary
    for a notice with no jurisdiction lives in `jurisdiction_selection.feature`'s Rule 3, which
    this item reopens with one row — an unsupported property state and an absent loss date,
    asserting `NOT_EVALUATED:NO_LOSS_DATE`. Item 4k is the precedent: an ordering between two
    absences is invisible to every gate — no test fails on a reordering, and mutation does not
    reorder statements — so until this row exists the precedence is protected by a source comment
    and nothing else, the state 4k existed to close. Sequenced after item 5h's implementation,
    because the behaviour the row asserts does not exist before it; independent of item 5i.
    *Blast radius, unmeasured — measure at drafting, per `docs/harness-findings.md`.*

    **Premise corrected, and the sequencing precondition satisfied, 2026-08-27, after item 5h's
    implementation merged at `e8e76c0`.** The both-absent case is not unreachable and never was: a
    `NoticeFields` carrying no `property_state` and no loss date reaches it through the shell today,
    which is exactly the shape the test that preserved item 5h's gap already had. What is true is
    narrower than what this entry claimed - **nothing asserts which reason the determination names**,
    so no test fails on a reordering, and mutation does not reorder statements. The shortcut that
    follows was considered and **declined**: a shell or unit test could assert the precedence without
    touching any spec, but such a test is agent-editable and sits outside the approval ledger, and
    this item exists precisely so the ordering is protected by a human-locked spec row rather than by
    something a later session can rewrite without anyone approving it. A test alongside the row is
    fine; it is not a substitute for the row. Item 5h's source comment in
    `_determine_future_dated_loss` is written to the corrected claim, not the original one.

    **Rider, added 2026-08-28 at item 5i's close: this item also corrects
    `jurisdiction_selection.feature`'s line-29 comment.** That comment says a carrier the identity
    reference recognizes whose rules cannot be resolved "is QUEUE.md item 5i's undecided status
    code, which no scenario in this file may reach." The case is built, ratified and merged — it is
    `500` with `CARRIER_RULES_UNRESOLVABLE` — so the claim is false on both halves. It is the one
    known stale claim item 5i left standing, and it survives outside `src/`: that item's sweep
    corrected every falsified comment under `src/`, and this one is in an approved spec, where a
    comment fix costs an approval cycle of its own — which this item's reopening pays anyway.
    The second half of the sentence needs judgment, not just a factual fix — whether a scenario in this file *may* now reach the case is a scope question for
    whoever drafts the reopening, and the answer that keeps Rule 3's subject intact is probably
    still no. Do not let the correction quietly widen the rule.

## Phase 3

6. **Phase 3 opens with planning documents, not code.** This session's review found that no
   document says what "done" means for ClaimGate as a product: `PHASE2_DESIGN.md` names "phase 3's
   adapter boundary" in a dozen places and scopes it in none, and nothing lists what follows it.
   The deliverables of this item, drafted with the advisor and human-ratified before any
   implementation item is queued: (a) `ROADMAP.md` — the target state for a pilotable FNOL service,
   which phase carries each missing piece, and what is out of scope permanently;
   (b) `PHASE3_DESIGN.md` for the policy administration adapter. Known missing, as of phase 2
   close, for the roadmap to place: no HTTP server binding (the shell's handlers return response
   objects; no framework is in the dependencies — a decision, `PHASE2_DESIGN` "not a separate
   server process"), no authentication (`PHASE2_DESIGN` states the audit endpoint returns PII to
   anyone who can reach it), no policy admin adapter — so no coverage verification ("in force on
   the loss date") and no claim numbers (`notice_id` is deliberately not one), no attachments, no
   reporter channels, no CAT handling, no deployment story.
   **Progress, 2026-09-01: (a) is ratified — `ROADMAP.md` at `42c6903`, ratification recorded in
   the file; (b) `PHASE3_DESIGN.md` is ratified. Item 6 is complete; the phase-3 items below are
   written against it.**
   Reading for this item:
   `PHASE2_DESIGN.md` in full, `STATUTORY_REGISTER.md`, `README.md`'s design commitments.

7a. **Term-in-force at the loss date (pure domain rule).** New spec
    `features/coverage_verification.feature`, then the rule. Four values — `IN_FORCE`,
    `NOT_IN_FORCE`, `BOUNDARY_DAY`, `NOT_EVALUATED` — per `PHASE3_DESIGN.md`, "Term in force at the
    loss date", and a scenario on each side of every boundary: loss inside an active term; before
    the first term; after the last; on a term's effective date and on its expiration date (both
    `BOUNDARY_DAY`); cancellation effective before the loss date, and after it (pending cancellation
    is `IN_FORCE`); loss on a cancellation effective date; retroactive reinstatement (`IN_FORCE`);
    reinstatement leaving a lapse, with the loss inside the lapse; loss on a reinstatement effective
    date. The result names the deciding term and its dates. Term history arrives as data; the rule
    reads no configuration and no clock. `RULESET_VERSION` bumps at the wiring item, not here — the
    rule has no caller until 7f.

7b. **Continuous-coverage date derivation (pure domain rule).** New spec
    `features/continuous_coverage.feature`, then the rule, under the 2026-08-14 semantics in
    `ASSUMPTIONS.md` ("Data we do not have at intake") unchanged: continuous coverage on the risk;
    back-to-back renewals continue it; an administrative rewrite continues it; a retroactive
    reinstatement continues it; a genuine lapse resets it to the date coverage resumed. Scenarios on
    both sides of each clause, including the single-term case and a history whose earliest terms
    predate what the source system can supply (`NOT_EVALUATED`, reason). Gives
    `Candidate.continuous_coverage_date` its first producer — at 7f, not here.

7c. **Identifier sufficiency and the new notice fields (pure rule + surface fields).**
    `insured_name`, `risk_address`, `risk_city`, `risk_postal_code` join `NoticeFields`;
    `property_state` stays the address's only state component. Sufficiency rule per
    `PHASE3_DESIGN.md`: searchable = policy number present, or insured name plus risk postal code;
    otherwise blocker `POLICY_IDENTIFIERS_INSUFFICIENT`. Scenarios both sides of each arm, including
    each field present alone. The new fields join the hashed field set: a byte-identical
    resubmission of an old payload under a key remembered before this item answers `409` rather than
    a `200` replay, bounded to the 24-hour key lifetime — item 5g's accepted consequence, accepted
    again here and recorded in this entry when the item closes.

7d. **Retire policy-number shape validation (reopens `validation.feature`).** Reverses items 4b and
    4j, ratified in `PHASE3_DESIGN.md`, "Identifiers". Delete the prefix scenario; retire
    `POLICY_NUMBER_MALFORMED` from the domain and `recognized_policy_number_prefixes` from the
    required carrier configuration, the rules files, and `carrier_configuration.feature`'s
    required-key rows. Before drafting: measure the full blast radius with the mutation engine
    against the lock at the working ref — the 2026-09-01 floor is 3 approvals deleted with the
    prefix scenario and 28 untouched, and the floor is what to check against, not the answer.
    `POLICY_NOT_MATCHED`, `POLICY_AMBIGUOUS` and the search behaviour are 7f's, not this item's:
    after 7d a policy number is accepted as given and nothing yet checks it against anything.

7e. **Port protocols, bindings, and the live-query implementations (shell).** The policy port
    (`search`, `term_history`) and claims port (`existing_claims`) protocols; three-valued results
    with reason codes and `as_of`, never raising; the per-carrier bindings file with per-binding
    timeout budgets and no defaults; unresolvable binding → deployment fault, new code, item 5i's
    pattern; the live-query implementation of each port against an in-process fixture service,
    timeout and unavailability paths included. Contract suite runs against the protocols so 7i can
    reuse it. No acceptance spec: nothing user-visible changes until 7f — say so in the gate report
    rather than manufacturing one. `register_claim` is named in the protocol documentation as phase
    6's and is not defined.

7f. **Intake wiring, persistence, and the identification outcomes (shell + spec).** New spec
    `features/policy_identification.feature`: the five-row outcome table in `PHASE3_DESIGN.md` —
    matched proceeds; zero candidates pends `POLICY_NOT_MATCHED`; several pend `POLICY_AMBIGUOUS`;
    port `NOT_EVALUATED` triages with the verification attribute carrying the reason; insufficient
    identifiers pend from 7c's rule. Port calls sit between the two transactions, ordered search →
    term history → existing claims → rules; the decision transaction writes decision, SIU events,
    and the new `coverage_verifications` row together. Term-in-force and continuous-coverage results
    become visible attributes on `GET /notices/{id}`; store the deciding term and the `as_of`, never
    the full history. `RULESET_VERSION` bumps here. Scenarios describe outcomes and attributes; none
    names a port, table, or column.

7g. **Resolution path restructured (shell).** Evaluation moves outside the write transaction: read
    the merged view, evaluate (ports included), write in a second transaction that re-checks
    `PENDED` and answers `409` if the notice moved. `resolution.feature`'s surface is unchanged — a
    re-run of its unmodified scenarios is the evidence; the race guard is unit-tested, and the unit
    test is named in the gate report. Port re-evaluation on resolution uses the merged identifiers,
    so correcting a policy number through resolution is what clears `POLICY_NOT_MATCHED`.

7h. **Duplicate detection wired (shell).** `existing_claims` feeds `find_duplicates` with the
    carrier's `window_days` on every transition into `TRIAGED`, both paths; results persist to
    `duplicate_evaluations` and surface as their own response field, not in `reason_codes`
    (2026-08-22). `duplicates.feature` is not edited. The first evidence the locked spec describes
    the product rather than the test API: say what the surviving-mutant picture looked like before
    and after in the gate report.

7i. **Extract-shape implementations and the swappability proof.** The extract implementation of each
    port — a generated file set with an `as_of` instant; a policy bound after the extract is
    `NOT_FOUND` as of that instant — passing 7e's contract suite unchanged; the acceptance suite
    green under live-query/live-query, extract/extract, and live-policy-beside-extract-claims
    bindings, with no shell change between runs. Any difficulty writing either implementation is
    reported as a finding, not smoothed over (`PHASE2_DESIGN.md`, "Swappability proofs").

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
| 4g | `ASSUMPTIONS.md` — "Carrier-varying rules are caller-supplied configuration", "Item 4g's Section II required-field set", "ClaimGate is a general product" |
| 4i | this item's own entry; no other document needed |
| 4j | `ASSUMPTIONS.md` — the same three entries as 4g, plus the `POLICY_NUMBER_PATTERN` open decision |
| 4k | `ASSUMPTIONS.md` — the carried-requirements entry on reason-code precedence; `PHASE2_DESIGN.md`'s "SIU handling" item 5 |
| 5a | `PHASE2_DESIGN.md` — "Carrier reference"; `ASSUMPTIONS.md` — the three configuration entries dated 2026-08-17, plus the per-carrier rules entry dated 2026-08-22 |
| 5b | `ASSUMPTIONS.md` — "Timezone-correct 'now'"; no other document needed |
| 5c | `PHASE2_DESIGN.md` — "Record state model", "Audit log", "HTTP surface"; `STATUTORY_REGISTER.md` |
| 5d | `PHASE2_DESIGN.md` — "Idempotency" and the "HTTP surface" status-code table |
| 5e | `PHASE2_DESIGN.md` — "Pending resolution and tolling"; `STATUTORY_REGISTER.md` |
| 5f | `PHASE2_DESIGN.md` — "SIU handling"; `ASSUMPTIONS.md` — "Data we do not have at intake" and the continuous-coverage entry dated 2026-08-22 |
| 5g | `PHASE2_DESIGN.md` — "Jurisdiction axis" and "Swappability proofs" |
| 5h | `ASSUMPTIONS.md` — "An absent loss date is a domain blocker, not a schema refusal"; `validation.feature`, `validation.py`, `models.py` |
| 5i | `PHASE2_DESIGN.md` — the status-code table; `ASSUMPTIONS.md` — "A carrier this deployment administers but cannot configure is our defect, not the reporter's" |
| 5j | `ASSUMPTIONS.md` — the item 5h three-decision entry dated 2026-08-27; `jurisdiction_selection.feature`'s Rule 3; item 4k's entry above |
| 6 | `ROADMAP.md`; `PHASE2_DESIGN.md` in full; `STATUTORY_REGISTER.md`; `README.md` |
| 7a–7d | `PHASE3_DESIGN.md`; the item's spec file; 7b also the 2026-08-14 entry in `ASSUMPTIONS.md`; 7d also the blast-radius technique in `docs/harness-findings.md` |
| 7e–7i | `PHASE3_DESIGN.md` in full; `PHASE2_DESIGN.md` "The two-transaction shape" and "SIU handling"; 7f–7h also `shell/notice_intake.py` and `shell/resolution.py` as they stand at the item's start |
| A regulatory value, anywhere | `STATUTORY_REGISTER.md` |
| A record state, the audit log, idempotency, or the HTTP surface | `PHASE2_DESIGN.md` |

**Process finding, 2026-08-23: this table's per-item entries can claim completeness they don't have.**
Item 5b's row reads `ASSUMPTIONS.md` — "Timezone-correct 'now'"; no other document needed`. The
item's actual blocking question — where the resolution function lives, `domain/` or a not-yet-built
shell package — turned out to be a `PHASE2_DESIGN.md`-shaped structural question, the exact kind of
document this row said wasn't needed. A memoryless session following the table alone would have
reached the same escalation, just with less to reason from before doing so. The table needs either a
column or a stated convention for "documents this item may need if it hits a structural question," or
its entries need to stop reading as exhaustive.

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
where a configured book writes that line, and `MH` (manufactured housing) after that — both
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
make, not a pickup for the next session. *Note added 2026-08-17: "`HO` is what's confirmed today"
was confirmed against a carrier estate that is no longer this project's target, so that rationale
has lost its referent. The behaviour stands as the shipped configuration's scope; item 4j reopens
the prefix set as configuration rather than correcting this closed item.*

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

**Item 4e is done and merged to `main`** (merge commit `423a78d`, 2026-08-16). `features/validation.feature`'s
Rule becomes "The loss type must be stated and recognized": `RECOGNIZED_LOSS_TYPES` (fourteen values —
fire, flood, hurricane, injury, liability, lightning, mold, roof_leak, sinkhole, smoke, theft,
vandalism, water_damage, wind_hail) sits beside `RECOGNIZED_NOTICE_TYPES` in `validation.py`, and an
unrecognized loss type now resolves `LOSS_TYPE_UNRECOGNIZED` — a distinct code from
`MISSING_REQUIRED_FIELD`, so a typo is no longer indistinguishable from a blank field. The recognized
set is drawn on what intake can interpret, not what the policy covers — flood, mold, and smoke are
recognized and routinely excluded or sub-limited on a Florida HO book; whether a notice is covered is a
downstream question. Mirrors `_check_notice_type`'s shape exactly, including where it deliberately
doesn't: `LOSS_TYPE_UNRECOGNIZED` joins `_CANONICAL_CODE_ORDER` between `NOTICE_TYPE_UNRECOGNIZED` and
`LOSS_DATE_IN_FUTURE`, while the check order in `validate()` stays as-is, per the existing comment on
why the two orders differ. Spec locked at `3daaa77`; implementation at `6d79852`.

**The outline shape was a measured choice, not a stylistic one — the reusable part of this item.** The
16-row outline mixes recognized, unrecognized, and absent loss types in one table rather than following
the notice-type scenario above it, which enumerates its four recognized values in their own
same-outcome table. In a same-outcome table, a mutation that swaps one recognized value for another
can't change the expected result, so it survives and costs a human approval to dismiss as equivalent —
exactly what happened to all 4 of the notice-type scenario's approvals. Measured directly against
gauntlet's real mutation engine, not assumed: isolating the 13 non-injury recognized loss-type values in
a same-outcome table of their own (mirroring the notice-type scenario's exact pattern) produces 13 such
survivors. Mixing outcomes in one table instead means every recognized-value swap lands on a row with a
different `blockers` expectation and gets killed outright — confirmed both by construction (`9e74ad3`:
"Zero recognized->recognized swaps in the new outline") and by the result (0 surviving, 40
reviewed-equivalent post-merge, unchanged from pre-merge). 13 approvals avoided, prediction held at zero
survivors.

`gauntlet check` passes on `main` post-merge (197/197 tests, mutation 100%/204 killed, 4 specs / 0
surviving / 40 reviewed-equivalent / 0 stale — the same 40 as before this reopening). Measured, not
assumed: `features/validation.feature`'s mutant count moved 80 -> 116 (verified by running
`gauntlet.acceptance.mutation.mutants()` directly against the feature file at both refs, not read off a
gate summary). Cross-boundary note recorded while closing this item, not acted on: `triage.py`'s
`_HIGH_SEVERITY_LOSS_TYPES` (`injury`, `fire`, `sinkhole`) are all members of the new
`RECOGNIZED_LOSS_TYPES`, but nothing enforces that relationship — see item 4h, added below.

**Item 4h is done and merged to `main`** (merge commit `62f9412`, 2026-08-16). See its own entry
above for what the fix is and why the other two options were rejected. `ASSUMPTIONS.md`'s entry
documenting the test also picked up a verified-on date on its five symbol references (a test
function, two frozensets, `validate`, `triage_and_route`), so it doesn't strand the way item 4f's
dead-symbol comment did. `gauntlet check` passes on `main` post-merge (198/198 tests, mutation
100%/204 killed, 4 specs / 0 surviving / 40 reviewed-equivalent / 0 stale — mutation score unchanged
from before this reopening, expected per the entry's own explanation above, not a sign of drift).

**Item 4g is done and merged to `main`** (merge commit `51f2956`, 2026-08-17), carrying item 4i with
it. The Section II required-field set became carrier configuration: `claimant_name` and
`claimant_contact` are each caller-supplied booleans with no default, `incident_description` is
required unconditionally, and both `injury` and `liability` are covered. The three model fields were
renamed from the injured-party vocabulary. `_SECTION_II_LOSS_TYPES` is held to
`RECOGNIZED_LOSS_TYPES` by a direct unit-test assertion, reusing item 4h's mechanism rather than
adding a second one. Item 4i's step definition now guards the empty case before splitting, matching
its sibling — it landed in this item's implementation commit, as decided.

**The decision this item shipped is not the one it started with.** The 2026-08-16 session settled
that `claimant_contact` stops blocking while name and description stay required. That was superseded
on 2026-08-17: fixing a carrier policy choice in the domain is what the configuration entry in
`ASSUMPTIONS.md` forbids, and making both fields configuration dissolved the question rather than
answering it — a book that holds claimant details at first notice and one that does not are now both
expressible, so there is no shipped answer to be wrong about.

**Three scenario breaks the original entry did not name were found by measurement, not by reading.**
The `liability` row in the loss-type recognition outline asserted an empty blockers cell that went
false; "Multiple missing claimant fields" and "A later-canonical subset" both built their blockers
from a field that stopped blocking, and both keep true titles while their bodies break — which is
why nothing flagged them. See the item's own entry above.

**The spec took three drafts, and the second and third are the instructive ones.** The first draft
measured correctly and still under-specified the item: every scenario asserting a claimant-field
blocker used `injury`, all three mentioning `liability` asserted no blockers, and an implementation
keying on `loss_type == "injury"` would have passed it unchanged. It also stated the configuration
in unquoted fixed `Given` lines, which generate no mutants at all — so the subject of the entire
item was outside mutation's reach while the count rose from 116 to 122 and looked like growth. The
second draft fixed both and produced one eleven-row outline carrying a `loss_type` column, which
simulated at ~31 surviving mutants: the rule is symmetric across `injury` and `liability` by design,
so every swap in that column is inert. The third split it into two six-row outlines with the loss
type fixed per outline, which removed that column entirely. **The deciding argument was reason
granularity, not the count**: `gauntlet mutant approve` scopes only by feature file and
`--scenario`, so thirty-one survivors in one scenario would have shared one reason spanning three
unrelated equivalence arguments — item 4c's recorded failure at triple scale.

**Final shape:** `features/validation.feature` 116 -> 178 mutants; 24 surviving, 12 per outline,
confined to the configuration-flag and field-value columns with none in `description` or `blockers`.
Predicted at 24 before implementation and measured at 24 after, which is the check that the
implementation reads the configuration the way the specification means it. `gauntlet check` passes
on `main` post-merge (213/213 tests, mutation 100%/209 killed, 4 specs / 0 surviving / 64
reviewed-equivalent / 0 stale).

**One defect was caught in review and fixed before the merge:** the implementation added
`DEFAULT_CLAIMANT_NAME_REQUIRED` and `DEFAULT_CLAIMANT_CONTACT_REQUIRED` to the step definitions and
read them through `context.get()`. The domain honored the no-default constraint and the harness
reinstated exactly what items 2 and 3 were merged to remove. It was inert at the time — every
Section II scenario stated its configuration — but a future scenario that forgot the `Given` would
have silently passed for the wrong reason, invisibly: step files are not covered by the spec digest,
and the code-mutation gate only mutates `src/`. The fix moved the values into `features/validation.feature`'s
`Background`, where they are approved, visible, and digest-covered, and made the step read the
context directly so a missing configuration raises. **Measured before recommending: `Background`
steps are collected into their own list and never walked by `mutants()`, so the count stayed at 178
and no locator moved.** A configuration value belongs in the specification, not in a constant beside
the code that reads it.

**Item 4j is done and merged to `main`** (merge commit `22d672e`, 2026-08-18). The recognized
policy-number prefix set is now a caller-supplied collection with no default; `POLICY_NUMBER_PATTERN`
drops its hardcoded `HO` and becomes shape-only, with the captured prefix checked against the
configured set. An unrecognized prefix still resolves `POLICY_NUMBER_MALFORMED` — no new reason code,
no unrecognized-configuration branch. The number *shape* stays a domain constant, per
`ASSUMPTIONS.md`'s open decision that it is structural and belongs to phase 2's adapter layer.

**Its specification was split for the reason item 4g established, applied before the cost was
incurred rather than after.** A single outline carrying the configured set as a column beside the
digit-count, case, and separator rows simulated at ~13 survivors: on a row testing `HO-ABCDEFG` the
configured set is inert, because the number is malformed whatever the set holds. Splitting into
"Policy number prefix recognition, by configuration" and "Policy number shape" — the latter with the
set fixed in a `Given`, which mutation never reaches — gave 3 survivors and 0. Both were measured
before the draft, not after. The `AU`/`CP`/`CA`/`GL` rows were reduced to one representative excluded
prefix: under configuration, "documents which lines this book does not write" is no longer a fact the
specification states, and four same-outcome rows would have bought equivalent-mutant approvals for
nothing new.

`features/validation.feature` 178 -> 180 mutants; 3 surviving, all in the prefix-recognition outline,
zero in the shape outline — which is itself the check that the two rules stayed separate.
`gauntlet check` passes on `main` post-merge (212/212 tests, mutation 100%/217 killed, 4 specs / 0
surviving / 67 reviewed-equivalent / 0 stale).

**ClaimGate is generalized away from a named carrier estate** (merge commit `ef90c77`, 2026-08-17).
The project was designed against a specific three-carrier Florida residential property estate; that
is no longer the target, and the working tree no longer names it. `ASSUMPTIONS.md`, `DISCLAIMER.md`,
and `PHASE2_DESIGN.md` lost the carrier names, the invented carrier codes, and the real NAIC company
and group codes — the codes being the identifying part, not the names, so removing one without the
other would have generalized nothing. Two spec comments carried the name too
(`features/validation.feature`'s policy-number prefix Rule, `features/duplicates.feature`'s window
rationale), so both files needed `gauntlet spec approve` again. **Measured rather than assumed: a
comment edit moves the spec digest but not the mutants.** The digest hashes raw file bytes
(`gauntlet/registry.py`, over `path.read_bytes()`), while locators and signatures come from the
parsed structure — `validation.feature` 116 -> 116 and `duplicates.feature` 57 -> 57, every locator
and signature byte-identical, all 40 mutant approvals untouched. A re-approval, not a re-review.

**The scrub's first attempt deleted two unrelated `ASSUMPTIONS.md` entries** — item 4g's two
configuration decisions — because the block to replace was identified by line number against a view
of the file taken before an earlier commit had shifted it. Caught by grepping the branch for the
entries the queue cross-references, restored at `141f799` before the merge. Locate a block to
replace by an anchor string, never by a line range.

**A corrupted spec was found on `main` on 2026-08-17, before any of the above.** `gauntlet check`
reported 197/198 tests and one modified, unapproved spec at 0.001s. Neither was a defect:
`features/duplicates.feature` was sitting in a mutated state from an interrupted acceptance run,
with `matching_claim_id` blanked on the first row of "Matching against a single existing claim" — a
killed mutant, left injected. `git restore` cleared it, no ledger change. Recorded because the
diagnosis was first wrong in an instructive way: the failing test's parametrize id
(`[HO-1234567-2026-06-01-fire-]`) is built from the example row *after* mutation, so two different
mutants in that scenario produce the identical id and the id alone cannot say which cell moved.
Identify an injection from `git diff`, or by matching the signature against
`mutation.mutants()` — never from the test id. See `docs/harness-findings.md`.

**Documentation was corrected against phase 1's completed state on 2026-08-18** (commit `0114b45`).
`README.md` still described a three-carrier estate as the design target and carried a disclaimer
paragraph asserting that carrier names and NAIC identifiers in the repository were public regulatory
information — directly contradicting `DISCLAIMER.md`, which the generalization had rewritten to say
the opposite. `PHASE2_DESIGN.md` carried six stale claims about phase-1 code, including two dead
symbol names in the paragraph arguing that SIU vocabulary must never harden into a conclusion:
`siu_flags.feature`, renamed at item 2, and `SiuFlags(late_reporting, recent_policy_inception)`,
replaced by `SiuIndicatorResult`. Item 4f's defect, in the document least able to afford it.

**Current state, `main` at `6e8364c`.** `gauntlet check` passes: 213/213 tests, code mutation
100%/217 killed, acceptance 4 specs / 0 surviving / 67 reviewed-equivalent / 0 stale. The ledger
holds 67 mutant approvals across 4 specs plus 3 config paths. `features/validation.feature` yields
180 mutants, `features/siu_indicators.feature` 39, `features/duplicates.feature` 57. No reopening
branch is open and no spec is unapproved.

**Item 4k is done and merged to `main`** (merge commit `7da0bd1`, 2026-08-18), and it needed no
implementation. The behaviour was already correct; what was missing was any assertion of it. Every
step the scenario needs already existed, so the item is a spec commit and an approval, with no code
change and no new step definition — the first item in this queue with that shape.

"Neither recent policy inception input is present" completes a 2x2 over date known/unknown and
threshold configured/absent. The corner that matters is the pair against "No recent policy inception
threshold configured": same threshold state, coverage date present in one and absent in the other,
and the reason code changes between them. That pair is what proves the ordering rather than
restating it, and the scenario comment says so, because a later reader pruning either row as
redundant would remove the proof with it.

**The gap existed because a deferral outlived its premise.** Both this file and `PHASE2_DESIGN.md`
recorded the combination as unreachable, on the grounds that the recent-inception threshold was
always a supplied value of 30. Item 2 falsified that on 2026-08-10 by removing the SIU threshold
defaults, and neither document moved for eight days. Nothing could have caught it: a reordering of
the two checks fails no test, and mutation testing substitutes values rather than reordering
statements, so the precedence was protected by a source comment and by nothing else. **A deferral
whose stated reason is a fact about the code needs the same revisit discipline as an approval
reason** — that is the reusable lesson, and it is why the entry now carries its history.

`features/siu_indicators.feature` 38 -> 39 mutants, one new and killed; 67 reviewed-equivalent
unchanged. `gauntlet check` passes on `main` post-merge.

**The toolchain that produced every gate result in this project was undeclared until 2026-08-18**
(commit `6e8364c`). `pyproject.toml` carried no `dependencies` and no `optional-dependencies`: every
tool the gates shell out to had been installed into one venv by hand and recorded nowhere. A fresh
clone could not run `gauntlet check`, which means none of the figures in this file were checkable by
anyone, including their author. It surfaced only by accident, when the project venv went missing and
the mutation gate reported `No module named mutmut` from Gauntlet's own interpreter — the message
names the module, the cause was the venv, and `gauntlet doctor` does not cover it because it checks
that tooling is present rather than that the environment is reconstructible.

**Rebuilding from scratch with current tool versions reproduced 213/213, 100% / 217 killed, and 67
reviewed-equivalent exactly**, which is the strongest form this project's evidence has taken: those
numbers are now reproduced rather than merely recorded. Direct tools are declared as a `dev` extra
and the exact versions are pinned in `requirements-dev.txt`. The package itself is never installed —
the root `conftest.py` puts `src/` on `sys.path` — so the install path matching how this project runs
is `uv pip install -r requirements-dev.txt`, not an editable install.

**Phase 1 is complete.** Items 1 through 4k are merged, and the documentation pass across
`README.md`, `PHASE2_DESIGN.md`, `QUEUE.md`, `ASSUMPTIONS.md`, and `docs/harness-findings.md` is
done. Item 5, the phase-2 build, is next, and `PHASE2_DESIGN.md` is where it starts.

**Item 5 is split into 5a through 5g, 2026-08-22.** Its entry was three lines pointing at a design
document covering seven independent concerns — a state model, four endpoints, an audit log, an
idempotency constraint, a jurisdiction map, a carrier reference, an SIU table, a timezone function,
and two swappability tests — behind one number and one spec lock. Item 4 was also one number, and
became 4a through 4k. The split is by spec lock: each subitem owns one specification, one measured
blast radius, and one approval boundary. Sequencing is 5a and 5b first because they are what 5c
calls, not because they are smaller.

**Four phase-2 decisions were made on 2026-08-22 and recorded in `ASSUMPTIONS.md`,** each of which
the shell would otherwise have had to decide for itself mid-implementation: the per-carrier rules
file moves from phase 3 into phase 2 (5a); duplicate-detection not-evaluated reason codes stay out
of `reason_codes` (5c's serializer); phase 2 matches duplicate candidates against ClaimGate's own
persisted notices only (5c); and the recent-inception indicator resolves not-evaluated on every
phase-2 notice because its input does not exist yet (5f). `PHASE2_DESIGN.md`'s carrier-reference,
duplicate-reason-code, and SIU-threshold-axis passages are corrected to match.

**Current refs, 2026-08-22.** `main` is at `071af43`. It carries phase 1 closed, item 5 split into
5a–5g, the phase-2 decisions in `ASSUMPTIONS.md`, three skills under `.claude/skills/`, and nine
new entries in `docs/harness-findings.md`. The earlier note in this section naming `55357df` and
`6e8364c` is superseded; no gate figure has moved, because nothing since `55357df` has touched
`src/`, `features/`, or the ledger.

**Item 5a is drafted, not locked, and its scope is contested.** The spec is
`features/carrier_configuration.feature` on branch `phase2/5a-carrier-configuration`, spec-only
commit `5d37a4f`. Four scenarios, 42 mutants measured directly against the engine — 17, 11, 4 and
10 by scenario. Survivors are unknown and unknowable until the spec is approved and step
definitions exist, because the acceptance gate's approval stage short-circuits before mutation runs.

**`gauntlet check` is red on the acceptance gate, and that is the guaranteed state rather than a
defect.** It reports `1 unapproved or modified spec(s)`; every other gate is green with `src/`
untouched. The diagnostic instructs a human to run `gauntlet lock`, which is the wrong command —
spec approval is `gauntlet spec approve`, and neither belongs to the agent. See
`docs/harness-findings.md`, "Command ownership."

**The next action is a redraft, not an approval.** Three things are owed before the spec is worth
locking, all recorded in `ASSUMPTIONS.md` under 2026-08-22: malformed-but-present values were
narrowed out of the draft and item 5a covers them; a refusal must name every value it rejected
rather than one; and the fourth scenario states four values by their domain parameter names in a
file that otherwise speaks business language, alongside a compound `CODE:field` reason value no
other feature file uses.

**What the draft got right and should survive the redraft:** the first rule is a plain scenario
rather than an outline precisely so its literals are mutation targets; both SIU thresholds are
proven configured and unconfigured; the refusal rows sit in one scenario so a single approval reason
covers them; and both tables carry a loading row so the engine has a differing row to swap against.
The draft also established that two of the six caller-supplied values accept `int | None` and four
do not — a distinction this file and `ASSUMPTIONS.md` had both been blurring, now corrected in both.

**The first redraft landed at `11fd18b` and needs a second.** Spec-only,
pushed, `src/` untouched. Measured against the engine and verified
independently rather than accepted from the agent's report: 42 -> 59 mutants,
17 / 11 / 4 unchanged and 10 / 12 / 5 on the three new refusal scenarios. Rules
1-3 are unchanged, confirmed by comparing all 32 locator and signature pairs
rather than by equal counts, which do not establish it.

**Two defects block a lock, both measured.** The malformed-value outline
states its expectation in the `Then` step as
`INVALID_REQUIRED_CONFIGURATION:<field>`, reusing a placeholder that also
appears in a `Given`, so the expectation is not a column and all 12 of its
mutants are equivalent - simulated 12 of 12, the first fully inert scenario in
this project. And the scenario carrying this item's headline rule, that a
refusal names every value it rejected, puts its whole assertion in a step data
table, which the Gherkin IR discards at parse time: measured 5 mutants, all on
`"AAAA"` literals, none on the assertion. Both are in
`docs/harness-findings.md`.

**The reason-code decision the agent escalated is settled the other way.** It
renamed `MISSING_REQUIRED_CONFIGURATION` to `INVALID_REQUIRED_CONFIGURATION`
to keep one code honest across both cases, and flagged it rather than treating
it as settled, which is the behaviour wanted. The answer is two codes, per item
4e's precedent one layer down. See `ASSUMPTIONS.md`, 2026-08-22.

**A claim in the prompt that produced that draft was wrong, and the agent was
right not to take it.** The prompt said the compound `CODE:field` reason value
is used by no other feature file. `validation.feature` carries 22
`MISSING_REQUIRED_FIELD` occurrences and 7
`POLICY_NUMBER_MALFORMED:policy_number` in `Examples` cells, plus a
`| code | field |` data-table form in nine scenarios. The agent read the file
and said so.

**The second redraft landed at `b039b48` and needed four corrections, none
structural.** Measured independently rather than accepted from the agent's
report: 76 mutants, 17 / 11 / 4 unchanged on rules 1-3, 10 on the new zero-day
rule, 33 and 1 on the two refusal scenarios; `gauntlet.lock.json`, `src/` and
`tests/` untouched across the whole branch, and `main` confirmed an ancestor of
it. Both shape decisions stand. The collapse of the refusal outline to a single
field/value pair, with `absent` as a value a field can be configured as, is
better than what was recommended: every non-blank cell substitutes to empty
rather than to a sibling value, so all thirty real-row mutants die.

**What needed correcting, and one piece of advice that was wrong.** Moving the
multi-value assertion out of a data table was right and cost five mutants
nobody measured, because a one-row outline forfeits its step literals - the
advice in `docs/harness-findings.md` that sent it to an `Examples` column is
now corrected there. The scenario title claimed a canonical order a single row
cannot exercise. The sort was specified over "field name" without saying which
string, while this file's field names are business prose and `validate()`'s are
snake_case. And three synonyms for a negative day count bought no
discrimination at all - 76 mutants before and after unifying them.

**The simulated survivor count on the refusal outline is 1 or 2, not 1.** The
blank row's `field` and `value` cells are symmetric; which of them survives
turns on what the loader does with an unrecognized field name, which item 5a
deliberately does not specify (`ASSUMPTIONS.md`). Recorded as a range because a
simulation reported as 1 that the gate later measures as 2 reads as
specification-implementation divergence, and that signal is only worth having
if the simulation was right.

**Rules 1-3's locators moved once during item 5a, at `b039b48`.** The counts
held at 17 / 11 / 4 throughout, which is why the record read "unchanged", but
three locators were replaced when the example prefix set changed from `HO;AU`
to `HO;DP` - twice in `Given "AAAA" recognizes the policy-number prefixes` and
once in `Then the recognized policy-number prefixes are received as`, across two
rules the decision was not about. Costless here because the spec was never
locked. The general shape is worth carrying: the blast radius of an example-data
change is the number of scenarios restating that literal, it is invisible from
the decision itself, and equal mutant counts will hide it. Compare locators, not
counts.

**Item 5a is done and locked.** `features/carrier_configuration.feature`
approved and locked at `f19317e` on `phase2/5a-carrier-configuration`, ledger
digest `sha256:99c29e034fd0d43c...`, matching the file reviewed at `3ebea71`
byte for byte. 84 mutants across seven scenarios: 17 / 11 / 4 on rules 1-3,
10 on the zero-day rule, 33 on the refusal outline, 5 and 4 on the two
multi-value scenarios. No step definitions and no `src/` change - the
acceptance gate stays red until 5b's implementation phase, by design. One
open item carried forward: the refusal outline's blank loading row costs 30
sibling-value mutants and adds one or two permanent equivalent approvals.
Correct as locked, not worth reopening for; revisit when the implementation
lands and those survivors need reasons written.

**Item 5b is next**, on `phase2/5b-jurisdiction-date` off `main`. Two of the
four scenarios its `ASSUMPTIONS.md` entry named tested the wrong thing and
have been corrected there; the entry now also records that the jurisdiction
timezone is a parameter rather than a constant, because Florida spans two
zones.

**Item 5b's first draft landed at `3d8278f`, spec-only, pushed.**
`features/jurisdiction_date.feature`: three rules, each its own scenario - an
instant resolves to the jurisdiction's local calendar date rather than the
UTC one (2 rows), the jurisdiction timezone is a parameter the resolution
reads rather than a zone it assumes (a plain scenario proving it with the
same instant under both `America/New_York` and `America/Chicago`), and the
UTC offset in effect for a date, not proximity to a DST transition, is what
moves a resolved date across a boundary (4 rows). Measured directly against
the engine: 18 mutants, 4 / 6 / 8 by rule. Simulated survivors: 0 across all
three - every row's instant and resolved-date values are pairwise distinct,
so every substitution the engine would pick produces either a value mismatch
or an unparseable literal, and unlike item 5a's field-name ambiguity, nothing
here turns on a question the spec leaves open. `gauntlet check` is red on
the acceptance gate on this branch, reporting one unapproved spec - the
guaranteed state between a spec draft and its approval, not a defect
(`docs/harness-findings.md`, "Command ownership"). The next action is a
human review and `gauntlet spec approve`, not an agent action.

**Item 5a's locked spec carries 47 literal mutants whose kills may all be
vacuous, and that is the first thing to check when its step definitions are
written.** Measured 2026-08-23 on the four features that already have step
definitions: a quoted literal mutated in a plain scenario renders a line that
binds to no step pattern, so it is killed at step resolution rather than by
the implementation. `carrier_configuration.feature` at `f19317e` has 47 of its
84 mutants in plain scenarios. Whether they are vacuous depends on step
definitions that do not exist yet; if they follow the house style, they will
be. The same question applies to the 30 blank substitutions the refusal
outline's loading row induces, which render lines with an empty field and may
not bind either. Not worth reopening a locked spec on a prediction - worth
measuring the moment there is something to measure against.

**Item 5b's timezone-parameter rule went from 22 nominal mutants to 20,
and from 16 real ones to 20.** Converting it from a plain scenario to a
two-row outline removed six quoted-literal mutants that would have died at
step resolution and added four Examples-column swaps that reach the domain.
Every mutant in `jurisdiction_date.feature` is now `kind == "example"`,
with no blank substitutions and no marker appends, so the nominal and real
counts coincide for the first time in this project. An earlier report of
this change gave the before-state as 24 nominal and 18 real; both figures
were two high, and the correction is recorded rather than silently fixed
because the point of counting real separately from nominal is that the two
diverge.

**Item 5b's implementation is blocked on an unresolved module-home question,
escalated rather than decided, 2026-08-23.** Neither `PHASE2_DESIGN.md` nor
`ASSUMPTIONS.md` names a `src/` path for the shell layer both documents
describe — "the phase-2 API shell must receive a timezone-aware UTC instant
and convert it to a calendar date... before calling any domain function"
(`ASSUMPTIONS.md`, "Timezone-correct 'now'") states the *responsibility* but
not a location, and no shell package exists yet: `src/claimgate/` holds only
`domain/`; everything else — 5c's endpoints, 5a's carrier/config loader — is
unbuilt.

The choice has a measured consequence, not just a style preference.
`pyproject.toml`'s `[tool.mutmut] source_paths = ["src/claimgate/domain/"]` —
a protected path this session cannot edit — is what the code-mutation gate
scopes to. Placing the resolution function inside `domain/` puts it under
that gate automatically, but contradicts the design's own framing that
timezone conversion is explicitly *not* a domain concern ("the domain never
receives a date derived from server local time"). Placing it anywhere else
keeps that separation but silently exempts it from code-mutation coverage —
mutmut will never generate a mutant against it, and there is no
session-writable way to extend `source_paths` to reach it. The other
structural gates (size, complexity, coverage, crap, duplication, static) run
over all of `src/` per `gauntlet.toml`'s `src = "src/"`, so those are
unaffected either way; only the mutmut-scoped code-mutation gate is.

Not decided here. Item 5b's own entry already says this is a shell concern;
this is the missing second half — where in `src/` the shell lives — and it
is genuinely unset, not merely undocumented.
**Corrected 2026-08-23: the constraint this entry records does not exist.**
`pyproject.toml` is not a protected path. Gauntlet's `DEFAULT_PROTECTED_PATHS`
(`src/gauntlet/config.py`) is `gauntlet.toml`, `.gauntlet/`,
`.claude/settings.json` and the lock file; those are what the PreToolUse guard
blocks. `pyproject.toml` appears only in `DEFAULT_VERIFIED_PATHS`, which the
protect gate hashes against the lock — "content-verified rather than blocked". An
agent may write it; the protect gate then fails with `N-1/N paths unchanged` until
a human runs `gauntlet lock`. Extending `[tool.mutmut] source_paths` was therefore
available as a proposal routed through a human, not blocked. The placement
decision was made on the merits and not on this constraint, but the false fact is
corrected here rather than the entry silently fixed.


**Item 5b is done.** Spec locked at `aafd66c`, implementation at `cefe8ec`, documentation
corrections at `12dbb48`, on `phase2/5b-jurisdiction-date`, all pushed. Not merged to `main` on its
own — per the 5a/5b split above, the two merge together once 5a is green.

`features/jurisdiction_date.feature` carries 20 acceptance mutants, 4 / 4 / 4 / 8 across its four
scenarios, every one `kind == "example"` — measured directly against
`gauntlet.acceptance.mutation.mutants()`, not read off a gate summary. Zero survivors, independently
re-measured against the locked spec rather than taken on trust from the implementing session's own
report: the branch's most recent full gate run (`20260823T184121-20922`, a stop-check run with no
`run.started`/`run.finished` bracket but a complete `gate.finished` sequence — see
`docs/harness-findings.md`) shows 236/236 tests passing and the acceptance gate passing at "5 spec(s),
67 reviewed-equivalent" — the same reviewed-equivalent count as before this item, confirming its 20
new mutants added zero new approvals. Code mutation: 100% / 232 killed project-wide, of which 15 are
`domain/jurisdiction.py` — agent-measured, in isolation, and recorded as such rather than independently
re-verified here.

A session report on 2026-08-23 attributed item 5b's status closure to two `main`
commits that did not contain it. The closure was on the branch, which is correct,
and the entry itself says so. The error was in the report only. Recorded because
a status summary that names the wrong commit is indistinguishable from one that
names the right commit until someone checks, and nothing in the harness checks it.

**Items 5a and 5b are merged to `main`** (merge commit `9935461`, 2026-08-23), confirmed by
`git show --stat` rather than assumed from this file, which never itself recorded the merge - the
gap this correction closes. `main` carries `features/carrier_configuration.feature`,
`features/jurisdiction_date.feature`, both domain modules, and both status sections above unchanged
from the branches they merged from. `gauntlet check` on `main` post-merge: 274/274 tests, mutation
100%/330 killed, acceptance 6 specs / 69 reviewed-equivalent / 0 stale.

**Item 5c's first draft landed at `a5379c7`, spec-only, pushed, on `phase2/5c-notice-intake` off
`main`.** `features/notice_intake.feature`: three rules - a schema-valid notice reaches `TRIAGED` or
`PENDED` synchronously and is retrievable either way (a two-row outline mixing both outcomes); the
receipt is its own audit entry, entered by `EXTERNAL` before the `SYSTEM` determination that follows,
proved on the row where every rule finds a blocker rather than the row where none does, because a
receipt that only shows up when validation goes well is exactly the failure the design exists to
prevent; a notice whose loss date is not a date at all is refused before receipt, with nothing
persisted (a two-row outline, a real date against one that is not a date at all, drafted as an outline
from the start once a second, differing row made it free rather than costly). Measured directly
against `gauntlet.acceptance.mutation.mutants()`: 13 mutants, 8 / 1 / 4 by rule, 12 of the 13
`example`-kind and domain-reaching. The one `literal`-kind mutant is the second rule's reused "absent"
policy number, restated as a plain-scenario quoted literal; the fact it represents is already real and
Examples-driven on the first rule, so its own likely vacuousness (this project's established
quoted-literal-in-a-plain-scenario defect) costs nothing beyond what the first rule already proves.
Simulated survivors: 0 across all three rules, evaluated against the rule as drafted in each case -
every mutant listed produces a mismatch against a correct implementation; none turns on a question the
spec leaves open the way item 5a's field-name ambiguity did.

**One phrasing defect was found and fixed while drafting, not shipped: paired possessive apostrophes
read as a quoted literal to the mutation engine.** "the notice's audit trail's first entry" contains
two apostrophes with `'s audit trail'` between them, which `gauntlet.acceptance.mutation` treated as a
delimited literal exactly like a double-quoted one - appending a marker outside the second apostrophe
and, since that step's text carried no other quotation, producing what would have been an additional
vacuous mutant unrelated to anything the sentence actually asserts. Rephrased to at most one apostrophe
per step line before drafting was finished, so this cost nothing in the delivered draft; recorded
because it is a mutation-engine behavior stated nowhere in `docs/harness-findings.md`, and the next
drafting session should know to check for it rather than rediscover it. Whether it belongs in that
file too is left to whoever closes this out.

**Four things this draft deliberately does not specify, each a named gap rather than a silent
assumption:**

- **The `400` on an unknown or malformed `carrier_code` validates against a disputed reference.** This
  item's own entry above says "the reference file it validates against is 5a's" - read most naturally
  as `carrier_configuration.py`'s rules loader. `features/carrier_configuration.feature`'s own comment,
  written during item 5a, says the identity-only reference (`carrier_code` to NAIC company and group)
  that `PHASE2_DESIGN.md`'s carrier-reference section describes "item 5c owns" - a different file with
  a different purpose, and `PHASE2_DESIGN.md`'s own text ties the 400 to that identity list by name
  ("validated against this reference list"). Nothing read while drafting settles which of the two the
  check is meant to hit, and they are not interchangeable: a carrier could be a recognized identity
  with a broken rules entry, or the reverse. A placement question per this session's own instructions -
  escalated, not decided from either precedent.
- **`GET /notices/{notice_id}/audit` and the not-found case on both `GET` endpoints sit outside
  `PHASE2_DESIGN.md`'s closed status-code table.** That table lists codes only for `POST /notices` and
  `POST .../resolution`. Nothing in items 5a-5g claims the audit-read endpoint or either `GET`'s 404.
  Not drafted.
- **Whether a `TRIAGED` notice carries a duplicate-candidate attribute is unsettled.** `PHASE2_DESIGN.md`
  and this item's own entry are explicit that SIU is out of scope here (item 5f builds all of it);
  neither says the same for duplicate detection, and neither claims it either. Not drafted, rather than
  assumed silently in either direction.
- **The zone a given notice's jurisdiction resolves to is still open, per `ASSUMPTIONS.md`'s own
  entry** ("The jurisdiction timezone is a parameter of the conversion, not a constant in it") - risk
  location, mailing address, and carrier configuration are named as candidates and none is chosen. This
  draft states "today, in the jurisdiction" as an already-resolved fact, the same way
  `validation.feature` already treats "today," rather than deciding the mechanism.
- **What counts as "schema-invalid" versus a domain blocker is inferred, not confirmed.** The draft
  treats a structurally wrong field (a loss date that is not a date at all) as the 400 case and an
  absent-but-well-typed field (a blank policy number) as a domain blocker landing `PENDED`, on the
  strength of `Candidate`'s own `str = ""` / `date.min` defaults in `models.py` - a recommendation that
  follows from what the code currently does, not from an independent reading of `PHASE2_DESIGN.md`,
  which does not draw this line itself.

**Further-split trigger, fired.** This item's own entry above states the trigger: more than one Rule
per endpoint. This draft carries three for one endpoint (`POST /notices`, with
`GET /notices/{notice_id}` folded into the same scenarios as a retrieval check rather than a Rule of
its own). Recommend splitting before locking, on the same reasoning item 4 was split on - each Rule
already carries its own reason and its own measured cost, and one lock covering all three would put
unrelated equivalence arguments behind a single `gauntlet mutant approve` reason the way item 4c's did
at scale. Not decided here; the human's call.

**`a5379c7` is superseded, decided by the human, 2026-08-23.** Four amendments returned:
restructure the receipt rule for real mutation reach; leave the loss-date schema-boundary rule
(Rule 3) untouched pending a human boundary decision; add a Background comment on the
claimant-name requirement's non-effect in this file; and decide the further-split trigger
explicitly rather than let it stand unaddressed. Landed at `bce47a6` on the same branch,
spec-only, no step definitions.

**The apostrophe finding is confirmed from source, not just reproduced.**
`gauntlet/acceptance/mutation.py`'s `LITERAL_PATTERN` is
`"[^"]*"|'[^']*'|\b\d+\.\d+\b|\b\d+\b` - the single-quote alternative matches any span between two
apostrophes, which is why two possessives on one step line produce a mutant on the text between
them, not on either possessive itself. The one-apostrophe-per-line rule stands; nothing in this
draft needed correcting on this point.

**The receipt rule (Rule 2) is restructured, measured before and after.** The plain scenario
`a5379c7` shipped had seven `Then` steps and exactly one mutant, the vacuous "absent" literal -
zero of the seven assertions were reachable by mutation, on the rule `PHASE2_DESIGN.md`'s audit-log
section calls out as carrying the most statutory weight in this item. Rewritten as a Scenario
Outline over the two audit entries themselves (one row per entry: ordinal, state, actor, identity,
blockers), measured as a string against the engine before being written to disk and compared
against a second candidate that kept `RECEIVED`/`EXTERNAL`/`SYSTEM` as fixed text on
named-not-columned steps:

| Candidate | Mutants | Kind | Notes |
|---|---|---|---|
| A - one row per entry (ordinal/state/actor/identity/blockers) | 10 | all `example` | chosen |
| B - one row per notice outcome, receipt fields fixed | 6 | all `example` | 4 of 6 duplicate Rule 1's own policy_number/state coverage; never touches the receipt entry's own actor or state, since fixed text inside either scenario shape is never mutated |

Candidate A chosen: it is the only one of the two that can catch an implementation which gets the
*receipt* entry's own actor or state wrong, which is the entry the two-write design most needs
protected, and it does not restate ground Rule 1 already covers. The relational blockers assertion
survives the restructuring and is stronger for it - the receipt row now asserts no blockers yet,
the determination row asserts the same ones the notice itself carries, and the swap between the
two rows is what proves the receipt entry is not merely a second copy of the determination one.

**`features/notice_intake.feature` now measures 22 mutants, 0 `literal`, 22 `example` - every
mutant in the file domain-reaching.** 8 / 10 / 4 by rule. Simulated survivors: 0 across all three
rules, evaluated against each rule as currently drafted - every mutant produces a mismatch against
a correct implementation, the same finding as the first draft, now also true of the rule that
previously had none to speak of.

**Rule 3 (the loss-date schema boundary) is untouched, byte-identical to `a5379c7`, and is not this
session's to amend.** Escalated back for a boundary decision: Fla. Stat. 627.70131(1)(a)'s
acknowledgment duty is triggered by receipt of a claim-related communication, not receipt of a
valid one, and a notice naming a carrier, a policy number, and a loss type with only the loss date
unparseable is plausibly such a communication - refusing it with nothing persisted may itself be
the exception to this feature's own two-write principle that its opening comment does not name as
one. An `ASSUMPTIONS.md` entry deciding the boundary is expected before this rule is touched again.

**A Background comment now explains why the claimant-name requirement never fires in this file.**
Every notice below reports `wind_hail`, a Section I property peril; the requirement applies only to
a Section II loss - an injury or a liability claim, where there is a specific person to name.
Stated as a domain fact, not by naming the function that enforces it, mirroring
`validation.feature`'s own convention of a Background comment explaining a configured value's
non-effect on the scenarios below it.

**The further-split trigger fired and was decided: declined.** What the trigger protects against is
approval scope being coarser than the judgments it records, a cost realized when a file accumulates
survivors - item 5a's 84 mutants, not this file's 22 with zero simulated survivors. Splitting would
duplicate a twelve-line Background across three files for no protective gain at today's size.
Reversal condition, recorded rather than left to be re-derived: revisit if this file passes roughly
40 mutants, or the moment any rule here accumulates a survivor - whichever comes first.

**Rule 3 is unblocked and amended, landed at `d768bdb` on `phase2/5c-notice-intake`, spec-only.**
`ASSUMPTIONS.md`'s "A refused submission is still a received communication" entry (added this
session, see below) settles the boundary the rule was waiting on. The outcome is now two columns,
`notice_outcome` and `record_outcome`, rather than one compound phrase - matching
`PHASE2_DESIGN.md`'s own status-code table wording for the same decision, "no notice created,
submission recorded," two clauses rather than one. No field, table, or column is named in the
scenario or its comment, per the instruction this amendment was given under. `features/notice_intake.feature`
re-measured after this and the audit-trail change below, not before: 24 mutants, 8 / 10 / 6 by rule,
all `example`-kind. Simulated survivors: 0 across all three rules, evaluated against each rule as
now drafted. Rule 3's own count rose from 4 to 6 (the outcome split alone: 2 to 4, plus the
unchanged `loss_date` swap); Rule 2's stayed at 10, its own addition below being deliberately
mutation-inert.

**Rule 2 gained one fixed assertion: the audit trail holds no entry beyond the two named.**
Generates no mutant - there is no sibling row where a third entry would be correct, so the engine
has nothing to swap it against - and is kept anyway as a domain fact worth stating even where
mutation cannot check it, per instruction.

**Constraint on 5c's implementation, recorded here rather than in the spec, since it decides
nothing about behavior and everything about whether a mutant stays real.** Rule 2's `identity`
column carries the same value on both rows (`no verified identity`, correctly - phase 2
authenticates nothing), so both of its mutants are marker substitutions rather than row swaps. The
placeholder is unquoted in the step (`Then that entry carries <identity>`), so the marker lands
*inside* the captured value and the mutated line still binds - but only if the eventual step
pattern captures to end of line. A quoted-literal or alternation-restricted pattern (matching only
`"no verified identity"` or one of a fixed set of phrases) would make both of these mutants vacuous
at step resolution instead, the same failure mode `docs/harness-findings.md` already documents for
quoted literals in plain scenarios. This is the one place in this file where step-definition style,
not spec content, decides whether a real mutant stays real - worth flagging to whoever writes the
step for this file.

**Two documents corrected together, `ASSUMPTIONS.md` and `PHASE2_DESIGN.md`, landed on `main` at
`ece1427`** (originally committed to the wrong branch by mistake as `b281d67` on
`phase2/5c-notice-intake`, caught before either was pushed, and cherry-picked onto `main` instead of
force-correcting branch history - recorded here because the mistake happened and the fix should be
traceable, not because it changed anything about the content). `ASSUMPTIONS.md` gains "A refused
submission is still a received communication": Fla. Stat. 627.70131(1)(a)'s acknowledgment duty
triggers on receipt of a communication, not receipt of a well-formed one, verified against the
Legislature's text 2026-08-23; a refused submission persists its raw payload record, verbatim and
hash-referenced, with a receipt timestamp - no notice identifier, no state, no audit entry, nothing
retrievable through the notice endpoints; the 400 response carries the payload hash as an intake
reference. Retention for these unreferenced payload records is named as item 5g's problem, not
solved here. `PHASE2_DESIGN.md`'s status-code table entry for the schema-invalid case corrected
from "nothing persisted," which this decision supersedes, to "no notice created, submission
recorded."


**`gauntlet spec approve` landed on `features/notice_intake.feature` before any step definition
existed, and the acceptance gate's mutation stage cannot tell the difference between that and a
locked, tested spec — it just runs the whole suite and asks whether it still passes.** Nothing in
this project binds the file to a test module. `gauntlet.gates.acceptance._survivors` mutates the
spec in place and demands `run_acceptance` over the whole steps directory fail; if no `scenarios()`
call collects this file, the run is unaffected by the mutation and every mutant it tries scores as
surviving. `survivors_for`'s own docstring says "the bound scenarios" — the concept is named in the
code and enforced nowhere. The tell: `tests` stayed 274/274 passing and code mutation 330 killed,
both figures identical to `main` before this item existed. A spec's own scenario count never
entered either total.

**The gate reported 24 surviving mutants against the pre-amendment draft. All 24 were vacuous —
binding artifacts, not real survivors — and none is to be approved.** `gauntlet mutant approve`
would stamp 24 judgments that were never made, over a rule this item's own comments call the one
carrying the most statutory weight in the file. A future session reading the survivor count alone,
without this entry, would have every reason to try.

**The acceptance gate took 423.622s scoring that state — a project maximum, above the 260.3s on
record and above the 300s timeout floor `docs/harness-findings.md` currently advises.** Corrected
there too, in the same section, with the cause named so the figure is not read as ordinary growth:
24 full-suite runs, one per vacuous mutant, not a bigger suite taking proportionally longer.

**The spec is amended, landed at `edb5abd` on `phase2/5c-notice-intake`, spec-only, still
unapproved — moving the digest is what returns the gate to its cheap approval-stage failure.** Five
changes: the Background states the jurisdiction's timezone and the notice's actual submission
instant directly rather than an opaque "today"; Rule 1 gains a response column (both rows `201`,
per `PHASE2_DESIGN.md`'s own reasoning for the two identical status codes); Rule 2's scenario title
is corrected — exactly one rule in this file's fixture finds a blocker, not none, and the old title
was false about its own data; Rule 3's titles read "created," not "received," matching cells that
already did, and gains a response column (`201`/`400`); a new Rule 4 proves the shell actually
calls `jurisdiction_date.feature`'s conversion with a timezone-aware instant and a
caller-supplied timezone rather than assuming either — the defense item 5c inherited from item 5b,
per `ASSUMPTIONS.md`'s "An instant that is not a timezone-aware UTC instant is out of scope for
item 5b." Rule 4's two scenarios are split rather than combined into one three-row table: measured
directly against the engine and confirmed by full hand-simulation before either shape was written
to disk, the combined shape carries exactly 2 real survivors — a zone swap and an instant swap can
each borrow the other axis's row to stay `PENDED`, since Chicago's local date for any UTC instant
is never ahead of New York's — while the split shape has 0, because neither scenario's own table
has the other axis's column to supply the borrowed row.

**Re-measured after the last amendment: 40 mutants, 10 / 10 / 8 / 6 / 6 by scenario, all
`example`-kind, zero overlap with the pre-amendment draft's 24 locators** (compared directly,
not assumed from the rewrite). All 40 hand-simulated against a correct implementation: 0 survivors,
across every scenario in the file.

**Correction to record: the response column does not produce a `_gauntlet` marker.** Predicted
as a marker substitution before this was measured; `201` and `400` are parsed as numbers, and the
engine's numeric rule increments them at matching precision — the real mutants are `201`→`202` and
`400`→`401`, both real, both killed by the design's own two-`201`s and one-`400` decisions.

**The further-split trigger this item recorded at `6ef20ff` — "revisit if this file passes roughly
40 mutants, or the moment any rule here accumulates a survivor" — is reached on the mutant-count
half by this amendment (40) and not on the survivor half: the 24 the gate reported were binding
artifacts, and the hand-simulated count is 0.** Consciously re-examined rather than left silently
unaddressed, and the decision is: still unsplit. What the original trigger protects against —
approval scope coarser than the judgments it records — is realized when a file accumulates
survivors needing separate equivalence arguments; that has not happened, and Rule 4 shares this
file's Background more thoroughly than the first three rules alone did, since it uses the same
jurisdiction-and-instant facts rather than an unrelated setup — splitting it out would duplicate
that Background rather than isolate an unrelated concern. Revised reversal condition, since the old
one's mutant-count half is now behind: revisit if this file passes roughly 60 mutants, or the
moment a mutant survives that still needs a human equivalence judgment once step definitions exist
and actually bind the file — a real survivor, not a gate artifact of the kind this session found.

**Two new queue items, 5h and 5i, added above after 5g** — an absent loss date reaching `TRIAGED`
with no presence check anywhere in `validate()`, and the missing status-code row for a carrier this
deployment's identity reference recognizes but cannot configure. Both found while drafting this
item; neither is this item's to build. See `ASSUMPTIONS.md` for both resolutions, ratified
2026-08-24, along with the settled placement of item 5c's `400` on an unknown or malformed
`carrier_code` — the identity reference, not item 5a's rules source, closing an escalation this
drafting session raised that turned out to be decidable from documents already in hand.

**Two more surgical fixes, both structurally inert to mutation, landed at `0d955af`.** Rule 4's two
unquoted Examples placeholders originated in the advisor's own prompt text for that rule and were
propagated faithfully rather than caught against Rule 1's and Rule 3's already-quoted convention;
the Feature-level comment naming `validate()` survived two advisor review rounds unflagged — the
same defect class item 4f cost its own queue item over, once that spec was already locked. Both
caught at the pre-lock review of the exported file, not by any gate. Re-measured against `edb5abd`:
40 mutants, every locator and every signature byte-identical, both as multisets and pairwise.

**A third advisor miss was found and closed at the pre-lock export review, not by any gate: the
item's own 400 on an unknown or malformed `carrier_code` still had no scenario.** It was flagged in
the first advisor review of the draft — the disputed-reference finding, above — but only as an open
question of which reference file the check validates against, not as a missing scenario, and it was
dropped again from both amendment prompts that followed (`bce47a6`, `edb5abd`), each of which fixed
other things and never added it. This is the third advisor miss recorded against item 5c, after the
two already recorded at `0d955af` (Rule 4's unquoted placeholders, the dead-`validate()` comment
surviving two review rounds), and is recorded as such.

**Closed by adding `Rule: A notice is accepted only from a carrier this deployment administers`,
between Rule 3 and Rule 4** — a two-row Scenario Outline (`AAAA`/201/kept, `ZZZZ`/400/not kept) that
introduces no new step vocabulary: it reuses the Background's `the notice is submitted by carrier`
step and Rule 3's `intake <notice_outcome>` and `a record of the submission <record_outcome>` steps
verbatim. A malformed code gets no third row — it is definitionally absent from the identity
reference, the same boundary as `ZZZZ`, and a third row would be same-outcome with `ZZZZ` and
equivalent under swap. Measured directly against `gauntlet.acceptance.mutation.mutants()` and
compared to `0d955af`: 48 mutants, the existing 40 byte-identical (locator, kind, original, and
mutated value all compared, not locator alone), 8 new, all `example`-kind. Hand-simulated against a
correct implementation: 0 survivors among the 8 — every substitution flips an outcome, matching this
session's own prediction with nothing to reconcile.

`features/notice_intake.feature` now specifies everything item 5c's own queue entry above says it
owns — schema validity and the two-write receipt, the loss-date schema boundary, the
jurisdiction-instant wiring, and now the carrier-identity 400, with 5a's reference file it validates
against settled and cited by name. Still unapproved; file count against the revisit threshold
recorded at `edb5abd` ("revisit if this file passes roughly 60 mutants, or the moment a mutant
survives that still needs a human equivalence judgment"): 48 of ~60.

**`features/notice_intake.feature` is approved at `59b58a4`** (commit `9ebaeb6`, human action) and
**item 5c's implementation is built on `phase2/5c-notice-intake`, `gauntlet check` green: 296/296
tests, coverage 100%/100%, code mutation 100%/342 killed, acceptance 7 spec(s)/69
reviewed-equivalent — 0 new approvals, all 48 of this file's mutants killed.** Not yet merged to
`main`; left for the human's review given the item's size and statutory weight, per this session's
own instruction to report refs pushed rather than to close the item out.

**What was built, and where.** `src/claimgate/domain/carrier_identity.py` (new): the identity
reference `PHASE2_DESIGN.md`'s carrier-reference section describes — `CARRIER_IDENTITY_REFERENCE`
(`AAAA`/`BBBB`/`CCCC`, matching that section's synthetic table verbatim) and
`resolve_carrier_identity()`, settling this file's own escalation from the first draft (identity
reference, not the rules source) in code, not just in `ASSUMPTIONS.md`. `CarrierIdentity` and
`CarrierIdentityResult` added to `domain/models.py`, same convention as `CarrierConfigurationResult`.
A new `src/claimgate/shell/` package — the "phase-2 API shell" `ASSUMPTIONS.md` and
`PHASE2_DESIGN.md` name repeatedly but that nothing had built yet: `store.py` (`NoticeStore`, an
in-memory repository — phase 2 names no database technology outside item 5d's idempotency
constraint, which isn't built) and `notice_intake.py` (`submit_notice`, `get_notice`). The
identity check runs first, ahead of the loss-date schema check, ahead of the receipt write, matching
the new Rule's own comment; a loss date that fails to parse persists a hashed payload record via
`NoticeStore.refuse_payload` and creates no notice; a recognized carrier and a parseable date reach
`NoticeStore.receive_notice` (the durable `RECEIVED` write, before any domain rule runs) and then
`record_decision` (`TRIAGED`/`PENDED`, `SYSTEM` actor). Test-side: `tests/api/notice_intake.py` (thin
passthrough), `tests/acceptance/test_notice_intake_acceptance.py` (all four Rules' step definitions,
12 scenario examples), `tests/unit/test_carrier_identity.py` (3 tests, domain-scoped), and
`tests/shell/test_notice_intake.py` (7 tests covering what no scenario reaches — see below and
`docs/harness-findings.md`'s new entry on why this file is not under `tests/unit/`).

**Item 5h is deliberately preserved, not fixed here, per this session's own instruction.** The
request schema does not require `loss_date`; an absent value flows to `Candidate.loss_date` unchanged
as `date.min`, reaching `TRIAGED` carrying `0001-01-01` as today's date exactly as `ASSUMPTIONS.md`'s
"An absent loss date is a domain blocker, not a schema refusal" describes. Requiring the field at the
schema boundary would have silently decided that reopening the opposite way. Asserted directly by
`test_an_absent_loss_date_flows_through_unchanged_item_5h_is_not_built_here`, so the preservation is
verifiable, not just claimed.

**Items 5g and 5i are not built; both raise rather than invent a status code, and both raises are
unit-tested rather than left silently unreachable.** A carrier the identity reference recognizes
whose rules entry cannot be resolved (`_resolve_rules`), and a `jurisdiction_timezone` this item
receives but cannot resolve (`_resolve_today`), each raise `NotImplementedError` naming the queue item
that owns the decision. No scenario in `features/notice_intake.feature` reaches either path.
`jurisdiction_timezone` itself is received as a plain caller-supplied parameter, not derived from a
map or `property_state` — item 5g's map-keyed generalization and swappability proofs are untouched.
Items 5d (idempotency), 5e (the resolution endpoint), and 5f (SIU) have no code anywhere in this
branch.

**One design decision flagged as following from the code and the vocabulary already in place, not
from an independent reading of a document that decides it:** the identity reference is a baked-in
domain constant, not a parameter threaded through `submit_notice` the way the six carrier-rules
values are. `PHASE2_DESIGN.md` calls the reference "a static, version-controlled file," structurally
different from the six values `ASSUMPTIONS.md` calls "caller-supplied configuration with no
default," and `RECOGNIZED_LOSS_TYPES`/`RECOGNIZED_NOTICE_TYPES` are the same shape already, baked
into `validation.py`. Item 5g's carrier-set swap proof will need the reference to be swappable at
the shell boundary; that plumbing is left for 5g to add rather than built ahead of need here.

**One harness finding recorded in `docs/harness-findings.md`, found while getting the mutation gate
green:** `[tool.mutmut]`'s `source_paths` (`domain/` only) and its `tests/unit/` test selection
disagree, and a new `tests/unit/` file importing outside `claimgate.domain` breaks mutmut's
collection for the whole run with an unhelpful captured error. Moved this item's shell-layer unit
tests to `tests/shell/` instead; `gauntlet`'s own `tests`/`coverage` gates are unaffected by the
directory name.

**Close-out review found one gap: the accepted path never persisted the raw payload.** A green
`gauntlet check` could not see it, because every scenario in `features/notice_intake.feature` that
reaches an accepted notice asserts the notice and its state, never the payload record — the gap is
against a design decision (`PHASE2_DESIGN.md`'s audit log section, "the raw inbound payload is
stored once, verbatim, immutable, and referenced by hash," cited to 627.70131(4)(b)) that no
scenario describes at all, so the gate's green run and 0-survivor mutation score were both correct
about what they checked and silent about what they didn't. Found by tracing the spec's own Rule
comments against `PHASE2_DESIGN.md`'s text and then against the code, not by any gate. **The
implementing session's own "judgment calls flagged" list named the payload-reference hash recipe as
a choice worth recording, and missed that the accepted path never called it at all** — the list
caught the "how" of a decision it never noticed the "whether" of.

**Fixed**: `NoticeStore.receive_notice` now persists a `PayloadRecord` (same `_hash_payload` recipe
`refuse_payload` uses, extracted to remove the duplication) linked to the notice via
`PayloadRecord.notice_id`, in the same call that writes the `RECEIVED` `NoticeRecord` and its audit
entry — before `_apply_domain_rules` runs, matching the receipt-before-any-rule ordering the rest of
this item already holds to. `submit_notice` builds the raw payload dict once and threads it through
both the refusal and acceptance paths, so the two persist by the identical recipe rather than two
implementations that could drift. Asserted by a new unit test,
`test_the_accepted_path_persists_the_raw_payload_linked_to_the_notice`, the same way the item 5h
preservation is asserted — proving the fix rather than only claiming it. `ASSUMPTIONS.md` gains "The
payload reference recipe" recording the hash recipe itself as a decision (SHA-256, JSON,
`sort_keys=True`, `default=str`) and flagging that it will need revisiting once a literal HTTP layer
exists and "verbatim" can mean raw request bytes rather than a shell-parsed field mapping.
`docs/harness-findings.md` gains two entries found while re-verifying: a mutant killed by a step
definition's own parse error (three of `notice_intake.feature`'s 48 marker mutants, all on empty
blockers cells) is scored identically to one killed by a real assertion, and the acceptance gate's
wall-time maximum moved again, to 472.803s, this time from ordinary growth rather than the
unbound-spec defect the prior maximum recorded.

**Item 5c is closed.** Spec approved at `59b58a4` (commit `9ebaeb6`), implementation and this fix
both on `phase2/5c-notice-intake`, `gauntlet check` green with the spec's digest unchanged
throughout (re-verified before this fix's own gate run, not assumed). Items 5d (idempotency), 5e
(the resolution endpoint), 5f (SIU), 5g (jurisdiction-map generalization), and 5h (the absent-loss-
date presence check) remain open, each its own queue item, none built or fixed here.

**Item 5c is merged to `main`** (merge commit `afb35a0`). Confirmed by `git log --oneline -1` on
`main` at the start of this session, not assumed from the prior entry. This record landed on the
item branch rather than on `main`, contrary to the documentation-lands-on-main convention; carried
forward at 5d's merge rather than unpicked, as item 4a did.

**Item 5d's prep decisions are recorded, drafting-session work only, on branch
`phase2/5d-idempotency` off `main`, three commits pushed.** Persistence engine (SQLite via the
stdlib `sqlite3` module, STRICT tables, schema-declared constraints) and one receipt clock
(`submitted_at`, not `now()`, for every receipt-adjacent timestamp) are both advisor-recommended,
human-ratified 2026-08-24 — see `ASSUMPTIONS.md`'s "Open decisions" and "Carried requirements"
sections and `PHASE2_DESIGN.md`'s new "Persistence engine" section. Neither is built yet; both are
flagged for item 5d's own implementing session, which ports `store.py` to SQLite regardless. The
size gate's zero headroom on `receive_notice` (25 of 25 lines) is noted in this item's own entry
above so that port doesn't discover it mid-change. Separately, `docs/harness-findings.md`'s
"Command ownership" entry is corrected: `registry.describe` branches three ways by spec status
(`MODIFIED`, `MISSING`, not-approved), not one code path as previously claimed — verified against
`src/gauntlet/registry.py` in the gauntlet repo itself. The operational advice (the acceptance
gate's remedy names the wrong command) is unchanged; only the mechanism claim is corrected.

**Item 5d's first draft landed, spec-only, on the same branch.** `features/idempotency.feature`:
three rules — a replay within its 24-hour window returns the original notice, response, and
receipt timestamp, and adds nothing to its audit trail; a replay past that window creates a fresh
notice, exactly as a first-ever submission would; the same key from two different carriers is not
a collision; a submission that omits the key it used the first time is never treated as a replay.
Measured directly against `gauntlet.acceptance.mutation.mutants()`: 20 mutants, 8 / 6 / 6 by rule,
all `example`-kind, zero `literal`. `features/notice_intake.feature` re-measured alongside it and
confirmed unchanged: 48 mutants, 48 unique locators, untouched by this branch.

**One redesign, caught by simulation before the draft was written to disk, not after.** The third
rule's first attempt varied both the original and the replay submission's key together over an
`absent`/`absent` row alongside a `K-300`/`K-300` row. Hand-simulated: 2 survivors, both on the
`absent` row — once either call's key is absent, the other call's key value stops mattering to the
outcome, so a mutant swapping either column in that row left the actual result unchanged, the same
symmetric-blank-row shape item 5a's refusal outline found. Fixed by holding the original
submission's key constant (a `Given`, not a column) and varying only the replay's key across the
two rows; re-measured at 6 mutants for that rule (down from 8, since one column was removed), 0
simulated survivors. **Hand-simulated total: 0 survivors across all 20 mutants, in all three
rules**, evaluated against each rule as currently drafted.

**One gap is named in the file and escalated here rather than drafted.** `PHASE2_DESIGN.md`'s
status-code table lists a fourth idempotency outcome — "idempotency key reused with a different
payload" → `409`, distinct from an ordinary replay's `200` — that its Idempotency section never
explains how to detect: whether by comparing the submitted content against what the key already
has on file, and if so by what rule. Nothing this session read decides that comparison, and
drafting a scenario for it would mean inventing one, which is exactly what `CLAUDE.md`'s standing
constraint against defaulting a status code forbids. Every scenario in this draft resubmits the
Background's own notice content unchanged for that reason; the `409` case is not built. *Resolved
2026-08-24: comparison by payload reference, decided and ratified — `ASSUMPTIONS.md`, "Idempotency:
what a repeated key is compared against"; the 409 rule is now drafted.*

**Not decided by this session, deliberately:** the exact-24-hour tie (whether a replay landing at
precisely `submitted_at + 24h` counts as within the window or past it). Both boundary rows sit a
full minute either side of the mark rather than on it, so the tie is untested rather than guessed.
*Resolved 2026-08-24: half-open, expired at equality; a row at exactly 24 hours is now in the
table.*

**`gauntlet check` is expected to report one unapproved spec on this branch** — the guaranteed
state between a spec draft and its approval, not a defect (`docs/harness-findings.md`, "Command
ownership"). Not run this session beyond `gauntlet spec list`, which confirms no other spec's state
has drifted. **The next action is a human review and `gauntlet spec approve`, not an agent
action** — per this session's own instruction, no implementation, no approval, and no `gauntlet`
command beyond `spec list` were run.

**Item 5d's spec is amended at `8926c7e`, spec-only plus documentation, pushed.** Three rules
added and two escalations closed by ratified decision (`ASSUMPTIONS.md`, "Idempotency: what a
repeated key is compared against"): the `409` conflict, decided by payload reference; the
exact-24-hour tie, decided half-open with a row now on the boundary; a replay reports the state the
notice is in (a `PENDED` original replays as `PENDED`); and a key is remembered only by the notice
it created (a key first used on a schema-refused submission does not block the corrected
resubmission). Rule 1's two fixed `Then`s now name the original notice — the previous phrasing
was ambiguous in the 201 row, where 5c's existing step definitions would have inspected the new
notice and proven nothing about the replay. Measured directly against the engine after the
amendment: 40 mutants, 12 / 6 / 6 / 4 / 6 / 6 by rule, all `example`, all 20 locators from
`9851478` preserved unchanged, so the comment and fixed-step rewrites are inert by locator
identity. Advisor's simulation, recorded as a simulation: 0 survivors of 40. Two step-definition
notes for the implementing session: "that submission is remembered as the original" must
tolerate a 400 response with no notice identifier, and "identifies a new notice, not the
original" must hold when there was no original notice. Next action is the human's: export at
this ref, review, `gauntlet spec approve` at the start of the implementing session.

**Item 5d is implemented and green on `phase2/5d-idempotency`, spec unchanged throughout.**
`features/idempotency.feature` was approved by the human at `b08b416` (digest
`sha256:f741ae2a6536`), re-confirmed against `gauntlet.lock.json` before any code was written and
unchanged at the end. `gauntlet check` passes: **327/327 tests** (297 before; +13 acceptance
scenarios, +17 shell unit tests), **coverage 100/100**, **code mutation 342 killed at 100%**
(unmoved, as expected — `[tool.mutmut] source_paths` is `src/claimgate/domain/` and nothing in the
domain changed), duplication 0, worst function 22 of 25 lines, largest module 246 of 250, and
acceptance **8 specs, 69 reviewed-equivalent** — the same 69 approvals the branch started with, so **all 40 of
`idempotency.feature`'s mutants were killed and no new approval was created**. Mutant count
re-measured directly against `gauntlet.acceptance.mutation.mutants()` at the implementing ref: 40,
12/6/6/4/6/6 by rule, all `example`, matching the amendment session's figures exactly;
`notice_intake.feature` re-measured at 48, unchanged. The advisor's simulation of 0 survivors held.

Four commits, in the order the log should read them: the SQLite port with the receipt clock
(`1952dc0`), the shared-step move the duplication gate forced (`d60fcdd`), idempotency itself
(`f740495`), and the transaction-boundary correction judgment-call 4 below records. **The port and
the receipt clock are deliberately one commit, not two** —
`ASSUMPTIONS.md`'s own "One receipt clock, not two" says to build the clock fix "during item 5d's
port of the store to SQLite, since that port rewrites `receive_notice` and its callers anyway," so
separating them would invent a boundary the ratified decision says is not there.

**What was built.** `src/claimgate/shell/` is now six modules rather than two: `schema.py` (the DDL
and the append-only triggers), `records.py` (the persisted shapes and the payload-reference recipe),
`store.py` (SQLite), `messages.py` (what crosses the boundary), `idempotency.py` (the repeated-key
rules), `notice_intake.py` (the order they run in). Four STRICT tables — notices, audit entries,
payload records, idempotency keys — with `UNIQUE(carrier_code, idempotency_key)` on the key table,
foreign keys to the notice from the other three, and `BEFORE UPDATE`/`BEFORE DELETE` triggers that
`RAISE(ABORT)` on the audit and payload tables, so `PHASE2_DESIGN.md`'s "no update path and no
delete path exist in this schema" is refused by the database rather than merely not offered. The
database path is a constructor argument with no default; tests pass `":memory:"`. A created
notice is two `BEGIN IMMEDIATE` transactions — receipt, then decision, with rule evaluation between
them and inside neither (judgment call 4); a refusal, a conflict and a replay are one each.
`datetime.now` is called **0 times** anywhere under
`src/claimgate/shell/` (counted, not assumed): the notice's receipt, both audit entries and the
payload record are all `submitted_at`, and `received_at` is now readable on `NoticeRecord` and on
`SubmitNoticeResponse` for `201` and `200` alike, which is what lets a replay report a timestamp at
all.

**Judgment calls, flagged rather than buried.**

1. **The decision-4 correction, made before implementation, not discovered by it.**
   `ASSUMPTIONS.md` decision 4 said the uniqueness constraint lives on the notice table. It cannot:
   Rule 1's third row requires a second notice under the same `(carrier_code, idempotency_key)`
   once the first has expired, which a `UNIQUE` there forbids. The key record is its own table, one
   row per pair, written inside the notice-creating transaction and replaced — not duplicated —
   when an expired key is reused. Annotated in place in `ASSUMPTIONS.md`; the decision's substance
   (a refused submission writes no key row and blocks nothing) is unchanged and is asserted by a
   unit test.
2. **`carrier_code` on audit entries** — `PHASE2_DESIGN.md`'s "Carrier reference" requires it
   persisted on every audit entry and its own audit-log entry-schema table omits it. Column and
   field added, attribution only, never branched on; the entry-schema table gains a dated row-note.
   Found by tracing design to code, which no gate can do.
3. **`payload_records.arrival_index` exists now, for item 5e.** Position 0 is the payload the
   notice was created from; 5e appends resolution payloads after it. `UNIQUE(notice_id,
   arrival_index)` keeps the sequence from acquiring two occupants of one position, and SQLite's
   distinct-NULL rule exempts the unlinked refusal records, which have no sequence.
4. **The one-transaction rule narrows what the two-write receipt protects against, and this
   follows from the instruction rather than from a document.** `PHASE2_DESIGN.md` justifies writing
   `RECEIVED` before any rule runs so that "a bug in rule evaluation must never be able to erase or
   delay the fact that a notice was received." Inside one transaction, a raise between the receipt
   and the decision rolls the receipt back too. No such path is reachable today — both raising
   helpers run before the receipt — and atomicity is the stronger guarantee for the failure that
   does exist, a receipt stranded with no decision. Recorded in `store.py`'s docstring for whoever
   adds a raise between those two writes.
   *Resolved 2026-08-25, before merge: the advisor instruction was wrong against the design and
   is reversed. "No such path is reachable" was wrong too — `_apply_domain_rules` runs between
   `receive_notice` and `record_decision`, and the guarantee `PHASE2_DESIGN.md` states is
   against **bugs** in that evaluation, not against the two known raises that happen to run
   earlier. A created notice is now two transactions: the receipt (payload record, notice at
   `RECEIVED`, its audit entry, and the key row) commits first, rule evaluation runs outside
   both, and the decision commits second. A raise in evaluation now leaves the notice at
   `RECEIVED` with its key remembered, so the client's retry replays it with `200` and state
   `RECEIVED` instead of creating a duplicate. Proven by
   `test_a_bug_in_rule_evaluation_cannot_erase_the_receipt` and
   `test_a_notice_stranded_at_received_replays_as_received` under `tests/shell/`; refusals,
   conflicts and replays stay single-transaction, and the `IMMEDIATE` lock still serializes the
   idempotency lookup with the insert that follows it. `PHASE2_DESIGN.md`'s two-write paragraph
   now names the boundary rather than leaving it to be inferred.*
5. **The shared-step move follows from the duplication gate, not from a preference.**
   *Corrected 2026-08-24: the duplication gate does not scan `tests/` — see the correction under the
   5d merge record below. The move stands as design, not as gate compliance.*
   `idempotency.feature` restates `notice_intake.feature`'s Background verbatim and both specs are
   locked, so neither rewording nor copying was available; `max_duplicate_blocks = 0` at six lines
   left `tests/acceptance/conftest.py` as the only place the definitions could go. Verified
   empirically before relying on it: a module's own step definition overrides one of the same text
   in `conftest.py`, which is what keeps `test_carrier_configuration_acceptance.py`'s identically
   worded carrier-rules steps pointed at its own vocabulary.
6. **The concurrency path is unreachable in this deployment and is built and proven anyway.**
   `BEGIN IMMEDIATE` takes the write lock before the key lookup, so with one process and one
   database no writer can commit between the lookup and the insert. The constraint and its
   resolution are `PHASE2_DESIGN.md`'s mandated mechanism, so both exist: `remember_key` is a plain
   `INSERT` (an upsert would silence the constraint), and losing to it rolls the submission back
   whole and re-reads the key to answer as a replay. `tests/shell/` proves the constraint fires by
   asserting the raised error's `__cause__` is `sqlite3.IntegrityError` — the database refusing,
   not Python — and stages the resolution by making the lookup miss a key that is already
   remembered.

**Shell unit tests carry more weight here than usual, and that is why they exist.**
`docs/harness-findings.md` records that mutmut's `source_paths` is `src/claimgate/domain/`, so code
mutation reaches no shell code at all; for `src/claimgate/shell/` the acceptance suite and
`tests/shell/` are the whole of the protection. They cover what no scenario reaches: the constraint
firing, the four triggers refusing `UPDATE` and `DELETE`, a notice's own row still being allowed to
move state, no key row after a `400`, an expired key row replaced by the notice that reused it, the
`409`'s payload record and its reference, the half-open boundary at one-second resolution rather
than the spec's one-minute rows, the single receipt clock, `carrier_code` on every audit entry, and
— since the transaction correction — that a bug in rule evaluation leaves the notice standing at
`RECEIVED` with its key remembered and that a replay of it reports `RECEIVED`.

**Scope walls held.** No HTTP layer. Items 5e, 5f, 5g, 5h, 5i untouched; both `NotImplementedError`
raises stay and stay tested; no SIU table, no field named `tolling`, and no persistence for anything
outside this item's four tables. Item 5e's carried requirement — that a replay of a notice moved
`PENDED → TRIAGED` reports `TRIAGED` — is still 5e's; Rule 4 here proves only the half that is
reachable, that a `PENDED` original replays as `PENDED`.

**Next action is the human's: review and merge to `main`.** Nothing about this item is waiting on an
agent, and no `gauntlet` command from the human's list was run.

**Item 5d is merged to `main`** (merge commit `8f3c19e`, `--no-ff`, 22 files, +2071/−425), 2026-08-24.
Branch `phase2/5d-idempotency` ends at `e761d24`. This record lands on `main` directly, per the
documentation-lands-on-main convention the 5c record missed. Gate at merge: 327/327, coverage
100/100, code mutation 342 killed / 100%, acceptance 8 specs, 69 reviewed-equivalent, no survivors,
no new approvals; size worst function 22/25, largest module `notice_intake.py` 246/250 — item 5e
should put the resolution endpoint in its own module rather than add to that one.

**Correction, 2026-08-24, advisor's own claim.** Item 5d's judgment call 5 and the harness-findings
entry it cites say the duplication gate forced the shared-step move into `tests/acceptance/conftest.py`.
It did not. Read from `gates/base.py` in the agent-gauntlet repo: `tool_targets()` hands external
tools the `src` tree only, and `python_files()` filters even `--changed` runs to `src`, so `static`,
`size`, `complexity` and `duplication` never analyze anything under `tests/`. The advisor asserted
the coverage from `gauntlet.toml`'s `tests = "tests/"` key rather than from source; the agent
repeated it. The move stands on design grounds — two locked specs sharing a Background should
share one definition per phrase — but no gate would have refused the alternative, and none will
catch a future duplicated step module. Recorded in `gauntlet-findings.md` as a proposed change.

**Item 5e's prep decisions are recorded, drafting-session work only, on branch `phase2/5e-resolution`
off `main`.** Five points `PHASE2_DESIGN.md` leaves open are escalated in `ASSUMPTIONS.md`'s "Open
decisions" rather than defaulted, and no scenario is drafted against any of them: what a resolution
payload may contain ("the supplemental field values" is never given a set); what a resolution is
evaluated against, both which rules run and which calendar date they run on; what happens to the
payload of a resolution that is not applied, which the item's own required payload-sequence scenario
turns on; whether `actor_type` is a caller input at all, and what status a refused actor or an
absent `actor_id` gets, neither of which the closed status-code table has a row for; and whether the
`409` for "not currently `PENDED`" covers a notice standing at `RECEIVED`, a state item 5d's
two-transaction receipt made observable after that row was written. Three of the five would widen a
table `PHASE2_DESIGN.md` calls closed, which is the human's call. Separately, `ASSUMPTIONS.md`'s "One
receipt clock" entry gains a dated extension to the resolution path — every timestamp this endpoint
writes is the caller-supplied instant for that call, and the notice's receipt instant is untouched by
a resolution — stated by the instruction that opened this item, not inferred here. Recorded as read
rather than escalated: this endpoint has no idempotency key, so a network retry of a resolution that
already succeeded is answered by the `409` row above.

**Item 5e's first draft landed, spec-only, on the same branch.** `features/resolution.feature`, five
rules: a resolution is acted on only while the notice is still pended (`200` against a `409` on a
notice already `TRIAGED`, with the trail proving the `409` wrote nothing); the notice moves only when
the resolution clears every blocker, and either way the attempt is audited (`200`/`APPLIED` against
`422`/`REFUSED`, the notice staying `PENDED` on the refusal); what a reviewer supplies is added in
arrival order and never written over what is already there (the first record still reports the policy
number absent after a resolution supplied one); a replay of the original submission reports `TRIAGED`
after an applied resolution and `PENDED` after a refused one — item 5d's carried requirement, and the
half `idempotency.feature` could not reach; and a resolution is recorded at the instant its caller
gave it while the notice's pend instant is untouched. **Measured** directly against
`gauntlet.acceptance.mutation.mutants()`: **40 mutants, 10 / 14 / 6 / 4 / 6 by rule, all `example`
kind, zero `literal`.** `idempotency.feature` and `notice_intake.feature` re-measured alongside it at
**40** and **48**, unchanged by this branch. **Simulated**, and recorded as a simulation rather than a
measurement: **0 survivors of 40**, each mutant walked individually against the rule it belongs to.

**Every scenario is written to sit inside the intersection of the five open points, so none of them
has to be decided before the spec can be locked.** Every resolution supplies only fields the notice's
own blockers name; no row introduces a blocker the notice did not already have, and none is pended
for `LOSS_DATE_IN_FUTURE`, so re-checking only the recorded blockers and re-running the whole
validation agree on every row; only an applied resolution's payload record is asserted; every audited
attempt is a reviewer's, so every one is `USER`; and the `409` row is a `TRIAGED` notice, never a
`RECEIVED` one. The file names all five in its own header comment rather than leaving the omissions to
be inferred from what is absent.

**One shape decision worth the human's eye, taken against `notice_intake.feature`'s precedent
deliberately.** Rule 2 asserts the audit entry's blockers as a literal set rather than relationally
against the notice's, which is the opposite of what that file's Rule 2 chose. Hand-simulated before
the file was written to disk: here the entry and the notice carry the same set on both rows, so "the
same ones the notice still carries" is true on the applied row as well and its own mutant survives.
Two literal columns are redundant on their face and are kept anyway — an implementation that gets the
`422` body right and the audit entry wrong, or the reverse, is caught by exactly one of them.

**Two step-definition notes for the implementing session.** `the notice's state is <state>` is used in
Rule 1 as both a precondition and an assertion, so it needs `@given` and `@then` on one function — the
same stacking `docs/harness-findings.md` records for `@given`/`@when`, one position further along.
And `the <ordinal> record kept for the notice ...` appears in two `Then` steps of Rule 3, so a mutant
on the ordinal column moves both together; that is intended and is what makes the swap ask the wrong
record for both its content and its origin at once.

**`gauntlet check` is expected to report one unapproved spec on this branch** — the guaranteed state
between a spec draft and its approval, not a defect. Not run this session beyond `gauntlet spec list`,
which confirms `features/resolution.feature` is the only unapproved spec and that no other spec's
state has drifted. **The next action is a human review and `gauntlet spec approve`, not an agent
action** — and, before that, the five escalated points, three of which would widen a status-code table
`PHASE2_DESIGN.md` calls closed. No implementation, no approval, and no `gauntlet` command beyond
`spec list` were run.

**Item 5e's five points are decided at `809e783` and the draft is amended in the commit that carries
this paragraph, spec-only, pushed to `phase2/5e-resolution`.** The amendment names no ref of its own
because a commit cannot carry its own hash and the spec and this record are deliberately one commit;
the stable identity, and the one to lock against, is `features/resolution.feature` at sha256
`2b014521a1bc`, 589 lines — export it with `git show <branch tip>:features/resolution.feature` and
check the digest before approving.
Advisor-recommended, human-ratified 2026-08-25; all five recorded in full in `ASSUMPTIONS.md`'s "Open
decisions" under the item 5e entry, which is the source for every line below. **1.** A resolution may
supply any notice-content field, not only the ones its blockers name — a field-level overlay in
arrival order, an omitted field keeping its prior value, and no way to blank a field in phase 2, only
to replace it. **2.** The full validation re-runs over the merged current view, on the jurisdiction
date of the resolution's own caller-supplied instant; a blocker the resolution introduces is not a new
outcome but simply among "the current blockers" the `422` reports, and an empty resolution (`actor_id`
only) is valid input. **3.** A refused resolution's data is kept, in sequence, and is part of the
current view — the release was refused, not the data — while the `409` persists nothing at all.
**4.** `actor_type` is not a caller input; the endpoint stamps `USER`, and a body with an absent or
blank `actor_id` is schema-invalid — the single row this adds to the closed status-code table, `400`,
nothing persisted. **5.** A `RECEIVED` notice gets the existing `409` whose body carries its current
state; no new row, and the scenario is carried to item 5i, annotated in that item's entry.

**One correction the ratification forced, recorded where the wrong claim was made.** The escalation
entry and the draft's own header both said this file decided none of the five. That was false for
point 3: Rule 2's refused row asserts the notice's blockers as `NOTICE_TYPE_UNRECOGNIZED:notice_type`
alone, which is true only if the refused resolution's policy number had already entered the current
view. The draft had decided point 3, in the direction since ratified, without saying so. Annotated in
`ASSUMPTIONS.md` under decision 3 and in the feature file's replacement header.

**Four rules added, two amended.** Added: a resolution with no reviewer behind it is refused before
anything is written (`400`, nothing persisted, against the identified reviewer's `200`); a reviewer
may correct a field the notice already had, not only supply one it was missing (an omitted loss type
keeping `standard`/`standard` against a supplied `fire` moving the notice to `high`/`complex` — the
accepted cost of decision 1, in the spec rather than only in the record of it, and since extended by a
third row that is decision 2(a)'s only real proof anywhere in the file: a reviewer who corrects the
peril to `injury` leaves the notice held for `claimant_name` and `incident_description`, fields nobody
supplied and the notice was never pended for, which only a full run of the whole validation over the
merged view can reach — every other refusal here is caught by validating the supplied field alone); a resolution is judged
on the calendar date it arrives, one minute either side of the boundary; and what a refused resolution
supplied is kept, in sequence, and counts toward what the notice says — three records for one
submission and two resolutions, the second clearing the pend only because the first attempt's policy
number is already part of the current view. Amended: Rule 1 gains a records column, so the `409`'s "no
state change, no audit entry" is a complete claim rather than half of one; Rule 2 gains a third row
where the resolution introduces a blocker the notice never had, which a blockers-only recheck would
have answered `200`.

**Measured** directly against `gauntlet.acceptance.mutation.mutants()`: **97 mutants, all `example`
kind, zero `literal`** — 12 / 10 / 24 / 18 / 8 / 6 / 9 / 4 / 6 in file order, up from 40 at the first
draft. Re-measured alongside: `idempotency.feature` **40**, `notice_intake.feature` **48**, both
unchanged by this branch. **Simulated**, and recorded as a simulation rather than a measurement:
**0 survivors of 97**, each substitution dumped from the engine and walked individually against the
rule its row belongs to rather than predicted from the table's shape. The 79 mutants outside the
corrected-field outline were shown byte-identical to the set already walked — same scenario, column,
original and substitution — rather than re-walked, and only that outline's 18 were simulated afresh.

**The arithmetic in the arrival-date rule was recomputed rather than carried over.** America/New_York
is UTC−4 in August 2026, so `2026-08-26T03:59Z` is 23:59 on the 25th there and `2026-08-26T04:00Z` is
00:00 on the 26th; against a loss date of `2026-08-26`, the first is still in the future and the
second is not. Verified against `zoneinfo` at the two instants plus the Background's own.

**Nineteen step phrases in this file have no definition yet, and two existing definitions need a
second keyword** — `the notice's state is <state>` and `the response is <response>` are both used in
`Given` position as well as `Then`, the same stacking `docs/harness-findings.md` records for
`@given`/`@when`. Two phrasings were changed during drafting to avoid shadowing: a records assertion
reading `the notice <phrase>` would have captured `the notice is submitted for intake`, and a second
`the <ordinal> record kept for the notice <phrase>` would have shadowed the first, so they are now
`the notice's records <phrase>` and `that record <phrase>`. **One requirement the implementing session
cannot get wrong without silently losing two mutants:** `the notice's blockers are <blockers>` must
assert the exact set, never containment — Rule 2's second and third rows are killed only because a
mutated row produces two blockers where one is asserted.

**`gauntlet check` still expects exactly one unapproved spec.** Not run this session beyond `gauntlet
spec list`. **The next action is the human's: review and lock.** No implementation, no approval, and
no `gauntlet` command from the human's list were run.

**Item 5e is implemented and green on `phase2/5e-resolution`, spec unchanged throughout.**
`features/resolution.feature` was approved by the human at `187244d` (blob sha256 `2b014521a1bc`,
589 lines), re-confirmed against the working tree after the acceptance run and unchanged at the end.
`gauntlet check` **passes**: **363/363 tests** (327 at the 5d merge; +21 acceptance scenarios, +15
shell unit tests), **coverage 100/100** line and branch, **code mutation 342 killed at 100%**
(unmoved, as expected - `[tool.mutmut] source_paths` is `src/claimgate/domain/` and nothing in the
domain changed), duplication 0, crap 5.0 of 15, boundary 11 step files with 0 direct imports, worst
function 23 of 25, largest module `store.py` 243 of 250, and acceptance **9 specs, 69
reviewed-equivalent** - the same 69 the branch started with, so **all 97 of `resolution.feature`'s
mutants were killed and no new approval was created**. No survivor, so no `mutant approve` was
run or needed. The acceptance gate took **759s**, up from the ~500s range 5d left it at; it is still
growing and still the only gate that costs anything. Mutant counts re-measured directly against
`gauntlet.acceptance.mutation.mutants()` at the implementing ref: `resolution.feature` **97**,
12/10/24/18/8/6/9/4/6 by rule, all `example`, zero `literal` - identical to the amendment session's
figures; `idempotency.feature` **40** and `notice_intake.feature` **48**, both unchanged. The
drafting session's simulation of 0 survivors of 97 held.

Five commits, in the order the log should read them: the two implementation decisions (`5bedbdf`),
the schema and the two extractions it forced (`295ff64`), the resolution path with its steps and
tests (`2702f7f`), the scope-wall citation fix (`6c64893`), and this paragraph.

**What was built.** `src/claimgate/shell/` is now nine modules rather than six: `resolution.py` is
the path itself, and `payloads.py` and `rules.py` are extractions the path forced rather than
preferred (judgment call 2). `notices` gains `pended_at` and `resolved_at`; `payload_records` gains
`content`. A resolution is one transaction after two checks that are deliberately outside it: the
reviewer's identity is checked first, before the notice is read at all, so a caller who has not said
who they are learns nothing about it; the state check is second and writes nothing, per decision 3.
Inside the transaction the reviewer's payload record joins the arrival sequence, the current view is
overlaid from that sequence field by field, the whole validation re-runs over it on the jurisdiction
date of the resolution's own instant, the notice's blockers are replaced by that whole result, and
one audit entry is written from `PENDED` to `TRIAGED` whether the outcome is `APPLIED` or `REFUSED`.
`datetime.now` is still called **0 times** anywhere under `src/claimgate/shell/`.

**Judgment calls, flagged rather than buried.**

1. **The schema needed a third column the instruction did not name, and this was found by reading
   the spec against the code rather than by any gate.** `payload_records` stored only the reference
   hash. Rules 6 and 7 assert what each record *reports for a policy number*, and decision 1's
   overlay derives the current view field by field - neither is computable from a hash.
   `PHASE2_DESIGN.md` says the payload is stored "once, **verbatim**, immutable, and referenced by
   hash"; item 5d stored the reference and not the verbatim half because nothing yet read it.
   `content` was added and flagged before it was written.
2. **Two extractions instead of a separate resolution store module.** The instruction offered either;
   the size gate decided. `payloads.py` owns the arrival sequence, which is the thing this item
   extends and which `store.py` had four lines of headroom for. `rules.py` owns the domain rules as
   the shell runs them, and that one is forced by decision 2(a) rather than by size: a resolution
   re-validates through *one* definition of "no blocker", the same one intake uses, and two copies
   of that call would let it stop being true with no gate noticing. `store.py` ends at 243/250 and
   absorbed the resolution's writes, so no third store module was needed; `notice_intake.py` drops
   246 -> 187 and `receive_notice` was not touched.
3. **`the notice's state is` overrides `conftest.py`'s definition rather than stacking `@given` on
   it, against the instruction, because stacking cannot work.** The shared definition asserts
   `response.state`, and Rule 2's `400` row asserts `PENDED` on a response that carries no state -
   the identity check runs before the notice is read. The local definition asserts the stored notice
   **and** the response wherever the response reports a state, which is what keeps Rule 6 a proof
   about the replay rather than a second copy of Rule 3. `the response is` did just need `@given`,
   as the instruction said.
4. **Which arrival a record came from is checked against what arrived, never off `arrival_index`.**
   A step that read the origin from the record's stored position would be asserting the index it
   just indexed by. Each named arrival is rebuilt from the scenario's own steps and hashed with
   `payload_reference`, so "the second record is the reviewer's first resolution" is a claim about
   content that can fail.
5. **Two escalations rather than invented status codes.** A resolution naming a notice this
   deployment does not have, and one carrying a loss date that is not a date at all, both raise
   `NotImplementedError`: the closed status-code table has a row for neither, routing an unknown
   identifier belongs to the HTTP layer that does not exist, and intake answers the second at its own
   schema boundary with no decision extending that row here. Both are tested.
6. **Four phrases moved into `tests/acceptance/conftest.py`** - the blockers assertion from
   `test_notice_intake_acceptance.py` and the three idempotency phrases - because
   `resolution.feature` is the second locked spec to state each of them word for word, which is the
   standing reason for that file rather than the duplication gate (which does not read `tests/`).
   `tests/acceptance/support.py` is new and holds the compact-blockers parser, for the reason
   `tests/shell/support.py` exists.
7. **The replay rule passes with no change to the replay path - verified, not assumed.**
   `answer_repeated_key` already reports `remembered.state` read fresh from the notice row, so a
   notice a resolution moved replays `TRIAGED`. Not one line of `idempotency.py`, and no line of
   `notice_intake.py`'s replay path, changed for it.
8. **What the acceptance suite cannot see was measured, not guessed, and is why the shell tests
   exist.** Stamping `resolved_at` on refusals as well as applications passes all 21 scenarios -
   nothing in the spec can observe it - so that rule is asserted only under `tests/shell/`, along
   with the transaction boundary, the two refusals that persist nothing, and the pend instant
   surviving a resolution. Three other deliberate breakages were run to confirm the scenarios do
   bite: disabling the identity check, ignoring later records in the overlay, and judging on the
   receipt date instead of the resolution's instant each fail exactly the rows they should.
9. **The scope wall on the word `tolling` was broken and then fixed rather than argued with.**
   Four docstrings named the statutory interval by that word. Every one was a citation or a
   disclaimer rather than an identifier, but `src/` had never contained the word and the wall says
   nowhere, so `6c64893` cites Fla. Stat. 627.70131(8)(b) by number instead - which is the primary
   source this project's citation rule asks for anyway.

**One thing recorded rather than fixed, and it is `ASSUMPTIONS.md` decision (c).**
`resolution.feature`'s injury row asserts `claimant_name` before `incident_description`, an order
`validation.feature` does not state anywhere: canonical order is fixed by code there, and the
within-code order is alphabetical by field, from `validation.py`'s sort key alone. A locked spec now
depends on it. Stating it in `validation.feature` is a reopening of a locked spec and is a candidate
queue item, not this item's defect to fix.

**Scope walls held.** Items 5f, 5g, 5h, 5i untouched; both `NotImplementedError` raises stay and
stay tested, moved into `rules.py` intact; `src/claimgate/domain/` is byte-identical to `origin/main`
(`git diff origin/main HEAD -- src/claimgate/domain/` is empty); no HTTP layer; no SIU computation;
no field, column, function or word `tolling` anywhere under `src/`.

**Next action is the human's: review and merge to `main`.** Nothing about this item is waiting on an
agent, and no `gauntlet` command from the human's list was run.

**Item 5e is merged to `main`** (merge commit `0bab644`, `--no-ff`, 24 files, +2250/−218),
2026-08-25. Branch `phase2/5e-resolution` ends at `911c962`. Spec locked at `187244d` (blob sha256
`2b014521a1bc`, 589 lines, 97 mutants, 0 simulated and 0 gate survivors); implemented and green at
`911c962`: 363/363, coverage 100/100, code mutation 342 killed / 100%, acceptance 9 specs, 69
reviewed-equivalent, no new approvals; size worst function 23/25, largest module `store.py` 243/250.
The acceptance gate now takes 693–759s. `handoff.sh`'s false `on origin: NO` for a SHA was fixed in
the branch's last commit.

**Two decisions made after the merge, 2026-08-25, advisor-recommended, human-ratified,** recorded
in `ASSUMPTIONS.md` under item 5e as (d) and (e): an unknown `notice_id` on the resolution endpoint is
`404`, nothing persisted; an unparseable loss date in a resolution body is body schema-invalid and
takes the existing `400` row. Both currently raise `NotImplementedError` in `shell/resolution.py`,
correctly escalated. Their scenarios are carried to item 5i's reopening of `resolution.feature`.

**Correction, 2026-08-25, a claim in the 5e implementation report.** "Working tree clean" was true
when written. After the merge, the human's working tree carried `features/validation.feature` one
line off its lock — the `_gauntlet` marker. Cause, from the event log and `.gauntlet/mutation-backup/`
timestamps: the Stop hook's stop-check run `20260825T152701` was killed by the hook's 600s timeout
608 seconds in, mid-mutation on the last spec; the next stop-check then reported the spec as
"changed since it was approved". That diagnosis is false whenever a backup in
`.gauntlet/mutation-backup/` differs from the spec beside it. Restored with `git checkout --`;
nothing committed was affected. Mitigations: commits 3 and 4 below; recorded for Gauntlet in
`gauntlet-findings.md` (agent-gauntlet repo, `2547aa1`'s successor).

*Corrected 2026-08-26: that successor does not exist. `agent-gauntlet`'s HEAD on origin is
`2547aa1` itself, and `gauntlet-findings.md` there carries no mention of the 600s timeout, of
the path-order determinism that makes `validation.feature` the deterministically stranded file,
or of the `.gauntlet/mutation-backup/` diagnostic. The ClaimGate-facing half of that finding was
written and the Gauntlet-facing half was not. Recorded rather than silently fixed: this file
naming the ref the finding was supposed to land in is the only reason the gap was recoverable.*

*Annotated 2026-08-26, later the same day: the correction above is itself superseded, and is kept
rather than deleted because the sequence is the point. `agent-gauntlet`'s HEAD is now `f807aaf`
("record the 2026-08-26 session"), and `gauntlet-findings.md` at that ref carries the 600s-timeout
entry, the path-order determinism that makes `validation.feature` the deterministically stranded
file, and the `.gauntlet/mutation-backup/` diagnostic — plus a further entry recording that a
stop-check is more often killed by an interrupting human reply than by any timeout, which is a class
neither this file nor that one had named. Verified by reading the file at `f807aaf`, not inferred
from the commit subject. The Gauntlet-facing half of the finding did land; it landed after the
correction saying it had not.*

**Note on history.** `ea64069` and `ab12a2b` added `gauntlet-findings.md` to this repository by
mistake and `c360ce9` reverted them; that file lives in the agent-gauntlet repository and this
project never reads or edits it.

**Next action:** the human runs `gauntlet lock` for commit 4, then a fresh advisory session decides
item 5f's SIU open points before 5f's opening prompt is written. Nothing else is in flight.

**Item 5f is open on `phase2/5f-siu-separation`**, cut from `main` at the commit that carries this
paragraph. It supersedes the "Next action" line above: `gauntlet lock` for commit 4 was run
(`0c53323`), and the advisory session that line called for has happened. Six decisions came out of
it — advisor-recommended, human-ratified, 2026-08-25, all recorded in full with their reasoning in
`ASSUMPTIONS.md` under "Item 5f, SIU separation", one line each here:

1. Indicators are evaluated on every transition into `TRIAGED`, on both paths, inside that
   transaction, on the merged current view — never at `RECEIVED` or `PENDED`.
2. Late reporting is measured from the original receipt instant's jurisdiction date, never from the
   resolution instant.
3. One append-only event row per indicator per evaluation, including `FALSE` and `NOT_EVALUATED`,
   carrying the indicator, the value, the reason code, the `ruleset_version` and the transaction's
   caller-supplied instant.
4. No read surface in phase 2 beyond a restricted read in the test API the scenarios use.
5. The leak assertions are outcome negatives on four surfaces — intake response, resolution
   response, the notice's standard view, every audit entry — plus the reason-code exclusion from
   blockers.
6. The rules applied are the carrier's configuration as resolved at the triaging transaction.

None of the six is a new indicator; further FNOL indicators are recorded in `ASSUMPTIONS.md` as a
candidate item, not as 5f scope. **Next: draft `features/siu_separation.feature`, spec-only.** No
implementation, no approval, and no command from the human's list. The acceptance gate will report
one unapproved spec for as long as the draft is unlocked, which is guaranteed by the
separate-commits rule and is not a defect to retry.

**One point of item 5f's is escalated and undecided:** what `ruleset_version` names on an indicator
event row, and what its value is. Decision 3 settles that the field is carried; `PHASE2_DESIGN.md`'s
audit schema calls it a label for the domain rules while decision 6's wording reads as a version of
the carrier configuration, and the carrier configuration model has no version in it at all. No
agreed value exists either — `records.py` leaves the audit entry's own copy unset and
`notice_intake.feature` deliberately asserts no literal for it. Full reasoning in `ASSUMPTIONS.md`
under "Item 5f, one point the six decisions do not cover". The draft stays inside the intersection:
it asserts that one evaluation's two event rows record the same ruleset version as each other and
names no literal, and asserts nothing about which version it is or how it relates to the audit
entry's. **This is the human's call and blocks nothing else in 5f.** Two other things were checked
rather than assumed and needed no decision: `carrier_configuration.feature` already carries both
carrier phrases for a configured and an unconfigured late reporting threshold, so the draft reuses
them; and the restricted read of a notice with no events is determinate under decision 3.

**That point is now decided** — 2026-08-25, advisor-recommended, human-ratified: `ruleset_version`
names the domain rule set's own version, never the carrier's numbers, and the spec asserts it
relationally with no literal. Full reasoning in `ASSUMPTIONS.md` under "Item 5f, one point the six
decisions do not cover", in the entry's closing paragraph.

**Item 5f's spec is drafted, not approved.** `features/siu_separation.feature`, on
`phase2/5f-siu-separation` — blob sha256 `cbde5f6ab716`, 511 lines, exported from the ref rather
than read out of the working tree (`9e3beed49521`/388 was the first draft, `cfe5494ea8b8`/440 the
ruleset-version amendment). Six Rules, eight scenarios: what a notice triaged at intake
records for each indicator (an outline over the carrier's threshold and the loss date, with the
unconfigured threshold as a sibling scenario because "no threshold" has no numeral to share a
column with 45 and 44); that nothing is recorded until the notice reaches `TRIAGED`, so a pend and a
refused resolution record none and the resolution that releases it records two; that late reporting
is counted from the receipt date and not the resolution date, while the events are still stamped
with the resolution's own instant; that a replay records nothing while a resubmission past the
idempotency window records its own pair; and that nothing about SIU reaches the intake response, the
resolution response, the notice's view, or any audit entry. Since the ruleset-version decision, an
evaluation's two events are also tied relationally to the audit entry that moved the notice — on the
intake path, on the resolution path, and, for a resubmission past the idempotency window, to the new
notice's own entry rather than the original's — and the late reporting event records the threshold
it applied, or no threshold where none was configured, never a zero. A sixth Rule, added on
review, is the only scenario that tells decision 6 apart from an implementation that reads the
carrier configuration once when the notice arrives and carries that reading forward: the carrier has
no late reporting threshold at intake and gains a 7-day one while the notice sits pended, so an
arrival-time reading records `NOT_EVALUATED`/`NO_THRESHOLD_CONFIGURED` where the correct one records
`TRUE`. Every other scenario in the file passes identically under both. The Background now also
configures the recent policy inception threshold at 30, matching `notice_intake.feature`, so this
file's `NO_CONTINUOUS_COVERAGE_DATE` reasons follow from one absent input rather than from
`siu_indicators.feature`'s precedence rule between two absences.

**Measured** against `gauntlet.acceptance.mutation.mutants()` at the committed blob:
`siu_separation.feature` **53 mutants**, 29 `example` and 24 `literal`, by scenario
9/3/8/4/9/8/4/8 — 44 before the review amendments, and all 9 of the increase belong to the new
plain scenario. The ruleset-version amendment before it moved the total not at all, because every
assertion it added is a fixed step in an outline or an unquoted, digit-free step in a plain
scenario, and neither is a mutation target; the Background's new threshold line is likewise never
mutated.
The four files the item touches nothing in re-measure unchanged at the same ref:
`resolution.feature` **97**, `idempotency.feature` **40**, `notice_intake.feature` **48**,
`siu_indicators.feature` **39**. Each amendment's blast radius inside the file was measured by
dumping every `locator :: signature` at both refs and diffing element for element, not inferred from
the matching totals (`docs/harness-findings.md`, "Comment inertness is confirmed by locator
identity, not count parity"). The ruleset-version amendment left **six of seven scenarios
byte-identical**, moving 5 of the resolution outline's 8 — the ones whose locator or signature embeds
the applied row's `events` cell, which that amendment lengthened — and slot-for-slot the two lists
paired 1:1 on scenario, kind, column and order, so those five moved rather than being replaced. The
review amendments are cleaner still: **nothing was removed and 9 were added, every one of them in
the new scenario**. The Background change and the two comment rewrites disturbed no existing mutant,
which is the measured form of the claim that a Background step and a comment are both invisible to
the engine. **Simulated** — hand-run against each rule, not measured, because
survivors cannot be measured before the spec is approved and step definitions exist: **2 survivors
of 44**, both in the intake outline and both in one scenario, so one approval reason covers them.
The first is the threshold increment on the row where the interval equals the threshold: that row
asserts the non-firing side of the boundary, which `gherkin-specs` requires, and raising a threshold
above an interval already below it cannot change the answer. The second is the loss-date swap on the
44-day row: that row exists to prove the boundary follows the carrier's configured value rather than
a constant, and both loss dates in the column exceed 44, so no swap between them can flip it.
Neither was reshaped away — a shape that hid them would remove the boundary row or the
configuration proof itself. Of the 42 simulated kills, **10 are vacuous step-lookup kills** rather
than real tests (`docs/harness-findings.md`, 2026-08-23): all 3 in the unconfigured-threshold
scenario and 8 of the 12 in the two leak scenarios, where a quoted literal in a plain scenario takes
the `_gauntlet` marker and binds to no step pattern. The unconfigured-threshold rule is therefore
stated and executed but not protected by mutation, and that is recorded in the file rather than left
to be inferred from a count.

Each amendment re-simulated only what it touched; every other scenario keeps its earlier
simulation because its mutants are byte-identical. Same **2 survivors, now of 53**, same two rows in
the intake outline, same two reasons, across both amendments. **No new survivor appeared, and the
new scenario produced none**: its 9 mutants are 3 real kills and 6 vacuous ones — the two `7->8`
increments both die (the configured one on the `TRUE` it contradicts, the asserted one on the number
the event actually reports), `200->201` dies on the status, and the six quoted literals take the
`_gauntlet` marker and bind to no step. That brings the vacuous share to **16 of 51 kills**, up from
10 of 42. The relational threshold tie in the intake outline reuses the input placeholder, so a
threshold mutant moves the configured value and the recorded one together and its verdict is still
decided by the outcome column; the new scenario states both numbers as literals instead, so there
they mutate independently and an implementation echoing a constant back rather than what it applied
fails.

**Eighteen step phrases in the draft have no definition anywhere**, all of them the restricted read
and the leak negatives: the two `... indicator recorded for the notice is ...` assertions, the three
event-count forms (`exactly two ... are recorded`, `the SIU indicator events recorded for the notice
<compact>`, `<count> ... recorded in all`), `no SIU indicator event is recorded for the notice`,
`the original notice still has exactly two ...`, the two stamp assertions, `those two events record
the same ruleset version as each other`, the four negatives (`the response`, `the notice's own
view`, `every entry in the audit trail`, `the blockers in that response`), and the five the
ruleset-version decision added — the three audit-entry ties (`... as the audit entry that triaged
the notice`, `... that released the notice`, `... that triaged its own notice`) and the two
threshold assertions (`records a threshold of <threshold> days`, `records no threshold`). The review
amendments added none: the new scenario reuses phrases the draft already had, and the Background's
recent policy inception threshold is one `conftest.py` defines.

**One of the six module-local phrases needs more than moving, and it was checked rather than
assumed.** `"AAAA" configures a late reporting threshold of N days` is defined only in
`test_carrier_configuration_acceptance.py`, and it writes to `context["rules_source"]` — that
module's own key, which neither `submit_notice` nor `resolve_notice` reads. Copied as-is it would
set a value nothing consults, and the new sixth Rule would pass for the wrong reason. Written to
`conftest.py`'s `_rules_entry` pattern instead it replaces in place on a second invocation, and the
shell honours the change: `shell/resolution.py:131` re-resolves the carrier configuration inside the
resolution transaction from the mapping handed to that call, with no snapshot on the notice record.
That is what makes the new Rule reachable at all, and it is implementation-side work, not a spec
question. Six more phrases exist but
only as module-local definitions another module cannot see — the four reviewer phrases and the
`the notice's state is` `@given` override in `test_resolution_acceptance.py`, and `"AAAA" configures
a late reporting threshold of N days` in `test_carrier_configuration_acceptance.py`, which writes to
a differently-named context key. Implementation moves them or redefines them; that is item 5f's
implementation commit, not the spec's. **Two phrases stack a second keyword on an existing one**:
`the notice's state is` is `@then`-only in `conftest.py` and is used `@given` here, exactly as
`resolution.feature` does, and the two given-side negatives (`no SIU indicator event is recorded` and
`the blockers in that response name no SIU reason code`) are assertions used as setup. **One phrase
deliberately stacks a second phrasing on an existing concept:** `conftest.py` already defines
`the late reporting indicator is ...`, which reads a computed value; `... recorded for the notice is
...` reads the stored event. Two subjects, two phrases, on purpose.

**Next action is the human's: review the draft, decide the escalated ruleset-version point, and
approve the spec.** The acceptance gate will report `features/siu_separation.feature` as an
unapproved spec until then — guaranteed by the separate-commits rule, not a defect. No
implementation exists, `src/` is untouched, and no command from the human's list was run.

**Item 5f is implemented on `phase2/5f-siu-separation`, awaiting two mutant approvals.** The spec
was approved at `c82ee92` (`54a3d70` records the approval) and neither the file nor its digest
moved: `features/siu_separation.feature` still hashes `cbde5f6ab716`, matching `gauntlet.lock.json`.
Three implementation commits, in the order the log should read them: the domain label and its
convention (`a897f4d`), the schema and the store (`cbe204e`), and the evaluation with its
allow-lists, steps and tests (`16c2b34`). This paragraph is the fourth.

**Gate figures from one full `gauntlet check` at `16c2b34`.** Everything green except acceptance,
which fails on the two survivors below and on nothing else: protect 3/3, static 0 findings, size
worst function 24 of 25 and largest module `store.py` 248 of 250, complexity 5 of 6, boundary 12
step files and 0 direct imports, tests **397/397**, coverage **line 100.0 / branch 100.0**, crap
5.0, duplication 0, and code mutation **score 100.0%, 342 killed**. That mutation figure is
*identical* to the baseline this item started from, which is the measured answer to whether the
domain addition disturbed it: `RULESET_VERSION` is a module-level string constant and the engine
generates **no mutant for it at all**, so the score moved by zero rather than by its own mutants
being killed. `tests/unit/test_ruleset.py` still asserts the label round-trips as an ISO date,
because the convention is that it is date-stamped and nothing else would enforce that.

**Acceptance: 10 specs, 2 surviving mutants, 69 reviewed-equivalent, 866.202s** - up from 5e's 759s
and still the only gate that costs anything. The gate prints no killed count, so it was derived
rather than read: `gauntlet.acceptance.mutation.mutants()` measured directly at the implementing ref
gives **708 mutants across the ten specs**, so **637 were killed** (708 − 2 surviving − 69
reviewed-equivalent). The 69 are the same 69 the branch started with - **no new approval was created
by any other spec**. Per file, re-measured: `siu_separation.feature` **53**, exactly the drafting
session's figure; and the four files this item touches nothing in are unchanged at
`resolution.feature` **97**, `idempotency.feature` **40**, `notice_intake.feature` **48**,
`siu_indicators.feature` **39**.

**The two survivors are the two the spec header named, and no third appeared.** Both are in the
intake outline's `Examples`, so one approval reason covers them.

1. **`features/siu_separation.feature:198`, `45->46`** - the threshold cell on the row
   `| 45 | 2026-07-10 | FALSE |`. That row is the non-firing side of the boundary, which
   `gherkin-specs` requires a threshold to have: the interval is 45 days and late reporting fires
   only when the interval is *more* than the threshold, so raising the threshold to 46 leaves 45
   days still not more than it and the answer is still `FALSE`. My reading: equivalent, and
   necessarily so - raising a threshold that an interval already fails to exceed cannot change the
   outcome in any implementation, correct or not. Removing it would mean removing the non-firing
   row, which is the one the boundary is proven by.
2. **`features/siu_separation.feature:200`, `2026-07-10->2026-07-09`** - the loss-date cell on the
   row `| 44 | 2026-07-10 | TRUE |`. That row exists to prove the boundary follows the carrier's
   configured value rather than a constant, so it pairs the 44-day threshold with a 45-day interval.
   Both dates in that column are more than 44 days before the receipt's jurisdiction date of
   2026-08-24 - 45 days and 46 days - so a swap between them leaves the row `TRUE`. My reading:
   equivalent. Killing it would need a third loss date inside 44 days, which would be a second
   non-firing row proving nothing the first does not, and reshaping it away would mean dropping the
   44-day row, which is the only proof in the file that the threshold is read from the carrier.

Both were predicted by hand during drafting and both landed exactly where the simulation put them.
**Nothing was run against them:** `gauntlet mutant approve` is the human's.

**What was built.** `src/claimgate/shell/` is now twelve modules rather than nine. `siu.py` is the
evaluation itself, called from both places a notice transitions into `TRIAGED` - the intake decision
transaction and an applied resolution - so decision 1 is one rule rather than two implementations
free to drift. `siu_events.py` owns the new append-only `siu_indicator_events` table: notice, an
ordinal in that notice's own order, indicator, value, reason code, the threshold that evaluation
applied, the ruleset version and `evaluated_at`, with `BEFORE UPDATE` / `BEFORE DELETE` triggers and
no statement in the package that would attempt either. `serialization.py` holds the four allow-lists.
`audit.py` is an extraction, and `domain/ruleset.py` is the label. No column was added to `notices`,
and nothing reachable from a notice row reaches an event.

**Judgment calls, flagged rather than buried.**

1. **`store.py` had seven lines of headroom, so the audit table moved to `audit.py`** - the same
   forced extraction `payloads.py` was in 5e, and this item both adds a column to every entry and a
   table beside them. `store.py` ends at 248 of 250 with delegating methods, so every existing
   caller of `get_audit_trail` and `append_audit_entry` is untouched.
2. **The rule label goes on *every* audit entry, not only the `SYSTEM` ones.** `PHASE2_DESIGN.md`
   describes `ruleset_version` as a label "for the domain rules that produced a SYSTEM decision",
   but the entry that releases a pend is a `USER` entry and the full validation ran to produce it,
   so actor type does not separate rule-driven entries from the rest. Writing it in one place also
   makes the leak negative over "every entry in the audit trail" uniform. Verified by grep before
   relying on it that no locked spec asserts the field is null - `notice_intake.feature:140-143`
   only records that it declines to name a literal, for the same reason this spec does.
3. **The events carry both indicators' thresholds, though only the late reporting one is asserted.**
   The schema stores the number each evaluation was given; the recent policy inception event
   therefore carries the Background's 30 even though its value is `NOT_EVALUATED` for a missing
   coverage date. That is the input it was given, and no spec says otherwise.
4. **`_judge` now returns the candidate and the carrier's rules alongside the outcome** (the new
   `Judgement` in `messages.py`) rather than the resolution path resolving the rules a second time.
   Decision 6 is that the rules are the ones *that transaction* resolved, and a second
   `resolve_rules` call would be a second reading even inside the same transaction.
5. **`the notice's state is` binds to a definition local to the new step module, and that was
   checked rather than assumed.** A module-local step in `test_resolution_acceptance.py` is invisible
   to any other module, and `conftest.py` defines the phrase `@then`-only, so this spec's `Given`
   uses would have found nothing at all. The reading itself moved to `tests/acceptance/support.py`
   and both modules call it, which is what keeps the duplication gate satisfied without either file
   losing its own definition. It cannot move to `conftest.py`: three other specs assert the phrase on
   responses to submissions that created no notice, and there would be no stored notice to read.
6. **Five phrases moved into `tests/acceptance/conftest.py`** - the reviewer's identity, the field
   the reviewer supplies, the resolution's instant, and the carrier's late reporting threshold -
   because `siu_separation.feature` is the second locked spec to state each of them word for word.
   The threshold phrase is written on `_rules_entry` rather than copied from
   `test_carrier_configuration_acceptance.py`, whose definition writes to that module's own
   `rules_source` key, and that module keeps its own. **This was verified rather than reasoned:**
   pointing the conftest step at `rules_source` instead fails 8 of the 13 scenarios, including the
   decision-6 one, which is precisely the "passes for the wrong reason" the drafting session warned
   of.
7. **The leak negatives were proved non-vacuous by planting a leak.** Adding a `late_reporting`
   field to `NoticeView` and to its allow-list fails both leak scenarios and nothing else; the two
   scenarios pass again when it is removed. The step reads the serialized surface as text rather
   than any named field, and takes the forbidden names from the test API, which takes them from the
   code that defines them.
8. **The atomicity tests fail *after* the events are written, not before.** A fixture that raised
   before the write would only prove the events were never made. `tests/shell/test_siu_evaluation.py`
   patches `siu.record_evaluation` to write and then raise, so what it asserts is that the events
   were rolled back with the transition they belong to - on both paths, leaving the notice at
   `RECEIVED` and at `PENDED` respectively with no `TRIAGED` entry and no events.
9. **One out-of-scope edit was made and reverted.** A `ruff check --fix` across the tree reordered
   an import in `tests/unit/test_validation.py`, which this item does not touch and which the
   project's own static gate does not ask for. Reverted with `git checkout --` before the commit;
   the gates were run through `gauntlet check --gates ...` from then on.

**Scope walls held.** No new indicator, value or reason code; no HTTP layer and no read route for
events; items 5g, 5h and 5i untouched, with all four `NotImplementedError` escalations intact (two
in `rules.py`, two in `resolution.py`). `src/claimgate/domain/` differs from `origin/main` by the
addition of `ruleset.py` and by nothing else - `git diff --name-only origin/main HEAD --
src/claimgate/domain/` prints that one path. No `tolling` and no `suspicious` anywhere under `src/`;
the single occurrence of `fraud` is the prohibition's own wording in `domain/siu.py:4`, byte-
identical to `origin/main` and predating this item. `datetime.now` is still called **0 times** under
`src/claimgate/shell/`.

**Next action is the human's: `gauntlet mutant approve` for the two survivors above, then review and
merge to `main`.** The acceptance gate stays red until then, which is guaranteed by there being
survivors at all rather than a defect, and no command from the human's list was run.

**Item 5f's two survivors are approved and the branch is green.** `gauntlet mutant approve`
landed at `1778e25`, one reason covering both, approvals stamped `2026-08-26T10:42:18Z`. The
spec's digest did not move: `features/siu_separation.feature` still hashes `cbde5f6ab716`,
matching `gauntlet.lock.json`. `gauntlet check` passes at `23bb58d`: protect 3/3 paths
unchanged, static 0 findings, size worst function 24 of 25, complexity 5 of 6, boundary 12 step
files / 0 direct imports, tests **397/397**, coverage **line 100.0 / branch 100.0**, crap 5.0 of
15, duplication 0, code mutation **100.0% / 342 killed**, acceptance **10 specs, 71
reviewed-equivalent, 893.841s**.

**Reviewed-equivalent moved 69 -> 71; the killed count is derived, not printed.** The green
acceptance summary carries no killed figure, so it was computed: **708 mutants across the ten
specs**, measured directly against `gauntlet.acceptance.mutation.mutants()` at the branch ref
rather than read off any gate — 180 / 97 / 90 / 84 / 57 / 53 / 48 / 40 / 39 / 20 for
`validation`, `resolution`, `triage`, `carrier_configuration`, `duplicates`, `siu_separation`,
`notice_intake`, `idempotency`, `siu_indicators`, `jurisdiction_date` — minus 0 surviving and 71
reviewed-equivalent gives **637 killed**, the same 637 as the pre-approval run. Approving a
survivor moves it between two columns and changes nothing about what executes: Gauntlet's
`gates/acceptance.py`'s `_survivors` applies every mutant and runs the full suite for each one
before the ledger is consulted at all.

**The acceptance gate's wall time is a new project maximum at 893.841s**, against 866.202s on
the same ten specs and the same 708 mutants at the pre-approval run. The 27.6s between them is
unexplained and inside ordinary variance — two datapoints, not a trend, and specifically not
evidence that an approval costs time. The Stop hook's timeout is 1800s, so headroom is roughly
2x; the cost is mutant count times suite time and both still grow with every item.

**`docs/temp_doc.odt` is removed.** No gate would have caught it, and that was verified from
Gauntlet's source rather than inferred from `gauntlet.toml`: `gates/base.py`'s `python_files()`
filters candidates on `f.is_relative_to(self.src)` and `tool_targets()` hands external tools the
`src` tree, so anything outside `src/` is invisible to static, size, complexity and duplication
alike.

**Item 5f is ready to merge, and merging promptly is the point.** `main`'s copy of this file
described item 5f as having no implementation and `src/` untouched for two days while it sat
finished and approved on this branch. That is the third instance of the
documentation-lands-on-main convention being missed — item 4a carried two such commits forward,
item 5c recorded its own, and this is 5f's. The cost is specific and is not stylistic: `main` is
what a memoryless session reads.

**Item 5f is merged to `main`** (merge commit `96a5e9e`, `--no-ff`, 27 files, +2021/−121),
2026-08-26. Branch `phase2/5f-siu-separation` ends at `d4ecf1b`. Spec locked at `c82ee92`
(`features/siu_separation.feature`, blob sha256 `cbde5f6ab716`, 511 lines, 53 mutants), two
equivalent mutants approved at `1778e25`, close-out at `9a39c0b` and `d4ecf1b`. Ledger: **71
mutant approvals**, up from 69. Verified after the merge rather than assumed: `main`'s tree is
byte-identical to the branch tip (`git diff phase2/5f-siu-separation main` is empty), the spec
digest on `main` matches `gauntlet.lock.json`, and both new approvals pair to live mutants by
digest.

**No post-merge `gauntlet check` was run, and this entry says so rather than leaving the omission
to look like a pass.** The convention every prior item follows is to record a post-merge figure.
Here the merged tree is byte-identical to `d4ecf1b`, which differs from the green-measured
`23bb58d` only in `QUEUE.md`, `docs/harness-findings.md`, `.gitignore` and a deleted binary — none
of which any gate reads. So the figures at `23bb58d` carry over: 397/397 tests, coverage 100/100,
code mutation 100.0% / 342 killed, acceptance 10 specs / 71 reviewed-equivalent / 893.841s. That
is **reasoned from tree identity, not measured on `main`**, and it is labelled that way
deliberately: a 900-second run against a byte-identical tree buys nothing, and the next coding
session's Stop hook will produce a real post-merge figure for free.

**Four corrections, all from the 2026-08-26 advisory session.**

1. **A session report named a commit that does not exist.** Item 5f's close-out report gave `main`
   as `2448922`; `main` was `244892e`, and `git cat-file -t 2448922` returns "Not a valid object
   name". Confined to the report — neither committed document contains the string. This is the
   second instance in this project, after the 2026-08-23 report that attributed item 5b's closure
   to two `main` commits that did not contain it. The cheap check that settles it, and that neither
   instance had applied: **every commit a report cites is falsifiable with `git cat-file -t`**, in
   one command, before the report is written.
2. **A claim was attributed to the advisor's prompt that the prompt did not make.** The same report
   said the advisor had stated that a concurrent `gauntlet check` exits 0 having executed zero
   gates. The prompt said only not to run a second check. The claim is true and is `CLAUDE.md`'s,
   corroborated by `docs/harness-findings.md`'s record of five lock-rejected runs in 59 seconds —
   so the decision not to run one was right and only the sourcing was wrong. Recorded because
   citing the wrong source for a true fact is the same failure as citing a stale one: the next
   reader checks the named source, does not find it, and cannot tell which half is wrong.
3. **The advisor's own error, recorded where it was made.** Item 5f's close-out paragraph argues
   for merging promptly, and it was written into `main`'s copy of this file — a copy no memoryless
   session reads until after the merge it is arguing for. As a record of the third instance of the
   documentation-lands-on-main convention failing (items 4a, 5c, 5f) it stands. As an argument for
   acting it was addressed to a reader who cannot act on it, and it should have gone to `CLAUDE.md`
   as a standing constraint or been landed on `main` directly the way item 5d's record was. The
   general shape: **an exhortation written into an artifact only reachable after the moment it
   describes is inert, however true it is.**
4. **The prompt that requested this entry carried a wrong anchor, and the stop that caught it is
   the mechanism working.** The anchor given as "the file's current final line" — "is the copy
   nobody reads until after the merge…" — appears nowhere in this file at any ref; `git log
   --all -S` confirms it never has. It is a verbatim sentence from the implementing session's
   own conversational close-out report, quoted as though it were the document. The advisor had
   the file at the ref and did not read its tail before writing the anchor. The rule this adds
   to the anchor convention: **an anchor is quoted from the file at the ref, never from the
   conversation about the file** — the two can agree closely enough to pass a careless read and
   still never have shared a byte. The exactly-once assertion plus stop-on-missing converted the
   error into a question; a guess would have been unrecoverable in one direction, since the
   plausible alternative reading rewrote a merged record to absorb a criticism of itself, which
   no later check could distinguish from the record having always said that.

**Item 5g is open on `phase2/5g-jurisdiction-map`, drafted and not implemented.** The draft spec is
`features/jurisdiction_selection.feature`, committed at `1a5d90d` — 189 lines, blob sha256
`4d269770f90e`, **30 mutants across 30 unique locators**, no locator collision, every mutant
`example`-kind. `gauntlet spec list` reports it `unapproved`; approving it is mine and has not
happened. The branch also carries a merge of `main`'s documentation commit for this entry and the
`PHASE2_DESIGN.md` correction below, so it stays a superset. Nothing under `src/` is touched, no step
definitions exist, and the two swappability tests are not written.

**The acceptance gate is red on this branch, and it is guaranteed rather than a defect.** A spec that
is drafted and not approved is the state the spec-lock-then-implementation rule produces on every
reopening, and this one additionally has no step definitions bound to it. Neither clears from the
agent's side. Do not treat a red acceptance gate here as something to fix.

**`PHASE2_DESIGN.md`'s "Jurisdiction axis" gained a dated correction** (2026-08-26): "`property_state`
is captured on the notice for this purpose" described intent, not the codebase. At `92db17d`, `git
grep property_state` across `src/`, `features/` and `tests/` returned nothing. Capturing it is item
5g's work.

**Three rules in the draft; the third is recommended and not ratified, and that is the decision this
item is waiting on.** Rule 1 is that the jurisdiction's calendar date, not the UTC one, decides
whether a loss date is ahead of today — the proof that the map's Florida entry actually supplies the
date the domain receives. Rule 2 is that an unsupported or absent property state marks the notice
`jurisdiction_unsupported` and does not block it. Rule 3 covers the collision the design section is
silent on: an unsupported property state means no map entry, so no timezone, so no jurisdiction
today, and "today" is exactly what the future-dated-loss determination and item 5f's late-reporting
indicator are counted against. The draft recommends the shape "Notice type and window selection"
already uses for `LOSS_ASSESSMENT` — an explicit not-evaluated outcome with a reason, never a silent
fallback — and names one new reason code, `NO_JURISDICTION_DATE`, in each of two separate closed
enumerations. Adding to a closed enumeration is mine. Until it is ratified, Rule 3's scenarios assert
behaviour nobody has approved.

**Four locked specs carry a step this item's submission-surface change invalidates, and none of them
has been touched.** `And the jurisdiction observes "<zone>"` appears in the Backgrounds of
`notice_intake.feature`, `resolution.feature`, `siu_separation.feature` and `idempotency.feature`,
and twice more inside `notice_intake.feature`'s Rule 5 scenarios. Once the timezone comes from a
jurisdiction map keyed by `property_state` rather than from the submission, that step has nothing to
set. `notice_intake.feature`'s "The same submission instant is judged differently under each of the
jurisdictions the book writes in" is the sharpest case: it varies `America/New_York` against
`America/Chicago`, and a Florida entry holding one timezone cannot produce the second. Reopening
those specs is a decision, not a mechanical follow-on, and it is not part of the draft.

**A one-entry-per-jurisdiction map is factually wrong for the Florida panhandle, and the draft says so
rather than asserting either answer.** Escambia, Santa Rosa, Okaloosa and most of Walton are
`America/Chicago`; the rest of the state is `America/New_York` (`ASSUMPTIONS.md`, "The jurisdiction
timezone is a parameter of the conversion, not a constant in it"). A notice on a Pensacola risk is
dated Eastern under this design, which is a wrong `LOSS_DATE_IN_FUTURE` answer around midnight
Central.

**Adding `property_state` to the notice's fields breaks item 5d's idempotency comparison for keys
already remembered.** The comparison hashes the submitted fields — `records.payload_reference`, SHA-256
over the whole field set — and compares that against the reference stored when the notice was created.
A new field changes every reference, so a byte-identical resubmission under a remembered key computes
a reference the stored one cannot match and is answered `409 conflict` instead of a `200` replay.
Bounded to the 24-hour key lifetime, and only for keys remembered before the change. Removing
`jurisdiction_timezone` costs nothing here by contrast: it is a shell input, never part of the hashed
field set.

**What remains before item 5g closes:** ratify or replace Rule 3; approve the spec; decide the four
locked specs' reopening; then the map, the `property_state` capture through schema, message shape and
persistence, the step definitions, and last the two swappability tests — which land as tests, not as
feature files, because a fictional second jurisdiction is not a business rule of this product.

**The draft was reviewed and amended, 2026-08-26; the current draft is `955dfef`, superseding the
figures above.** 200 lines, blob sha256 `67e65c362fd7`, **36 mutants across 36 unique locators**, no
collision, every mutant `example`-kind. Four amendments, all from the review: two comments were
recomputed and had been wrong in the first draft — Rule 1's claimed that a UTC implementation is
wrong on both of its rows when only the 02:30Z row separates the two calendars, and the panhandle
note had the skew direction backwards. Two assertions were added: Rule 1 now asserts the clean
`FALSE` determination, which nothing asserted before, so an implementation recording nothing on a
clean evaluation would have passed; and Rule 2 gained an `fl` row pinning the unrecognized-string
class.

**Three decisions were ratified and are recorded in `ASSUMPTIONS.md`, dated 2026-08-26.** One
timezone per jurisdiction, with the skew stated in its corrected direction — Eastern's date is never
behind Central's, so no false `LOSS_DATE_IN_FUTURE` is possible and both skewed answers are tolerant.
`property_state` is matched exactly and a miss is marked rather than normalized. And the zone that
dates a resolution's SIU interval comes from the notice's merged view rather than from what was known
at receipt, which closes a gap item 5f decision 2 left open by fixing the instant and not the
timezone. The four per-consumer recommendations from the collision analysis were accepted as drafted.

**Two things are still open before the spec can be approved.** The acceptance gate stays red until
`gauntlet spec approve` runs, which is mine. And Rule 3 still carries a `RECOMMENDED, NOT RATIFIED`
banner over its two scenarios; if accepting the per-consumer recommendations settled those rules —
including `NO_JURISDICTION_DATE` as a new code in two separate closed enumerations — that banner is
stale and should come off before approval rather than being locked into the file. It was left in
place because removing it was not among the amendments asked for, and a closed-enumeration addition
is not something to infer.

**Both of those closed on 2026-08-26, and the current draft is `a456913`.** 202 lines, blob sha256
`4ea48af66271`, still **36 mutants across 36 unique locators**, all `example`-kind — verified as
comment-only by locator *and* signature list identity against `955dfef`, not by count parity, which
`docs/harness-findings.md` records as the check that catches a swapped mutant at an unchanged total.
Rule 3's banner now reads `RATIFIED 2026-08-26, advisor-recommended`, and its closing sentence names
the ratification as what adds the reason code rather than leaving the addition to look like a
consequence of the spec having been written: **`NO_JURISDICTION_DATE` enters two closed enumerations
as two codes of one spelling** — the future-dated-loss determination's reasons and the SIU indicator
reasons — by that ratification and by nothing else. All four per-consumer recommendations stand as
accepted, and the resolution-path one is explicitly ratified in the form it was recommended: an
unsupported jurisdiction's `NOT_EVALUATED` determination never by itself refuses a release, which is
decided on the remaining checks.

**One obligation is carried forward to the implementation prompt, because no gate can raise it and
it is invisible until step definitions exist.** Six of the 36 mutants die by marker rather than by
sibling swap — the four `TRIAGED -> TRIAGED_gauntlet` in Rule 2, and the two empty `blockers` cells
that take `-> _gauntlet` because an empty cell has no sibling alternative. Those six die **only if
the step definitions compare outcome tokens exactly and refuse an unrecognized one.** A tolerant
parser — one that maps an unparseable `blockers` string to "no blockers", or an unrecognized state
token to a default — converts all six into vacuous survivors that cost six equivalence approvals
while proving nothing, the same failure `features/jurisdiction_date.feature` records from the
opposite direction, where a marker landing outside a closing quote killed a mutant at step
resolution before the domain was reached. The predicted zero survivors is conditional on that, and
the condition is the implementer's to satisfy.

**That obligation is now settled by reading the step definitions that already exist, and it splits
in two (2026-08-26).** The four `TRIAGED -> TRIAGED_gauntlet` mutants in Rule 2 die by
`conftest.check_state`'s exact string comparison — `assert context["response"].state == value` —
which are **real kills**, provided item 5g's own step module does not shadow that phrase with a
looser definition of its own. The two empty-`blockers` mutants that take `-> _gauntlet` die
differently: `parse_compact_blockers` splits each token on `":"` and unpacks two values, so a
colon-less `_gauntlet` raises `ValueError` on its first line, before the response's blockers are
ever read. Those are **vacuous kills** of exactly the class `docs/harness-findings.md` already
records under "A mutant killed by a step definition's own parse error" — not the vacuous *survivors*
this entry predicted, which is a better outcome than feared but not a test. Read the simulated zero
survivors as **34 real kills and 2 parse-error kills**, not as 36 assertions firing.

**A second, larger vacuity was found in the same reading, and it is not specific to this file
(2026-08-26).** Three of the 36 mutants — both determination cells that read `FALSE -> true` and
`TRUE -> false` — are the boolean substitution class now recorded in `docs/harness-findings.md`:
`mutate_value` returns `BOOLEANS.get(value.lower())` before `_swap` runs, so an upper-case `TRUE`
mutates to a lower-case `true` that no implementation can produce, and the sibling swap Rule 3's
first scenario exists for — `TRUE` becoming `NOT_EVALUATED:NO_JURISDICTION_DATE` — is **never
generated at all**. *Implementation-phase obligation:* the step definition that reads the
future-dated-loss determination must parse its expected token case-insensitively, which converts all
three into real tests. The same treatment of `conftest.py`'s two bare indicator steps
(`check_late_reporting_indicator`, `check_recent_inception_indicator`) and of
`test_siu_separation_acceptance.py`'s `check_recorded_indicator` converts the 30 vacuous kills
measured across `triage.feature`, `siu_indicators.feature` and `siu_separation.feature` likewise.
It belongs in item 5g's implementation commit, verified by the gate staying green with no locator
and no approval movement.

**The four-spec reopening is decided and executed, spec-only (2026-08-26)**, per `ASSUMPTIONS.md`'s
entry of that date: `jurisdiction_timezone` leaves the submission surface rather than living beside
`property_state`. Measured per file, before -> after, locators and signatures compared pairwise
rather than by count:

- `features/resolution.feature` 97 -> 97, `features/idempotency.feature` 40 -> 40,
  `features/siu_separation.feature` 53 -> 53. Background-only: `And the jurisdiction observes
  "America/New_York"` becomes `And the insured property is in "FL"`. **Zero locators moved and zero
  signatures changed** in all three.
- `features/notice_intake.feature` 48 -> 36. The same Background swap, plus Rule 5 deleted whole and
  replaced by a comment recording where each of its two obligations went. The 12 locators lost are
  exactly the 12 in those two scenarios; every other locator and signature is byte-identical; **no
  mutant approval is disturbed, because that file carries none** — verified against
  `gauntlet.lock.json`, where the 71 mutant approvals sit on `validation` (31), `duplicates` (18),
  `triage` (11), `siu_indicators` (7), `carrier_configuration` (2) and `siu_separation` (2), none of
  the last on a Background.
- `features/jurisdiction_selection.feature` 36 -> 48, from this session's own amendments (the
  corrected panhandle comment, the threshold-configured corner in Rule 3, and the new merged-view
  rule). All 36 pre-existing locators and signatures are unchanged; the 12 new ones are all in the
  three new scenarios.

**All five spec approvals are deferred to the start of the implementing session**, per the
operational rule in `docs/harness-findings.md`: approving a spec that is about to be edited again
spends a human action on a digest that will not survive. `gauntlet spec list` will report five specs
modified-since-approved until then, and the acceptance gate fails cheaply at its approval stage —
guaranteed by the spec-lock-then-implementation rule, not a defect, and not clearable from the
agent's side.

**One step-definition note the implementer should not have to rediscover.** The phrase
`the late reporting indicator recorded for the notice is <value>` that item 5g's new scenarios use is
already implemented, in `test_siu_separation_acceptance.py`'s `check_recorded_indicator`, and it
already parses both spellings the new `Examples` cells render (`TRUE`, and `NOT_EVALUATED with
reason NO_JURISDICTION_DATE`). pytest-bdd binds step definitions per test module, so item 5g either
duplicates it or the shared form moves to `conftest.py` — `docs/harness-findings.md`'s "Two locked
specs sharing a Background can only share step definitions through `conftest.py`" is the same
constraint arriving from a second direction. Duplicating it is the thing that would silently shadow
`check_state` and turn the four real marker kills above into vacuous survivors.

**The 2026-08-26 correction earlier in this file — that `agent-gauntlet`'s `gauntlet-findings.md`
never received the stop-hook findings — is itself superseded, and has been annotated in place rather
than deleted.** `agent-gauntlet`'s HEAD moved to `f807aaf` later the same day and now carries the
600s-timeout, path-order-determinism and `.gauntlet/mutation-backup/` entries. Verified this session
by reading `gauntlet-findings.md` at that ref, not inferred from the commit subject.

**Item 5g state as of 2026-08-26, superseding every figure above it in this entry.** The branch is
`phase2/5g-jurisdiction-map`, tip `263e54e`, a superset of `main`. Three commits carry the work that
matters: `e1a25cf` is the human's approval of `features/jurisdiction_selection.feature` at `a456913`
(so the "`gauntlet spec list` reports it `unapproved`" line far above is stale — it was approved, and
then reopened by the next commit); `0895546` amends that spec to 202 -> 327 lines and 36 -> 48
mutants; `263e54e` reopens the four Background-bound specs. Nothing under `src/` is touched, no step
definitions exist, and the two swappability tests are still not written.

**Five specs now read modified-since-approved, and the acceptance gate fails at its approval stage.**
That is the state the spec-lock-then-implementation rule produces, doubled here because the four
reopened specs were approved and are now edited and the amended one was approved and is now amended
again. It is guaranteed, not a defect, and not clearable from the agent's side. **The next action is
the human's:** `gauntlet spec approve` for all five, deferred to the start of the implementing
session so the approvals are not spent on digests that another amendment would invalidate.

**What remains before item 5g closes**, replacing the older list above: the five approvals; then the
jurisdiction map itself, the `property_state` capture through schema, message shape and persistence,
the removal of `jurisdiction_timezone` from the submission surface, the step definitions — including
the case-insensitive token parsing recorded above, without which six of the file's 48 mutants and 30
across three other specs test nothing — and last the two swappability tests, which land as tests
rather than as feature files because a fictional second jurisdiction is not a business rule of this
product. Item 5d's idempotency-comparison consequence, recorded above, is unchanged and still
unaddressed: adding a field to the hashed set answers a byte-identical resubmission under a
remembered key with `409` instead of a `200` replay, bounded to the 24-hour key lifetime.

**Item 5g is implemented on `phase2/5g-jurisdiction-map` and is not merged, 2026-08-27, and this entry supersedes every figure and every remaining-work list above it for this item.** Two
commits carry it: `951ff06` is the implementation, `faf8b5f` the two swappability proofs, which the
item sequences last because they are demo artifacts rather than the feature. The five specs were
approved at `402fdeb` at the start of the implementing session and **their digests are byte-identical
now to what they were then** — `jurisdiction_selection` `d71c9be553ce`, `notice_intake`
`dc714fa3bf6f`, `resolution` `e3c3a952c1b1`, `idempotency` `c66ea76c75a4`, `siu_separation`
`4aa68f2801c1` — verified against `gauntlet.lock.json` before the final gate run. **The human's
review is the next action; nothing about this merge is automatic.**

**Measured, not read off the gate.** Eleven specs, **744 mutants** across them
(`validation` 180, `resolution` 97, `triage` 90, `carrier_configuration` 84, `duplicates` 57,
`siu_separation` 53, `jurisdiction_selection` 48, `idempotency` 40, `siu_indicators` 39,
`notice_intake` 36, `jurisdiction_date` 20), against `gauntlet.acceptance.mutation.mutants()` at the
implementing ref. `gauntlet check` is green: 433/433 tests, code mutation 100% with 392 killed,
coverage 100% line and 100% branch, worst function 24/25 lines, duplication 0, and the acceptance
gate **71 reviewed-equivalent — the same figure as before the item**, so `jurisdiction_selection`
produced no survivor, the four reopened files produced none either, and no approval moved.

**What was built.** The jurisdiction map is a real lookup keyed by jurisdiction code, injected at the
shell boundary and structurally identical to the carrier rules lookup — the check QUEUE.md item 5a
names. The carrier identity reference gained the same seam, which item 5c left for this item.
`property_state` is notice content: hashed, persisted, part of the merged view, and overlayable by a
resolution. `jurisdiction_timezone` is gone from both surfaces. The future-dated-loss determination
is a recorded three-valued outcome on the notice row, rewritten by every decision; `NO_JURISDICTION_
DATE` entered both closed enumerations as ratified, outranking a missing threshold. Both zones come
from the merged current view, so a reviewer supplying the property state makes an interval
computable that was not computable at receipt. The notices table moved to `shell/notices.py` rather
than growing `store.py` past the size gate.

**Three judgment calls the reviewer should look at rather than take on trust.**

1. **The determination is deliberately off every outward surface**, unlike the marking, which is on
   `NoticeView` and its allow-list because a marking nobody can read is not a marking. The reason is
   measured, not stylistic: `features/siu_separation.feature`'s leak negatives scan a serialized
   surface as text, and `NO_JURISDICTION_DATE` is a code of one spelling in two enumerations, so a
   legitimate determination reason on an ordinary surface matches the exclusion list and fails the
   check that exists to catch a leak. It does not bite today only because both leak scenarios use
   `FL`. The determination sits where `pended_at` and `resolved_at` already sit — on the record, not
   in the view. **If the reviewer wants it visible, the leak negatives need a decision first.**
2. **Item 5g's raise is rebuilt, not removed.** The reporter-supplied timezone that caused it is
   gone; what escalates now is this deployment's own map holding an entry that names no timezone, or
   one this system cannot resolve. That is item 5i's class of question, not this item's, and it is
   an escalation nobody has ratified — recorded here rather than presented as a consequence of the
   spec. `select_jurisdiction` grew a third outcome, `MALFORMED`, to carry it; the code-mutation
   gate is what forced the question, by surviving three mutants on the defaulted timezone the first
   implementation used.
   **Ratified 2026-08-27 as built**, and the status-code question it raises is docketed on item
   5i — see that item's entry, which now names four escalations rather than three. The raise
   stays; what is undecided is the code a caller sees, not whether to escalate.
3. **`NO_JURISDICTION_DATE` was added to `tests/api/siu.py`'s `SIU_REASON_CODES`.** That set is the
   leak negatives' exclusion list and had to grow with the enumeration, but it is the enumeration's
   "complete set" claim, which `CLAUDE.md` scopes to one feature.

**What remains before item 5g closes:** the human's review of the two commits, and then the merge.
Item 5d's idempotency consequence is unchanged and still unaddressed by design: `property_state`
joining the hashed field set answers a byte-identical resubmission under a key remembered before
this item with `409` instead of a `200` replay, bounded to the 24-hour key lifetime and accepted
when the item was specified. Items 5h and 5i are untouched: the 5h preservation test is green and
all three of 5i's `NotImplementedError` escalations stay and stay tested.

**Item 5g is merged to `main`** (merge commit `e7beee2`, `--no-ff`, 39 files, +1585/−267),
2026-08-27, and **item 5g is closed**. This paragraph supersedes every remaining-work list above it
for this item. Branch `phase2/5g-jurisdiction-map` ends at `ef0d906` and is fully contained in
`origin/main` (`git log --oneline origin/phase2/5g-jurisdiction-map ^origin/main` prints 0). The
five specs were approved at `402fdeb`; implementation at `951ff06`, swappability proofs at
`faf8b5f`. **All five digests are byte-identical on `main` after the merge to what they were when
approved** — `jurisdiction_selection` `d71c9be553ce`, `notice_intake` `dc714fa3bf6f`, `resolution`
`e3c3a952c1b1`, `idempotency` `c66ea76c75a4`, `siu_separation` `4aa68f2801c1` — measured on the
merged tree, not carried over from the pre-merge entry. `gauntlet spec list` on `main` after the
merge shows all eleven specs `approved`, none drafted or modified.

Item 5g's numbered entry above now carries a closed marker. **Items 5a through 5f carried no such
marker even though all six were merged** — the `*(Done — see below.)*` convention was applied through
item 4k and then quietly dropped for the 5-series, each of which records its merge in a status
paragraph instead. **Back-filled 2026-08-27**, at the start of item 5h: all six now carry the plain
`*(Done — see below.)*` marker the 4-series used, and the numbered list is once again readable on its
own. Item 5g keeps its richer form naming the merge commit; the two forms are not reconciled, because
the plain one is what 4a through 4k established and inventing merge refs for six closed entries would
be a second convention, not a completed one. The rule the gap taught still stands and is why this
paragraph is annotated rather than deleted: **absence of a marker is not evidence that an item is
open, and the status section is the authority.**

**Both flagged judgment calls are ratified, 2026-08-27.** The determination staying off every
outward surface is now recorded in `ASSUMPTIONS.md` with its basis and with the ordering constraint
it imposes on any later item that wants it visible. The rebuilt `NotImplementedError` in
`shell/rules.py` is ratified as built, and the status-code question it raises is docketed on item
5i, which now names four escalations rather than three. The third call — `NO_JURISDICTION_DATE`
joining `tests/api/siu.py`'s `SIU_REASON_CODES` — needed no separate ratification: that set is the
leak negatives' exclusion list and had to grow with the enumeration it mirrors.

**The merged tree is not byte-identical to the branch tip, and that is deliberate.** `main` carries
two documentation commits the branch does not — `b5d4325` (the `ASSUMPTIONS.md` surfacing entry) and
`555a167` (the item 5i docket and the item 5g ratification line) — landed on `main` before the merge
per this file's own convention that documentation lands on `main` and item work stays on its branch.
`git diff phase2/5g-jurisdiction-map main` is therefore not empty: it is exactly those two files,
+36/−0. No file under `src/` or `tests/` differs, and no spec file differs.

**No post-merge `gauntlet check` was run, and this entry says so rather than leaving the omission to
look like a pass.** The session that closed this item was scoped to documentation and the merge, with
`gauntlet spec list` the only gauntlet command authorized. The last measured green run is the one
recorded above at the implementing ref: 433/433 tests, code mutation 100% with 392 killed, coverage
100% line and 100% branch, worst function 24/25 lines, duplication 0, acceptance **71
reviewed-equivalent** — the same figure as before the item, so nothing moved in the ledger. Those
figures carry to `main` by tree identity on everything a gate reads: the merged tree differs from
`ef0d906` only in `ASSUMPTIONS.md` and `QUEUE.md`. That is **reasoned from tree identity, not
measured on `main`**, and is labelled that way on purpose.

**Item 5h is done and merged to `main`** (merge commit `e8e76c0`, 2026-08-27). An absent loss date is
a domain blocker, not a schema refusal: `Candidate.loss_date` is `date | None`, `date.min` is gone as
a sentinel anywhere, and a notice stating no loss date lands `201`/`PENDED` carrying
`MISSING_REQUIRED_FIELD:loss_date` instead of reaching `TRIAGED` with `0001-01-01` as today's date.
The presence check is its own, and had to be: `_check_loss_date` still reads its blocker off the
future-dated-loss determination and a `NOT_EVALUATED` determination still raises none — which is what
keeps an unsupported jurisdiction from blocking a notice — so the presence blocker could not ride
that path. `_determine_future_dated_loss` checks the loss date before the jurisdiction date, so
`NOT_EVALUATED:NO_LOSS_DATE` outranks `NOT_EVALUATED:NO_JURISDICTION_DATE`. The shell's
`parse_loss_date` returned one `None` for two facts and now returns three outcomes — `LossDateParse`
in `shell/rules.py`, recorded in `PHASE2_DESIGN.md`'s HTTP surface — so absence flows through to the
domain and only an unparseable value is still the schema-invalid `400` with the payload record and
nothing else persisted. An indicator evaluation or a duplicate comparison reached with no loss date
raises `ValueError` rather than growing a `NOT_EVALUATED` enumeration (`ASSUMPTIONS.md`, "Item 5h,
three decisions", decisions 3 and 4). The spec is `features/validation.feature` at blob `8fe71ee`,
549 lines, sha256 `d32ba62f5a3d`, approved at `4836212`; the implementation is `e521e58`. Spec lock
and implementation are separate commits in that order, so the sequence is visible in the log itself.

**`gauntlet check` passes on `main` post-merge, measured on `main` rather than reasoned from tree
identity** — 439/439 tests, coverage 100% line and 100% branch, code mutation **100%, 422 killed, no
survivors**, worst function 24/25 lines, complexity 5/6, duplication 0, protect 3/3 unchanged,
acceptance 11 specs with **71 reviewed-equivalent** and no unreviewed survivors. The acceptance gate
took 1233s. **This deliberately closes the gap the item 5g entry above flags about itself**: that
entry records that no post-merge check was run and that its figures carry to `main` by tree identity,
labelled that way on purpose. These figures were measured at `e8e76c0`.

**Measured blast radius of the spec amendment**, kept here because it is recorded nowhere else. The
table was measured at drafting with `mutation.mutants()` over the file at each ref against
`gauntlet.lock.json`, when the locked digest was `cd571b5dd976`; the amended column has since been
re-measured at the merge ref and confirmed, the locked column has not been re-derived and is carried:

| | locked | amended |
|---|---|---|
| mutants | 180 | 192 |
| unique locators | 180 | 192 |
| boolean-class | 0 | 4 |
| marker-class | 76 | 81 |

Twenty locators gained, eight lost, 172 kept, and **no approval was disturbed**: all 31 live mutant
approvals on this file sat on kept locators and not one signature moved. Counted against the ledger
at the merge ref, `features/validation.feature` still carries 31 of the project's 71 mutant
approvals, and the eleven specs measure 756 mutants in total.

**One harness finding, and it is why the mutation figure above can be trusted.** The first full
`gauntlet check` on the implementation reported `mutation … 98.58%, 416 killed, 6 unresolved` and
**passed** — 98.58% is far above the 90% floor, so the six were printed as diagnostics on a green
gate and nothing asked for a second look. That figure was mutmut's stale `mutants/` cache
under-reporting: cleared and re-run cold, the same tree without the guarding unit test shows **12**
survivors, and with the test 0 survivors at 422 killed. It is the first measured instance of the
false-PASS direction that `docs/harness-findings.md` says goes unnoticed — see "A mutation score is
only meaningful from a cold run when the commit adds or removes code", extended there with this
measurement. Practical consequence for the next session: **clear `mutants/` before quoting any
mutation score, including a green one.**

**Carried to item 5i, decided at item 5h's drafting and deliberately not built:** a scenario for a
reviewer supplying a missing loss date at resolution. It is the composition of two mechanisms already
proved — `jurisdiction_selection.feature`'s merged-view rule and `resolution.feature`'s
supplying-a-missing-field rule — over a different field, and it cannot be expressed in
`validation.feature` at all, which has no notice, no state and no endpoint in its vocabulary. If it
is wanted stated explicitly it belongs in `resolution.feature`, which item 5i already reopens.

**Item 5i is done and merged to `main`** (merge commit `5ae5762`, 2026-08-28). Both deployment
faults — a carrier present in the identity reference whose rules entry will not resolve, and this
deployment's own jurisdiction map naming no timezone or one the system cannot resolve — are answered
`500` with a machine error code from a new closed shell-side enumeration (`shell/faults.py`:
`CARRIER_RULES_UNRESOLVABLE`, `JURISDICTION_MAP_UNUSABLE`). One typed fault is raised from
`shell/rules.py` and answered by whichever endpoint catches it, because the fault is one fact and the
answer is not: intake receipts the submission and keeps its payload with its own reference and the
code, creating no notice and remembering no key, while a resolution rolls the whole transaction back
including the payload record appended before the configuration is read. `_require_notice`'s raise
became the ratified `404`; the unparseable resolution loss date moved to the schema boundary beside
`actor_id`, taking the merged-view parse in `_loss_date_of` with it as unreachable. **All four
`NotImplementedError` raises are gone and none remains anywhere in `src/`.**

**`gauntlet check` passes on `main` post-merge, from a cold cache with `mutants/` cleared first**:
453/453 tests, code mutation 100.0% at **422 killed**, acceptance 11 specs, **0 surviving**, **75
reviewed-equivalent**, 1439.7s. The cold run matters here rather than being ceremony — a warm score
is only meaningful when the commit neither adds nor removes code (`docs/harness-findings.md`), and
this one added a module, two endpoint answers and a database column.

**The code-mutation count did not move, and that is ruling 6 holding rather than a gap.** 422 before
the implementation and 422 after it, against a 493-line change: `mutmut`'s source scope is
`src/claimgate/domain/` alone and this item is shell-side by ruling, so a *risen* count would have
been the finding. The only `domain/` change was two comments claiming the shell escalates what it
now answers. `RULESET_VERSION` is untouched. Recorded in `docs/harness-findings.md`.

**Four mutant approvals landed at `b31e341`, before the merge, under two scenario-scoped reasons —
one reason per argument, not one per mutant.** Both pairs are substitutions between two rows that
already agree on their outcome, which each scenario's own comment named in advance as a measured and
accepted cost:

| file | line | mutation |
|---|---|---|
| `idempotency.feature` | 261 | `this deployment is configured correctly` -> `the carrier's rules entry cannot be resolved` |
| `idempotency.feature` | 262 | `2026-06-01` -> `not-a-date` |
| `resolution.feature` | 229 | `adjuster-4471` -> `absent` |
| `resolution.feature` | 228 | `2026-06-02` -> `not-a-date` |

`idempotency.feature`'s reason is that the schema boundary is read before the deployment
configuration, so a first attempt whose loss date does not parse is `400` whether or not the
carrier's rules load, neither failure remembers the key, and both retries create. `resolution.feature`'s
is that a body this endpoint cannot read is refused before the notice is read, whichever half is
unreadable. **The ledger now holds 75 approvals**, up from 71.

**Spec mutant counts, re-measured against the engine after implementation** and unchanged from the
drafting prediction: `resolution.feature` 133, `notice_intake.feature` 51, `idempotency.feature` 46,
project total 813 (from 756). No approval on any of the three predates this item.

**Five implementation shapes are recorded in `ASSUMPTIONS.md`, "Item 5i implementation shapes"** —
none is a rule, and two are visible on a surface: `payload_records.error_code` as a new nullable
column, `error` on both response types and both serialization allow-lists (the allow-list test
forced that decision rather than defaulting it), which half of the jurisdiction fault each test layer
exercises, how the carrier fault is produced, and why `_loss_date_of` is deleted rather than guarded.
**That entry also records that `shell/notice_intake.py` and `shell/resolution.py` now sit at exactly
250 of 250 lines** — neither has room for another comment paragraph, and the next item touching
either splits it first, on `messages.py`'s precedent.

**Item 5j is next, and it is the last item in the queue.** Its only sequencing precondition was item
5h's implementation, merged at `e8e76c0`; it was independent of 5i, so the order between them was a
free choice and 5i went first. Its entry above already carries the 2026-08-27 correction to its own
premise — the both-absent case is reachable from the shell today, so what 5j closes is that nothing
*asserts* which reason the determination names, not that the case cannot be reached — and asserting
it in a shell or unit test instead was considered and declined there, with the reason. Its entry
also now carries a rider added at this item's close: the reopening of
`jurisdiction_selection.feature` must also correct that file's line-29 comment, which still calls
the unresolvable-rules case item 5i's undecided status code. That comment is the one known survivor
of item 5i's stale-claim sweep, left deliberately because correcting it costs an approval cycle that
5j's reopening pays anyway. **Blast radius was unmeasured at the time this was written; it was
measured at drafting and the figures are in the close-out below.**

**This session ended at the save point**, on `main` with a clean tree and nothing in flight. There
is no open branch: item 5i's `reopening/5i-deployment-fault-status-codes` is merged and remains on
`origin` at `b8b5268`, as does `reopening/5h-absent-loss-date` at `e521e58`; deleting either is
optional and nothing depends on them.

**Item 5j is drafted and open on `reopening/5j-both-absent-precedence`, tip `4ad23e8`, 2026-08-29.**
This supersedes the paragraph above where it says there is no open branch. Three commits, spec only —
nothing under `src/` or `tests/` is touched:

- `4db7568` corrects the line-29 comment's claim that a carrier the identity reference recognizes
  whose rules cannot be resolved is item 5i's undecided status code. It was decided and merged
  2026-08-28 — `500` with `CARRIER_RULES_UNRESOLVABLE` — and the sentence's second half is kept
  rather than dropped, restated as the scope choice it now is: the carrier's rules resolve above the
  jurisdiction in `shell/notice_intake.py`, so a carrier whose rules will not load never reaches
  selection and such a scenario would have no selection left to assert. Measured comment-inert — the
  locator list is byte-identical to the locked file's.
- `4f554f4` adds Rule 3's both-absent row: an unsupported property state with no loss date records
  `NOT_EVALUATED:NO_LOSS_DATE`, closing the state item 4k's shape describes, where a reordering of
  the two checks fails no test and mutation does not reorder statements. The loss date leaves its
  fixed `Given` for an `Examples` column, because a fixed `Given` above an outline is never mutated
  and the row's own subject stated there would have been protected by nothing.
- `4ad23e8` retitles that outline. The old title described rows 1–2 and misdescribed the new row,
  which reports no loss date at all. Done now because it is only free now: this file carries zero
  mutant approvals and the spec re-approval is already owed, so the 15 locator moves cost nothing;
  once approvals land on this scenario it is never free again.

**The spec is drafted, not locked, and the next action is the human's `gauntlet spec approve`.**
Export for review: `git show 4ad23e8:features/jurisdiction_selection.feature` — 357 lines, blob
`301bbfe`, sha256 `3201e3142700`.

**Two gate failures are expected on this branch and neither clears from the agent's side.** The
acceptance gate is red at its approval stage, because the spec is modified since it was approved —
guaranteed by the separate-commits rule, which puts spec lock and implementation in that order and so
makes a red state between them the normal case rather than a defect. The test gate is red at
**453/454**: `tests/acceptance/conftest.py`'s `set_loss_date` has no `absent` convention, so it
assigns the literal string, the notice is refused at the schema boundary, and no notice exists for the
row to read. Measured, and it is exactly the new row and exactly that cause — the other 453 pass, so
the widened table and the moved `Given` broke nothing.

**Measured blast radius**, `mutation.mutants()` over the file at each ref against `gauntlet.lock.json`:

| | locked (`120ebd7`) | comment only | drafted (`4ad23e8`) |
|---|---|---|---|
| mutants | 48 | 48 | 55 |
| unique locators | 48 | 48 | 55 |
| boolean-class | 6 | 6 | 6 |
| marker-class | 6 | 6 | 6 |
| locators vs the lock | — | byte-identical | 8 lost, 15 gained, 40 kept |

The 8 lost and 15 gained are the whole of that one scenario, measured rather than inferred from the
totals. **No approval is disturbed, which is what made the shape choices above affordable:** this file
carries **0 of the ledger's 75 mutant approvals**, measured against the lock. The retitle moved only
the scenario half of its 15 locators — across `4f554f4..4ad23e8` the `kind|context` halves and all 55
signatures are identical in order.

**One survivor is predicted, simulated and not measured** — survivors cannot be measured until the
spec is approved and the step exists. `property_state: GA->FL` on the new row, inert because with no
loss date the determination is the same wherever the property is. Drafted approval reason, for the
human at implementation: *with no loss date the determination does not depend on where the property
is, which is the precedence this row exists to assert.* Three alternative shapes were measured and
declined; the two that simulate zero survivors buy it either by restating Rule 2's subject inside
Rule 3 or by putting the unsupported-jurisdiction half back into an unmutated fixed `Given`, and the
third — spelling the new row's property state `absent` instead of `GA` — costs a second survivor,
because Rule 2 makes those two the same marking deliberately.

**What remains.** The human's spec approval; then implementation, which is the `absent` convention in
`conftest.py`'s `set_loss_date`, the `domain/validation.py` comment at lines 127–130 updated to cite
the row instead of calling itself the ordering's only protection, and this section's close-out. No
`RULESET_VERSION` bump: no rule's behaviour changes, on item 5i's precedent. `domain/validation.py`
sits at 203 of 250 lines, so neither 250/250 shell module is involved and no split is triggered.

**Item 5j is done and merged to `main`** (merge commit `806f403`, 2026-08-30). This supersedes both
the "Item 5j is next" paragraph and the drafted-state paragraph above; where they disagree with this
one, this one is current.

**The refs, in the order the log carries them** — the sequence is the point, not decoration, because
it is what makes lock-then-implement visible rather than merely asserted:

| ref | what it is |
|---|---|
| `4ad23e8` | the spec as reviewed — 357 lines, blob `301bbfe`, sha256 `3201e3142700` |
| `981f8d3` | the human's spec approval, `gauntlet.lock.json` alone |
| `2d89ff8` | the implementation |
| `fecde95` | the human's mutant approval, `gauntlet.lock.json` alone |
| `806f403` | the merge, `--no-ff` |

**One survivor was approved, and it is the rule showing through rather than a gap in it.**
`property_state` `GA->FL` on the row carrying no loss date, recorded reason: *with no loss date the
determination is the same wherever the property is, which is the precedence this row asserts.* The
ledger goes from 75 to 76, and this file holds exactly one of the 76.

**`gauntlet check` passes twice, both from a cold cache with `mutants/` cleared first, and both
measured rather than reasoned from tree identity.** On the branch at `fecde95`: 454/454 tests,
coverage 100% line and 100% branch, code mutation 100.0% at 422 killed, worst function 25/25,
complexity 5/6, duplication 0, protect 3/3, acceptance 11 specs with **76 reviewed-equivalent** and
no surviving mutants — acceptance 1220.9s, run 1237.1s. On `main` post-merge at `806f403`: the same
figures, acceptance 1198.8s, run 1212.5s. The two documentation commits that follow the merge
(`96b1595`, `2f906bf`) are documentation only and were not covered by that run, which is stated here
rather than left to look like coverage they do not have.

**This closes the queue. Item 5j was the last item, and every item in it is done.** A session
arriving here with no memory of the work should conclude exactly this: phase 2 is complete, nothing
is in flight, there is no open branch, and no gate is red or waiting on anyone. The reopening
branches remain on `origin` — `reopening/5j-both-absent-precedence` at `fecde95` alongside 5h's and
5i's — and deleting them is optional, as nothing depends on them.

**Whatever comes next starts with a new queue entry, not with this section.** The numbered list above
is a closed record of phase 2 and should be read as history; appending work to it, or reopening an
item to carry something new, would make a finished record look open again. The per-item paragraphs
say what each item decided and why — this one deliberately does not repeat them.

**Phase 3 planning is open as item 6 above, and it is the only thing open.** That item supersedes
this section's closing claim that nothing is in flight — a claim true when written at phase 2's
close, and now true only of code: no branch exists, no spec is drafted or awaiting approval, no
gate is red or waiting on anyone, and no implementation item is queued. The next action belongs to
the human and the advisor rather than to a coding agent: a planning session producing `ROADMAP.md`
and `PHASE3_DESIGN.md`. A coding agent's next work arrives only after both are ratified. Until
then there is nothing for one to implement, and an item queued ahead of those documents would be
scoped against the boundary they exist to draw.

**2026-09-01: item 6 is half delivered, and three documents were corrected.** `ROADMAP.md` is on
`main`, status sentence "drafted, awaiting human ratification"; the human ratifies by instructing a
commit that removes that sentence, and `PHASE3_DESIGN.md` is not started until then. Same session:
`README.md`'s status section was a phase stale — it described phase 2 as unbuilt and quoted 67
approvals and four specifications, both exact at `0114b45` on 2026-08-21, against 76 and 11 today;
`PHASE2_DESIGN.md`'s claim that `ROUTED`/`SUPERSEDED`/`WITHDRAWN` were "defined now" was false
against the code and is corrected there; and the policy administration adapter is phase 3, so every
"phase-2 adapter" reference in `ASSUMPTIONS.md` and in this file's closed entries is history and
is annotated as such in `ASSUMPTIONS.md`. In code, nothing is in flight: no branch, no spec, no red
gate. The next action is the human's ratification of `ROADMAP.md`.

**2026-09-01, later: `ROADMAP.md` is ratified.** The human read the committed file at `42c6903`
and ratified it; this commit records that in the roadmap, `README.md` and item 6. Item 6's
remaining deliverable is `PHASE3_DESIGN.md`, which is the human's and the advisor's work, not a
coding agent's — the next coding session arrives with that document ratified and a phase-3 queue
item written against it. Nothing is in flight in code: no branch, no spec, no red gate.

**2026-09-01, later still: `ROADMAP.md` amended once after ratification.** Duplicate detection
had no shell caller and the roadmap placed its wiring nowhere; the existing-claims read is now
phase 3's, and the human re-ratifies that paragraph from the committed file. Found while reading
the shell for `PHASE3_DESIGN.md`, which also established that rule evaluation runs outside every
transaction on the intake path and inside the single transaction on the resolution path — the
first structural decision `PHASE3_DESIGN.md` must make. Nothing in flight in code.

**2026-09-01, evening: `PHASE3_DESIGN.md` is drafted and awaiting ratification.** Two ports
(policy, claims), every answer three-valued with an as-of instant, calls between the two
transactions on intake, the resolution path restructured to match, policy identification moved
out of the domain (reversing 4b and 4j), the continuous-coverage derivation moved into it,
two new append-only attribute tables, per-carrier bindings, and a two-shape swappability proof.
The human ratifies from the committed file; then phase-3 queue items are written in the order the
design's last section gives. `ROADMAP.md`'s 2026-09-01 amendment also awaits the human's
re-ratification of its one changed paragraph. Nothing in flight in code.

**2026-09-01, closing the planning day: item 6 is complete.** `ROADMAP.md` (amended paragraph
included) and `PHASE3_DESIGN.md` are both ratified from committed files at named refs, recorded in
the files. Items 7a–7i are queued above; 7a is next and is implementation, so it opens in a fresh
coding session with a spec draft for `features/coverage_verification.feature` reviewed by the human
before anything is built. Nothing is in flight in code, and the full gate was green at `ee8b4b3`
earlier today: 454 tests, mutation 100%, 11 specs, 76 reviewed-equivalent.

**2026-09-03: item 7a is open; the specification is proposed and awaits the human's approval.**
Branch `phase3/7a-term-in-force` off `main` at `2b35dd7`, tip `dfb1284`, pushed. One commit:
`features/coverage_verification.feature` exactly as the advisor supplied it — 142 lines, sha256
`b9bcedcb3cfa…`, both confirmed from `git show dfb1284:features/coverage_verification.feature`, not
from the working tree. Measured through the mutation engine at that ref: 78 mutants, 40 sibling swaps
(every one an `Examples` cell in the four outlines) and 38 markers (every one a quoted literal in the
six single-probe scenarios), matching the advisor's 78/40/38 exactly. The advisor's zero survivors is
a simulation against a model of the rule, not a measurement — survivors cannot be measured until the
spec is approved and step definitions exist. The spec is drafted, not locked: `gauntlet check` on the
branch is expected to stop at the acceptance gate's approval stage until the human exports at
`dfb1284` and approves — the human's command, never a session's — and that condition is the
separate-commits rule working, not a defect to retry. Nothing else is built: no domain rule, no step
definitions, no unit tests. After approval, implementation goes on the same branch, with two
requirements the simulated marker kills depend on: step definitions parse every quoted date strictly
(an unparseable date is a step error, never a skip or a default) and assert the determination and
reason strings exactly. `RULESET_VERSION` does not bump at this item — the rule has no caller until
7f. Measurement note: the project `.venv` does not import `gauntlet`, so `measure_mutants.py` ran
with `GAUNTLET_SRC=~/Code/agent-gauntlet/src` (engine at `aa29c42`), the fallback the script itself
documents.
