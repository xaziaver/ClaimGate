# Assumptions

The index of ClaimGate's assumptions and decisions, by status at `prototype-1` (`be87d38`). Every
entry's full text — what was assumed or decided, why, what it costs, and every amendment — was moved
on 2026-09-11, clean-up stage C2b, byte for byte to `docs/queue-history/assumptions.md`, where it is
not edited. Each entry here sits under the section it sat in and gives its number, its status, its
dates, its provenance, its line in the history file and its title verbatim. So a citation quoting a
title, a section or an item's decisions, from a locked spec, a source comment or an approval reason,
still finds its entry here and is sent on to the full text. The A-numbers count the history file's entries
in order: every block at column 0 that begins `- ` or `**`.

The statuses were drafted by the coding agent and ruled on by the advisor on 2026-09-11, and the
evidence for each is in `docs/queue-history/assumptions-classification.md`. Two were changed in the
ruling, A050 and A079, and say so. A "Note" is the advisor's, and records a sentence in the full text
that the tree at `prototype-1` contradicts, or a loose end nothing settled; the full text is left as
written. In force means the locked specs and the code do what the entry decides. Open means the
question, defect or gap is still there. Settled means fixed, decided, superseded or retired, with
what did it. A record decides nothing.

**Adding a decision.** A decision made after `prototype-1` goes in full at the end of this file,
under "Decisions after prototype-1", dated and carrying a provenance tag as A001 defines them:
advisor-recommended, human-ratified; or human, from carrier experience. A decision that changes an
entry indexed here names it by A-number, and that entry's index line gains a note pointing to it.

## In force (72)

### Before the first section

- **A001** — in force — 2026-08-14 — none — history line 19.
  Title: Provenance convention, proposed 2026-08-14.

### From the section "Carrier estate — no internal access to any"

- **A008** — in force — undated — none — history line 78.
  Title: Carrier codes.

- **A010** — in force — undated — none — history line 82.
  Title: NAIC group codes.

- **A011** — in force — undated — none — history line 85.
  Title: Book scope.

- **A012** — in force — 2026-09-01 — none — history line 87.
  Title: "Policy administration system" in this project's documents means the carrier's core system including its claims side — noted 2026-09-01.

### From the section "Carried requirements — decided, not yet built"

- **A013** — in force — 2026-08-24 to 2026-08-25 — advisor-recommended, human-ratified — history line 96.
  Title: One receipt clock, not two — decided 2026-08-24, advisor-recommended, human-ratified.

- **A014** — in force as amended — 2026-08-23 — bare "decided" — history line 125.
  Title: Timezone-correct "now."
  Status: amended in place by its own two 2026-08-23 corrections, and by A015 (zone is a parameter) and A017/A020 (the zone comes from the jurisdiction map, not the submission).
  Decisions: the principle (domain never receives a server-local date) — IN FORCE. The four named scenarios as corrected — IN FORCE (`jurisdiction_date.feature` rules "An instant resolves to the calendar date in the jurisdiction's timezone..." and "The UTC offset in effect for a date, not proximity to a DST transition..."). Pinning `tzdata` in `pyproject.toml` — STILL OPEN (no `tzdata` in `pyproject.toml`; the entry said "settled with item 5c's deployment work", and no later entry settles it).

- **A015** — in force — 2026-08-22 — advisor-recommended, human-ratified — history line 183.
  Title: The jurisdiction timezone is a parameter of the conversion, not a constant in it.
  Decisions: the parameter — IN FORCE (`jurisdiction_date.feature` rule "The jurisdiction's timezone is a parameter the resolution reads, not a zone it assumes"). "Which zone a given notice gets" recorded as open — DECIDED at item 5g by A017 (one zone per jurisdiction, keyed on `property_state`) and A018.

- **A016** — in force — 2026-08-23 — advisor-recommended, human-ratified — history line 195.
  Title: An unrecognized jurisdiction timezone is refused, never defaulted — advisor-recommended, human-ratified, 2026-08-23.
  Decisions: the refusal — IN FORCE (`jurisdiction_date.feature` rule "An unrecognized jurisdiction timezone refuses the resolution rather than falling back to a default"; `JURISDICTION_TIMEZONE_UNRECOGNIZED` at `jurisdiction.py:46`). "Settle the inconsistency when 5a's implementation lands" (subject-first vs `MISSING_REQUIRED_CONFIGURATION`) — STILL OPEN: `carrier_configuration.py` lines 26–28 still carry `MALFORMED_REQUIRED_CONFIGURATION` and `MISSING_REQUIRED_CONFIGURATION`, and no later entry settles the order.
  Note: Not settled: the code-name order this entry defers to item 5a's implementation was never decided. `carrier_configuration.py` still reads `MALFORMED_REQUIRED_CONFIGURATION` and `MISSING_REQUIRED_CONFIGURATION`, both in the locked `carrier_configuration.feature`, so settling it reopens that spec.

- **A017** — in force — 2026-08-26 — advisor-recommended, human-ratified — history line 216.
  Title: One timezone per jurisdiction, and Florida's is `America/New_York` — advisor-recommended, human-ratified, 2026-08-26.
  Decisions: one zone per jurisdiction, Eastern for Florida — IN FORCE (`jurisdiction.py:62` comment "Eastern's date is never behind Central's"; `jurisdiction_selection.feature:64–66` comment). Re-verify 49 CFR 71.5(f) against the full section — STILL OPEN: `STATUTORY_REGISTER.md` has no `49 CFR` entry (checked, grep empty), so the boundary rests on the search excerpt only.
  Note: `STATUTORY_REGISTER.md` has no 49 CFR entry, so the county boundary's source is recorded only in this entry, not in the register's weaker-provenance class the entry mentions.

- **A018** — in force — 2026-08-26 — advisor-recommended, human-ratified — history line 254.
  Title: `property_state` is matched exactly, and a miss is marked rather than normalized — advisor-recommended, human-ratified, 2026-08-26.

- **A019** — in force — 2026-08-26 — advisor-recommended, human-ratified — history line 265.
  Title: The zone that dates a resolution's SIU interval comes from the merged view, not from what was known at receipt — advisor-recommended, human-ratified, 2026-08-26.

- **A020** — in force — 2026-08-26 — advisor-recommended, human-ratified — history line 285.
  Title: `jurisdiction_timezone` is removed from the submission surface rather than kept beside `property_state` — advisor-recommended, human-ratified, 2026-08-26.

- **A021** — in force — 2026-08-27 — advisor-recommended, human-ratified — history line 308.
  Title: The future-dated-loss determination is off every outward surface in phase 2; the jurisdiction marking is on `NoticeView` — advisor-recommended, human-ratified, 2026-08-27.

- **A022** — in force — 2026-08-23 — advisor-recommended, human-ratified — history line 330.
  Title: An instant that is not a timezone-aware UTC instant is out of scope for item 5b — advisor-recommended, human-ratified, 2026-08-23.
  Decisions: out of scope for 5b — IN FORCE. The obligation moved to item 5c (where the instant is obtained) — unverified: no later entry records 5c discharging it, and I did not read `receipt.py`'s instant handling for an awareness check.

- **A023** — in force — 2026-08-23 — advisor-recommended, human-ratified — history line 354.
  Title: A refused submission is still a received communication — advisor-recommended, human-ratified, 2026-08-23.
  Decisions: refused payload persisted with its hash, no notice — IN FORCE (`notice_intake.feature` at be87d38 scenario "A notice is created only if its loss date is a real date"; `receipt.py:129` `refuse_payload`). Retention of refused payloads "item 5g's problem" — STILL OPEN, now A103 (phase 5).

- **A024** — in force — 2026-08-24 — advisor-recommended, human-ratified — history line 391.
  Title: Item 5c's 400 validates against the identity reference, not the rules source — advisor-recommended, human-ratified, 2026-08-24.

- **A025** — in force as amended — 2026-08-24 — advisor-recommended, human-ratified — history line 401.
  Title: A carrier this deployment administers but cannot configure is our defect, not the reporter's — advisor-recommended, human-ratified, 2026-08-24.
  Status: the status code left as "5xx" was fixed at `500` by A099 ruling 1 (2026-08-28); the response column on `notice_intake.feature` Rules 1 and 3 is in the locked spec.

- **A026** — in force — 2026-08-24 — advisor-recommended, human-ratified — history line 419.
  Title: The payload reference recipe — advisor-ratified, 2026-08-24.
  Decisions: the recipe — IN FORCE (`records.py:124` `json.dumps(raw_payload, sort_keys=True, default=str)`). "Revisit when a literal HTTP layer exists" — STILL OPEN (no HTTP layer exists; `resolution.py:4–5` says so).
  Note: Its provenance tag is not one A001 defines; read it as advisor-recommended, human-ratified.

- **A027** — in force — 2026-08-24 — advisor-recommended, human-ratified — history line 440.
  Title: Idempotency: what a repeated key is compared against, and when the window closes — advisor-recommended, human-ratified 2026-08-24.
  Decisions: (1) reference comparison — IN FORCE (spec title above). (2) key examined before the schema boundary — IN FORCE (`receipt.py:3` docstring order). (3) 409 keeps the content — IN FORCE (unverified in source; `idempotency.feature:188–190` comment). (4) key table of its own — IN FORCE (`schema.py:122–126` `idempotency_keys` with `UNIQUE (carrier_code, idempotency_key)`). (5) half-open window — IN FORCE (`idempotency.py:32,45` `timedelta(hours=24)` and `<`). Carried to 5e — DECIDED: `resolution.feature` rule "A replay of the original submission reports the state the notice is in now, not the one it landed in".

- **A028** — in force — undated — none — history line 491.
  Title: Unevaluated is not negative.

- **A029** — in force — 2026-08-18 — bare "decided" — history line 498.
  Title: Recent-inception reason-code precedence when both required inputs are absent.
  Decisions: the precedence — IN FORCE (`siu.py:80–83`: coverage-date check first, "Do not reorder these checks"). The owed scenario — FIXED at item 4k (`7da0bd1`, git-dated 2026-08-21; queue history says 2026-08-18): `siu_indicators.feature` at be87d38 scenario "Neither recent policy inception input is present".
  Note: Date: the queue history dates item 4k's merge `7da0bd1` 2026-08-18; git dates it 2026-08-21.

- **A030** — in force — 2026-08-13 — bare "decided" — history line 524.
  Title: Severity assignments for the new perils (`hurricane`, `sinkhole`, `roof_leak`) — decided 2026-08-13, documentation-only session on `main`, no branch/spec/implementation yet (`QUEUE.md`'s merged item 4c).

- **A031** — in force — 2026-08-13 — bare "decided" — history line 535.
  Title: Catastrophe handling is a deliberate non-goal for this phase, not an oversight — the reasoning behind `hurricane`'s `STANDARD` severity above, not a separate decision.

- **A032** — in force — 2026-08-13 — bare "decided" — history line 541.
  Title: Loss amount is removed from the severity rule entirely, not replaced with a better threshold — decided in the same session.

- **A033** — in force — 2026-08-14 — advisor-recommended, human-ratified — history line 551.
  Title: Advisor-recommended, human-ratified, 2026-08-14: the `low` severity band and its `fast_track` queue are retired, not left as reachable dead code.

- **A034** — in force — 2026-08-14 — advisor-recommended, human-ratified — history line 559.
  Title: Advisor-recommended, human-ratified, 2026-08-14: the end-to-end outline keeps its `loss_amount` column after loss amount stops affecting severity.

- **A035** — in force — 2026-08-16 — bare "decided" — history line 568.
  Title: The blocking criterion: a missing field blocks intake only if the information is actionable and crucial to the FNOL process or to the carrier's exposure — decided 2026-08-16, documentation-only session on `main`, no branch/spec/implementation yet (`QUEUE.md` item 4g).

- **A036** — in force — 2026-08-17 — advisor-recommended, human-ratified — history line 587.
  Title: Carrier-varying rules are caller-supplied configuration with no domain default — advisor-recommended, human-ratified, 2026-08-17.

- **A037** — in force — 2026-08-16 to 2026-08-17 — advisor-recommended, human-ratified — history line 611.
  Title: Item 4g's Section II required-field set is carrier configuration; `incident_description` is not — advisor-recommended, human-ratified, 2026-08-17. Supersedes the 2026-08-16 decision that `claimant_contact` is non-blocking while `claimant_name` blocks.

- **A038** — in force — 2026-08-17 — bare "decided" — history line 630.
  Title: ClaimGate is a general product, not a build against one named estate — stated 2026-08-17.
  Decisions: consequence 1 (4b prefix set as configuration scope) — RETIRED at item 7d (A057). Consequence 2 (`POLICY_NUMBER_PATTERN` belongs to the adapter) — DECIDED by retirement at 7d (A097's closing paragraph, 2026-09-06). Consequence 3 (NAIC codes now in `STATUTORY_REGISTER.md`) — unverified. Consequence 4 (no history rewrite) — IN FORCE (history intact; `git log` resolves every cited hash).

- **A039** — in force as amended — 2026-08-17 to 2026-08-23 — advisor-recommended, human-ratified — history line 654.
  Title: A carrier configuration crosses into the domain already resolved, so the domain has no unrecognized-configuration case — advisor-recommended, human-ratified, 2026-08-17.
  Status: amended by its own 2026-08-23 annotation (the loader lives in `src/claimgate/domain/carrier_configuration.py`); the six rules still have no unrecognized-configuration branch.

- **A040** — in force as amended — 2026-08-22 — advisor-recommended, human-ratified — history line 687.
  Title: The per-carrier rules file moves from phase 3 into phase 2 — advisor-recommended, human-ratified, 2026-08-22.
  Status: the lookup-not-branch shape is built (`rules.py:109–115` `resolve_rules(carrier_code, rules_source)`); "six values" became five at 7d (prefix set retired, A057). The "rules file" as a file: see A050 and part 3 — no file reader exists in the tree; the source is a mapping the caller supplies.
  Decisions: carrier axis for five of six — IN FORCE. The late-reporting threshold's axis — STILL OPEN (A095).

- **A041** — in force — 2026-08-22 — advisor-recommended, human-ratified — history line 713.
  Title: Duplicate-detection not-evaluated reason codes do not appear in `reason_codes` — advisor-recommended, human-ratified, 2026-08-22. Resolves the carried requirement `PHASE2_DESIGN.md` records as undecided under "HTTP surface."

- **A044** — in force — 2026-08-22 — advisor-recommended, human-ratified — history line 760.
  Title: A configuration value that is present but malformed is refused at load, alongside an absent one — advisor-recommended, human-ratified, 2026-08-22.

- **A045** — in force — 2026-08-22 — advisor-recommended, human-ratified — history line 775.
  Title: A refusal names every value it rejected, not the first one — advisor-recommended, human-ratified, 2026-08-22.

- **A046** — in force — 2026-08-22 — advisor-recommended, human-ratified — history line 787.
  Title: A missing configuration value and a malformed one are different reason codes - advisor-recommended, human-ratified, 2026-08-22.
  Decisions: three codes, closed, in that order — IN FORCE (`carrier_configuration.py:26–28, 33–37` `_CANONICAL_CODE_ORDER`). Order stated over the rendered field name — unverified (`_canonical_order` body not read).

- **A047** — in force — 2026-08-22 — advisor-recommended, human-ratified — history line 811.
  Title: A key in a carrier's entry that is not one of the six values is out of scope for item 5a - advisor-recommended, human-ratified, 2026-08-22.

- **A048** — in force — 2026-08-22 — advisor-recommended, human-ratified — history line 822.
  Title: A day count of zero is a valid configuration, not a malformed one - advisor-recommended, human-ratified, 2026-08-22.

- **A050** — in force, not built — 2026-08-22 — advisor-recommended, human-ratified — history line 839.
  Title: The per-carrier rules file is TOML, keyed by `carrier_code`, with one placeholder carrier — advisor-recommended, human-ratified, 2026-08-22.
  Status: the decision stands, and nothing implements it yet: no code reads a rules file of any format. `rules.py`'s `resolve_rules` takes a mapping from its caller, and `carrier_configuration.py` names TOML (lines 13–14) only to cite this entry. The loader is phase 5's: "configuration injection for the carrier reference and rules files" (`ROADMAP.md`, phase 5). The report classed this STILL OPEN; ruled 2026-09-11.

- **A051** — in force as amended — 2026-08-22 — none — history line 850.
  Title: Two of the six caller-supplied values legitimately accept an absent state; four do not.
  Status: two optional thresholds, three required values (not four) since 7d retired the prefix set (A057).

- **A052** — in force — 2026-09-01 — advisor-recommended, human-ratified — history line 860.
  Title: Phase 3 designs the policy administration adapter against three named exemplar system shapes and ships two conforming implementations — advisor-recommended, human-ratified, 2026-09-01.

- **A053** — in force as amended — 2026-09-01 — advisor-recommended, human-ratified — history line 869.
  Title: Coverage verification at intake is clerical, and it is not coverage determination — advisor-recommended, human-ratified as the recommendation to carry into `PHASE3_DESIGN.md`, 2026-09-01.
  Status: the four consequences were ratified and built at 7a/7f: the term is cited (`coverage_verification.feature` rule "The determination cites the deciding term"); a boundary day is a third value (`BOUNDARY_DAY`, A061 decision 10); `as_of` is stored (`coverage_verifications.py`); search not fetch (`policy_match.feature`); the outcome split is A060/A061 (unmatched pends, out-of-force triages).

- **A054** — in force — 2026-08-17 to 2026-09-01 — advisor-recommended, human-ratified — history line 897.
  Title: Policy identification leaves the domain: `POLICY_NUMBER_MALFORMED` and `recognized_policy_number_prefixes` are retired in phase 3 — advisor-recommended, ratified with `PHASE3_DESIGN.md`.

- **A055** — in force as amended — 2026-09-05 — advisor-recommended, human-ratified — history line 903.
  Title: Identifier sufficiency: decisions taken before the spec was locked — advisor-recommended, human-ratified 2026-09-05.
  Decisions: (1)–(3), (6) — IN FORCE (`policy_identification.feature` scenarios "A policy number pasted with surrounding whitespace", "Anything less is insufficient, and the blocker names what is absent", "A nine-digit postal code is carried as given, not reshaped"). (4) unwired, no `RULESET_VERSION` bump — SUPERSEDED at 7g (A062: wired; `RULESET_VERSION` moved at 7d, 7f, 7h). (5) `policy_number` required until 7g — RETIRED at 7g (A062 decision 3; `validation.feature` rule "A policy number need not be stated...").

- **A056** — in force as amended — 2026-09-05 — advisor-recommended, human-ratified — history line 921.
  Title: Identifier-sufficiency judgments beyond the locked spec — agent-proposed, advisor-reviewed, human-ratified 2026-09-05.
  Status: (3) serialization onto a notice was 7g's decision and is now A062 decision 1 (comma-joined fields, one blocker); (4) the rule takes three identifiers and 7g passes them from the merged view — IN FORCE.
  Note: Its provenance tag is not one A001 defines; read it as advisor-recommended, human-ratified.

- **A057** — in force as amended — 2026-09-05 to 2026-09-06 — advisor-recommended, human-ratified — history line 943.
  Title: Item 7d decisions, taken before the specs were re-locked — advisor-recommended, human-ratified 2026-09-05.
  Decisions: (1) retirement — IN FORCE. (2) `policy_number` required until 7g — RETIRED at 7g (A062 decision 3). (3) interplay rule on four codes — IN FORCE (`validation.feature` rule "All blockers are reported together, in canonical order..."). (4), (5) — unverified against the locked rows. (6) `RULESET_VERSION` bump — done at `e62cdd6` (2026-09-06), since moved to `2026-09-09` (A064).

- **A058** — in force as amended — 2026-09-06 — advisor-recommended, human-ratified — history line 959.
  Title: Item 7e decisions — advisor-recommended, human-ratified 2026-09-06.
  Status: (5) "no endpoint answers `PORT_BINDING_UNRESOLVABLE` until 7f" — done at 7f (A061 decision 7); (1) "killed count staying at 687" is a dated measurement (757 at prototype-1 per QUEUE.md).

- **A059** — in force — 2026-08-14 to 2026-09-01 — advisor-recommended, human-ratified — history line 983.
  Title: The continuous-coverage derivation is a domain rule, not port logic — advisor-recommended, ratified with `PHASE3_DESIGN.md`.

- **A060** — in force — 2026-09-01 — advisor-recommended, human-ratified — history line 989.
  Title: A port fault lands `TRIAGED` with verification `NOT_EVALUATED`; it does not pend — advisor-recommended, ratified with `PHASE3_DESIGN.md`.

- **A061** — in force as amended — 2026-09-07 — advisor-recommended, human-ratified — history line 994.
  Title: Item 7f spec decisions — advisor-recommended, human-ratified 2026-09-07.
  Decisions: (1)–(5), (7), (9)–(11) — IN FORCE. (6) unmatched/ambiguous persist through resolution — AMENDED by A062 decision 6 (7g re-searches; an answer decides afresh). (8) insured-name search unreachable until 7g — SUPERSEDED at 7g (A062 decision 3, 7).

- **A062** — in force — 2026-09-08 — advisor-recommended, human-ratified — history line 1025.
  Title: Item 7g spec decisions — advisor-recommended, human-ratified 2026-09-08.

- **A063** — in force — 2026-08-22 to 2026-09-09 — advisor-recommended, human-ratified — history line 1049.
  Title: Item 7h spec decisions — advisor-recommended, human-ratified 2026-09-09.

- **A064** — in force — 2026-09-09 — advisor-recommended, human-ratified — history line 1069.
  Title: Item 7h implementation decisions — advisor-recommended, human-ratified 2026-09-09.

- **A065** — in force as amended — 2026-09-10 — advisor-recommended, human-ratified — history line 1088.
  Title: Item 7i decisions — advisor-recommended, human-ratified 2026-09-10.
  Status: decision (6)'s closing sentence, "Its implementation is queued as the next item's opening housekeeping", is stale: `be87d38` itself (prototype-1, 2026-09-11) is "7i decision (6): an extract whose history starts later than the binding's horizon...", and `extract_ports.py:134` tests `_holds_less(manifest.history_from, horizon)`. Recorded in part 3.
  Note: Decision (6) settles the open decision that `src/claimgate/shell/extract_source.py`'s docstring still cites as "an open decision (ASSUMPTIONS.md, 7i)" (7i judgment 8).

### From the section "Undocumented phase-1 thresholds"

- **A069** — in force — 2026-08-27 — advisor-recommended, human-ratified — history line 1132.
  Title: Not a threshold, recorded beside them because it is the project's other hand-declared value and fails the same way: `RULESET_VERSION` is a bare date and cannot label two rule changes made on one day.
  Note: Its provenance tag is not one A001 defines; read it as advisor-recommended, human-ratified.

### From the section "Domain defects found, not yet fixed"

- **A082** — in force — 2026-08-16 — none — history line 1291.
  Title: Why `test_triage.py::test_every_high_severity_loss_type_is_recognized_by_validation` exists, recorded because the set comparison it makes is not self-explanatory (`QUEUE.md` item 4h).

- **A084** — in force — 2026-08-27 to 2026-08-30 — advisor-recommended, human-ratified — history line 1329.
  Title: Item 5h, three decisions, advisor-recommended, human-ratified, 2026-08-27.
  Decisions: (1) — IN FORCE (`validation.py:62–67` `NO_JURISDICTION_DATE`, `NO_LOSS_DATE`). (2) — IN FORCE, its scenario landed at 5j (`jurisdiction_selection.feature` at be87d38 scenario "What the future-dated-loss determination records when it evaluates, when the jurisdiction date is missing, and when the loss date is missing too"). (3) — IN FORCE (`siu.py:23` comment; the both-paths premise holds: `shell/siu.py:3` "on every transition into TRIAGED, on both"). (4) — IN FORCE (`duplicates.py:55–67` `_require_loss_date` raises `ValueError`, placed after the notice-type exclusion at line 38–52).

### From the section "Data we do not have at intake"

- **A086** — in force as amended — 2026-08-13 — bare "decided" — history line 1397.
  Title: `policy_inception_date` is available at FNOL via a lookup against the policy administration system — decided 2026-08-13, documentation-only session on `main` (`QUEUE.md`'s merged item 4c); no branch, no spec, no implementation yet.
  Status: the date arrives via the port's term history (A059, A087) and is derived in the domain as of the loss date (A089); `compute_siu_indicators` still receives it as a parameter. "Original inception date" became "start of the unbroken run of coverage in force on the loss date".

- **A087** — in force as amended — 2026-08-14 to 2026-09-04 — bare "decided" — history line 1412.
  Title: Decided 2026-08-14: how the adapter derives that date, and what "continuous coverage" means.
  Status: by its own 2026-09-01 and 2026-09-04 insertions, A059 and A089. "Per-system mechanics for each of the three policy administration systems" — SUPERSEDED by A052 (exemplar shapes, 2026-09-01).

- **A088** — in force — 2026-09-04 — advisor-recommended, human-ratified — history line 1433.
  Title: Term-in-force judgments beyond the locked spec — agent-proposed, advisor-reviewed, human-ratified 2026-09-04.
  Note: Its provenance tag is not one A001 defines; read it as advisor-recommended, human-ratified.

- **A089** — in force — 2026-08-14 to 2026-09-04 — advisor-recommended, human-ratified — history line 1472.
  Title: Continuous-coverage derivation: decisions taken before the spec was locked — advisor-recommended, human-ratified 2026-09-04.

- **A090** — in force — 2026-09-04 to 2026-09-05 — advisor-recommended, human-ratified — history line 1517.
  Title: Continuous-coverage judgments beyond the locked spec — agent-proposed, advisor-reviewed, human-ratified 2026-09-05.
  Note: Its provenance tag is not one A001 defines; read it as advisor-recommended, human-ratified.

- **A091** — in force as amended — undated — none — history line 1548.
  Title: Consequence, updated for the decision above:
  Status: "once the adapter is built, NOT_EVALUATED becomes a genuine exception path" is now the case (7f, A061 decision 5); the late-reporting gap STILL OPEN (A095).

- **A093** — in force — 2026-08-15 to 2026-08-18 — advisor-recommended, human-ratified — history line 1557.
  Title: Advisor-recommended, human-ratified, 2026-08-15: the SIU reason code `NO_POLICY_INCEPTION_DATE` is renamed `NO_CONTINUOUS_COVERAGE_DATE` — implemented and merged at item 4d (`36ae5b3`, 2026-08-15); this entry read "in the spec draft so far, not yet implemented" until 2026-08-18.
  Note: Stale in the text: the SIU not-evaluated enumeration has had three codes since item 5g — `NO_JURISDICTION_DATE` beside `NO_THRESHOLD_CONFIGURED` and `NO_CONTINUOUS_COVERAGE_DATE`.

### From the section "Open decisions"

- **A094** — in force — 2026-08-24 — advisor-recommended, human-ratified — history line 1574.
  Title: Persistence engine: SQLite via the stdlib `sqlite3` module, decided 2026-08-24, advisor-recommended, human-ratified.

- **A098** — in force — 2026-08-25 to 2026-08-28 — advisor-recommended, human-ratified — history line 1688.
  Title: Item 5e's resolution endpoint: five points the design leaves open — escalated 2026-08-25, undecided, nothing drafted against any of them.
  Decisions: 1 (any field) — IN FORCE (`resolution.feature` rule "A reviewer may correct a field the notice already had..."). 2(a) full validation — IN FORCE (`resolution_evaluation.py:18`). 2(b) resolution's own date — IN FORCE (rule "A resolution is judged on the calendar date it arrives, not the one the notice was pended on"). 3 refused data kept — IN FORCE (rule "What a refused resolution supplied is kept, in sequence..."). 4 `USER` stamped, 400 — IN FORCE (`resolution.py:77`). 5 `RECEIVED` gets 409 — IN FORCE, no scenario, by the 2026-08-28 measurement. (a) `pended_at`/`resolved_at` — IN FORCE (`schema.py:86–87`). (b) schema recreates — IN FORCE (unverified beyond `CREATE TABLE IF NOT EXISTS` at `schema.py:122`). (c) within-code blocker order stated nowhere in `validation.feature` — STILL OPEN (`validation.feature` has no "alphabetical" statement; `resolution.feature:493` still asserts `claimant_name` before `incident_description`). (d) 404 — IN FORCE (`resolution.py:20`). (e) unparseable loss date 400 — IN FORCE (`resolution.py:16`).

- **A099** — in force — 2026-08-24 to 2026-08-28 — advisor-recommended, human-ratified — history line 1869.
  Title: Item 5i decisions, advisor-recommended, human-ratified, 2026-08-28.
  Decisions: 1–5 — IN FORCE (`faults.py:36–37`; `schema.py:117` `error_code`; `notice_intake.feature` scenario "A carrier this deployment cannot configure is receipted, refused as our defect, and creates no notice"; `resolution.feature` rule "A fault in this deployment's own configuration is answered as ours, and the reviewer's attempt leaves no trace"). 6 no `RULESET_VERSION` bump — IN FORCE (codes live in `shell/faults.py`). The two stale `NotImplementedError` messages — FIXED (`resolution.py:44` "No NotImplementedError remains"). A third code, `PORT_BINDING_UNRESOLVABLE`, joined the enumeration at 7e/7f (A058, A061 decision 7), so "closed" now means three.
  Note: Stale in the text: the two-code enumeration of deployment faults has a third code, `PORT_BINDING_UNRESOLVABLE`, from A058 decision 5 (2026-09-06), surfaced by A061 decision 7.

- **A100** — in force as amended — 2026-08-28 — bare "decided" — history line 1940.
  Title: Item 5i implementation shapes — decided at the keyboard, 2026-08-28, none of them a rule.
  Status: shapes 1–5 stand; the closing note that `notice_intake.py` and `resolution.py` sit at the 250-line ceiling is SUPERSEDED: both were split (7f extracted `receipt.py`, 7h split `bundles.py`), and they are 207 and 111 lines at be87d38.

- **A101** — in force — 2026-08-25 — advisor-recommended, human-ratified — history line 1994.
  Title: Item 5f, SIU separation — six decisions, advisor-recommended, human-ratified, 2026-08-25.

- **A102** — in force — 2026-08-25 — advisor-recommended, human-ratified — history line 2039.
  Title: Item 5f, one point the six decisions do not cover — escalated 2026-08-25 while drafting `features/siu_separation.feature`, undecided, nothing drafted against it.

### From the section "Synthetic data"

- **A104** — in force — undated — none — history line 2098.
  Title: No real policy numbers, names, addresses, phone numbers, or claim numbers appear anywhere in specs, fixtures, or tests.

## Open (8)

### From the section "Domain defects found, not yet fixed"

- **A074** — still open — undated — none — history line 1200.
  Title: Exact `loss_type` equality in the duplicate match key is a false-negative source, and a real tradeoff rather than an obvious relaxation.
  Status: the match key still requires exact loss-type equality.

- **A075** — still open — 2026-08-18 — none — history line 1207.
  Title: The `duplicates.feature` notice_type exclusion (`QUEUE.md` item 3) guards only the candidate side of the comparison — an existing claim carries no notice type, so the reverse direction is unguarded.
  Status: `ExistingClaim` carries `claim_id`, `policy_number`, `loss_date`, `loss_type` and no notice or coverage type, so the reverse direction is still unguarded; the claims port (7h) did not add one.

- **A077** — still open — undated — none — history line 1242.
  Title: "injury" is modelled as a peril rather than a Section II liability coverage.
  Status: `loss_type` is single-valued and `injury` sits in the recognized set; the open decision is A096.

- **A081** — still open — undated — none — history line 1281.
  Title: The record captures no reporter identity or relationship to the insured.
  Status: `NoticeFields` names no reporter identity or capacity; "represented at FNOL" is not an indicator (A101's candidate list names it as a future candidate needing its own basis, so the rejection here stands as the constraint on that).

### From the section "Data we do not have at intake"

- **A092** — still open — undated — none — history line 1554.
  Title: The phase-1 SIU tests pass at 100% mutation score against fixture data with no real-world source.
  Status: every input is still fixture data (`tests/fixtures/core_system.py`, `tests/fixtures/extract.py`); no real-world source exists.

### From the section "Open decisions"

- **A095** — still open — undated — none — history line 1592.
  Title: Replacement for the 30-day late-reporting threshold — not being set now.
  Status: the threshold is caller-supplied, illustrated as 45 days in the spec, and no value is agreed.

- **A096** — still open — 2026-08-17 — none — history line 1600.
  Title: `loss_type` conflates perils with Section II coverage categories, and the conflation is load-bearing today, not cosmetic.
  Status: one field still carries both facts. Detail: the entry quotes the high-severity set as `{"injury", "fire"}`; it is `{"injury", "fire", "sinkhole"}` since 4c (part 3).
  Note: Stale in the text: the high-severity set it quotes is `{"injury", "fire", "sinkhole"}` since item 4c (`triage.py`).

- **A103** — still open — 2026-09-01 — none — history line 2089.
  Title: Retention is currently an unapproved default — opened 2026-09-01, decided in phase 5.
  Status: ROADMAP.md phase 5 owns it; no deletion path exists (`schema.py` triggers refuse UPDATE/DELETE per `audit.py:11`, `payloads.py:13–14`).

## Settled: fixed, decided, superseded or retired (18)

### From the section "Carrier estate — no internal access to any"

- **A009** — retired — undated — none — history line 80.
  Title: Policy number format.
  Status: "currently a domain-layer regex" stopped being true at item 7d (`2e8ba71`, 2026-09-06): nothing checks a policy number's shape anywhere, so the format is no longer assumed by any rule.

### From the section "Carried requirements — decided, not yet built"

- **A042** — superseded — 2026-08-22 — advisor-recommended, human-ratified — history line 731.
  Title: Phase 2 matches duplicate candidates against ClaimGate's own persisted notices only — advisor-recommended, human-ratified, 2026-08-22.
  Status: by A063 (item 7h, 2026-09-09): the candidate set is the claims the claims port returns for the policy the search found, not ClaimGate's own notices. The entry's own "Revisit when the phase-3 adapter lands" is that revisit.

- **A043** — superseded — 2026-08-22 — advisor-recommended, human-ratified — history line 746.
  Title: The continuous coverage date does not exist in phase 2, so the recent-inception indicator resolves not-evaluated on every phase-2 notice — advisor-recommended, human-ratified, 2026-08-22.
  Status: by A089 (item 7b, 2026-09-04) and A061 decision 5 (item 7f, 2026-09-07): the date is derived from the port's term history and reaches the indicator; `NOT_EVALUATED`/`NO_CONTINUOUS_COVERAGE_DATE` is now the path for a source that could not answer. The phase-2 statement was correct for phase 2 and is dated history.

- **A049** — retired — 2026-08-22 — advisor-recommended, human-ratified — history line 831.
  Title: Example prefix sets use `HO` and `DP`, never `AU` - advisor-recommended, human-ratified, 2026-08-22.
  Status: the prefix set itself was retired at item 7d (`2e8ba71`, 2026-09-06; A057 decision 1), so no example prefix set exists to use `HO`/`DP`. No `AU` remains in `features/`.

### From the section "Undocumented phase-1 thresholds"

- **A066** — retired — undated — none — history line 1115.
  Title: 365 (`REPORTING_WINDOW_DAYS`).
  Status: the gate is gone ("Now removed"); late notice is non-blocking. Removing commit: unverified (not located by grep of the log this session; A035 attributes the line to item 2).

- **A067** — retired as a constant — undated — none — history line 1119.
  Title: 30 (`LATE_REPORTING_THRESHOLD_DAYS`).
  Status: item 2 (`9d3fc2d`, 2026-08-10) made the threshold caller-supplied with no default; the replacement value is STILL OPEN (A095).

- **A068** — retired — 2026-08-13 — none — history line 1125.
  Title: 500 (`THEFT_LOW_SEVERITY_THRESHOLD`).
  Status: by A032 (loss amount out of the severity rule), built at item 4c (merge commit unverified this session).

### From the section "Domain defects found, not yet fixed"

- **A070** — fixed — 2026-08-09 — none — history line 1150.
  Title: SIU flag overrides queue routing.
  Status: item 1, `7f985e7`, 2026-08-09.

- **A071** — fixed as to the default (item 2, `9d3fc2d`, 2026-08-10); the legal question still open (a095). — 2026-08-10 — none — history line 1161.
  Title: Late reporting fires at 30 days against a one-year statutory notice window

- **A072** — fixed — 2026-08-10 — none — history line 1172.
  Title: `siu_flags.feature` framing
  Status: item 2, `9d3fc2d`, 2026-08-10.

- **A073** — fixed — 2026-08-12 — none — history line 1181.
  Title: `duplicates.feature` framing and gaps.
  Status: item 3, `0b4e315`, 2026-08-12.

- **A076** — fixed — 2026-08-13 to 2026-08-18 — none — history line 1218.
  Title: Loss type vocabulary, policy number prefixes, and example data across all four feature files reflect a multi-line liability book
  Status: items 4a and 4b (both 2026-08-13), amended at 4j; the shape it left open closed by retirement at 7d (A097, 2026-09-06).
  Decisions: example data — FIXED (4a, 4b). Prefix set — configuration at 4j, then RETIRED at 7d. Number shape — RETIRED at 7d.
  Note: Date: this entry and the queue history date item 4j's merge `22d672e` 2026-08-18; git dates it 2026-08-21, author and committer alike.

- **A078** — fixed — undated — none — history line 1244.
  Title: Loss amount affects severity only for theft.
  Status: by removal, not by extension: A032 (2026-08-13, item 4c) took loss amount out of the severity rule for every peril. The entry's own framing (amount as a severity signal) was rejected, so "fixed" here means the defect no longer exists, not that the entry's implied remedy was adopted.

- **A079** — decided — undated — none — history line 1247.
  Title: No plausibility floor on loss date.
  Status: the principled fix this entry names, a loss date checked against policy data, has existed since items 7a and 7f as the term-in-force verification. It is delivered as an attribute of the notice, never a refusal: a loss before any term surfaces in the locked scenario `coverage_verification.feature`, "A loss before any term began has no term to cite". No entry recorded the connection; ruled 2026-09-11, advisor-recommended, human-ratified.

- **A080** — fixed — 2026-08-09 to 2026-08-15 — none — history line 1250.
  Title: `compute_siu_flags` already guards against a policy inception date after the loss date, and nothing has ever said so.
  Status: the scenario exists: `siu_indicators.feature` at be87d38 rule "A continuous coverage date after the loss date does not indicate recent policy inception". Date note: item 2's implementation `33d602b` is 2026-08-09 and its merge `9d3fc2d` is 2026-08-10; the entry's "RESOLVED 2026-08-09" matches the implementation, A071/A072 use the merge date (part 3).
  Decisions: the larger question (a loss predating coverage is a coverage problem) — DECIDED at 7a: `coverage_verification.feature` answers it as the term-in-force verification (see A079).
  Note: Date: item 2 merged at `9d3fc2d` on 2026-08-10; 2026-08-09 is its implementation commit `33d602b`.

- **A083** — fixed — 2026-08-24 — advisor-recommended, human-ratified — history line 1311.
  Title: An absent loss date is a domain blocker, not a schema refusal — advisor-recommended, human-ratified, 2026-08-24.
  Status: item 5h, merged `e8e76c0` (2026-08-27); `loss_date` is `date | None` and validation has a presence check.

### From the section "Open decisions"

- **A097** — decided — 2026-08-18 to 2026-09-06 — none — history line 1644.
  Title: `POLICY_NUMBER_PATTERN` encodes a carrier fact in the domain layer, and item 4b narrows the prefix set without resolving that.
  Status: closed 2026-09-06 by retirement (A057 decision 1, `2e8ba71`); the entry records this itself.
  Note: Date: this entry and the queue history date item 4j's merge `22d672e` 2026-08-18; git dates it 2026-08-21, author and committer alike.

### From the section "Synthetic data"

- **A105** — superseded — undated — none — history line 2101.
  Title: Carrier identity data (names, NAIC codes) is public regulatory information, used because the design targets a real, named carrier estate rather than a generic one.
  Status: by A038 (2026-08-17): there is no "real, named carrier estate", and the identity reference now holds "Placeholder Carrier A/B/C" with NAIC values 10001–10003 and group 4001, which are not public regulatory data. The first clause is false at be87d38; the second ("everything else is fabricated") still holds. Part 3.
  Note: In force instead: carrier identity data is fabricated placeholders, like everything else here.

## Records (7)

### From the section "docs/decisions.md audit"

- **A002** — record only — undated — none — history line 38.
  Title: Headline finding: zero of the seven entries cite an external source.
  Status: a count over `docs/decisions.md`; it decides nothing.

- **A003** — record only — undated — none — history line 43.
  Title: Rationale contradicts its own rule (1 — worst category):
  Status: the 365-day gate it audits is retired (A066; "Now removed" in the entry); the audit finding itself has no rule.

- **A004** — record only — undated — none — history line 48.
  Title: Asserts an unverified or false fact (2):
  Decisions: the 30-day recent-inception default — RETIRED as a default at item 2 (`9d3fc2d`, 2026-08-10; A071). The LOB prefix list — RETIRED at item 7d (`2e8ba71`, 2026-09-06; A057 decision 1), after narrowing at 4b and 4j.

- **A005** — record only — undated — none — history line 58.
  Title: Restates the rule (1):
  Status: its subject is moot (A032, A068: loss amount left the severity rule).

- **A006** — record only — undated — none — history line 60.
  Title: Orphaned (1):
  Status: the 3-day window was replaced by a caller-supplied window at item 3 (A073; `0b4e315`, 2026-08-12).

- **A007** — record only — undated — none — history line 68.
  Title: Records a rationale (2):
  Decisions: the 30-day late-reporting default — RETIRED at item 2 (A071); its replacement STILL OPEN (A095). "LOB-vs-loss-type cross-validation: deferred" — RETIRED with the prefix set at item 7d (A057): there is no LOB in the domain to cross-validate.

### From the section "Data we do not have at intake"

- **A085** — record only — 2026-08-17 to 2026-09-01 — none — history line 1390.
  Title: Annotation, 2026-09-01: every reference in this section and elsewhere in this file to "phase 2's adapter layer" or "the phase-2 adapter" predates phase 2's close on 2026-08-30. Phase 2 shipped no policy administration adapter; the adapter is phase 3 (`ROADMAP.md`, `PHASE2_DESIGN.md`). "Each of the three policy administration systems" refers to the estate this project stopped targeting on 2026-08-17. The entries are left as written because they are dated history; read "phase 2's adapter" as "phase 3's".

## Decisions after prototype-1

None yet.
