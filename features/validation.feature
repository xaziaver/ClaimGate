Feature: FNOL validation
  As a claims intake system
  I need to validate a candidate First Notice of Loss record
  So that only claims the carrier can legally accept enter the queue

  Background:
    Given today is "2026-08-02"
    And the record is otherwise valid

  Rule: The loss date must not be in the future and must be reported within 365 days

    Scenario Outline: Loss date acceptable window relative to today
      Given the loss date is "<loss_date>"
      When the candidate FNOL record is validated
      Then the validation result is "<result>"

      Examples:
        | loss_date  | result  |
        | 2026-08-03 | invalid |
        | 2026-08-02 | valid   |
        | 2026-08-01 | valid   |
        | 2025-08-02 | valid   |
        | 2025-08-01 | invalid |

  Rule: The policy number must have a recognized line-of-business prefix and a 7-digit number

    Scenario Outline: Policy number format
      Given the policy number is "<policy_number>"
      When the candidate FNOL record is validated
      Then the validation result is "<result>"

      Examples:
        | policy_number | result  |
        | HO-1234567    | valid   |
        | AU-1234567    | valid   |
        | CP-1234567    | valid   |
        | CA-1234567    | valid   |
        | GL-1234567    | valid   |
        | XX-1234567    | invalid |
        | HO-123456     | invalid |
        | HO-12345678   | invalid |
        | ho-1234567    | invalid |
        | HO1234567     | invalid |
        | HO-ABCDEFG    | invalid |

  Rule: Injury losses require injured-party details

    Scenario Outline: Required fields for an injury loss
      Given the loss type is "injury"
      And the injured party name is "<name>"
      And the injured party contact is "<contact>"
      And the injury description is "<description>"
      When the candidate FNOL record is validated
      Then the validation result is "<result>"
      And the missing field reported is "<missing_field>"

      Examples:
        | name     | contact  | description               | result  | missing_field         |
        | Jane Doe | 555-0100 | Twisted ankle, wet floor  | valid   | none                  |
        |          | 555-0100 | Twisted ankle, wet floor  | invalid | injured_party_name    |
        | Jane Doe |          | Twisted ankle, wet floor  | invalid | injured_party_contact |
        | Jane Doe | 555-0100 |                           | invalid | injury_description    |

    Scenario: Non-injury losses do not require injured-party details
      Given the loss type is "fire"
      And no injured-party details are provided
      When the candidate FNOL record is validated
      Then the validation result is "valid"
