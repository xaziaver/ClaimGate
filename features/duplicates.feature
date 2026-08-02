Feature: Duplicate detection
  As a claims intake system
  I need to identify probable duplicate claims
  So that the same loss is not opened twice

  Rule: A probable duplicate has the same policy, a loss date within 3 days, and the same loss type
        Matching claim ids are returned in ascending order

    Background:
      Given an existing claim "CLM-1001" with policy number "HO-1234567", loss date "2026-06-01", and loss type "fire"

    Scenario Outline: Matching against a single existing claim
      Given a candidate with policy number "<policy_number>", loss date "<loss_date>", and loss type "<loss_type>"
      When duplicate detection runs against the existing claims
      Then the probable duplicate claim ids in ascending order are <duplicate_ids>

      Examples:
        | policy_number | loss_date  | loss_type    | duplicate_ids |
        | HO-1234567    | 2026-06-01 | fire         | ["CLM-1001"]  |
        | HO-1234567    | 2026-06-04 | fire         | ["CLM-1001"]  |
        | HO-1234567    | 2026-05-29 | fire         | ["CLM-1001"]  |
        | HO-1234567    | 2026-06-05 | fire         | []            |
        | HO-1234567    | 2026-05-28 | fire         | []            |
        | AU-7654321    | 2026-06-01 | fire         | []            |
        | HO-1234567    | 2026-06-01 | water_damage | []            |

  Rule: A candidate can match more than one existing claim

    Scenario: Two existing claims both match the candidate
      Given an existing claim "CLM-2001" with policy number "AU-7654321", loss date "2026-06-10", and loss type "auto_collision"
      And an existing claim "CLM-2002" with policy number "AU-7654321", loss date "2026-06-11", and loss type "auto_collision"
      And a candidate with policy number "AU-7654321", loss date "2026-06-10", and loss type "auto_collision"
      When duplicate detection runs against the existing claims
      Then the probable duplicate claim ids in ascending order are ["CLM-2001", "CLM-2002"]
