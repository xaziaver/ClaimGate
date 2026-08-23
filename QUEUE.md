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

5a. **Carrier configuration: the loader, and the rejection of an unrecognized value.** Phase 1 moved
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

5b. **Instant-to-jurisdiction-date resolution, as its own named function with its own scenarios.**
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
    receipt, and the audit entries those transitions produce.** The core of phase 2 and the largest
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

5d. **Idempotency on `POST /notices`.** `Idempotency-Key` as a header, uniqueness on
    `(carrier_code, idempotency_key)` enforced by a database constraint rather than a
    check-then-write, 24-hour expiry, replay returning `200` with the original `notice_id` and
    receipt timestamp but the notice's current state, replays kept out of the audit trail. All
    specified in `PHASE2_DESIGN.md`; this item builds it.

    Sequenced after 5c because the constraint is a real database constraint and there is no schema
    to put it on until 5c exists. Its own reason for being separate from business duplicate
    detection is in `PHASE2_DESIGN.md` and should not be re-litigated here: a bare network retry is
    indistinguishable, to the duplicate matcher, from a genuinely separate loss on the same policy
    inside the match window.

5e. **`POST /notices/{notice_id}/resolution`.** The `PENDED → TRIAGED` transition, `USER` actor
    only, `409` when the notice is not currently `PENDED`, `200` when the supplied data clears every
    blocker, `422` with the current blockers when it does not — and, in that last case, a notice
    that stays `PENDED` while an audit entry is still written with `outcome=REFUSED`. A refused
    resolution attempt is an audit event, not a non-event.

    **Supplemental data never mutates the stored payload**: each resolution writes its own immutable
    payload record with its own hash, linked in arrival order, and the current view is derived from
    that sequence. Tolling is recorded and never computed — precise UTC pend and resolution-received
    timestamps, no tolling logic, and no field named `tolling` anywhere in phase 2.

5f. **SIU separation: the separate table, the write-side event trail, the allow-list serializer's
    negative assertions, and SIU computation wired in at all.** `PHASE2_DESIGN.md`'s SIU section is
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

5g. **The jurisdiction map, and the two swappability proofs.** Statutory configuration is a real map
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


