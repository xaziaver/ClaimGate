Feature: FNOL validation
  As a claims intake system
  I need to identify what is missing or malformed in a candidate First
  Notice of Loss
  So that every notice is accepted and recorded, and the ones that cannot
  proceed are held with a clear statement of what the reporter must supply

  # "Today" is the current calendar date in the jurisdiction of the insured
  # risk (America/New_York for the Florida book this system serves today),
  # never a server date or UTC date. The domain function under test here
  # receives that date as a parameter and never reads a clock itself -
  # deriving it correctly from a real timestamp at request time is a
  # phase-2 API-shell concern, and belongs proven where that derivation
  # actually happens, not in a spec that only ever calls the pure function
  # with an already-resolved date.

  # In Scenario Outlines an empty blockers cell asserts that no blockers were
  # produced. Standalone scenarios state this explicitly as "there are no
  # blockers"; the outline form is a table-cell constraint, not a different
  # meaning.
  Background:
    Given today is "2026-08-02"
    And the notice type is "INITIAL"
    And the policy number is "HO-1234567"
    And the loss date is "2026-07-01"
    And the loss type is "wind_hail"

  Rule: The loss date must not be in the future

    Scenario Outline: Loss date must not be in the future
      Given the loss date is "<loss_date>"
      When the candidate FNOL record is validated
      Then the blockers are <blockers>

      Examples:
        | loss_date  | blockers                       |
        | 2027-06-01 | LOSS_DATE_IN_FUTURE:loss_date  |
        | 2026-08-03 | LOSS_DATE_IN_FUTURE:loss_date  |
        | 2026-08-02 |                                 |
        | 2026-08-01 |                                 |

    # Late notice is a coverage determination made downstream on the facts
    # of prejudice and tolling, not an intake rule.
    Scenario: A loss reported long after the date of loss is not blocked at intake
      Given the loss date is "2022-09-28"
      When the candidate FNOL record is validated
      Then there are no blockers

  Rule: The policy number must have a recognized line-of-business prefix and a 7-digit number

    Scenario Outline: Policy number format
      Given the policy number is "<policy_number>"
      When the candidate FNOL record is validated
      Then the blockers are <blockers>

      Examples:
        | policy_number | blockers                                |
        | HO-1234567    |                                          |
        | AU-1234567    |                                          |
        | CP-1234567    |                                          |
        | CA-1234567    |                                          |
        | GL-1234567    |                                          |
        | XX-1234567    | POLICY_NUMBER_MALFORMED:policy_number   |
        | HO-123456     | POLICY_NUMBER_MALFORMED:policy_number   |
        | HO-12345678   | POLICY_NUMBER_MALFORMED:policy_number   |
        | ho-1234567    | POLICY_NUMBER_MALFORMED:policy_number   |
        | HO1234567     | POLICY_NUMBER_MALFORMED:policy_number   |
        | HO-ABCDEFG    | POLICY_NUMBER_MALFORMED:policy_number   |

    Scenario: An absent policy number is a missing field, not a malformed one
      Given the policy number is ""
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                   | field         |
        | MISSING_REQUIRED_FIELD | policy_number |

    Scenario: A whitespace-only policy number is a missing field, not a malformed one
      Given the policy number is "   "
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                   | field         |
        | MISSING_REQUIRED_FIELD | policy_number |

  Rule: The loss type must be stated

    Scenario: An absent loss type is a missing field
      Given the loss type is ""
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                   | field     |
        | MISSING_REQUIRED_FIELD | loss_type |

  Rule: Injury losses require injured-party details

    Scenario Outline: Required fields for an injury loss
      Given the loss type is "injury"
      And the injured party name is "<name>"
      And the injured party contact is "<contact>"
      And the injury description is "<description>"
      When the candidate FNOL record is validated
      Then the blockers are <blockers>

      Examples:
        | name       | contact  | description                                            | blockers                                     |
        | Pat Rivera | 555-0101 | Guest slipped on the pool deck and fractured a wrist   |                                               |
        |            | 555-0101 | Guest slipped on the pool deck and fractured a wrist   | MISSING_REQUIRED_FIELD:injured_party_name    |
        | Pat Rivera |          | Guest slipped on the pool deck and fractured a wrist   | MISSING_REQUIRED_FIELD:injured_party_contact |
        | Pat Rivera | 555-0101 |                                                         | MISSING_REQUIRED_FIELD:injury_description    |

    Scenario: Non-injury losses do not require injured-party details
      Given the loss type is "wind_hail"
      And no injured-party details are provided
      When the candidate FNOL record is validated
      Then there are no blockers

    Scenario: Multiple missing injury fields all survive as blockers, deduplicated in reason codes
      Given the loss type is "injury"
      And the injured party name is ""
      And the injured party contact is ""
      And the injury description is "Dog bit a visitor on the front porch"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                   | field                 |
        | MISSING_REQUIRED_FIELD | injured_party_contact |
        | MISSING_REQUIRED_FIELD | injured_party_name    |
      And the reason codes are "MISSING_REQUIRED_FIELD"

  Rule: Every notice states which kind of notice it is

    Scenario Outline: Recognized notice types are accepted
      Given the notice type is "<notice_type>"
      When the candidate FNOL record is validated
      Then there are no blockers

      Examples:
        | notice_type     |
        | INITIAL         |
        | REOPENED        |
        | SUPPLEMENTAL    |
        | LOSS_ASSESSMENT |

    Scenario: A missing notice type is a blocker
      Given the notice type is ""
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                   | field       |
        | MISSING_REQUIRED_FIELD | notice_type |

    Scenario: An unrecognized notice type is a distinct blocker from a missing one
      Given the notice type is "SUPPLEMENT"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field       |
        | NOTICE_TYPE_UNRECOGNIZED | notice_type |

  Rule: All blockers are reported together, in canonical order, regardless of how many checks fail or which ones

    # Canonical order is a declared property of the code enumeration, not an
    # artifact of check sequence: POLICY_NUMBER_MALFORMED, then
    # NOTICE_TYPE_UNRECOGNIZED, then LOSS_DATE_IN_FUTURE, then
    # MISSING_REQUIRED_FIELD. The scenarios below prove that a fixed emission
    # sequence in the implementation cannot satisfy every case: the full set,
    # a subset that skips the earliest codes, and a subset that is
    # non-contiguous in the canonical order.

    Scenario: All four canonical blocker codes fire together
      Given the policy number is "XX-1234567"
      And the notice type is "SUPPLEMENT"
      And the loss date is "2026-08-03"
      And the loss type is "injury"
      And the injured party name is ""
      And the injured party contact is "555-0101"
      And the injury description is "Guest slipped on the pool deck and fractured a wrist"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field              |
        | POLICY_NUMBER_MALFORMED  | policy_number      |
        | NOTICE_TYPE_UNRECOGNIZED | notice_type        |
        | LOSS_DATE_IN_FUTURE      | loss_date          |
        | MISSING_REQUIRED_FIELD   | injured_party_name |
      And the reason codes are "POLICY_NUMBER_MALFORMED;NOTICE_TYPE_UNRECOGNIZED;LOSS_DATE_IN_FUTURE;MISSING_REQUIRED_FIELD"

    Scenario: A later-canonical subset fires without any earlier code present
      Given the loss date is "2026-08-03"
      And the loss type is "injury"
      And the injured party name is "Pat Rivera"
      And the injured party contact is ""
      And the injury description is "Dog bit a visitor on the front porch"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                      | field                 |
        | LOSS_DATE_IN_FUTURE       | loss_date             |
        | MISSING_REQUIRED_FIELD    | injured_party_contact |

    Scenario: A non-contiguous subset of canonical order still sorts correctly
      Given the policy number is "XX-1234567"
      And the loss type is "injury"
      And the injured party name is "Pat Rivera"
      And the injured party contact is "555-0101"
      And the injury description is ""
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field              |
        | POLICY_NUMBER_MALFORMED  | policy_number      |
        | MISSING_REQUIRED_FIELD   | injury_description |
