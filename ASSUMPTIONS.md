 # Assumptions

ClaimGate is a general FNOL intake product, configured per carrier: a managing agency running
several carriers on several policy administration systems runs several configurations in
parallel; a single carrier or MGA runs one. It ships configured for Florida residential property.
This project has no access to any carrier's or policy administration vendor's internal systems or
data, so every rule here rests on a public source or a stated assumption. Every entry below states
what was assumed, why, and what would correct it — this file is the difference between a gap that
reads as identified and one that reads as missed.

**Provenance convention, proposed 2026-08-14.** A dated decision below should carry a provenance
tag, not a bare "decided": **advisor-recommended, human-ratified** when it rests on an argued chain
from stated premises to a conclusion — inspectable on its own terms, and wrong if a premise is
wrong or the argument doesn't follow — that an advisor proposed and the human then approved. A
decision resting on the human's own direct carrier or claims-handling experience, not derived from
any chain of reasoning stated in this file, is tagged **human, from carrier experience** instead —
this file cannot self-check that kind of claim the way it can check an argument, so the tag says
which kind of trust the entry is asking for. Entries predating this convention carry a bare
"decided" and should be read as unclassified, not silently reinterpreted as either tag.

## docs/decisions.md audit

All seven entries classified as: cites an external source; records a rationale; asserts an
unverified or false fact; restates the rule; rationale is orphaned (justified relative to a rule
that has since been deleted); or rationale contradicts its own rule. Severity order, worst first:
a rationale that argues against the rule it justifies, an unverified-or-false assertion (a reader
cannot tell it apart from a grounded one), an orphaned rationale (was coherent, isn't anymore), a
bare restatement (empty but at least not misleading), a real rationale, a real citation.

**Headline finding: zero of the seven entries cite an external source.** Nothing in this project's
threshold decisions is grounded in a statute, an industry study, or carrier data. Full counts:
external source — 0; records a rationale — 2; asserts an unverified or false fact — 2; restates
the rule — 1; orphaned — 1; rationale contradicts its own rule — 1.

- **Rationale contradicts its own rule (1 — worst category):**
  - *Validation reporting window: 365 days* — "carriers accept late FNOL" is factually correct
    and argues *against* the 365-day rejection gate it was written to justify. Not a false fact,
    not a restatement — a correct note attached to a rule that does the opposite, and it survived
    the life of the project without anyone noticing. (Now removed; late notice is non-blocking.)
- **Asserts an unverified or false fact (2):**
  - *Recent policy inception threshold: 30 days* — "a standard fraud indicator." Asserts an
    industry basis with nothing behind it. This is the only entry in the file that *sounds*
    externally grounded, and it is not.
  - - *Policy number LOB prefixes: HO, AU, CP, CA, GL* — "the lines of business this carrier
    actually intakes." A statement of fact about a specific carrier's book, and false for the book
    it was written against: residential property only, no auto, no commercial (see Finding 5
    below). Whose book it was is no longer recorded here and does not need to be — the defect is
    asserting a carrier fact in the domain at all, which is what item 4b narrowed and what the
    `POLICY_NUMBER_PATTERN` entry below still carries.
- **Restates the rule (1):** *Theft low-severity threshold: $500* — restates what happens under
  and at $500 with no justification for the number itself.
- **Orphaned (1):** *Duplicate detection window: 3 days* — "tight enough to avoid false positives
  on genuinely separate losses" is precision-only, and it was written when a duplicate match
  blocked a notice. Duplicates are now non-blocking evidence, which flips the cost asymmetry: a
  false positive costs a reviewer a glance, a false negative means a duplicate claim opens in the
  policy system. The window is tuned against a model that no longer exists. Milder than the 30-day
  SIU threshold — the reasoning is coherent, just obsolete — but the same failure shape: a
  threshold justified relative to a rule that was deleted. Recorded with the duplicates defects
  below.
- **Records a rationale (2):** *SIU late-reporting threshold: 30 days* (also orphaned in
  substance — see "Domain defects found" below — but classified here because its defect is
  tracked separately as a legal-exposure issue, not merely a stale citation); *LOB-vs-loss-type
  cross-validation: deferred*.

## Carrier estate — no internal access to any

ClaimGate has never had access to a carrier's or policy administration vendor's internal systems
or data. Nothing below was confirmed against a live book.

- **Carrier codes.** The 4-character `carrier_code` values in `PHASE2_DESIGN.md` are placeholders.
  Real codes substitute at integration; they are configuration, not behaviour.
- **Policy number format.** Assumed, not known, and it varies between real carriers. Currently a
  domain-layer regex, which is the open defect the `POLICY_NUMBER_PATTERN` entry below records.
- **NAIC group codes.** The schema must tolerate a null group code. A member-owned reciprocal may
  be grouped by management rather than ownership, so group membership does not follow from a
  shared administrator and cannot be inferred.
- **Book scope.** The shipped configuration assumes Florida residential property only. A
  configuration choice, not a finding about any carrier.
  
## Carried requirements — decided, not yet built

- **Timezone-correct "now."** The phase-2 API shell must receive a timezone-aware UTC instant and
  convert it to a calendar date in the jurisdiction's timezone before calling any domain function.
  The domain never receives a date derived from server local time. The conversion is a named,
  separately-specified function needing scenarios for: an instant at 01:00 America/New_York
  resolving to the Eastern date and not the UTC date; an instant at 22:00 Eastern likewise; and
  both DST transition boundaries. A zone behind Eastern produces false `LOSS_DATE_IN_FUTURE`
  flags; UTC produces the inverse error, accepting a date that is genuinely future locally.
- **Unevaluated is not negative.** General rule, not SIU-specific, to implement when the SIU
  reopening comes: any derived indicator or attribute whose required input is unavailable is
  recorded as `NOT_EVALUATED` with a reason code. It is never defaulted to false, absent, or any
  other value that reads as a determination. "We checked and found nothing" and "we never checked"
  are different facts — if a claim is later determined fraudulent, a record asserting the second
  as the first is a false record in a file a regulator or a court can read. Applies to any phase-2
  attribute whose real inputs don't arrive until phase 3.
- **Recent-inception reason-code precedence when both required inputs are absent.** When
  `compute_siu_indicators` is called with no recent-inception threshold configured *and* no policy
  inception date known, the recent policy inception indicator resolves `NOT_EVALUATED` with reason
  `NO_POLICY_INCEPTION_DATE`, not `NO_THRESHOLD_CONFIGURED`. Principle: the reason code names the gap
  that would still block evaluation if the other were closed. With no inception date known,
  configuring a threshold changes nothing — reporting `NO_THRESHOLD_CONFIGURED` would name a gap
  whose closure would not help, and would imply a fix that is not one. The missing input outranks
  the missing rule. This was originally an accident of implementation order, not a decision: the
  code's pre-existing `inception is None` check ran first because it was already there from before
  this reopening; the new `threshold_days is None` check was appended after it to satisfy mypy's
  type narrowing, with no thought given at the time to which reason code should win. Reviewed and
  confirmed correct against the principle above on a later pass, not left as the accident that
  produced it. No scenario specifies this in `siu_indicators.feature` — the combination is
  unreachable in the shipped configuration, where the recent-inception threshold is always a real,
  kept value of 30. Reachable in phase 2 once thresholds come from jurisdiction config rather than a
  fixed value — see PHASE2_DESIGN.md's SIU handling section.
- **Severity assignments for the new perils (`hurricane`, `sinkhole`, `roof_leak`) — decided
  2026-08-13, documentation-only session on `main`, no branch/spec/implementation yet (`QUEUE.md`'s
  merged item 4c).** `sinkhole` is `HIGH`: Florida prescribes an investigation process for sinkhole
  claims involving engineering and geological testing (627.707 — see `STATUTORY_REGISTER.md`), and
  it is low-frequency, high-cost, specialty-handled work. `roof_leak` is `STANDARD` —
  operationally distinct in Florida because of the separate roof deductible and the litigation
  environment around it, but neither of those is a severity signal at intake. `hurricane` is
  `STANDARD`, and this answer is a symptom rather than a conclusion: severity is the wrong axis for
  catastrophe. During a declared event, hurricane claims go to catastrophe staffing with different
  workflows and reserving, not to the queue an injury claim goes to, and coding hurricane `HIGH`
  would flood that queue exactly when volume spikes hardest.
- **Catastrophe handling is a deliberate non-goal for this phase, not an oversight — the reasoning
  behind `hurricane`'s `STANDARD` severity above, not a separate decision.** If it is ever built, it
  is a parallel attribute, the way SIU indicators are: `PHASE2_DESIGN.md` already establishes that
  queue, severity, SIU indicators, and duplicate candidates are attributes rather than states, and
  `QUEUE.md` item 1 existed precisely because SIU had been crammed into queue routing. Putting
  catastrophe into severity would repeat that mistake in a different field.
- **Loss amount is removed from the severity rule entirely, not replaced with a better threshold —
  decided in the same session.** The current rule applies an amount test to theft alone, the peril
  where magnitude matters least, and omits it from fire, where it matters most; it was never
  coherent, so the `$500` figure was the wrong thing to argue about. The deeper reason:
  `reported_loss_amount` at intake is a reporter's guess, not an appraisal — frequently absent,
  systematically wrong, and revised within days, so a severity scheme keying on it keys on the least
  reliable field in the record. Severity derives from loss type alone. No statute or industry
  standard supports this; it is a carrier policy decision. What would reverse it: a validated
  exposure figure at intake, not what the caller said. Supersedes the `$500` threshold recorded
  under "Undocumented phase-1 thresholds" below — that entry is now moot, not merely unsourced.
- **Advisor-recommended, human-ratified, 2026-08-14: the `low` severity band and its `fast_track`
  queue are retired, not left as reachable dead code.** Severity is `standard` or `high`; queues
  are `standard` and `complex`. The theft-amount rule above was the only producer of `low`, and no
  peril is a credible fast-track feeder — `roof_leak` least of all, given Florida's separate roof
  deductible and the litigation environment around it. What would reverse this: a genuine
  complexity signal captured at intake — single-trade damage, no additional living expense, no
  injury, no coverage question — which is what a real fast-track band keys on, not amount and not
  peril, and which needs structured damage capture the FNOL record does not have.
- **Advisor-recommended, human-ratified, 2026-08-14: the end-to-end outline keeps its `loss_amount`
  column after loss amount stops affecting severity.** The surviving mutants on that column are the
  proof of the new rule, not incidental: a mutation that changes the reported amount without moving
  severity, approved as equivalent, is the spec demonstrating "severity derives from loss type
  alone" in a form mutation testing can verify. Dropping the column would leave the spec merely not
  contradicting the rule instead of demonstrating it. `Candidate.loss_amount` stays on the model as
  captured-not-used; `assign_severity` loses the parameter entirely. Recording the distinction
  explicitly so a later reader doesn't mistake the unused field for dead code and delete it — it
  earns its place by what the spec demonstrates with it, not by being read anywhere in `triage.py`.
- **The blocking criterion: a missing field blocks intake only if the information is actionable and
  crucial to the FNOL process or to the carrier's exposure — decided 2026-08-16, documentation-only
  session on `main`, no branch/spec/implementation yet (`QUEUE.md` item 4g).** Stated as a general
  test because it already explains two decisions this project made separately, without ever writing
  the test itself down. Late notice does not block intake: whether a loss was reported inside the
  statutory window is a coverage determination made downstream on the facts of prejudice and
  tolling, not something intake can act on (`QUEUE.md` item 2; the same line is drawn in
  `validation.feature`'s comment on the point). `flood` is a recognized loss type, not a blocked
  one, even on a book that routinely excludes or sub-limits flood — the notice is fully intelligible
  and actionable for intake and adjuster assignment regardless of what eventually pays; whether it's
  covered is answered later, on policy language, not at intake (item 4e's merge; `validation.feature`'s
  comment that the recognized set is what intake can interpret, not what the policy covers). Both
  facts — timing of notice, eventual coverage — are crucial to the *claim* and immaterial to whether
  *FNOL can proceed*, which is the distinction the test is drawing: information the carrier will
  want eventually is not, by itself, a reason to block today. This is the test to apply when
  Section I's own required fields are specced (`QUEUE.md` item 4g's note that Section I needs model
  fields — location, damage description — before it can be scoped at all): a field blocks only if
  its absence leaves intake with nothing actionable, not because the carrier will eventually need
  the information.
- **Carrier-varying rules are caller-supplied configuration with no domain default —
  advisor-recommended, human-ratified, 2026-08-17.** ClaimGate is a product configured per carrier,
  not a system built for one estate. A company running three carriers on three policy administration
  systems runs three configurations in parallel; a single MGA runs one. Where a rule genuinely varies
  by carrier, it becomes configuration rather than a domain constant.

  **Configuration is not a default.** `CLAUDE.md`'s first standing constraint — never default a
  threshold, state name, status code, or retention behaviour — applies to configuration values
  unchanged, and this project has applied it twice already: item 2 removed both SIU threshold
  defaults so every call supplies them, and item 3 removed `DUPLICATE_WINDOW_DAYS` so `window_days`
  is a required parameter with no fallback. A configurable value carrying a shipped default is a rule
  nobody approved, reached by omission. The pattern is: required, caller-supplied, no fallback,
  stated in the scenario's Given step the way `siu_indicators.feature` states its thresholds.

  An unsupplied configuration is a caller contract violation, not a business outcome. It has no
  analogue to `siu_indicators.feature`'s "no threshold configured" scenarios: an indicator can
  meaningfully resolve NOT_EVALUATED, while validation must return blockers or none.

  **Not everything becomes configurable.** A rule is configuration only where carriers genuinely
  differ. Where it follows from what a notice of loss is, it stays in the domain. Making everything
  configurable moves the assertions out of the specification and leaves the gates exercising
  plumbing. Each rule that becomes configurable gets its own item, spec lock, and measured blast
  radius — not one sweeping pass.

- **Item 4g's Section II required-field set is carrier configuration; `incident_description` is not —
  advisor-recommended, human-ratified, 2026-08-17. Supersedes the 2026-08-16 decision that
  `claimant_contact` is non-blocking while `claimant_name` blocks.** That decision fixed a carrier
  policy choice in the domain. Under the entry above, `claimant_name` and `claimant_contact` each
  become caller-supplied required-or-not configuration with no default, which dissolves the question
  rather than answering it: a carrier holding claimant details at first notice and one that does not
  are both expressible, and there is no shipped answer to be wrong about. `incident_description`
  stays required unconditionally — without it the record is not a notice of loss, only an assertion
  that one exists, and nothing downstream can be reserved, assigned, or investigated from it. Cost of
  holding it in the domain: a carrier wanting to accept description-less liability notices needs a
  spec change, not a configuration change. Accepted deliberately.

  The case that produced this: a liability notice frequently arrives with the claimant unidentified
  or unreachable — a guest hurt on the pool deck who left, a delivery driver who slipped and was
  never named. FNOL proceeds; it does not finish. Blocking would PEND a real and not-rare notice for
  information intake cannot act on, the same failure shape item 4h identified from the other
  direction. Advisor's basis is FNOL practice, where claimant details are captured "if known" — not a
  primary source, and no primary source of the kind `STATUTORY_REGISTER.md` requires exists for a
  practice question.
- **ClaimGate is a general product, not a build against one named estate — stated 2026-08-17.**
  It was originally designed against a specific three-carrier Florida residential property estate.
  That is no longer the target, and this file no longer names it: the references were removed
  rather than marked historical, so that nothing here reads as a live carrier relationship.
  Four consequences outlive the removal:

  - Item 4b's `HO`-only prefix set was justified as "a carrier scope decision — `HO` is what's
    confirmed today," and what confirmed it was that estate's public materials. The behaviour is
    unchanged and still defensible as the shipped configuration's scope, but the justification is
    now a configuration choice rather than a finding. `features/validation.feature`'s comment on
    that rule was rewritten to say so, which is why its approval was renewed on this date.
  - The `POLICY_NUMBER_PATTERN` open decision below is strengthened rather than changed: with no
    named estate, a domain-layer regex asserting one carrier's number shape has nothing left
    justifying it, and the structural fix that entry already prefers — the pattern belongs to the
    adapter layer, not to a domain parameter — is now the only defensible one.
  - The removed section held this project's only claim explicitly verified against a primary
    source and flagged as a different confidence class from its neighbours: three NAIC company
    codes checked against FLOIR filings. Deleting it costs the worked example of that discipline.
    `STATUTORY_REGISTER.md` carries it instead, which is the better home for it anyway.
  - Git history retains every removed name. This removal is presentational, not erasure, and no
    history rewrite is planned — the ledger keys on file digests rather than commits, so a rewrite
    would not break it, but the disruption buys nothing a disclaimer does not already cover.

  Revisiting 4b's prefix set as configuration is a new queue item, not a correction to a closed one.
- **A carrier configuration crosses into the domain already resolved, so the domain has no
  unrecognized-configuration case — advisor-recommended, human-ratified, 2026-08-17.** Item 4g's
  `claimant_name` and `claimant_contact` requirements reach the domain as booleans, not as strings
  the domain interprets. Parsing, validating, and rejecting a malformed configuration value is the
  caller's job, above the domain boundary; by the time the rule runs, the question is already
  settled. So no scenario specifies what an unrecognized configuration value does, and none should
  — there is nothing there to specify.

  This is not the same as `loss_type` or `notice_type`, which are field values arriving from a
  reporter and therefore have genuine unrecognized cases with their own reason codes. A
  configuration is supplied by the integrator, not the reporter. Item 3's precedent applies to the
  boundary rather than to the domain: an unreachable caller-supplied value is a caller contract
  violation, not a business outcome, and it does not earn a reason code.

  **Consequence to hold when this reaches phase 2.** The adapter layer becomes the only thing
  standing between a mistyped configuration file and a silently wrong required-field set, and no
  gate in this project currently watches that boundary — mutation cannot reach it, because the
  engine only swaps between values a column already contains. Whatever loads a carrier
  configuration needs its own rejection of unrecognized values, specified where that loading
  happens. Recorded here so it is a known gap rather than a discovered one.

## Undocumented phase-1 thresholds

- **365 (`REPORTING_WINDOW_DAYS`).** Its only rationale was "carriers accept late FNOL" — a
  correct claims instinct implemented as a rejection gate, so the note and the behaviour pointed
  in opposite directions. Coincidentally near Florida's one-year statutory notice window
  (627.70132(2)) but not derived from it. Now removed; late notice is non-blocking.
- **30 (`LATE_REPORTING_THRESHOLD_DAYS`).** Not merely unsourced — orphaned. Its rationale defined
  it relative to the 365-day window and described that window as the point a claim becomes
  "outright unacceptable." That gate no longer exists, and its premise was wrong regardless: a
  Florida property claim is reportable for a year, and refusing late notice was never something
  this system does. Recording the full chain because it is the clearest example in the project of
  a threshold that looked authoritative because it sat in an approved spec.
- **500 (`THEFT_LOW_SEVERITY_THRESHOLD`).** No rationale of any kind; `docs/decisions.md` restates
  the rule rather than justifying it. Also largely academic: Florida homeowners all-other-peril
  deductibles typically run $1,000–$2,500, so most of the "low" band is claims that would not be
  paid at all.
  **Decided moot, 2026-08-13:** loss amount is removed from the severity rule entirely, not
  re-thresholded — see "Carried requirements — decided, not yet built" above.

## Domain defects found, not yet fixed

- **SIU flag overrides queue routing.** An SIU-flagged record is routed to `siu_review` instead of
  its severity queue, so a high-severity fire loss with a recent-inception indicator never reaches
  a complex adjuster. SIU referral and claim handling are parallel, not alternative. Fla. Stat.
  627.70131(7)(a) gives 60 days from notice to pay or deny, and that clock does not pause for an
  indicator — a claim parked in an SIU queue is a claim running out of statutory time. Routing to
  a queue literally named `siu_review` also makes SIU status visible in ordinary routing data.
- **Late reporting fires at 30 days against a one-year statutory notice window** (627.70132(2)).
  Flags a large share of a legitimate Florida property book — roof damage surfaces when a ceiling
  stains, hurricane claims arrive over months. Legally sensitive: treating a claimant's exercise of
  a statutory right as grounds for suspicion reads badly in a FLOIR market conduct exam.
  Consequence noted below: this indicator is currently unusable.
- **`siu_flags.feature` framing** characterizes system output as a fraud conclusion — in the title
  ("SIU fraud indicators"), the narrative ("I need to flag fraud-prone patterns"), and the
  "regardless of whether the claim is otherwise valid" line.
- **`duplicates.feature` framing and gaps.** States a preventive purpose ("the same loss is not
  opened twice"), but duplicates are non-blocking evidence, and a second claimant on one loss is
  not a duplicate at all. The matcher does not know about `notice_type`, so a declared
  `SUPPLEMENTAL` or `REOPENED` notice is treated as a potential duplicate or missed entirely
  depending on timing. The ascending-order assertion is not proven — the two example claim ids are
  inserted in the order the scenario asserts they come out in. The 3-day window itself is also now
  orphaned (see the decisions.md audit above) — tuned for a model where a match blocked a notice,
  which is no longer how duplicates work. Whoever resolves this reopening should treat the window
  value as open, not just the framing and the `notice_type` interaction.
  **Resolved by the `reopening/duplicates` merge (`0b4e315`, 2026-08-12; `QUEUE.md` item 3):** the
  spec now states non-blocking evidence throughout — "candidate matches," never "probable
  duplicates" or a second claimant's report. `notice_type` is matched explicitly, with
  `SUPPLEMENTAL`/`REOPENED`/`LOSS_ASSESSMENT` resolving `NOT_EVALUATED` with a reason instead of
  running the window comparison, rather than being silently treated as a candidate or silently
  missed. The ascending-order assertion is now proven: evaluation walks input order while emission
  is explicitly sorted, and the two orders are deliberately different in the example data, so a
  mutation removing the sort is caught rather than passing by coincidence. The window is 60 days,
  symmetric on reported loss date, supplied by the caller with no domain default — replacing the
  orphaned 3-day constant rather than re-tuning it.
- **Exact `loss_type` equality in the duplicate match key is a false-negative source, and a real
  tradeoff rather than an obvious relaxation.** Chosen under the same blocking model that orphaned
  the 3-day window above — tight equality was cheap when a false positive blocked a notice, expensive
  now that a false negative means a duplicate claim opens. A loss typed `wind_hail` by the insured and
  `water_damage` by the contractor once it comes through the ceiling is the same physical loss
  reported under two different `loss_type` values, and exact equality silently loses the match.
  Recording only, not fixing in this item.
- **The `duplicates.feature` notice_type exclusion (`QUEUE.md` item 3) guards only the candidate side
  of the comparison — an existing claim carries no notice type, so the reverse direction is
  unguarded.** An ordinary `INITIAL` candidate can still be surfaced as a candidate match against an
  existing claim that is itself a `LOSS_ASSESSMENT` claim: same policy, same loss date, same
  `loss_type`, and today nothing tells them apart from that side. `loss_type` equality above is what
  currently limits this direction in practice, not a rule that guarantees it — the same missing
  phase-3 input the `NO_EXISTING_CLAIM_NOTICE_TYPE` reason code names (the existing claim's own
  coverage/notice type, unavailable at intake) appearing on the other side of the comparison.
  Recording only, not fixing in this item.
- **Loss type vocabulary, policy number prefixes, and example data across all four feature files
  reflect a multi-line liability book**, not this one: `AU`/`CP`/`CA`/`GL` prefixes,
  `auto_collision` and `auto_comprehensive` loss types, auto policy numbers throughout the
  duplicates examples.
  **Resolved by the `reopening/loss-type-vocabulary` merge (`a0983ef`, 2026-08-13; `QUEUE.md` item
  4a) and the `reopening/policy-prefix-set` merge (`f78ba74`, 2026-08-13; `QUEUE.md` item 4b),
  together:** the loss-type and policy-number *example data* is fixed in `triage.feature`
  (`auto_collision` -> `lightning`, `auto_comprehensive` -> `smoke`) and `duplicates.feature`
  (`AU-7654321` -> `HO-7654321`, on the policy-mismatch row and the "Two existing claims both match
  the candidate" scenario). The recognized policy-number *prefix set* is narrowed to `HO` alone —
  `validation.py`'s `POLICY_NUMBER_PATTERN` no longer accepts `AU`/`CP`/`CA`/`GL`, and
  `validation.feature`'s "Policy number format" outline now asserts `AU-1234567`, `CP-1234567`,
  `CA-1234567`, and `GL-1234567` as `POLICY_NUMBER_MALFORMED` rather than passing — kept as explicit
  rows rather than folded into the outline's existing malformed-prefix catch-all, because they
  document which lines this book does not write. Nothing else in `validation.feature`'s own example
  data still reflects a multi-line book. What genuinely remains open: what the recognized set grows
  to next (`DP`, then `MH`) is still an open question recorded at `QUEUE.md` item 4b, not decided by
  this merge; and the number *shape* — two letters, a hyphen, seven digits — is untouched by either
  merge and stays open below, under "`POLICY_NUMBER_PATTERN` encodes a carrier fact in the domain
  layer."
- **"injury" is modelled as a peril rather than a Section II liability coverage.** `loss_type` is
  also single-valued, so a hurricane loss where someone was hurt cannot be represented.
- **Loss amount affects severity only for theft.** A $50,000 water loss and a $500 water loss
  receive identical severity, despite loss amount being one of the strongest severity signals
  across every peril.
- **No plausibility floor on loss date.** A loss date of 1850-01-01 flows through as non-blocking
  late notice. The principled fix is "loss date cannot precede policy inception," which needs
  policy data that doesn't exist until phase 3. Not inventing an arbitrary floor in the meantime.
- **`compute_siu_flags` already guards against a policy inception date after the loss date, and
  nothing has ever said so.** `_is_recent_inception`'s range check is
  `0 <= (loss_date - inception_date).days <= 30` — an explicit lower bound, not just the upper bound
  the 30-day threshold implies. When `policy_inception_date` is after `loss_date`, the day count is
  negative, the lower bound fails, and `recent_policy_inception` resolves to `False` rather than
  being computed on a negative interval. The `0 <=` is written deliberately (a real two-sided bound,
  not an accidental side effect of how the comparison happens to be written), but the *rule* it
  encodes — a loss cannot predate the policy that covers it, for SIU purposes — is not documented
  anywhere: not `siu_flags.feature`, not `docs/decisions.md`, not this file, until now. No scenario
  in `siu_flags.feature`, `tests/unit/test_siu.py`, or (pre-mutation) `triage.feature` has ever set
  an inception date after a loss date; the guard has been correct by construction since phase 1 and
  invisible to every gate for exactly that long. Found by mutation testing on `triage.feature`'s
  reopening — a mutant setting `inception_date` after `loss_date` survived, because the guard already
  produced the same result the row's example expected — not by anything examining the code directly.
  This is this file's usual failure shape in reverse: not a spec asserting something the code
  doesn't do, but code doing something no spec asserts. A loss date preceding policy inception is a
  coverage question (was the policy even in force), not an SIU question, and belongs with "No
  plausibility floor on loss date" above — both need policy data that doesn't exist until phase 3.
  Not fixing, and not adding a scenario, in this reopening: item 1 is queue routing, not SIU
  thresholds. See `QUEUE.md` item 2.

  **RESOLVED 2026-08-09 by item 2; recorded 2026-08-15.** The scenario this entry
  says was not being added was added — `siu_indicators.feature`'s Rule "A continuous
  coverage date after the loss date does not indicate recent policy inception".
  Four names above are dead and are corrected here rather than in the text:
  `compute_siu_flags` is `compute_siu_indicators`, `_is_recent_inception` is
  `_evaluate_recent_inception` (both renamed in `33d602b`), `siu_flags.feature` is
  `siu_indicators.feature`, and `policy_inception_date`/`inception_date` is
  `continuous_coverage_date`/`coverage_start` after item 4d. The larger question the
  entry raises — whether a loss predating coverage is a coverage problem — is still
  open and still needs phase-3 policy data.
- **The record captures no reporter identity or relationship to the insured.** FNOL on a Florida
  residential book arrives from the insured, the agent, a public adjuster, an attorney, a mitigation
  contractor, or a CAT call center, and the reporter is frequently not the insured. The 7-day
  acknowledgment duty (627.70131(1)(a) — see `STATUTORY_REGISTER.md`) has a recipient the record
  cannot name: nothing in `Candidate` records who reported the loss or in what capacity.
  **Considered and rejected:** "represented at FNOL" (an attorney or public adjuster reporting on
  the insured's behalf) must not become an SIU indicator. Same legal shape as the 30-day
  late-reporting rule `QUEUE.md` item 2 already removed — a claimant's lawful exercise of a right,
  here the right to representation, is not grounds for suspicion, and coding it as a fraud signal
  reads exactly as badly in a market conduct exam as the late-notice indicator did.
- **Why `test_triage.py::test_every_high_severity_loss_type_is_recognized_by_validation` exists,
  recorded because the set comparison it makes is not self-explanatory (`QUEUE.md` item 4h).** It
  is easy to read as redundant with `validation.feature`'s "Recognized loss types" outline, which
  already carries `fire` and `sinkhole` as rows, and with the separate "Required fields for an
  injury loss" rule that covers `injury` — and to delete it on that reading. It is not redundant.
  Those rows and that rule establish that `validate()` recognizes `injury`, `fire`, and `sinkhole`;
  they say nothing about `triage._HIGH_SEVERITY_LOSS_TYPES`, a separate frozenset in a different
  module that neither one touches. The two sets are only related because nothing enforces that they
  must be: if a future edit to `RECOGNIZED_LOSS_TYPES` ever dropped `injury`, `fire`, or `sinkhole`,
  or if `injury`'s field-completeness coverage in the rule above stopped tracking it as recognized,
  `validate()` would block every notice of that loss type into `PENDED` before `triage_and_route`
  ever ran — the highest-severity category silently stops reaching a queue, and nothing in either
  feature file would fail, because each only asserts facts about its own set. This test is the only
  thing that would. Those `validation.feature` rows are load-bearing for triage's high-severity
  routing too, not only for intake, even though nothing in `validation.feature` says so.
  Names verified 2026-08-16: `test_every_high_severity_loss_type_is_recognized_by_validation`,
  `RECOGNIZED_LOSS_TYPES`, `_HIGH_SEVERITY_LOSS_TYPES`, `validate`, and `triage_and_route` are
  current as of that date; the argument above is about the sets these symbols locate, not the
  symbols themselves, and survives their renaming.

## Data we do not have at intake

- **`policy_inception_date` is available at FNOL via a lookup against the policy administration
  system — decided 2026-08-13, documentation-only session on `main` (`QUEUE.md`'s merged item 4c);
  no branch, no spec, no implementation yet.** Previously recorded here as needing policy data that
  "does not exist until phase 3" and as "probably not reporter-knowable." Both were true only for
  self-reported data; a system lookup was never considered before and changes the answer. The
  domain shape does not change: the lookup is I/O and belongs to phase 2's adapter layer, and
  `compute_siu_indicators` keeps receiving the date as a parameter it never derives itself, exactly
  as today.
  **Decided 2026-08-13: the lookup returns the policy's ORIGINAL inception date — the date
  continuous coverage on the risk began — never the current term's effective date.** This was
  a domain decision, not a data-availability one: both dates are available from the policy
  administration systems. The recent-inception indicator exists to surface new business — a loss
  shortly after coverage was first bought. A renewal effective date carries no such signal, and
  keying on it would fire the indicator across a lawful book every twelve months — the same defect,
  in the same shape, `QUEUE.md` item 2 already removed from the late-reporting side.
- **Decided 2026-08-14: how the adapter derives that date, and what "continuous coverage" means.**
  Answers the mechanics the decision above left open, not a separate question. The adapter does not
  read a stored inception field. It resolves the party/risk identity from whatever the reporter
  supplies, pulls every associated policy term for that risk plus cancellations, non-renewals, and
  reinstatements, and derives the continuous-coverage start from that history. Administrative
  rewrites and book transfers are transparent to this, because the term chain underneath them is
  continuous even though the policy number changes.
  A lapse is a gap in coverage IN FORCE, not a gap in the policy record: a reinstatement effective
  retroactively to the cancellation date leaves no gap and does not reset the date; one leaving an
  uncovered interval does. This is what makes the date survive an administrative rewrite but not a
  genuine lapse.
  Takeout and assumption business settle a second question this entry previously left open — whether
  "continuous coverage" means with this carrier or on the risk: it is **on the risk**, regardless of
  which carrier wrote it, because that is what the available data models. The first term in the
  assuming carrier's own system carries the prior carrier's continuous-coverage date as a data point,
  not a reset. **Corrects the "continuous coverage with this carrier began" wording** in the decided
  entry above and in `QUEUE.md`'s item 4c — narrower than what the lookup can actually compute; both
  now read "on the risk."
  **What remains unverified is only per-system mechanics** — which identifier resolves to the
  party/risk in each of the three policy administration systems. Needed before the phase-2 adapter is
  wired, not before the spec.
- **Consequence, updated for the decision above:** the recent-policy-inception indicator's blocking
  gap was its missing input; that gap is resolved in principle now that the lookup's semantics are
  decided. Once the phase-2 adapter is built, `NOT_EVALUATED` becomes a genuine exception path for
  this indicator — triggered by an actual lookup miss, not the expected steady state every fixture
  and caller hits today. The late-reporting indicator's blocking gap (no defensible threshold) is
  unrelated to this decision and is still open — see the open replacement-threshold decision below.
- **The phase-1 SIU tests pass at 100% mutation score against fixture data with no real-world
  source.** The gates are correct and the input is fictional; that distinction belongs on the
  record, not just in this file.
- **Advisor-recommended, human-ratified, 2026-08-15: the SIU reason code `NO_POLICY_INCEPTION_DATE`
  is renamed `NO_CONTINUOUS_COVERAGE_DATE`, in the spec draft so far, not yet implemented.** It names
  the same date the rest of item 4d's vocabulary rename retitled everywhere else in
  `siu_indicators.feature` and `triage.feature`; leaving it would have the record assert a value
  named for exactly the artifact the rename exists to stop naming. Nothing consumes this value as
  serialized output yet — whether SIU's reason codes belong in a `reason_codes` field is still an
  open question (`PHASE2_DESIGN.md`) — so this is the cheapest point in the value's life to change
  it: before any consumer, human or system, comes to depend on the old spelling. The reason-code
  enumeration stays closed and unchanged in membership: `NO_THRESHOLD_CONFIGURED` and (now)
  `NO_CONTINUOUS_COVERAGE_DATE` are still the complete set, per `CLAUDE.md`'s reason-code-enumeration
  constraint — this is a rename, not an addition. `src/claimgate/domain/siu.py`'s constant is
  unchanged until implementation follows the lock.

## Open decisions

- **Replacement for the 30-day late-reporting threshold — not being set now.** Setting it quickly
  is the process that produced the 365, the 30, and the 500. Constraints for whoever settles it: a
  bare day count is probably the wrong instrument on a property book, because discovery time varies
  by peril — fire, theft, and vandalism are known immediately; wind, hail, and roof damage
  frequently surface months later. This is a carrier policy decision, not an industry standard. The
  strongest option here may be one well-grounded indicator with its data-availability caveat
  stated, rather than two where one is indefensible — an open question for whoever owns this
  decision, not an answer this project can supply on its own.
- **`loss_type` conflates perils with Section II coverage categories, and the conflation is
  load-bearing today, not cosmetic.** `fire`, `water_damage`, `theft`, `wind_hail`, and `vandalism`
  are perils — physical causes of loss. `injury` and `liability` are Section II liability coverage
  categories, not perils, and one field can't represent both dimensions of the same loss: a
  hurricane claim where someone was also hurt has nowhere to go today (see the related defect
  already recorded above, "'injury' is modelled as a peril rather than a Section II liability
  coverage"). Two real behaviors are keyed on this single field carrying both kinds of fact at
  once: `validation.py`'s `_check_injury_fields` branches on `loss_type != "injury"` to decide
  whether injured-party fields are required, and `triage.py`'s high-severity set is
  `{"injury", "fire"}` — a peril and a coverage category in the same frozenset because `loss_type`
  has nowhere else to put either one. Real carriers capture cause of loss and claim/coverage type
  as separate fields. This is the same shape of question `PHASE2_DESIGN.md` already raises for
  `notice_type` — "the approval is void the moment required fields vary by notice type" — arriving
  here for `loss_type`, independently and earlier than expected. Recording as an open decision, not
  a defect: nothing here is wrong today, and `QUEUE.md` item 4c (missing perils) should not assume
  an answer to whether `loss_type` eventually splits into separate peril and coverage-type fields —
  adding perils is orthogonal to, and shouldn't presume the outcome of, that split.

- **`POLICY_NUMBER_PATTERN` encodes a carrier fact in the domain layer, and item 4b narrows the
  prefix set without resolving that.** The regex asserts one numbering *shape* — two letters, a
  hyphen, seven digits — for every carrier a configuration might cover. 4b (`QUEUE.md`) narrows the
  recognized *prefix* to `HO` alone, but the shape itself stays a domain-layer assumption applied
  uniformly across every carrier a configuration might cover, and real carriers number policies
  differently from one another — a difference this project never had the access to check against
  any live book, and which the entry above now records as an open assumption rather than a
  carrier-specific gap. `README.md`'s core design commitment is that carrier
  identity is data, never behavior, and `PHASE2_DESIGN.md`'s swappability tests exist specifically to
  prove that claim rather than argue it; a domain regex naming a specific number shape is in tension
  with both — the same shape of problem as the false "lines of business this carrier actually
  intakes" claim in the `docs/decisions.md` audit above, arriving here for the number format instead
  of the prefix list.
  **Why not simply make it caller-supplied, the way the duplicate window and the SIU thresholds
  were:** those are bare scalars with no structure behind them, so a parameter fully resolves the
  concern. Parameterizing only the prefix list here would not — the two-letter-hyphen-seven-digit
  shape would still be fixed in the domain, producing something that reads as configurable without
  actually being so. The real fix is structural, not a parameter: whether a policy number is
  well-formed is a fact about the carrier's own numbering scheme, which belongs to phase 2's adapter
  layer, where carrier differences are designed to live — not to a single domain-wide pattern.
  Recording only: not fixed in item 4b, and not part of 4b's spec change.

## Synthetic data

- No real policy numbers, names, addresses, phone numbers, or claim numbers appear anywhere in
  specs, fixtures, or tests. Names are fictional; phone numbers stay in the 555-01xx reserved
  range.
- Carrier identity data (names, NAIC codes) is public regulatory information, used because the
  design targets a real, named carrier estate rather than a generic one. Everything else — every
  notice, every policy number, every loss description — is fabricated.
