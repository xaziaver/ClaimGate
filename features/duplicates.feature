Feature: Duplicate candidate detection
  As a claims intake system
  I need to surface existing claims that may describe the same loss as an
  incoming notice
  So that a human reviewer has that evidence when deciding how to handle it

  # The system reports candidate matches. It does not determine that a
  # notice is a duplicate, and a match never blocks, delays, or refuses a
  # notice - see PHASE2_DESIGN.md's record state model, where duplicate
  # candidates are listed as an attribute of a TRIAGED notice, not a state.
  # A second claimant reporting the same loss is not a duplicate at all;
  # only a human reviewer makes that judgment, using a candidate match as
  # one piece of evidence toward it.

  # In the Scenario Outline below, an empty matching_claim_id cell asserts
  # that no candidate match was produced - the same convention
  # validation.feature uses for an empty blockers cell.

  Background:
    Given an existing claim "CLM-1001" with policy number "HO-1234567", loss date "2026-06-01", and loss type "fire"

  Rule: A candidate match has the same policy, a loss date within 60 days, and the same loss type

    # 60 is a carrier policy decision with no statutory or industry-standard
    # basis - not derived from any citation in STATUTORY_REGISTER.md. It
    # exists because the same physical loss is frequently reported twice
    # under two different stated loss dates: for most Florida property
    # perils the reporter states a discovery date, not an event date, and
    # 627.70132(3)'s statutory weather date of loss (landfall, or the date
    # NOAA verifies the event) is not what ClaimGate captures - only what
    # the reporter asserts. Under non-blocking evidence the cost asymmetry
    # is severe: a false positive costs a reviewer one glance; a false
    # negative opens a second claim carrying its own 627.70131(7)(a)
    # 60-day pay-or-deny clock. What would correct this value: the
    # distribution of reported-loss-date deltas across confirmed duplicate
    # pairs on Windward's book - data this project does not have.
    Scenario Outline: Matching against a single existing claim
      Given a candidate with policy number "<policy_number>", loss date "<loss_date>", loss type "<loss_type>", and notice type "INITIAL"
      When duplicate detection runs against the existing claims
      Then the candidate match is "<matching_claim_id>"

      Examples:
        | policy_number | loss_date  | loss_type    | matching_claim_id |
        | HO-1234567    | 2026-06-01 | fire         | CLM-1001          |
        | HO-1234567    | 2026-07-31 | fire         | CLM-1001          |
        | HO-1234567    | 2026-08-01 | fire         |                   |
        | HO-1234567    | 2026-04-02 | fire         | CLM-1001          |
        | HO-1234567    | 2026-04-01 | fire         |                   |
        | AU-7654321    | 2026-06-01 | fire         |                   |
        | HO-1234567    | 2026-06-01 | water_damage |                   |

  Rule: A candidate can match more than one existing claim, returned in ascending claim id order

    Scenario: Two existing claims both match the candidate
      Given an existing claim "CLM-2002" with policy number "AU-7654321", loss date "2026-06-11", and loss type "auto_collision"
      And an existing claim "CLM-2001" with policy number "AU-7654321", loss date "2026-06-10", and loss type "auto_collision"
      And a candidate with policy number "AU-7654321", loss date "2026-06-10", loss type "auto_collision", and notice type "INITIAL"
      When duplicate detection runs against the existing claims
      Then the candidate matches are:
        | claim_id |
        | CLM-2001 |
        | CLM-2002 |

  Rule: Every notice_type either gets compared for a candidate match, or is explicitly not evaluated with a reason - never silently defaulted

    # Reason codes are a closed enumeration, like the reason codes in
    # siu_indicators.feature: FOLLOW_ON_NOTICE_TYPE and
    # NO_EXISTING_CLAIM_TYPE are the complete set today. Escalate before
    # adding to it.

    # A SUPPLEMENTAL or REOPENED notice declares itself a continuation of a
    # known loss - the existing claim it follows on genuinely does describe
    # the same loss, which is a true statement, not the absence of one.
    # Resolving that to "no candidate matches" would assert a negative the
    # system never checked (ASSUMPTIONS.md's "Unevaluated is not negative",
    # already applied to siu_indicators.feature's TRUE/FALSE/NOT_EVALUATED
    # split). NOT_EVALUATED does not depend on timing: whether the notice
    # arrives days or months after the loss it follows, the reason it is
    # never compared is the same, so a notice_type-blind matcher's window
    # arithmetic must never be consulted for these two types.
    Scenario Outline: A follow-on notice type is never compared, regardless of timing
      Given a candidate with policy number "HO-1234567", loss date "<loss_date>", loss type "fire", and notice type "<notice_type>"
      When duplicate detection runs against the existing claims
      Then duplicate matching is NOT_EVALUATED with reason FOLLOW_ON_NOTICE_TYPE

      Examples:
        | notice_type  | loss_date  |
        | SUPPLEMENTAL | 2026-06-02 |
        | REOPENED     | 2026-06-02 |
        | SUPPLEMENTAL | 2026-12-01 |
        | REOPENED     | 2026-12-01 |

    # Loss assessment coverage (s. 627.714) responds to a condominium
    # association's assessment for damage to the common elements, not to
    # the unit owner's own loss - so one owner can legitimately hold both
    # an INITIAL claim and a LOSS_ASSESSMENT claim on the same policy for
    # the same hurricane. Telling those apart from a duplicate needs the
    # existing claim's own notice/coverage type, which intake does not have
    # until phase 3 - a different reason than the follow-on scenario above,
    # hence the separate reason code.
    Scenario: A loss assessment notice is never compared, for a different reason than a follow-on notice
      Given a candidate with policy number "HO-1234567", loss date "2026-06-01", loss type "fire", and notice type "LOSS_ASSESSMENT"
      When duplicate detection runs against the existing claims
      Then duplicate matching is NOT_EVALUATED with reason NO_EXISTING_CLAIM_TYPE

    Scenario: An INITIAL notice is still compared normally
      Given a candidate with policy number "HO-1234567", loss date "2026-06-01", loss type "fire", and notice type "INITIAL"
      When duplicate detection runs against the existing claims
      Then the candidate match is "CLM-1001"
