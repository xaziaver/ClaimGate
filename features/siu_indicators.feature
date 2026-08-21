Feature: SIU indicators
  As a claims intake system
  I need to record factual observations about a candidate First Notice of Loss
  So that a trained investigator can review them and decide what, if anything,
  they mean

  # The system records observations. It does not identify fraud, does not
  # identify fraud-prone patterns, and reaches no conclusion about any claim
  # or claimant. See PHASE2_DESIGN.md's "SIU handling" section.

  # Reason codes are a closed enumeration, like the blocker codes in
  # validation.feature: NO_THRESHOLD_CONFIGURED and NO_CONTINUOUS_COVERAGE_DATE
  # are the complete set today. Escalate before adding to it.

  Background:
    # compute_siu_indicators evaluates both indicators in one call, so `now` is
    # required even by scenarios that only assert recent policy inception. Set
    # once here so the file cannot develop two reference dates: a per-scenario
    # value can be changed in one place and missed in another, and every
    # scenario in this file is date arithmetic.
    Given today is "2026-08-02"

  Rule: Late reporting is evaluated against a threshold supplied by the caller

    # Thresholds are never a domain default - same pattern as "now". No
    # late-reporting threshold has been agreed (see ASSUMPTIONS.md: the 30-day
    # value was orphaned against the deleted 365-day validation gate and fires
    # against Florida's 1-year statutory notice window). It ships unconfigured
    # until a real value is supplied, and absence of a value is never read as
    # "not late."
    Scenario: No late reporting threshold configured
      Given the loss date is "2025-01-01"
      And no late reporting threshold is configured
      When SIU indicators are computed for the candidate FNOL record
      Then the late reporting indicator is NOT_EVALUATED with reason NO_THRESHOLD_CONFIGURED

    # Illustrative only: no late-reporting threshold has been approved (see
    # above). 45 exists here solely to prove the mechanism resolves TRUE/FALSE
    # correctly on both sides of a supplied boundary - it is not a proposed
    # value. Deliberately not 30, so it cannot be confused with the recent
    # policy inception threshold below, which is a real kept value: a single
    # shared threshold would pass every scenario in this file without the
    # implementation actually keeping the two thresholds distinct.
    Scenario Outline: Late reporting threshold, given an illustrative configured value
      Given the loss date is "<loss_date>"
      And the late reporting threshold is 45 days
      When SIU indicators are computed for the candidate FNOL record
      Then the late reporting indicator is <result>

      Examples:
        | loss_date  | result |
        | 2026-07-28 | FALSE  |
        | 2026-06-18 | FALSE  |
        | 2026-06-17 | TRUE   |
        | 2026-05-04 | TRUE   |
        | 2025-06-28 | TRUE   |

  Rule: Recent policy inception is evaluated against a threshold supplied by the caller

    # The indicator's name and its input's name differ on purpose, and that
    # is not an oversight. The indicator is named for what an investigator
    # observes: coverage obtained shortly before a reported loss. Its input,
    # the continuous coverage date, is the date continuous coverage on the
    # risk began, derived from the full term history - deliberately NOT the
    # current policy's inception date. An administrative rewrite or a takeout
    # issues a new policy number with a new inception date while coverage
    # never lapsed, so keying on the policy record's own date would fire the
    # indicator across a lawful book. The indicator name was left unchanged
    # when the input was renamed for exactly this reason. See ASSUMPTIONS.md's
    # "Data we do not have at intake."

    # 30 is a real, kept value here (unlike late reporting above) - within the
    # range carriers actually use for this indicator. See ASSUMPTIONS.md.
    Scenario Outline: Recent policy inception threshold
      Given the loss date is "2026-06-15"
      And the recent policy inception threshold is 30 days
      And the continuous coverage date is "<coverage_start>"
      When SIU indicators are computed for the candidate FNOL record
      Then the recent policy inception indicator is <result>

      Examples:
        | coverage_start | result |
        | 2026-06-15      | TRUE   |
        | 2026-05-16      | TRUE   |
        | 2026-05-15      | FALSE  |
        | 2026-06-10      | TRUE   |
        | 2026-03-17      | FALSE  |

  Rule: Recent policy inception requires a known continuous coverage date

    # The continuous coverage date is available at intake via a phase-2
    # adapter lookup against the policy administration system, not captured
    # from the reporter (see ASSUMPTIONS.md's "Data we do not have at
    # intake"). This scenario is the lookup missing - the party or risk could
    # not be resolved, or the resolved coverage history has no
    # continuous-coverage start to report - not the gap phase 1 has today,
    # where no caller supplies a date because the adapter has not been built
    # yet. Either way, absence is never read as "not recent."
    Scenario: No continuous coverage date known
      Given the loss date is "2026-06-15"
      And the recent policy inception threshold is 30 days
      And no continuous coverage date is known
      When SIU indicators are computed for the candidate FNOL record
      Then the recent policy inception indicator is NOT_EVALUATED with reason NO_CONTINUOUS_COVERAGE_DATE

  Rule: Recent policy inception is not evaluated without a threshold

    # Symmetry with the late-reporting rule above: an absent threshold is never
    # read as "not recent." Surfaced during implementation - the "No late
    # reporting threshold configured" scenario supplies no recent policy
    # inception threshold either, so the type had to admit absence, and absence
    # needed a defined result. Same reason code as late reporting: the
    # condition is "no threshold," not a late-reporting-specific fact. The
    # continuous coverage date below is 5 days before the loss and would fire
    # the indicator if a threshold were configured, so this scenario cannot
    # pass by coincidence with a FALSE result.
    Scenario: No recent policy inception threshold configured
      Given the loss date is "2026-06-15"
      And no recent policy inception threshold is configured
      And the continuous coverage date is "2026-06-10"
      When SIU indicators are computed for the candidate FNOL record
      Then the recent policy inception indicator is NOT_EVALUATED with reason NO_THRESHOLD_CONFIGURED

    # The missing input outranks the missing rule: a threshold cannot help
    # without a date to apply it to, so when neither is present the reason
    # names the date, not the threshold. Deferred as unreachable while the
    # recent-inception threshold was a fixed, always-supplied value; item 2
    # removed that default, making the threshold caller-supplied and
    # reachable in this state. Nothing else protects the ordering - a
    # reordering of the two checks would fail no test, because mutation
    # testing generates value substitutions, not statement reorderings.
    #
    # This scenario is the fourth corner of a 2x2 (date known/unknown x
    # threshold configured/absent) and, paired against the scenario just
    # above, is what proves the ordering rather than merely restating it:
    # same threshold state (absent) in both, coverage date present above and
    # absent here, and the reason code changes - NO_THRESHOLD_CONFIGURED
    # there, NO_CONTINUOUS_COVERAGE_DATE here. A later reader pruning either
    # row would remove the proof along with it.
    Scenario: Neither recent policy inception input is present
      Given the loss date is "2026-06-15"
      And no late reporting threshold is configured
      And no recent policy inception threshold is configured
      And no continuous coverage date is known
      When SIU indicators are computed for the candidate FNOL record
      Then the late reporting indicator is NOT_EVALUATED with reason NO_THRESHOLD_CONFIGURED
      And the recent policy inception indicator is NOT_EVALUATED with reason NO_CONTINUOUS_COVERAGE_DATE
      And no other SIU indicator is present

  Rule: A continuous coverage date after the loss date does not indicate recent policy inception

    # Specifies a lower-bound guard the implementation already had and no
    # scenario asserted, found by mutation testing during the triage.feature
    # reopening (ASSUMPTIONS.md, QUEUE.md item 2) - this does not change
    # behavior. Every input is present here; they simply describe an
    # impossible situation, so the honest answer is FALSE, not NOT_EVALUATED.
    # Whether a loss predating its policy's inception is itself a coverage
    # problem is a separate, larger question needing phase-3 policy data -
    # not built here.
    Scenario: A continuous coverage date later than the loss date does not fire the indicator
      Given the loss date is "2026-06-15"
      And the recent policy inception threshold is 30 days
      And the continuous coverage date is "2026-06-20"
      When SIU indicators are computed for the candidate FNOL record
      Then the recent policy inception indicator is FALSE

  Rule: Both indicators can be NOT_EVALUATED at once, for different reasons

    # Today, phase 1, no late-reporting threshold has been agreed and no
    # caller supplies a continuous coverage date, so both indicators resolve
    # NOT_EVALUATED here every time - but for two different reasons
    # (ASSUMPTIONS.md): the late-reporting threshold is undecided, while the
    # coverage-date gap is an implementation gap, not a data gap - the
    # phase-2 adapter that looks it up against the policy administration
    # system is not yet wired (see "Data we do not have at intake"). Once it
    # is, an absent coverage date here means the lookup missed, not that
    # intake never had a source for it - the same reason code either way, a
    # different fact behind it. This scenario proves both resolve honestly to
    # NOT_EVALUATED rather than silently to FALSE, regardless of which is
    # true.
    Scenario: No late reporting threshold configured and no continuous coverage date known
      Given the loss date is "2026-07-15"
      And no late reporting threshold is configured
      And the recent policy inception threshold is 30 days
      And no continuous coverage date is known
      When SIU indicators are computed for the candidate FNOL record
      Then the late reporting indicator is NOT_EVALUATED with reason NO_THRESHOLD_CONFIGURED
      And the recent policy inception indicator is NOT_EVALUATED with reason NO_CONTINUOUS_COVERAGE_DATE
      And no other SIU indicator is present

  Rule: Both indicators can fire at once; there is no combined or escalated indicator

    # Both thresholds below are supplied for this scenario; the late-reporting
    # value remains illustrative only, per the rule above.
    Scenario: Both SIU indicators fire together
      Given the loss date is "2026-06-01"
      And the late reporting threshold is 45 days
      And the recent policy inception threshold is 30 days
      And the continuous coverage date is "2026-05-20"
      When SIU indicators are computed for the candidate FNOL record
      Then the late reporting indicator is TRUE
      And the recent policy inception indicator is TRUE
      And no other SIU indicator is present

  Rule: The two thresholds are independent and are not interchangeable

    # Both intervals here are 40 days, which sits between the two thresholds.
    # With each threshold applied to its own indicator, both resolve FALSE:
    # 40 does not exceed the 45-day late reporting threshold, and 40 exceeds
    # the 30-day recent policy inception threshold. Swap the two thresholds
    # and both flip to TRUE. This scenario exists so that an implementation
    # wiring a threshold to the wrong indicator fails, which no other example
    # in this file catches - every other example sits outside the band where
    # the two thresholds disagree.
    Scenario: Thresholds applied to the wrong indicator produce the wrong result
      Given the loss date is "2026-06-23"
      And the late reporting threshold is 45 days
      And the recent policy inception threshold is 30 days
      And the continuous coverage date is "2026-05-14"
      When SIU indicators are computed for the candidate FNOL record
      Then the late reporting indicator is FALSE
      And the recent policy inception indicator is FALSE
