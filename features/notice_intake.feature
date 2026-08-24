Feature: Notice intake

  As a claims intake system
  I need every submitted notice to receive a durable receipt and then reach
  a state a caller can act on, in the same request
  So that a reporter's notice is never lost, never refused outright, and
  always ends up either triaged or held for the specific thing it is
  missing

  # PHASE2_DESIGN.md's Record state model: RECEIVED, TRIAGED, and PENDED are
  # the three states phase 2 can reach. There is no rejected, invalid, or
  # discarded state and there will not be one (CLAUDE.md) - a notice cannot
  # be refused once it clears the schema boundary below, because notice
  # given is notice received and the Fla. Stat. 627.70131(1)(a)
  # acknowledgment clock starts at receipt regardless of data quality.
  # RECEIVED itself is never observed at rest: the transition out of it -
  # to TRIAGED if no domain rule finds a blocker, to PENDED if one does -
  # happens synchronously within the same request that captured the notice,
  # per the transition table's own actor column (EXTERNAL captures,
  # SYSTEM decides, both before this feature's steps ever query the record
  # back).

  # "A domain rule finds a blocker" here means validate()'s blockers only -
  # the transition table's own wording. SIU indicators are explicitly out
  # of this item's scope (QUEUE.md item 5f: "No SIU computation, no SIU
  # storage, no SIU field - 5f builds all of it") and are asserted nowhere
  # below. Duplicate-candidate detection is not named as this item's or as
  # excluded from it by anything read while drafting this file; this draft
  # does not assert a duplicate-candidate attribute either way, and that
  # silence is recorded as a gap in QUEUE.md rather than resolved here by
  # assuming an answer.

  # Severity and queue are asserted only for the row that reaches TRIAGED,
  # per PHASE2_DESIGN.md's own framing: "Queue, severity, SIU indicators,
  # and duplicate candidates are attributes... data carried by a TRIAGED
  # notice" (emphasis on which record carries them). A PENDED notice has
  # not been triaged and so carries neither - proven below as its own
  # assertion, not left to silence.

  # "Today, in the jurisdiction" is stated as a fact throughout, exactly as
  # validation.feature already treats "today" as an already-resolved date
  # the domain receives - deriving it from a request's UTC instant and a
  # jurisdiction's timezone is jurisdiction_date.feature's job one layer
  # down. Which zone a given notice's jurisdiction resolves to (risk
  # location, mailing address, or carrier configuration) is recorded in
  # ASSUMPTIONS.md, "The jurisdiction timezone is a parameter of the
  # conversion, not a constant in it," as arriving with this item and still
  # open - not decided here, and nothing below depends on how it is
  # eventually resolved.

  Background:
    Given the carrier "AAAA" requires the claimant name
    And "AAAA" does not require the claimant contact
    And "AAAA" recognizes the policy-number prefixes "HO;DP"
    And "AAAA" has no late reporting threshold configured
    And "AAAA" configures a recent policy inception threshold of 30 days
    And "AAAA" configures a duplicate match window of 60 days
    And the notice is submitted by carrier "AAAA"
    And today, in the jurisdiction, is "2026-08-24"
    And the notice reports a policy number of "HO-1234567"
    And the notice reports a loss date of "2026-06-01"
    And the notice reports a loss type of "wind_hail"
    And the notice reports a notice type of "INITIAL"

  Rule: A schema-valid notice always reaches a state the caller can act on, in the same request

    # One outline, both outcomes mixed, so a substitution between TRIAGED
    # and PENDED - or between a real blocker and none - lands on a row
    # with a different expectation and is killed rather than surviving as
    # an equivalent swap between same-outcome rows
    # (.claude/skills/gherkin-specs, "Prefer one table mixing outcomes over
    # separate same-outcome tables"). The PENDED row's blocker is the
    # ordinary MISSING_REQUIRED_FIELD:policy_number from validation.feature
    # - reused, not reinvented, since this item calls that same rule and
    # does not get its own blocker vocabulary.
    Scenario Outline: A schema-valid notice is triaged or pended depending on whether a domain rule finds a blocker
      Given the notice reports a policy number of <policy_number>
      When the notice is submitted for intake
      Then the notice's state is <state>
      And the notice's blockers are <blockers>
      And the notice's severity and queue are <severity_and_queue>
      And the notice can be retrieved afterward, showing state <state>

      Examples:
        | policy_number | state   | blockers                              | severity_and_queue      |
        | HO-1234567    | TRIAGED |                                       | standard, standard      |
        | absent        | PENDED  | MISSING_REQUIRED_FIELD:policy_number  | not yet assigned        |

  Rule: The notice's receipt is recorded before any rule runs, and does not depend on what those rules find

    # Statutory point, not a shape preference: PHASE2_DESIGN.md's audit log
    # section calls the two-write design deliberate, "not an inefficiency,"
    # because the Fla. Stat. 627.70131(1)(a) acknowledgment clock starts at
    # the receipt timestamp and must not depend on whether rule evaluation
    # succeeds, is correct, or runs at all. The sharpest place to prove it
    # holds is the row where every rule finds a blocker - reusing Rule
    # 1's PENDED case rather than its TRIAGED one, because a receipt that
    # only shows up when validation goes well is exactly the failure this
    # design exists to prevent, and the TRIAGED case alone could not tell
    # the two apart.
    #
    # A plain scenario, not an outline, so every value below - both
    # entries' actor type, both entries' unauthenticated state, the
    # determination's outcome and blockers - is independently reachable by
    # mutation without needing a second row (docs/harness-findings.md,
    # "Mutation cannot see a fixed Given"; carrier_configuration.feature's
    # first rule uses the same reasoning).
    #
    # occurred_at and ruleset_version are named in PHASE2_DESIGN.md's audit
    # schema but are not asserted with a literal value here: occurred_at is
    # real wall-clock time at the moment the acceptance run executes, which
    # cannot be stated as a spec literal at all, and ruleset_version is a
    # deployment-declared label with no agreed value yet. Both are recorded
    # in this item's own report as assertions that could not be moved into
    # an Examples column, not silently dropped. The blockers named on the
    # audit entry are asserted relationally, against the notice's own
    # blockers, rather than restated as a second quoted literal - the
    # literal value itself is already a real, Examples-driven mutant on the
    # rule above, and restating it here would only be checking the same
    # fact a second time under a plain scenario's weaker reach.
    Scenario: A notice that satisfies no domain rule is still received before it is pended
      Given the notice reports a policy number of "absent"
      When the notice is submitted for intake
      Then the notice's audit trail records that it first moved to RECEIVED
      And that entry is entered by the system that captured it
      And that entry carries no verified identity
      And the audit trail next records it moving to PENDED
      And that entry is entered by the system's rules
      And that entry also carries no verified identity
      And that entry names the same blockers the notice itself carries

  Rule: A notice is received only if its loss date is a real date

    # Distinct from the rule above: a notice with a blank policy number is
    # schema-valid and reaches PENDED, because intake can still parse and
    # hold it for the reporter to complete. A loss date that is not a date
    # at all cannot be evaluated by any domain rule and cannot be held for
    # correction the way a missing field can - there is nothing here to
    # acknowledge, so the acknowledgment clock this item exists to protect
    # never starts, and nothing is persisted. PHASE2_DESIGN.md's status-code
    # table: "schema-invalid, nothing persisted" - 400.
    #
    # Both rows sit in one table, a real date against one that is not a
    # date at all, rather than each in a same-outcome scenario of its own -
    # a substitution between them moves the actual outcome instead of
    # swapping between two rows that already agree
    # (.claude/skills/gherkin-specs, "Prefer one table mixing outcomes over
    # separate same-outcome tables"). Item 5a's precedent for a plain
    # scenario applies only to a single-value refusal with no differing row
    # to place beside it; here a second, differing row exists, so an
    # outline costs nothing and reaches a real mutant that a plain
    # scenario's quoted literal would only have reached vacuously, at step
    # resolution (docs/harness-findings.md, "A one-row outline forfeits its
    # own step literals").
    Scenario Outline: A notice is received only if its loss date is a real date
      Given the notice reports a loss date of "<loss_date>"
      When the notice is submitted for intake
      Then intake <outcome>

      Examples:
        | loss_date  | outcome                               |
        | 2026-06-01 | creates the notice                    |
        | not-a-date | refuses the request, creating nothing |
