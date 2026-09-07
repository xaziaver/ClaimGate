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
    # rows show the verdict reaching the notice unchanged, including the
    # one that would tempt a blocker. NOT_IN_FORCE is a fact for the
    # coverage reviewer, not a reason intake may hold the notice: the
    # reporter has given notice, and the acknowledgment clock is running.
    Scenario Outline: The term verdict is an attribute, whatever it says
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
        | 2025-01-15 | 2026-01-15 | NOT_IN_FORCE | 2025-01-15               |

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
