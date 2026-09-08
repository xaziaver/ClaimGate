Feature: Policy match at intake - what the search finds, and what the notice carries afterward
  As a claims intake system
  I need to search the carrier's policy source with the identifiers a notice carries
  So that a notice on a policy the source can find proceeds with a recorded, dated
  verification, and one it cannot find pends for a reviewer with the reason

  # PHASE3_DESIGN.md, "Coverage verification as an intake outcome". Three
  # rules already locked feed this one and are not restated: identifier
  # sufficiency (policy_identification.feature), term in force at the loss
  # date (coverage_verification.feature) and the continuous-coverage date
  # (continuous_coverage.feature). This file specifies the intake surface
  # those rules reach through: what the search's answer does to the notice,
  # and which attributes the notice shows afterward.
  #
  # Verification, not determination. A policy that was not in force on the
  # loss date is an attribute of a TRIAGED notice, never a blocker. The
  # blockers here are the two a reviewer can act on - no policy found, or
  # more than one - and a source fault is neither: a reviewer cannot resolve
  # an outage, so the notice proceeds with the verification marked
  # NOT_EVALUATED and its reason, and the standing rule holds - a result not
  # computed is never reported as a negative.
  #
  # Every notice in this file carries a policy number, because validation
  # still requires one until item 7g. The insured-name-and-postal-code
  # search and POLICY_IDENTIFIERS_INSUFFICIENT are therefore not reachable
  # through intake here, and this file does not pretend they are; 7g adds
  # them. A carrier with no policy source is a deployment fault and is a
  # row of notice_intake.feature's deployment-fault table, not this file's.

  Background:
    Given the carrier "AAAA" requires the claimant name
    And "AAAA" does not require the claimant contact
    And "AAAA" has no late reporting threshold configured
    And "AAAA" configures a recent policy inception threshold of 30 days
    And "AAAA" configures a duplicate match window of 60 days
    And "AAAA"'s policy source holds policy "POL-88213" numbered "HO-4471209" for "Marisol Quintero" at postal code "34287"
    And that policy has a term effective "2026-01-15" and expiring "2027-01-15"
    And the notice is submitted by carrier "AAAA"
    And the insured property is in "FL"
    And the notice is submitted at "2026-08-24T16:00Z"
    And the notice reports a loss date of "2026-06-01"
    And the notice reports a loss type of "wind_hail"
    And the notice reports a notice type of "INITIAL"

  Rule: One candidate proceeds; none or several pends, and the blocker says which

    # One table mixing the outcomes, so a substitution between TRIAGED and
    # PENDED, or between the two blockers, lands on a row that expects the
    # other and is killed. The number that finds nothing is well-formed: a
    # wrong number is a search miss, not a validation failure (item 7d).
    Scenario Outline: The search's answer decides whether intake proceeds or pends
      Given the notice reports a policy number of "<policy_number>"
      When the notice is submitted for intake
      Then the response is 201
      And the notice's state is <state>
      And the notice's blockers are <blockers>
      And the notice's policy match is <match>
      And the matched policy is <matched_policy>

      Examples:
        | policy_number | state   | blockers           | match       | matched_policy |
        | HO-4471209    | TRIAGED |                    | MATCHED     | "POL-88213"    |
        | HO-4471290    | PENDED  | POLICY_NOT_MATCHED | NOT_MATCHED | none           |

    # A number that answers with two references is a real shape: a policy
    # rewritten mid-term keeps its number under a new reference in some
    # systems, and both are on the source. Intake does not pick; the
    # reviewer does.
    Scenario: The number is on two policies, so the reviewer chooses
      Given "AAAA"'s policy source also holds policy "POL-88214" numbered "HO-4471209" for "Marisol Quintero" at postal code "34287"
      And the notice reports a policy number of "HO-4471209"
      When the notice is submitted for intake
      Then the response is 201
      And the notice's state is PENDED
      And the notice's blockers are POLICY_AMBIGUOUS
      And the notice's policy match is AMBIGUOUS
      And the matched policy is none

  Rule: A matched notice carries the term verdict, the deciding term, and the instant the answer reflects

    # The term rule itself is coverage_verification.feature's; here the
    # rows show the verdict reaching the notice unchanged. A boundary day on
    # the term's expiration belongs to the run that ended that day
    # (continuous_coverage.feature), so both rows carry a coverage date.
    Scenario Outline: The term verdict is an attribute, and a covered date carries its run
      Given that policy's only term is effective "<effective>" and expiring "<expiration>"
      And the notice reports a policy number of "HO-4471209"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the term in force at the loss date is <term>
      And the deciding term is effective "<effective>" and expiring "<expiration>"
      And the coverage verification is as of "2026-08-24T16:00Z"
      And the notice's continuous coverage date is "<continuous_coverage_date>"

      Examples:
        | effective  | expiration | term         | continuous_coverage_date |
        | 2026-01-15 | 2027-01-15 | IN_FORCE     | 2026-01-15               |
        | 2025-06-01 | 2026-06-01 | BOUNDARY_DAY | 2025-06-01               |

    # The verdict that would tempt a blocker. NOT_IN_FORCE is a fact for the
    # coverage reviewer, not a reason intake may hold the notice: the
    # reporter has given notice, and the acknowledgment clock is running.
    # No run of coverage contains the loss, so there is no coverage date to
    # derive, and the locked rule says so rather than reaching for the
    # lapsed term's inception. The lapsed term is cited, as the reviewer's
    # starting point. Fixed values throughout: the shape is what mutation
    # cannot reach here, and the verdict itself is protected above.
    Scenario: A loss after the only term expired proceeds, not in force, with no coverage date
      Given that policy's only term is effective "2025-01-15" and expiring "2026-01-15"
      And the notice reports a policy number of "HO-4471209"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the term in force at the loss date is NOT_IN_FORCE
      And the deciding term is effective "2025-01-15" and expiring "2026-01-15"
      And the notice has no continuous coverage date
      And the continuous coverage reason is NO_COVERAGE_ON_LOSS_DATE

    # The first producer of the continuous-coverage date. Until this item
    # the recent policy inception indicator was NOT_EVALUATED on every real
    # notice; now it reads the date the term history yields. Twelve days
    # before the loss is recent against the carrier's 30-day threshold;
    # 137 days is not. The threshold's own boundary is siu_indicators.feature's.
    Scenario Outline: The continuous-coverage date reaches the recent policy inception indicator
      Given that policy's only term is effective "<effective>" and expiring "2027-06-30"
      And the notice reports a policy number of "HO-4471209"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the notice's continuous coverage date is "<effective>"
      And the recent policy inception indicator recorded for the notice is <recent>

      Examples:
        | effective  | recent |
        | 2026-05-20 | TRUE   |
        | 2026-01-15 | FALSE  |

  Rule: A source fault proceeds with the verification marked not evaluated, and its reason

    # Three faults, one outcome, distinct reasons: a substitution between
    # reasons is killed by the reason column, and a substitution of the
    # state by any row. Nothing about the term or the coverage date is
    # derived from an answer that did not arrive.
    Scenario Outline: A fault on the policy source is not the reporter's problem
      Given "AAAA"'s policy source <fault>
      And the notice reports a policy number of "HO-4471209"
      When the notice is submitted for intake
      Then the response is 201
      And the notice's state is TRIAGED
      And the notice's policy match is NOT_EVALUATED
      And the verification's reason is <reason>
      And the term in force at the loss date is NOT_EVALUATED
      And the notice has no continuous coverage date
      And the coverage verification is as of "2026-08-24T16:00Z"
      And the recent policy inception indicator recorded for the notice is NOT_EVALUATED with reason NO_CONTINUOUS_COVERAGE_DATE

      Examples:
        | fault                                 | reason             |
        | is unavailable                        | SOURCE_UNAVAILABLE |
        | does not answer within its budget     | SOURCE_TIMEOUT     |
        | answers in a shape that is not its own | SOURCE_MALFORMED   |

  Rule: The search runs on any notice that can be searched, whether or not it pends for another reason

    # An injury notice with no claimant name and no incident description
    # pends on validation. The search still runs: a reviewer clearing the
    # missing-field pend sees the match beside it, the port call is spent
    # once, at intake, and the answer is on the notice for whoever opens it.
    Scenario Outline: A notice pending on a missing field still carries its verification
      Given the notice reports a policy number of "HO-4471209"
      And the notice reports a loss type of "<loss_type>"
      When the notice is submitted for intake
      Then the notice's state is <state>
      And the notice's blockers are <blockers>
      And the notice's policy match is <match>
      And the term in force at the loss date is <term>

      Examples:
        | loss_type | state   | blockers                                                                         | match   | term     |
        | wind_hail | TRIAGED |                                                                                  | MATCHED | IN_FORCE |
        | injury    | PENDED  | MISSING_REQUIRED_FIELD:claimant_name;MISSING_REQUIRED_FIELD:incident_description | MATCHED | IN_FORCE |

  Rule: Without a policy number, an insured name and risk postal code find the policy; less than that pair pends, and the blocker names what is absent

    # Item 7g. The sufficiency rule is policy_identification.feature's; these
    # rows are its intake surface now that validation no longer requires a
    # number. An insufficient set is not searched, so the notice carries no
    # verification: there was nothing to ask. The blocker lists every absent
    # identifier field in the rule's order, comma-joined on the notice. The
    # policy number is fixed absent here because, where the pair finds the
    # policy, the number is inert, and a column mutation cannot see it; the
    # name-absent row is left to the domain spec for the same reason, a
    # postal code beside no name being inert too.
    Scenario Outline: With no policy number, the pair decides whether the notice is searched
      Given the notice reports a policy number of "absent"
      And the notice reports an insured name of "<insured_name>"
      And the notice reports a risk postal code of "<risk_postal_code>"
      When the notice is submitted for intake
      Then the response is 201
      And the notice's state is <state>
      And the notice's blockers are <blockers>
      And the notice's policy match is <match>

      Examples:
        | insured_name     | risk_postal_code | state   | blockers                                                                    | match   |
        | Marisol Quintero | 34287            | TRIAGED |                                                                             | MATCHED |
        | Marisol Quintero | absent           | PENDED  | POLICY_IDENTIFIERS_INSUFFICIENT:policy_number,risk_postal_code              | none    |
        | absent           | absent           | PENDED  | POLICY_IDENTIFIERS_INSUFFICIENT:policy_number,insured_name,risk_postal_code | none    |

    # The case the search exists for: a contractor's mistyped number beside
    # the correct insured name and postal code is a match, on the pair, and
    # the notice says which identifiers found it. The same mistyped number
    # with the name alone is a search that misses: a name without a postal
    # code is not a searchable pair, and the number found nothing.
    Scenario Outline: A wrong policy number is a search miss the pair can rescue
      Given the notice reports a policy number of "HO-4471290"
      And the notice reports an insured name of "Marisol Quintero"
      And the notice reports a risk postal code of "<risk_postal_code>"
      When the notice is submitted for intake
      Then the notice's state is <state>
      And the notice's blockers are <blockers>
      And the notice's policy match is <match>
      And the policy was identified on <identified_on>

      Examples:
        | risk_postal_code | state   | blockers           | match       | identified_on                |
        | 34287            | TRIAGED |                    | MATCHED     | INSURED_NAME_AND_POSTAL_CODE |
        | absent           | PENDED  | POLICY_NOT_MATCHED | NOT_MATCHED | none                         |

    # The identification blocker is about what arrived, so it sorts with the
    # arrival blockers, after them, and before the search's own - which
    # cannot co-occur with it, since an unsearchable notice is not searched.
    Scenario: An insufficient set beside missing claimant fields lists all three, arrival first
      Given the notice reports a policy number of "absent"
      And the notice reports a loss type of "injury"
      When the notice is submitted for intake
      Then the notice's state is PENDED
      And the notice's blockers are MISSING_REQUIRED_FIELD:claimant_name;MISSING_REQUIRED_FIELD:incident_description;POLICY_IDENTIFIERS_INSUFFICIENT:policy_number,insured_name,risk_postal_code

    # A source that cannot search on the identifiers it was given is a
    # source limitation, not the reporter's: the notice proceeds with the
    # verification marked not evaluated and the port's reason, like a fault.
    Scenario: A source that searches by number only cannot answer a name-and-postal-code notice
      Given "AAAA"'s policy source searches by policy number only
      And the notice reports a policy number of "absent"
      And the notice reports an insured name of "Marisol Quintero"
      And the notice reports a risk postal code of "34287"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the notice's policy match is NOT_EVALUATED
      And the verification's reason is IDENTIFIERS_INSUFFICIENT

  Rule: Correcting identifiers through resolution searches again on the merged notice, and only an answer clears the search's blocker

    # Item 7g. Resolution re-searches with the identifiers the notice has
    # after the reviewer's corrections are merged, and the answer decides
    # afresh: a right number clears the miss, a second wrong one keeps it.
    Scenario Outline: A corrected policy number is searched, and the answer decides
      Given the notice reports a policy number of "HO-4471290"
      And the notice is submitted for intake
      When the reviewer supplies a policy number of "<supplied_policy_number>"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is <response>
      And the notice's state is <state>
      And the notice's blockers are <blockers>
      And the notice's policy match is <match>

      Examples:
        | supplied_policy_number | response | state   | blockers           | match       |
        | HO-4471209             | 200      | TRIAGED |                    | MATCHED     |
        | HO-4471299             | 422      | PENDED  | POLICY_NOT_MATCHED | NOT_MATCHED |

    # A search that could not answer leaves the blocker the last answer set:
    # a result not computed is neither a match nor a miss, and an outage
    # must not turn a reviewer's correction into a triage. The verification
    # shown is the latest, and says why it could not answer.
    Scenario Outline: Only a search that answers can clear the search's blocker
      Given the notice reports a policy number of "HO-4471290"
      And the notice is submitted for intake
      And "AAAA"'s policy source <source>
      When the reviewer supplies a policy number of "HO-4471209"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is <response>
      And the notice's state is <state>
      And the notice's blockers are <blockers>
      And the notice's policy match is <match>

      Examples:
        | source           | response | state   | blockers           | match         |
        | answers as before | 200      | TRIAGED |                    | MATCHED       |
        | is unavailable    | 422      | PENDED  | POLICY_NOT_MATCHED | NOT_EVALUATED |

    Scenario: A reviewer supplies the insured name and postal code the notice lacked, and the policy is found
      Given the notice reports a policy number of "absent"
      And the notice is submitted for intake
      And the notice's blockers are POLICY_IDENTIFIERS_INSUFFICIENT:policy_number,insured_name,risk_postal_code
      When the reviewer supplies an insured name of "Marisol Quintero"
      And the reviewer supplies a risk postal code of "34287"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is 200
      And the notice's state is TRIAGED
      And the notice's policy match is MATCHED
      And the policy was identified on INSURED_NAME_AND_POSTAL_CODE
