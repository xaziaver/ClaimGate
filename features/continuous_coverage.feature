Feature: Continuous coverage - how long the risk has been covered without a lapse
  As a claims intake system
  I need the date from which coverage on the risk was continuous as of the loss date
  So that the recent-inception SIU indicator evaluates against a real date
  instead of resolving NOT_EVALUATED on every notice

  # Semantics ratified 2026-08-14 (ASSUMPTIONS.md, "Data we do not have at
  # intake"), location moved into the domain 2026-09-01, and stated as of the
  # loss date 2026-09-04: continuous coverage on the risk survives back-to-back
  # renewal, administrative rewrite, retroactive reinstatement, and a seamless
  # takeout from a prior carrier, and is reset by a genuine lapse to the date
  # coverage resumed. The derivation reads the unbroken run of coverage in force
  # on the loss date; what the history records after that day cannot change it.
  # The port supplies term history; this rule derives. A derivation that cannot
  # be concluded from the supplied history is NOT_EVALUATED with a reason -
  # never a guess in either direction.

  Rule: Unbroken terms extend continuous coverage back to the earliest of them

    Scenario: A single term
      Given a policy term effective "2026-01-15" and expiring "2027-01-15"
      When the continuous-coverage derivation runs for a loss dated "2026-08-03"
      Then the continuous-coverage date is "2026-01-15"

    Scenario: Three back-to-back renewals
      Given a policy term effective "2023-02-01" and expiring "2024-02-01"
      And a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      When the continuous-coverage derivation runs for a loss dated "2025-09-12"
      Then the continuous-coverage date is "2023-02-01"

    Scenario Outline: A second term that renews seamlessly continues; one that leaves any gap resets
      # Terms end at 12:01 a.m. on the expiration date, so a renewal effective
      # even one day later left the risk uncovered for that day.
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "<second_effective>" and expiring "2026-03-15"
      When the continuous-coverage derivation runs for a loss dated "2025-10-05"
      Then the continuous-coverage date is "<continuous_since>"

      Examples:
        | second_effective | continuous_since |
        | 2025-02-01       | 2024-02-01       |
        | 2025-02-02       | 2025-02-02       |
        | 2025-03-15       | 2025-03-15       |

    Scenario: Two lapses; only the most recent one before the loss resets
      Given a policy term effective "2021-04-01" and expiring "2022-04-01"
      And a policy term effective "2022-05-01" and expiring "2023-05-01"
      And a policy term effective "2023-05-01" and expiring "2024-05-01"
      And a policy term effective "2024-06-01" and expiring "2025-06-01"
      And a policy term effective "2025-06-01" and expiring "2026-06-01"
      When the continuous-coverage derivation runs for a loss dated "2025-11-14"
      Then the continuous-coverage date is "2024-06-01"

  Rule: The derivation is as of the loss date; what happened to the policy afterwards does not count

    Scenario: A lapse and reinstatement after the loss date leave the date unchanged
      # A late-reported loss on a policy that lapsed after it. The run of
      # coverage the loss fell in began in 2024; the later lapse is not its.
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      And the term was cancelled effective "2025-09-01"
      And the term was reinstated effective "2025-10-15"
      When the continuous-coverage derivation runs for a loss dated "2025-04-18"
      Then the continuous-coverage date is "2024-02-01"

    Scenario: A loss dated inside a lapse has no run of coverage to derive from
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      And the term was cancelled effective "2025-09-01"
      And the term was reinstated effective "2025-10-15"
      When the continuous-coverage derivation runs for a loss dated "2025-09-20"
      Then the continuous-coverage derivation is "NOT_EVALUATED" with reason "NO_COVERAGE_ON_LOSS_DATE"

    Scenario: A loss dated after a cancellation that was never reinstated
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      And the term was cancelled effective "2025-06-10"
      When the continuous-coverage derivation runs for a loss dated "2025-08-01"
      Then the continuous-coverage derivation is "NOT_EVALUATED" with reason "NO_COVERAGE_ON_LOSS_DATE"

    Scenario: A loss on the day a term was cancelled belongs to the run that ended that day
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And the term was cancelled effective "2024-11-01"
      When the continuous-coverage derivation runs for a loss dated "2024-11-01"
      Then the continuous-coverage date is "2024-02-01"

    Scenario: A loss on the day coverage resumed after a lapse belongs to the run that began that day
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-03-15" and expiring "2026-03-15"
      When the continuous-coverage derivation runs for a loss dated "2025-03-15"
      Then the continuous-coverage date is "2025-03-15"

    Scenario: A loss on a seamless renewal date is inside one run
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      When the continuous-coverage derivation runs for a loss dated "2025-02-01"
      Then the continuous-coverage date is "2024-02-01"

  Rule: An administrative rewrite and a retroactive reinstatement continue coverage; a lapsed reinstatement resets it

    Scenario: A mid-term rewrite on the day of cancellation
      # The cancelled term keeps its nominal expiration in the source record;
      # days in force do not overlap, and coverage never broke.
      Given a policy term effective "2024-06-10" and expiring "2025-06-10"
      And the term was cancelled effective "2024-11-01"
      And a policy term effective "2024-11-01" and expiring "2025-11-01"
      When the continuous-coverage derivation runs for a loss dated "2025-03-03"
      Then the continuous-coverage date is "2024-06-10"

    Scenario: A cancellation rescinded by retroactive reinstatement
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      And the term was cancelled effective "2025-06-10"
      And the term was reinstated retroactively as of "2025-06-10"
      When the continuous-coverage derivation runs for a loss dated "2025-11-02"
      Then the continuous-coverage date is "2024-02-01"

    Scenario: A reinstatement that left a lapse
      Given a policy term effective "2024-02-01" and expiring "2025-02-01"
      And a policy term effective "2025-02-01" and expiring "2026-02-01"
      And the term was cancelled effective "2025-06-10"
      And the term was reinstated effective "2025-07-20"
      When the continuous-coverage derivation runs for a loss dated "2025-11-02"
      Then the continuous-coverage date is "2025-07-20"

  Rule: Coverage assumed from a prior carrier continues if the takeout was seamless

    Scenario Outline: A takeout with no uncovered day carries the prior carrier's date; one with a gap does not
      # Depopulation and assumption business: the source records the prior
      # carrier's coverage on the risk as a data point. It is not a reset.
      Given the source records coverage on the risk by a prior carrier effective "2017-05-20" and ending "<prior_ending>"
      And a policy term effective "2023-02-01" and expiring "2024-02-01"
      And a policy term effective "2024-02-01" and expiring "2025-02-01"
      When the continuous-coverage derivation runs for a loss dated "2024-07-09"
      Then the continuous-coverage date is "<continuous_since>"

      Examples:
        | prior_ending | continuous_since |
        | 2023-02-01   | 2017-05-20       |
        | 2023-01-31   | 2023-02-01       |

    Scenario: A prior carrier's coverage that ended after this carrier's began still continues
      # A prior policy cancelled a few days after the takeout term took effect:
      # overlapping days are covered days.
      Given the source records coverage on the risk by a prior carrier effective "2017-05-20" and ending "2023-02-10"
      And a policy term effective "2023-02-01" and expiring "2024-02-01"
      When the continuous-coverage derivation runs for a loss dated "2023-09-30"
      Then the continuous-coverage date is "2017-05-20"

  Rule: A history that may not reach the beginning of the run cannot conclude

    # "Supplies history from" a date means every term in force on or after that
    # date is supplied; terms that ended before it may be missing. Concluding a
    # date on or before it would understate continuity, and understating it is
    # what makes the recent-inception indicator fire falsely. The test is on
    # the derived date, not on the earliest supplied term.

    Scenario: The run starts where the source's history starts
      Given the source supplies history from "2020-01-01" onward
      And a policy term effective "2020-01-01" and expiring "2021-01-01"
      And a policy term effective "2021-01-01" and expiring "2022-01-01"
      When the continuous-coverage derivation runs for a loss dated "2021-06-15"
      Then the continuous-coverage derivation is "NOT_EVALUATED" with reason "HISTORY_MAY_PREDATE_SOURCE"

    Scenario: The run starts the day after the source's history starts
      # Any earlier seamless term would have expired on this date, so it was in
      # force on the day history starts and would have been supplied.
      Given the source supplies history from "2020-01-01" onward
      And a policy term effective "2020-01-02" and expiring "2021-01-02"
      When the continuous-coverage derivation runs for a loss dated "2020-09-09"
      Then the continuous-coverage date is "2020-01-02"

    Scenario: The run starts before the source's history starts
      # A legacy conversion migrates the term in force with its true effective
      # date. That term is well-formed; what it cannot say is whether another
      # preceded it.
      Given the source supplies history from "2020-01-01" onward
      And a policy term effective "2019-06-01" and expiring "2020-06-01"
      And a policy term effective "2020-06-01" and expiring "2021-06-01"
      When the continuous-coverage derivation runs for a loss dated "2021-03-03"
      Then the continuous-coverage derivation is "NOT_EVALUATED" with reason "HISTORY_MAY_PREDATE_SOURCE"

    Scenario: A term from before the source's history stops mattering once a lapse resets
      Given the source supplies history from "2020-01-01" onward
      And a policy term effective "2019-06-01" and expiring "2020-06-01"
      And a policy term effective "2020-09-01" and expiring "2021-09-01"
      When the continuous-coverage derivation runs for a loss dated "2021-05-05"
      Then the continuous-coverage date is "2020-09-01"

    Scenario: The run starts well after the source's history starts
      Given the source supplies history from "2020-01-01" onward
      And a policy term effective "2022-05-01" and expiring "2023-05-01"
      When the continuous-coverage derivation runs for a loss dated "2022-11-11"
      Then the continuous-coverage date is "2022-05-01"

    Scenario: A loss dated before the source's history starts may have been covered by a term it cannot see
      Given the source supplies history from "2020-01-01" onward
      And a policy term effective "2020-03-01" and expiring "2021-03-01"
      When the continuous-coverage derivation runs for a loss dated "2019-11-11"
      Then the continuous-coverage derivation is "NOT_EVALUATED" with reason "HISTORY_MAY_PREDATE_SOURCE"

    Scenario: A loss dated in a gap after the source's history starts is a gap the source can see
      Given the source supplies history from "2020-01-01" onward
      And a policy term effective "2020-03-01" and expiring "2021-03-01"
      And a policy term effective "2021-04-01" and expiring "2022-04-01"
      When the continuous-coverage derivation runs for a loss dated "2021-03-15"
      Then the continuous-coverage derivation is "NOT_EVALUATED" with reason "NO_COVERAGE_ON_LOSS_DATE"

    Scenario: Term history could not be obtained
      Given the policy's term history could not be obtained, with reason "SOURCE_UNAVAILABLE"
      When the continuous-coverage derivation runs for a loss dated "2025-08-01"
      Then the continuous-coverage derivation is "NOT_EVALUATED" with reason "SOURCE_UNAVAILABLE"
