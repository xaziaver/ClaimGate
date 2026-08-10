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

  Rule: A candidate match has the same policy, a loss date within 3 days, and the same loss type

    # The 3-day window's own rationale is under review: it was written when
    # a match blocked a notice, and duplicate candidates are now non-blocking
    # evidence instead - see ASSUMPTIONS.md's decisions.md audit ("Duplicate
    # detection window: 3 days") and QUEUE.md item 3. Left at 3 in this
    # draft; the replacement value is a business decision, not made here.
    Scenario Outline: Matching against a single existing claim
      Given a candidate with policy number "<policy_number>", loss date "<loss_date>", loss type "<loss_type>", and notice type "INITIAL"
      When duplicate detection runs against the existing claims
      Then the candidate match is "<matching_claim_id>"

      Examples:
        | policy_number | loss_date  | loss_type    | matching_claim_id |
        | HO-1234567    | 2026-06-01 | fire         | CLM-1001          |
        | HO-1234567    | 2026-06-04 | fire         | CLM-1001          |
        | HO-1234567    | 2026-05-29 | fire         | CLM-1001          |
        | HO-1234567    | 2026-06-05 | fire         |                   |
        | HO-1234567    | 2026-05-28 | fire         |                   |
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

  Rule: A declared SUPPLEMENTAL or REOPENED notice is a known follow-on to a loss, not a candidate match of it

    # notice_type resolves the exact ambiguity this feature otherwise exists
    # to catch (PHASE2_DESIGN.md, "Notice type and window selection"). Under
    # a notice_type-blind matcher this cuts both ways: a follow-on arriving
    # within the window is wrongly surfaced as a candidate match, and one
    # arriving months later - the normal case for a SUPPLEMENTAL or REOPENED
    # notice - is wrongly missed altogether. Both are wrong for the same
    # reason: notice_type already answers the question this feature asks, so
    # timing is never consulted for these two types.
    Scenario Outline: SUPPLEMENTAL and REOPENED notices are never candidate matches, regardless of timing
      Given a candidate with policy number "HO-1234567", loss date "<loss_date>", loss type "fire", and notice type "<notice_type>"
      When duplicate detection runs against the existing claims
      Then there are no candidate matches

      Examples:
        | notice_type  | loss_date  |
        | SUPPLEMENTAL | 2026-06-02 |
        | REOPENED     | 2026-06-02 |
        | SUPPLEMENTAL | 2026-12-01 |
        | REOPENED     | 2026-12-01 |

    Scenario: An INITIAL notice is still matched normally
      Given a candidate with policy number "HO-1234567", loss date "2026-06-01", loss type "fire", and notice type "INITIAL"
      When duplicate detection runs against the existing claims
      Then the candidate match is "CLM-1001"
