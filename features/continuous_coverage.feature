Feature: Continuous coverage - how long the risk has been covered without a lapse
  As a claims intake system
  I need the date from which coverage on the risk has been continuous
  So that the recent-inception SIU indicator evaluates against a real date
  instead of resolving NOT_EVALUATED on every notice

  # Semantics ratified 2026-08-14 (ASSUMPTIONS.md, "Data we do not have at
  # intake"), location moved into the domain 2026-09-01: continuous coverage
  # on the risk survives back-to-back renewal, administrative rewrite, and
  # retroactive reinstatement, and is reset by a genuine lapse to the date
  # coverage resumed. The port supplies term history; this rule derives.
  # A derivation that cannot be concluded from the supplied history is
  # NOT_EVALUATED with a reason - never a guess in either direction.

  Rule: Unbroken terms extend continuous coverage back to the earliest of them

    Scenario: A single term
      Given a policy term effective "2026-01-15" and expiring "2027-01-15"
      When the continuous-coverage derivation runs
      Then the continuous-coverage date is "2026-01-15"

    Scenario: Three back-to-back renewals
      Given a policy term effective "2023-02-01" and expiring "2024-02-01"
      And a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      When the continuous-coverage derivation runs
      Then the continuous-coverage date is "2023-02-01"

    Scenario Outline: A second term that renews seamlessly continues; one that leaves a gap resets
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "<second_effective>" and expiring "2026-03-15"
      When the continuous-coverage derivation runs
      Then the continuous-coverage date is "<continuous_since>"

      Examples:
        | second_effective | continuous_since |
        | 2025-02-01       | 2024-02-01       |
        | 2025-03-15       | 2025-03-15       |

  Rule: An administrative rewrite and a retroactive reinstatement continue coverage; a lapsed reinstatement resets it

    Scenario: A mid-term rewrite on the day of cancellation
      # The cancelled term keeps its nominal expiration in the source record;
      # days in force do not overlap, and coverage never broke.
      Given a policy term effective "2024-06-10" and expiring "2025-06-10"
      And the term was cancelled effective "2024-11-01"
      And a policy term effective "2024-11-01" and expiring "2025-11-01"
      When the continuous-coverage derivation runs
      Then the continuous-coverage date is "2024-06-10"

    Scenario: A cancellation rescinded by retroactive reinstatement
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      And the term was cancelled effective "2025-06-10"
      And the term was reinstated retroactively as of "2025-06-10"
      When the continuous-coverage derivation runs
      Then the continuous-coverage date is "2024-02-01"

    Scenario: A reinstatement that left a lapse
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      And the term was cancelled effective "2025-06-10"
      And the term was reinstated effective "2025-07-20"
      When the continuous-coverage derivation runs
      Then the continuous-coverage date is "2025-07-20"

  Rule: A history that may not reach the beginning of coverage cannot conclude

    Scenario: The earliest supplied term starts where the source's history starts
      # Coverage may extend earlier than the source can see; concluding the
      # earliest visible date would understate continuity, and understating
      # it is what makes the recent-inception indicator fire falsely.
      Given the source supplies history from "2020-01-01" onward
      And a policy term effective "2020-01-01" and expiring "2021-01-01"
      And a policy term effective "2021-01-01" and expiring "2022-01-01"
      When the continuous-coverage derivation runs
      Then the continuous-coverage derivation is "NOT_EVALUATED" with reason "HISTORY_MAY_PREDATE_SOURCE"

    Scenario: The earliest supplied term starts after the source's history starts
      Given the source supplies history from "2020-01-01" onward
      And a policy term effective "2022-05-01" and expiring "2023-05-01"
      When the continuous-coverage derivation runs
      Then the continuous-coverage date is "2022-05-01"

    Scenario: Term history could not be obtained
      Given the policy's term history could not be obtained, with reason "SOURCE_UNAVAILABLE"
      When the continuous-coverage derivation runs
      Then the continuous-coverage derivation is "NOT_EVALUATED" with reason "SOURCE_UNAVAILABLE"
