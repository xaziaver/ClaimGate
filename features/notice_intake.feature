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
    # The claimant-name requirement below never fires anywhere in this file:
    # it applies only to a Section II loss - an injury or a liability claim,
    # where there is a specific person to name - and every notice below
    # reports wind_hail, a Section I property peril. A TRIAGED notice below
    # therefore carries no claimant name despite the carrier requiring one,
    # and that is consistent with the rule, not a gap in it -
    # validation.feature is where the requirement's own behavior, by loss
    # type, is specified.
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
    # succeeds, is correct, or runs at all. The notice used throughout is the
    # one every rule finds a blocker on - reusing Rule 1's PENDED case rather
    # than its TRIAGED one, because a receipt that only shows up when
    # validation goes well is exactly the failure this design exists to
    # prevent, and the TRIAGED case alone could not tell the two apart.
    #
    # An outline over the two audit entries themselves, one row per entry,
    # rather than a plain scenario naming both: a plain scenario's first
    # draft here had seven Then steps and exactly one mutant, because a fixed
    # step inside either shape is never mutated and nothing in this rule had
    # a second row to place a value beside. The ordinal column is what makes
    # the swap real - substituting first for second (or the reverse) asks
    # for the wrong entry's state, actor, and blockers together, so an
    # implementation that only gets one of the two entries right is still
    # caught. Measured directly against the engine before this was written to
    # disk: 10 mutants, all example-kind, none vacuous - up from the plain
    # scenario's 1 (itself vacuous) and ahead of the other layout measured
    # alongside it, which kept RECEIVED/EXTERNAL/SYSTEM as fixed text on
    # named-not-columned steps and so never mutated them at all, missing the
    # receipt entry's own actor and state entirely for 6 mutants, 4 of which
    # duplicated Rule 1's own policy_number/state coverage rather than adding
    # to it.
    #
    # occurred_at and ruleset_version are named in PHASE2_DESIGN.md's audit
    # schema but are not asserted with a literal value here: occurred_at is
    # real wall-clock time at the moment the acceptance run executes, which
    # cannot be stated as a spec literal at all, and ruleset_version is a
    # deployment-declared label with no agreed value yet. Both are recorded
    # in this item's own report as assertions that could not be moved into an
    # Examples column, not silently dropped. The blockers column keeps the
    # relational assertion rather than a second copy of the literal reason
    # code Rule 1 already carries for real: the receipt entry's row asserts
    # it carries none yet, the determination entry's row asserts it carries
    # the same ones the notice itself does, and the swap between those two
    # rows is what proves the receipt entry is not merely a second copy of
    # the determination one.
    #
    # The last line - no entry beyond the two named above - is a fixed
    # assertion, true identically on both rows, and generates no mutant:
    # there is no sibling row where a third entry would be correct, so the
    # engine has nothing to swap it against. Kept anyway, because it is a
    # domain fact worth asserting even where mutation cannot check it: an
    # append-only log that is the statutory system of record for a claim
    # communication should never tolerate a spurious extra write, and
    # nothing else in this rule would notice one.
    Scenario Outline: Each audit entry for a notice that satisfies no domain rule names its own state, actor, and identity, in order
      Given the notice reports a policy number of "absent"
      When the notice is submitted for intake
      Then the audit trail's <ordinal> entry moves it to <state>
      And that entry is entered by <actor>
      And that entry carries <identity>
      And that entry's blockers are <blockers>
      And the audit trail holds no entry beyond those two

      Examples:
        | ordinal | state    | actor    | identity              | blockers                                 |
        | first   | RECEIVED | EXTERNAL | no verified identity  | none yet, since no rule has run          |
        | second  | PENDED   | SYSTEM   | no verified identity  | the same ones the notice itself carries  |

  Rule: A notice is received only if its loss date is a real date

    # Distinct from the rule above: a notice with a blank policy number is
    # schema-valid and reaches PENDED, because intake can still parse and
    # hold it for the reporter to complete. A loss date that is not a date
    # at all cannot be evaluated by any domain rule and cannot be held for
    # correction the way a missing field can, so no notice is ever created
    # for it. That is not the same as nothing having arrived: a submission
    # naming a carrier, a policy number, and a loss type, with only the loss
    # date unusable, is still a received communication, and refusing to
    # create a notice does not mean refusing to keep a record of the attempt
    # - intake keeps one, and hands the reporter a reference to it, so the
    # same submission can be named again later even though it never became a
    # notice. ASSUMPTIONS.md, "A refused submission is still a received
    # communication." PHASE2_DESIGN.md's status-code table: "schema-invalid,
    # no notice created, submission recorded" - 400.
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
    #
    # Whether a notice exists and whether a record of the submission exists
    # are two columns, not one compound phrase, because they are two
    # independent facts now that they can disagree - PHASE2_DESIGN.md's own
    # status-code table states the decision the same way, as two clauses
    # joined by a comma, not one. Splitting them doubles the outcome
    # columns' own mutants, 2 to 4, over the single-column version this
    # amendment replaced, raising this rule's total from 4 to 6: each column
    # now carries its own swap between rows, so an implementation that gets
    # the notice half right and the record half wrong - or the reverse - is
    # still caught, where one compound column could only fail or pass as a
    # whole.
    Scenario Outline: A notice is received only if its loss date is a real date
      Given the notice reports a loss date of "<loss_date>"
      When the notice is submitted for intake
      Then intake <notice_outcome>
      And a record of the submission <record_outcome>

      Examples:
        | loss_date  | notice_outcome     | record_outcome                              |
        | 2026-06-01 | creates the notice | is kept, and reachable through the notice   |
        | not-a-date | creates no notice  | is kept anyway, with a reference of its own |
