Feature: Coverage verification - term in force at the loss date
  As a claims intake system
  I need to determine whether a term of the identified policy was in force
  on the reported loss date
  So that downstream coverage review starts from a recorded, dated answer

  # Verification, not determination. This rule answers whether a term was
  # in force on the loss date. Whether the policy covers the loss - perils,
  # exclusions, endorsements, limits - is coverage determination, which is
  # permanently out of scope (ROADMAP.md). The result is an attribute of a
  # TRIAGED notice and never blocks, delays, or refuses a notice.
  #
  # Why BOUNDARY_DAY exists: residential property terms conventionally
  # incept and expire at 12:01 a.m. standard time at the described
  # property, and intake captures a loss date, not an instant. On a date
  # that is a coverage boundary, the answer turns on the time of loss,
  # which intake does not hold. Reporting a third value instead of picking
  # a side is the standing rule: a result not computed is never reported
  # as a negative.

  Rule: A loss inside an active term is in force; outside every term it is not

    Scenario Outline: A single term with no status changes
      Given a policy term effective "2026-01-15" and expiring "2027-01-15"
      When the in-force determination runs for a loss dated "<loss_date>"
      Then the determination is "<determination>"

      Examples:
        | loss_date  | determination |
        | 2026-01-14 | NOT_IN_FORCE  |
        | 2026-01-15 | BOUNDARY_DAY  |
        | 2026-01-16 | IN_FORCE      |
        | 2026-07-04 | IN_FORCE      |
        | 2027-01-14 | IN_FORCE      |
        | 2027-01-15 | BOUNDARY_DAY  |
        | 2027-01-16 | NOT_IN_FORCE  |

    Scenario Outline: Two terms separated by a gap in coverage
      # Non-renewed, then rewritten six weeks later. The gap is real:
      # no term covers it, so a loss inside it is NOT_IN_FORCE, not a
      # boundary question.
      Given a policy term effective "2025-01-15" and expiring "2026-01-15"
      And a policy term effective "2026-03-01" and expiring "2027-03-01"
      When the in-force determination runs for a loss dated "<loss_date>"
      Then the determination is "<determination>"

      Examples:
        | loss_date  | determination |
        | 2024-12-31 | NOT_IN_FORCE  |
        | 2026-02-01 | NOT_IN_FORCE  |
        | 2026-06-01 | IN_FORCE      |
        | 2027-04-01 | NOT_IN_FORCE  |

  Rule: A seamless renewal date is a boundary day

    # Coverage is continuous across a back-to-back renewal, but which term
    # responds turns on the loss time: forms, deductibles, and limits can
    # change at renewal. The date belongs to both terms at the granularity
    # intake holds, so it is a boundary day, not a silent pick of one term.
    Scenario: A loss on the shared date of two back-to-back terms
      Given a policy term effective "2025-06-01" and expiring "2026-06-01"
      And a policy term effective "2026-06-01" and expiring "2027-06-01"
      When the in-force determination runs for a loss dated "2026-06-01"
      Then the determination is "BOUNDARY_DAY"

  Rule: Cancellation ends coverage at its effective date; one not yet effective at the loss date does not

    Scenario Outline: A term cancelled mid-term
      Given a policy term effective "2026-01-15" and expiring "2027-01-15"
      And the term was cancelled effective "2026-06-10"
      When the in-force determination runs for a loss dated "<loss_date>"
      Then the determination is "<determination>"

      Examples:
        | loss_date  | determination |
        | 2026-01-20 | IN_FORCE      |
        | 2026-06-09 | IN_FORCE      |
        | 2026-06-10 | BOUNDARY_DAY  |
        | 2026-06-11 | NOT_IN_FORCE  |
        | 2026-12-01 | NOT_IN_FORCE  |

  Rule: Reinstatement resumes coverage at its effective date; a retroactive reinstatement erases the lapse

    Scenario Outline: A cancelled term reinstated with a lapse
      Given a policy term effective "2026-01-15" and expiring "2027-01-15"
      And the term was cancelled effective "2026-06-10"
      And the term was reinstated effective "2026-07-20"
      When the in-force determination runs for a loss dated "<loss_date>"
      Then the determination is "<determination>"

      Examples:
        | loss_date  | determination |
        | 2026-07-01 | NOT_IN_FORCE  |
        | 2026-07-20 | BOUNDARY_DAY  |
        | 2026-07-21 | IN_FORCE      |
        | 2026-12-01 | IN_FORCE      |

    Scenario: A loss inside the erased lapse
      # The reinstatement rescinds the cancellation: coverage was
      # continuous and the lapse never existed.
      Given a policy term effective "2026-01-15" and expiring "2027-01-15"
      And the term was cancelled effective "2026-06-10"
      And the term was reinstated retroactively as of "2026-06-10"
      When the in-force determination runs for a loss dated "2026-07-01"
      Then the determination is "IN_FORCE"

    Scenario: A loss on the rescinded cancellation date itself
      # A rescinded date is not a boundary - nothing turns on the loss
      # time there, so the retroactive clause takes precedence over the
      # boundary clause. Single-probe scenarios on purpose: every row of
      # this rule is IN_FORCE by design, and a uniform outcome column
      # cannot kill in-column swaps (docs/harness-findings.md).
      Given a policy term effective "2026-01-15" and expiring "2027-01-15"
      And the term was cancelled effective "2026-06-10"
      And the term was reinstated retroactively as of "2026-06-10"
      When the in-force determination runs for a loss dated "2026-06-10"
      Then the determination is "IN_FORCE"

  Rule: The determination cites the deciding term

    Scenario: An in-force determination cites the term that was in force
      Given a policy term effective "2025-03-01" and expiring "2026-03-01"
      And a policy term effective "2026-03-01" and expiring "2027-03-01"
      When the in-force determination runs for a loss dated "2026-09-15"
      Then the determination is "IN_FORCE"
      And the determination cites the term effective "2026-03-01" and expiring "2027-03-01"

    Scenario: A not-in-force determination on a cancelled term cites that term and its cancellation
      Given a policy term effective "2026-01-15" and expiring "2027-01-15"
      And the term was cancelled effective "2026-06-10"
      When the in-force determination runs for a loss dated "2026-08-01"
      Then the determination is "NOT_IN_FORCE"
      And the determination cites the term effective "2026-01-15" and expiring "2027-01-15"
      And the determination cites the cancellation effective "2026-06-10"

  Rule: A determination that cannot be made is NOT_EVALUATED with the reason, never a negative

    Scenario: Term history could not be obtained
      Given the policy's term history could not be obtained, with reason "SOURCE_TIMEOUT"
      When the in-force determination runs for a loss dated "2026-06-01"
      Then the determination is "NOT_EVALUATED"
      And the determination reason is "SOURCE_TIMEOUT"
