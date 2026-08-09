Feature: SIU indicators
  As a claims intake system
  I need to record factual observations about a candidate First Notice of Loss
  So that a trained investigator can review them and decide what, if anything,
  they mean

  # The system records observations. It does not identify fraud, does not
  # identify fraud-prone patterns, and reaches no conclusion about any claim
  # or claimant. See PHASE2_DESIGN.md's "SIU handling" section.

  Rule: Late reporting is evaluated against a threshold supplied by the caller

    # Thresholds are never a domain default - same pattern as "now". No
    # late-reporting threshold has been agreed (see ASSUMPTIONS.md: the 30-day
    # value was orphaned against the deleted 365-day validation gate and fires
    # against Florida's 1-year statutory notice window). It ships unconfigured
    # until a real value is supplied, and absence of a value is never read as
    # "not late."
    Scenario: No late reporting threshold configured
      Given today is "2026-08-02"
      And the loss date is "2025-01-01"
      And no late reporting threshold is configured
      When SIU indicators are computed for the candidate FNOL record
      Then the late reporting indicator is NOT_EVALUATED with reason NO_THRESHOLD_CONFIGURED

    # Illustrative only: no late-reporting threshold has been approved (see
    # above). 30 exists here solely to prove the mechanism resolves TRUE/FALSE
    # correctly on both sides of a supplied boundary - it is not a proposed
    # value.
    Scenario Outline: Late reporting threshold, given an illustrative configured value
      Given today is "2026-08-02"
      And the loss date is "<loss_date>"
      And the late reporting threshold is 30 days
      When SIU indicators are computed for the candidate FNOL record
      Then the late reporting indicator is <result>

      Examples:
        | loss_date  | result |
        | 2026-07-03 | FALSE  |
        | 2026-07-02 | TRUE   |
        | 2026-07-28 | FALSE  |
        | 2026-05-04 | TRUE   |
        | 2025-06-28 | TRUE   |

  Rule: Recent policy inception is evaluated against a threshold supplied by the caller

    # 30 is a real, kept value here (unlike late reporting above) - within the
    # range carriers actually use for this indicator. See ASSUMPTIONS.md.
    Scenario Outline: Recent policy inception threshold
      Given the loss date is "2026-06-15"
      And the recent inception threshold is 30 days
      And the policy inception date is "<inception_date>"
      When SIU indicators are computed for the candidate FNOL record
      Then the recent policy inception indicator is <result>

      Examples:
        | inception_date | result |
        | 2026-06-15      | TRUE   |
        | 2026-05-16      | TRUE   |
        | 2026-05-15      | FALSE  |
        | 2026-06-10      | TRUE   |
        | 2026-03-17      | FALSE  |

  Rule: Recent policy inception requires a known inception date

    # policy_inception_date has no source at intake and is probably not
    # reporter-knowable at all until phase 3 (ASSUMPTIONS.md). Its absence is
    # never read as "not recent."
    Scenario: No policy inception date known
      Given the loss date is "2026-06-15"
      And the recent inception threshold is 30 days
      And no policy inception date is known
      When SIU indicators are computed for the candidate FNOL record
      Then the recent policy inception indicator is NOT_EVALUATED with reason NO_POLICY_INCEPTION_DATE

  Rule: An inception date after the loss date does not indicate recent inception

    # Specifies the existing 0 <= guard in _is_recent_inception, found by
    # mutation testing during the triage.feature reopening (ASSUMPTIONS.md,
    # QUEUE.md item 2) - this does not change behavior. Every input is
    # present here; they simply describe an impossible situation, so the
    # honest answer is FALSE, not NOT_EVALUATED. Whether a loss predating its
    # policy's inception is itself a coverage problem is a separate, larger
    # question needing phase-3 policy data - not built here.
    Scenario: An inception date later than the loss date does not fire the indicator
      Given the loss date is "2026-06-15"
      And the recent inception threshold is 30 days
      And the policy inception date is "2026-06-20"
      When SIU indicators are computed for the candidate FNOL record
      Then the recent policy inception indicator is FALSE

  Rule: Both indicators can fire at once; there is no combined or escalated indicator

    # Both thresholds below are supplied for this scenario; the late-reporting
    # value remains illustrative only, per the rule above.
    Scenario: Both SIU indicators fire together
      Given today is "2026-08-02"
      And the loss date is "2026-07-01"
      And the late reporting threshold is 30 days
      And the recent inception threshold is 30 days
      And the policy inception date is "2026-06-20"
      When SIU indicators are computed for the candidate FNOL record
      Then the late reporting indicator is TRUE
      And the recent policy inception indicator is TRUE
      And no other SIU indicator is present
