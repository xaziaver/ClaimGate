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
- **"Policy administration system" in this project's documents means the carrier's core system
  including its claims side — noted 2026-09-01.** `PHASE2_DESIGN.md` has claim numbers minted by
  "the policy administration system"; in practice policy and claims are separate modules with
  separate interfaces (Duck Creek and Guidewire both ship them so), and a claims manager would not
  use the term for the claims side. The wording is left as history; `PHASE3_DESIGN.md` uses
  "policy port" and "claims port" or names two adapters, and says which.
  
## Carried requirements — decided, not yet built

- **One receipt clock, not two — decided 2026-08-24, advisor-recommended, human-ratified.**
  `store.py`'s `receive_notice` timestamps the payload record and the `RECEIVED` audit entry with
  `datetime.now(UTC)`, while `notice_intake.py`'s `submit_notice` separately judges the notice
  against the `submitted_at` parameter the shell was given — two different clock reads for one
  statutory receipt event (Fla. Stat. 627.70131(1)(a)'s acknowledgment clock; `PHASE2_DESIGN.md`'s
  Record state model, "the timestamp is set once at capture"). Invisible to every scenario today
  because calls are synchronous and the gap between the two reads is microseconds; wrong the moment
  a transport layer, a queue, or any asynchronous boundary sits between the two calls.

  **Decided:** the receipt instant is `submitted_at`, passed through to the store; `now()` is not
  consulted for any receipt-adjacent timestamp. Not fixed now — build it during item 5d's port of
  the store to SQLite, since that port rewrites `receive_notice` and its callers anyway. Flag it in
  that item's own report as design-consistency work the port carries, not something any
  `idempotency.feature` scenario mandates: no scenario asserts a literal timestamp value, for the
  same reason `notice_intake.feature`'s own Rule 2 comment already gives — `occurred_at` is real
  wall-clock time at the moment a run executes and cannot be stated as a spec literal.

  **Extended to the resolution path, 2026-08-25, stated by the instruction that opened item 5e.**
  Every timestamp the resolution endpoint writes — the resolution-received instant on the notice, the
  `occurred_at` of the entry it adds to the audit trail, and the resolution payload record's own — is
  the caller-supplied instant for that call, never `now()`. The receipt instant the notice already
  carries is untouched by a resolution, per the Record state model's "set once at capture and never
  recomputed on any later transition." This is the same rule as above rather than a second one, but
  it is written down because the entry above reasons entirely about receipt, and item 5e writes
  timestamps that are not receipts: `PHASE2_DESIGN.md`'s tolling section wants the pend instant and
  the resolution-received instant recorded "precisely, in UTC," and two clock reads on one resolution
  would put an unexplained gap between the two ends of the interval something downstream computes
  tolling from.

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
- **One timezone per jurisdiction, and Florida's is `America/New_York` — advisor-recommended,
  human-ratified, 2026-08-26.** Item 5g keys the statutory map by jurisdiction code, so a
  jurisdiction holds one IANA timezone and Florida's Central-zone counties are dated Eastern along
  with the rest of the state. **Corrected 2026-08-26: the county list first recorded here was
  wrong.** The `America/Chicago` zone is Escambia, Santa Rosa, Okaloosa, Walton, Holmes, Washington,
  Bay, Jackson and Calhoun entirely, plus the part of Gulf County west of the boundary; the line is
  **49 CFR 71.5(f)**, running down the Apalachicola River to the Jackson River, along the
  Intracoastal Waterway to the west line of Gulf County, then south. Verified **2026-08-26** against
  the eCFR text via a search excerpt rather than a full-section fetch — the same weaker provenance
  class `STATUTORY_REGISTER.md` states for its hurricane and sinkhole entries, and it should be
  re-verified against the full section before anything depends on the boundary itself rather than on
  the fact that a boundary exists.

  **The ratified decision is unchanged by the correction.** The skew direction and both tolerant
  effects below follow from Eastern being ahead of Central, not from how many counties are Central,
  so nothing that was approved on 2026-08-26 moves. What the correction changes is the *recorded
  cost*: "most of Walton" made this read as a Pensacola footnote, and the zone in fact contains Bay
  County — Panama City and Panama City Beach — along with the Destin and Fort Walton Beach corridor,
  roughly a million residents of a disproportionately coastal, wind-exposed residential market. That
  is the population this one-entry map dates under the wrong clock for one hour a day, and it is
  worth knowing accurately even when the effects are tolerant.

  The entry above records that this is a real divergence; this entry records that it is accepted for
  phase 2, and what it actually costs, recomputed rather than carried over from the first statement
  of it. **Eastern's date is never behind Central's**, so the skew is one-directional and both of its
  effects are tolerant:

  - A loss dated tomorrow by a Central-clock reporter passes the future-date check unflagged,
    because Eastern's today has already reached that date. **No false `LOSS_DATE_IN_FUTURE` is
    possible** — the failure this whole axis exists to prevent cannot occur in this direction.
  - The late-reporting interval reads up to one day long, so an advisory indicator flags early
    rather than late.

  It applies for one hour a day, and a wrong block is the only outcome that would be unacceptable.
  Corrected from the first drafting of item 5g's spec, which stated the direction backwards and
  called it "a real wrong answer around midnight Central" on the blocking field. Revisit when a
  jurisdiction key finer than the state exists, not before.

- **`property_state` is matched exactly, and a miss is marked rather than normalized —
  advisor-recommended, human-ratified, 2026-08-26.** The jurisdiction lookup is an exact match on
  the value as submitted. `fl`, a misspelling, a full state name and a state this deployment has no
  entry for all resolve the same way: no jurisdiction, and a `jurisdiction_unsupported` marking for
  a person. Nothing is upper-cased, trimmed into a match, or mapped from a name to a code. Case
  folding looks free and is not: it is the first step of a chain that ends in inferring what the
  reporter meant, on the field that selects which state's law applies. A marked notice is still
  received, still triaged, and still visible; a normalized one is judged under a jurisdiction nobody
  chose. Specified by `features/jurisdiction_selection.feature`'s `fl` row, which exists to pin this
  class rather than to document a spelling.

- **The zone that dates a resolution's SIU interval comes from the merged view, not from what was
  known at receipt — advisor-recommended, human-ratified, 2026-08-26.** Item 5f decision 2 fixes the
  *instant* the late-reporting interval is counted from as the notice's own receipt, and says nothing
  about the *timezone* that instant is converted under — a gap that only opens once the zone stops
  riding the submission and starts coming from `property_state`, which a reviewer can supply at
  resolution like any other field. The zone is resolved from the notice's current merged view:
  where the insured property is, is a fact about the risk, not about the moment the notice arrived,
  and a notice whose property state arrives later should have its interval become computable rather
  than stay permanently unevaluated. **Corrected 2026-08-26: the path this sentence originally
  named — "a notice that reached `TRIAGED` unsupported and is later told where the property is" — is
  unreachable, and the decision does not rest on it.** `features/resolution.feature`'s first rule
  answers a resolution on any notice that is not `PENDED` with `409` and persists nothing, so a
  notice that reached `TRIAGED` can never be told anything afterwards. The reachable form, and the
  one `features/jurisdiction_selection.feature`'s new scenarios are built on, is a notice pended for
  an unrelated blocker — its policy number absent — whose resolution supplies the property state
  alongside the missing field. The decision itself stands as ratified. This rewrites
  nothing: the SIU trail is append-only, so the intake-time `NOT_EVALUATED` observation stands as
  the evaluation that was actually made then, and the resolution appends a second one beside it.
  Both carry their own `evaluated_at`, so which is which is readable from the trail without a
  convention.
- **`jurisdiction_timezone` is removed from the submission surface rather than kept beside
  `property_state` — advisor-recommended, human-ratified, 2026-08-26.** Once the zone comes from the
  jurisdiction map keyed on the property's state, a caller-supplied timezone name is a second source
  for one fact, and two sources need a precedence rule saying which wins when they disagree. Nobody
  has ratified such a rule, and defaulting one would be exactly the class `CLAUDE.md` forbids — a
  rule nobody approved, on the field that decides which state's law applies. Keeping the parameter
  alive only inside step definitions is not a middle course either: that re-creates item 4g's
  recorded defect, configuration honoured by the harness that no specification states, where the
  tests pass because the harness supplies something the product does not.

  **Cost, measured rather than estimated (2026-08-26).** Four locked specs reopen. Three —
  `features/resolution.feature`, `features/idempotency.feature` and `features/siu_separation.feature`
  — are Background-only re-approvals: `And the jurisdiction observes "America/New_York"` becomes
  `And the insured property is in "FL"`, Background steps generate no mutants, and all three were
  verified locator-*and*-signature identical against their locked content, not merely
  count-identical (97, 40 and 53 mutants, zero locators moved, zero signatures changed).
  `features/notice_intake.feature` additionally loses its Rule 5 whole, superseded rather than
  merely edited: 48 mutants to 36, losing exactly the 12 in its two scenarios, every other locator
  and signature byte-identical, and no mutant approval touched because that file carries none
  (verified against `gauntlet.lock.json`, not assumed). The two-zone discrimination those scenarios
  carried is re-homed to item 5g's jurisdiction swappability test, and that obligation is written
  into `QUEUE.md`'s item 5g entry so the test cannot silently shrink to a single-fixture existence
  check.
- **The future-dated-loss determination is off every outward surface in phase 2; the jurisdiction
  marking is on `NoticeView` — advisor-recommended, human-ratified, 2026-08-27.** The two halves of
  item 5g's jurisdiction work are surfaced differently on purpose. The marking is readable, because
  a marking nobody can read is not a marking. The determination is not, and the basis is three
  facts rather than a preference: the case that actually blocks already surfaces as the
  `LOSS_DATE_IN_FUTURE` blocker, so nothing is hidden that a reporter or a reviewer needs; the
  determination has no phase-2 consumer, so nothing reads it; and surfacing it collides with
  `features/siu_separation.feature`'s leak negatives, which scan a serialized surface **as text**
  and would therefore match a legitimate `NO_JURISDICTION_DATE` determination reason — the one
  spelling deliberately shared by two enumerations, entered into both as ratified. The check that
  exists to catch a leak would fail on a value that is not one. The determination sits where
  `pended_at` and `resolved_at` already sit: on the record, not in the view.

  **Ordering constraint for whichever later item wants it visible.** Decide the leak-scan exclusion
  mechanism *first*, then the surface — not the other way round. By field path rather than by token
  text is the likely shape, since a text scan cannot distinguish a shared code appearing in its
  legitimate place from the same code appearing where it leaked, and no renaming of either
  enumeration's copy is available: the shared spelling is the ratified decision, not an accident.
  Note that the collision is **latent today only because both leak scenarios use `FL` notices**,
  whose determination reason is empty. That is a property of the fixtures, not of the design, so a
  later item that changes either scenario's jurisdiction surfaces the collision without touching
  the determination at all.
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

- **The payload reference recipe — advisor-ratified, 2026-08-24.** SHA-256 over the submitted
  fields, serialized as JSON with `sort_keys=True` and `default=str`. This is the reference by which
  a reporter and a carrier name the same communication - "A refused submission is still a received
  communication," above, and "A carrier this deployment administers but cannot configure is our
  defect, not the reporter's," both rely on a hash existing without saying what it is computed over.
  Recorded because an unrecorded serialization is an unreproducible reference: two sessions hashing
  the "same" payload with a different key order, a different float-vs-Decimal rendering, or a
  different treatment of an absent field would produce different references for what a reporter and
  a carrier would call the same submission, defeating the reference's own purpose. `sort_keys=True`
  makes field order irrelevant; `default=str` is what lets a `Decimal` loss amount serialize at all.

  **Revisit when a literal HTTP layer exists.** This recipe hashes the shell's own parsed field
  mapping, because nothing in this project has raw request bytes to hash yet - every item through 5c
  calls domain and shell functions directly, never over the wire. "Verbatim" in `PHASE2_DESIGN.md`'s
  audit log section can then mean the raw request body itself, which is a stronger and simpler claim
  than hashing a mapping this shell already parsed; whether that's a real behavior change or just a
  documentation correction depends on whether parsing before hashing has ever hidden a distinction
  the raw bytes would have kept (e.g. two payloads differing only in insignificant whitespace or key
  casing that the parse step normalizes away). Not decided now - flagged for whoever builds that
  layer.

- **Idempotency: what a repeated key is compared against, and when the window closes —
  advisor-recommended, human-ratified 2026-08-24.** `PHASE2_DESIGN.md`'s "Idempotency" section and
  status-code table decided that a key reused with a different payload is `409` and that keys
  expire after 24 hours, and decided neither how "different" is judged nor what happens at exactly
  24 hours. Item 5d's first draft escalated both rather than guess (correctly, under `CLAUDE.md`'s
  never-default constraint). Decided:

  1. **"Different payload" is a different payload reference** — the SHA-256 recipe recorded above
     under "The payload reference recipe", already persisted on every created notice since item 5c's
     close-out fix. The resubmission's reference is computed by the same recipe and compared to the
     reference linked to the notice that `(carrier_code, idempotency_key)` resolves to. Equal is a
     replay (`200`); unequal is a conflict (`409`). One recipe, one definition of "the same
     submission" — a second comparison rule would be a second source of truth for the same
     question. This is what Stripe-style idempotency does (compare request content, refuse a
     mismatch); the IETF Idempotency-Key draft prescribes the same comparison. The draft's
     preferred status code for a mismatch differs from `409` and was not re-read this session; the
     `409` decision stands as already recorded and is not reopened.
  2. **The key is envelope and is examined before the schema boundary.** Order on `POST /notices`:
     carrier identity, then the idempotency lookup, then the loss-date schema check, then receipt.
     Consequence: a conflicting resubmission whose loss date does not parse gets `409`, not `400`.
     This also means `PHASE2_DESIGN.md`'s "never returns a 4xx once a payload clears the schema
     boundary" remains true — `409` is decided before that boundary; see the annotation there.
  3. **A `409` creates no notice and adds no audit entry to the original, but the conflicting
     content is kept with a reference of its own** — the same treatment as a schema-invalid `400`,
     deliberately unlike the unknown-carrier `400` that persists nothing. An unknown carrier creates
     no duty here; a mis-keyed submission from an administered carrier may be a real loss, and the
     record of what arrived is cheap to keep and expensive to reconstruct. Design call, not an
     industry standard.
  4. **A key is remembered only by the notice it created.** The uniqueness constraint lives on the
     notice table. A submission refused at the schema boundary creates no notice and its key is not
     remembered against the refusal; the next use of that key is judged on its own. Keeping a
     separate table of attempts would make a refused submission's key block the corrected
     resubmission the caller is most likely to send next. *Corrected 2026-08-24, advisor,
     before implementation: not the notice table. A `UNIQUE(carrier_code, idempotency_key)`
     there would refuse the post-expiry fresh notice that Rule 1's third row requires. The key
     record is its own table, one row per pair, written only inside the transaction that
     creates a notice, and replaced — not duplicated — when an expired key is reused, so the
     new notice holds the key and the old one no longer does. The substance stands: a refused
     submission writes no key row and can block nothing.*
  5. **The 24-hour window is half-open.** A replay is within the window while
     `replay_submitted_at - submitted_at < 24h`, and past it at equality. Basis: RFC 9111 §4.2 —
     a stored response is fresh only while `freshness_lifetime > current_age`, stale at equality
     (verified 2026-08-24 against rfc-editor.org's text). It is the convention every caller's HTTP
     stack already applies to a TTL, so a client cannot be surprised by it. Both instants are the
     receipt clock (`submitted_at`, per the one-receipt-clock decision above), never `now()`.

  **Carried to item 5e:** a scenario that a replay of a notice resolved `PENDED → TRIAGED` reports
  `TRIAGED`. Item 5d proves only that the replayed state comes from the notice rather than a
  constant (a `PENDED` original replays as `PENDED`); the "may have moved since" half of the design
  text is unprovable until a notice can move.

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

- **Phase 3 designs the policy administration adapter against three named exemplar system shapes
  and ships two conforming implementations — advisor-recommended, human-ratified, 2026-09-01.**
  There is no target deployment; the human named Duck Creek as one example. An interface designed
  against zero real systems comes out shaped like our own domain model, and one implementation
  cannot show that has not happened. The third exemplar shape — a periodic flat-file extract with
  no live query — is the one that stops the interface assuming a synchronous answer exists.
  **Cost:** phase 3 roughly doubles, and the second implementation has no customer asking for it.
  The full argument is `ROADMAP.md`, "Why phase 3 ships two implementations".

- **Coverage verification at intake is clerical, and it is not coverage determination —
  advisor-recommended, human-ratified as the recommendation to carry into `PHASE3_DESIGN.md`,
  2026-09-01.** Verification asks whether a policy exists matching the identifiers given and
  whether a term of it was in force at the loss date. Determination asks whether that policy covers
  this loss — perils, exclusions, endorsements, limits, insurable interest — and is an adjuster and
  coverage-counsel function, downstream, permanently (`ROADMAP.md`). Four consequences for the
  adapter, each from claims-operations practice rather than statute, so no primary source of the
  kind `STATUTORY_REGISTER.md` requires exists for them:
  - *Coverage attaches to a term, not to a policy.* The loss date selects the term; the adapter
    returns that term with its effective and expiration dates and its status at that date.
    Residential terms conventionally incept and expire at 12:01 a.m. standard time at the described
    property, and FNOL captures a loss date, not an instant, so a loss on a term boundary is
    ambiguous at the granularity captured — a third value, not a negative, under the standing
    not-evaluated rule.
  - *The answer is not idempotent.* Policy administration systems process backdated transactions,
    so "in force on 2026-06-01?" can answer differently on two different days. Every verification
    result is stored with the adapter's as-of instant, the same discipline `RULESET_VERSION`
    applies to domain decisions. A stored "in force" with no as-of stamp is indefensible in a
    coverage dispute later.
  - *Search, not fetch.* A large share of real notices arrive with no policy number or a wrong one
    — contractors, public adjusters, mortgagees, agents from memory. Intake resolves by named
    insured, risk address and loss date. `POLICY_NUMBER_PATTERN`'s role as a blocker is reopened in
    phase 3 on this ground.
  - *Recommended outcome split, for phase 3's design to ratify:* an unmatched policy is a blocker —
    intake has nothing actionable — and the notice lands `PENDED` for a reviewer to correct
    identifiers through resolution; an out-of-force term is **not** a blocker — the notice is real
    and the question is coverage — and lands `TRIAGED` with the verification result as an attribute,
    on `jurisdiction_unsupported`'s precedent.
- **Policy identification leaves the domain: `POLICY_NUMBER_MALFORMED` and
  `recognized_policy_number_prefixes` are retired in phase 3 — advisor-recommended, ratified with
  `PHASE3_DESIGN.md`.** Reverses items 4b and 4j. A wrong number beside a correct insured name and
  risk address is a match once the policy port searches; today it pends the notice before any
  search can run. The 2026-08-17 entry above already concluded the pattern belonged to the adapter
  layer. Cost and measured floor are in `PHASE3_DESIGN.md`, "Identifiers".
- **The continuous-coverage derivation is a domain rule, not port logic — advisor-recommended,
  ratified with `PHASE3_DESIGN.md`.** Amends the 2026-08-14 entry under "Data we do not have at
  intake", which has the adapter deriving the date: the semantics are unchanged in every clause —
  on the risk, surviving rewrite and retroactive reinstatement, reset by a genuine lapse — and only
  the location moves, so the lapse rule gets a specification and a mutation score. The port
  supplies term history and nothing else.
- **A port fault lands `TRIAGED` with verification `NOT_EVALUATED`; it does not pend —
  advisor-recommended, ratified with `PHASE3_DESIGN.md`.** Item 4h's principle: a blocker is
  something a reviewer can supply. Nobody can supply an outage, and pending a book on
  infrastructure asks humans to clear a machine fault one notice at a time. Phase 6 owns the
  system re-evaluation this creates a need for.

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

- **Not a threshold, recorded beside them because it is the project's other hand-declared value and
  fails the same way: `RULESET_VERSION` is a bare date and cannot label two rule changes made on one
  day.** Advisor-found, human-ratified 2026-08-27. First hit that day, when items 5g and 5h both
  changed rule behaviour under `src/claimgate/domain/`: 5g bumped the label to `2026-08-27`, and 5h -
  which changed the loss-date rule, the future-dated-loss determination and the SIU entry contract -
  had no distinct value left to bump it to. **Accepted without a code change**, on two grounds.
  `main` only ever exposes the merged state, and 5g's ruleset reached `main` the same day 5h's did,
  so no consumer ever observed the 5g-only ruleset and no stored row is mislabelled against anything
  that was in force on `main`. And nothing yet distinguishes same-day rulesets: no consumer reads the
  label finer than by day. **Revisit with an edition-plus-revision label** - the date plus a
  within-day counter - **before any consumer must make that distinction**, because the moment one
  does, every row written on a two-ruleset day becomes ambiguous retroactively and no later change
  can disambiguate it. `tests/unit/test_ruleset.py`'s ISO-format assertion is the deliberate
  tripwire: the format cannot be widened by accident, so anyone who needs a finer label has to
  decide it consciously rather than append a suffix and move on.

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

- **Item 5h, three decisions, advisor-recommended, human-ratified, 2026-08-27.** Taken together at
  the point the item's spec was drafted and before any of it was implemented, so the implementation
  chooses none of them.

  **(1) `NO_LOSS_DATE` enters the future-dated-loss determination's closed reason enumeration** as
  its second member, beside `NO_JURISDICTION_DATE`. It is not added to the SIU indicator
  enumeration — see (3). The two enumerations share the `NO_JURISDICTION_DATE` spelling and are not
  the same set; they are scoped to their own subjects and grow independently, and this decision
  grows exactly one of them.

  **(2) Precedence: `NO_LOSS_DATE` outranks `NO_JURISDICTION_DATE`, which outranks
  `NO_THRESHOLD_CONFIGURED`.** The existing tie-break — name the gap that would still block
  evaluation if the other were closed — decides the lower pair and is silent on the upper one: with
  neither a loss date nor a jurisdiction, closing either leaves the other. The ground for the
  direction is that the loss date is the determination's subject and today only the yardstick it is
  held against, and a missing subject is the more basic absence.

  **The direction is low-stakes; the assertion is not.** In the both-absent case each absence is
  already independently visible on the record — the loss date as `MISSING_REQUIRED_FIELD:loss_date`
  among the blockers, the jurisdiction as the unsupported marking — so a reader loses nothing
  whichever reason the determination names. What was at stake is that **until item 5j's row existed
  in `jurisdiction_selection.feature`, this ordering was protected by a source comment and nothing
  else**: no test failed on a reordering, and mutation does not reorder statements. That is item 4k's
  exact shape, and it is why this decision was ratified together with the creation of item 5j rather
  than separately from it.

  **Closed 2026-08-30, item 5j merged at `806f403`.** That row exists: `jurisdiction_selection.feature`'s
  Rule 3 carries an unsupported property state with no loss date, asserting `NOT_EVALUATED:NO_LOSS_DATE`,
  so a reordering of the two checks now fails that scenario instead of passing unnoticed. The source
  comment in `_determine_future_dated_loss` cites the row rather than standing in for it.

  **(3) The SIU indicators gain no third `NOT_EVALUATED` reason for an absent loss date.** An
  indicator evaluation reached with no loss date raises — the `find_duplicates` shape from item 3,
  where an unreachable value is a caller contract violation rather than a business outcome to
  record. Basis and fragility belong together here: this holds **because** evaluation runs only on a
  transition into `TRIAGED`, on both the intake and the resolution paths, and an absent loss date
  now pends the notice so that transition never happens. It stops holding the moment anything
  evaluates indicators on a pended notice, and whoever builds that revisits this decision then
  rather than discovering it as a crash.

  **(4) Ratified 2026-08-27, post-implementation: duplicate detection reached with no loss date
  raises `ValueError`.** Advisor-recommended, human-ratified. Recorded as a fourth decision rather
  than folded into (3) because it was taken *after* the implementation, not before it: (1)-(3) were
  settled at drafting and the implementation chose none of them, while this question only appeared
  when `date | None` forced `find_duplicates` to answer it. The entry keeps its "three decisions"
  title deliberately - `domain/siu.py`, `domain/validation.py` and `QUEUE.md` all cite it by that
  name, and renaming it would silently break every pointer.

  Grounds, in the order they decide it. The match window is arithmetic on the loss date, so with no
  loss date there is no coherent result to return - not a `NOT_EVALUATED` outcome, an absence of any
  outcome to name. `find_duplicates` has no shell caller at all yet, so the guard is a contract on an
  unwired function; the item that wires it decides where the check runs on the wired path, and this
  decision does not pre-empt that. The guard sits after the notice-type exclusion, so an excluded
  notice type still resolves without ever reading a date, and that placement is asserted by a test
  rather than left to the reading. **The alternative - a reason code in duplicate detection's closed
  enumeration - was considered and declined**, on the ground (3) uses for SIU: an unreachable value
  is a caller contract violation, not a business outcome to record, and both enumerations stay closed
  at two.

## Data we do not have at intake

**Annotation, 2026-09-01: every reference in this section and elsewhere in this file to "phase 2's
adapter layer" or "the phase-2 adapter" predates phase 2's close on 2026-08-30. Phase 2 shipped no
policy administration adapter; the adapter is phase 3 (`ROADMAP.md`, `PHASE2_DESIGN.md`). "Each of
the three policy administration systems" refers to the estate this project stopped targeting on
2026-08-17. The entries are left as written because they are dated history; read "phase 2's
adapter" as "phase 3's".**

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
  Answers the mechanics the decision above left open, not a separate question. **Location amended 2026-09-01: the derivation described in this entry is a domain rule in phase 3; the port supplies the history (`PHASE3_DESIGN.md`). Semantics unchanged.** **Stated as of the loss date 2026-09-04 (item 7b, advisor-recommended, human-ratified): the date is the start of the unbroken run of coverage in force on the loss date; a lapse and reinstatement recorded after the loss cannot move it.** The adapter does not
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
- **Term-in-force judgments beyond the locked spec — agent-proposed, advisor-reviewed,
  human-ratified 2026-09-04.** `features/coverage_verification.feature` (locked at `dfb1284`, item
  7a) states the rule where `PHASE3_DESIGN.md` was precise enough to draft; the rule as built also
  answers histories the spec does not state. Each answer below was proposed in the implementation,
  re-driven independently by the advisor, and ratified from the committed code — none was
  defaulted.
  **Reinstatement is one transaction shape, told apart by its date.** A reinstatement dated on the
  cancellation it follows is retroactive: it rescinds the cancellation and the lapse never existed.
  One dated later leaves a lapse between the two. That is how a policy administration system
  records the two kinds, and the port carries no flag. The test API's "reinstated retroactively as
  of" refuses an as-of date that is not the cancellation's, rather than quietly recording a lapse
  under a phrase that promised none.
  **A boundary day is a date on which coverage changes within the day.** A term's effective and
  expiration dates, and the effective date of a standing cancellation or reinstatement, are
  boundary days: coverage incepts or ends at 12:01 a.m. on them and intake holds a date, not an
  instant. A cancelled term's nominal expiration date and the effective date of a term cancelled
  flat from inception are not — coverage changes on neither, because the term did not run to the
  one and never ran on the other. This applies the spec's own precedence for a rescinded date,
  that nothing turns on the loss time there, one step past what the spec states.
  **A malformed history raises; reason codes stay port-owned.** The rule's `NOT_EVALUATED` reasons
  are the policy source's, passed through, and a domain-originated code would be a new entry in a
  closed enumeration. A history the rule cannot answer is therefore a `ValueError` on the caller: a
  term expiring on or before it takes effect; a status change dated outside its term; a
  reinstatement with no cancellation to reinstate, one dated before its cancellation included; a
  cancellation on a term already cancelled; two terms in force on the same day — overlapping
  coverage, added at ratification after the advisor showed that the implementation's first-stated
  tie-break made a citation depend on input order; and that rule's residue, two terms cancelled the
  same date both holding the loss date with no day in force shared, which only a rewrite voided on
  its own effective date produces. Item 7e decides what the ports map to `SOURCE_MALFORMED` from
  these.
  **An obtained history with no terms is `NOT_IN_FORCE` citing nothing.** No term ran on the date,
  which is what the value says. Whether an unbound submission is searchable at all is item 7e's
  note to answer at the port, not this rule's.
  **`NOT_IN_FORCE` cites the latest standing cancellation on or before the loss date, and its
  term.** A cancelled, rewritten, and cancelled-again history cites the second term; a term
  cancelled, reinstated with a lapse, and cancelled again cites the cancellation that opened the
  lapse the date is in. Ties are unreachable by the malformed-overlap rule above, never broken by
  input order. The order in which terms and status changes are supplied is otherwise irrelevant,
  and the cited term is the term as supplied.
- **Continuous-coverage derivation: decisions taken before the spec was locked —
  advisor-recommended, human-ratified 2026-09-04.** `features/continuous_coverage.feature` (item 7b)
  was amended after review of its first draft found four gaps. (1) *As of the loss date.* The
  derivation takes the loss date, like the term-in-force rule, and reads the unbroken run of
  coverage in force on that day. A late-reported loss on a policy that lapsed and was reinstated
  afterwards must not derive the reinstatement date: that fires the recent-inception indicator
  falsely into the restricted-read table. A loss date no supplied run covers is `NOT_EVALUATED` with
  reason `NO_COVERAGE_ON_LOSS_DATE` — the term-in-force rule already answers that notice, and the
  indicator is moot. A boundary day belongs to the run it bounds: a loss on a cancellation date
  derives that run's start; on the day coverage resumed after a lapse, that day. (2) *Takeout and
  assumption business.* The 2026-08-14 entry's "prior carrier's continuous-coverage date as a data
  point, not a reset" had no input in the first draft, so every depopulation policy would have
  derived the assumption date. The history now carries an optional prior-coverage interval
  (effective, ending) the source states; if it reaches the first own term of the run — ending on, or
  after, that term's effective date — the derived date is the prior interval's effective date; a gap
  of even one day leaves the own term's date. The term-in-force rule reads `terms` only and ignores
  this interval: prior-carrier days are never in force with this carrier. Whether a given policy
  administration system carries a prior-coverage *inception* date rather than only a prior carrier
  and expiration is carrier-estate-dependent; a port that lacks it supplies nothing, and the rule
  concludes from own terms. (3) *The source's history horizon.* "Supplies history from" a date means
  every term in force on or after that date is supplied and terms that ended before it may be
  missing — the shape a legacy conversion produces, where the term in force migrates with its true
  effective date. A supplied term effective before the horizon is therefore well-formed, not
  malformed (resolving the agent's third design point of 2026-09-04). The test is on the derived
  date: conclusive iff the run's start is strictly after the horizon; on or before it is
  `NOT_EVALUATED` with reason `HISTORY_MAY_PREDATE_SOURCE`. A loss dated before the horizon and
  covered by no supplied term is `HISTORY_MAY_PREDATE_SOURCE`, not `NO_COVERAGE_ON_LOSS_DATE`; a gap
  after the horizon is one the source can see. The horizon test is applied to the own-term run
  before any prior-coverage extension: a run whose own start is on or before the horizon is
  `NOT_EVALUATED` even when a prior interval is stated. An absent horizon means the source asserts a
  complete history — a silent failure mode if a port forgets it, so item 7e's contract suite asserts
  every port implementation states one; that obligation is recorded in `QUEUE.md`'s 7e entry. (4)
  *Reason ownership.* `HISTORY_MAY_PREDATE_SOURCE` and `NO_COVERAGE_ON_LOSS_DATE` are domain-owned,
  in a closed enumeration this feature owns; `SOURCE_UNAVAILABLE` and any other not-obtained reason
  pass through from the port as in 7a. This does not contradict 7a's judgment that
  inconsistent-source reasons are the port's: a truncation boundary and an uncovered loss date are
  well-formed data the source states truthfully, not contradictions within the history. (5)
  *Boundary rows.* A renewal effective one day after expiration is a lapse — terms end at 12:01 a.m.
  on the expiration date, and a payment grace period does not move the term's dates; a renewal
  issued late with its effective date backdated to the expiration is seamless and arrives as such.
  **Addendum, three cases beyond the amended spec — advisor-recommended, human-ratified 2026-09-04,
  coded with item 7b's implementation.** (a) A loss dated exactly on the horizon day and covered by
  no supplied term is `HISTORY_MAY_PREDATE_SOURCE`: "on or before the horizon" is the conservative
  side, matching the run-start test. (b) A loss on an expiration date with no renewal derives that
  run's start. (c) A loss on the first day of a first term derives that day.
- **Continuous-coverage judgments beyond the locked spec — agent-proposed, advisor-reviewed,
  human-ratified 2026-09-05.** `features/continuous_coverage.feature` (locked at `c5c9b1c`, item 7b)
  states the rule; the rule as built (`c434fca`, judgment 5 reversed at `e2a7cc5`) also answers
  histories the spec does not state. Each answer below was proposed in the implementation, reported
  in `QUEUE.md`'s status section on 2026-09-04, and ratified from the committed code; one was
  reversed. (1) The result is `DERIVED` with the date or `NOT_EVALUATED` with a reason, nothing else
  recorded. (2) "Reaches" is measured against the day the run began: the first own term's effective
  date, except for a run opened by a lapsed reinstatement, where it is the reinstatement date. (3) A
  prior interval beginning after the run did cannot move the date later; the derived date is the
  earlier of the two starts. (4) A prior interval extends whichever run holds the loss date, a later
  run across a gap in own terms included when the interval ends on or after that run began — the
  prior carrier covered the gap; one ending inside an earlier run does not reach. A prior carrier
  still on risk across a gap in this carrier's own terms is dual coverage and rare; this is the
  consistent reading, not an expected shape. (5) A prior interval is malformed when it ends on or
  before it takes effect, matching the term rule's convention; the agent's first cut accepted a
  zero-day interval on a literal reading of the instruction's "before", reported it, and was
  reversed. (6) A loss dated inside the prior interval and before any own term is
  `NO_COVERAGE_ON_LOSS_DATE`: the interval extends a run, it is not one. (7) A malformed prior
  interval raises for any loss date on an obtained history, as malformed terms do; on a not-obtained
  history it is ignored and the source's reason is the answer, and a not-obtained history with no
  reason is an error. (8) An obtained history with no terms holds no date:
  `NO_COVERAGE_ON_LOSS_DATE`, or `HISTORY_MAY_PREDATE_SOURCE` when the loss is on or before a stated
  horizon. (9) A stated prior interval may reach back before the horizon once the own run's start
  passes the horizon test — a data point the source states, not a term that might be missing. (10) A
  loss covered by a supplied term from before the horizon takes the run-start test,
  `HISTORY_MAY_PREDATE_SOURCE`, not the uncovered one. (11) Input order of terms and of status
  changes is irrelevant. Noted 2026-09-05: The advisor's pre-lock simulation model tested the
  uncovered-loss horizon case with strictly-before where the ratified rule is on-or-before; no
  scenario exercised the difference, so the simulation matched the gate regardless. A simulation
  checks only what the spec exercises; judgment 8's second clause is where the code holds the
  ratified reading.
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

- **Persistence engine: SQLite via the stdlib `sqlite3` module, decided 2026-08-24,
  advisor-recommended, human-ratified.** Item 5d's own design text requires uniqueness on
  `(carrier_code, idempotency_key)` "enforced by a database constraint" (`PHASE2_DESIGN.md`,
  "Idempotency") — a literal `UNIQUE` constraint satisfies that with zero new dependencies. The
  two-write receipt (Record state model, above) becomes a single real transaction instead of two
  in-memory dict writes that happen to share a process, which is what turns `store.py`'s "the raw
  payload and the RECEIVED write are one statutory fact" comment into an enforced guarantee rather
  than a comment describing call order. Item 5g's swappability proofs are data-swaps — a different
  carrier set, a different jurisdiction map — not engine-swaps, so nothing in this project's design
  asks persistence itself to be pluggable; nothing is lost committing to one engine now. STRICT
  tables, constraints declared in the schema, no ORM.

  **Costs, stated rather than discovered later:** single-writer concurrency, and no server-side
  access control beyond what the process itself enforces. Both accepted for phase 2. Both are
  revisited at phase 3's adapter boundary — the same boundary that already owns policy
  administration and claim-number minting (`CLAUDE.md`) — not before. See `PHASE2_DESIGN.md`'s
  "Persistence engine" section for the same decision in design-doc voice.

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

- **Item 5e's resolution endpoint: five points the design leaves open — escalated 2026-08-25,
  undecided, nothing drafted against any of them.** `PHASE2_DESIGN.md`'s "Pending resolution and
  tolling" section, its audit-log entry schema, and its closed status-code table together settle the
  endpoint's `200` and `422` outcomes, its `409`, the `outcome=REFUSED` entry a refusal still writes,
  and the immutable per-resolution payload record. Each point below is something a scenario in
  `features/resolution.feature` would have to answer by defaulting, which `CLAUDE.md`'s never-default
  constraint forbids. They are listed in the order a scenario meets them.

  1. **What a resolution payload may contain.** The body is "`actor_id` (required), the supplemental
     field values, an optional note" — and "the supplemental field values" is never given a set. Two
     readings, and they are not close: only the fields named by the notice's own recorded blockers,
     or any field the original submission could have carried. The second lets a reviewer change the
     loss type of a notice pended for a missing policy number, moving severity and queue on a notice
     nobody said was wrong about its peril; the first cannot express a correction to a field that was
     present but wrong, which is a real reviewer action a `PENDED` notice invites. The design's own
     "the current view of a notice is derived from that ordered sequence" is true under either.

  2. **What a resolution is evaluated against.** Two questions that arrive together.
     **(a) Which rules run.** "Supplied data clears every blocker" and "`422` with the current
     blockers" point opposite ways: re-checking only the blockers already recorded, or re-running the
     full validation over the merged current view. Under the second a resolution can introduce a
     blocker the notice never had — a supplied policy number that is itself malformed — and the
     design has no word for that outcome.
     **(b) Which calendar date.** `LOSS_DATE_IN_FUTURE` is a blocker whose truth changes with the
     date alone. If re-evaluation uses the resolution instant's jurisdiction date, a notice pended
     for a future loss date clears itself on an empty payload with no reviewer supplying anything; if
     it uses the calendar date the notice was originally judged on, that pend can never clear at all,
     because nothing a reviewer supplies moves it. Neither is obviously right and neither is written
     down anywhere.

  3. **What happens to the payload of a resolution that is not applied.** Both the `422` refusal and
     the `409` carry content. Arrival order is what the current view is derived from, so a refused
     resolution's data cannot simply take the next position — that would apply data the system just
     refused. `POST /notices`'s comparable cases went deliberately opposite ways (a schema-invalid
     `400` and an idempotency `409` each keep the content with a reference of its own; an
     unknown-carrier `400` persists nothing), so there is precedent for either answer and no rule
     that reaches this endpoint. This one is load-bearing for the item's own required
     payload-sequence scenario rather than a corner of it.

  4. **The actor: what identifies one, whether its type is an input, and what a refused actor gets.**
     `actor_id` is "caller-asserted in phase 2" and `actor_authenticated` is `false` on every entry
     regardless, so nothing verifies who a reviewer is — that much is settled and needs no decision.
     What is not: whether `actor_type` is supplied by the caller at all. The Record state model says
     a `SYSTEM`-actor attempt at `PENDED → TRIAGED` "is a refused attempt, not an invalid request"
     and still gets an `outcome=REFUSED` entry — which describes a reachable case only if a caller
     can name a type. If instead the endpoint writes `USER` because it is the resolution endpoint,
     that paragraph describes nothing phase 2 can reach and the item's "`USER` actor only" is a
     tautology with no scenario behind it. Either way the closed status-code table has no row for a
     refused actor, and none for an absent `actor_id` either — every `400` in it belongs to
     `POST /notices`.

  5. **Whether `409` covers a notice still at `RECEIVED`.** The table's row is "notice not currently
     `PENDED`", which reads a `RECEIVED` notice as `409` — but that row was written when `RECEIVED`
     was not observable at rest, which `notice_intake.feature` states as fact in its own opening
     comment. Item 5d's two-transaction receipt made it observable: a notice whose rule evaluation
     raised stands at `RECEIVED`, with its idempotency key remembered and no decision ever recorded.
     A `409` on it is defensible, since there is no pend to resolve — but so is treating it as a
     distinct case, because `TRIAGED` means resolved and `RECEIVED` means never judged, and one code
     for both tells a reviewer nothing about which they hit. The table is closed, so widening it is
     the human's call and not a spec-drafting one.

  **Not escalated — read from the design rather than defaulted, and recorded so the next session does
  not reopen it as a gap:** the resolution endpoint has no idempotency key. `PHASE2_DESIGN.md`'s
  Idempotency section scopes the header to `POST /notices` explicitly, and the status-code table
  carries no idempotency row for this endpoint. The consequence is that a network retry of a
  resolution that already succeeded meets a `TRIAGED` notice and is answered `409` by point 5's own
  row — a correct answer rather than a gap, but one reached by composing two rules rather than one
  the design states, which is why it is written here instead of assumed.

  **Decided 2026-08-25, advisor-recommended, human-ratified — all five, in the numbering above.**

  1. **A resolution may supply any notice-content field, not only the fields its blockers name.**
     Field-level overlay in arrival order: a field absent from a resolution keeps its prior value,
     and there is no way to blank a field in phase 2, only to replace it. This is what an intake desk
     does on the callback — the reporter who left the policy number off also had the peril wrong —
     and the narrow reading would carry a value a human knew was wrong through triage and into the
     adapter. Cost, accepted: a reviewer can move severity and queue. That is what makes
     `PENDED → TRIAGED` a `USER` transition — a human judgment, attributed, with the payload
     immutable and hashed.

  2. **(a) The full validation runs over the merged current view.** One definition of "no blocker",
     the same one intake uses; a second definition for this endpoint would be two meanings of
     `TRIAGED`. It is also forced by decision 1: claimant-field requirements depend on loss type, so
     a blockers-only recheck cannot be evaluated once loss type can change. A resolution that
     introduces a blocker the notice never had is not a new outcome — it is the `422` "with the
     current blockers" row, and the notice's stored blockers are replaced by that full set, so body
     and record agree. **(b) The calendar date is the jurisdiction date of the resolution's own
     caller-supplied instant**, through the same lookup intake performs. The frozen alternative makes
     a future-loss-date pend permanently unresolvable, and a notice that can never leave `PENDED` is
     a discarded state under another name. Nothing clears by the passage of time: nothing runs
     without a `USER` resolution, and a reviewer submitting an empty resolution is a human asserting
     on the record that the notice is acceptable as it stands. Consequence: an empty resolution
     (`actor_id` only) is valid input.

  3. **A refused resolution's data is kept, in sequence, and is part of the current view.** The
     release was refused, not the data: what the reviewer supplied is the reporter's answer to a
     request for information under 627.70131(4)(b)3 and is received the moment it arrives. A reviewer
     who fixed one of two problems does not re-supply the fixed one, and "`422` with the current
     blockers" only means something if the current view includes what was just supplied. No
     applied/unapplied marker on payload records: the sequence is the notice, and the audit entry's
     `APPLIED`/`REFUSED` records whether the state moved. The `409` persists nothing — no pend, no
     request, nothing to answer; content goes to the operational log as the unknown-carrier `400`
     does. Correcting a `TRIAGED` notice is a phase-2 non-goal.

     **Correction to the entry above and to the draft's header:** the draft at `6a7e1fc` had already
     decided this point in this direction. Rule 2's refused row asserts the notice's blockers as
     `NOTICE_TYPE_UNRECOGNIZED:notice_type` alone, which is true only if the refused resolution's
     policy number entered the current view. "Nothing drafted against any of them" was wrong for
     point 3.

  4. **`actor_type` is not an input; the endpoint stamps `USER`.** `actor_id` is a required
     caller-asserted string; absent or blank is schema-invalid → `400`, nothing persisted,
     operational log only. An unauthenticated caller asserting `SYSTEM` means nothing, and a table
     row for a refused actor would be a row for a claim nobody can check. `PHASE2_DESIGN.md`'s "a
     `SYSTEM`-actor attempt is refused and audited" describes a guard on the transition for a future
     system re-evaluation path; phase 2 has no producer for it, and a guard with no reachable caller
     would be uncovered code no scenario describes. It stays a carried requirement, annotated there.
     The `400` row is one addition to the closed status-code table, ratified.

  5. **A `RECEIVED` notice gets the existing `409`, and the `409` body carries the notice's current
     state.** No new row. The design already answers "one code tells the reviewer nothing": state is
     read from the body, never inferred from status. A notice at rest in `RECEIVED` is this
     deployment's defect, not a pend, and no reviewer input can cure it. Its scenario is owed to item
     5i, the item that makes that state reachable by a specified path; today the only way to produce
     it is an exception from unbuilt code, and a spec whose setup depends on that is not a spec.

     **Premise false, measured from the code 2026-08-28; the ruling itself stands.** The `409`, the
     body carrying the notice's current state, and the absence of a new status row are all unchanged
     and unchallenged. What is false is the sentence deferring the scenario: item 5i does not make
     `RECEIVED` reachable by a specified path, it confirms the state is unreachable.
     `shell/notice_intake.py`'s `_first_submission` resolves the carrier's rules and the jurisdiction
     — every raise item 5i decides — and only then calls `_create_notice`, which writes the receipt.
     Both deployment faults are therefore answered **before any notice exists**, so neither leaves one
     behind. The two answers are also mutually exclusive: a fault that left a notice at `RECEIVED`
     with its idempotency key remembered would make the reporter's retry after the fix a `200` replay
     of a notice no rule ever ran over, which is exactly the outcome item 5i's own idempotency row
     forbids. The only producer of a notice at rest in `RECEIVED` is a process that stops between the
     receipt transaction and the decision transaction — a durability fact, not a Given anyone can
     write. **A durability or recovery item owns that state if it is ever specified, and nothing in
     item 5i does.** The row was drafted against this decision, measured, and removed the same day
     (branch `reopening/5i-deployment-fault-status-codes`, `079a346`).

  Statutory citations in this entry and in `resolution.feature`'s header were re-verified 2026-08-25
  by the advisor against flsenate.gov's 2024 statutes text of 627.70131 (history ending s. 15 ch.
  2022-271, matching `STATUTORY_REGISTER.md`): (1)(a), (4)(b)1–7, (5)(b), (7)(a), (8)(b), (9) all as
  stated. The 2025 statutes page was not separately fetched.

  **Two further decisions for the implementation, 2026-08-25, advisor-recommended, human-ratified.**

  **(a) The notice carries `pended_at` and `resolved_at`; the audit trail carries every attempt.**
  `PHASE2_DESIGN.md`'s tolling paragraph wants both instants "on the notice and in the audit trail",
  and the notice carried only its receipt instant. `pended_at` is written once, when the notice
  enters `PENDED`, and never rewritten; `resolved_at` is written only by the resolution that moves
  the notice to `TRIAGED`, and is null while it is pended. A refused attempt's instant lives on its
  audit entry and nowhere else. Downstream gets one unambiguous pair per notice for the
  627.70131(8)(b) interval and the full attempt history where the fidelity belongs. **Revisit
  trigger:** any later phase that lets a notice enter `PENDED` a second time.

  **(b) A phase-2 schema change recreates the database.** The schema is `CREATE TABLE IF NOT EXISTS`
  on STRICT tables with no migration path, so adding columns does not upgrade an existing file.
  Accepted: every acceptance scenario opens `:memory:` and no deployment exists. Migration tooling
  joins the phase-3 adapter boundary with the rest of persistence.

  **(c) Recorded, not decided:** `resolution.feature`'s injury row asserts two blockers in an order -
  `claimant_name` before `incident_description` - that `validation.feature` does not state. That file
  fixes canonical order by code only; the within-code order is alphabetical by field, from
  `validation.py`'s sort key and from nowhere in any spec. A locked spec now depends on it. Stating
  it in `validation.feature` is a reopening of a locked spec and is not this item's; it is a
  candidate queue item, not a defect to fix here.

  **(d) An unknown `notice_id` on the resolution endpoint is `404`, nothing persisted.** A resolution
  against an id nobody has is not a notice event. One row added to the closed table, ratified
  2026-08-25.

  **(e) An unparseable loss date in a resolution body is body schema-invalid:** the existing `400`
  row, nothing persisted, checked before the notice is read, beside `actor_id`. Intake answers the
  same input the same way at its own schema boundary, so the merged view can never carry one and the
  in-transaction parse that currently raises is unreachable once this lands. Ratified 2026-08-25.

  Both carried to item 5i's reopening of `resolution.feature`.

- **Item 5i decisions, advisor-recommended, human-ratified, 2026-08-28.** Six escalations raised at
  the drafting of item 5i, ruled together. The item's own entry in `QUEUE.md` names four status
  codes; these are the rulings that close them, plus the three questions drafting turned up that no
  document had anticipated.

  1. **Both deployment faults are `500`, ratified.** A `carrier_code` present in the identity
     reference whose rules entry resolves `CARRIER_NOT_CONFIGURED` or malformed, and a jurisdiction
     map entry naming no timezone or one this system cannot resolve, both answer `500` on the intake
     path with a receipted payload record carrying its own reference and **no notice created**; both
     answer `500` on the resolution path with the transaction rolled back and **nothing recorded**.
     This ratifies the status the 2026-08-24 entry below left open ("A carrier this deployment
     administers but cannot configure is our defect, not the reporter's" decided 5xx and the
     persistence shape, not the code). The two paths differ deliberately: an intake submission is a
     reporter's statutory communication under 627.70131(1)(a) and is receipted whatever this
     deployment does with it, while a resolution is an internal staff action against a notice whose
     receipt duty was discharged long before, so a failed attempt at one creates no record-keeping
     duty of its own. Keeping a payload record on the resolution path would put an unanswered request
     into the sequence the notice's current view is derived from.

  2. **The error-code enumeration is ratified: `CARRIER_RULES_UNRESOLVABLE` and
     `JURISDICTION_MAP_UNUSABLE`.** One status for both faults, told apart by machine error code and
     never by status. A caller's client branches on status to decide whether to retry, and the answer
     is the same for both — not until someone fixes this deployment — so a second status would be a
     distinction with no consequence, the same argument `PHASE2_DESIGN.md` already makes for the two
     identical `201`s. This is a **closed enumeration scoped to the intake and resolution surfaces**,
     shared between `notice_intake.feature` and `resolution.feature` because it is one vocabulary for
     one fault class; it is not duplicate detection's and not SIU's, and adding a code to it is an
     escalation like adding one to either of those. The codes are also load-bearing on mutation:
     without them the two refusing rows agree in every column and both substitutions survive as
     equivalents needing a human approval each.

  3. **The jurisdiction fault is not degraded to the `jurisdiction_unsupported` marking, ratified.**
     A property state this deployment supports no jurisdiction for is a fact about the risk: the
     notice is created, triaged, and marked for a person to search on. A map entry this deployment
     wrote badly is a fact about us, and marks nothing, because there is nothing wrong with the notice
     to mark. Degrading one into the other would hide a deployment defect inside an ordinary
     attribute and make the two indistinguishable in the only place anyone would look.
     `jurisdiction_selection.feature` is untouched by item 5i, so its four marking rows remain the
     sole statement of the marking.

  4. **The advisor's "in body and audit" instruction is corrected against the schema, and the
     correction is accepted.** The brief for item 5i's drafting said the error code should be carried
     "in body and audit". It cannot be: `audit_entries.notice_id` is `NOT NULL REFERENCES notices
     (notice_id)` in `shell/schema.py`, so no audit entry can exist without a notice, and ruling 1
     creates none. **The response body and the receipted payload record carry the code**;
     `payload_records.notice_id` is nullable, which is already how the schema-invalid `400` keeps its
     record. Recorded because it is a correction of the instruction rather than of the code, and a
     later session reading the brief alone would try to build the impossible half.

  5. **The `RECEIVED` row is removed from the draft, not held.** See the dated annotation on item 5e
     decision 5 above for the measurement and the reason. The ruling that a notice at rest in
     `RECEIVED` gets the existing `409` stands; it has no scenario anywhere, and that is correct
     rather than a gap.

  6. **`RULESET_VERSION` does not bump for item 5i.** The two error codes are shell vocabulary: they
     name a fault in this deployment's configuration, not an outcome any rule under
     `src/claimgate/domain/` computed, and no stored decision's meaning changes because one exists.
     **If implementation finds otherwise — if either code ends up produced by or stored through the
     domain layer — that is a stop-and-escalate, not a judgment call to make at the keyboard.**

  **Two implementation notes, ruled here so they are not rediscovered.** The symmetric carrier fault
  on the resolution path stands and is specified: `shell/resolution.py`'s `_judge` calls
  `resolve_rules` exactly as it calls the two jurisdiction resolvers, inside the transaction and
  after the payload append, so the carrier fault has the identical shape there and is drafted with a
  row of its own rather than left implicit. Separately, **two `NotImplementedError` messages are
  stale against ratifications that landed after they were written** and must be corrected when their
  raises are removed: `_loss_date_of` says no decision covers a resolution's unparseable loss date,
  which decision (e) of 2026-08-25 does; `_require_notice` says an unknown notice id has no status
  code in the closed table, which decision (d) of the same date added. `_conflict`'s docstring
  carries the same false premise ruling 5 corrects.

- **Item 5i implementation shapes — decided at the keyboard, 2026-08-28, none of them a rule.** The
  six rulings above settled every behavioural question; these are the shapes the implementation had
  to pick to realize them, recorded because each is a choice a later session would otherwise have to
  re-derive from the diff, and two of them are visible on a surface.

  1. **`payload_records.error_code`, a new nullable column, is how ruling 4's "the receipted payload
     record carries the code" is realized.** The alternative readings were worse: the code cannot go
     in `content`, which is the verbatim payload the reference is hashed from, and it cannot go on an
     audit entry, which is the impossibility ruling 4 exists to correct. It sits beside
     `carrier_code` and `received_at` as metadata about how the submission was answered, and is null
     on the accepted path, on the schema-invalid 400 and on the mis-keyed 409 alike — those refusals
     are about what arrived rather than about this deployment, and the column is what tells the two
     kinds apart in the record. **Cost, stated rather than hidden:** there is no migration story
     anywhere in phase 2, and `CREATE TABLE IF NOT EXISTS` does not add a column to a database that
     already exists. This is the same cost item 5g's three `notices` columns carried and is
     acceptable on the same grounds — no deployment has durable data yet — but it stops being
     acceptable the moment one does.

  2. **`error` is on both response surfaces and on both serialization allow-lists.** Not a free
     choice: `serialization.py`'s allow-list test failed the moment the field existed and would not
     pass until someone named it or deliberately kept it off, which is the mechanism working exactly
     as `PHASE2_DESIGN.md`'s "SIU handling" point 2 intends. It is named because both specs assert
     the caller reads the code from the body — one status carries both faults, so a client that
     could not read the code would have no way to tell them apart at all.

  3. **Which half of the jurisdiction fault each layer exercises.** The map can be unusable two ways
     — an entry naming no timezone (`select_jurisdiction` returns `MALFORMED`) and one naming a
     timezone this system cannot resolve (`resolve_jurisdiction_date` refuses) — and both resolve to
     `JURISDICTION_MAP_UNUSABLE`, which is ruling 2 working as intended. One scenario row can carry
     only one input, so the acceptance suite exercises the naming-no-timezone half on both paths and
     `tests/shell/` covers the unresolvable-name half on both. Recorded because the spec phrase "the
     jurisdiction map entry names no usable timezone" is deliberately true of both, so nothing in the
     feature files says which one a row runs.

  4. **The carrier fault is produced by leaving the entry present and malformed, not by removing
     it.** Ruling 1 names both `CARRIER_NOT_CONFIGURED` and malformed as the fault, and
     `resolve_rules` cannot tell them apart — it branches on `result.rules is None`. The acceptance
     step corrupts one value in an entry that stays present, because that is the case the rule is
     about: a carrier this deployment *claims to administer* whose rules will not load, which is
     what separates this rule from the unknown-carrier 400 above it. `tests/shell/` uses the empty
     source, so both inputs are exercised.

  5. **`_loss_date_of` is gone rather than kept as a guard.** Decision (e) moved the unparseable
     check to the schema boundary, and every arrival in a notice's sequence has cleared a boundary
     that answers that input 400 — intake's for position 0, this endpoint's for every later one,
     including a refused 422's record, which is kept precisely because it was readable. The merged
     view therefore carries a date or states none, and `_judge` has no branch for a third case. A
     guard there would be a branch no test could reach and no gate could score.

  **Two modules are now exactly at the 250-line size ceiling** — `shell/notice_intake.py` and
  `shell/resolution.py`, both at 250 of 250 after this item. Neither has room for another paragraph
  of comment, let alone a function. The next item touching either one splits it first; the precedent
  is `messages.py`, extracted at item 5d for this exact reason and saying so in its own docstring.

- **Item 5f, SIU separation — six decisions, advisor-recommended, human-ratified, 2026-08-25.** All
  six were open in `PHASE2_DESIGN.md`'s "SIU handling"; none is a new indicator. New indicators are
  out of scope for 5f and recorded below as a candidate item.

  1. **SIU indicators are evaluated on every transition into `TRIAGED`, on both paths, inside that
     transaction, on the merged current view — never at `RECEIVED` or `PENDED`.** A pended notice is
     an incomplete intake record, not a claim; carriers score indicators on the claim. A resolution
     that corrects the loss date changes the interval, so an evaluation at pend time would record a
     determination on data a human later corrected. A refused resolution and an idempotent replay
     evaluate nothing, because neither transitions.

  2. **Late reporting is measured from the original receipt instant's jurisdiction date, never from
     the resolution instant.** Notice given is notice received; a pend does not make the reporter
     late. The one-receipt-clock entry implies this and did not state it. A notice pended nine days
     after loss and resolved five weeks later is not late.

  3. **One event row per indicator per evaluation, including `FALSE` and `NOT_EVALUATED`.**
     "Unevaluated is not negative" is only auditable if unevaluated is written; a trail of positives
     makes an absent row mean three different things. A row carries the indicator name, the value,
     the reason code (null unless `NOT_EVALUATED`), the `ruleset_version`, and `evaluated_at`, which
     is the triaging transaction's caller-supplied instant. Append-only: no update, no delete, no
     code path for either.

  4. **No read surface in phase 2 beyond a restricted read in the test API used by scenarios.** No
     HTTP route for indicators until an authenticated identity exists to log a read against — the
     design's reasoning for deferring the read-side log applies to the read itself.

  5. **The leak assertions are outcome negatives on four surfaces** — intake response, resolution
     response, the notice's standard view, and every audit entry — for a notice whose late
     reporting is `TRUE` and whose inception indicator is `NOT_EVALUATED`, so there is something to
     leak; and the two SIU reason codes never appear among a response's blockers. Some of these will
     be fixed steps the engine cannot mutate; they still execute, and the limit is recorded in the
     spec's comments, not hidden.

  6. **The rules applied are the carrier's configuration as resolved at the triaging transaction,**
     with `ruleset_version` on every event row — the same answer as item 5e decision 2(a).

  **Candidate item, not 5f:** further FNOL indicators a Florida residential SIU desk actually uses —
  loss shortly before expiration or pending cancellation; a public adjuster, attorney, or assignee
  as the reporter at first notice; a coverage or limit increase shortly before the loss; prior-loss
  frequency from an industry database hit; reporter-versus-insured identity mismatch; loss dates
  just outside a declared catastrophe window. Each needs its own defensible basis and its own
  sensitivity review. The referral side (s. 626.9891 anti-fraud plan and SIU requirements) is
  unverified this session and is not 5f's.

- **Item 5f, one point the six decisions do not cover — escalated 2026-08-25 while drafting
  `features/siu_separation.feature`, undecided, nothing drafted against it.** Decision 3 settles that
  an indicator event row carries a `ruleset_version`. Two things it does not settle, and a scenario
  meets both the moment it asserts one.

  1. **Which version the field names.** `PHASE2_DESIGN.md`'s audit-log schema defines
     `ruleset_version` as a "hand-declared semantic label (e.g. `1.0.0`) for the domain rules that
     produced a `SYSTEM` decision" — a version of the domain rules. Decision 6 reads "the carrier's
     configuration as resolved at the triaging transaction, with `ruleset_version` on every event
     row", which reads instead as a version of the carrier configuration. Nothing in the carrier
     configuration model carries a version at all: `carrier_configuration.feature` resolves six
     values and none of them is one. The readings differ in observable behaviour, not only in
     wording — under the first the field does not move when a carrier edits a threshold, under the
     second it must.

  2. **What its value is.** No agreed value exists. `records.py` leaves `AuditEntry.ruleset_version`
     unset on every entry written today, with a comment saying why, and `notice_intake.feature`'s
     Rule 2 comment records that it deliberately asserts no literal for the same reason — "a
     deployment-declared label with no agreed value yet". A scenario stating a literal would invent
     the deployment's label; one asserting only that the field is populated would assert behaviour
     no decision has authorized.

  **Drafted inside the intersection:** `siu_separation.feature` asserts that the two event rows of
  one evaluation record the same ruleset version as each other, and names no literal. That is true
  under both readings, and it is the same restraint `notice_intake.feature` already applied to this
  field. Nothing in the draft asserts which version it is, what it contains, or that it equals the
  audit entry's.

  **Two things checked rather than assumed while drafting, neither of which needed a decision.**
  A carrier phrase configuring a late reporting threshold already exists in a locked spec —
  `carrier_configuration.feature` carries both `"AAAA" configures a late reporting threshold of 45
  days` and `"AAAA" has no late reporting threshold configured`, so the draft reuses them verbatim
  rather than inventing a variant that could hold the unconfigured state in an `Examples` cell.
  And the restricted read of a notice with no events is determinate under decision 3 alone: one row
  per indicator per evaluation, so a notice that has never transitioned into `TRIAGED` has none, and
  the read returns nothing rather than a pair of absent values.

  **Decided 2026-08-25, advisor-recommended, human-ratified.** `ruleset_version` names the version
  of the domain rule set — the evaluating code — never the carrier's configured numbers, which have
  no version and do not acquire one for this. Its value is a date-stamped label declared once in the
  domain package and copied by the shell onto every audit entry (which has left it null since item
  5c; 5f's implementation fills it on both paths) and onto every SIU event row. Any commit that
  changes a rule's behaviour under `src/claimgate/domain/` bumps the label. That is a convention no
  gate can enforce, recorded as one. Reproducibility of a row comes from recording the input
  applied, not from versioning configuration: each SIU event row also carries the threshold the
  evaluation used, null when none was configured. The spec asserts all of this relationally and with
  no literal: one evaluation's two events carry the same version as each other and as the audit
  entry that triaged the notice, and the late reporting event records the threshold the carrier
  configured.

- **Retention is currently an unapproved default — opened 2026-09-01, decided in phase 5.** The
  audit log and payload store are append-only with no deletion path anywhere. Keeping everything
  forever is a retention behaviour, and `CLAUDE.md`'s first constraint names retention as one of the
  four things never to default. Phase 5 decides it against a primary source for the Florida
  claim-file retention duty; no period is recorded here because none has been verified, and
  recording one from memory would be the exact failure the register exists to prevent.

## Synthetic data

- No real policy numbers, names, addresses, phone numbers, or claim numbers appear anywhere in
  specs, fixtures, or tests. Names are fictional; phone numbers stay in the 555-01xx reserved
  range.
- Carrier identity data (names, NAIC codes) is public regulatory information, used because the
  design targets a real, named carrier estate rather than a generic one. Everything else — every
  notice, every policy number, every loss description — is fabricated.
