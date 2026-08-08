Feature: FNOL triage
  As a claims intake system
  I need to assign a severity and route each loss to a queue
  So that adjusters and SIU see the right claims in the right order

  Rule: Severity is assigned from loss type

    Scenario Outline: Severity by loss type
      Given the loss type is "<loss_type>"
      When the candidate FNOL record is triaged
      Then the assigned severity is "<severity>"

      Examples:
        | loss_type          | severity |
        | injury              | high     |
        | fire                | high     |
        | water_damage        | standard |
        | wind_hail           | standard |
        | vandalism           | standard |
        | liability           | standard |
        | auto_collision      | standard |
        | auto_comprehensive  | standard |

  Rule: Theft severity depends on the loss amount

    Scenario Outline: Theft severity by loss amount
      Given the loss type is "theft"
      And the loss amount is <loss_amount>
      When the candidate FNOL record is triaged
      Then the assigned severity is "<severity>"

      Examples:
        | loss_amount | severity |
        | 499.99      | low      |
        | 500.00      | standard |
        | 500.01      | standard |

  Rule: Queue is derived from severity, but any SIU flag overrides it to siu_review

    Scenario Outline: Queue routing
      Given the assigned severity is "<severity>"
      And the late reporting SIU flag is <late_reporting>
      And the recent policy inception SIU flag is <recent_inception>
      When the candidate FNOL record is routed to a queue
      Then the routed queue is "<queue>"
      And the severity recorded on the record is "<severity>"

      Examples:
        | severity | late_reporting | recent_inception | queue      |
        | low      | false           | false             | fast_track |
        | standard | false           | false             | standard   |
        | high     | false           | false             | complex    |
        | low      | true            | false             | siu_review |
        | standard | false           | true              | siu_review |
        | high     | true            | true              | siu_review |


  Rule: A record is triaged and routed end to end

    Scenario Outline: From raw record to queue
      Given today is "2026-08-02"
      And a candidate with loss type "<loss_type>", loss amount <loss_amount>, loss date "<loss_date>", and policy inception date "<inception_date>"
      When the candidate FNOL record is triaged and routed
      Then the assigned severity is "<severity>"
      And the routed queue is "<queue>"

      Examples:
        | loss_type    | loss_amount | loss_date  | inception_date | severity | queue      |
        | theft        | 400.00      | 2026-08-01 | 2024-01-01     | low      | fast_track |
        | theft        | 400.00      | 2026-06-15 | 2024-01-01     | low      | siu_review |
        | fire         | 50000       | 2026-08-01 | 2024-01-01     | high     | complex    |
        | fire         | 50000       | 2026-08-01 | 2026-07-20     | high     | siu_review |
        | water_damage | 400.00      | 2026-08-01 | 2024-01-01     | standard | standard   |