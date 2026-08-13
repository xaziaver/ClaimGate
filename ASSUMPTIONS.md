# Assumptions

ClaimGate is designed against a concrete three-carrier Florida residential property estate —
Florida Peninsula Insurance Company, Edison Insurance Company, and Ovation Home Insurance
Exchange — administered by Windward Risk Managers. This project has no access to Windward's or
Duck Creek's internal systems or data. Every entry below states what was assumed, why, and what
would correct it — this file is the difference between a gap that reads as identified and one
that reads as missed.

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
  - *Policy number LOB prefixes: HO, AU, CP, CA, GL* — "the lines of business this carrier
    actually intakes." A statement of fact about Windward, and it is false: Windward intakes
    Florida residential property only, no auto, no commercial (see Finding 5 below).
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

## Windward / Duck Creek estate — all unverified, no internal access

- **Carrier codes.** `FPIC` / `EDIS` / `OVTN` are our invention, not Windward's codes. Windward's
  real codes substitute at integration.
- **Policy number format.** Assumed, not known. It is a config value so a real format substitutes
  without a code change.
- **Ovation's NAIC group code.** Unverified, left null. Demotech groups it with Florida Peninsula,
  but a member-owned reciprocal may be grouped by management rather than ownership.
- **Ovation's policy number format.** May differ from Florida Peninsula's and Edison's. Not public;
  needs an internal check.
- **Book scope.** Assumed Florida-only, residential-only. Well-supported by public sources
  (Windward's own materials describe exactly these three carriers, Florida homeowners only), but
  not formally confirmed by Windward.
- **NAIC company codes (10132, 12482, 17621) ARE verified**, against FLOIR primary sources —
  Florida Peninsula's targeted market conduct exam report and Edison's financial examination
  report, cross-checked against a second source. Stated explicitly so this entry is not read as
  the same class of unverified claim as the rest of this section.

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

## Data we do not have at intake

- **`policy_inception_date` has no source.** It is populated directly by fixtures and callers, with
  no domain code, no infrastructure, no lookup behind it. Policy data does not exist until phase 3.
  It is also probably not reporter-knowable — a homeowner calling in a loss does not know their
  policy's inception date — so there is no honest source for this field at intake even in
  principle, self-reported or otherwise.
- **Consequence:** the recent-policy-inception SIU indicator cannot be honestly computed until
  phase 3. Combined with the 30-day late-reporting defect above, both SIU indicators are currently
  unusable — one because its threshold is indefensible, the other because its required input does
  not exist.
- **The phase-1 SIU tests pass at 100% mutation score against fixture data with no real-world
  source.** The gates are correct and the input is fictional; that distinction belongs on the
  record, not just in this file.

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
  hyphen, seven digits — for all three carriers in the target estate. 4b (`QUEUE.md`) narrows the
  recognized *prefix* to `HO` alone, but the shape itself stays a domain-layer assumption applied
  uniformly across Florida Peninsula, Edison, and Ovation, and real carriers number policies
  differently from one another — Ovation's own format is already recorded above as unverified and
  possibly different from the other two. `README.md`'s core design commitment is that carrier
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
