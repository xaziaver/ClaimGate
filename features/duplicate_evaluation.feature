Feature: Duplicate detection at intake - what the notice carries about the claims already on its policy
  As a claims intake system
  I need to compare a triaged notice against the claims already open on the policy the search found
  So that a second report of the same loss reaches the adjuster marked as a probable duplicate,
  and a notice that could not be compared says so rather than looking clean

  # PHASE3_DESIGN.md, "Existing claims", and ASSUMPTIONS.md 2026-08-22. The
  # matching rule - same policy, a loss date within the carrier's window, the
  # same loss type - is duplicates.feature's and is not restated. This file
  # specifies its intake surface: the evaluation runs on every transition
  # into TRIAGED, on either path, against the claims the carrier's claims
  # source holds for the policy the search found; it is one structure on the
  # notice - status, candidates, reason - so a not-evaluated result and its
  # reason cannot be read apart. A PENDED notice carries no evaluation: the
  # comparison is made when the notice is triaged, on what it carries then.
  #
  # Two families of reason. The rule's own - FOLLOW_ON_NOTICE_TYPE,
  # NO_EXISTING_CLAIM_NOTICE_TYPE - when the rule declines to compare; and,
  # when the shell never asked the rule because there was no policy to ask
  # about or the source could not answer, the reason the coverage
  # verification already carries for the same failure. A result not
  # computed is never reported as "no duplicates".

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

  Rule: A triaged notice is compared against the claims on the policy the search found

    # The window is the carrier's 60 days and the type must agree; the rule
    # is locked elsewhere. Two tables, one column each: a row where the date
    # and the type are both wrong would leave either column inert to
    # mutation, so each table varies one thing and holds the other.
    Scenario Outline: A claim inside the window is a candidate; one outside is not
      Given "AAAA"'s claims source holds claim "CLM-1001" on policy "POL-88213" with loss date "<held_loss_date>" and loss type "wind_hail"
      And the notice reports a policy number of "HO-4471209"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the duplicate evaluation is OBTAINED
      And the duplicate candidates are <candidates>

      Examples:
        | held_loss_date | candidates |
        | 2026-05-20     | CLM-1001   |
        | 2026-03-01     | none       |

    Scenario Outline: A claim of the same loss type is a candidate; one of another type is not
      Given "AAAA"'s claims source holds claim "CLM-1001" on policy "POL-88213" with loss date "2026-05-20" and loss type "<held_loss_type>"
      And the notice reports a policy number of "HO-4471209"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the duplicate evaluation is OBTAINED
      And the duplicate candidates are <candidates>

      Examples:
        | held_loss_type | candidates |
        | wind_hail      | CLM-1001   |
        | fire           | none       |

    # The rule declines a follow-on notice itself; its reason reaches the
    # notice unchanged. INITIAL is the row that proves the structure carries
    # candidates when the rule did compare.
    Scenario Outline: The rule's own refusal to compare reaches the notice with its reason
      Given "AAAA"'s claims source holds claim "CLM-1001" on policy "POL-88213" with loss date "2026-05-20" and loss type "wind_hail"
      And the notice reports a policy number of "HO-4471209"
      And the notice reports a notice type of "<notice_type>"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the duplicate evaluation is <status>
      And the duplicate evaluation's reason is <reason>

      Examples:
        | notice_type  | status        | reason                |
        | INITIAL      | OBTAINED      | none                  |
        | SUPPLEMENTAL | NOT_EVALUATED | FOLLOW_ON_NOTICE_TYPE |

    # The search found the policy on the insured name and postal code; the
    # number the reporter typed is wrong. The comparison is against the
    # claims on the policy that was found, not the number that was typed,
    # so the existing claim is still a candidate.
    Scenario: A notice matched on the pair is compared against the found policy's claims, not the typed number
      Given "AAAA"'s claims source holds claim "CLM-1001" on policy "POL-88213" with loss date "2026-05-20" and loss type "wind_hail"
      And the notice reports a policy number of "HO-4471290"
      And the notice reports an insured name of "Marisol Quintero"
      And the notice reports a risk postal code of "34287"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the policy was identified on INSURED_NAME_AND_POSTAL_CODE
      And the duplicate candidates are CLM-1001

  Rule: A notice that could not be compared says why, and a pended notice is compared when it is triaged

    # The one fixture stands in for both sources, so a fault on it is felt by
    # the search first: there is no policy to ask about, and the evaluation
    # carries the reason the verification carries. The claims-side fault is
    # the case where the policy was found and the claims could not be read.
    Scenario Outline: A source fault leaves the evaluation not evaluated, with the verification's reason
      Given "AAAA"'s policy source <fault>
      And the notice reports a policy number of "HO-4471209"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the duplicate evaluation is NOT_EVALUATED
      And the duplicate evaluation's reason is <reason>

      Examples:
        | fault                                  | reason             |
        | is unavailable                         | SOURCE_UNAVAILABLE |
        | does not answer within its budget      | SOURCE_TIMEOUT     |
        | answers in a shape that is not its own | SOURCE_MALFORMED   |

    Scenario: The policy was found but its claims could not be read
      Given "AAAA"'s claims source holds claim "CLM-1001" on policy "POL-88213" with loss date "2026-05-20" and loss type "wind_hail"
      And "AAAA"'s claims source is unavailable
      And the notice reports a policy number of "HO-4471209"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the notice's policy match is MATCHED
      And the duplicate evaluation is NOT_EVALUATED
      And the duplicate evaluation's reason is SOURCE_UNAVAILABLE

    # The comparison belongs to the transition into TRIAGED, on either path.
    # While the notice pends on a wrong number there is nothing to compare
    # against; when the reviewer's correction finds the policy, the claims
    # on it are read then.
    Scenario: A pended notice carries no evaluation, and is compared when the reviewer's correction triages it
      Given "AAAA"'s claims source holds claim "CLM-1001" on policy "POL-88213" with loss date "2026-05-20" and loss type "wind_hail"
      And the notice reports a policy number of "HO-4471290"
      And the notice is submitted for intake
      And the notice's state is PENDED
      And the notice has no duplicate evaluation
      When the reviewer supplies a policy number of "HO-4471209"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is 200
      And the notice's state is TRIAGED
      And the duplicate evaluation is OBTAINED
      And the duplicate candidates are CLM-1001
