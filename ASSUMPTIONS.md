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

  **Corrected 2026-08-23: two of the four named scenarios test the wrong thing, found while
  drafting item 5b.** The 01:00 America/New_York scenario is degenerate. Any instant at 01:00
  Eastern is 05:00 or 06:00 UTC the same day, so the local date and the UTC date always agree and
  the scenario passes under an implementation that ignores the timezone entirely. The instant that
  actually discriminates is early-UTC, not early-Eastern: `2026-06-11T01:00Z` resolves to
  `2026-06-10T21:00` EDT, local date 2026-06-10, one day behind the UTC date 2026-06-11. That
  replaces the 01:00-Eastern scenario. The 22:00-Eastern scenario stands as originally named: an
  instant at 22:00 EDT is 02:00 UTC the next day, so it does discriminate.

  "Both DST transition boundaries" tests the wrong quantity. The 2026 Eastern transitions are
  2026-03-08 02:00 -> 03:00 local (spring forward) and 2026-11-01 02:00 -> 01:00 local (fall
  back), both well inside their day rather than anywhere near a local midnight, so no UTC instant
  crossing either transition instant changes which calendar date it resolves to. What DST changes
  is the UTC offset in effect for a given date, and it is a *change in offset* — not proximity to a
  transition — that can move a resolved date across a boundary. Replaced with an offset pair at a
  date boundary, keeping the standing either-side constraint (an instant on both sides of local
  midnight, under each offset): under EST, `2026-01-15T04:30Z` resolves to `2026-01-14` (30
  minutes before local midnight) and `2026-01-15T05:01Z` resolves to `2026-01-15` (a minute
  after); under EDT, `2026-07-15T03:59Z` resolves to `2026-07-14` (a minute before local midnight)
  and `2026-07-15T04:30Z` resolves to `2026-07-15` (30 minutes after). The same UTC wall-clock
  time, `04:30Z`, resolves to a different date under each offset — that pair is the point: the
  offset moved it, not the calendar date of the UTC instant itself.

  For the record, so neither is re-added as its own scenario: the spring-forward gap (02:00-02:59
  local on 2026-03-08 does not exist) and the fall-back ambiguous hour (01:00-01:59 local on
  2026-11-01 occurs twice) are both real and both irrelevant to *date* resolution. A UTC instant
  can never land in the gap — the tzdata mapping skips it entirely — and both readings of the
  ambiguous hour fall on the same calendar date, 2026-11-01. They matter for timestamps, which is
  item 5c's problem, not this one.
  **Corrected 2026-08-23: the conversion is a domain function, not a shell one —
  advisor-recommended, human-ratified.** This entry's original wording places the
  conversion in the shell, "before calling any domain function". That placement is
  what makes the shell compute a date and hand a date to the domain, which is
  nearer the thing this entry exists to forbid than the alternative. The
  conversion takes a timezone-aware UTC instant and an IANA timezone name, both
  supplied by the caller, reads no clock and no ambient state, and returns a
  calendar date or refuses with `JURISDICTION_TIMEZONE_UNRECOGNIZED`. It lives at
  `src/claimgate/domain/jurisdiction.py`. The shell's remaining job is unchanged
  and is item 5c's: obtain the instant, resolve which zone applies, pass both. The
  shell never computes a date. The principle stands verbatim — the domain never
  receives a date derived from server local time — and is now met literally,
  because the domain never receives a date at all. Cost: `zoneinfo` enters the
  domain, so the domain depends on the platform IANA database, and ClaimGate
  declares no runtime dependencies today. The dependency is specified rather than
  hidden, since an absent zone is the refusal path this item builds — but a
  runtime image with no tz database refuses every notice rather than none. Whether
  to pin `tzdata` is a `pyproject.toml` change and a human re-lock; recorded here
  as open, and settled with item 5c's deployment work rather than now.


- **The jurisdiction timezone is a parameter of the conversion, not a constant in it.**
  Advisor-recommended, human-ratified, 2026-08-22. Florida spans two timezones: the western
  panhandle — Escambia, Santa Rosa, Okaloosa, and most of Walton — is `America/Chicago`, the rest
  of the state `America/New_York`. The same instant is two different Florida dates across that
  line: `2026-06-11T04:30Z` is 2026-06-11 in Miami and 2026-06-10 in Pensacola. A carrier writing
  notices out of Pensacola would get a loss date a day off around midnight Central, on the field
  that already drives `LOSS_DATE_IN_FUTURE` today. Item 5b therefore specifies a function taking a
  timezone-aware UTC instant **and an IANA timezone name**, returning the calendar date in that
  zone. It does not decide which zone a given notice gets — that question (risk location, mailing
  address, or carrier configuration) arrives with item 5c and is recorded here as open, not
  answered. Scenarios may use `America/New_York` throughout; at least one must use
  `America/Chicago` to prove the zone is read rather than assumed.
- **An unrecognized jurisdiction timezone is refused, never defaulted — advisor-recommended,
  human-ratified, 2026-08-23.** Once item 5c resolves the zone from risk location or carrier
  configuration, a bad value arrives here as an unrecognized IANA name — the same shape item 5a
  settled one layer down, where a malformed configuration value is refused and named rather than
  silently repaired. Falling back to `America/New_York` is the precise failure this item exists to
  prevent, and it is worse than the bug it replaces: a silent default produces a wrong
  `LOSS_DATE_IN_FUTURE` determination that reads as correct in a record a regulator or a court can
  later inspect. This file's "Unevaluated is not negative" entry already states the principle — a
  resolution whose required input is unusable must not return something that reads as a
  determination. Cost: the resolution now has two outcomes rather than one, and every caller has to
  handle the refusal.

  Named `JURISDICTION_TIMEZONE_UNRECOGNIZED`, subject first, matching
  `LOSS_TYPE_UNRECOGNIZED` and `NOTICE_TYPE_UNRECOGNIZED` - the only two
  codes in implemented domain code that name the same kind of failure
  (verified against `src/claimgate/domain/` 2026-08-23). Item 5a's
  `MISSING_REQUIRED_CONFIGURATION` and `MALFORMED_REQUIRED_CONFIGURATION`
  invert that order and are the product's only codes that do; they were
  settled before this inventory was checked and are left as they are
  because that specification is locked. Settle the inconsistency when item
  5a's implementation lands, not by reopening an approved spec for a name.
- **An instant that is not a timezone-aware UTC instant is out of scope for item 5b —
  advisor-recommended, human-ratified, 2026-08-23.** The "Timezone-correct 'now'" contract has the
  shell supply that instant, and it comes from the request pipeline and the server clock rather
  than from configuration or a reporter, so it is a caller-contract violation rather than a runtime
  input this resolution has to defend against. Distinguished here from the timezone name, which
  genuinely does arrive from configuration, and named rather than left silent because two of the
  timezone-parameter scenario's mutants depend on the answer and an equivalent-mutant approval will
  need something to point at.

  **Annotated 2026-08-23, measured: the violation is silent, which is why the
  obligation moves to item 5c rather than disappearing.** A naive `datetime`
  is not rejected by anything. `datetime.astimezone()` on a value with no
  `tzinfo` assumes *server local time* and returns a plausible wrong date
  rather than raising: with the server clock on `America/Chicago`, a naive
  `2026-06-11T01:00` resolves to `2026-06-11` where the correct answer for the
  aware UTC instant is `2026-06-10`. `[tool.mypy] strict = true` cannot catch
  it, because aware and naive datetimes share one type. So this caller-contract
  violation does not fail loudly at first integration - it produces exactly the
  wrong `LOSS_DATE_IN_FUTURE` determination this item exists to prevent, from a
  code path with no error and a green gate. Item 5b is still the wrong place to
  defend against it: a guard here would be behavior no scenario in the locked
  spec describes. The obligation is item 5c's, where the instant is obtained,
  and it is recorded there rather than left implicit in this exclusion.

- **A refused submission is still a received communication — advisor-recommended,
  human-ratified, 2026-08-23.** Item 5c's draft refuses a notice whose loss date is
  not a date, "creating nothing". `PHASE2_DESIGN.md`'s own audit section is why that
  is wrong: it records that Fla. Stat. 627.70131(4)(b) requires the insurer to
  maintain claim records, including dates, of any claim-related communication, that
  an FNOL is such a communication under (4)(b)1, and that this audit log is the
  system of record for that duty. Verified against the Florida Legislature's
  published text on 2026-08-23: 627.70131(1)(a) requires review and acknowledgment
  of receipt within 7 calendar days of receiving a communication with respect to a
  claim — the trigger is receipt of a communication, not receipt of a well-formed
  one. A submission naming a carrier, a policy number and a loss type, with an
  unusable loss date, is such a communication. The entry schema already carries
  `outcome: APPLIED or REFUSED`, "every transition attempt gets an entry, including
  refused ones"; "creating nothing" contradicts a field added for exactly this.

  The decision is narrow. A refused submission persists its raw payload record —
  the verbatim, immutable, hash-referenced record this design already defines — with
  its receipt timestamp. It does not create a notice: no notice identifier is
  allocated, no state is written, no audit entry is made, and nothing becomes
  retrievable through the notice endpoints. The 400 response carries the payload
  hash as an intake reference, so the reporter and the carrier can name the same
  communication.

  Why not the two obvious alternatives. Creating a notice would put a phantom claim
  into claim counts, reserving and regulatory reporting — worse than the problem it
  solves, and not what carriers do: intake keeps a submission record and issues a
  claim number only on acceptance. Extending the audit log would require an entry
  with no `notice_id`, which the schema makes mandatory and whose `from_state` is
  meaningful only against a notice; loosening that weakens the log for the case it
  was designed for.

  Cost. Refused payloads accumulate with no notice referencing them, so retention
  must cover them explicitly rather than by reachability from a notice — item 5g's
  problem, recorded here rather than solved. And the 400 path now writes, so it is
  no longer free under a submission flood; rate limiting is outside phase 2's scope
  and this entry does not pretend otherwise.

- **Item 5c's 400 validates against the identity reference, not the rules source —
  advisor-recommended, human-ratified, 2026-08-24.** Settled, not open:
  `features/carrier_configuration.feature`'s own comment at `f19317e` says so verbatim
  ("this is not item 5c's 400 on an unknown or malformed carrier_code against the identity
  reference, either: that is a different file, a different check, owned there"), and
  `PHASE2_DESIGN.md`'s carrier-reference section ties the 400 to the identity list by name.
  `QUEUE.md` item 5c's shorthand "the reference file it validates against is 5a's" is the only text
  pointing the other way and is the loosest of the three. The drafting session escalated this as
  undecided; it was decidable from documents already in hand.

- **A carrier this deployment administers but cannot configure is our defect, not the reporter's —
  advisor-recommended, human-ratified, 2026-08-24.** A `carrier_code` present in the identity
  reference whose rules entry resolves `CARRIER_NOT_CONFIGURED` or malformed returns 5xx, not 400,
  and still persists a receipted payload record with its hash as an intake reference - the same
  shape as "A refused submission is still a received communication," above. An identity-recognized
  carrier is one this deployment claims to administer, so a statutory duty arises under
  627.70131(1)(a); a 4xx would tell a reporter their notice was refused for a defect on this
  deployment's own side, which is exactly what the no-rejected-state rule exists to prevent. Cost,
  stated rather than hidden: `PHASE2_DESIGN.md`'s status-code table is no longer closed and needs a
  new row. Sequenced as its own queue item, not built inside item 5c.

  **The response column added to `features/notice_intake.feature`'s Rules 1 and 3 this session
  makes the same decision this entry's cost paragraph names, applied one layer up.**
  Caller-observable status is behavior, not implementation, and asserting it is what protects
  `PHASE2_DESIGN.md`'s deliberate two-201s design from a future 202 someone adds because a `PENDED`
  notice "sounds" incomplete. Reversible before this spec is locked, at a measured cost of 4 mutants
  and every locator in Rules 1 and 3 - free now, not free later.

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
  `NO_CONTINUOUS_COVERAGE_DATE`, not `NO_THRESHOLD_CONFIGURED`. (The code was
  `NO_POLICY_INCEPTION_DATE` when this entry was written; item 4d renamed both the field and the
  code — see the ratified entry below.) Principle: the reason code names the gap
  that would still block evaluation if the other were closed. With no inception date known,
  configuring a threshold changes nothing — reporting `NO_THRESHOLD_CONFIGURED` would name a gap
  whose closure would not help, and would imply a fix that is not one. The missing input outranks
  the missing rule. This was originally an accident of implementation order, not a decision: the
  code's pre-existing `inception is None` check ran first because it was already there from before
  this reopening; the new `threshold_days is None` check was appended after it to satisfy mypy's
  type narrowing, with no thought given at the time to which reason code should win. Reviewed and
  confirmed correct against the principle above on a later pass, not left as the accident that
  produced it.

  **Corrected 2026-08-18: it is reachable now, and the scenario is owed.** This entry and
  `PHASE2_DESIGN.md`'s SIU handling section both deferred the scenario on the premise that the
  recent-inception threshold is "always a real, kept value of 30" in the shipped configuration. Item
  2 removed both SIU threshold defaults, so the threshold is caller-supplied and may be absent —
  `siu_indicators.feature`'s "No recent policy inception threshold configured" scenario proves it —
  and a caller omitting it for a candidate with no coverage date reaches the both-absent state
  today. No scenario exercises it: every one of the nine supplies at least one of the two inputs. A
  reordering of the two checks would fail no test, and mutation testing does not generate statement
  reorderings, so the precedence is protected by `siu.py`'s "Do not reorder these checks" comment
  and by nothing else. Sequenced as `QUEUE.md` item 4k, before phase 2.
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

  **Annotated 2026-08-23: this entry's substance holds, its boundary language no longer does.**
  Item 5a placed `carrier_configuration.py` in `src/claimgate/domain/`, so the domain package now
  contains a module that parses configuration, refuses an unrecognized carrier code, and refuses
  absent or malformed values by name. The sentence above - parsing, validating and rejecting a
  malformed configuration value is the caller's job, above the domain boundary - is still true of
  the six domain rules, which have no unrecognized-configuration branch and should never grow one.
  It is no longer true of the domain package. The placement was ratified for the same reason item
  5b's was: the module is a pure function of caller-supplied inputs carrying named refusal
  outcomes, and `[tool.mutmut] source_paths` scopes the code-mutation gate to
  `src/claimgate/domain/` only, so a sibling package would have exempted 98 killed mutants from
  that gate with no visible signal. Read "above the domain boundary" here as a statement about
  which code interprets configuration, not about which directory it lives in.
- **The per-carrier rules file moves from phase 3 into phase 2 — advisor-recommended,
  human-ratified, 2026-08-22.** `PHASE2_DESIGN.md`'s carrier-reference section describes a static
  identity-only file in phase 2 and a per-carrier rules file "eventually," in phase 3. That was
  written before items 2, 3, 4g, and 4j moved six values out of the domain and made them
  caller-supplied with no default: three on `validate`, two on `compute_siu_indicators`, one on
  `find_duplicates`. The phase-2 shell has to supply all six on every call and has nowhere to get
  them, so the rules file is phase-2 work whatever the design document says. Identity and rules stay
  separate files, per that section's own reasoning — a carrier's NAIC number and a carrier's
  duplicate window are different kinds of fact, and one file holding both is what makes
  `carrier_code` look branchable.

  Selecting a parameter set by `carrier_code` is a lookup, not a branch: the shell passes the
  selected values through to the domain, and no code path reads the key to choose behaviour. The
  distinction is the same one the jurisdiction map rests on, and if the two end up structurally
  different, one of them is wrong.

  **The axis is carrier, not jurisdiction, with one genuine exception pending.**
  `PHASE2_DESIGN.md`'s SIU carried requirement says these thresholds will come "from jurisdiction
  config"; the configuration entry above says carrier. Carrier is right for five of the six — a
  duplicate window, a required-field set, and a recognized prefix set are carrier policy, and
  identical Florida statute governs carriers that differ on all three. The late-reporting threshold
  is the one that may genuinely belong on the jurisdiction axis, since its defensibility is
  entangled with the statutory notice window; that stays open under "Replacement for the 30-day
  late-reporting threshold" and is not settled by this entry. Cost of deciding carrier now: if that
  one threshold later moves axes, it moves alone.

- **Duplicate-detection not-evaluated reason codes do not appear in `reason_codes` —
  advisor-recommended, human-ratified, 2026-08-22. Resolves the carried requirement
  `PHASE2_DESIGN.md` records as undecided under "HTTP surface."** `reason_codes` is derived from
  blockers and means something is wrong with this notice. `FOLLOW_ON_NOTICE_TYPE` and
  `NO_EXISTING_CLAIM_NOTICE_TYPE` mean a comparison was deliberately not run, which is not a defect
  in the notice: a `SUPPLEMENTAL` notice resolving `FOLLOW_ON_NOTICE_TYPE` is behaving exactly as
  intended. Merging the two would make every follow-on notice read as flawed to any client counting
  `reason_codes`, and would put a second enumeration into a field whose codes are validation
  blockers — against the standing constraint that reason-code enumerations are closed and scoped to
  one feature.

  They surface instead on the duplicate-candidates structure the notice already needs, carrying
  status, matches, and reason together, so the not-evaluated value and its reason cannot be read
  apart from each other. Cost: a client reads two fields rather than one, and a client that reads
  only `reason_codes` cannot see that duplicate detection did not run. Accepted, because the
  alternative is worse in the direction that matters — a false signal of defect beats a signal in a
  field the caller has to know to look at.

- **Phase 2 matches duplicate candidates against ClaimGate's own persisted notices only —
  advisor-recommended, human-ratified, 2026-08-22.** `find_duplicates` takes an existing-claims
  collection and `PHASE2_DESIGN.md` never says where the shell gets it. The policy administration
  lookup is a phase-3 adapter concern, so in phase 2 the candidate set is the notices ClaimGate
  itself holds for the same `carrier_code`.

  **Stated cost, which is real and not a technicality:** a loss already open in the administration
  system before ClaimGate went live, or reported through any other channel, is invisible to the
  matcher. Duplicate detection in phase 2 therefore answers "has this been reported *here* before,"
  not "has this been reported." That is a narrower question than the specification's language
  implies, and a reader who assumes the broader one will over-trust a clean result. Acceptable for a
  shell whose duplicate output is non-blocking evidence rather than a gate; unacceptable to leave
  unwritten. Revisit when the phase-3 adapter lands — at which point the candidate set widens and
  the reason a clean result can be trusted changes with it.

- **The continuous coverage date does not exist in phase 2, so the recent-inception indicator
  resolves not-evaluated on every phase-2 notice — advisor-recommended, human-ratified,
  2026-08-22.** Item 4c settled that the date arrives via a phase-2 adapter lookup returning the
  policy's original inception date; there is no adapter in the phase-2 shell, and building one is
  phase-3 work. So the input is genuinely absent and the indicator resolves `NOT_EVALUATED` with
  `NO_CONTINUOUS_COVERAGE_DATE` on every notice the shell processes.

  **This is the correct behaviour, not a stub awaiting a value**, and it is recorded because it will
  look like a gap to whoever builds 5f. Supplying a placeholder date — the loss date, the receipt
  date, a null-safe default — manufactures a determination nobody made, which is the precise failure
  "unevaluated is not negative" exists to prevent, and it would do so silently on every record in
  the system. The indicator is a fact about what was evaluated; phase 2's honest answer is that it
  was not. See "Data we do not have at intake" for how the date is obtained once an adapter exists.

- **A configuration value that is present but malformed is refused at load, alongside an absent one
  — advisor-recommended, human-ratified, 2026-08-22.** `QUEUE.md` item 5a specifies that "an
  unrecognized or absent configuration value is refused at load," and the entry above records the
  loading boundary as the only thing standing between "a mistyped configuration file and a silently
  wrong required-field set." Mistyped means present and wrong, not missing. A first spec draft
  narrowed the item to absence only; that removes the half of the rule the harness can actually
  protect, because a wrong-typed value is a mutable Examples cell while an absent one is an empty
  cell that only ever takes the mutation marker.

  What counts as malformed is decided per value by its type, not by a new vocabulary: a
  non-boolean where a boolean is required, a non-integer or negative where a day count is
  required, an empty collection where at least one recognized prefix is required. Cost: the spec
  carries more rows, and each malformed row must state which value it malformed or the refusal is
  untestable.

- **A refusal names every value it rejected, not the first one — advisor-recommended,
  human-ratified, 2026-08-22.** `validation.feature` already established that blockers are
  reported together rather than one per run, and a configuration loader has the stronger version of
  the same argument: a deployment with six malformed values that learns about them one restart at a
  time costs six restarts to fix what one message could have named. The refusal is a collection,
  and a scenario asserting a single-value refusal is asserting the degenerate case of that
  collection rather than a different rule.

  This is an operational decision rather than a business one — no statutory duty attaches to a
  configuration file — but it shapes the spec, so it is recorded rather than left to whoever writes
  the loader.

- **A missing configuration value and a malformed one are different reason codes -
  advisor-recommended, human-ratified, 2026-08-22.** Your redraft widened `MISSING_REQUIRED_CONFIGURATION`
  to `INVALID_REQUIRED_CONFIGURATION` so one code stayed honest across both cases. Widening is the wrong
  direction. `validation.feature` settled this one layer down at item 4e, splitting
  `LOSS_TYPE_UNRECOGNIZED` out of `MISSING_REQUIRED_FIELD` so a typo is not indistinguishable from a blank
  field. The operational version is sharper here: an absent value means the carrier was never onboarded
  into the rules file, a malformed one means it was onboarded wrongly. Different defects, different
  people, different fixes, and the load boundary is the last point at which the system can tell them
  apart. The codes are `CARRIER_NOT_CONFIGURED`, `MALFORMED_REQUIRED_CONFIGURATION` and
  `MISSING_REQUIRED_CONFIGURATION`, a closed enumeration, in that canonical order - malformed before
  missing, for the same reason `POLICY_NUMBER_MALFORMED` precedes `MISSING_REQUIRED_FIELD` in
  `validation.feature`'s declared order. Cost: one more code, and the refusal's ordering must now be
  specified rather than left implicit. Free today - measured at `5d37a4f`, the old name has five
  occurrences, all inside this one unlocked spec file, no step definition, no `src/`, no ledger entry.

  The refusal's order is stated over the field name as the specification writes
  it - the business term the `CODE:field` pair renders - not over any internal
  key. `validate()` sorts by `_CANONICAL_CODE_ORDER.index(code)` then `field`,
  where `field` is the model's own snake_case name (verified 2026-08-22); the
  two orders agree on today's six values but are not the same rule. Stating it
  over the rendered name keeps the order checkable from the specification alone.
  Cost: a change to a rendered field name is then an ordering change, and has to
  be measured as one rather than treated as vocabulary.

- **A key in a carrier's entry that is not one of the six values is out of
  scope for item 5a - advisor-recommended, human-ratified, 2026-08-22.** Item
  5a resolves the six caller-supplied values the domain will receive. Whether
  the rules file may carry anything else, and what a loader does when it finds
  it, is a question about that file's schema rather than about resolving a
  value, and it belongs with the phase-2 adapter layer where the file's shape
  is settled. Named here rather than left silent because the valid row of the
  refusal outline carries a surviving mutant that depends on the answer - an
  unrecognized field name substituted into a blank cell - and an
  equivalent-mutant approval reason needs something to point at.

- **A day count of zero is a valid configuration, not a malformed one -
  advisor-recommended, human-ratified, 2026-08-22.** Malformed for a day count is non-integer or
  negative. Zero is neither and it is meaningful: a duplicate match window of 0 compares only same-day
  notices, a late reporting threshold of 0 makes every notice late, a recent policy inception threshold
  of 0 counts only a same-day inception as recent. Each is a carrier choice a deployment might make
  deliberately, and a configuration loader has no standing to refuse it. Whether it is sensible carrier
  policy is a different question asked somewhere else. The spec carries a scenario on the accepting side
  of that boundary, not only the refusing side.

- **Example prefix sets use `HO` and `DP`, never `AU` - advisor-recommended, human-ratified,
  2026-08-22.** Your example carrier recognizes `"HO;AU"`. `AU` is personal auto: a different line, and
  no auto peril exists in `RECOGNIZED_LOSS_TYPES` - there is no collision or comprehensive value a notice
  could carry. A claims manager reading a residential rules file configured for HO and AU reads it as a
  configuration error, not an example. `DP` (dwelling fire) is the standard companion form on a Florida
  residential book for landlord and non-owner-occupied risk, and item 4b already named it as the next
  candidate prefix. Two prefixes are still two prefixes for what the example is doing.

- **The per-carrier rules file is TOML, keyed by `carrier_code`, with one placeholder carrier —
  advisor-recommended, human-ratified, 2026-08-22.** Matching `gauntlet.toml` and `pyproject.toml`
  rather than introducing a second configuration format, and readable by `tomllib` in the standard
  library at the project's pinned floor with no dependency added.

  **The specification does not name the format and must not.** A feature file describing TOML would
  be describing a storage decision rather than business behaviour, and the swappability the
  jurisdiction and carrier axes rest on requires that the format be replaceable without touching a
  spec. This entry exists because item 5a's *implementation* commit cannot proceed without the
  decision, not because the spec needs it.

- **Two of the six caller-supplied values legitimately accept an absent state; four do not.**
  Recorded 2026-08-22, correcting a looser framing in the entry above and in `QUEUE.md` item 5a,
  both of which describe all six as caller-supplied with no default without distinguishing "must be
  supplied" from "must have a value." `compute_siu_indicators` takes `int | None` for both
  thresholds on `main`; `validate`'s two booleans and prefix collection and `find_duplicates`'s
  window day count have no such affordance. So an unconfigured SIU threshold loads and resolves
  not-evaluated downstream, while an unconfigured required field refuses the load. Both facts were
  established from the signatures, and the distinction is the difference between a correct loader
  and one that refuses a deployment for declining to set a threshold nobody has agreed a value for.

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
  **Resolved by the item 1 merge (`7f985e7`, 2026-08-09):** queue routing derives from severity
  alone, `SIU_QUEUE` and the `siu_review` string are gone from `src/`, and SIU indicators are not a
  field on `TriageOutcome`. The name survives in one place only — a comment in `triage.feature`
  recording why routing to a queue so named would leak SIU status — which is the argument, not the
  behaviour.
- **Late reporting fires at 30 days against a one-year statutory notice window** (627.70132(2)).
  Flags a large share of a legitimate Florida property book — roof damage surfaces when a ceiling
  stains, hurricane claims arrive over months. Legally sensitive: treating a claimant's exercise of
  a statutory right as grounds for suspicion reads badly in a FLOIR market conduct exam.
  Consequence noted below: this indicator is currently unusable.
  **Partly resolved by the item 2 merge (`9d3fc2d`, 2026-08-10):** the 30-day value is no longer a
  domain default — the late-reporting threshold is caller-supplied with no fallback, and
  `siu_indicators.feature` states it as an explicitly illustrative value rather than a rule. The
  *legal* question the entry raises is untouched by that and stays open below, under "Replacement
  for the 30-day late-reporting threshold." Removing the default made the threshold nobody's
  silent inheritance; it did not decide what a defensible value is.
- **`siu_flags.feature` framing** characterizes system output as a fraud conclusion — in the title
  ("SIU fraud indicators"), the narrative ("I need to flag fraud-prone patterns"), and the
  "regardless of whether the claim is otherwise valid" line.
  **Resolved by the item 2 merge (`9d3fc2d`, 2026-08-10):** the file is now
  `features/siu_indicators.feature`, retitled and renarrated, and the domain type is
  `SiuIndicatorResult`, carrying a value and a reason code rather than a pair of booleans named for
  a conclusion. The filename `siu_flags.feature` is retained in this entry deliberately — it is what
  the defect was found in, and renaming it here would make the record unsearchable against its own
  history. Nothing outside this file's historical entries should still refer to it.
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
  Recording only, not fixing in this item. **Still open as of 2026-08-18** — item 3 merged the
  candidate-side guard and this reverse direction was explicitly out of its scope; it needs the
  phase-3 input, so it is not schedulable before then.
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
  data still reflects a multi-line book.

  **Amended by the item 4j merge (`22d672e`, 2026-08-18):** the recognized prefix set is now
  caller-supplied configuration rather than a narrowed constant, so "which lines this book does not
  write" stopped being a fact the specification states — it is one configured set among others. The
  four explicit rows were reduced to a single representative excluded prefix, and the question of
  what the set grows to next dissolved with them: a deployment configures whatever it writes. The
  number *shape* — two letters, a hyphen, seven digits — is untouched by any of these merges and
  stays open below, under "`POLICY_NUMBER_PATTERN` encodes a carrier fact in the domain layer.""
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

- **An absent loss date is a domain blocker, not a schema refusal — advisor-recommended,
  human-ratified, 2026-08-24.** `validate()` has no presence check for `loss_date`:
  `_check_loss_date` tests only the future bound, and `Candidate.loss_date` defaults to `date.min`.
  A notice submitted with no loss date at all reaches `TRIAGED` carrying `0001-01-01` as today's
  date, and no scenario anywhere covers it. Found while drafting item 5c's Rule 3 - "A notice is
  created only if its loss date is a real date" implies an answer its own table does not contain, an
  absent date being neither "a real date" nor tested as "not a real date" by anything in that rule.

  **Resolution: it resolves `PENDED` with `MISSING_REQUIRED_FIELD:loss_date`, not `400`.** A
  reporter genuinely may not know when a loss began - water under a sink, a roof that has been
  leaking - and carriers pend for the date rather than refusing the call. Item 5c's own Rule 3 draws
  its boundary on whether a value can be held for correction, and an absent date can be; it is the
  blank-policy-number case one field over. 627.70131(4)(b) makes the claim record, including dates,
  the statutory duty - recording a date nobody supplied is worse than recording its absence.
  Implementation shape: `loss_date` becomes `date | None`, mirroring `continuous_coverage_date`, and
  `_check_loss_date` gains a presence check. A phase-1 reopening -
  `validation.feature`, `validation.py`, `models.py` - sequenced separately, not built inside item 5c.

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
  is renamed `NO_CONTINUOUS_COVERAGE_DATE` — implemented and merged at item 4d (`36ae5b3`,
  2026-08-15); this entry read "in the spec draft so far, not yet implemented" until 2026-08-18.**
  It names
  the same date the rest of item 4d's vocabulary rename retitled everywhere else in
  `siu_indicators.feature` and `triage.feature`; leaving it would have the record assert a value
  named for exactly the artifact the rename exists to stop naming. Nothing consumes this value as
  serialized output yet — whether SIU's reason codes belong in a `reason_codes` field is still an
  open question (`PHASE2_DESIGN.md`) — so this is the cheapest point in the value's life to change
  it: before any consumer, human or system, comes to depend on the old spelling. The reason-code
  enumeration stays closed and unchanged in membership: `NO_THRESHOLD_CONFIGURED` and (now)
  `NO_CONTINUOUS_COVERAGE_DATE` are still the complete set, per `CLAUDE.md`'s reason-code-enumeration
  constraint — this is a rename, not an addition. `src/claimgate/domain/siu.py`'s constant followed
  the lock and now reads `NO_CONTINUOUS_COVERAGE_DATE`.

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
  once: `validation.py`'s `_check_claimant_fields` branches on membership in
  `_SECTION_II_LOSS_TYPES` to decide whether claimant fields are required, and `triage.py`'s
  high-severity set is
  `{"injury", "fire"}` — a peril and a coverage category in the same frozenset because `loss_type`
  has nowhere else to put either one. Real carriers capture cause of loss and claim/coverage type
  as separate fields. This is the same shape of question `PHASE2_DESIGN.md` already raises for
  `notice_type` — "the approval is void the moment required fields vary by notice type" — arriving
  here for `loss_type`, independently and earlier than expected. Recording as an open decision, not
  a defect: nothing here is wrong today, and `QUEUE.md` item 4c (missing perils) should not assume
  an answer to whether `loss_type` eventually splits into separate peril and coverage-type fields —
  adding perils is orthogonal to, and shouldn't presume the outcome of, that split.

  **Item 4g sharpened this rather than resolving it, 2026-08-17.** The branch it names was
  `_check_injury_fields` testing `loss_type != "injury"`; it is now `_check_claimant_fields` testing
  membership in `_SECTION_II_LOSS_TYPES`, which is `{"injury", "liability"}`. The specification now
  *names* the Section I / Section II division explicitly and the code enforces it, so the conflation
  is no longer implicit — but the field is still single-valued and still carries both kinds of fact,
  so a hurricane loss with an injury still has nowhere to go. What changed is that the split now has
  a name and one enforced consumer, which makes it cheaper to act on later and easier to mistake for
  having been dealt with.

  **The intended direction, stated 2026-08-17 and deliberately not built.** Under the
  general-product framing, the recognized loss-type set is no longer a fact about one book: the
  shape is a full catalogue shipped with the product from which a carrier selects in its
  configuration, the same pattern items 4g and 4j establish. Not queued, and that is a judgment
  rather than an oversight — a narrow set that works end to end is worth more than a configurable
  one that does not run, and the mechanism should be designed once against phase 2's adapter shape
  rather than twice.

  **Two things to settle when it is built, both of which a single flat catalogue would hide.**
  First, this entry's own point: a carrier selecting from one list would be answering "which perils
  do we accept" and "do we write Section II at all" with the same mechanism, and those are different
  questions that probably want different configuration surfaces. Second, loss type is not coverage —
  a coverage is what the policy insures, a loss type is what happened — and a configuration
  described as "coverages" that actually selects loss types would be the same wrong-lookup defect
  items 4d and 4g each cost a session to remove.

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

  **Half-resolved by the item 4j merge (`22d672e`, 2026-08-18), and the split was deliberate.** The
  prefix *list* is now caller-supplied configuration with no default — the paragraph above argued
  that parameterizing it alone "would not" resolve the concern, and that is exactly right and
  exactly why it was done anyway: the list is a scalar set that a parameter genuinely resolves,
  while the shape is not, and conflating them would have produced something reading as configurable
  without being so. `POLICY_NUMBER_PATTERN` is now shape-only (`^([A-Z]{2})-\d{7}$`) with the
  captured prefix checked against the configured set. **What remains open is exactly the harder
  half:** two letters, a hyphen, seven digits is still a domain-wide assumption about how every
  carrier numbers policies, and it is still structural rather than parametric. The generalization
  away from a named estate strengthened this rather than changing it — with no estate, the shape has
  nothing left justifying it, and phase 2's adapter layer is now the only defensible home. Do not
  read 4j as having closed this entry.

## Synthetic data

- No real policy numbers, names, addresses, phone numbers, or claim numbers appear anywhere in
  specs, fixtures, or tests. Names are fictional; phone numbers stay in the 555-01xx reserved
  range.
- Carrier identity data (names, NAIC codes) is public regulatory information, used because the
  design targets a real, named carrier estate rather than a generic one. Everything else — every
  notice, every policy number, every loss description — is fabricated.
