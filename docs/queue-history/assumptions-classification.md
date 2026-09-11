# C2b classification report — ASSUMPTIONS.md at prototype-1 (be87d38)

Written 2026-09-11 on `cleanup/documents` at 370a042. ASSUMPTIONS.md read in full at HEAD,
sha256 prefix 5b306fc2561f0d3c, 2095 lines, unchanged since prototype-1. Working tree for
`src`, `tests`, `features` is byte-identical to be87d38 (`git diff --stat be87d38 HEAD -- features src`
printed nothing), so "source" and "locked spec" checks made on the tree are checks at be87d38.

Conventions. "checked" means read this session; "unverified" means not read this session.
Scenario titles are quoted from the locked files at be87d38 (`git show be87d38:features/...`).
Commit dates are `git log --date=iso-strict` on the named hash. Queue items are cited to
`docs/queue-history/phases-1-2.md` (items 1–5j) or `phase-3.md` (items 6–7i).

## Part 1 — entries

### A001 — (preamble, before any section) — line 11
Head: **Provenance convention, proposed 2026-08-14.** A dated decision below should carry a provenance
Dates: 2026-08-14 — convention proposed.
Provenance: none (proposed by the advisor; no ratification recorded in the entry).
Kind: convention
Status at prototype-1 (be87d38): IN FORCE — later entries carry the tags it defines (A016 onward), and undated or bare entries are read as unclassified.
Evidence: the entries below that carry the tags (checked, this file); no source or spec claim.
Live citations: 0

### A002 — docs/decisions.md audit — line 30
Head: **Headline finding: zero of the seven entries cite an external source.** Nothing in this project's
Dates: none.
Provenance: none
Kind: audit record
Status at prototype-1 (be87d38): RECORD ONLY — a count over `docs/decisions.md`; it decides nothing.
Evidence: README.md:75 still points at this audit (checked). `docs/decisions.md` itself: unverified this session.
Live citations: 1 (README.md:75 names "the audit of this file"; counted here as the section lead for A002–A007)

### A003 — docs/decisions.md audit — line 35
Head: - **Rationale contradicts its own rule (1 — worst category):**
Dates: none.
Provenance: none
Kind: audit record
Status at prototype-1 (be87d38): RECORD ONLY — the 365-day gate it audits is retired (A066; "Now removed" in the entry); the audit finding itself has no rule.
Evidence: A066 (later entry, checked); `validation.feature` at be87d38 scenario "A loss reported long after the date of loss is not blocked at intake" (checked, title list).
Live citations: 0

### A004 — docs/decisions.md audit — line 40
Head: - **Asserts an unverified or false fact (2):**
Dates: none.
Provenance: none
Kind: audit record
Status at prototype-1 (be87d38): RECORD ONLY
Sub-decisions: the 30-day recent-inception default — RETIRED as a default at item 2 (`9d3fc2d`, 2026-08-10; A071). The LOB prefix list — RETIRED at item 7d (`2e8ba71`, 2026-09-06; A057 decision 1), after narrowing at 4b and 4j.
Evidence: A071, A057, A097 (checked); git dates of `9d3fc2d` and `2e8ba71` (checked).
Live citations: 0

### A005 — docs/decisions.md audit — line 50
Head: - **Restates the rule (1):** *Theft low-severity threshold: $500* — restates what happens under
Dates: none.
Provenance: none
Kind: audit record
Status at prototype-1 (be87d38): RECORD ONLY — its subject is moot (A032, A068: loss amount left the severity rule).
Evidence: A032, A068 (checked); `src/claimgate/domain/triage.py` `assign_severity` takes no amount (checked, function index and `_HIGH_SEVERITY_LOSS_TYPES`).
Live citations: 0

### A006 — docs/decisions.md audit — line 52
Head: - **Orphaned (1):** *Duplicate detection window: 3 days* — "tight enough to avoid false positives
Dates: none.
Provenance: none
Kind: audit record
Status at prototype-1 (be87d38): RECORD ONLY — the 3-day window was replaced by a caller-supplied window at item 3 (A073; `0b4e315`, 2026-08-12).
Evidence: A073 (checked); `src/claimgate/domain/duplicates.py` `find_duplicates(..., window_days: int, ...)` (checked, line 17).
Live citations: 0

### A007 — docs/decisions.md audit — line 60
Head: - **Records a rationale (2):** *SIU late-reporting threshold: 30 days* (also orphaned in
Dates: none.
Provenance: none
Kind: audit record
Status at prototype-1 (be87d38): RECORD ONLY
Sub-decisions: the 30-day late-reporting default — RETIRED at item 2 (A071); its replacement STILL OPEN (A095). "LOB-vs-loss-type cross-validation: deferred" — RETIRED with the prefix set at item 7d (A057): there is no LOB in the domain to cross-validate.
Evidence: A071, A095, A057 (checked).
Live citations: 0

### A008 — Carrier estate — no internal access to any — line 70
Head: - **Carrier codes.** The 4-character `carrier_code` values in `PHASE2_DESIGN.md` are placeholders.
Dates: none.
Provenance: none
Kind: assumption
Status at prototype-1 (be87d38): IN FORCE — the identity reference holds `AAAA`, `BBBB`, `CCCC` named "Placeholder Carrier A/B/C".
Evidence: `src/claimgate/domain/carrier_identity.py` lines 29–31 (checked). PHASE2_DESIGN.md's "4-character" wording: unverified (grep for "4-char"/"four-char" found nothing; the codes themselves are 4 characters).
Live citations: 0

### A009 — Carrier estate — no internal access to any — line 72
Head: - **Policy number format.** Assumed, not known, and it varies between real carriers. Currently a
Dates: none.
Provenance: none
Kind: assumption
Status at prototype-1 (be87d38): RETIRED — "currently a domain-layer regex" stopped being true at item 7d (`2e8ba71`, 2026-09-06): nothing checks a policy number's shape anywhere, so the format is no longer assumed by any rule.
Evidence: A057 decision 1, A097 closing paragraph (checked); grep of `src/` for `POLICY_NUMBER_PATTERN` finds only two retrospective comments (checked); `policy_identification.feature` at be87d38 scenario "A policy number of unfamiliar shape is a search, not a pend" (checked, title list).
Live citations: 0

### A010 — Carrier estate — no internal access to any — line 74
Head: - **NAIC group codes.** The schema must tolerate a null group code. A member-owned reciprocal may
Dates: none.
Provenance: none
Kind: assumption
Status at prototype-1 (be87d38): IN FORCE — `CCCC` carries `naic_group=None`, with the entry's reasoning quoted beside it.
Evidence: `src/claimgate/domain/carrier_identity.py` lines 25–31 (checked).
Live citations: 0

### A011 — Carrier estate — no internal access to any — line 77
Head: - **Book scope.** The shipped configuration assumes Florida residential property only. A
Dates: none.
Provenance: none
Kind: assumption
Status at prototype-1 (be87d38): IN FORCE — the jurisdiction map and the recognized loss types are residential-property values; no auto or commercial peril exists.
Evidence: `src/claimgate/domain/validation.py` `RECOGNIZED_LOSS_TYPES` begins fire, flood, hurricane (checked, lines 26–30); `features/` at be87d38 contain no `AU` prefix (checked, grep).
Live citations: 0

### A012 — Carrier estate — no internal access to any — line 79
Head: - **"Policy administration system" in this project's documents means the carrier's core system
Dates: 2026-09-01 — noted.
Provenance: none (a note, undated as a decision; "noted 2026-09-01").
Kind: convention
Status at prototype-1 (be87d38): IN FORCE — PHASE3_DESIGN.md names "policy port" and "claims port" and cites this entry.
Evidence: PHASE3_DESIGN.md:106 (checked, citation line); `src/claimgate/shell/ports.py` `PolicyPort` and `ClaimsPort` (checked, function index).
Live citations: 1

### A013 — Carried requirements — decided, not yet built — line 88
Head: - **One receipt clock, not two — decided 2026-08-24, advisor-recommended, human-ratified.**
Dates: 2026-08-24 — decided; 2026-08-25 — extended to the resolution path by the instruction opening item 5e.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — the shell reads no clock; every receipt-adjacent instant is `submitted_at`, and a resolution's instants are its own caller-supplied instant. Built at item 5d (not "not yet built").
Evidence: grep of `src/` for `now(` returns nothing (checked); `src/claimgate/shell/receipt.py` lines 111–144 pass `submission.submitted_at` to the store and the port clock (checked); `resolution.feature` at be87d38 scenario "The instant a resolution is submitted is what is recorded for it, whenever that is" (checked, title list); `src/claimgate/shell/store.py:25` cites it (checked).
Live citations: 9

### A014 — Carried requirements — decided, not yet built — line 117
Head: - **Timezone-correct "now."** The phase-2 API shell must receive a timezone-aware UTC instant and
Dates: 2026-08-23 — two scenarios corrected while drafting 5b; 2026-08-23 — conversion moved to the domain (advisor-recommended, human-ratified). 2026-01-14/15, 2026-03-08, 2026-06-10/11, 2026-07-14/15, 2026-11-01 — example instants and DST transition dates, not events.
Provenance: bare (the original entry is undated and untagged); the 2026-08-23 correction is advisor-recommended, human-ratified.
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — amended in place by its own two 2026-08-23 corrections, and by A015 (zone is a parameter) and A017/A020 (the zone comes from the jurisdiction map, not the submission).
Sub-decisions: the principle (domain never receives a server-local date) — IN FORCE. The four named scenarios as corrected — IN FORCE (`jurisdiction_date.feature` rules "An instant resolves to the calendar date in the jurisdiction's timezone..." and "The UTC offset in effect for a date, not proximity to a DST transition..."). Pinning `tzdata` in `pyproject.toml` — STILL OPEN (no `tzdata` in `pyproject.toml`; the entry said "settled with item 5c's deployment work", and no later entry settles it).
Evidence: `src/claimgate/domain/jurisdiction.py` lines 38, 87–88 import `zoneinfo` and refuse on `ZoneInfoNotFoundError` (checked); `jurisdiction_date.feature` at be87d38 rule titles (checked); `pyproject.toml` grep for `tzdata` empty (checked).
Live citations: 6

### A015 — Carried requirements — decided, not yet built — line 175
Head: - **The jurisdiction timezone is a parameter of the conversion, not a constant in it.**
Dates: 2026-08-22 — advisor-recommended, human-ratified. 2026-06-10/11 — example instant.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Sub-decisions: the parameter — IN FORCE (`jurisdiction_date.feature` rule "The jurisdiction's timezone is a parameter the resolution reads, not a zone it assumes"). "Which zone a given notice gets" recorded as open — DECIDED at item 5g by A017 (one zone per jurisdiction, keyed on `property_state`) and A018.
Evidence: `src/claimgate/domain/jurisdiction.py` `resolve_jurisdiction_date(instant, timezone_name)` (checked, function index and lines 85–88); A017, A018 (checked).
Live citations: 3

### A016 — Carried requirements — decided, not yet built — line 187
Head: - **An unrecognized jurisdiction timezone is refused, never defaulted — advisor-recommended,
Dates: 2026-08-23 — ratified; 2026-08-23 — code-name order verified against `src/claimgate/domain/`.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Sub-decisions: the refusal — IN FORCE (`jurisdiction_date.feature` rule "An unrecognized jurisdiction timezone refuses the resolution rather than falling back to a default"; `JURISDICTION_TIMEZONE_UNRECOGNIZED` at `jurisdiction.py:46`). "Settle the inconsistency when 5a's implementation lands" (subject-first vs `MISSING_REQUIRED_CONFIGURATION`) — STILL OPEN: `carrier_configuration.py` lines 26–28 still carry `MALFORMED_REQUIRED_CONFIGURATION` and `MISSING_REQUIRED_CONFIGURATION`, and no later entry settles the order.
Evidence: source lines named (checked); spec rule title (checked).
Live citations: 1

### A017 — Carried requirements — decided, not yet built — line 208
Head: - **One timezone per jurisdiction, and Florida's is `America/New_York` — advisor-recommended,
Dates: 2026-08-26 — ratified; 2026-08-26 — county list corrected; 2026-08-26 — 49 CFR 71.5(f) verified via a search excerpt.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Sub-decisions: one zone per jurisdiction, Eastern for Florida — IN FORCE (`jurisdiction.py:62` comment "Eastern's date is never behind Central's"; `jurisdiction_selection.feature:64–66` comment). Re-verify 49 CFR 71.5(f) against the full section — STILL OPEN: `STATUTORY_REGISTER.md` has no `49 CFR` entry (checked, grep empty), so the boundary rests on the search excerpt only.
Evidence: source and spec comment lines named (checked); `STATUTORY_REGISTER.md` grep (checked).
Live citations: 2

### A018 — Carried requirements — decided, not yet built — line 246
Head: - **`property_state` is matched exactly, and a miss is marked rather than normalized —
Dates: 2026-08-26 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `src/claimgate/domain/jurisdiction.py` lines 29–31 ("The match is exact", nothing upper-cased or trimmed) (checked); `jurisdiction_selection.feature` at be87d38 scenario "A notice whose property state has no supported jurisdiction is still created and triaged" (checked, title list); `tests/unit/test_jurisdiction.py:111` (checked, citation line).
Live citations: 2

### A019 — Carried requirements — decided, not yet built — line 257
Head: - **The zone that dates a resolution's SIU interval comes from the merged view, not from what was
Dates: 2026-08-26 — ratified; 2026-08-26 — the named path corrected as unreachable.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `src/claimgate/shell/resolution_evaluation.py` lines 21–22 ("the jurisdiction the merged view selects, not the one known at receipt") (checked); `jurisdiction_selection.feature` at be87d38 scenario "A late reporting interval is counted under the jurisdiction the resolution supplies" (checked, title list); `resolution.feature` rule "A resolution is acted on only while the notice is still pended" supports the unreachable-path correction (checked, title list).
Live citations: 3

### A020 — Carried requirements — decided, not yet built — line 277
Head: - **`jurisdiction_timezone` is removed from the submission surface rather than kept beside
Dates: 2026-08-26 — ratified; 2026-08-26 — cost measured (four specs reopened).
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — `jurisdiction_timezone` appears in `src/` only as a retrospective comment in `messages.py`; the specs' Backgrounds use "the insured property is in".
Evidence: `src/claimgate/shell/messages.py` lines 33–35 (checked); grep of `src/` for `jurisdiction_timezone` (checked: comment only; the acceptance test for the domain function still names the parameter, which is the conversion's argument, not a submission field). The four-spec reopening's mutant counts: unverified this session.
Live citations: 1

### A021 — Carried requirements — decided, not yet built — line 300
Head: - **The future-dated-loss determination is off every outward surface in phase 2; the jurisdiction
Dates: 2026-08-27 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — `NoticeView` carries `jurisdiction_marking` and no future-dated-loss field. The ordering constraint for a later item is STILL OPEN by design (no item has wanted the determination visible).
Evidence: `src/claimgate/shell/messages.py` lines 90–95, 119 (checked); `src/claimgate/shell/serialization.py` `NOTICE_VIEW_FIELDS` (unverified beyond the function index).
Live citations: 0

### A022 — Carried requirements — decided, not yet built — line 322
Head: - **An instant that is not a timezone-aware UTC instant is out of scope for item 5b —
Dates: 2026-08-23 — ratified; 2026-08-23 — annotated, measured (the violation is silent). 2026-06-10/11 — example instant.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — `resolve_jurisdiction_date` still has no naive-datetime guard, as the entry requires.
Sub-decisions: out of scope for 5b — IN FORCE. The obligation moved to item 5c (where the instant is obtained) — unverified: no later entry records 5c discharging it, and I did not read `receipt.py`'s instant handling for an awareness check.
Evidence: `src/claimgate/domain/jurisdiction.py` lines 85–88 (checked: no `tzinfo` test).
Live citations: 0

### A023 — Carried requirements — decided, not yet built — line 346
Head: - **A refused submission is still a received communication — advisor-recommended,
Dates: 2026-08-23 — ratified; 2026-08-23 — 627.70131 verified against the Florida Legislature's text.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Sub-decisions: refused payload persisted with its hash, no notice — IN FORCE (`notice_intake.feature` at be87d38 scenario "A notice is created only if its loss date is a real date"; `receipt.py:129` `refuse_payload`). Retention of refused payloads "item 5g's problem" — STILL OPEN, now A103 (phase 5).
Evidence: `src/claimgate/shell/receipt.py` line 129 (checked); spec title (checked); A103 (checked).
Live citations: 1

### A024 — Carried requirements — decided, not yet built — line 383
Head: - **Item 5c's 400 validates against the identity reference, not the rules source —
Dates: 2026-08-24 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `src/claimgate/domain/carrier_identity.py:13` (checked, citation line); `notice_intake.feature` at be87d38 scenario "A carrier absent from the identity reference is refused before any record is made" (checked, title list); `f19317e` exists, dated 2026-08-23 (checked).
Live citations: 2

### A025 — Carried requirements — decided, not yet built — line 393
Head: - **A carrier this deployment administers but cannot configure is our defect, not the reporter's —
Dates: 2026-08-24 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — the status code left as "5xx" was fixed at `500` by A099 ruling 1 (2026-08-28); the response column on `notice_intake.feature` Rules 1 and 3 is in the locked spec.
Evidence: A099 (checked); `notice_intake.feature` at be87d38 scenario "A carrier this deployment cannot configure is receipted, refused as our defect, and creates no notice" (checked, title list); `src/claimgate/shell/faults.py:36` `CARRIER_RULES_UNRESOLVABLE` (checked).
Live citations: 1

### A026 — Carried requirements — decided, not yet built — line 411
Head: - **The payload reference recipe — advisor-ratified, 2026-08-24.** SHA-256 over the submitted
Dates: 2026-08-24 — advisor-ratified.
Provenance: advisor-recommended, human-ratified (the entry's own tag is "advisor-ratified"; read as the standard tag, flagged in part 3).
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Sub-decisions: the recipe — IN FORCE (`records.py:124` `json.dumps(raw_payload, sort_keys=True, default=str)`). "Revisit when a literal HTTP layer exists" — STILL OPEN (no HTTP layer exists; `resolution.py:4–5` says so).
Evidence: `src/claimgate/shell/records.py` lines 124–129 (checked); `idempotency.feature` at be87d38 scenario "Whether a repeated key is honoured as a replay depends on whether the notice content is unchanged" (checked, title list).
Live citations: 2

### A027 — Carried requirements — decided, not yet built — line 432
Head: - **Idempotency: what a repeated key is compared against, and when the window closes —
Dates: 2026-08-24 — ratified; 2026-08-24 — decision 4 corrected by the advisor before implementation; 2026-08-24 — RFC 9111 §4.2 verified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Sub-decisions: (1) reference comparison — IN FORCE (spec title above). (2) key examined before the schema boundary — IN FORCE (`receipt.py:3` docstring order). (3) 409 keeps the content — IN FORCE (unverified in source; `idempotency.feature:188–190` comment). (4) key table of its own — IN FORCE (`schema.py:122–126` `idempotency_keys` with `UNIQUE (carrier_code, idempotency_key)`). (5) half-open window — IN FORCE (`idempotency.py:32,45` `timedelta(hours=24)` and `<`). Carried to 5e — DECIDED: `resolution.feature` rule "A replay of the original submission reports the state the notice is in now, not the one it landed in".
Evidence: source lines named (checked); spec titles (checked).
Live citations: 8

### A028 — Carried requirements — decided, not yet built — line 483
Head: - **Unevaluated is not negative.** General rule, not SIU-specific, to implement when the SIU
Dates: none.
Provenance: none (undated, untagged; predates A001).
Kind: convention
Status at prototype-1 (be87d38): IN FORCE — every three-valued result in the domain models cites it; it is also a CLAUDE.md standing constraint.
Evidence: `src/claimgate/domain/models.py` lines 42, 86, 112, 172 (checked, citation lines); `duplicates.feature` at be87d38 rule "Every notice type either gets compared for a candidate match, or is explicitly not evaluated with a reason - never silently defaulted" (checked, title list); CLAUDE.md "A result that was not computed is never reported as a negative" (checked).
Live citations: 7

### A029 — Carried requirements — decided, not yet built — line 490
Head: - **Recent-inception reason-code precedence when both required inputs are absent.** When
Dates: 2026-08-18 — corrected: reachable now, scenario owed, sequenced as item 4k.
Provenance: bare "decided" (unclassified) — "Reviewed and confirmed correct ... on a later pass", no tag.
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Sub-decisions: the precedence — IN FORCE (`siu.py:80–83`: coverage-date check first, "Do not reorder these checks"). The owed scenario — FIXED at item 4k (`7da0bd1`, git-dated 2026-08-21; queue history says 2026-08-18): `siu_indicators.feature` at be87d38 scenario "Neither recent policy inception input is present".
Evidence: source lines (checked); spec title (checked); `7da0bd1` date (checked, git).
Live citations: 3

### A030 — Carried requirements — decided, not yet built — line 516
Head: - **Severity assignments for the new perils (`hurricane`, `sinkhole`, `roof_leak`) — decided
Dates: 2026-08-13 — decided, documentation-only session.
Provenance: bare "decided" (unclassified)
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — `sinkhole` is in the high-severity set; `hurricane` and `roof_leak` are not.
Evidence: `src/claimgate/domain/triage.py:5` `_HIGH_SEVERITY_LOSS_TYPES = frozenset({"injury", "fire", "sinkhole"})` (checked); `triage.feature` at be87d38 rule "Severity is assigned from loss type" (checked, title list). Item 4c's merge commit: unverified (not located by grep of the log this session).
Live citations: 0

### A031 — Carried requirements — decided, not yet built — line 527
Head: - **Catastrophe handling is a deliberate non-goal for this phase, not an oversight — the reasoning
Dates: none (same session as A030, 2026-08-13).
Provenance: bare "decided" (unclassified), by inheritance from A030.
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — no catastrophe attribute exists; `hurricane` routes standard.
Evidence: `triage.py:5–6` (checked); no `catastrophe` symbol in the function index (checked).
Live citations: 0

### A032 — Carried requirements — decided, not yet built — line 533
Head: - **Loss amount is removed from the severity rule entirely, not replaced with a better threshold —
Dates: none ("decided in the same session", 2026-08-13).
Provenance: bare "decided" (unclassified)
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — `assign_severity` reads loss type only; `loss_amount` is captured on `Candidate` and read by no rule.
Evidence: `triage.py` `assign_severity` (checked, function index and line 12); `models.py:20` `loss_amount: Decimal | None = None` (checked); `gauntlet.lock.json` approvals citing "item 4c" retain the column as the demonstration (checked, 11 lines).
Live citations: 0

### A033 — Carried requirements — decided, not yet built — line 543
Head: - **Advisor-recommended, human-ratified, 2026-08-14: the `low` severity band and its `fast_track`
Dates: 2026-08-14 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `triage.py:6` `_SEVERITY_QUEUES = {"standard": "standard", "high": "complex"}` (checked); `triage.feature` at be87d38 rule "Queue is derived from severity alone" (checked, title list).
Live citations: 0

### A034 — Carried requirements — decided, not yet built — line 551
Head: - **Advisor-recommended, human-ratified, 2026-08-14: the end-to-end outline keeps its `loss_amount`
Dates: 2026-08-14 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — the column stands and its surviving mutants are approved with this reasoning.
Evidence: `gauntlet.lock.json` lines 222–282, eleven approval reasons "The column is retained deliberately to demonstrate that independence (ASSUMPTIONS.md, item 4c)" (checked); `models.py:20` (checked); `triage.feature` at be87d38 scenario "From raw record to queue, with SIU indicators recorded separately and never affecting routing" (checked, title list).
Live citations: 11 (all eleven `gauntlet.lock.json` lines; their locator names item 4c, not this entry's title)

### A035 — Carried requirements — decided, not yet built — line 560
Head: - **The blocking criterion: a missing field blocks intake only if the information is actionable and
Dates: 2026-08-16 — decided, documentation-only session.
Provenance: bare "decided" (unclassified)
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — late notice does not block (`validation.feature` scenario "A loss reported long after the date of loss is not blocked at intake"); `flood` is recognized; the same test was applied at 7c/7f (A060: "a blocker is something a reviewer can supply").
Evidence: spec title (checked); `validation.py:26–30` includes `flood` (checked); A060 (checked).
Live citations: 0

### A036 — Carried requirements — decided, not yet built — line 579
Head: - **Carrier-varying rules are caller-supplied configuration with no domain default —
Dates: 2026-08-17 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — the six values (now four after 7d retired the prefix set) are caller-supplied; the loader refuses an absent required one.
Evidence: `src/claimgate/domain/carrier_configuration.py` `_REQUIRED_FIELDS` (three) and `_OPTIONAL_THRESHOLD_FIELDS` (two) (checked, lines 48–66); `carrier_configuration.feature:121` quotes this entry (checked); `siu_indicators.feature` rule "Late reporting is evaluated against a threshold supplied by the caller" (checked, title list).
Live citations: 1

### A037 — Carried requirements — decided, not yet built — line 603
Head: - **Item 4g's Section II required-field set is carrier configuration; `incident_description` is not 
Dates: 2026-08-17 — ratified; supersedes a 2026-08-16 decision (not itself an entry in this file).
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — built at item 4g (merge `51f2956`, 2026-08-19).
Evidence: `carrier_configuration.py:49–50` `claimant_name_required`, `claimant_contact_required` (checked); `validation.feature` at be87d38 scenarios "Required fields for an injury loss, by configuration" and "Required fields for a liability loss, by configuration" (checked, title list); `51f2956` date (checked, git).
Live citations: 0

### A038 — Carried requirements — decided, not yet built — line 622
Head: - **ClaimGate is a general product, not a build against one named estate — stated 2026-08-17.**
Dates: 2026-08-17 — stated.
Provenance: bare (unclassified) — "stated", no tag; reads as the human's product decision.
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — no named estate appears anywhere; carriers are placeholders (A008).
Sub-decisions: consequence 1 (4b prefix set as configuration scope) — RETIRED at item 7d (A057). Consequence 2 (`POLICY_NUMBER_PATTERN` belongs to the adapter) — DECIDED by retirement at 7d (A097's closing paragraph, 2026-09-06). Consequence 3 (NAIC codes now in `STATUTORY_REGISTER.md`) — unverified. Consequence 4 (no history rewrite) — IN FORCE (history intact; `git log` resolves every cited hash).
Evidence: `carrier_identity.py:29–31` placeholders (checked); A057, A097 (checked); PHASE3_DESIGN.md:243 (checked, citation line).
Live citations: 0 resolved; 1 ambiguous (PHASE3_DESIGN.md:243 fits A038 and A097)

### A039 — Carried requirements — decided, not yet built — line 646
Head: - **A carrier configuration crosses into the domain already resolved, so the domain has no
Dates: 2026-08-17 — ratified; 2026-08-23 — annotated: the boundary language no longer holds, the substance does.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — amended by its own 2026-08-23 annotation (the loader lives in `src/claimgate/domain/carrier_configuration.py`); the six rules still have no unrecognized-configuration branch.
Evidence: `carrier_configuration.py:10` cites it and sits in `domain/` (checked); `validation.py` `_check_claimant_fields` takes booleans (checked, function index; parameter types unverified); `tests/acceptance/test_validation_acceptance.py:12` (checked, citation line).
Live citations: 5

### A040 — Carried requirements — decided, not yet built — line 679
Head: - **The per-carrier rules file moves from phase 3 into phase 2 — advisor-recommended,
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — the lookup-not-branch shape is built (`rules.py:109–115` `resolve_rules(carrier_code, rules_source)`); "six values" became five at 7d (prefix set retired, A057). The "rules file" as a file: see A050 and part 3 — no file reader exists in the tree; the source is a mapping the caller supplies.
Sub-decisions: carrier axis for five of six — IN FORCE. The late-reporting threshold's axis — STILL OPEN (A095).
Evidence: `src/claimgate/shell/rules.py` lines 109–115 (checked); `carrier_configuration.feature:32` (checked, citation line); PHASE2_DESIGN.md:291, 480 (checked, citation lines).
Live citations: 2 (+ PHASE2_DESIGN.md:291, NO LOCATOR, whose content is this entry)

### A041 — Carried requirements — decided, not yet built — line 705
Head: - **Duplicate-detection not-evaluated reason codes do not appear in `reason_codes` —
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — reaffirmed as 7h decision 6 (A063); the evaluation is one structure on the notice.
Evidence: `src/claimgate/shell/duplicate_evaluations.py:86` (checked, citation line); A063 decision 6 (checked); `duplicate_evaluation.feature` at be87d38 rule "A notice that could not be compared says why..." (checked, title list); PHASE2_DESIGN.md:185 (checked).
Live citations: 3 (+ `duplicate_evaluation.feature:7`, ambiguous with A042)

### A042 — Carried requirements — decided, not yet built — line 723
Head: - **Phase 2 matches duplicate candidates against ClaimGate's own persisted notices only —
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): SUPERSEDED — by A063 (item 7h, 2026-09-09): the candidate set is the claims the claims port returns for the policy the search found, not ClaimGate's own notices. The entry's own "Revisit when the phase-3 adapter lands" is that revisit.
Evidence: A063 decisions 3–5 (checked); `duplicate_evaluation.feature` at be87d38 rule "A triaged notice is compared against the claims on the policy the search found" (checked, title list); `src/claimgate/shell/duplicate_evaluations.py` `evaluate_duplicates` and `ClaimsPort` import (checked, lines 43, 106).
Live citations: 0 resolved; 1 ambiguous (`duplicate_evaluation.feature:7`)

### A043 — Carried requirements — decided, not yet built — line 738
Head: - **The continuous coverage date does not exist in phase 2, so the recent-inception indicator
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): SUPERSEDED — by A089 (item 7b, 2026-09-04) and A061 decision 5 (item 7f, 2026-09-07): the date is derived from the port's term history and reaches the indicator; `NOT_EVALUATED`/`NO_CONTINUOUS_COVERAGE_DATE` is now the path for a source that could not answer. The phase-2 statement was correct for phase 2 and is dated history.
Evidence: `policy_match.feature` at be87d38 scenario "The continuous-coverage date reaches the recent policy inception indicator" (checked, title list); `siu_separation.feature:148` comment still describes the phase-2 stub for a Background whose source is unavailable (checked, citation line); A061, A089 (checked).
Live citations: 1

### A044 — Carried requirements — decided, not yet built — line 752
Head: - **A configuration value that is present but malformed is refused at load, alongside an absent one
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `carrier_configuration.feature` at be87d38 scenario "A single value absent or malformed in a recognized carrier's entry refuses the load, naming it" (checked, title list); `carrier_configuration.py` `_is_boolean`, `_is_valid_day_count` (checked, lines 40–46).
Live citations: 1

### A045 — Carried requirements — decided, not yet built — line 767
Head: - **A refusal names every value it rejected, not the first one — advisor-recommended,
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `carrier_configuration.feature` at be87d38 scenario "Several missing and malformed values in the same entry are all named in one refusal, in canonical order" (checked, title list); `carrier_configuration.py` `_check_required_fields` returning a collection (checked, function index; body unverified).
Live citations: 0

### A046 — Carried requirements — decided, not yet built — line 779
Head: - **A missing configuration value and a malformed one are different reason codes -
Dates: 2026-08-22 — ratified; 2026-08-22 — old name's occurrences measured at `5d37a4f`; 2026-08-22 — `validate()`'s sort key verified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Sub-decisions: three codes, closed, in that order — IN FORCE (`carrier_configuration.py:26–28, 33–37` `_CANONICAL_CODE_ORDER`). Order stated over the rendered field name — unverified (`_canonical_order` body not read).
Evidence: source lines (checked); `carrier_configuration.feature:54, 270` cite it (checked); `5d37a4f` exists, 2026-08-22 (checked, git).
Live citations: 4

### A047 — Carried requirements — decided, not yet built — line 803
Head: - **A key in a carrier's entry that is not one of the six values is out of
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — the scoping decision. The question it scopes out (what a loader does with an unknown key) is STILL OPEN: no entry answers it and the loader has no branch for it (grep of `carrier_configuration.py` and `rules.py` for unknown/extra keys is empty).
Evidence: grep (checked); the surviving-mutant approval it says needs "something to point at": unverified against `gauntlet.lock.json`.
Live citations: 0

### A048 — Carried requirements — decided, not yet built — line 814
Head: - **A day count of zero is a valid configuration, not a malformed one -
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `carrier_configuration.py:44–45` `_is_valid_day_count` accepts `value >= 0` (checked); `carrier_configuration.feature` at be87d38 scenario "A day count of zero is accepted for every value that measures one" (checked, title list).
Live citations: 2

### A049 — Carried requirements — decided, not yet built — line 823
Head: - **Example prefix sets use `HO` and `DP`, never `AU` - advisor-recommended, human-ratified,
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): RETIRED — the prefix set itself was retired at item 7d (`2e8ba71`, 2026-09-06; A057 decision 1), so no example prefix set exists to use `HO`/`DP`. No `AU` remains in `features/`.
Evidence: grep of `features/*.feature` for `"AU`/`AU-` empty (checked); A057 (checked).
Live citations: 0

### A050 — Carried requirements — decided, not yet built — line 831
Head: - **The per-carrier rules file is TOML, keyed by `carrier_code`, with one placeholder carrier —
Dates: 2026-08-22 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): STILL OPEN — as a decision it stands unamended, but nothing in the tree reads TOML: the string `toml` occurs nowhere under `src/` or `tests/`, and `rules.py:109–115` takes `rules_source: Mapping[...]` supplied by the caller. The format decision has no implementation to be in force in. Recorded in part 3.
Evidence: grep of `src`, `tests` for `toml` empty (checked); `src/claimgate/shell/rules.py` lines 109–115 (checked); `carrier_configuration.py:14` cites this entry for the file-not-branch point only (checked).
Live citations: 1

### A051 — Carried requirements — decided, not yet built — line 842
Head: - **Two of the six caller-supplied values legitimately accept an absent state; four do not.**
Dates: 2026-08-22 — recorded.
Provenance: none (recorded from signatures; no tag).
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — two optional thresholds, three required values (not four) since 7d retired the prefix set (A057).
Evidence: `carrier_configuration.py:48–66` `_REQUIRED_FIELDS` (three) and `_OPTIONAL_THRESHOLD_FIELDS` (two) (checked); `carrier_configuration.feature` at be87d38 scenario "A recognized carrier's rules load with neither SIU threshold configured" (checked, title list).
Live citations: 0

### A052 — Carried requirements — decided, not yet built — line 852
Head: - **Phase 3 designs the policy administration adapter against three named exemplar system shapes
Dates: 2026-09-01 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — two implementations shipped: live-query (7e) and extract (7i).
Evidence: `src/claimgate/shell/live_query_ports.py`, `extract_ports.py` (checked, function index); ROADMAP.md:114 "Why phase 3 ships two implementations" (checked, grep); A058, A065 (checked).
Live citations: 0

### A053 — Carried requirements — decided, not yet built — line 861
Head: - **Coverage verification at intake is clerical, and it is not coverage determination —
Dates: 2026-09-01 — ratified as the recommendation to carry into PHASE3_DESIGN.md. 2026-06-01 — example date.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — the four consequences were ratified and built at 7a/7f: the term is cited (`coverage_verification.feature` rule "The determination cites the deciding term"); a boundary day is a third value (`BOUNDARY_DAY`, A061 decision 10); `as_of` is stored (`coverage_verifications.py`); search not fetch (`policy_match.feature`); the outcome split is A060/A061 (unmatched pends, out-of-force triages).
Evidence: spec rule and scenario titles at be87d38 (checked, title list); A060, A061 (checked); ROADMAP.md:97–99 (checked).
Live citations: 1

### A054 — Carried requirements — decided, not yet built — line 889
Head: - **Policy identification leaves the domain: `POLICY_NUMBER_MALFORMED` and
Dates: 2026-08-17 — the entry it cites; ratified with PHASE3_DESIGN.md (2026-09-01, undated in the entry).
Provenance: advisor-recommended, human-ratified ("ratified with PHASE3_DESIGN.md").
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — executed at item 7d (`2e8ba71`, 2026-09-06).
Evidence: grep of `src/` for both symbols finds only two retrospective comments (checked); A057 (checked).
Live citations: 0

### A055 — Carried requirements — decided, not yet built — line 895
Head: - **Identifier sufficiency: decisions taken before the spec was locked — advisor-recommended,
Dates: 2026-09-05 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED
Sub-decisions: (1)–(3), (6) — IN FORCE (`policy_identification.feature` scenarios "A policy number pasted with surrounding whitespace", "Anything less is insufficient, and the blocker names what is absent", "A nine-digit postal code is carried as given, not reshaped"). (4) unwired, no `RULESET_VERSION` bump — SUPERSEDED at 7g (A062: wired; `RULESET_VERSION` moved at 7d, 7f, 7h). (5) `policy_number` required until 7g — RETIRED at 7g (A062 decision 3; `validation.feature` rule "A policy number need not be stated...").
Evidence: spec titles at be87d38 (checked); `domain/policy_identification.py:5` cites the entry (checked); `docs/harness-findings.md:1147–1148` carries the nine-digit accommodation (checked).
Live citations: 1 resolved (harness-findings 1148, by content) + 1 ambiguous (`policy_identification.py:5`, "2026-09-05 identifier-sufficiency entry" fits A055 and A056)

### A056 — Carried requirements — decided, not yet built — line 913
Head: - **Identifier-sufficiency judgments beyond the locked spec — agent-proposed, advisor-reviewed,
Dates: 2026-09-05 — ratified; implementation at `60ef615`, `e75f5dd`, `652c2f1`.
Provenance: advisor-recommended, human-ratified (the entry's tag is "agent-proposed, advisor-reviewed, human-ratified"; a third form, flagged in part 3).
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — (3) serialization onto a notice was 7g's decision and is now A062 decision 1 (comma-joined fields, one blocker); (4) the rule takes three identifiers and 7g passes them from the merged view — IN FORCE.
Evidence: the three commits exist, dated 2026-09-05 (checked, git); `policy_identification.py:117` `identification_blockers` docstring cites 7g decision 1 (checked); phase-3.md status paragraph 2026-09-05 "item 7c is closed" (checked, heading list only).
Live citations: 0 resolved; 1 ambiguous (shared with A055)

### A057 — Carried requirements — decided, not yet built — line 935
Head: - **Item 7d decisions, taken before the specs were re-locked — advisor-recommended, human-ratified
Dates: 2026-09-05 — ratified; 2026-09-06 — corrected: seven specs, not five.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED
Sub-decisions: (1) retirement — IN FORCE. (2) `policy_number` required until 7g — RETIRED at 7g (A062 decision 3). (3) interplay rule on four codes — IN FORCE (`validation.feature` rule "All blockers are reported together, in canonical order..."). (4), (5) — unverified against the locked rows. (6) `RULESET_VERSION` bump — done at `e62cdd6` (2026-09-06), since moved to `2026-09-09` (A064).
Evidence: `e62cdd6`, `fb47d43`, `2e8ba71` dates (checked, git); `ruleset.py:21` (checked); spec rule title (checked).
Live citations: 0

### A058 — Carried requirements — decided, not yet built — line 951
Head: - **Item 7e decisions — advisor-recommended, human-ratified 2026-09-06.** (1) Port answers are shell
Dates: 2026-09-06 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — (5) "no endpoint answers `PORT_BINDING_UNRESOLVABLE` until 7f" — done at 7f (A061 decision 7); (1) "killed count staying at 687" is a dated measurement (757 at prototype-1 per QUEUE.md).
Evidence: `src/claimgate/shell/ports.py:50–58` reason and status constants (checked); `bindings.py:53–57` `COMPLETE_HISTORY`, `_POLICY_KEYS` with `history_horizon` (checked); `faults.py:27` (checked); `ce104ea`, `b846768` dates (checked, git).
Live citations: 1

### A059 — Carried requirements — decided, not yet built — line 975
Head: - **The continuous-coverage derivation is a domain rule, not port logic — advisor-recommended,
Dates: 2026-08-14 — the entry it amends; ratified with PHASE3_DESIGN.md (2026-09-01).
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — built at 7b.
Evidence: `src/claimgate/domain/continuous_coverage.py` `derive_continuous_coverage` (checked, function index and lines 29–32); `continuous_coverage.feature` at be87d38 (checked, title list); A087's 2026-09-01 location amendment (checked).
Live citations: 0

### A060 — Carried requirements — decided, not yet built — line 981
Head: - **A port fault lands `TRIAGED` with verification `NOT_EVALUATED`; it does not pend —
Dates: none in the entry (ratified with PHASE3_DESIGN.md, 2026-09-01).
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `policy_match.feature` at be87d38 rule "A source fault proceeds with the verification marked not evaluated, and its reason" and scenario "A fault on the policy source is not the reporter's problem" (checked, title list); `src/claimgate/domain/policy_match.py:11` cites it (checked).
Live citations: 1

### A061 — Carried requirements — decided, not yet built — line 986
Head: - **Item 7f spec decisions — advisor-recommended, human-ratified 2026-09-07.** (1) The intake
Dates: 2026-09-07 — ratified (all eleven).
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED
Sub-decisions: (1)–(5), (7), (9)–(11) — IN FORCE. (6) unmatched/ambiguous persist through resolution — AMENDED by A062 decision 6 (7g re-searches; an answer decides afresh). (8) insured-name search unreachable until 7g — SUPERSEDED at 7g (A062 decision 3, 7).
Evidence: `policy_match.feature` rules at be87d38 ("The search runs on any notice that can be searched...", "A matched notice carries the term verdict, the deciding term, and the instant the answer reflects") (checked, title list); `coverage_verification.feature` citation scenarios (checked, title list); `receipt.py:26`, `coverage_verifications.py:138`, `continuous_coverage.py:139` cite decisions 9, 6, 5 (checked); `a20e06e`, `2ad4055`, `850fe04` dates (checked, git).
Live citations: 5

### A062 — Carried requirements — decided, not yet built — line 1017
Head: - **Item 7g spec decisions — advisor-recommended, human-ratified 2026-09-08.** (1)
Dates: 2026-09-08 — ratified (1–9).
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `validation.py:76–84` canonical order comment for 7g decision 2 (checked); `policy_identification.py:117` (checked); `resolution_evaluation.py:31` "re-search decides afresh only when it answers" (checked); `policy_match.feature` at be87d38 rules "Without a policy number, an insured name and risk postal code find the policy..." and "Correcting identifiers through resolution searches again on the merged notice..." (checked, title list); `validation.feature` scenarios "An absent policy number is not a validation blocker", "A whitespace-only policy number is not a validation blocker" (checked, title list).
Live citations: 6

### A063 — Carried requirements — decided, not yet built — line 1041
Head: - **Item 7h spec decisions — advisor-recommended, human-ratified 2026-09-09.** (1) The intake
Dates: 2026-09-09 — ratified; 2026-08-22 — decision 6 cites A041's date.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `duplicate_evaluation.feature` at be87d38 rules "A triaged notice is compared against the claims on the policy the search found" and "...a pended notice is compared when it is triaged" (checked, title list); `duplicates.feature` digest unchanged in QUEUE.md's list (checked); `tests/fixtures/core_system.py:150`, `tests/api/policy_match.py:24` cite decisions 5 and 11 (checked); `9d41011`, `a1e3e28` dates (checked, git).
Live citations: 3

### A064 — Carried requirements — decided, not yet built — line 1061
Head: - **Item 7h implementation decisions — advisor-recommended, human-ratified 2026-09-09.** (8) The
Dates: 2026-09-09 — ratified (8–11); `RULESET_VERSION` becomes `2026-09-09`.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `src/claimgate/domain/ruleset.py:21` `RULESET_VERSION = "2026-09-09"` (checked); `duplicate_evaluations.py:26–27, 46` `OBTAINED` translation (checked); `coverage_verifications.py:60`, `trails.py:37`, `resolution_evaluation.py:47` cite decisions 8–9 (checked).
Live citations: 5

### A065 — Carried requirements — decided, not yet built — line 1080
Head: - **Item 7i decisions — advisor-recommended, human-ratified 2026-09-10.** (1) The extract shape's
Dates: 2026-09-10 — ratified (1–5); 2026-09-10 — decision (6) ratified after the implementation.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — decision (6)'s closing sentence, "Its implementation is queued as the next item's opening housekeeping", is stale: `be87d38` itself (prototype-1, 2026-09-11) is "7i decision (6): an extract whose history starts later than the binding's horizon...", and `extract_ports.py:134` tests `_holds_less(manifest.history_from, horizon)`. Recorded in part 3.
Evidence: `be87d38` subject line (checked, git); `src/claimgate/shell/extract_ports.py` lines 23–27, 95, 134, 147 (checked); `tests/shell/port_harness.py:10`, `tests/fixtures/core_system.py:78` cite decisions 3 and 4 (checked); `576912e`, `c123151` dates (checked, git).
Live citations: 8

### A066 — Undocumented phase-1 thresholds — line 1107
Head: - **365 (`REPORTING_WINDOW_DAYS`).** Its only rationale was "carriers accept late FNOL" — a
Dates: none.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): RETIRED — the gate is gone ("Now removed"); late notice is non-blocking. Removing commit: unverified (not located by grep of the log this session; A035 attributes the line to item 2).
Evidence: `validation.feature` at be87d38 scenario "A loss reported long after the date of loss is not blocked at intake" (checked, title list); no `REPORTING_WINDOW_DAYS` in the source constant index (checked).
Live citations: 0

### A067 — Undocumented phase-1 thresholds — line 1111
Head: - **30 (`LATE_REPORTING_THRESHOLD_DAYS`).** Not merely unsourced — orphaned. Its rationale defined
Dates: none.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): RETIRED as a constant — item 2 (`9d3fc2d`, 2026-08-10) made the threshold caller-supplied with no default; the replacement value is STILL OPEN (A095).
Evidence: no `LATE_REPORTING_THRESHOLD_DAYS` in the source constant index (checked); `siu_indicators.feature` at be87d38 scenarios "No late reporting threshold configured" and "Late reporting threshold, given an illustrative configured value" (45 days) (checked, title list and line 46); A071, A095 (checked).
Live citations: 0 resolved; 1 ambiguous (`siu_indicators.feature:26`, fits A067 and A071)

### A068 — Undocumented phase-1 thresholds — line 1117
Head: - **500 (`THEFT_LOW_SEVERITY_THRESHOLD`).** No rationale of any kind; `docs/decisions.md` restates
Dates: 2026-08-13 — decided moot.
Provenance: none (the moot decision inherits A032's bare "decided").
Kind: defect
Status at prototype-1 (be87d38): RETIRED — by A032 (loss amount out of the severity rule), built at item 4c (merge commit unverified this session).
Evidence: no `THEFT_LOW_SEVERITY_THRESHOLD` in the source constant index (checked); `triage.py:5–12` (checked).
Live citations: 0

### A069 — Undocumented phase-1 thresholds — line 1124
Head: - **Not a threshold, recorded beside them because it is the project's other hand-declared value and
Dates: 2026-08-27 — advisor-found, human-ratified; first hit that day (5g and 5h).
Provenance: advisor-recommended, human-ratified ("advisor-found, human-ratified").
Kind: decision (accepted without a code change)
Status at prototype-1 (be87d38): IN FORCE — the label is still a bare date (`2026-09-09`), the tripwire test still asserts ISO format. "Revisit with an edition-plus-revision label before any consumer must make that distinction" — STILL OPEN.
Evidence: `ruleset.py:21` (checked); `tests/unit/test_ruleset.py:8–11` (checked).
Live citations: 0

### A070 — Domain defects found, not yet fixed — line 1142
Head: - **SIU flag overrides queue routing.** An SIU-flagged record is routed to `siu_review` instead of
Dates: 2026-08-09 — resolved by the item 1 merge `7f985e7`.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): FIXED — item 1, `7f985e7`, 2026-08-09.
Evidence: `7f985e7` date and subject (checked, git); `triage.py:6` `_SEVERITY_QUEUES` has no SIU queue (checked); `triage.feature` at be87d38 rule "...SIU indicators are recorded separately and never affect routing" (checked, title list).
Live citations: 0

### A071 — Domain defects found, not yet fixed — line 1153
Head: - **Late reporting fires at 30 days against a one-year statutory notice window** (627.70132(2)).
Dates: 2026-08-10 — partly resolved by the item 2 merge `9d3fc2d`.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): FIXED as to the default (item 2, `9d3fc2d`, 2026-08-10); the legal question STILL OPEN (A095).
Evidence: `9d3fc2d` date (checked, git); `siu.py:56` `_evaluate_late_reporting` takes the threshold as a parameter (checked, function index; A036's signature claim); `siu_indicators.feature` titles (checked).
Live citations: 0 resolved; 2 ambiguous (`siu_indicators.feature:26` with A067; `siu_indicators.feature:154` "QUEUE.md item 2" with A072)

### A072 — Domain defects found, not yet fixed — line 1164
Head: - **`siu_flags.feature` framing** characterizes system output as a fraud conclusion — in the title
Dates: 2026-08-10 — resolved by the item 2 merge `9d3fc2d`.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): FIXED — item 2, `9d3fc2d`, 2026-08-10.
Evidence: `features/siu_indicators.feature` exists at be87d38 titled "SIU indicators" (checked, title list); `models.py:85` `SiuIndicatorResult` (checked, function index); no `siu_flags.feature` at be87d38 (checked, file list).
Live citations: 0 resolved; 1 ambiguous (shared with A071)

### A073 — Domain defects found, not yet fixed — line 1173
Head: - **`duplicates.feature` framing and gaps.** States a preventive purpose ("the same loss is not
Dates: 2026-08-12 — resolved by the `reopening/duplicates` merge `0b4e315` (item 3).
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): FIXED — item 3, `0b4e315`, 2026-08-12.
Evidence: `0b4e315` date (checked, git); `duplicates.feature` at be87d38 rules "A candidate match has the same policy, a loss date within 60 days, and the same loss type", "A candidate can match more than one existing claim, returned in ascending claim id order", "Every notice type either gets compared..." (checked, title list); `duplicates.py:14–17` `window_days` parameter (checked).
Live citations: 0

### A074 — Domain defects found, not yet fixed — line 1192
Head: - **Exact `loss_type` equality in the duplicate match key is a false-negative source, and a real
Dates: none.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): STILL OPEN — the match key still requires exact loss-type equality.
Evidence: `src/claimgate/domain/duplicates.py:75` `same_loss_type = candidate.loss_type == claim.loss_type` (checked); `duplicate_evaluation.feature` at be87d38 scenario "A claim of the same loss type is a candidate; one of another type is not" (checked, title list).
Live citations: 0

### A075 — Domain defects found, not yet fixed — line 1199
Head: - **The `duplicates.feature` notice_type exclusion (`QUEUE.md` item 3) guards only the candidate sid
Dates: 2026-08-18 — still open as of.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): STILL OPEN — `ExistingClaim` carries `claim_id`, `policy_number`, `loss_date`, `loss_type` and no notice or coverage type, so the reverse direction is still unguarded; the claims port (7h) did not add one.
Evidence: `src/claimgate/domain/models.py:28–32` (checked); `duplicates.py:38` `_resolve_notice_type_exclusion` reads the candidate only (checked, function index; body unverified).
Live citations: 0

### A076 — Domain defects found, not yet fixed — line 1210
Head: - **Loss type vocabulary, policy number prefixes, and example data across all four feature files
Dates: 2026-08-13 — resolved by `a0983ef` (4a) and `f78ba74` (4b); 2026-08-18 — amended by the item 4j merge `22d672e`.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): FIXED — items 4a and 4b (both 2026-08-13), amended at 4j; the shape it left open closed by retirement at 7d (A097, 2026-09-06).
Sub-decisions: example data — FIXED (4a, 4b). Prefix set — configuration at 4j, then RETIRED at 7d. Number shape — RETIRED at 7d.
Evidence: `a0983ef`, `f78ba74` dated 2026-08-13; `22d672e` git-dated 2026-08-21 while this entry and `docs/queue-history/phases-1-2.md:899` both say 2026-08-18 (checked, git and grep; part 3).
Live citations: 0

### A077 — Domain defects found, not yet fixed — line 1234
Head: - **"injury" is modelled as a peril rather than a Section II liability coverage.** `loss_type` is
Dates: none.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): STILL OPEN — `loss_type` is single-valued and `injury` sits in the recognized set; the open decision is A096.
Evidence: `validation.py:26–49` `RECOGNIZED_LOSS_TYPES`, `_SECTION_II_LOSS_TYPES = {"injury", "liability"}` (checked); `models.py` `Candidate.loss_type` single field (unverified beyond the citation context).
Live citations: 0

### A078 — Domain defects found, not yet fixed — line 1236
Head: - **Loss amount affects severity only for theft.** A $50,000 water loss and a $500 water loss
Dates: none.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): FIXED — by removal, not by extension: A032 (2026-08-13, item 4c) took loss amount out of the severity rule for every peril. The entry's own framing (amount as a severity signal) was rejected, so "fixed" here means the defect no longer exists, not that the entry's implied remedy was adopted.
Evidence: `triage.py` `assign_severity` reads loss type only (checked, lines 5–12); A032 (checked).
Live citations: 0

### A079 — Domain defects found, not yet fixed — line 1239
Head: - **No plausibility floor on loss date.** A loss date of 1850-01-01 flows through as non-blocking
Dates: none.
Provenance: none
Kind: defect
Status at prototype-1 (be87d38): DECIDED — the "principled fix" the entry names (loss date against policy data) exists since 7a/7f as the term-in-force verification, and by A053/A060 an out-of-force answer is an attribute, not a blocker: a loss before any term is `NOT_IN_FORCE` citing nothing and the notice proceeds. No floor was added, by design. This is my reading of A053, A060 and the 7a spec, not a statement any entry makes; flagged as such.
Evidence: `coverage_verification.feature` at be87d38 scenario "A loss before any term began has no term to cite" (checked, title list); `policy_match.feature` scenario "A loss after the only term expired proceeds, not in force, with no coverage date" (checked, title list); A053, A060 (checked).
Live citations: 0

### A080 — Domain defects found, not yet fixed — line 1242
Head: - **`compute_siu_flags` already guards against a policy inception date after the loss date, and
Dates: 2026-08-09 — "RESOLVED by item 2" (recorded 2026-08-15); 2026-08-15 — recorded.
Provenance: none
Kind: defect (code doing something no spec asserts)
Status at prototype-1 (be87d38): FIXED — the scenario exists: `siu_indicators.feature` at be87d38 rule "A continuous coverage date after the loss date does not indicate recent policy inception". Date note: item 2's implementation `33d602b` is 2026-08-09 and its merge `9d3fc2d` is 2026-08-10; the entry's "RESOLVED 2026-08-09" matches the implementation, A071/A072 use the merge date (part 3).
Sub-decisions: the larger question (a loss predating coverage is a coverage problem) — DECIDED at 7a: `coverage_verification.feature` answers it as the term-in-force verification (see A079).
Evidence: spec rule title (checked); `33d602b`, `9d3fc2d` dates (checked, git); `siu.py:74` `_evaluate_recent_inception` (checked, function index).
Live citations: 0

### A081 — Domain defects found, not yet fixed — line 1273
Head: - **The record captures no reporter identity or relationship to the insured.** FNOL on a Florida
Dates: none.
Provenance: none
Kind: data gap
Status at prototype-1 (be87d38): STILL OPEN — `NoticeFields` names no reporter identity or capacity; "represented at FNOL" is not an indicator (A101's candidate list names it as a future candidate needing its own basis, so the rejection here stands as the constraint on that).
Evidence: grep of `src/claimgate/shell/messages.py` for `reporter`/`reported_by` finds prose only (checked); `NoticeFields` field list: unverified.
Live citations: 0

### A082 — Domain defects found, not yet fixed — line 1283
Head: - **Why `test_triage.py::test_every_high_severity_loss_type_is_recognized_by_validation` exists,
Dates: 2026-08-16 — names verified.
Provenance: none
Kind: audit record (rationale for a test)
Status at prototype-1 (be87d38): IN FORCE — the test exists and the two sets it guards are still separate frozensets in separate modules.
Evidence: `tests/unit/test_triage.py:18` (checked); `triage.py:5`, `validation.py:26` (checked).
Live citations: 0

### A083 — Domain defects found, not yet fixed — line 1303
Head: - **An absent loss date is a domain blocker, not a schema refusal — advisor-recommended,
Dates: 2026-08-24 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: defect (with its decided resolution)
Status at prototype-1 (be87d38): FIXED — item 5h, merged `e8e76c0` (2026-08-27); `loss_date` is `date | None` and validation has a presence check.
Evidence: `models.py:17` `loss_date: date | None = None` (checked); `validation.py:164` `_check_loss_date_present` (checked, function index) and line 169 docstring (checked); `validation.feature` at be87d38 scenario "A loss date is stated, absent, or ahead of today" (checked, title list); `e8e76c0` date (checked, git).
Live citations: 5

### A084 — Domain defects found, not yet fixed — line 1321
Head: - **Item 5h, three decisions, advisor-recommended, human-ratified, 2026-08-27.** Taken together at
Dates: 2026-08-27 — (1)–(3) ratified at drafting; 2026-08-27 — (4) ratified post-implementation; 2026-08-30 — (2)'s assertion gap closed by item 5j `806f403`.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Sub-decisions: (1) — IN FORCE (`validation.py:62–67` `NO_JURISDICTION_DATE`, `NO_LOSS_DATE`). (2) — IN FORCE, its scenario landed at 5j (`jurisdiction_selection.feature` at be87d38 scenario "What the future-dated-loss determination records when it evaluates, when the jurisdiction date is missing, and when the loss date is missing too"). (3) — IN FORCE (`siu.py:23` comment; the both-paths premise holds: `shell/siu.py:3` "on every transition into TRIAGED, on both"). (4) — IN FORCE (`duplicates.py:55–67` `_require_loss_date` raises `ValueError`, placed after the notice-type exclusion at line 38–52).
Evidence: source lines (checked); spec title (checked); `806f403` date 2026-08-30 (checked, git).
Live citations: 5

### A085 — Data we do not have at intake — line 1382
Head: **Annotation, 2026-09-01: every reference in this section and elsewhere in this file to "phase 2's
Dates: 2026-09-01 — annotation; 2026-08-30 — phase 2's close; 2026-08-17 — the estate dropped.
Provenance: none
Kind: convention (reading rule for the section)
Status at prototype-1 (be87d38): RECORD ONLY
Evidence: ROADMAP.md, PHASE2_DESIGN.md as it cites: unverified this session beyond A052/A085's own text.
Live citations: 0

### A086 — Data we do not have at intake — line 1389
Head: - **`policy_inception_date` is available at FNOL via a lookup against the policy administration
Dates: 2026-08-13 — decided (availability); 2026-08-13 — decided (original inception, not current term).
Provenance: bare "decided" (unclassified)
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — the date arrives via the port's term history (A059, A087) and is derived in the domain as of the loss date (A089); `compute_siu_indicators` still receives it as a parameter. "Original inception date" became "start of the unbroken run of coverage in force on the loss date".
Evidence: `siu.py:32` `compute_siu_indicators` (checked, function index); `continuous_coverage.py` (checked, lines 29–32); A087, A089 (checked).
Live citations: 1 (ROADMAP.md:94, with A087)

### A087 — Data we do not have at intake — line 1404
Head: - **Decided 2026-08-14: how the adapter derives that date, and what "continuous coverage" means.**
Dates: 2026-08-14 — decided; 2026-09-01 — location amended (domain rule, port supplies history); 2026-09-04 — stated as of the loss date (item 7b).
Provenance: bare "decided" (unclassified) for the 2026-08-14 core; the 2026-09-04 amendment is advisor-recommended, human-ratified.
Kind: decision
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — by its own 2026-09-01 and 2026-09-04 insertions, A059 and A089. "Per-system mechanics for each of the three policy administration systems" — SUPERSEDED by A052 (exemplar shapes, 2026-09-01).
Evidence: `continuous_coverage.feature` at be87d38 rules "An administrative rewrite and a retroactive reinstatement continue coverage; a lapsed reinstatement resets it" and "Coverage assumed from a prior carrier continues if the takeout was seamless" (checked, title list); `continuous_coverage.py:6` cites it (checked).
Live citations: 3

### A088 — Data we do not have at intake — line 1425
Head: - **Term-in-force judgments beyond the locked spec — agent-proposed, advisor-reviewed,
Dates: 2026-09-04 — ratified; locked at `dfb1284` (item 7a).
Provenance: advisor-recommended, human-ratified (entry tag "agent-proposed, advisor-reviewed, human-ratified"; part 3).
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `src/claimgate/domain/term_periods.py:68–92` raises `ValueError` on malformed histories (checked); `coverage.py` `_not_in_force`, `_last_ended`, `_standing_cancellations` (checked, function index); `coverage_verification.feature` at be87d38 scenarios "A loss on the rescinded cancellation date itself", "A not-in-force determination on a cancelled term cites that term and its cancellation" (checked, title list); `dfb1284` dated 2026-09-03 (checked, git).
Live citations: 0

### A089 — Data we do not have at intake — line 1464
Head: - **Continuous-coverage derivation: decisions taken before the spec was locked —
Dates: 2026-09-04 — ratified, and the addendum (a)–(c) ratified the same day; 2026-08-14 — the entry it builds on.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `continuous_coverage.py:29–32` `HISTORY_MAY_PREDATE_SOURCE`, `NO_COVERAGE_ON_LOSS_DATE` closed set (checked); `continuous_coverage.feature` at be87d38 rules "The derivation is as of the loss date...", "A history that may not reach the beginning of the run cannot conclude" and scenarios "The run starts where the source's history starts", "A loss dated before the source's history starts may have been covered by a term it cannot see" (checked, title list); `bindings.py:31` cites it for the required horizon (checked); `c5c9b1c` dated 2026-09-04 (checked, git).
Live citations: 3

### A090 — Data we do not have at intake — line 1509
Head: - **Continuous-coverage judgments beyond the locked spec — agent-proposed, advisor-reviewed,
Dates: 2026-09-05 — ratified; 2026-09-04 — reported in the queue; judgment 5 reversed at `e2a7cc5`.
Provenance: advisor-recommended, human-ratified (entry tag "agent-proposed, advisor-reviewed, human-ratified"; part 3).
Kind: decision
Status at prototype-1 (be87d38): IN FORCE
Evidence: `e2a7cc5` "a zero-day prior-carrier interval is malformed" dated 2026-09-05 (checked, git); `continuous_coverage.py:108` cites judgment 5 (checked); `continuous_coverage.py:107` `_require_prior_coverage_well_formed` (checked, function index).
Live citations: 1

### A091 — Data we do not have at intake — line 1540
Head: - **Consequence, updated for the decision above:** the recent-policy-inception indicator's blocking
Dates: none.
Provenance: none
Kind: decision (consequence)
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — "once the adapter is built, NOT_EVALUATED becomes a genuine exception path" is now the case (7f, A061 decision 5); the late-reporting gap STILL OPEN (A095).
Evidence: `policy_match.feature` at be87d38 scenario "The continuous-coverage date reaches the recent policy inception indicator" (checked, title list); A095 (checked).
Live citations: 0

### A092 — Data we do not have at intake — line 1546
Head: - **The phase-1 SIU tests pass at 100% mutation score against fixture data with no real-world
Dates: none.
Provenance: none
Kind: data gap
Status at prototype-1 (be87d38): STILL OPEN — every input is still fixture data (`tests/fixtures/core_system.py`, `tests/fixtures/extract.py`); no real-world source exists.
Evidence: fixture modules (checked, file list); mutation 100 % at prototype-1 (QUEUE.md status, checked).
Live citations: 0

### A093 — Data we do not have at intake — line 1549
Head: - **Advisor-recommended, human-ratified, 2026-08-15: the SIU reason code `NO_POLICY_INCEPTION_DATE`
Dates: 2026-08-15 — ratified and merged at item 4d `36ae5b3`; 2026-08-18 — entry corrected from "not yet implemented".
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — implemented at 4d. The enumeration has since grown by one (`NO_JURISDICTION_DATE`, A084/5g), so "still the complete set" of two is dated.
Evidence: `siu.py:12–19` three codes (checked); `36ae5b3` dated 2026-08-15 (checked, git).
Live citations: 0

### A094 — Open decisions — line 1566
Head: - **Persistence engine: SQLite via the stdlib `sqlite3` module, decided 2026-08-24,
Dates: 2026-08-24 — ratified.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — decided, despite the section heading. The costs "revisited at phase 3's adapter boundary" — DECIDED: PHASE3_DESIGN.md:306 records the revisit and defers again to phase 5.
Evidence: `schema.py:6, 88, 106` STRICT tables (checked); `store.py:3` (checked); `schema.py:122–126` the UNIQUE constraint (checked); PHASE3_DESIGN.md:306 (checked, citation line).
Live citations: 7

### A095 — Open decisions — line 1584
Head: - **Replacement for the 30-day late-reporting threshold — not being set now.** Setting it quickly
Dates: none.
Provenance: none
Kind: open decision
Status at prototype-1 (be87d38): STILL OPEN — the threshold is caller-supplied, illustrated as 45 days in the spec, and no value is agreed.
Evidence: `siu_indicators.feature` at be87d38 line 46 "the late reporting threshold is 45 days" under the "illustrative configured value" scenario (checked); `carrier_configuration.feature:93–95` comment (checked).
Live citations: 0 (+ `siu_indicators.feature:73, 172`, NO LOCATOR, whose content is this entry)

### A096 — Open decisions — line 1592
Head: - **`loss_type` conflates perils with Section II coverage categories, and the conflation is
Dates: 2026-08-17 — sharpened by 4g; 2026-08-17 — intended direction stated, not built.
Provenance: none for the open question; the 2026-08-17 direction is bare "stated" (unclassified).
Kind: open decision
Status at prototype-1 (be87d38): STILL OPEN — one field still carries both facts. Detail: the entry quotes the high-severity set as `{"injury", "fire"}`; it is `{"injury", "fire", "sinkhole"}` since 4c (part 3).
Evidence: `validation.py:49` `_SECTION_II_LOSS_TYPES = frozenset({"injury", "liability"})`, `validation.py:192` `_check_claimant_fields` (checked); `triage.py:5` (checked); `validation.feature:155` cites it (checked).
Live citations: 1

### A097 — Open decisions — line 1636
Head: - **`POLICY_NUMBER_PATTERN` encodes a carrier fact in the domain layer, and item 4b narrows the
Dates: 2026-08-18 — half-resolved by the 4j merge `22d672e` (git-dated 2026-08-21); 2026-09-06 — closed by item 7d.
Provenance: none for the finding; the closure is A057's advisor-recommended, human-ratified.
Kind: open decision
Status at prototype-1 (be87d38): DECIDED — closed 2026-09-06 by retirement (A057 decision 1, `2e8ba71`); the entry records this itself.
Evidence: grep of `src/` for `POLICY_NUMBER_PATTERN` finds comments only (checked); `2e8ba71` date (checked, git); ROADMAP.md:82 (checked, citation line).
Live citations: 1 resolved (ROADMAP.md:82) + 1 ambiguous (PHASE3_DESIGN.md:243, with A038)

### A098 — Open decisions — line 1680
Head: - **Item 5e's resolution endpoint: five points the design leaves open — escalated 2026-08-25,
Dates: 2026-08-25 — escalated; 2026-08-25 — all five decided, plus (a)–(e) for the implementation; 2026-08-25 — statutes re-verified against flsenate.gov; 2026-08-28 — decision 5's premise measured false, ruling stands (`079a346`).
Provenance: advisor-recommended, human-ratified (for the decisions; the escalation itself has none).
Kind: escalation record, resolved in place into decisions
Status at prototype-1 (be87d38): IN FORCE — the five decisions and (a), (b), (d), (e) are built and specified.
Sub-decisions: 1 (any field) — IN FORCE (`resolution.feature` rule "A reviewer may correct a field the notice already had..."). 2(a) full validation — IN FORCE (`resolution_evaluation.py:18`). 2(b) resolution's own date — IN FORCE (rule "A resolution is judged on the calendar date it arrives, not the one the notice was pended on"). 3 refused data kept — IN FORCE (rule "What a refused resolution supplied is kept, in sequence..."). 4 `USER` stamped, 400 — IN FORCE (`resolution.py:77`). 5 `RECEIVED` gets 409 — IN FORCE, no scenario, by the 2026-08-28 measurement. (a) `pended_at`/`resolved_at` — IN FORCE (`schema.py:86–87`). (b) schema recreates — IN FORCE (unverified beyond `CREATE TABLE IF NOT EXISTS` at `schema.py:122`). (c) within-code blocker order stated nowhere in `validation.feature` — STILL OPEN (`validation.feature` has no "alphabetical" statement; `resolution.feature:493` still asserts `claimant_name` before `incident_description`). (d) 404 — IN FORCE (`resolution.py:20`). (e) unparseable loss date 400 — IN FORCE (`resolution.py:16`).
Evidence: source lines (checked); spec rule titles at be87d38 (checked); `6a7e1fc`, `079a346` dates (checked, git).
Live citations: 9

### A099 — Open decisions — line 1861
Head: - **Item 5i decisions, advisor-recommended, human-ratified, 2026-08-28.** Six escalations raised at
Dates: 2026-08-28 — ratified; 2026-08-24 and 2026-08-25 — the entries it builds on.
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — decided, despite the section heading.
Sub-decisions: 1–5 — IN FORCE (`faults.py:36–37`; `schema.py:117` `error_code`; `notice_intake.feature` scenario "A carrier this deployment cannot configure is receipted, refused as our defect, and creates no notice"; `resolution.feature` rule "A fault in this deployment's own configuration is answered as ours, and the reviewer's attempt leaves no trace"). 6 no `RULESET_VERSION` bump — IN FORCE (codes live in `shell/faults.py`). The two stale `NotImplementedError` messages — FIXED (`resolution.py:44` "No NotImplementedError remains"). A third code, `PORT_BINDING_UNRESOLVABLE`, joined the enumeration at 7e/7f (A058, A061 decision 7), so "closed" now means three.
Evidence: source lines (checked); spec titles at be87d38 (checked).
Live citations: 7

### A100 — Open decisions — line 1932
Head: - **Item 5i implementation shapes — decided at the keyboard, 2026-08-28, none of them a rule.** The
Dates: 2026-08-28 — decided at the keyboard.
Provenance: bare "decided" (unclassified) — implementation shapes, agent-chosen, ratified by the merge.
Kind: decision (implementation shapes, "none of them a rule")
Status at prototype-1 (be87d38): IN FORCE AS AMENDED — shapes 1–5 stand; the closing note that `notice_intake.py` and `resolution.py` sit at the 250-line ceiling is SUPERSEDED: both were split (7f extracted `receipt.py`, 7h split `bundles.py`), and they are 207 and 111 lines at be87d38.
Evidence: `schema.py:117` `error_code TEXT` (checked); `serialization.py:79, 82` `"error"` on both allow-lists (checked); `wc -l` on the two modules and `receipt.py` (checked).
Live citations: 0 (the two `resolution.feature` citations dated 2026-08-28 resolve to A099 by content)

### A101 — Open decisions — line 1986
Head: - **Item 5f, SIU separation — six decisions, advisor-recommended, human-ratified, 2026-08-25.** All
Dates: 2026-08-25 — ratified (1–6).
Provenance: advisor-recommended, human-ratified
Kind: decision
Status at prototype-1 (be87d38): IN FORCE — decided, despite the section heading. The candidate item (further indicators) — STILL OPEN, unqueued.
Evidence: `shell/siu.py:3` cites decision 1; `siu_events.py:13`, `store.py:40` cite decision 3; `tests/api/siu.py:7` cites decision 4 (checked, citation lines); `siu_separation.feature` at be87d38 rules "Nothing is recorded until the notice reaches TRIAGED", "Late reporting is counted from the day the notice was received, not the day it was released", "Nothing about SIU reaches any surface an ordinary reader sees" (checked, title list).
Live citations: 10

### A102 — Open decisions — line 2031
Head: - **Item 5f, one point the six decisions do not cover — escalated 2026-08-25 while drafting
Dates: 2026-08-25 — escalated; 2026-08-25 — decided (`ruleset_version` names the domain rule set).
Provenance: advisor-recommended, human-ratified (for the decision).
Kind: escalation record, resolved in place into a decision
Status at prototype-1 (be87d38): IN FORCE — the label is declared once in `domain/ruleset.py` and copied onto audit entries and SIU events; each event row carries the threshold used.
Evidence: `ruleset.py:5, 21` (checked); `audit.py:32, 50` (checked); `resolution_evaluation.py:196, 201` (checked); `tests/unit/test_ruleset.py:11` (checked); `siu_separation.feature:57` cites it (checked); CLAUDE.md's `RULESET_VERSION` standing constraint (checked).
Live citations: 4

### A103 — Open decisions — line 2081
Head: - **Retention is currently an unapproved default — opened 2026-09-01, decided in phase 5.** The
Dates: 2026-09-01 — opened.
Provenance: none
Kind: open decision
Status at prototype-1 (be87d38): STILL OPEN — ROADMAP.md phase 5 owns it; no deletion path exists (`schema.py` triggers refuse UPDATE/DELETE per `audit.py:11`, `payloads.py:13–14`).
Evidence: ROADMAP.md:153, 166–167 (checked, grep); source comment lines (checked).
Live citations: 0

### A104 — Synthetic data — line 2090
Head: - No real policy numbers, names, addresses, phone numbers, or claim numbers appear anywhere in
Dates: none.
Provenance: none
Kind: convention
Status at prototype-1 (be87d38): IN FORCE — fixture phone numbers are in the 555-01xx range; names are placeholders.
Evidence: `tests/unit/test_validation.py:232–233` `"555-0101"` (checked); `tests/api/policy_match.py:87` "Fabricated (ASSUMPTIONS.md, 'Synthetic data')" (checked); a full sweep of fixtures for real data: unverified.
Live citations: 0 resolved; 1 ambiguous (`tests/api/policy_match.py:87` names the section, A104–A105)

### A105 — Synthetic data — line 2093
Head: - Carrier identity data (names, NAIC codes) is public regulatory information, used because the
Dates: none.
Provenance: none
Kind: assumption
Status at prototype-1 (be87d38): SUPERSEDED — by A038 (2026-08-17): there is no "real, named carrier estate", and the identity reference now holds "Placeholder Carrier A/B/C" with NAIC values 10001–10003 and group 4001, which are not public regulatory data. The first clause is false at be87d38; the second ("everything else is fabricated") still holds. Part 3.
Evidence: `src/claimgate/domain/carrier_identity.py:29–31` (checked); A038 (checked).
Live citations: 0 resolved; 1 ambiguous (shared with A104)

## Part 1 — status counts

Counted by script over each entry's `Status at prototype-1` line (top-level status only; sub-decisions are not counted).

| Status | Count | Entries |
|---|---|---|
| IN FORCE | 55 | A001, A008, A010, A011, A012, A013, A015, A016, A017, A018, A019, A020, A021, A022, A023, A024, A026, A027, A028, A029, A030, A031, A032, A033, A034, A035, A036, A037, A038, A041, A044, A045, A046, A047, A048, A052, A054, A059, A060, A062, A063, A064, A069, A082, A084, A088, A089, A090, A093, A094, A098, A099, A101, A102, A104 |
| IN FORCE AS AMENDED | 16 | A014, A025, A039, A040, A051, A053, A055, A056, A057, A058, A061, A065, A086, A087, A091, A100 |
| SUPERSEDED | 3 | A042, A043, A105 |
| RETIRED | 5 | A009, A049, A066, A067, A068 |
| FIXED | 8 | A070, A071, A072, A073, A076, A078, A080, A083 |
| STILL OPEN | 9 | A050, A074, A075, A077, A081, A092, A095, A096, A103 |
| DECIDED | 2 | A079, A097 |
| RECORD ONLY | 7 | A002, A003, A004, A005, A006, A007, A085 |
| total | 105 | |

## Part 2 — citations

`grep -n ASSUMPTIONS` over src, tests, features, gauntlet.lock.json, .claude, CLAUDE.md, QUEUE.md, ROADMAP.md, PHASE2_DESIGN.md, PHASE3_DESIGN.md, STATUTORY_REGISTER.md, README.md and docs/harness-findings.md at 370a042 (= cleanup/documents HEAD this session): **187 lines**. Step 1's commit was not made (its script is absent), so the count is 187, not 188. The locator column is a verbatim window of the line around the mention, at most 80 characters; where the locator sits on a neighbouring line the classification says so.

| file:line | locator (verbatim window) | resolves to |
|---|---|---|
| src/claimgate/domain/continuous_coverage.py:6 | the run. Ratified semantics: ASSUMPTIONS.md, "Data we do not have at intake | A087 + A089 (names both) |
| src/claimgate/domain/continuous_coverage.py:25 | closed and scoped to one feature; ASSUMPTIONS.md, the | A089 |
| src/claimgate/domain/continuous_coverage.py:108 | , the term rule's own convention (ASSUMPTIONS.md, the | A090 |
| src/claimgate/domain/continuous_coverage.py:139 | (ASSUMPTIONS.md, 7f decision 5).""" | A061 |
| src/claimgate/domain/models.py:12 | # have (ASSUMPTIONS.md, "An absent loss date is a doma | A083 |
| src/claimgate/domain/models.py:42 | - "unevaluated is not negative" (ASSUMPTIONS.md) applies here | A028 |
| src/claimgate/domain/models.py:86 | # "Unevaluated is not negative" (ASSUMPTIONS.md): reason is set only when | A028 |
| src/claimgate/domain/models.py:112 | # negative" (ASSUMPTIONS.md) applies the same way: a result | A028 |
| src/claimgate/domain/models.py:172 | # negative" (ASSUMPTIONS.md) applies here as "a refusal car | A028 |
| src/claimgate/domain/carrier_configuration.py:10 | se domain calls already resolved (ASSUMPTIONS.md, "A carrier | A039 |
| src/claimgate/domain/carrier_configuration.py:14 | - see ASSUMPTIONS.md, "The per-carrier rules file is | A050 |
| src/claimgate/domain/carrier_configuration.py:31 | # _CANONICAL_CODE_ORDER. ASSUMPTIONS.md, "A missing configuration value | A046 |
| src/claimgate/domain/carrier_configuration.py:46 | ass as 1/0. Zero itself is valid (ASSUMPTIONS.md, "A day count of zero | A048 |
| src/claimgate/domain/validation.py:64 | # ratification recorded in ASSUMPTIONS.md's "Item 5h, three decisions" an | A084 |
| src/claimgate/domain/validation.py:84 | earchable notice is not searched (ASSUMPTIONS.md, 7g decision 2). | A062 |
| src/claimgate/domain/validation.py:142 | ICTION_DATE, ratified 2026-08-27 (ASSUMPTIONS.md, "Item 5h, | A084 |
| src/claimgate/domain/validation.py:169 | date is a blocker, not a refusal (ASSUMPTIONS.md, "An | A083 |
| src/claimgate/domain/carrier_identity.py:5 | configuration values (ASSUMPTIONS.md, "A carrier configuration cross | A039 |
| src/claimgate/domain/carrier_identity.py:13 | reference, not the rules file (ASSUMPTIONS.md, "Item 5c's 400 validates | A024 |
| src/claimgate/domain/siu.py:23 | TED reason - ratified 2026-08-27 (ASSUMPTIONS.md, "Item 5h, three | A084 |
| src/claimgate/domain/siu.py:80 | NTINUOUS_COVERAGE_DATE wins - see ASSUMPTIONS.md's carried-requirements | A029 (locator names the section; content resolves it) |
| src/claimgate/domain/jurisdiction.py:29 | **The match is exact** (ASSUMPTIONS.md, "`property_state` is matched e | A018 |
| src/claimgate/domain/jurisdiction.py:62 | # ASSUMPTIONS.md, ratified 2026-08-26). Eastern' | A017 (date fits A017–A020; content resolves it) |
| src/claimgate/domain/ruleset.py:5 | ASSUMPTIONS.md's item 5f ruleset-version decis | A102 |
| src/claimgate/shell/rules.py:4 | ones. That is not a convenience: ASSUMPTIONS.md's item 5e decision | A098 |
| src/claimgate/shell/rules.py:13 | for a resolution (ASSUMPTIONS.md, "One receipt clock, not two", | A013 |
| src/claimgate/shell/rules.py:81 | ED_FIELD:loss_date in the domain (ASSUMPTIONS.md, "An absent | A083 |
| src/claimgate/domain/policy_match.py:11 | ause nobody can supply an outage (ASSUMPTIONS.md, the | A060 + A061 (names both) |
| src/claimgate/domain/policy_match.py:63 | ason. identified_on is item 7g's (ASSUMPTIONS.md, | A062 |
| src/claimgate/domain/policy_identification.py:5 | icy_identification.feature and by ASSUMPTIONS.md's 2026-09-05 | AMBIGUOUS: A055, A056 (both are 2026-09-05 identifier-sufficiency entries) |
| src/claimgate/domain/policy_identification.py:20 | , the absent fields comma-joined (ASSUMPTIONS.md, 7g | A062 |
| src/claimgate/domain/policy_identification.py:117 | blocker joins the notice's list (ASSUMPTIONS.md, 7g decision 1): | A062 |
| src/claimgate/shell/coverage_verifications.py:60 | # match is MATCHED (ASSUMPTIONS.md, 7h decision 9). Carried so dup | A064 |
| src/claimgate/shell/coverage_verifications.py:138 | path to re-assert unchanged (ASSUMPTIONS.md, 7f decision 6).""" | A061 |
| src/claimgate/shell/schema.py:6 | schema-declared constraints, per ASSUMPTIONS.md's | A094 |
| src/claimgate/shell/schema.py:33 | d_records.error_code` is item 5i (ASSUMPTIONS.md, "Item 5i decisions", | A099 |
| src/claimgate/shell/schema.py:56 | (ASSUMPTIONS.md): the two ends of the interval | A098 (locator 'item 5e decision (a)' is on line 55) |
| src/claimgate/shell/trails.py:20 | for the reason ASSUMPTIONS.md's item 5f decision 3 gives: "un | A101 |
| src/claimgate/shell/trails.py:37 | s (`OBTAINED` or `NOT_EVALUATED`, ASSUMPTIONS.md 7h decision 8), the | A064 |
| src/claimgate/shell/bundles.py:63 | tever an earlier arrival gave it (ASSUMPTIONS.md item 5e decision 1: | A098 |
| src/claimgate/shell/bundles.py:104 | transaction resolved (ASSUMPTIONS.md, item 5f decision 6) and read i | A101 |
| src/claimgate/shell/resolution_evaluation.py:22 | 5g; ASSUMPTIONS.md 2026-08-26), and the late-repor | A019 |
| src/claimgate/shell/resolution_evaluation.py:27 | resolution that moves the notice (ASSUMPTIONS.md, "One receipt clock, not | A013 |
| src/claimgate/shell/resolution_evaluation.py:31 | es afresh only when it answers** (ASSUMPTIONS.md, 7g | A062 |
| src/claimgate/shell/resolution_evaluation.py:47 | (ASSUMPTIONS.md, 7h decision 9) - and its row i | A064 |
| src/claimgate/shell/records.py:128 | """The recipe ASSUMPTIONS.md records under "The payload refe | A026 |
| src/claimgate/shell/records.py:219 | nt the interval was counted from (ASSUMPTIONS.md, item | A101 |
| src/claimgate/shell/extract_source.py:18 | disagreeing is an open decision (ASSUMPTIONS.md, 7i), not a rule here. | A065 (7i; but A065 records no searchable_by question — part 3) |
| src/claimgate/shell/extract_source.py:39 | UNAVAILABLE as for a live source (ASSUMPTIONS.md, 7e | A058 |
| src/claimgate/shell/faults.py:4 | Shell vocabulary, deliberately (ASSUMPTIONS.md, "Item 5i decisions", ruling 6) | A099 |
| src/claimgate/shell/receipt.py:3 | **Order on the way in** (ASSUMPTIONS.md, "Idempotency: what a repeated | A027 |
| src/claimgate/shell/receipt.py:26 | clock is the submission instant (ASSUMPTIONS.md, 7f decision 9), so | A061 |
| src/claimgate/shell/audit.py:20 | es the domain rule set's label** (ASSUMPTIONS.md, item 5f's | A102 |
| src/claimgate/shell/extract_ports.py:21 | is. That is a judgment (ASSUMPTIONS.md, 7i), recorded rather than assu | A065 |
| src/claimgate/shell/extract_ports.py:23 | horizon against the binding's** (ASSUMPTIONS.md, 7i decision | A065 |
| src/claimgate/shell/siu.py:3 | an a branch inside each endpoint. ASSUMPTIONS.md's item | A101 |
| src/claimgate/shell/siu.py:23 | but not one timezone** (item 5g, ASSUMPTIONS.md 2026-08-26). | A019 |
| src/claimgate/shell/resolution.py:4 | ASSUMPTIONS.md's five item 5e decisions, ratif | A098 |
| src/claimgate/shell/bindings.py:31 | history_from (None for complete). ASSUMPTIONS.md's | A089 |
| src/claimgate/shell/store.py:3 | Engine decided 2026-08-24, ASSUMPTIONS.md "Persistence engine": stdlib sq | A094 |
| src/claimgate/shell/store.py:25 | call. See ASSUMPTIONS.md, "One receipt clock, not two", | A013 |
| src/claimgate/shell/store.py:40 | (ASSUMPTIONS.md, item 5f decision 3); tests/she | A101 |
| src/claimgate/shell/resolution_reading.py:29 | (ASSUMPTIONS.md, 7g decision 6), and the judgem | A062 |
| src/claimgate/shell/resolution_reading.py:75 | as false and no scenario is owed (ASSUMPTIONS.md, item 5i, ruling | A099 |
| src/claimgate/shell/notice_intake.py:14 | the caller supplied (ASSUMPTIONS.md, "One receipt clock, not two", | A013 |
| tests/fixtures/extract.py:9 | ASSUMPTIONS.md decision 4). | A065 ('item 7i' is on line 8) |
| src/claimgate/shell/siu_events.py:13 | (ASSUMPTIONS.md, item 5f decision 3). A trail o | A101 |
| src/claimgate/shell/duplicate_evaluations.py:5 | e detection gets its caller", and ASSUMPTIONS.md's | A063 + A064 ('two 7h entries') |
| src/claimgate/shell/duplicate_evaluations.py:86 | its reason cannot be read apart (ASSUMPTIONS.md 2026-08-22).""" | A041 |
| src/claimgate/shell/ports.py:30 | the shell itself reads none (ASSUMPTIONS.md, "One receipt clock, not two"). | A013 |
| tests/unit/test_ruleset.py:11 | # a date over a semantic version (ASSUMPTIONS.md, item 5f's ruleset-version | A102 |
| tests/unit/test_jurisdiction.py:111 | # ASSUMPTIONS.md, ratified 2026-08-26: the match | A018 |
| tests/shell/test_store.py:168 | other half of ASSUMPTIONS.md's item 5f decision 3 - "no code | A101 |
| features/carrier_configuration.feature:32 | rier_code to choose behavior. See ASSUMPTIONS.md, "The per-carrier | A040 |
| features/carrier_configuration.feature:37 | alue never reaches a domain call (ASSUMPTIONS.md, "A | A039 |
| features/carrier_configuration.feature:54 | # means it was onboarded wrongly. ASSUMPTIONS.md, "A missing configuration | A046 |
| features/carrier_configuration.feature:66 | malformed one in the rule below. ASSUMPTIONS.md, "A | A044 |
| features/carrier_configuration.feature:95 | # (ASSUMPTIONS.md), it exists here solely to prov | NO LOCATOR (content: A095) |
| features/carrier_configuration.feature:121 | lain int have no such affordance. ASSUMPTIONS.md says so explicitly: | A036 |
| features/carrier_configuration.feature:144 | is the loading-boundary rejection ASSUMPTIONS.md names as an | A039 |
| features/carrier_configuration.feature:171 | # ASSUMPTIONS.md, "A day count of zero is a vali | A048 |
| features/carrier_configuration.feature:206 | # (ASSUMPTIONS.md, above), so this outline mixes | A046 ('above' points at the file's own line 54 quotation) |
| features/carrier_configuration.feature:270 | # ASSUMPTIONS.md, "A missing configuration value | A046 |
| tests/api/notice_intake.py:19 | serts depends on a file existing (ASSUMPTIONS.md, | A094 |
| tests/acceptance/test_validation_acceptance.py:12 | reaches the domain as a boolean (ASSUMPTIONS.md, "A | A039 |
| gauntlet.lock.json:222 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:228 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:234 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:240 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:246 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:252 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:258 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:264 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:270 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:276 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| gauntlet.lock.json:282 | to demonstrate that independence (ASSUMPTIONS.md, item 4c); these eight survivor | A034 (locator 'item 4c'; content is the loss_amount column entry) |
| tests/shell/conftest.py:12 | with no default (ASSUMPTIONS.md, "Persistence engine"), so a te | A094 |
| tests/shell/test_notice_intake.py:106 | # ASSUMPTIONS.md, "One receipt clock, not two": | A013 |
| tests/shell/test_notice_intake.py:141 | # beside an unparseable one (ASSUMPTIONS.md, "An absent loss date is a | A083 |
| tests/api/siu.py:7 | has. ASSUMPTIONS.md's item 5f decision 4: no route | A101 |
| ROADMAP.md:82 | es to the adapter layer, closing `ASSUMPTIONS.md`'s open decision. | A097 |
| ROADMAP.md:94 | h the semantics already decided (`ASSUMPTIONS.md`, "Data we do | A086 + A087 (names both dates) |
| ROADMAP.md:99 | or's recommendation, recorded in `ASSUMPTIONS.md` dated 2026-09-01, is exactly t | A053 |
| ROADMAP.md:103 | - **Persistence revisited**, as `ASSUMPTIONS.md` scheduled: the adapter call is | A094 |
| ROADMAP.md:209 | `docs/queue-history/` per phase. `ASSUMPTIONS.md` | NO LOCATOR |
| tests/shell/port_harness.py:10 | (ASSUMPTIONS.md, 7i decision 3): the clock's ow | A065 |
| src/claimgate/shell/messages.py:35 | (ASSUMPTIONS.md, 2026-08-26). | A020 |
| tests/shell/test_extract_ports.py:10 | extract's (ASSUMPTIONS.md, 7i). | A065 |
| src/claimgate/shell/__init__.py:6 | "Persistence engine" and ASSUMPTIONS.md's "Timezone-correct 'now'" and | A094 + A014 + A013 (names all three) |
| features/duplicate_evaluation.feature:7 | DESIGN.md, "Existing claims", and ASSUMPTIONS.md 2026-08-22. The | AMBIGUOUS: A041, A042 (both 2026-08-22, both about existing claims; A042 is superseded) |
| src/claimgate/shell/policy_match.py:19 | date, whatever else blocks it** (ASSUMPTIONS.md, 7f decision 4). An injury | A061 |
| tests/shell/test_idempotency.py:35 | # ASSUMPTIONS.md decision 4, as corrected 2026-0 | A027 |
| .claude/skills/repo-edits/SKILL.md:3 | ng a long document like QUEUE.md, ASSUMPTIONS.md, CLAUDE.md, or harness-findings | NO LOCATOR |
| .claude/skills/repo-edits/SKILL.md:14 | scripts/splice.py --file ASSUMPTIONS.md --anchor-file anchor.txt \ | NO LOCATOR |
| features/resolution.feature:38 | d in full, with its reasoning, in ASSUMPTIONS.md's "Open | A098 |
| features/resolution.feature:63 | #      own comment below, and ASSUMPTIONS.md's item 5i entry dated | A099 (ruling 5; A100 shares the date) |
| features/resolution.feature:133 | # ASSUMPTIONS.md, item 5i, 2026-08-28. | A099 (ruling 5; A100 shares the date) |
| features/resolution.feature:278 | # ASSUMPTIONS.md, "Item 5i decisions". The two f | A099 |
| features/resolution.feature:643 | Carried from item 5d, recorded in ASSUMPTIONS.md under "Idempotency: | A027 |
| features/resolution.feature:695 | d for that call, never now(), per ASSUMPTIONS.md's "One | A013 |
| features/jurisdiction_date.feature:13 | # ASSUMPTIONS.md, "The jurisdiction timezone is | A015 |
| features/jurisdiction_date.feature:21 | # ASSUMPTIONS.md, "Timezone-correct 'now.'" | A014 |
| features/jurisdiction_date.feature:42 | # ASSUMPTIONS.md, "Timezone-correct 'now,'" corr | A014 |
| features/jurisdiction_date.feature:90 | ismatch, not a same-outcome swap. ASSUMPTIONS.md, "An | A016 |
| features/jurisdiction_date.feature:113 | # ASSUMPTIONS.md, "Timezone-correct 'now,'" corr | A014 |
| features/siu_indicators.feature:26 | ng threshold has been agreed (see ASSUMPTIONS.md: the 30-day | AMBIGUOUS: A067, A071 (the orphaned 30-day value is told in both) |
| features/siu_indicators.feature:69 | amed for exactly this reason. See ASSUMPTIONS.md's | AMBIGUOUS: section 'Data we do not have at intake' (A085–A093); content fits A087 or A093 |
| features/siu_indicators.feature:73 | ually use for this indicator. See ASSUMPTIONS.md. | NO LOCATOR (content: A095 / A071) |
| features/siu_indicators.feature:93 | # from the reporter (see ASSUMPTIONS.md's "Data we do not have at | AMBIGUOUS: section 'Data we do not have at intake' (A085–A093); content fits A086 or A087 |
| features/siu_indicators.feature:154 | # reopening (ASSUMPTIONS.md, QUEUE.md item 2) - this does n | AMBIGUOUS: A071, A072 (QUEUE.md item 2 resolved both) |
| features/siu_indicators.feature:172 | # (ASSUMPTIONS.md): the late-reporting threshold | NO LOCATOR (content: A095, A091) |
| README.md:72 | ¦ [`ASSUMPTIONS.md`](ASSUMPTIONS.md) ¦ Every unver | NO LOCATOR |
| README.md:75 | ons as originally recorded — see `ASSUMPTIONS.md`'s audit of this file for which | A002 (the 'docs/decisions.md audit' section, A002–A007) |
| tests/unit/test_siu.py:79 | # (ASSUMPTIONS.md) forbids: absence of the requir | A028 (title quoted on line 78) |
| tests/unit/test_siu.py:172 | # Ratified 2026-08-27 (ASSUMPTIONS.md, "Item 5h, three decisions", de | A084 |
| features/siu_separation.feature:31 | # full, with their reasoning, in ASSUMPTIONS.md under "Item 5f, SIU | A101 |
| features/siu_separation.feature:57 | # ASSUMPTIONS.md under "Item 5f, one point the s | A102 |
| features/siu_separation.feature:148 | # stub (ASSUMPTIONS.md, 2026-08-22): the continuous co | A043 |
| features/siu_separation.feature:292 | # ASSUMPTIONS.md implies this and did not state | A013 ('the one-receipt-clock entry', line 291) |
| features/validation.feature:42 | date is a blocker, not a refusal (ASSUMPTIONS.md, "An | A083 |
| features/validation.feature:155 | t does not presume the outcome of ASSUMPTIONS.md's | A096 |
| features/notice_intake.feature:48 | configuration) is still open, per ASSUMPTIONS.md, "The jurisdiction | A015 |
| features/notice_intake.feature:189 | # notice. ASSUMPTIONS.md, "A refused submission is still | A023 |
| features/notice_intake.feature:236 | # Settled by ASSUMPTIONS.md, "Item 5c's 400 validates again | A024 |
| features/notice_intake.feature:278 | # ASSUMPTIONS.md, "Item 5i decisions". What is p | A099 |
| features/notice_intake.feature:279 | # earlier and separately: ASSUMPTIONS.md, "A carrier this deployment | A025 |
| tests/fixtures/core_system.py:78 | (ASSUMPTIONS.md, 7i decision 4).""" | A065 |
| tests/fixtures/core_system.py:150 | 7h, ASSUMPTIONS.md decision 5): a policy the searc | A063 |
| features/continuous_coverage.feature:7 | # Semantics ratified 2026-08-14 (ASSUMPTIONS.md, "Data we do not have at | A087 |
| features/idempotency.feature:31 | # 2026-08-24, recorded in ASSUMPTIONS.md, "Idempotency: what a repeated | A027 |
| features/idempotency.feature:75 | # stale at equality - recorded in ASSUMPTIONS.md. The rows either side | A027 (decision 5, by content; no title on the line) |
| features/idempotency.feature:182 | # reference - the recipe ASSUMPTIONS.md already records under "The | A026 |
| features/idempotency.feature:190 | # 2026-08-24, recorded in ASSUMPTIONS.md. | A027 |
| CLAUDE.md:57 | ach lives in `PHASE2_DESIGN.md`, `ASSUMPTIONS.md`, and | NO LOCATOR |
| CLAUDE.md:160 | `ASSUMPTIONS.md` with provenance and a date. Ha | NO LOCATOR |
| tests/api/policy_match.py:24 | system (ASSUMPTIONS.md, 7h decisions 5 and 11): the cl | A063 + A064 (7h decisions 5 and 11) |
| tests/api/policy_match.py:30 | (ASSUMPTIONS.md, 7i decisions 2 and 4). CLAIMGA | A065 |
| tests/api/policy_match.py:87 | # Fabricated (ASSUMPTIONS.md, "Synthetic data"). | AMBIGUOUS: section 'Synthetic data' (A104, A105) |
| QUEUE.md:32 | C2b. `ASSUMPTIONS.md` becomes an index of the decisi | NO LOCATOR |
| QUEUE.md:67 | ¦ C2b ¦ `ASSUMPTIONS.md` in full; `docs/queue-history/` | NO LOCATOR |
| STATUTORY_REGISTER.md:27 | ss-date field-naming decision in `ASSUMPTIONS.md`. ¦ | UNRESOLVED: no entry carries a 'loss-date field-naming decision' |
| PHASE3_DESIGN.md:106 | (`ASSUMPTIONS.md`, 2026-09-01). This file says " | A012 |
| PHASE3_DESIGN.md:243 | fix. `ASSUMPTIONS.md` already recorded that with no | AMBIGUOUS: A038 (consequence 2), A097 (same sentence) |
| PHASE3_DESIGN.md:259 | ason_codes` (decided 2026-08-22, `ASSUMPTIONS.md`). Evaluated on every transitio | A041 |
| PHASE3_DESIGN.md:306 | ch was the only phase-3 pressure `ASSUMPTIONS.md` named. Revisit again | A094 |
| features/jurisdiction_selection.feature:45 | # ASSUMPTIONS.md's "Timezone-correct 'now'" has | A014 |
| features/jurisdiction_selection.feature:55 | # (ASSUMPTIONS.md, "The jurisdiction timezone is | A015 |
| features/jurisdiction_selection.feature:66 | ceptable for phase 2; recorded in ASSUMPTIONS.md, and no scenario below | A017 (the accepted skew, by content; no title on the line) |
| features/jurisdiction_selection.feature:182 | # outranks NO_JURISDICTION_DATE (ASSUMPTIONS.md, "Item 5h, three | A084 |
| features/jurisdiction_selection.feature:225 | # (ASSUMPTIONS.md, carried requirements): the rea | A029 |
| features/jurisdiction_selection.feature:279 | # ASSUMPTIONS.md, same date: the zone that dates | A019 |
| features/duplicates.feature:72 | # (ASSUMPTIONS.md's "Unevaluated is not negative" | A028 |
| features/duplicates.feature:86 | # system never checked (ASSUMPTIONS.md's "Unevaluated is not negative" | A028 |
| docs/harness-findings.md:1148 | not a domain statement, and `ASSUMPTIONS.md`'s 2026-09-05 identifier-suffic | A055 (the nine-digit accommodation is its point 6) |
| docs/harness-findings.md:1442 | `ASSUMPTIONS.md`, `QUEUE.md`, and this file. No | NO LOCATOR |
| PHASE2_DESIGN.md:53 | e built as unreachable code. See `ASSUMPTIONS.md`, item 5e decision 4. | A098 |
| PHASE2_DESIGN.md:136 | row added 2026-08-25, ratified; `ASSUMPTIONS.md` item 5e decisions 4 and (e) ¦ | A098 |
| PHASE2_DESIGN.md:137 | row added 2026-08-25, ratified; `ASSUMPTIONS.md` item 5e decision (d) ¦ | A098 |
| PHASE2_DESIGN.md:167 | d the 24-hour tie are decided in `ASSUMPTIONS.md`, "Idempotency: what a repeated | A027 |
| PHASE2_DESIGN.md:185 | ed 2026-08-22: they do not — see `ASSUMPTIONS.md`. The question and its reasonin | A041 |
| PHASE2_DESIGN.md:262 | which `ASSUMPTIONS.md`'s "Timezone-correct 'now'" nev | A014 |
| PHASE2_DESIGN.md:291 | ork — see `QUEUE.md` item 5a and `ASSUMPTIONS.md`. Identity and rules remain sep | NO LOCATOR (content: A040) |
| PHASE2_DESIGN.md:401 | **Decided 2026-08-25** (`ASSUMPTIONS.md`, item 5e decisions 1–3): a res | A098 |
| PHASE2_DESIGN.md:462 | rule; see ASSUMPTIONS.md's carried-requirements entry fo | A029 ('carried-requirements entry', the precedence principle) |
| PHASE2_DESIGN.md:480 | configuration under `ASSUMPTIONS.md`, with the late-reporting thres | A040 (the carrier-axis exception, by content) |
| PHASE2_DESIGN.md:497 | **Decided 2026-08-25 (`ASSUMPTIONS.md`, item 5f decisions 1–6):** eva | A101 |
| src/claimgate/shell/idempotency.py:5 | ed 2026-08-24 and are recorded in ASSUMPTIONS.md, | A027 |

### Part 2 — counts

| class | count |
|---|---|
| resolved | 165 |
| NO LOCATOR | 13 |
| UNRESOLVED | 1 |
| AMBIGUOUS | 8 |
| total | 187 |

## Part 3 — what parts 1 and 2 do not carry

- A065 decision (6) says its implementation "is queued as the next item's opening housekeeping"; it was implemented at `be87d38` itself (prototype-1, 2026-09-11, subject "7i decision (6): an extract whose history starts later than the binding's horizon..."), and `src/claimgate/shell/extract_ports.py:134` tests `_holds_less(manifest.history_from, horizon)`. The entry is one commit stale.
- A105 says carrier identity data is "public regulatory information, used because the design targets a real, named carrier estate"; A038 (2026-08-17) dropped the estate, and `src/claimgate/domain/carrier_identity.py:29–31` holds "Placeholder Carrier A/B/C" with NAIC 10001–10003 and group 4001, which are not public data. The first clause is false at be87d38.
- A050 (and A040's "rules file") decide a TOML file; the string `toml` occurs nowhere under `src/` or `tests/`, and `src/claimgate/shell/rules.py:109–115` takes `rules_source: Mapping[...]` from the caller. No file of any format is read.
- A076 and A097 date the item 4j merge `22d672e` at 2026-08-18, agreeing with `docs/queue-history/phases-1-2.md:899`; git dates the commit 2026-08-21T16:38:57Z. The same day's `7da0bd1` (item 4k, cited by A029's correction) and `0114b45` are git-dated 2026-08-21 while the queue history says 2026-08-18. The queue history and git disagree; ASSUMPTIONS follows the queue history.
- A080 says "RESOLVED 2026-08-09 by item 2"; item 2's merge `9d3fc2d` is 2026-08-10 (as A071, A072 and `phases-1-2.md:623` say). 2026-08-09 is the implementation commit `33d602b`, which A080 also names.
- A096 quotes `triage.py`'s high-severity set as `{"injury", "fire"}`; it is `{"injury", "fire", "sinkhole"}` since item 4c (`src/claimgate/domain/triage.py:5`). The 2026-08-17 sharpening did not update the quotation.
- A093 says `NO_THRESHOLD_CONFIGURED` and `NO_CONTINUOUS_COVERAGE_DATE` "are still the complete set"; `src/claimgate/domain/siu.py:19` adds `NO_JURISDICTION_DATE` (item 5g, A084 decision 1's sibling), so the SIU enumeration has three members at be87d38.
- A099 ruling 2 ratifies a closed two-code enumeration for deployment faults; `src/claimgate/shell/faults.py:36–38` carries a third, `PORT_BINDING_UNRESOLVABLE` (A058 decision 5, surfaced by A061 decision 7). The addition is recorded, but not as the escalation A099 says adding a code requires.
- A100 closes with `shell/notice_intake.py` and `shell/resolution.py` "at 250 of 250"; at be87d38 they are 207 and 111 lines, after 7f extracted `receipt.py` and 7h split `bundles.py`.
- A009 says the policy number format is "currently a domain-layer regex"; no regex exists at be87d38 (item 7d, `2e8ba71`, 2026-09-06). A097 records the closure; A009 was not annotated.
- A016 defers the subject-first/subject-last code-name inconsistency to "when item 5a's implementation lands"; 5a landed and `carrier_configuration.py:26–28` still reads `MALFORMED_REQUIRED_CONFIGURATION`, `MISSING_REQUIRED_CONFIGURATION`. No entry records settling it either way.
- A014 defers pinning `tzdata` to "item 5c's deployment work"; 5c closed, `pyproject.toml` names no `tzdata`, and no entry records the settlement.
- A017 says the 49 CFR 71.5(f) verification shares "the same weaker provenance class `STATUTORY_REGISTER.md` states for its hurricane and sinkhole entries"; the register has no `49 CFR` entry at all (grep empty), so the county boundary is recorded only in ASSUMPTIONS.md.
- Provenance tags A001 does not define: A026 "advisor-ratified"; A056, A088, A090 "agent-proposed, advisor-reviewed, human-ratified"; A069 "advisor-found, human-ratified". Part 1 reads all of them as advisor-recommended, human-ratified.
- `STATUTORY_REGISTER.md:27` cites "the loss-date field-naming decision in `ASSUMPTIONS.md`"; no entry carries such a decision (part 2's one UNRESOLVED row).
- `src/claimgate/shell/extract_source.py:18` cites "an open decision (ASSUMPTIONS.md, 7i)" about `searchable_by` disagreeing with the binding; A065 records no such open decision.
- Section headings versus contents at be87d38: "Carried requirements — decided, not yet built" holds 53 entries of which 46 are IN FORCE or IN FORCE AS AMENDED and none is unbuilt except A050; "Domain defects found, not yet fixed" holds 15 of which 8 are FIXED, 1 DECIDED, 1 RETIRED-by-removal (A078), 4 STILL OPEN, 1 IN FORCE (A082); "Open decisions" holds 10 of which 6 are IN FORCE or IN FORCE AS AMENDED, 1 DECIDED, 3 STILL OPEN. For the index, not for this report.

Report digest: sha256 prefix 97bfab7ace3ca78b over this file excluding these last two lines; 1222 lines including them.
