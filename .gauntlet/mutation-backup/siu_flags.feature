Feature: SIU fraud indicators
  As a claims intake system
  I need to flag fraud-prone patterns on a candidate FNOL record
  So that SIU can review them regardless of whether the claim is otherwise valid

  Rule: Late reporting fires when the claim is reported more than 30 days after the loss

    Scenario Outline: Late reporting threshold
      Given today is "2026-08-02"
      And the loss date is "<loss_date>"
      When SIU flags are computed for the candidate FNOL record
      Then the late reporting flag is <late_reporting>

      Examples:
        | loss_date  | late_reporting |
        | 2026-07-03 | false           |
        | 2026-07-02 | true            |
        | 2026-07-28 | false           |
        | 2026-05-04 | true            |
        | 2025-06-28 | true            |

  Rule: Recent policy inception fires when the policy started within 30 days of the loss

    Scenario Outline: Recent policy inception threshold
      Given the loss date is "2026-06-15"
      And the policy inception date is "<inception_date>"
      When SIU flags are computed for the candidate FNOL record
      Then the recent policy inception flag is <recent_inception>

      Examples:
        | inception_date | recent_inception |
        | 2026-06-15      | true              |
        | 2026-05-16      | true              |
        | 2026-05-15      | false             |
        | 2026-06-10      | true              |
        | 2026-03-17      | false             |

  Rule: Both indicators can be present at once with no additional escalated flag

    Scenario: Both SIU indicators fire together
      Given today is "2026-08-02"
      And the loss date is "2026-07-01"
      And the policy inception date is "2026-06-20"
      When SIU flags are computed for the candidate FNOL record
      Then the late reporting flag is true
      And the recent policy inception flag is true
      And no other SIU flag is present
