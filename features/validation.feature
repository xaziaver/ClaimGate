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

    # HO is the only recognized prefix - a scope decision for the shipped
    # configuration, not a statutory one. That configuration covers Florida
    # residential property only; AU (auto), CP (commercial property), CA
    # (commercial auto), and GL (general liability) are lines outside it.
    # DP (dwelling fire, common on Florida residential books for landlord
    # and non-owner-occupied risks) and MH (manufactured housing) were both
    # considered and excluded for want of evidence a configured book writes
    # either - see QUEUE.md item 4b. An unrecognized prefix resolves
    # POLICY_NUMBER_MALFORMED like any other malformed policy number: a
    # blocker, not a refusal. PHASE2_DESIGN.md's record state model has no
    # rejected or discarded state, so a notice carrying this blocker still
    # lands PENDED, not refused, and a reviewer can still act on it.
    #
    # The AU/CP/CA/GL rows stay even though their outcome is now identical
    # to the XX row's - they document which lines of business this book
    # does not write, which is worth more than the four extra rows cost.
    Scenario Outline: Policy number format
      Given the policy number is "<policy_number>"
      When the candidate FNOL record is validated
      Then the blockers are <blockers>

      Examples:
        | policy_number | blockers                              |
        | HO-1234567    |                                       |
        | AU-1234567    | POLICY_NUMBER_MALFORMED:policy_number |
        | CP-1234567    | POLICY_NUMBER_MALFORMED:policy_number |
        | CA-1234567    | POLICY_NUMBER_MALFORMED:policy_number |
        | GL-1234567    | POLICY_NUMBER_MALFORMED:policy_number |
        | XX-1234567    | POLICY_NUMBER_MALFORMED:policy_number |
        | HO-123456     | POLICY_NUMBER_MALFORMED:policy_number |
        | HO-12345678   | POLICY_NUMBER_MALFORMED:policy_number |
        | ho-1234567    | POLICY_NUMBER_MALFORMED:policy_number |
        | HO1234567     | POLICY_NUMBER_MALFORMED:policy_number |
        | HO-ABCDEFG    | POLICY_NUMBER_MALFORMED:policy_number |

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

  Rule: The loss type must be stated and recognized

    # The recognized set is what intake can INTERPRET, not what the policy
    # covers. flood, mold, and smoke are recognized and are routinely
    # excluded or sub-limited on a Florida HO book; an insured reporting
    # surge damage after a named storm is making a perfectly intelligible
    # notice, and whether it is covered is decided downstream on policy
    # language - the same line the late-notice comment above already draws.
    #
    # Enumerating the set does not presume the outcome of ASSUMPTIONS.md's
    # open decision on whether loss_type conflates perils with Section II
    # coverage categories. It states what intake can interpret today, not a
    # settled taxonomy.
    #
    # injury and liability are two of the fourteen recognized values but
    # have no row here: both are Section II loss types that require
    # claimant details (see the Section II rule below), so a bare row for
    # either could not assert an empty blockers cell the way the other
    # twelve recognized values do. Their recognized-value coverage lives in
    # the Section II rule below, whose complete-information rows already
    # assert zero blockers for a fully supplied injury or liability notice;
    # supplying only some of those fields there adds MISSING_REQUIRED_FIELD
    # blockers alongside a recognized loss type, not instead of one.
    #
    # Recognized, unrecognized, and absent share one outline deliberately,
    # unlike the notice-type enumeration below. When every row of an outline
    # asserts the same outcome, a mutation that swaps one recognized value
    # for another survives, proving nothing beyond the one approval it costs
    # to dismiss. That is measured, not assumed: all four of this file's
    # current acceptance-mutant approvals are exactly the notice-type rows
    # this pattern warns against (true as of 2026-08-16; nothing revalidates
    # this if a future approval lands elsewhere in the file). A varying
    # blockers column makes each swap discriminating instead.
    #
    # The compact "the blockers are <blockers>" form is used here rather
    # than "the reason codes are", even though both can assert a code,
    # because the reason-codes step cannot express an empty expectation: it
    # splits the expected string on semicolons, and an empty string does not
    # split into an empty list, so an empty codes cell could never match a
    # zero-blocker result. The compact "the blockers are" form handles an
    # empty cell correctly. Recorded here so the next person reaching for
    # "the reason codes are" in an outline finds this out from the comment,
    # not from a failing gate.
    #
    # Recognition is exact-match and case-sensitive - the WIND_HAIL row below
    # is deliberately not folded into wind_hail. Normalizing case at intake
    # is a feed-adapter concern that belongs where the feed is parsed, not in
    # a pure domain check.
    Scenario Outline: A loss type is recognized, unrecognized, or absent
      Given the loss type is "<loss_type>"
      When the candidate FNOL record is validated
      Then the blockers are <blockers>

      Examples:
        | loss_type    | blockers                         |
        | fire         |                                  |
        | flood        |                                  |
        | hurricane    |                                  |
        | lightning    |                                  |
        | mold         |                                  |
        | roof_leak    |                                  |
        | sinkhole     |                                  |
        | smoke        |                                  |
        | theft        |                                  |
        | vandalism    |                                  |
        | water_damage |                                  |
        | wind_hail    |                                  |
        | watr_damage  | LOSS_TYPE_UNRECOGNIZED:loss_type |
        | WIND_HAIL    | LOSS_TYPE_UNRECOGNIZED:loss_type |
        |              | MISSING_REQUIRED_FIELD:loss_type |

  Rule: Section II losses require claimant details

    # Of the fourteen recognized loss types, injury and liability are the
    # two Section II categories; the other twelve are Section I property
    # perils with no claimant fields to require. incident_description is
    # required unconditionally for either Section II type: without it the
    # record is not a notice of loss, only an assertion that one exists,
    # and nothing downstream can be reserved, assigned, or investigated
    # from it. claimant_name and claimant_contact are each required or not
    # by caller-supplied configuration, with no default - a liability claim
    # is frequently third-party property damage with nobody injured at all,
    # and a carrier that captures claimant details at first notice and one
    # that does not are both expressible. There is no "not configured"
    # scenario: an unsupplied configuration is a caller contract violation,
    # not a business outcome, and validation has no NOT_EVALUATED to
    # resolve to, unlike siu_indicators.feature's thresholds.
    #
    # Coverage E (personal liability, fault-based) and Coverage F (MedPay,
    # no-fault) are not sub-divided here - both land in the same
    # required-field set, a deliberate scope decision rather than an
    # omission.

    # loss_type, name_required, and contact_required are all Examples columns,
    # not fixed Given lines, so every one of them is a mutable literal
    # (gauntlet.acceptance.mutation only mutates quoted/numeric text in a step,
    # or an Outline's Examples cells - a bare word in a fixed Given above the
    # table is neither). Each required/not-required pair below holds loss type
    # and every other field constant and varies only the one configuration
    # flag under test, so a mutation swapping that flag is the only thing that
    # can change the row's blockers.
    Scenario Outline: Required fields for a Section II loss, by configuration and loss type
      Given the loss type is "<loss_type>"
      And claimant name is "<name_required>" by configuration
      And claimant contact is "<contact_required>" by configuration
      And the claimant name is "<name>"
      And the claimant contact is "<contact>"
      And the incident description is "<description>"
      When the candidate FNOL record is validated
      Then the blockers are <blockers>

      Examples:
        | loss_type | name_required | contact_required | name       | contact  | description                                           | blockers                                     |
        | injury    | required      | required          | Pat Rivera | 555-0101 | Guest slipped on the pool deck and fractured a wrist  |                                               |
        | liability | required      | required          | Pat Rivera | 555-0101 | Delivery driver slipped on the wet lobby floor        |                                               |
        | liability | required      | required          |            | 555-0101 | Guest slipped on the pool deck and fractured a wrist  | MISSING_REQUIRED_FIELD:claimant_name         |
        | liability | not required  | required          |            | 555-0101 | Guest slipped on the pool deck and fractured a wrist  |                                               |
        | liability | required      | required          | Pat Rivera |          | Guest slipped on the pool deck and fractured a wrist  | MISSING_REQUIRED_FIELD:claimant_contact      |
        | liability | required      | not required      | Pat Rivera |          | Guest slipped on the pool deck and fractured a wrist  |                                               |
        | injury    | required      | required          |            | 555-0101 | Guest slipped on the pool deck and fractured a wrist  | MISSING_REQUIRED_FIELD:claimant_name         |
        | injury    | not required  | required          |            | 555-0101 | Guest slipped on the pool deck and fractured a wrist  |                                               |
        | injury    | required      | required          | Pat Rivera |          | Guest slipped on the pool deck and fractured a wrist  | MISSING_REQUIRED_FIELD:claimant_contact      |
        | injury    | required      | not required      | Pat Rivera |          | Guest slipped on the pool deck and fractured a wrist  |                                               |
        | liability | not required  | not required      | Pat Rivera | 555-0101 |                                                        | MISSING_REQUIRED_FIELD:incident_description  |

    Scenario: Section I losses do not require claimant details
      Given the loss type is "wind_hail"
      And no claimant details are provided
      When the candidate FNOL record is validated
      Then there are no blockers

    Scenario: Multiple missing claimant fields all survive as blockers, deduplicated in reason codes
      Given the loss type is "injury"
      And claimant name is required by configuration
      And claimant contact is required by configuration
      And the claimant name is ""
      And the claimant contact is ""
      And the incident description is "Dog bit a visitor on the front porch"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                   | field             |
        | MISSING_REQUIRED_FIELD | claimant_contact  |
        | MISSING_REQUIRED_FIELD | claimant_name     |
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
    # NOTICE_TYPE_UNRECOGNIZED, then LOSS_TYPE_UNRECOGNIZED, then
    # LOSS_DATE_IN_FUTURE, then MISSING_REQUIRED_FIELD.
    #
    # No candidate reaches all five codes at once. POLICY_NUMBER_MALFORMED,
    # NOTICE_TYPE_UNRECOGNIZED, and LOSS_TYPE_UNRECOGNIZED each require their
    # own field to be non-empty - a field that's empty produces
    # MISSING_REQUIRED_FIELD instead, never both from the same field. The
    # only other source of MISSING_REQUIRED_FIELD is the Section II claimant
    # fields (claimant_name, claimant_contact, incident_description), and
    # those only apply when the loss type is injury or liability, both of
    # which are recognized and so never the source of
    # LOSS_TYPE_UNRECOGNIZED. So whenever all three of those field-recognition
    # codes fire together, every field that could still supply
    # MISSING_REQUIRED_FIELD is already accounted for, and a fifth code has
    # nowhere left to come from. Four is the maximum reachable, and it is
    # reachable more than one way, not just the one example below:
    # exhaustively checked against a simulated closed loss-type set, four
    # distinct four-code combinations exist (true as of 2026-08-16; nothing
    # revalidates this if a sixth code or a sixth field-recognition check is
    # added). The scenarios below prove that a fixed emission sequence in the
    # implementation cannot satisfy every case: two different maximal
    # combinations, a subset that skips the earliest codes, and a subset that
    # is non-contiguous in the canonical order.

    Scenario: Policy, notice, and date codes fire together with a missing claimant field
      Given the policy number is "XX-1234567"
      And the notice type is "SUPPLEMENT"
      And the loss date is "2026-08-03"
      And the loss type is "injury"
      And claimant name is required by configuration
      And claimant contact is required by configuration
      And the claimant name is ""
      And the claimant contact is "555-0101"
      And the incident description is "Guest slipped on the pool deck and fractured a wrist"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field         |
        | POLICY_NUMBER_MALFORMED  | policy_number |
        | NOTICE_TYPE_UNRECOGNIZED | notice_type   |
        | LOSS_DATE_IN_FUTURE      | loss_date     |
        | MISSING_REQUIRED_FIELD   | claimant_name |
      And the reason codes are "POLICY_NUMBER_MALFORMED;NOTICE_TYPE_UNRECOGNIZED;LOSS_DATE_IN_FUTURE;MISSING_REQUIRED_FIELD"

    Scenario: Policy, notice, and date codes fire together with an unrecognized loss type
      Given the policy number is "XX-1234567"
      And the notice type is "SUPPLEMENT"
      And the loss date is "2026-08-03"
      And the loss type is "watr_damage"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field         |
        | POLICY_NUMBER_MALFORMED  | policy_number |
        | NOTICE_TYPE_UNRECOGNIZED | notice_type   |
        | LOSS_TYPE_UNRECOGNIZED   | loss_type     |
        | LOSS_DATE_IN_FUTURE      | loss_date     |
      And the reason codes are "POLICY_NUMBER_MALFORMED;NOTICE_TYPE_UNRECOGNIZED;LOSS_TYPE_UNRECOGNIZED;LOSS_DATE_IN_FUTURE"

    Scenario: A later-canonical subset fires without any earlier code present
      Given the loss date is "2026-08-03"
      And the loss type is "injury"
      And claimant name is required by configuration
      And claimant contact is required by configuration
      And the claimant name is "Pat Rivera"
      And the claimant contact is ""
      And the incident description is "Dog bit a visitor on the front porch"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                   | field            |
        | LOSS_DATE_IN_FUTURE    | loss_date        |
        | MISSING_REQUIRED_FIELD | claimant_contact |

    Scenario: A non-contiguous subset of canonical order still sorts correctly
      Given the policy number is "XX-1234567"
      And the loss type is "injury"
      And claimant name is required by configuration
      And claimant contact is required by configuration
      And the claimant name is "Pat Rivera"
      And the claimant contact is "555-0101"
      And the incident description is ""
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field                 |
        | POLICY_NUMBER_MALFORMED  | policy_number         |
        | MISSING_REQUIRED_FIELD   | incident_description  |
