Feature: FNOL triage
  As a claims intake system
  I need to assign a severity and route each loss to a queue
  So that adjusters see the right claims in the right order

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

  Rule: Queue is derived from severity alone

    Scenario Outline: Queue routing
      Given the assigned severity is "<severity>"
      When the candidate FNOL record is routed to a queue
      Then the routed queue is "<queue>"

      Examples:
        | severity | queue      |
        | low      | fast_track |
        | standard | standard   |
        | high     | complex    |

  Rule: A record is triaged and routed end to end; SIU indicators are recorded separately and never affect routing

    # SIU referral and claim handling are parallel, not alternative: a queue
    # named siu_review would make SIU status visible in ordinary routing data,
    # which is exactly the leak the restricted-attribute design exists to
    # prevent. These examples cover severity alone, one indicator firing, and
    # both firing at once, and the queue never changes from what severity
    # alone would produce. The final example gives no policy inception date
    # at all, proving the invariant holds when an indicator is NOT_EVALUATED,
    # not only when it is TRUE or FALSE - the configuration this system
    # actually ships with (see siu_indicators.feature).
    #
    # The thresholds below are supplied by the caller, per siu_indicators.feature;
    # 45 for late reporting is illustrative only, not an approved value - see
    # that file's rule for why.
    #
    # An empty inception_date cell means no policy inception date is known,
    # the same convention validation.feature uses for an empty blockers cell.
    Scenario Outline: From raw record to queue, with SIU indicators recorded separately and never affecting routing
      Given today is "2026-08-02"
      And the late reporting threshold is 45 days
      And the recent policy inception threshold is 30 days
      And a candidate with loss type "<loss_type>", loss amount <loss_amount>, loss date "<loss_date>", and policy inception date "<inception_date>"
      When the candidate FNOL record is triaged and routed
      Then the assigned severity is "<severity>"
      And the routed queue is "<queue>"
      And the late reporting indicator is <late_reporting>
      And the recent policy inception indicator is <recent_inception>

      Examples:
        | loss_type    | loss_amount | loss_date  | inception_date | severity | queue      | late_reporting | recent_inception |
        | theft        | 400.00      | 2026-08-01 | 2024-01-01     | low      | fast_track | FALSE          | FALSE            |
        | theft        | 400.00      | 2026-06-15 | 2024-01-01     | low      | fast_track | TRUE           | FALSE            |
        | fire         | 50000       | 2026-08-01 | 2024-01-01     | high     | complex    | FALSE          | FALSE            |
        | fire         | 50000       | 2026-08-01 | 2026-07-20     | high     | complex    | FALSE          | TRUE             |
        | fire         | 50000       | 2026-06-01 | 2026-05-15     | high     | complex    | TRUE           | TRUE             |
        | water_damage | 400.00      | 2026-08-01 | 2024-01-01     | standard | standard   | FALSE          | FALSE            |
        | water_damage | 400.00      | 2026-06-01 | 2026-05-15     | standard | standard   | TRUE           | TRUE             |
        | theft        | 400.00      | 2026-06-15 |                 | low      | fast_track | TRUE           | NOT_EVALUATED    |
