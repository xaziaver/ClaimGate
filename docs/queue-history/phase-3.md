# Work queue history — phase 3

Moved verbatim from `QUEUE.md` on 2026-09-11, clean-up stage C2a, and not to be edited: item 6
(phase 3 planning) through 7i, the reading table as it stood at `prototype-1`, then the status log
from phase 3's opening on 2026-09-01 to the tag. Every present-tense statement is true as of its
paragraph's date; the last paragraph's "is not merged" was overtaken by the merge at `24dd112`. The
live queue is `QUEUE.md`.

---

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

7a. **Term-in-force at the loss date (pure domain rule).** *(Done — see below.)* New spec
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

    **Closed 2026-09-04, merged to `main` at `f1429e6`.** Spec proposed at `dfb1284` — 78
    mutants, 40 sibling swaps, 38 markers, advisor-simulated zero survivors — approved by the human
    at `25ac004`, implemented at `689f285`, one judgment corrected at `89360c2`. The rule made six
    judgments beyond the locked spec: the single-transaction reinstatement shape told apart by
    date; flat cancellations and a cancelled term's nominal expiration not boundary days; a
    malformed history raising, with reason codes port-owned; an empty obtained history
    `NOT_IN_FORCE` citing nothing; input order irrelevant; `NOT_IN_FORCE` citing the latest
    standing cancellation. They are the dated 2026-09-04 entry under "Data we do not have at
    intake" in `ASSUMPTIONS.md`. The advisor re-drove the rule independently, 23/23. Measured out
    of band by applying every mutant with the engine and running the step file: 78/78/0 against
    the simulated zero, 69 unique locators. The one judgment corrected before merge: the
    first-stated tie-break between two terms cancelled the same date made the citation depend on
    input order — the advisor's probe, terms 2026-01-01 to 2027-01-01 and 2026-03-01 to
    2027-03-01 both cancelled 2026-06-01, cited a different term in each order. Two terms in force
    on the same day is now a malformed history that raises in either order, and the tie's residue
    raises too. Final gate at `89360c2`, run cold with `mutants/` cleared first — the warm run had
    reported three false survivors on the new code, the direction `docs/harness-findings.md`
    records: 552/552 tests, coverage 100/100, complexity 6, CRAP 6.0, code mutation 100%/560
    killed, acceptance 12 specs, 76 reviewed-equivalent.

7b. **Continuous-coverage date derivation (pure domain rule).** *(Closed at merge `a56bd18`,
    2026-09-05 — see below: spec `c5c9b1c`, approval `c497312`, implementation `c434fca`, judgment 5
    reversed at `e2a7cc5`.)* New spec `features/continuous_coverage.feature`, then the rule, under
    the 2026-08-14 semantics in `ASSUMPTIONS.md` ("Data we do not have at intake") unchanged:
    continuous coverage on the risk; back-to-back renewals continue it; an administrative rewrite
    continues it; a retroactive reinstatement continues it; a genuine lapse resets it to the date
    coverage resumed. Scenarios on both sides of each clause, including the single-term case and a
    history whose earliest terms predate what the source system can supply (`NOT_EVALUATED`,
    reason). Gives `Candidate.continuous_coverage_date` its first producer — at 7f, not here.
    Amended 2026-09-04 before approval: the derivation is as of the loss date, the history carries
    an optional prior-carrier coverage interval and an optional history horizon, and the two
    domain-owned reasons are `HISTORY_MAY_PREDATE_SOURCE` and `NO_COVERAGE_ON_LOSS_DATE` — the dated
    2026-09-04 continuous-coverage entry in `ASSUMPTIONS.md`.

7c. **Identifier sufficiency and the new notice fields (pure rule + surface fields).** *(Closed at
    merge `c3ecc4e`, 2026-09-05 — see below: spec `d06e236`, approval `6fe269c`, implementation
    `60ef615` / `e75f5dd` / `652c2f1`.)*
    `insured_name`, `risk_address`, `risk_city`, `risk_postal_code` join `NoticeFields`;
    `property_state` stays the address's only state component. Sufficiency rule per
    `PHASE3_DESIGN.md`: searchable = policy number present, or insured name plus risk postal code;
    otherwise blocker `POLICY_IDENTIFIERS_INSUFFICIENT`. Scenarios both sides of each arm, including
    each field present alone. The new fields join the hashed field set: a byte-identical
    resubmission of an old payload under a key remembered before this item answers `409` rather than
    a `200` replay, bounded to the 24-hour key lifetime — item 5g's accepted consequence, accepted
    again here and recorded in this entry when the item closes.
    Does not touch `validation.feature` or `notice_intake.feature`: `policy_number` stays a required
    field until 7g, so the insured-name arm is built and specified here but unreachable at intake
    until then (`PHASE3_DESIGN.md` annotation, 2026-09-05).
    Recorded at close, as this entry said to: a byte-identical resubmission of a pre-7c payload under
    a key remembered before this item answers `409` rather than a `200` replay, bounded to the
    24-hour key lifetime — proven at `e75f5dd`, accepted again (`ASSUMPTIONS.md` 2026-09-05,
    judgment 7).

7d. **Retire policy-number shape validation (reopens `validation.feature`).** *(Closed at merge
    `2e8ba71`, 2026-09-06 — see below: specs `6ebea22` and `fb47d43`, approvals `e78a04f` and `68f9e97`,
    implementation `e62cdd6`, prune `cbbac25`; seven specs reopened, not five.)* Reverses items 4b and
    4j, ratified in `PHASE3_DESIGN.md`, "Identifiers". Delete the prefix scenario; retire
    `POLICY_NUMBER_MALFORMED` from the domain and `recognized_policy_number_prefixes` from the
    required carrier configuration, the rules files, and `carrier_configuration.feature`'s
    required-key rows. Before drafting: measure the full blast radius with the mutation engine
    against the lock at the working ref — the 2026-09-01 floor is 3 approvals deleted with the
    prefix scenario and 28 untouched, and the floor is what to check against, not the answer.
    `POLICY_NOT_MATCHED`, `POLICY_AMBIGUOUS` and the search behaviour are 7f's, not this item's:
    after 7d a policy number is accepted as given and nothing yet checks it against anything.
    Two things for the blast-radius measurement, found 2026-09-05: every combination scenario in
    `validation.feature`'s interplay rule uses `POLICY_NUMBER_MALFORMED` as an ingredient and the
    rule's comments enumerate a five-code closed set, so the radius is scenario text, not only the 3
    approvals; and `policy_number`'s required-ness is not this item's — it is 7g's.
    Measured 2026-09-05 at `e29410e`: five specs reopen, not two — see the `PHASE3_DESIGN.md`
    annotation of that date. `resolution.feature`'s partial-clearance row moves from
    `HO-12`/`POLICY_NUMBER_MALFORMED` to `absent`/`MISSING_REQUIRED_FIELD:policy_number`, because
    with no shape check every policy number in that column is equivalent and two of its kills would
    have become survivors; 7g retargets the row's code. `RULESET_VERSION` bumps: this changes live
    decisions.

7e. **Port protocols, bindings, and the live-query implementations (shell).** *(Closed at merge
    `ce104ea`, 2026-09-07 — implementation `b846768`, judgment-6 reversal `ef751fc`, ratification
    documents `4e08b19`; no spec, no approvals; killed count 687 flat as predicted, 95 tests added.)*
    The policy port
    (`search`, `term_history`) and claims port (`existing_claims`) protocols; three-valued results
    with reason codes and `as_of`, never raising; the per-carrier bindings file with per-binding
    timeout budgets and no defaults; unresolvable binding → deployment fault, new code, item 5i's
    pattern; the live-query implementation of each port against an in-process fixture service,
    timeout and unavailability paths included. Contract suite runs against the protocols so 7i can
    reuse it. The contract suite also asserts that every `term_history` answer states its history
    horizon; an absent horizon means complete, so a port that omits it makes every derivation
    conclusive silently (`ASSUMPTIONS.md`, continuous-coverage decisions, 2026-09-04). No acceptance
    spec: nothing user-visible changes until 7f — say so in the gate report rather than
    manufacturing one. `register_claim` is named in the protocol documentation as phase 6's and is
    not defined.

7f. **Intake wiring, persistence, and the identification outcomes (shell + spec).**
    *(Closed 2026-09-07 — spec `a20e06e`, amendment `2ad4055`, approvals `6cc3e56` and `eb794e4`,
    implementation `69a5f45`, bindings `1e2bfc0`; green run `20260907T214626-43332`, 832 tests, 756
    killed, 73 reviewed-equivalent; merged to `main` at `850fe04`, 2026-09-08.)*
    New spec
    `features/policy_match.feature`, beside 7c's locked rule: the outcome table in `PHASE3_DESIGN.md` —
    matched proceeds; zero candidates pends `POLICY_NOT_MATCHED`; several pend `POLICY_AMBIGUOUS`;
    port `NOT_EVALUATED` triages with the verification attribute carrying the reason; insufficient
    identifiers pend from 7c's rule. Port calls sit between the two transactions, ordered search →
    term history → existing claims → rules; the decision transaction writes decision, SIU events,
    and the new `coverage_verifications` row together. Term-in-force and continuous-coverage results
    become visible attributes on `GET /notices/{id}`; store the deciding term and the `as_of`, never
    the full history. `RULESET_VERSION` bumps here. Scenarios describe outcomes and attributes; none
    names a port, table, or column.

7g. **Resolution path restructured (shell).**
    *(Closed 2026-09-08 — structural `ce62f3d`, spec `acb06eb`, approval `1a24146`, split
    `17de43c`, implementation `828ded3`; green run `20260908T124244-462219`, 858 tests, 757
    killed, 73 reviewed-equivalent; merged to `main` at `7f5f786`, 2026-09-08. Five debts
    carried, listed in the closing status paragraph.)*
    Evaluation moves outside the write transaction: read
    the merged view, evaluate (ports included), write in a second transaction that re-checks
    `PENDED` and answers `409` if the notice moved. `resolution.feature`'s surface is unchanged — a
    re-run of its unmodified scenarios is the evidence; the race guard is unit-tested, and the unit
    test is named in the gate report. Port re-evaluation on resolution uses the merged identifiers,
    so correcting a policy number through resolution is what clears `POLICY_NOT_MATCHED`.
    Also retires `policy_number` as a required field in the same commit that wires
    `POLICY_IDENTIFIERS_INSUFFICIENT`: the two absent/whitespace policy-number scenarios in
    `validation.feature` and the absent-policy-number row in `notice_intake.feature` change to the
    identification blocker, measured against the lock at the working ref before drafting.
    Also decides how a blocker carrying several absent fields serializes onto a notice —
    `POLICY_IDENTIFIERS_INSUFFICIENT` is one code with an ordered field tuple, a shape no existing
    serializer or `reason_codes` convention has (7c judgment 3, `ASSUMPTIONS.md` 2026-09-05).

7h. **Duplicate detection wired (shell).**
    *(Closed 2026-09-10 — housekeeping `6a0d219`, structural `9d41011`, spec `083362e`, approval
    `bf7cbb4`, implementation `a1e3e28`, documents `81e9a68`; green run `20260910T112652-904083`
    at 3169.29 s, 882 tests, 757 killed, 73 reviewed-equivalent, the new spec 46/46; merged to
    `main` at `fc479e3`.)*
    `existing_claims` feeds `find_duplicates` with the
    carrier's `window_days` on every transition into `TRIAGED`, both paths; results persist to
    `duplicate_evaluations` and surface as their own response field, not in `reason_codes`
    (2026-08-22). `duplicates.feature` is not edited. The first evidence the locked spec describes
    the product rather than the test API: say what the surviving-mutant picture looked like before
    and after in the gate report. `duplicates.feature`'s surviving-mutant picture is identical
    before and after (decision 1: it binds to the domain and never submits a notice).

7i. **Extract-shape implementations and the swappability proof.**
    *(Closed 2026-09-10 — spec `c123151`, approval `7b02204`, implementation `576912e`, documents
    `3e2610c`; green run `20260910T212538-1548345` at 3404.662 s, 963 tests, 757 killed, 73
    reviewed-equivalent, the reopened spec 112/112; merged to `main` at `24dd112`. Judgment 8 is
    decided by decision (6) in `ASSUMPTIONS.md`, its implementation the next item's opening
    housekeeping.)*
    The extract implementation of each
    port — a generated file set with an `as_of` instant; a policy bound after the extract is
    `NOT_FOUND` as of that instant — passing 7e's contract suite unchanged; the acceptance suite
    green under live-query/live-query, extract/extract, and live-policy-beside-extract-claims
    bindings, with no shell change between runs. Any difficulty writing either implementation is
    reported as a finding, not smoothed over (`PHASE2_DESIGN.md`, "Swappability proofs").
    *Amended 2026-09-10 (7i decision 3, `ASSUMPTIONS.md`): "passing 7e's contract suite unchanged"
    does not hold — the suite's three `as_of` assertions compare against the injected clock while
    `ports.py` promises an extract stamps its generation instant, so each harness carries the
    instant its answers reflect and the assertions compare against that.*

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
| 7e–7i | `PHASE3_DESIGN.md` in full; `PHASE2_DESIGN.md` "Record state model" (the two-write receipt paragraph) and "SIU handling"; 7f–7h also `shell/notice_intake.py` and `shell/resolution.py` as they stand at the item's start |
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

## Status log, from phase 3's opening to the tag

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
Branch `phase3/7a-term-in-force` off `main` at `2b35dd7`, spec commit `dfb1284`, pushed;
anything above it on the branch is a merge of `main` and nothing else. One commit of substance:
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

**2026-09-03, later: item 7a is implemented on `phase3/7a-term-in-force` and awaits the human's
review before merge.** The human approved the spec at `25ac004` — lock entry at digest
`b9bcedcb3cfa…`, the spec at `dfb1284` byte for byte. Implementation commit `689f285`:
`src/claimgate/domain/coverage.py` (the rule and the data structures it reads),
`tests/api/coverage.py` (the step-definition surface), the acceptance step file and
`tests/unit/test_coverage.py`. No wiring, no shell change, no `RULESET_VERSION` bump — the rule has
no caller until 7f. Full gate green at `689f285`: 546/546 tests, coverage 100/100, complexity 6,
CRAP 6.0, code mutation 100%/538 killed, acceptance 12 specs and 76 reviewed-equivalent — the same
76 as before this spec, so it added no survivor, and its file in `.gauntlet/mutation-backup/`
carries the run's timestamp, so the gate did mutate it. Measured outside the gate by applying each
mutant with the engine and running the step file: 78 mutants, 78 killed, 0 survivors, 69 unique
locators (nine two-literal step lines share one, the known Gauntlet addressing defect; nothing to
approve on them). The advisor's simulated zero held. **Judgments made in the implementation, for
the human to confirm or reverse before merge — recorded here and deliberately not yet in
`ASSUMPTIONS.md`:** (1) reinstatement is one transaction shape told apart by its date, which is how a
policy administration system records it: a reinstatement dated on its cancellation rescinds it, a
later one leaves a lapse, and the test API's "retroactively as of" refuses a date that is not the
cancellation's rather than quietly recording a lapse. (2) A cancelled term's nominal expiration
date, and the effective date of a term cancelled flat from inception, are not boundary days:
nothing turns on the loss time on a date the term did not run to, the spec's own precedence for a
rescinded date, applied one step further than the spec states. (3) A malformed history raises
`ValueError` rather than resolving NOT_EVALUATED — expiration on or before effective, a status
change dated outside its term, a reinstatement with no cancellation to reinstate (one dated before
its cancellation included), a cancellation on a term already cancelled, two terms both covering
the loss date — because the NOT_EVALUATED reasons are the source's, and a domain-originated code
would be a new enumeration entry, which is the human's decision; whether 7f's adapter maps
inconsistent source data to a port reason is open. (4) Input order of terms and of status changes
is irrelevant, and the cited term is the term as supplied. (5) An obtained history with no terms
is NOT_IN_FORCE citing nothing; a not-obtained history with no reason is an error. (6)
NOT_IN_FORCE cites the latest standing cancellation on or before the loss date and its term — a
cancelled, rewritten, and cancelled-again history cites the second term — and a tie between two
terms cancelled the same date that both hold the loss date, an inconsistent history, cites the
first stated. Next: the human reviews the gate table and the survivor list against the
simulation, then merges; the branch is a superset of `main`.

**2026-09-04: item 7a is closed, merged to `main` at `f1429e6`.** The full gate was green cold
at `89360c2`, the last code commit before the merge; the merge and the two document commits after
it change no file under `src/`, `tests/`, or `features/`. Item 7b is next — the continuous-coverage
date derivation, a pure domain rule under the 2026-08-14 semantics unchanged — and opens in a fresh
session with `features/continuous_coverage.feature` drafted for the human's review before anything
is built. Nothing is in flight in code: no branch, no spec, no red gate.

**2026-09-04, later: item 7b is open; the specification is proposed and awaits the human's approval.**
Branch `phase3/7b-continuous-coverage` off `main` at `de2262f`, spec commit `d5c33ea`, pushed;
anything above it on the branch is a merge of `main` and nothing else. One commit of substance:
`features/continuous_coverage.feature` exactly as the advisor supplied it — 88 lines, sha256
`8a5e71454c47…`, both confirmed from `git show d5c33ea:features/continuous_coverage.feature`, not
from the working tree. Measured through the mutation engine at that ref (agent-gauntlet `9afd421`;
its acceptance module is unchanged since the `aa29c42` 7a measured with): 48 mutants — 4 sibling
swaps, all in the one outline's two `Examples` rows, and 44 markers, every quoted literal in the
eight plain scenarios — over 33 unique locators, because fifteen step lines carry two literals each
(the known Gauntlet addressing defect; nothing is approvable on a marker). Matches the advisor's
48/44/4 exactly. The advisor's zero survivors on the 4 swaps is a simulation against the ratified
rule, re-derived here with the same result, and not a measurement; the 44 markers die at step
resolution conditionally on the two requirements 7a's step definitions already meet — strict date
parsing and exact-string assertions. `gauntlet check` at `d5c33ea`: every gate green (552/552 tests,
coverage 100/100, code mutation 100% from a warm cache on a commit that adds no code) and acceptance
stopped at the approval stage in 0.004s — `1 unapproved or modified spec(s)`, remedy naming
`gauntlet lock`, the known-wrong command; the human's is `gauntlet spec approve`. That red is the
separate-commits rule working, not a defect to retry. Nothing else is built: no domain rule, no step
definitions, no unit tests, no `RULESET_VERSION` bump (no caller until 7f). Three design points for
the implementation session, flagged and deliberately not resolved: (1) the "source supplies history
from" Given implies the term-history input gains a supplied-from date; (2) `HISTORY_MAY_PREDATE_SOURCE`
is a domain-owned reason in a closed enumeration this feature owns, which the spec's other reason,
`SOURCE_UNAVAILABLE`, passes through from the port's enumeration — distinct from 7a's ratified judgment
that inconsistent-source reasons are the port's, because a truncation boundary is well-formed data the
source states truthfully, not a contradiction within the history; (3) a supplied term effective before
the supplied-from date is neither Rule 3 scenario's case, and whether that is malformed (`ValueError`,
7a's judgment 3) or NOT_EVALUATED with a reason is the human's to decide before it is coded. Next: the
human exports at `d5c33ea` and approves — the human's command, never a session's — then
implementation on the same branch.

**2026-09-04, later still: item 7b's spec is amended at `c5c9b1c`; `d5c33ea` is superseded and must
not be approved.** The human reviewed `d5c33ea` with the advisor and found four gaps: the derivation
took no loss date, so a lapse and reinstatement recorded after a late-reported loss would have
derived the reinstatement date; there was no prior-carrier input, so every depopulation policy would
have derived its assumption date; the lapse clause was exercised at one gap width and one gap per
history; and the history horizon was undefined, so a supplied term effective before it had no
answer. The four decisions that close them are the dated 2026-09-04 continuous-coverage entry under
"Data we do not have at intake" in `ASSUMPTIONS.md`, and the 2026-08-14 entry there now carries the
as-of-the-loss-date sentence. The previous paragraph's three design points are resolved in that
entry: the supplied-from date is the history horizon, its absence meaning a complete history (item
7e's contract suite asserts every port states one — recorded in 7e's entry above);
`HISTORY_MAY_PREDATE_SOURCE` and the new `NO_COVERAGE_ON_LOSS_DATE` are domain-owned in a closed
enumeration this feature owns, port reasons passing through as in 7a; and a term effective before
the horizon is well-formed, with the test on the derived date rather than on the earliest supplied
term. Spec commit `c5c9b1c`, one file, pushed; anything above it on the branch is a merge of `main`
and nothing else. `features/continuous_coverage.feature` exactly as supplied — 213 lines, sha256
`dc00a588ea21…`, both confirmed from `git show c5c9b1c:features/continuous_coverage.feature`, not
from the working tree. Measured through the mutation engine at that ref (agent-gauntlet `9afd421`):
156 mutants, 146 markers, 10 sibling swaps (6 in the Rule 1 outline, 4 in the takeout outline), 110
unique locators — the advisor's floor exactly, 46 step lines carrying two literals each. Each of the
10 swaps re-derived against the rule as the spec states it: 0 survivors, a simulation like the
advisor's, not a measurement. `gauntlet check` at `c5c9b1c`: every gate green (552/552 tests,
coverage 100/100, code mutation 100% warm on a commit adding no code) and acceptance red at the
approval stage in 0.004s on the one unapproved spec, remedy naming `gauntlet lock`, the known-wrong
command — the separate-commits rule working, not a defect to retry. Nothing else is built: no domain
rule, no step definitions, no unit tests. `docs/session-prompts/ADVISOR.md` carried an uncommitted
working-tree modification this session did not make; it was left untouched and is in no commit.
Next: the human exports at `c5c9b1c` and approves — `gauntlet spec approve`, the human's command,
never a session's — then implementation on the same branch.

**2026-09-04, evening: item 7b is implemented on `phase3/7b-continuous-coverage` and awaits the
human's review before merge.** The human approved the amended spec at `c5c9b1c` — lock entry at
digest `dc00a588ea21…`, approval commit `c497312`, `gauntlet.lock.json` only. Implementation commit
`c434fca`: `src/claimgate/domain/continuous_coverage.py` (the rule and its result type, a sibling of
`coverage.py`, which stands at 249 of the size gate's 250 lines once the history gains its horizon
and prior-carrier interval), `coverage.py` extended with those two optional fields and a public
in-force-periods reader with the term-in-force rule unchanged, `tests/api/coverage.py`, a new step
file, the five term-history Givens both locked specs state word for word moved to
`tests/acceptance/conftest.py`, and unit tests in `tests/unit/test_continuous_coverage.py` plus
additions to `test_coverage.py` holding a stated prior interval to never being in force. The three
cases decided beyond the spec are coded and recorded as the dated addendum to the 2026-09-04
continuous-coverage entry in `ASSUMPTIONS.md`. No wiring, no shell change, no `RULESET_VERSION` bump
— no caller until 7f. Full gate cold at `c434fca`, `mutants/` cleared first: every gate green —
657/657 tests, coverage 100/100, complexity 6, CRAP 6.0, duplication 0, code mutation 100% with 643
killed (560 before this item; the rise is the new rule's own mutants), acceptance 13 specs and 76
reviewed-equivalent in 1741s — the same 76 as before this spec, so it added no survivor. Measured
outside the gate by applying each of the spec's 156 mutants with the engine and running the step
file: 156 applied, 156 killed, 0 survivors, 110 unique locators, the spec restored to its locked
digest — the advisor's simulated zero held. **Judgments made in the implementation beyond the locked
spec and the three ratified cases, for the human to confirm or reverse before merge — recorded here
and deliberately not yet in `ASSUMPTIONS.md`:** (1) the result is `DERIVED` with the date or
`NOT_EVALUATED` with a reason, nothing else recorded. (2) "Reaches" is measured against the day the
run began: the first own term's effective date, except for a run opened by a lapsed reinstatement,
where it is the reinstatement date. (3) A prior interval beginning after the run did cannot move the
date later; the derived date is the earlier of the two starts. (4) A prior interval extends
whichever run holds the loss date, a later run across a gap in own terms included when the interval
ends on or after that run began — the prior carrier covered the gap; one ending inside an earlier
run does not reach. (5) A prior interval is malformed only when it ends strictly before it takes
effect, the instruction's "before"; a zero-day interval is accepted and changes nothing, one step
short of the term rule's "on or before". (6) A loss dated inside the prior interval and before any
own term is `NO_COVERAGE_ON_LOSS_DATE`: the interval extends a run, it is not one. (7) A malformed
prior interval raises for any loss date on an obtained history, as malformed terms do; on a
not-obtained history it is ignored and the source's reason is the answer, and a not-obtained history
with no reason is an error. (8) An obtained history with no terms holds no date:
`NO_COVERAGE_ON_LOSS_DATE`, or `HISTORY_MAY_PREDATE_SOURCE` when the loss is on or before a stated
horizon. (9) A stated prior interval may reach back before the horizon once the own run's start
passes the horizon test — a data point the source states, not a term that might be missing. (10) A
loss covered by a supplied term from before the horizon takes the run-start test,
`HISTORY_MAY_PREDATE_SOURCE`, not the uncovered one. (11) Input order of terms and of status changes
is irrelevant. `docs/session-prompts/ADVISOR.md` still carries the human's uncommitted working-tree
modification, untouched and in no commit. Next: the human reviews the gate table, the kill figure
and the judgments, then merges; the branch is a superset of `main`.

**2026-09-05: item 7b is closed, merged to `main` at `a56bd18`.** The human ratified judgments 1–4
and 6–11 as reported in the paragraph above and reversed 5: a prior-carrier interval ending on the
day it takes effect is malformed, matching the term rule's on-or-before convention, where the first
cut had accepted it on a literal reading of the instruction's "before". Reversed at `e2a7cc5` on the
branch — the comparison, the error text, and the unit test that held a zero-day interval as accepted
now holds it as raising; no other test asserted the old behaviour. The eleven judgments are recorded
in `ASSUMPTIONS.md` under "Data we do not have at intake", dated 2026-09-05; the 2026-09-04
paragraph above stays as the record of when they were reported. Full gate green cold at `e2a7cc5`,
`mutants/` and `.mutmut-cache` cleared first: every gate green — 656/656 tests, coverage 100/100,
complexity 6, CRAP 6.0, duplication 0, code mutation 100% with 643 killed, acceptance 13 specs and
76 reviewed-equivalent in 1705s, the same 76 as before. The out-of-band kill figure was not re-run:
neither the spec nor the step file changed after it was measured at 156 applied, 156 killed. Refs:
spec `c5c9b1c`, approval `c497312`, implementation `c434fca`, judgment 5 `e2a7cc5`, merge `a56bd18`;
the merge and the document commits around it change no file under `src/`, `tests/`, or `features/`.
Session start found `features/validation.feature` carrying a `_gauntlet` marker from a stop-check
killed inside the acceptance gate after the previous session's last turn; restored from the mutation
backup, digest confirmed against the lock — the routine case `CLAUDE.md`'s start-up names.
`docs/session-prompts/ADVISOR.md`'s uncommitted working-tree change remains the human's, untouched
and in no commit. Item 7c is next — identifier sufficiency and the new notice fields — with its
reading-table row unchanged. Nothing is in flight in code: no work open on any branch, no red gate.

**2026-09-05: item 7c opened on `phase3/7c-identifier-sufficiency`; spec drafted, not locked.** Spec
commit `d06e236` adds `features/policy_identification.feature`, 102 lines, sha256
`a504421e2c3ef5ed98074fe9e1a87d6e075b1ee1bbeec06eea6942d1f969782a` from `git show
d06e236:features/policy_identification.feature`; the branch tip is the merge of `main`'s document
commits, which change no file under `features/`, `src/`, or `tests/`. Enumerated independently
through the engine at agent-gauntlet `9afd421` against the advisor's floor, matching it exactly: 54
mutants, 42 quoted-literal markers across the eight plain scenarios, 12 example mutants all in the
insufficient-case outline — 7 empty-cell markers, 2 sibling swaps to the empty cell (`Marisol
Quintero` and `34287-2210`), 3 blocker-column swaps — and 51 unique locators, because a locator is
scenario, kind and step text, and the three steps carrying both a name and a postal code hold two
literals each. Simulation against the rule as the spec states it, not a measurement: all 12
example mutants die — a marker in an identifier cell makes that identifier present, which either
makes the row searchable or changes which fields the blocker names; each swap to empty makes a
third field absent, so the blocker names three; each blocker swap asserts the wrong field list. The
42 literal markers land outside the quotes and die at step resolution only if every step pattern
is anchored end-to-end: pytest-bdd 8.1.0's `parsers.re` uses `fullmatch`, observed by calling
`is_matching` on a marked step text, so validation-style `"(?P<value>.*)"` patterns reject the
marker without a `$`; a step bound any other way lets its markers through as survivors. Gate on the
branch at `d06e236`: ten gates green — 656/656 tests, coverage 100/100, complexity 6, CRAP 6.0,
duplication 0, code mutation 100% with 643 killed — and acceptance red at the approval stage on the
one unapproved spec, the separate-commits rule working; its remedy names `gauntlet lock`, which is
the human's and does not approve. Design gap, found by reading the design against source:
`policy_number` is a required field in `validation.py`, held by two locked `validation.feature`
scenarios and a `notice_intake.feature` row, so the insured-name arm is unreachable at intake until
the requirement is retired at 7g; recorded in `PHASE3_DESIGN.md`'s 2026-09-05 annotation, the 7c,
7d and 7g entries above, and `ASSUMPTIONS.md`'s carried-requirements entry of the same date, which
also carries the six pre-lock decisions. `docs/harness-findings.md` gains the five-digit postal
code entry: the numeric branch pre-empts the sibling swap, so the outline carries a nine-digit
code. One thing reads wrong and is left for the human: item 7f's entry above says "New spec
`features/policy_identification.feature`" for the five-row outcome table, and that file now exists
as 7c's; 7f either reopens it or its outcome table lives elsewhere, and the entry should say which.
Session start found `features/validation.feature` carrying a `_gauntlet` marker from a killed
stop-check; restored from the mutation backup, digest confirmed against the lock.
`docs/session-prompts/ADVISOR.md`'s uncommitted change remains the human's, untouched and in no
commit. Next action is the human's: export at `d06e236` (`git show
d06e236:features/policy_identification.feature > ~/claimgate-review/d06e236--1 && wc -l`, 102
lines, prefix `a504421e2c3ef5ed`), review, and `gauntlet spec approve`. After approval, in the
implementation session: step definitions, the four `NoticeFields` surface fields, the domain rule,
unit tests, and the idempotency hashed-field consequence the 7c entry records — none begun.

**2026-09-05, later: item 7c is implemented on `phase3/7c-identifier-sufficiency`, green, not
merged.** The human approved the spec at `6fe269c` (lock entry digest `a504421e2c3e…`, the spec at
`d06e236` hashing to it, the commit touching `gauntlet.lock.json` only). Item 7f's entry above now
reads "Reopens 7c's spec" (`3dc7fd7` on `main`, decided with the advisor 2026-09-05: one feature for
one question, measured against the lock at 7f's working ref before drafting). Implementation, three
commits: `60ef615` the rule in `domain/policy_identification.py` with its unit tests, the test API
and the step file binding the spec; `e75f5dd` the four optional fields on the notice surface with
the shell tests; `652c2f1` a restructure of the blocker helper after the first cold gate reported
one surviving code mutant — the policy number passed into the insufficient branch swapped for
`None`, provably equivalent because that branch is reached only with no number — removed rather
than approved, the `key=`-lambda technique in `docs/harness-findings.md`. Cold gate at `652c2f1`,
`mutants/` and `.mutmut-cache` cleared first: every gate green — 691/691 tests (35 new: 11
scenarios, 21 unit, 3 shell), coverage 100/100, complexity 6, CRAP 6.0, duplication 0, code
mutation 100% with 708 killed, acceptance 14 specs and 76 reviewed-equivalent in 1995s, the same 76
as before. Out of band at `652c2f1`, every mutant of the spec applied and the step file run: 54
applied, 54 killed, 0 survivors, 51 locators, 42 literal and 12 example kills, the spec's digest
restored and confirmed — matching the simulation exactly. Every step pattern is `parsers.re` with a
`.*` capture: a `parsers.parse` field needs at least one character, so it cannot read the spec's
`""`, and pytest-bdd fullmatches, so the 42 markers die at resolution; `docs/harness-findings.md`
records the fullmatch (2026-08-23) but not the one-character floor. `RULESET_VERSION` is unchanged:
the rule has no caller until 7g, so no decision changes. Judgments the implementation made beyond
the locked spec, for the human to confirm or reverse, here and not yet in `ASSUMPTIONS.md`: (1)
`None` is absence exactly as `""` and whitespace are — the shell's optional fields arrive as `None`,
the spec states only the other two. (2) An insured name or a postal code beside a policy number
without its partner is not carried to the search — the search identifiers hold `None` for the pair
— as instructed; the spec asserts the absence only where nothing was given. (3) The blocker is one
code and an ordered tuple of absent fields, not one blocker per field and not a string; the
`CODE:field;field` spelling is the step's rendering of the spec's text and is not the
`CODE:field;CODE:field` list three other specs spell with the same characters, so how it
serializes onto a notice's blockers is 7g's open decision. (4) The rule takes the three
identifiers as arguments, not a `Candidate`; `Candidate` and the candidate builder are unchanged,
so the four fields reach no rule through the domain's existing path, and 7g passes them from the
merged view. (5) The rule has no not-evaluated value: an absent identifier is the fact the rule is
about, not a missing input, so a result is `SEARCHABLE` or `INSUFFICIENT` and nothing else. (6)
`risk_address` and `risk_city` are notice content read by no rule — the design's arm is the name
with the postal code — and, like every field, can be supplied at resolution because a resolution's
keys are the surface's field names. (7) The 409 proof stages the pre-7c notice through the store's
own receive-and-remember calls with the old payload shape, because the intake path can no longer
produce that shape; the hashed-field consequence is thereby accepted again, as the 7c entry says,
and the entry itself is amended when the item closes. Session start restored nothing:
`features/validation.feature` showed the live gate's in-place mutation once, mid-run, and was clean
after. `docs/session-prompts/ADVISOR.md`'s uncommitted change remains the human's, untouched and in
no commit. Next: the human confirms or reverses the seven judgments, then merges; the branch is a
superset of `main`.

**2026-09-05: item 7c is closed, merged to `main` at `c3ecc4e`.** The human ratified all seven
judgments as reported in the paragraph above; they are recorded in `ASSUMPTIONS.md` under "Carried
requirements", dated 2026-09-05, with judgment 5 carrying the ratification's addition — a rule whose
subject is absence has no outage to report. The first cold gate at `e75f5dd` reported one surviving
code mutant, the policy number passed into the insufficient branch swapped for `None`, equivalent
because that branch is reached only with no number; restructured out at `652c2f1` rather than
approved, the `key=`-lambda technique. The second cold gate at `652c2f1` was green on every gate,
708 killed; out of band at the same ref, 54 applied, 54 killed, 0 survivors. Refs: spec `d06e236`,
approval `6fe269c`, implementation `60ef615` / `e75f5dd` / `652c2f1`, merge `c3ecc4e`; the merge and
the document commits around it change no file under `src/`, `tests/`, or `features/`.
`docs/harness-findings.md` gains the `parsers.parse` empty-value sentence beside the fullmatch entry.
Session start found `features/validation.feature` carrying a `_gauntlet` marker from a stop-check
killed between turns; restored, digest confirmed against the lock — the routine case.
`docs/session-prompts/ADVISOR.md`'s uncommitted change remains the human's, untouched and in no
commit. Item 7d is next — retiring policy-number shape validation, reopening `validation.feature` —
opening in a fresh session with its blast radius measured against the lock at the working ref before
any drafting, including the interplay-rule scenario text and the five-code comment enumeration the
7d entry now names. Nothing is in flight in code: no work open on any branch, no red gate.

**2026-09-05: item 7d opened; spec drafted on `phase3/7d-retire-policy-number-shape`, not locked,
and the pre-approval suite check failed.** Branch created at `e29410e`. The blast-radius record
landed on `main` at `9c6611e` (the `PHASE3_DESIGN.md` annotation, this entry's 7d note,
`ASSUMPTIONS.md`'s six ratified decisions); the five specs at `6ebea22`, one commit, spec only,
pushed. Digests from `git show 6ebea22:<path>`: `validation.feature` `7d9e727a6bcd2f1c` (441
lines), `carrier_configuration.feature` `49f1f2f04b781739` (303), `notice_intake.feature`
`062d4ee4afed6689` (351), `idempotency.feature` `31d5e828914cd162` (260), `resolution.feature`
`d134439ad7b483cc` (727) — each matching the edit script's printed line exactly. Enumerated through
the engine against the lock at `e29410e` and `6ebea22`: validation 192→165 mutants, locators equal
to mutants at both refs, 3 approvals MISSING and all three on the prefix outline, 28 untouched, 0
MODIFIED; carrier_configuration 84→73 (75→66 locators, the known collisions), both approvals
untouched; resolution 133→133, idempotency 46→46, notice_intake 51→51, every approval untouched;
0 MODIFIED anywhere; five spec approvals MODIFIED. One figure reads wrong and was left as it is:
the annotation on `main` says "37 untouched", but 37 is the five files' mutant-approval total before
the deletion — measured after it, 34 are untouched and the 3 deleted make 37. The suite check the
plan required before the gate did not pass: 113 of 116 scenarios across the five modules fail
against the current code, in three shapes, none of them a spec asserting the wrong behaviour —
`validation`'s run fixture reads the context key the removed Background step set (`KeyError`),
`carrier_configuration`'s steps bind the old "six values" text and have no definition for the
negative-threshold step (`StepDefinitionNotFoundError`), and `notice_intake`, `idempotency` and
`resolution` receive 500 because the carrier-rules loader still requires
`recognized_policy_number_prefixes` and the Background no longer supplies it. The premise that the
five files would pass before the implementation commit does not hold: the step glue and the loader,
not the specs, require the retired configuration, and changing them before the lock would invert
the spec-then-implementation order. `gauntlet check` was not run — the instruction was to stop on a
failing suite — so its outcome is predicted, not measured: the tests gate red on these 113, the
acceptance gate red on five MODIFIED spec approvals and three MISSING mutant approvals, short-
circuiting before mutation. Session start restored `features/validation.feature` from a stop-check
strand (a sibling-cell swap at line 364), digest confirmed against the lock;
`docs/session-prompts/ADVISOR.md`'s uncommitted change remains the human's, untouched and in no
commit. Next is the human's: decide whether the step-glue dependency changes the plan; if not,
export the five files at `6ebea22`, run `gauntlet spec approve` on each and `gauntlet mutant prune
features/validation.feature`, and the implementation commit — step glue, the domain retirement, the
carrier rules files, `RULESET_VERSION` — follows the lock on the branch. The branch is a superset
of `main`.

**2026-09-06: the pre-approval suite instruction was wrong; the human approved the five specs at
`6ebea22`, lock at `e78a04f` on the branch.** The advisor's instruction to run the five amended
specs against the current code before approval was reasoned from the spec text, not from the step
glue: `validation`'s run fixture read the context key the removed Background step set,
`carrier_configuration`'s steps bound the "six values" text, and the carrier-rules loader still
required the retired key — so 113 of 116 scenarios failed for glue reasons, none for a wrong
expectation. One detail of the 2026-09-05 report was inference, not observation: the
negative-threshold step was never unbound — the outline's field-and-value regex already matches
it — so the only unbound step was the "six values" text. The agent stopped rather than changing
glue before the lock, which was correct: a red tests gate between a reopening's spec commit and its
implementation commit is the expected state, not a defect, and is why that state lives on a branch.
`gauntlet mutant prune` was deliberately not run: read from source 2026-09-06, its path has no
baseline check, and with the suite red it would have classified all 31 approvals on
`validation.feature` as stale. Prune happens after this implementation, at a green ref.

**2026-09-06: 7d implementation at `e62cdd6` on `phase3/7d-retire-policy-number-shape`, green on
every gate but two, and stopped on a stop condition — two locked specs beyond the five bind the
retired step.** The retirement is complete in the listed files: `validation.py` keeps presence only
and its canonical order is four codes; `carrier_configuration.py` and `models.py` drop the key and
the loader requires five values; `shell/rules.py` and `tests/shell/support.py` stop passing and
supplying it; `RULESET_VERSION` is `2026-09-06`; the validation, carrier_configuration and conftest
step files and `tests/api/validation.py` follow; the unit tests retire the malformed rows and add
none asserting shape; `ASSUMPTIONS.md` closes the `POLICY_NUMBER_PATTERN` entry with a dated
paragraph pointing at the 7d decisions. Cold gate at `e62cdd6`, `mutants/` cleared first: protect,
static (0 findings), size (worst function 25), complexity 6, boundary (16 step files, 0 direct
imports), coverage 100/100, crap 6.0, duplication 0, code mutation 100% with 687 killed (708
before; the removed code carried the difference) — all green; tests red at 637/667; acceptance red
at its baseline stage, "scenarios failing", so it never reached the ledger and the 3 MISSING
approvals were not observed by the gate. Every failure has one cause: `jurisdiction_selection.feature`
line 76 and `siu_separation.feature` line 104 carry `And "AAAA" recognizes the policy-number
prefixes "HO;DP"` in their Backgrounds, a step whose definition left with the code, and all 30
scenarios in the two files fail at resolution. The advisor's radius missed them because a
Background step produces no mutant — `docs/harness-findings.md` gains the entry. Not touched, and
not bound to a no-op: the instruction says stop. Measured out of band and reverted, digests
confirmed against the lock: with that one line removed from each file the suite is 667 passed, and
the edit moves no locator and no digest (55→55 and 53→53 mutants, all 3 mutant approvals
untouched), so its cost is two file approvals — sha256 `b5adf23b9bc27653` (356 lines) and
`c01c07a3f1ad3c6f` (510 lines) if made exactly so. Out of band at `e62cdd6`, in a worktree, every
mutant of three specs applied through the engine and the step file run: `validation.feature` 165
applied, 137 killed, 28 survivors, all 28 approved and untouched, 0 new, the 3 non-surviving
approvals the deleted prefix outline's; `carrier_configuration.feature` 73 applied, 71 killed, 2
survivors, both approved, 0 new; `resolution.feature` 133 applied, 131 killed, 2 survivors, both
approved, 0 new — each file restored to its locked digest. Exactly the floors. Judgments beyond the
locked specs, for ratification: (1) `tests/shell/test_resolution.py`'s leaves-it-blocked
resolution moved from `HO-12` to a payload that says nothing about the number,
`{"notice_type": "SUPPLEMENTAL"}`, the move the spec's row made; (2) the negative
late-reporting-threshold step needed no new binding — the outline's field-and-value regex already
matched it — so none was added; (3) that step's "an empty set" branch was removed as dead once no
row supplies it; (4) `test_policy_number_format` became `test_policy_number_presence` with the
three presence rows, and the two interplay unit tests use `SUPPLEMENT` where they used the
malformed number; (5) the `ASSUMPTIONS.md` closing paragraph rode the implementation commit on the
branch, as instructed, rather than a document commit on `main`; (6) `README.md` lines 18 and 51
still describe the prefix set as required configuration and were left, being outside the listed
files. Also: the approval commit `e78a04f` carries the human's `ADVISOR.md` update beside the
lock, so "touches only `gauntlet.lock.json`" was read as "no spec, code or test file" and the work
proceeded. Next is the human's: decide the two extra specs — amend both by the one-line removal and
approve, or something else — then `gauntlet mutant prune features/validation.feature` at a green
ref, then merge. Not pruned, not merged. The branch is a superset of `main`.

**2026-09-06: the radius is seven specs, not five; the two missed specs are amended at `fb47d43`,
spec commit alone, awaiting approval.** The human ratified judgments 1–5 of the paragraph above;
`README.md` is the agent's at close-out. `jurisdiction_selection.feature` and
`siu_separation.feature` each lose the one Background line `And "AAAA" recognizes the policy-number
prefixes "HO;DP"` and nothing else: from `git show fb47d43:<path>`, `b5adf23b9bc27653` (356 lines)
and `c01c07a3f1ad3c6f` (510 lines), the digests measured before the edit. Enumerated against the
lock at `e62cdd6` and `fb47d43`: 55 and 53 mutants unchanged (55 and 50 unique locators — the
`siu_separation` collisions recorded under "Mutant counts and locator counts are different
numbers"), all 3 mutant approvals untouched, no signature moved, both spec approvals MODIFIED; the
suite at `fb47d43` is 667 passed. Why the radius was missed twice, and the method that replaces it:
the advisor's repo-wide grep searched the underscore identifiers and missed the hyphenated step
text, and the engine cannot see a Background dependency because a Background step yields no mutant —
so the next reopening measures with a plain-word grep across `features/` plus the engine, never the
engine alone (`docs/harness-findings.md`, "How the harness behaves", the entry of this date, into
which the earlier entry under "Process and technique" is folded). Out-of-band survivors at
`e62cdd6`, as measured: 28 on `validation.feature`, 2 on `carrier_configuration.feature`, 2 on
`resolution.feature`, all approved and untouched, 0 new. What is red, and why it is guaranteed: at
`e62cdd6` the tests gate was red only on the two unbound Background lines, every other gate green;
at `fb47d43` those lines are gone and the suite passes, so what stays red until the human approves
the two files is the acceptance gate at its approval stage, on two MODIFIED file approvals — before
the ledger, so the 3 MISSING entries on `validation.feature` remain unobserved by any gate until
then. Next, in order and all the human's: approve the two files, run the cold gate, prune
`features/validation.feature` at the green ref, merge. The branch is a superset of `main`.

**2026-09-06: item 7d is closed, merged to `main` at `2e8ba71`.** The human approved the two amended
specs at `68f9e97`, ran the cold gate green at that ref — 14 specs, 73 reviewed-equivalent, the 3
stale approvals on `validation.feature` reported — pruned exactly those three at `cbbac25` with the
diff verified, and the gate is fully green at `cbbac25`. Refs: specs `6ebea22` (five files) and
`fb47d43` (two more), approvals `e78a04f` and `68f9e97`, implementation `e62cdd6`, prune `cbbac25`,
merge `2e8ba71`. Close-out on `main` at `a98a5bc`: `README.md` no longer lists the prefix set among the
required configuration values — five, not six — and reads its history as retired; `ASSUMPTIONS.md`'s
7d decisions entry carries the dated seven-spec correction and the reopening method for every
later item. Reviewed-equivalent is 73. `RULESET_VERSION` is `2026-09-06`; every audit entry and SIU
indicator event written from the merge names it. The advisor session ended at this save point.
`docs/session-prompts/ADVISOR.md` is the human's: its last change landed in the human's own commit
`e78a04f`, no agent commit touches it, and the tree was clean at this save point. Item 7e is next —
port protocols, bindings and the live-query implementations — opening in a fresh session, with its
blast radius measured by plain-word grep across `features/` plus the engine before any drafting.
Nothing is in flight in code: no work open on any branch, no red gate.

**2026-09-07: item 7e is closed, merged to `main` at `ce104ea`.** Implementation `b846768`,
judgment-6 reversal `ef751fc`, ratification documents `4e08b19`; no spec, no approvals; killed
count 687 flat as predicted; 95 tests added, 762 passing at the merge. The Stop hook timeout is
raised from 1800 to 3600 in `.claude/settings.json` and re-locked with `gauntlet lock` in the commit
that carries this paragraph — the human's decision, the second raise after 600→1800 on 2026-08-25 —
because a cold green acceptance run measured 2135 s against the 1800 s hook, so every stop-check was
being killed by its own timeout and stranding a spec at every turn end (events 11 and 12 in
`docs/harness-findings.md`; a thirteenth, `validation.feature` from the 16:05:39Z stop-check on the
ratification commit, killed 43 s after entering that file, was restored at this close-out and is
not yet in that log). The full gauntlet runs at the end of the close-out turn under the new budget;
if it completes, the next start-up should read the acceptance gate's duration for that run from
`.gauntlet/events.jsonl` and record it here and in `docs/harness-findings.md` — that figure is
wanted, as the first green stop-check since the raise and the current cost of a turn end. Item 7f
opens in a fresh session. 7f reads `shell/notice_intake.py` and `shell/resolution.py` as they stand,
and both are at 250 lines, the size gate's module ceiling, so 7f cannot add a line to either without
a split — plan the split before the spec is drafted, not after the gate goes red.
`docs/session-prompts/ADVISOR.md` is modified in the working tree; it is the human's and is in no
agent commit. Nothing is in flight in code: no work open on any branch, no red gate.

**2026-09-07, start-up after the 7e close: the stop-check on the close-out commit finished green.**
Run `20260907T064859`, acceptance 1993.92 s against the 3600 s Stop hook budget — the pair the
save-point now records at every close — 14 specs, 73 reviewed-equivalent, 763 tests, killed 687.
`docs/session-prompts/ADVISOR.md` landed in the human's commit `db2970b`; the tree is clean. This
session was housekeeping on `main`, one commit, no item opened: `CLAUDE.md`'s start-up and
save-point rules, a prediction section in the `gauntlet-gates` skill, `repo-edits/scripts/radius.py`,
`ROADMAP.md`'s clean-up stage, and the two findings above logged. 7f is still next and still
opens in a fresh session.

**2026-09-07: item 7f is open on `phase3/7f-intake-wiring`; the pre-spec split is done and green at
`56419cf`, no spec touched.** `shell/receipt.py` (131 lines, seam `receive_or_replay`) takes the
five receipt-transaction functions from `notice_intake.py`, now 127;
`shell/resolution_evaluation.py` (142 lines, seam `evaluate`) takes the five evaluation functions
from `resolution.py`, now 116. All ten moved bodies AST-identical to `main`; the only non-import
change in kept code is the two seam calls. Three test files updated at the call site, nothing
re-exported: `tests/api/resolution.py` and `tests/shell/test_notice_intake.py` for
`merged_view`/`notice_records`, and `tests/shell/test_siu_evaluation.py`, whose
both-paths-share-`siu` assertion now names `resolution_evaluation`. Gate predicted before the run
and matched line for line at run `20260907T115727`: size worst function 25, complexity 6, boundary
16/0, tests 763/763, coverage 100/100, duplication 0, code mutation 100% with 687 killed (flat — a
move leaks nothing into scope), acceptance 14 specs, 73 reviewed-equivalent, digests unchanged,
1630.582 s against the 3600 s budget. Two corrections to earlier paragraphs: the 7e merge carried
763 tests, not 762 — 762 was `b846768`, and the judgment-6 reversal `ef751fc` added one
`test_bindings.py` case; and the acceptance pair is now 1630.582 s at this run and 1629.698 s at run
`20260907T095331` on `1b60af5`, both green, both under the budget by more than half. `8a08916`
annotates `PHASE3_DESIGN.md`'s notice-content bullet (the four identifier fields since 7c at
`e75f5dd`; the other five bullets hold at `56419cf`, with the intake and resolution functions now in
their new modules) and adds the radius sentence to the gherkin-specs skill and the `origin/main`
note to repo-edits. Stop-check on `8a08916`: `20260907T122622`, 1768.307 s.
`policy_identification.feature` is unchanged at `a504421e2c3ef5ed`; the reopening's spec is drafted
and measured in the next advisor session against the lock at the branch tip. No `tests/api` fixture
supplies bindings yet and no scenario reaches `PORT_BINDING_UNRESOLVABLE` through HTTP — 7f's spec
has to decide whether that is its scenario or `carrier_configuration.feature`'s. The branch is a
superset of `main`.

**2026-09-07: 7f spec committed at `a20e06e`, seven files, awaiting approval.** New
`features/policy_match.feature` (163 lines, sha256 `1e73c8f3c1c7be15`; 49 mutants, 45 locators, 7
literal; simulated 0 survivors, labelled a simulation), and one Background line in five locked
intake specs — `"AAAA"'s policy source is unavailable` — because wiring the policy port makes an
unbound carrier a `500` on every existing submission; measured against the lock: 0 locators moved, 0
approvals touched, five file approvals to re-issue. `notice_intake.feature` gains the
`PORT_BINDING_UNRESOLVABLE` row of its deployment-fault table (5 new locators). The advisor's
decisions are in `ASSUMPTIONS.md` under this date; the one that changes the queue is that 7f writes
a new spec rather than reopening `policy_identification.feature`, whose locked preamble says no
search runs in it. Tests red on the new file's unbound steps, as a spec commit is. Next: the human
approves seven files, then the implementation prompt.

**2026-09-07: 7f implemented at `69a5f45` on `phase3/7f-intake-wiring`, red on two locked scenarios
that await the human; cold gate run `20260907T205240-37029`.** Predicted, then measured, line for
line: protect 3/3; static 0 findings; size worst function 25, worst module `store.py` 248;
complexity 6; boundary 17 step files, 0 direct imports; tests 825/827, the same two failures
predicted from the suite; coverage 100/100; CRAP 6; duplication 0; code mutation 100 %, 756 killed —
687 plus 69 from the new domain code (`domain/policy_match.py`, the deciding-term reading in
`domain/coverage.py`, `carry_onto_candidate`), 0 survivors once two `pytest.raises(match=)` patterns
were anchored; acceptance `15 spec(s), scenarios failing` in 3.697 s, stopping before any mutant, so
the run took 45 s against the 3600 s budget and carries no reviewed-equivalent figure (73 stands; no
approval was added). Out of band, `policy_match.feature`: 49 applied, 49 killed — 42 example, 7
literal — 0 survivors, every kill a failure beyond the baseline's; the advisor's simulation held for
the mutants and not for the baseline. The 2026-09-07 spec paragraph's 'Tests red on the new file's
unbound steps' was the advisor's text and wrong: the new file had no test module and produced no
failure; the red was the five locked specs' new Background line, unbound until this commit — 83 of
764. **The two failures are spec gaps, not retries.** (1) `idempotency.feature`'s Background
configures `BBBB`'s rules and one row submits under `BBBB` expecting `201`; the amendment bound only
`AAAA`, so `BBBB` is an unbound carrier and answers `500 PORT_BINDING_UNRESOLVABLE` by design. The
fix is one Background line, `And "BBBB"'s policy source is unavailable`, after line 46; measured on
the amended text: 46 mutants, 46 locators, 0 signatures moved, both approvals untouched, sha256
`2c8b5c234060b523` at 262 lines — a spec commit and one file approval, the human's. (2)
`policy_match.feature`'s term-verdict row `2025-01-15 | 2026-01-15 | NOT_IN_FORCE | 2025-01-15`
asserts a continuous-coverage date on a loss dated after the only term expired;
`continuous_coverage.feature`, locked, makes that `NOT_EVALUATED` with `NO_COVERAGE_ON_LOSS_DATE`,
and the implementation follows the locked rule. The row cannot pass as written; the advisor decides
its shape — the step `the notice has no continuous coverage date` exists for it. Both are in
`docs/harness-findings.md` under this date. Shape as built: `shell/coverage_verifications.py` (231
lines: table, record, view, delegators reading `NoticeStore.connection`), `shell/policy_match.py`
(84: sufficiency, search, history, the three domain rules), `domain/policy_match.py` (91),
`coverage.py` split into `coverage_types.py` and `term_periods.py` (158/75/125);
`tests/api/policy_match.py` binds each carrier's `tests.fixtures.core_system` through the live-query
registry with a `source` parameter and holds a fault for the scenario; the recorded-indicator step
moved from `test_siu_separation_acceptance.py` to `conftest.py`; the two split-era docstring phrases
are rewritten. **Judgments for ratification:** (1) the binding is resolved in the receipt step
beside the rules and jurisdiction, not in `_decide`, because the spec row says the fault creates no
notice and a fault after receipt would leave one at RECEIVED; (2) the term-in-force rule cites the
one bounding term on a boundary day and, on an uncovered date with no standing cancellation, the
term whose coverage most recently ended before it — `policy_match.feature`'s rows 2 and 3 require
it, `coverage_verification.feature`'s citations are unchanged, and a date two terms share cites
neither; (3) a notice with no loss date, or nothing searchable, is not searched and no row is
written — the term rules have no reason code for a missing loss date and adding one is an
escalation; such a notice pends on validation regardless, and 7g's re-search verifies it; (4)
`POLICY_NOT_MATCHED` and `POLICY_AMBIGUOUS` carry an empty blocker field and sort after every
blocker about what arrived; (5) the verification row also stores the continuous-coverage date and
reason, which the design's column list omitted and the spec reads, and the view carries
`continuous_coverage_reason` so an absent date is never shown without its reason; (6) `as_of` and
`binding` are the search answer's; (7) `NoticeStore` exposes its connection for the table module,
since two delegators would put `store.py` over 250; (8) the shell tests' default binding is an
unavailable source for `AAAA` and `WXYZ`, the statement the locked Backgrounds make; (9) the fixture
gained persistent faults because five locked specs submit more than once under an unavailable
source. Next: the human amends `idempotency.feature`, decides row 3 and approves; the gate is then
expected green and the item closes. The branch is a superset of `main`.

**2026-09-07: 7f spec amended at `2ad4055`, three files, awaiting approval; both gate failures at
`69a5f45` were the advisor's spec errors.** (1) The binding radius of the `"AAAA"` Background line
was measured by grepping the literal, not the step's shape; `idempotency.feature` also submits under
`BBBB`, so `BBBB` gains the same line. (2) The `NOT_IN_FORCE` row asserted a continuous-coverage
date the locked `continuous_coverage.feature` denies — `NO_COVERAGE_ON_LOSS_DATE` — because the
advisor drafted from the design's account of the rule without reading the locked file. The row is
now a fixed-value scenario asserting no date and its reason. Judgment 2's extension of the citation
rule is ratified on the condition that it be specified where the rule lives:
`coverage_verification.feature` gains five citation scenarios (boundary on one term, shared boundary
cites neither, expired cites the lapsed term, gap cites the term before it, loss before any term
cites nothing), 20 new locators, 0 moved, 0 approvals. Digests: idempotency `2c8b5c234060b523`,
coverage_verification `4ce741d06d7f53f7`, policy_match `59b52fa7a7c09fa5`. Next: the human approves
three files, then the binding commit and the cold gate.

**2026-09-07: the three steps the amendment introduced are bound before approval, at the human's
request; the gate is red on the approval stage alone.** `the determination cites no term` and `the
determination cites no cancellation` in `test_coverage_verification_acceptance.py`, `the continuous
coverage reason is …` in `test_policy_match_acceptance.py`; no code touched, and the `BBBB` row
already passes on the amended Background. Cold run `20260907T210809-40620`: tests 832/832, code
mutation 100 %, 756 killed, size worst function 25, complexity 6, boundary 17 step files and 0
direct imports, coverage 100/100, CRAP 6, duplication 0, acceptance `3 unapproved or modified
spec(s)` in 0.004 s — idempotency, coverage_verification and policy_match at the digests in the
paragraph above, awaiting `gauntlet spec approve`. Next: the human approves three files, then the
cold gate is expected green and the item closes.

**2026-09-07: item 7f is closed at the close-out commit on `phase3/7f-intake-wiring`; the merge to
`main` is the human's after the advisor verifies run `20260907T214626-43332`.** Cold gate at
`eb794e4`, `mutants/` cleared, predicted then measured: protect 3/3; static 0; size worst function
25, worst module `store.py` 248; complexity 6; boundary 17 step files, 0 direct imports; tests
832/832 — 827 plus the five citation scenarios plus the reshaped NOT_IN_FORCE scenario minus the
retired row, as predicted; coverage 100/100; CRAP 6; duplication 0; code mutation 100 %, 756 killed,
unchanged since `69a5f45` with `src/` untouched; acceptance `15 spec(s), 73 reviewed-equivalent`, 0
diagnostics, 2427.14 s against the 3600 s Stop hook budget — the pair this close records, and the
one miss in the prediction, which said 1800–2000 s by scaling the last green 1685 s at 1070 mutants
to 1155: the run grew 44 % on 8 % more mutants, so the scaling is not linear and the margin under
the budget is 1173 s. Out of band, at the locked digests and restored to them afterward:
`policy_match.feature` 50 applied, 50 killed, 0 survivors — 38 example and 12 literal, where the
advisor's 43/7 split counted the reshaped NOT_IN_FORCE scenario's five fixed values as table cells;
the totals agree — and `coverage_verification.feature` 108 applied, 108 killed, 0 survivors (40
example, 68 literal); every kill a new failure and no baseline failure in either. The item's
commits, in order: spec `a20e06e`, documents `a9a9a14`, approval `6cc3e56`, implementation
`69a5f45`, documents `26b818d`, amendment `2ad4055`, documents `fe50e7e`, bindings `1e2bfc0`,
approval `eb794e4`, this close-out. Judgments 1–9 were ratified 2026-09-07 and stand in the
implementation paragraph above; decisions 10 and 11 are in `ASSUMPTIONS.md`'s 7f entry. 7g inherits
the debt that a notice with no loss date, or nothing searchable, receives its verification at the
re-search on resolution, and the insured-name search; 7h the claims port and `find_duplicates`'
caller. `ROADMAP.md`'s phase-3 section and `PHASE3_DESIGN.md`'s "what the code actually does today"
carry dated 7f notes. Nothing is in flight in code. Merged to `main` at `850fe04`, 2026-09-08.

**2026-09-08: item 7g is open on `phase3/7g-resolution-research` from `main` at `850fe04`; the
structural commit is done and green at `ce62f3d`, no spec touched, nothing drafted.**
`shell/resolution_evaluation.py` (249 lines) is now read → judge → write: `read` takes the notice,
its arrival sequence and its latest verification in one `BEGIN IMMEDIATE` transaction and answers
the 404 and the early 409 there; `judge` runs the full validation over the merged view holding no
lock, which is where 7g's port calls go, none added; `write` opens the second transaction, re-reads
the notice and answers 409 if it is no longer `PENDED`, otherwise appends the reviewer's payload
record and writes the decision, the audit entry and the SIU events together. `shell/resolution.py`
(98) keeps the 400 and catches the 500, which the judgement now raises between the transactions
with nothing to roll back. The race guard's specification is `tests/shell/test_resolution.py::
test_a_notice_that_moved_between_the_read_and_the_write_is_answered_409_with_nothing_written`: a
second reviewer's resolution runs through the endpoint from inside the first's judgement, and the
first is answered 409 carrying `TRIAGED` with two payload records, three audit entries, the
winner's `resolved_at` and the winner's SIU events, nothing of its own. `resolution.feature`'s 27
rows re-ran unmodified and green. Cold gate at `ce62f3d`, `mutants/` and `.mutmut-cache` cleared,
predicted then measured, run `20260908T085655-217436`: protect 3/3; static 0; size worst function 25, worst
module `resolution_evaluation.py` 249 beside `store.py` 248, `messages.py` 243, `records.py` 242
and `schema.py` 237; complexity 6; boundary 17 step files, 0 direct imports; tests 833/833;
coverage 100/100; CRAP 6; duplication 0; code mutation 100 %, 756 killed — the guard adds 0,
confirmed by a standalone cold `mutmut run` whose sandbox holds `src/claimgate/domain/` only,
756/756 killed; acceptance `15 spec(s), 73 reviewed-equivalent`, 0 diagnostics, 2458.573 s
against the 3600 s Stop hook budget — the pair this opening records — every digest unchanged. The
one figure the prediction could only model was the duration, 2553 s (below).

**Measurements at `ce62f3d` against the lock, read-only, for the advisor before any draft.**
(a) The retirement radius. The requirement's forms — `policy_number`, `policy number`,
`MISSING_REQUIRED_FIELD:policy_number` — occur in eleven specs, and the rows whose *subject*
changes when an absent number with no insured name and postal code becomes
`POLICY_IDENTIFIERS_INSUFFICIENT` are three: `validation.feature`'s two plain scenarios under "A
policy number must be stated" (lines 136 and 143; one literal mutant each, `""` and `"   "` to
the marker; 0 approved), whose assertion table is `MISSING_REQUIRED_FIELD | policy_number` and
which the rule's own comment says 7g replaces; `notice_intake.feature`'s Rule 1 row `absent | 201
| PENDED | MISSING_REQUIRED_FIELD:policy_number | not yet assigned` (line 109; 5 mutants, 5
locators, 0 approved; all five move because each embeds the row, the TRIAGED row's five do not);
and `resolution.feature`'s "clears every blocker" row `absent | SUPPLEMENTAL | 422 | PENDED |
MISSING_REQUIRED_FIELD:policy_number | REFUSED | USER | MISSING_REQUIRED_FIELD:policy_number`
(line 416; 8 mutants, 8 locators, 0 approved; two cells change, its eight locators move, the other
two rows' sixteen hold and their swap targets stay row 1). Fifteen mutants, fifteen locators,
zero approvals — the subject-changing floor — and the state on every one stays `PENDED`. Rows that
merely mention the field, every one using `the notice reports a policy number of "absent"` in a
fixed Given as the pending device and asserting state, records, audit or SIU events but never the
blocker text: `notice_intake.feature`'s audit-entry outline (10 mutants, a relational blockers
column), `idempotency.feature`'s replay row `absent | PENDED` (4), `resolution.feature`'s other
nine policy-number scenarios (101 mutants; the file's 2 approvals sit on the "read at all"
outline's `reviewer` and `supplied_loss_date` columns and embed no policy number) and the two
`HO-7654321` rows beside the changing one (16), `jurisdiction_selection.feature`'s two resolution
outlines (8; the comment at 291–292 names the old code), `siu_separation.feature`'s four (29,
including two `"absent"` literal mutants that die on state before and after). None of these
changes outcome: the notice still pends, the reviewer's number still clears it. Comment-only
mentions in `carrier_configuration.feature` (12, 50), `policy_match.feature` (23–27, "carries a
policy number because validation still requires one until item 7g"), `validation.feature`'s
interplay rule (343–357) and `resolution.feature` (71, 367 — stale since 7d, it still says
"malformed") move no locator; each edited comment costs that file's approval and nothing else.
Approvals to re-issue if only the three subject files are edited: three file approvals, zero
mutant approvals. `policy_identification.feature` (54 mutants, 0 approved) needs no edit for the
wiring. (b) `resolution.feature` after the re-search: ten of its eleven scenarios supply
`HO-7654321` — the future-loss-date outline supplies nothing and the Background's `HO-1234567` is
what its re-search would take — and every one expects `TRIAGED` where the number was supplied;
under the Background's unavailable source the re-search yields `NOT_EVALUATED`, which the design's
table makes an attribute and not a blocker, so no expectation moves. The `records` column counts
payload records and `audit_effect` counts audit entries; a verification row is neither. The row
that supplies `absent` is the subject-changing row in (a), pending either way. One question the
file does not ask: the resolution path will now resolve a binding, and an unbound carrier on that
path has no row anywhere — `notice_intake.feature`'s fault row covers intake only. (c)
Serialization today: a blocker is `ValidationBlocker(code, field)`, one code and one field,
rendered `{"code", "field"}` on every surface; the search's two carry an empty field. The compact
spelling three notice-level specs use is `CODE:field;CODE:field`, parsed by
`tests/acceptance/support.py::parse_compact_blockers` (partition on the first colon, so a bare
`CODE` is an empty field) and, for validation.feature's own step, by
`test_validation_acceptance.py::_parse_compact_blockers` (a split, so a bare code raises);
validation.feature otherwise uses the `| code | field |` table. `policy_identification.feature`
spells its blocker `POLICY_IDENTIFIERS_INSUFFICIENT:policy_number;insured_name;risk_postal_code`,
read by its own step as the code, a colon, and the fields joined by `;` — on a notice row that
same string parses as two blockers, `(POLICY_IDENTIFIERS_INSUFFICIENT, policy_number)` and
`(insured_name, "")`. The pure rule's spelling and the notice-level spelling collide on `;`, and
the advisor chooses between one blocker per absent field (the existing shape, the same code on up
to three rows), one blocker whose field is the tuple under another separator (a model and
serializer change), and a bare code (the fields lost). (d) Intake at the tip:
`shell/policy_match.py::verify_policy` runs `evaluate_identifier_sufficiency` first, between the
transactions, and on `INSUFFICIENT` returns `None` — the blocker is dropped, nothing is searched,
no row is written; `apply_domain_rules` then runs `validate`, whose `_check_policy_number` raises
`MISSING_REQUIRED_FIELD:policy_number`. Sufficiency first, validation second, and only validation's
answer reaches the notice. The resolution path evaluates no sufficiency at all.

**Duration model, from source and a measured baseline.** `gates/acceptance.py::_survivors` runs
`adapters/python.py::run_acceptance`, `pytest <steps directory>`, once per mutant — the whole
`tests/acceptance`, never the one spec's module. Measured at `ce62f3d` with the engine's flags on
a quiet machine: 2.210 s per whole-directory run (2.222, 2.164, 2.244); 291 rows, 1.316 s of
testcase time, the rest interpreter start and collection. Per spec, standalone module wall time ×
mutants at the lock: carrier_configuration 0.437 × 73 = 31.9; continuous_coverage 0.445 × 156 =
69.4; coverage_verification 0.442 × 108 = 47.7; duplicates 0.422 × 57 = 24.1; idempotency 0.518 ×
46 = 23.8; jurisdiction_date 0.395 × 20 = 7.9; jurisdiction_selection 0.493 × 55 = 27.1;
notice_intake 0.460 × 56 = 25.8; policy_identification 0.400 × 54 = 21.6; policy_match 1.447 × 50
= 72.4; resolution 0.598 × 133 = 79.5; siu_indicators 0.536 × 39 = 20.9; siu_separation 0.673 × 53
= 35.7; triage 0.421 × 90 = 37.9; validation 0.523 × 165 = 86.3 — sum 612.0 s, ratio 3.97 to
2427.14 s: the per-module model undercounts four times over because that is not what runs. The
whole-directory model, 2.210 × 1155 = 2552.6 s, is what the observed runs are read against: observed over
modelled is 0.951 for 2427.14 s, 1.002 for the 2556.762 s of run `20260907T223153-123173` on the
same lock, and 0.963 for this run's 2458.573 s. Pricing
a scenario of `resolution.feature`'s shape (27 rows, 0.197 s of testcase time, 7.3 ms a row):
each mutant it adds costs one whole-directory run, 2.21 s; each row it adds costs 7.3 ms on every
mutant's run, 8.4 s at 1155 mutants; a three-row outline with 18 mutants costs 39.8 + 25.7 ≈ 65
s, with 24 mutants ≈ 79 s. The growth is rows × mutants, which is why 8 % more mutants cost 44 %
more time at 7f.

**Judgments for ratification, structural commit:** (1) the reviewer's payload record is appended in
the write transaction, not the read, and the judgement sees it through an in-memory overlay of
the supplied fields, so a 409 from the re-check persists nothing — decision 3's "the 409 persists
nothing at all", extended to the late 409; (2) the read transaction is the same `BEGIN IMMEDIATE`
as every write: `store.py` has two lines of headroom under the module ceiling, a deferred-read
context manager does not fit, and the read holds the lock for three reads and no I/O; (3) the 404
and the early 409 moved into the read, so `conflict` lives in `resolution_evaluation.py` and
answers both 409s, and `resolution.py` keeps only what precedes the notice, the 400, and what
follows the judgement, the 500; (4) the re-read's `None` arm is carried by `or record` for the
type — nothing in the package deletes a notice row, and a vanished one would fail the write on
the payload's foreign key rather than be answered; (5) `judge` is public so the race test can
interpose a competing resolution at the one moment between the read and the write, and the
overtaking resolution is a real one through the endpoint, not a direct row write; (6) the
deployment-fault test's docstring now says what it proves — the read wrote nothing and the write
was never opened. One debt: `resolution_evaluation.py` has one line of headroom, so 7g's port
calls split it. Next: the advisor prices and drafts 7g's scenarios from the measurements above;
nothing is drafted here. The branch is a superset of `main` and is not merged.

**2026-09-08: 7g spec committed on `phase3/7g-resolution-research`, four files, awaiting four
approvals; judgments 1–6 on the structural commit are ratified.** The four files at the advisor's
digests, byte for byte: `validation.feature` 437 lines `dba16d9635813218` — the policy-number rule
is replaced, its two scenarios now assert no blocker (165 locators, 2 moved, 0 of 28 approvals
touched); `notice_intake.feature` 353 `a0619c90ffa2ada7` — the `absent` row's blockers cell is
`POLICY_IDENTIFIERS_INSUFFICIENT:policy_number,insured_name,risk_postal_code` (56 locators, 5
moved, 0 approvals); `resolution.feature` 728 `96dccb0629163d5d` — both cells of the "clears every
blocker" `absent` row (133 locators, 8 moved, 0 of 2 touched); `policy_match.feature` 301
`f7f118b9f5d7c7be` — two new Rules appended, the pair search at intake and the re-search on
resolution (106 mutants, 100 locators, 23 literal, 0 moved, 56 new: 15, 10, 2, 4, 10, 10 and 5 by
scenario in file order). Fifteen locators move, none approved; the suite goes from 1155 to 1211
mutants. Duration estimate from the whole-directory model: about 2,730 s — 2.210 × 1211 = 2676 s
before the twelve new rows' own testcase time, 2,780 s with it at `resolution.feature`'s 7.3 ms a
row, and 3,040 s if the new rows cost what `policy_match.feature`'s existing rows do (25 ms) — under
the 3600 s hook, whose last green run was the stop-check on `6768a16`, run
`20260908T094021-295714`, 2662.549 s, the maximum on the pre-7g lock. Gate on this tree, run
`20260908T114754-375575`: every gate green through code mutation (756 killed) and acceptance red on
the approval stage alone, `4 unapproved or modified spec(s)` in 0.004 s; the remedy names `gauntlet
lock` and the command is `gauntlet spec approve`, the human's. Decisions 1–8 are in `ASSUMPTIONS.md`
under the 7f entry, verbatim. `CLAUDE.md`'s branch rule carries the correction that documents for
an item go on the item's branch and `main` moves only by the human's merge after a verified run;
`da76610` stays where it is as the instance.

**Item 5, read-only.** The resolution endpoint accepts an insured name and risk postal code today:
`supplied` is overlaid field by field onto `NoticeFields`, which has carried both since 7c, so no
message field is new; only the acceptance glue's `_SUPPLIED_FIELDS` map (five names) and the
article in `the reviewer supplies an insured name of` — the regex requires `supplies a ` — stand
between the spec and the shell. Unbound in the appended block: `the notice reports an insured
name of`, `the notice reports a risk postal code of`, `the policy was identified on`, `"AAAA"'s
policy source searches by policy number only` (the fault regex admits three phrases; the fixture
already has `without_name_search`, raising `UnsupportedSearchError`, which the port answers
`IDENTIFIERS_INSUFFICIENT`), `"AAAA"'s policy source answers as before` (the outline's other row,
`is unavailable`, binds), and `the reviewer supplies an insured name of`. Bound but failing as
written: `the reviewer supplies a risk postal code of` raises `unrecognized supplied field`;
`the notice's blockers are` in Given position (the last scenario) has only a `@then` in
`conftest.py`; and `the notice's policy match is none` — three rows for an unsearched notice —
reads the verification through a helper that asserts one exists, unlike the matched-policy step,
which knows `none`. Nine bindings, none touched here. The basis already crosses the port:
`PolicyCandidate.match_basis` is the domain's two arms, the fixture's `matched_by` maps onto it in
the live-query source, and `shell/policy_match.py::verify_policy` drops it when it hands
`match_policy` the references alone; `coverage_verifications` has no column for it and the view no
field. Decision 5 is therefore a field on the match or the verification, one column, one view
field and one allow-list entry, not a port concept. Line counts against 250:
`resolution_evaluation.py` 249, `store.py` 248, `coverage_verifications.py` 231,
`notice_intake.py` 187, `policy_match.py` 84, `messages.py` 243 — the first two split on any
addition, and a column on the verification touches the record, `_columns`, `_from_row`, `view_of`
and `schema.py` (237), so the third likely splits too.

**Judgments beyond the ratified text:** (7) the corrective sentence sits in the "superset" bullet
beside the sentence it corrects, in bold with the date, and names `da76610` as the instance so the
two sentences read as a rule and its exception rather than a contradiction; (8) the ASSUMPTIONS
entry is a sibling bullet after the 7f entry, wrapped to the file's width, words unchanged; (9)
the duration is recorded as the human's "about 2,730 s" beside the arithmetic that brackets it.
Next: the human approves the four files; then the binding commit for the nine steps above and the
implementation — the sufficiency blocker joined to validation's through `canonical_order`, the
re-search in `judge`, the basis column, and the two module splits. The branch is a superset of
`main` and is not merged.

**2026-09-08: 7g implemented at `828ded3` on `phase3/7g-resolution-research`, after the split at
`17de43c`; green run `20260908T124244-462219`, 858 tests, 757 killed, 73 reviewed-equivalent; the merge to
`main` is the human's after the advisor verifies the run.** Cold gate at `828ded3`, `mutants/` and
`.mutmut-cache` cleared, predicted then measured, line by line: protect 3/3; static 0; size worst
function 25, no module at 250 — `messages.py` 248, `store.py` 248, `records.py` 242, `schema.py`
239, `coverage_verifications.py` 237, `validation.py` 209, `resolution_evaluation.py` 207;
complexity 6; boundary 17 step files, 0 direct imports; tests 858/858 — 833 at
`ce62f3d`, the twelve new scenario rows, thirteen unit and shell tests; coverage 100/100; CRAP 6;
duplication 0; code mutation 100 %, 757 killed — net one on 756, the presence check's mutants gone
and the comma-join's and the basis's arrived, from a standalone cold run of 757/757 at 69.35
mutations a second; acceptance `15 spec(s), 73 reviewed-equivalent`, 0 diagnostics, every digest at
the lock of `1a24146`, 2937.262 s against the 3600 s Stop hook budget — the pair this close
records — inside the predicted bracket of 2676 to 3040 s (2.210 s × 1211, plus the twelve new rows
at 7.3 to 25 ms a row) and nearer its top; the margin under the hook is 663 s, the smallest yet,
and 7h's rows will spend more of it. Out of band, at the locked digests and restored to them after, baseline
module green first: `policy_match.feature` 106 applied, 106 killed, 0 survived (83 example, 23
literal); `notice_intake.feature` 56/56 (56 example); `validation.feature` 165 applied, 137 killed,
28 survived (121 example, 44 literal) — the 28 are its 28 approved equivalents, none new;
`resolution.feature` 133 applied, 131 killed, 2 survived (133 example) — its 2 approved equivalents.
**The split.** One, `17de43c`: `resolution_reading.py` (105 lines: the read transaction, the 409
answer, the merged view, the last answer standing) out of `resolution_evaluation.py` (207 after
the judgement grew), because the judgement is where the re-search lands and the module had one
line of headroom. `store.py` was not split: the re-search writes its row through
`coverage_verifications.append`, which reads the connection (7f judgment 7), so no line landed
there. `schema.py` was not split: the column is one line, 239. `messages.py` took three lines and
sits at 248. **What was built.** Domain: `_check_policy_number` is gone;
`POLICY_IDENTIFIERS_INSUFFICIENT` sits in `_CANONICAL_CODE_ORDER` after `MISSING_REQUIRED_FIELD`
and before the search's two, asserted across all three families by
`tests/unit/test_policy_match.py::test_the_three_families_sort_arrival_then_identification_then_search`;
`identification_blockers` joins the absent fields with commas in the rule's order; `match_policy`
takes `FoundPolicy` (reference, basis) and a MATCHED result carries `identified_on`;
`RULESET_VERSION` is `2026-09-08`. Shell: `check_policy` runs sufficiency first on both paths and
searches only what can be searched with a loss date, returning the identification's blockers or
the verification, never both; `apply_domain_rules` composes the three families; the verification
row, record, view and allow-list carry `identified_on`; the port's `IDENTIFIERS_INSUFFICIENT` is
`NOT_EVALUATED` with that reason and the notice proceeds; `judge` resolves the carrier's policy
port with the resolution instant as its clock, re-searches, and where the re-search answers its
match and derivation replace the stored ones, else the last answering row's stand; `write` records
every search that ran beside the decision, applied or refused. The carry-over is proved by
`tests/shell/test_policy_search.py::test_a_re_search_that_cannot_answer_carries_the_last_answers_blocker_and_shows_the_latest_row`.
Glue: the nine bindings — two notice-content steps and a Given form of the blockers step in
`conftest.py`, the supplied-field map with `insured name` and `risk postal code` and its article
`an?`, and in the policy-match module the source's number-only shape, the source unchanged, the
match reader's `none` and the identified-on step — plus one binding the measurement did not list:
`policy_match.feature`'s resolution rows name no reviewer, and `submit_resolution` attributes them
to `adjuster-4471` where a scenario identified none. **Judgments for ratification, beyond the
decided shape:** (10) the re-search's port clock is the resolution instant, so the new row's
`as_of` is the instant the correction was searched on, 7f decision 9's analogue; (11) where the
re-search cannot answer, the last answer's continuous-coverage derivation stands with its
blocker — the decision spoke of blockers, and the date a release's SIU evaluation reads should be
one that was computed, proved by
`test_a_release_under_an_outage_reads_the_last_answers_date_for_its_siu_evaluation`; (12) a
verification row is written on every resolution whose search ran, refused or applied, so the
notice shows the newest row and its reason; (13) `Resolution` carries the two binding sources a
submission names and `Judgement` carries the verification for the write — no new endpoint
concept; (14) the glue's default reviewer for `policy_match.feature`'s resolution rows, a spec gap
to close at that file's next reopening with one Background line, recorded for the close-out beside
`resolution.feature` line 367's stale "malformed"; (15) the comma-join lives in the domain, so the
serialization rule is mutation-gated, and sufficiency runs in the shell's `check_policy` because
the identifiers are notice fields the candidate does not carry (7f judgment 4); (16) `FoundPolicy`
is the domain's shape for what the search found, the port's `PolicyCandidate` mapped onto it in the
shell, and `identified_on` is set only for MATCHED; (17) `answered` is a type guard in
`shell/policy_match.py` and the last answer standing is found in the reading from the trail, not
by a new query in `coverage_verifications.py`, which had room for the column and not a query; (18)
the resolution path's binding fault joined `test_resolution.py`'s fault parametrize as its fourth
row, the same 500 with nothing written. Next: the human verifies the run and merges; the close-out
records the two spec gaps; 7h takes the claims port. The branch is a superset of `main` and is not
merged.

**2026-09-08: item 7g is closed at the close-out commit on `phase3/7g-resolution-research`; the
merge to `main` is the human's after the advisor verifies run `20260908T124244-462219`.** The
pair this close records: acceptance 2937.262 s against the 3600 s Stop hook budget, on 858 tests,
757 killed, 73 reviewed-equivalent, 0 diagnostics, every digest at the lock of `1a24146`. The
stop-check that fired on the documents commit `813a677`, run `20260908T133307-609373`, measured
3149.067 s on the same lock — the largest green figure yet, 451 s under the budget. Out of band
at the locked digests, restored and re-matched: `policy_match.feature` 106/106, `notice_intake.feature`
56/56, `validation.feature` 137 of 165 with its 28 approved equivalents surviving,
`resolution.feature` 131 of 133 with its 2. The item's commits, in order: structural `ce62f3d`,
documents `da76610` (on `main`, the instance the corrected branch rule names), spec `acb06eb`,
approval `1a24146`, split `17de43c`, implementation `828ded3`, documents `813a677`, this
close-out. Judgments 1–18 are ratified and stand in the paragraphs above; decisions 1–9 are in
`ASSUMPTIONS.md`'s 7g entry, decision 9 being judgment 11 as the extension of decision 6 to the
coverage date. The debts:

- POLICY_AMBIGUOUS cannot clear: the re-search takes identifiers, and two references sharing a
  number both match on any re-search. A reviewer needs to choose a reference, which is a new staff
  action with its own audit shape. Proposed queue item, not phase 3's: "Reviewer selects among
  ambiguous candidates", to be placed by the human beside phase 6.
- policy_match.feature's three resolution scenarios name no reviewer; the glue attributes them to
  the locked Backgrounds' identity. One Background line at the file's next reopening.
- resolution.feature line 367 still says "malformed", stale since 7d; a comment-only fix at that
  file's next reopening.
- The acceptance margin is 663 s. Before 7h's spec: raise the hook or land the per-spec scoping
  change in Gauntlet (docs/harness-findings.md wall-time entry; the advisor's O4).
- 7f decision 11 and 7g decision 4 stand: an unsearchable notice or one with no loss date carries
  no verification until its identifiers or date arrive.

The margin in the fourth debt is the verified run's; the stop-check since measured it at 451 s.
`ROADMAP.md`'s phase-3 section and `PHASE3_DESIGN.md`'s "what the code actually does today" carry
dated 7g close notes; `CLAUDE.md`'s start-up step 3 carries the new pair. Nothing is in flight in
code. Merged to `main` at `7f5f786`, 2026-09-08. 7h is next.

**2026-09-09: item 7h is open on `phase3/7h-duplicates-wired` from `main` at `86cd32f`; this
session is housekeeping and read-only measurement, nothing drafted, no code.** Item 7g merged to
`main` at `7f5f786` on 2026-09-08. Two housekeeping merges followed it on `main`, neither an
item: `b0e18f1` put the Stop hook behind `.claude/hooks/stop-check.sh`, which skips the
stop-check when the gated tree is byte-identical to the last green run's and records a tree only
from a wholly green run; `86cd32f` recorded the protected-path rule — no full run while a lock is
pending, the cheap gates under `--fail-fast` instead, and the one permitted interrupt with its
recovery — after the lock at `856ea31`. The last green is the wrapper's seeding run, which the
timing places on the stop-check for `e2a8933`, and its events line reads:

```
{"actual": "15 spec(s), 73 reviewed-equivalent", "at": "2026-09-09T01:14:59+00:00", "diagnostics": 0, "duration": 2673.194, "error": null, "gate": "acceptance", "kind": "gate.finished", "passed": true, "run": "20260909T003016-338541", "v": 1}
```

The pair this paragraph records: acceptance 2673.194 s against the 3600 s Stop hook budget, on
858 tests, 757 killed, 73 reviewed-equivalent, 0 diagnostics, 1211 mutants across fifteen specs;
`.gauntlet/last-green-tree` names that run. A documents-only turn now ends in a skip, one printed
line — `gauntlet stop-check skipped: gated tree unchanged since green run
20260909T003016-338541, 2026-09-09T01:14:59+00:00` — so the hook budget bounds only turns that
touch a gated path, and the pair moves only on those. That run's `.gauntlet/mutation-backup/` is
on disk with all fifteen files byte-identical to the working tree: the engine's residue from a
completed run, not a strand. Nothing is in flight in code; the branch is a superset of `main` and
is not merged.

**2026-09-09: 7h structural commit `9d41011` green cold; spec `features/duplicate_evaluation.feature`
committed on `phase3/7h-duplicates-wired`, awaiting the human's approval; no bindings, no code.**
The split, first. `messages.py` (248) keeps the boundary shapes serialization.py projects —
`NoticeFields`, the two responses, `NoticeView` — and `shell/bundles.py` takes what the
orchestration passes to itself: `Submission`, `Resolution`, `Decision`, `Judgement`,
`AcceptedNotice`, each class AST-identical to the one it was (`ast.dump` compared per class
against the file at `6a0d219`). `schema.py` (239) keeps the notice record and its arrival
sequence — four tables, four triggers — and `shell/trails.py` takes `siu_indicator_events` and
`coverage_verifications` with their four triggers; `SCHEMA_STATEMENTS` is recomposed in its
original order and is value-identical, fourteen statements. Seven import blocks moved to the
new module and were re-sorted; nothing else changed. Sizes after: `messages.py` 136,
`bundles.py` 133, `schema.py` 156, `trails.py` 114; `store.py` 248 is the largest module now.
Cold gate at `9d41011`, `mutants/` cleared, predicted then measured, line by line: protect 3/3
= 3/3; static 0 = 0; size worst function 25, no module at 250 = 25; complexity 6 = 6; boundary
17 step files, 0 direct imports = 17/0; tests 858 = 858/858; coverage 100/100 = 100/100; CRAP
6 = 6.0; duplication 0 = 0; code mutation 757 killed = `score 100.0%, 757 killed`; acceptance
15 specs, 73 reviewed-equivalent, digests unchanged, 2630–2950 s = `15 spec(s), 73
reviewed-equivalent`, 0 diagnostics, every spec still approved, and the events line:

```
{"actual": "15 spec(s), 73 reviewed-equivalent", "at": "2026-09-09T10:28:39+00:00", "diagnostics": 0, "duration": 2670.57, "error": null, "gate": "acceptance", "kind": "gate.finished", "passed": true, "run": "20260909T094346-499212", "v": 1}
```

The pair this paragraph records: 2670.57 s against the 3600 s Stop hook budget, on 1211 mutants.
**The spec.** 147 lines, transcribed from the human's text; sha256 `58a5370b5194531d`, which is
not the `42b23f5dcf881df3` the human expected — no variant tried (trailing newline dropped or
doubled, CRLF, trailing whitespace stripped) matches, the file holds no tab or non-ASCII byte,
and the engine counts 46 mutants on it as expected, so the difference is bytes the transcription
cannot see rather than words; the human diffs their copy against the committed file before
approving. Radius from `radius.py` at the spec commit: 46 mutants, 34 locators, 26 literal,
against the same three expected. Per scenario: 4, 4, 6, 9, 6, 7 and 10 mutants in file order.
Duration estimate for the run that approves it: 1257 mutants at 2.207 s a run (the seeding
calibration) plus the new rows' testcase time, about 2,950 s; at the verified-run calibration of
2.425 s, about 3,200 s. Either fits under 3600 s; 7i's three binding configurations will not, and
that decision opens with 7i. **The measurement the spec was drafted on** (judgments 1–9 of this
morning, ratified; decisions 1–7 in `ASSUMPTIONS.md`'s 7h entry): the fixture holds claims per
policy reference, seeded empty by `hold_policy` and appended by `hold_claim`, and an unknown
reference raises, which the port answers `SOURCE_UNAVAILABLE`; every source method calls
`_misbehave` first, so the fixture's sleep, raise and malformed faults are shared across both
ports of one carrier, and number-only mode is search-only; the test API binds only the policy
half today, with `registry()` passing an empty claims map and nothing in `src/` calling
`resolve_claims_port`; no scenario outside `policy_match.feature` reaches TRIAGED with a matched
policy, because the other five submitting specs declare the source unavailable in their
Backgrounds; and the twelve rows that will call an empty claims source once the port is wired are
`policy_match.feature` lines 62, 97, 98, 108, 133, 134, 178, 204, 225 at intake and 268, 288,
291 on resolution, with line 179 pended-but-matched and, under decision 2, not compared. The
stop-check on this commit is expected red at the acceptance gate's approval stage on the
unapproved spec — the separate-commits rule guarantees it, and it is not a failure to retry.
Next: the human approves the spec; then the bindings for its steps — the claims-source holds
and unavailable steps, the evaluation, candidates and reason steps, the no-evaluation step —
and the implementation under decisions 2 to 7. The branch is a superset of `main` and is not
merged.

**2026-09-10: 7h implemented at `a1e3e28` on `phase3/7h-duplicates-wired`; green run
`20260910T112652-904083`, 882 tests, 757 killed, 73 reviewed-equivalent on 16 specs; the merge to
`main` is the human's after the advisor verifies the run.** The pair this paragraph records:
acceptance 3169.29 s against the 3600 s Stop hook budget, on 1257 mutants — inside the predicted
2,770–3,270 s and 101 s from its top; the margin under the hook is 431 s. Decisions 8–11
(`ASSUMPTIONS.md`, the 7h implementation entry, ratified 2026-09-09) are built: 8, the domain's
`EVALUATED` becomes `OBTAINED` in `duplicate_evaluations._evaluated` and nowhere else; 9,
`Verification.policy_number` carries the found number from the search answer, unstored and
unshown, and the evaluation follows the verification written beside it in the same transaction;
10, `RULESET_VERSION` is `2026-09-09`; 11, `resolve_port_bindings` at receipt and on resolution,
the test API's `claims_entry` beside every policy entry, and the five unavailable-source specs
record `NOT_EVALUATED`/`SOURCE_UNAVAILABLE` on every notice they triage. Cold gate at `a1e3e28`,
`mutants/` cleared, predicted then measured, every line equal: protect 3/3; static 0; size worst
function 25, largest module `store.py` 248 (`coverage_verifications.py` 243, `records.py` 242,
`duplicate_evaluations.py` 190); complexity 6; boundary 18 step files, 0 direct imports; tests
882/882 — 858 plus the twelve rows of the new spec, ten shell tests and two serialization tests;
coverage 100/100; CRAP 6; duplication 0; code mutation 757 killed, flat, so no shell logic reached
`domain/`; acceptance 16 specs, 73 reviewed-equivalent, 0 diagnostics, every digest at its lock,
`duplicate_evaluation.feature` 46 killed and 0 survivors, and the events line:

```
{"actual": "16 spec(s), 73 reviewed-equivalent", "at": "2026-09-10T12:20:05+00:00", "diagnostics": 0, "duration": 3169.29, "error": null, "gate": "acceptance", "kind": "gate.finished", "passed": true, "run": "20260910T112652-904083", "v": 1}
```

Measured out of band after the run, at the locked digest and restored to it:
`duplicate_evaluation.feature` 46 applied, 46 killed, 0 survived, against the advisor's simulated
46/46. The twelve `policy_match.feature` rows the 7h opening paragraph lists — lines 62, 97, 98,
108, 133, 134, 178, 204, 225 at intake and 268, 288, 291 on resolution — now read an empty claims
source and show `OBTAINED` with no candidates and no reason; line 179, pended but matched, shows
none; the four `NOT_EVALUATED` rows show `NOT_EVALUATED` with the port's reason; no locked digest
moved. The two deliberate breakages before the gate: a view served without the evaluation fails
all twelve rows of the new spec and one shell test; an evaluation answering `OBTAINED` with no
candidates on every notice fails nine rows — the three `none`/`OBTAINED` rows are satisfied by
it — and two shell tests. Judgments beyond the ratified decisions, for ratification: (12)
`AcceptedNotice` carries `PortBindings` as one field, `ports`; (13) where the search did not
answer, the evaluation is stamped with the verification's `as_of` and binding, since the claims
port was not asked; (14) `evaluate_on_triage` guards `verification is None` in the same condition
as the state — a type guard, not a case, and the comment says why; (15) the four steps
`policy_match.feature` and the new spec state in the same words — holds policy, has a term, policy
match is, identified on — moved to `conftest.py` with their readers in `support.py`, per the
two-locked-specs finding; (16) serialization's `_rendered` dispatches nested surfaces through a
type-keyed table, so the candidates tuple renders as ids and the blockers as before, at complexity
6; (17) `judge` gave its configuration lookups to `_configured` to stay under 25 lines, the fault
order unchanged; (18) this paragraph is a documents commit after the implementation, as at 7g.
Nothing is in flight in code; the branch is a superset of `main` and is not merged.

**2026-09-10: 7i implemented at `576912e` on `phase3/7i-extract-shape`; green run
`20260910T212538-1548345`, 963 tests, 757 killed, 73 reviewed-equivalent on 16 specs; the merge to
`main` is the human's after the advisor verifies the run.** The pair this paragraph records:
acceptance 3404.662 s against the 7200 s Stop hook budget, on 1263 mutants — inside the predicted
3,200–3,600 s, 2.696 s a mutant; the margin under the hook is 3795 s. Decisions 1–5
(`ASSUMPTIONS.md`, the 7i entry, ratified 2026-09-10) are built: 1, the outline at
`policy_match.feature` lines 136–157, approved at `7b02204`, six mutants, all killed; 2, the
mutation gate ran under live/live and the swap proof is the three plain runs below; 3, `PortHarness`
carries the instant its answers reflect, the three `as_of` assertions compare against it, the
extract harness generates at the clock minus one day, and the contract suite went from 51 to 102
tests with five lines added and seven removed in the suite; 4, `tests/fixtures/core_system.py`
holds a policy's bound day and the source's instant, the extract is generated into `tmp_path` at
the source's instant or the call's when a binding resolves, and `CLAIMGATE_PORT_CONFIGURATION` in
`tests/api/policy_match.py` selects the shape each entry names, live/live by default, read by no
shell module; 5, `CLAUDE.md`'s two sites carry the 3169.29 s / 7200 s pair since `c123151`. The
extract shape is `shell/extract_source.py` (211 lines) and `shell/extract_ports.py` (142 lines),
beside the live-query pair; `bindings.py` is untouched, the bindings schema unchanged, and
`RULESET_VERSION` stays at `2026-09-09` because nothing under `domain/` moved and no decision
changed — only where an answer came from and as of when. Cold gate at `576912e`, `mutants/`
cleared, predicted then measured, every line equal: protect 3/3; static 0; size worst function 25,
no module at 250 (`store.py` 248 unchanged, the two new modules 211 and 142); complexity 6;
boundary 18 step files, 0 direct imports; tests 963/963 — 884 plus 51 from the contract suite's
second harness, 2 from the outline's rows and 26 in `tests/shell/test_extract_ports.py`; coverage
100/100; CRAP 6; duplication 0; code mutation 757 killed, flat, so no shell logic reached `domain/`;
acceptance 16 specs, 73 reviewed-equivalent, 0 diagnostics, every digest at its lock,
`policy_match.feature` at `5f4eb8b7ea9495cc` with 112 mutants and 0 approved, so its 112 killed
follows from the green verdict rather than from a separate count; and the events line:

```
{"actual": "16 spec(s), 73 reviewed-equivalent", "at": "2026-09-10T22:22:50+00:00", "diagnostics": 0, "duration": 3404.662, "error": null, "gate": "acceptance", "kind": "gate.finished", "passed": true, "run": "20260910T212538-1548345", "v": 1}
```

The swap proof, decision 2, three plain runs after the green gate, no shell module changed
between them:

```
CLAIMGATE_PORT_CONFIGURATION=live/live       .venv/bin/python -m pytest tests/acceptance -q   -> 317 passed in 2.52s
CLAIMGATE_PORT_CONFIGURATION=extract/extract .venv/bin/python -m pytest tests/acceptance -q   -> 317 passed in 2.79s
CLAIMGATE_PORT_CONFIGURATION=live/extract    .venv/bin/python -m pytest tests/acceptance -q   -> 317 passed in 3.08s
```

The swappability of the new modules before the gate: an extract port stamping the call instant
instead of the manifest's turned 14 contract tests red (the twelve `as_of` parametrizations over
the extract harness and the two envelope-equality tests), 15 of the 26 extract-port tests (every
one asserting the extract's instant), and both rows of the new outline under extract/extract —
31 tests in all, restored to the same digest before the gate. Judgments beyond the ratified
decisions, for ratification: (6) `live_query_ports.py`'s guard is public, `guarded`, and gains one
mapping, `MalformedAnswerError` (declared in `live_query_source.py`) to `SOURCE_MALFORMED`, so the
extract ports reuse the budget and the mappings instead of carrying a second wrapper; (7) every
extract operation is two reads under one budget — the manifest first under the whole budget, then
the data file under what remains — so a data file that is missing, slow or not its shape still
answers with the extract's instant, while an extract that cannot be opened at all (no directory, no
manifest, a manifest not its shape, a manifest read exhausting the budget) answers with the call
instant, the only one there is; (8) the manifest's `history_from` is validated and read but the
port stamps the binding's horizon as the protocol requires, and the two disagreeing is an open
decision, not a rule — escalated, not defaulted — decided 2026-09-10 by decision (6) in
`ASSUMPTIONS.md`, a later manifest horizon answering `SOURCE_MALFORMED` on the term history, its
implementation queued as the next item's opening housekeeping — implemented 2026-09-11 on `main` as the
last build commit before the clean-up tag, `_holds_less` in `extract_ports.py` (171 lines) with
four tests, the inverted comparison turning exactly the two dated-side tests red, cold run
`20260911T100212-1991987` green at 3690.978 s on the same 1263 mutants, 966 tests; (9) the manifest declares `searchable_by`, and a
name search over an extract of numbers only is `IDENTIFIERS_INSUFFICIENT`, never a silent
`NOT_FOUND`; (10) a reference no file holds is `LookupError`, `SOURCE_UNAVAILABLE` as for a live
source (7e decision 7); (11) the generator is `tests/fixtures/extract.py`, shared by the contract
harness and the test API rather than placed in `tests/api/policy_match.py`, and the fixture's
standing faults become the file set's shape — unavailable is a manifest with no data files behind
it, malformed is data files that are not JSON, the claims side down is no claims file — while a
source that does not answer within its budget is the reader's sleep, since no file is slow on its
own; (12) the contract suite's timeout path over the extract is that same sleep, at the harness's
reader on the next data read: the port's budget is enforced on real elapsed time, so the assertion
tests the guard, and this is the class of the in-process system's own sleep, not decision 3's,
where the assertion compared against a value the fixture chose; the reader parameter on
`ExtractFileSet` exists so a test can do this; (13) `INSTANT` moved to `port_harness.py` so the
harness can generate a day before the clock without importing the suite, and the suite's own
definition and its unused `UTC` import went; (14) `bound_by` compares a bound day with the
instant's UTC date, and with no source instant every held policy is present, the fixture holding no
clock; (15) a live source that is behind stamps its instant through the test API's `_stamping`,
which replaces the binding's clock, so the outline holds under live/live without a shell change;
(16) an extract entry's `source` stays the carrier code in the test API and the factory maps it to
a directory under the scenario's `tmp_path`, generated again on every binding resolution, at
submission and at resolution; (17) a configuration value that is not `<policy>/<claims>` of
`live` or `extract` raises at import; (18) an extract with nothing held is written at the
harness's construction, so a search over nothing is `NOT_FOUND` as of the extract rather than no
extract; (19) `tests/api/policy_match.py` is 302 lines and `tests/shell/test_extract_ports.py`
283, outside the size gate, which measures `src/` only (`test_port_contracts.py` at 365 was
already green); (20) this paragraph is a documents commit after the implementation, as at 7h.
Nothing is in flight in code; the branch is a superset of `main` and is not merged.
