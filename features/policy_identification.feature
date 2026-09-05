Feature: Policy identification - whether a notice carries enough to search for its policy
  As a claims intake system
  I need to know whether the identifiers a notice carries can find its policy
  So that a notice with enough to search on proceeds to the search
  and one without pends for a reviewer to supply what is missing

  # PHASE3_DESIGN.md, "Identifiers: search, not fetch". The notice can be
  # searched if it carries a policy number, or an insured name together with
  # the risk postal code. Otherwise the blocker POLICY_IDENTIFIERS_INSUFFICIENT,
  # naming every identifier field that is absent so the reviewer resolving the
  # pend knows what to ask for. This rule reads the notice and nothing else: no
  # search runs here, and no identifier is checked for shape - a mistyped
  # number beside a correct name and postal code is a search, not a pend.
  # POLICY_NOT_MATCHED and POLICY_AMBIGUOUS are the search's outcomes, not
  # this rule's.

  Rule: A policy number alone is enough; an insured name and a risk postal code together are enough

    Scenario: A policy number and nothing else
      Given the policy number is "HO-4471209"
      And the insured name is ""
      And the risk postal code is ""
      When identifier sufficiency is evaluated
      Then the notice is searchable on "POLICY_NUMBER"
      And the search carries policy number "HO-4471209"
      And the search carries no insured name and no risk postal code

    Scenario: An insured name and a risk postal code, no policy number
      # A public adjuster or contractor reporting for the insured rarely has
      # the policy number and usually has the name and the address.
      Given the policy number is ""
      And the insured name is "Marisol Quintero"
      And the risk postal code is "34287"
      When identifier sufficiency is evaluated
      Then the notice is searchable on "INSURED_NAME_AND_POSTAL_CODE"
      And the search carries insured name "Marisol Quintero" and risk postal code "34287"
      And the search carries no policy number

    Scenario: All three identifiers
      Given the policy number is "HO-4471209"
      And the insured name is "Marisol Quintero"
      And the risk postal code is "34287"
      When identifier sufficiency is evaluated
      Then the notice is searchable on "POLICY_NUMBER;INSURED_NAME_AND_POSTAL_CODE"
      And the search carries policy number "HO-4471209"
      And the search carries insured name "Marisol Quintero" and risk postal code "34287"

    Scenario Outline: Anything less is insufficient, and the blocker names what is absent
      Given the policy number is "<policy_number>"
      And the insured name is "<insured_name>"
      And the risk postal code is "<risk_postal_code>"
      When identifier sufficiency is evaluated
      Then the identification blocker is "<blocker>"

      Examples:
        | policy_number | insured_name     | risk_postal_code | blocker                                                                |
        |               | Marisol Quintero |                  | POLICY_IDENTIFIERS_INSUFFICIENT:policy_number;risk_postal_code         |
        |               |                  | 34287-2210       | POLICY_IDENTIFIERS_INSUFFICIENT:policy_number;insured_name             |
        |               |                  |                  | POLICY_IDENTIFIERS_INSUFFICIENT:policy_number;insured_name;risk_postal_code |

  Rule: An identifier is carried as given, trimmed, and whitespace alone is absent

    Scenario: A policy number pasted with surrounding whitespace
      Given the policy number is "  HO-4471209 "
      And the insured name is ""
      And the risk postal code is ""
      When identifier sufficiency is evaluated
      Then the notice is searchable on "POLICY_NUMBER"
      And the search carries policy number "HO-4471209"

    Scenario: A whitespace-only policy number beside a name and postal code
      Given the policy number is "   "
      And the insured name is "Marisol Quintero"
      And the risk postal code is "34287"
      When identifier sufficiency is evaluated
      Then the notice is searchable on "INSURED_NAME_AND_POSTAL_CODE"
      And the search carries no policy number

    Scenario: A whitespace-only risk postal code beside an insured name
      Given the policy number is ""
      And the insured name is "Marisol Quintero"
      And the risk postal code is "   "
      When identifier sufficiency is evaluated
      Then the identification blocker is "POLICY_IDENTIFIERS_INSUFFICIENT:policy_number;risk_postal_code"

    Scenario: A nine-digit postal code is carried as given, not reshaped
      Given the policy number is ""
      And the insured name is "Marisol Quintero"
      And the risk postal code is "34287-2210"
      When identifier sufficiency is evaluated
      Then the notice is searchable on "INSURED_NAME_AND_POSTAL_CODE"
      And the search carries insured name "Marisol Quintero" and risk postal code "34287-2210"

    Scenario: A policy number of unfamiliar shape is a search, not a pend
      # The line-of-business prefix check is retired at item 7d; this rule
      # never had one. Whether the number finds a policy is the search's answer.
      Given the policy number is "7Q-000012"
      And the insured name is ""
      And the risk postal code is ""
      When identifier sufficiency is evaluated
      Then the notice is searchable on "POLICY_NUMBER"
      And the search carries policy number "7Q-000012"
