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
    # Scenarios where a configuration value matters restate it in their own
    # Examples cells or their own fixed Given, which are what mutation
    # reaches - a Background step is not mutated. These three file-wide
    # configuration values govern only scenarios where the value has no
    # effect.
    Given claimant name is "required" by configuration
    And claimant contact is "required" by configuration

  Rule: The loss date must be stated, and must not be in the future

    # DRAFTED FOR REVIEW, item 5h, 2026-08-27. Not ratified. Two things below
    # need the human's approval and neither is inside an agent's boundary: the
    # reason code NO_LOSS_DATE entering a closed enumeration, and the
    # precedence it is given against NO_JURISDICTION_DATE.
    #
    # An absent loss date is a blocker, not a refusal (ASSUMPTIONS.md, "An
    # absent loss date is a domain blocker, not a schema refusal", ratified
    # 2026-08-24). A reporter genuinely may not know when a loss began - water
    # under a sink, a roof that has been leaking a while - and carriers pend
    # for the date rather than refusing the call. It is the blank-policy-number
    # case one field over, and it lands PENDED like every other blocker, since
    # there is no rejected or discarded state anywhere in the record state
    # model. Fla. Stat. 627.70131(4)(b) makes the claim record, dates included,
    # the statutory duty: recording a date nobody supplied is worse than
    # recording its absence.
    #
    # Absence is spelled "absent" here rather than as an empty cell, unlike the
    # loss-type and notice-type rules below. Those two fields are text, and an
    # empty string IS their absent value; a loss date's is not a date at all,
    # so an empty cell would state absence in a spelling the field cannot hold.
    # The token also matters to what mutation can protect, measured rather than
    # assumed: an empty cell is replaced by the marker regardless of what else
    # sits in its column, which the step cannot read as a date and so kills
    # without testing anything, while "absent" is swapped for a sibling date -
    # a real change of outcome from a missing field to a past one, and a real
    # kill. jurisdiction_selection.feature already uses "absent" for exactly
    # this shape of field, one whose absent value is not a value.
    #
    # The determination column asserts what the row produced rather than only
    # what it blocked, and that is the reason it covers the four pre-existing
    # rows too rather than the absent one alone. A row asserting a blocker and
    # nothing else leaves the determination unstated, and an unstated
    # determination is indistinguishable from "checked, and not ahead of
    # today" - the precise confusion CLAUDE.md's "a result that was not
    # computed is never reported as a negative" exists to prevent, and the one
    # jurisdiction_selection.feature's Rule 3 already had to answer for a
    # missing jurisdiction. Widening the column is therefore part of stating
    # the new row, not scope taken alongside it.
    #
    # NO_LOSS_DATE is proposed as a second member of the future-dated-loss
    # determination's own closed reason enumeration, whose only member today is
    # NO_JURISDICTION_DATE. It is not shared with the SIU indicator
    # enumeration: the two are scoped to their own subjects and grow
    # independently (CLAUDE.md), and nothing here proposes adding it to that
    # one - see the queue entry for why the SIU side is a different question
    # with a different answer.
    #
    # Precedence, proposed: NO_LOSS_DATE outranks NO_JURISDICTION_DATE, which
    # outranks NO_THRESHOLD_CONFIGURED. The existing tie-break - name the gap
    # that would still block evaluation if the other were closed - decides the
    # lower pair and is silent on the upper one, because with no loss date and
    # no jurisdiction, closing either leaves the other. What decides it is what
    # the determination is a statement about: the loss date is its subject and
    # today is only the yardstick it is held against, and a missing subject is
    # a more basic absence than a missing yardstick. The both-absent case is
    # not provable here - this rule's scenarios always have a today, and the
    # vocabulary for a notice with no jurisdiction lives in
    # jurisdiction_selection.feature's Rule 3, which is where a row for it
    # belongs. It is left to that file deliberately rather than overlooked.
    #
    # Arithmetic, recomputed against the Background's today of 2026-08-02
    # rather than carried: 2026-08-03 is one day after it and 2026-08-02 is it,
    # so the threshold is exercised on each side by adjacent days, and the
    # comparison is strictly after rather than on-or-after. 2027-06-01 and
    # 2026-08-01 are the same two outcomes at a distance, proving the rule is
    # not a same-day special case.
    Scenario Outline: A loss date is stated, absent, or ahead of today
      Given the loss date is "<loss_date>"
      When the candidate FNOL record is validated
      Then the blockers are <blockers>
      And the future-dated-loss determination is <determination>

      Examples:
        | loss_date  | blockers                         | determination              |
        | 2027-06-01 | LOSS_DATE_IN_FUTURE:loss_date    | TRUE                       |
        | 2026-08-03 | LOSS_DATE_IN_FUTURE:loss_date    | TRUE                       |
        | 2026-08-02 |                                  | FALSE                      |
        | 2026-08-01 |                                  | FALSE                      |
        | absent     | MISSING_REQUIRED_FIELD:loss_date | NOT_EVALUATED:NO_LOSS_DATE |

    # Late notice is a coverage determination made downstream on the facts
    # of prejudice and tolling, not an intake rule.
    Scenario: A loss reported long after the date of loss is not blocked at intake
      Given the loss date is "2022-09-28"
      When the candidate FNOL record is validated
      Then there are no blockers

  Rule: A policy number must be stated

    # Item 7d (PHASE3_DESIGN.md, "Identifiers"): the line-of-business prefix
    # check and the two-letters-hyphen-seven-digits shape check are retired,
    # and POLICY_NUMBER_MALFORMED with them. A policy number is accepted as
    # given; whether it finds a policy is the policy search's answer (item 7f),
    # and a mistyped number beside a correct insured name and postal code is a
    # search, not a pend. What remains here is presence. That too is on notice:
    # item 7g replaces these two scenarios with the identification blocker from
    # features/policy_identification.feature, because a notice carrying an
    # insured name and risk postal code can be searched without a number.

    Scenario: An absent policy number is a missing field
      Given the policy number is ""
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                   | field         |
        | MISSING_REQUIRED_FIELD | policy_number |

    Scenario: A whitespace-only policy number is a missing field
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
    # to dismiss. That is measured, not assumed: this outline carries no
    # acceptance-mutant approvals, while the same-outcome notice-type
    # outline below does - exactly the contrast this comment predicts. A
    # varying blockers column makes each swap discriminating instead.
    #
    # The compact "the blockers are <blockers>" form is used here rather
    # than "the reason codes are". Both now handle an empty cell correctly -
    # item 4i added the same empty-string guard to "the reason codes are"
    # that "the blockers are" already had, so neither form is broken. The
    # compact form is still the better fit for this outline: it asserts
    # field alongside code in one cell (LOSS_TYPE_UNRECOGNIZED:loss_type),
    # which an outline built around a single field can use directly; "the
    # reason codes are" only asserts the code list and drops which field
    # each code belongs to.
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
    # resolve to, unlike siu_indicators.feature's thresholds. The
    # configuration reaches the domain as a boolean, so an unrecognized
    # configuration value cannot occur below the step definition and no
    # scenario specifies one - the same shape as the missing "not
    # configured" scenario above.
    #
    # Coverage E (personal liability, fault-based) and Coverage F (MedPay,
    # no-fault) are not sub-divided here - both land in the same
    # required-field set, a deliberate scope decision rather than an
    # omission.

    # Mutation only reaches quoted or numeric text in a plain scenario's
    # step, or an Outline's Examples cells - gauntlet's acceptance mutation
    # module never mutates a fixed Given above a table, regardless of
    # quoting. Anything this spec intends mutation to protect has to be a
    # quoted Examples cell, which is why name_required and contact_required
    # are columns below rather than fixed Given lines.
    Scenario Outline: Required fields for an injury loss, by configuration
      Given the loss type is "injury"
      And claimant name is "<name_required>" by configuration
      And claimant contact is "<contact_required>" by configuration
      And the claimant name is "<name>"
      And the claimant contact is "<contact>"
      And the incident description is "<description>"
      When the candidate FNOL record is validated
      Then the blockers are <blockers>

      Examples:
        | name_required | contact_required | name       | contact  | description                                           | blockers                                     |
        | required      | required          | Pat Rivera | 555-0101 | Guest slipped on the pool deck and fractured a wrist  |                                               |
        | required      | required          |            | 555-0101 | Guest slipped on the pool deck and fractured a wrist  | MISSING_REQUIRED_FIELD:claimant_name         |
        | not required  | required          |            | 555-0101 | Guest slipped on the pool deck and fractured a wrist  |                                               |
        | required      | required          | Pat Rivera |          | Guest slipped on the pool deck and fractured a wrist  | MISSING_REQUIRED_FIELD:claimant_contact      |
        | required      | not required      | Pat Rivera |          | Guest slipped on the pool deck and fractured a wrist  |                                               |
        | not required  | not required      | Pat Rivera | 555-0101 |                                                        | MISSING_REQUIRED_FIELD:incident_description  |

    Scenario Outline: Required fields for a liability loss, by configuration
      Given the loss type is "liability"
      And claimant name is "<name_required>" by configuration
      And claimant contact is "<contact_required>" by configuration
      And the claimant name is "<name>"
      And the claimant contact is "<contact>"
      And the incident description is "<description>"
      When the candidate FNOL record is validated
      Then the blockers are <blockers>

      Examples:
        | name_required | contact_required | name       | contact  | description                                                                     | blockers                                     |
        | required      | required          | Pat Rivera | 555-0101 | Delivery driver slipped on the wet lobby floor and left before being identified |                                               |
        | required      | required          |            | 555-0101 | Delivery driver slipped on the wet lobby floor and left before being identified | MISSING_REQUIRED_FIELD:claimant_name         |
        | not required  | required          |            | 555-0101 | Delivery driver slipped on the wet lobby floor and left before being identified |                                               |
        | required      | required          | Pat Rivera |          | Delivery driver slipped on the wet lobby floor and left before being identified | MISSING_REQUIRED_FIELD:claimant_contact      |
        | required      | not required      | Pat Rivera |          | Delivery driver slipped on the wet lobby floor and left before being identified |                                               |
        | not required  | not required      | Pat Rivera | 555-0101 |                                                                                  | MISSING_REQUIRED_FIELD:incident_description  |

    Scenario: Section I losses do not require claimant details
      Given the loss type is "wind_hail"
      And no claimant details are provided
      When the candidate FNOL record is validated
      Then there are no blockers

    Scenario: Multiple missing claimant fields all survive as blockers, deduplicated in reason codes
      Given the loss type is "injury"
      And claimant name is "required" by configuration
      And claimant contact is "required" by configuration
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
    # artifact of check sequence: NOTICE_TYPE_UNRECOGNIZED, then
    # LOSS_TYPE_UNRECOGNIZED, then LOSS_DATE_IN_FUTURE, then
    # MISSING_REQUIRED_FIELD. POLICY_NUMBER_MALFORMED led this order until item
    # 7d retired it (2026-09-05); every scenario in this rule used it as an
    # ingredient and was rewritten without it.
    #
    # Three is the maximum this rule exercises. NOTICE_TYPE_UNRECOGNIZED and
    # LOSS_TYPE_UNRECOGNIZED each require their own field to be non-empty - an
    # empty field produces MISSING_REQUIRED_FIELD instead, never both from the
    # same field - and LOSS_DATE_IN_FUTURE and MISSING_REQUIRED_FIELD:loss_date
    # stand in the same relation. The Section II claimant fields supply
    # MISSING_REQUIRED_FIELD only for a recognized loss type, so they never
    # compose with LOSS_TYPE_UNRECOGNIZED. Until item 7g an absent policy
    # number is one more source of MISSING_REQUIRED_FIELD and would let all
    # four codes fire at once; that composition is deliberately not exercised
    # here, so 7g's retirement of the requirement does not reopen this rule.
    # After 7g, three is the maximum outright. Re-derived by hand from the four
    # codes and their exclusions on 2026-09-05; nothing revalidates it if a
    # fifth code or field-recognition check is added.
    #
    # The scenarios below prove that a fixed emission sequence in the
    # implementation cannot satisfy every case: three different maximal
    # combinations, a subset that skips the earliest codes, and a subset that
    # is non-contiguous in the canonical order.

    Scenario: Notice and date codes fire together with a missing claimant field
      Given the notice type is "SUPPLEMENT"
      And the loss date is "2026-08-03"
      And the loss type is "injury"
      And claimant name is "required" by configuration
      And claimant contact is "required" by configuration
      And the claimant name is ""
      And the claimant contact is "555-0101"
      And the incident description is "Guest slipped on the pool deck and fractured a wrist"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field         |
        | NOTICE_TYPE_UNRECOGNIZED | notice_type   |
        | LOSS_DATE_IN_FUTURE      | loss_date     |
        | MISSING_REQUIRED_FIELD   | claimant_name |
      And the reason codes are "NOTICE_TYPE_UNRECOGNIZED;LOSS_DATE_IN_FUTURE;MISSING_REQUIRED_FIELD"

    Scenario: Notice, loss-type, and date codes fire together
      Given the notice type is "SUPPLEMENT"
      And the loss date is "2026-08-03"
      And the loss type is "watr_damage"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field         |
        | NOTICE_TYPE_UNRECOGNIZED | notice_type   |
        | LOSS_TYPE_UNRECOGNIZED   | loss_type     |
        | LOSS_DATE_IN_FUTURE      | loss_date     |
      And the reason codes are "NOTICE_TYPE_UNRECOGNIZED;LOSS_TYPE_UNRECOGNIZED;LOSS_DATE_IN_FUTURE"

    Scenario: A later-canonical subset fires without any earlier code present
      Given the loss date is "2026-08-03"
      And the loss type is "injury"
      And claimant name is "required" by configuration
      And claimant contact is "required" by configuration
      And the claimant name is "Pat Rivera"
      And the claimant contact is ""
      And the incident description is "Dog bit a visitor on the front porch"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                   | field            |
        | LOSS_DATE_IN_FUTURE    | loss_date        |
        | MISSING_REQUIRED_FIELD | claimant_contact |

    Scenario: A non-contiguous subset of canonical order still sorts correctly
      Given the notice type is "SUPPLEMENT"
      And the loss type is "injury"
      And claimant name is "required" by configuration
      And claimant contact is "required" by configuration
      And the claimant name is "Pat Rivera"
      And the claimant contact is "555-0101"
      And the incident description is ""
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field                 |
        | NOTICE_TYPE_UNRECOGNIZED | notice_type           |
        | MISSING_REQUIRED_FIELD   | incident_description  |

    # The maximal combination that omits LOSS_DATE_IN_FUTURE (item 5h,
    # 2026-08-27). It is here on reachability grounds rather than mutation
    # grounds: every value in a plain scenario's step takes the marker when
    # mutated, and a marked step no longer resolves, so this scenario's mutants
    # die without testing anything, as the ones in "Notice, loss-type, and
    # date codes fire together" do. What it proves is that an absent loss date
    # composes with both recognition codes and sorts into canonical position
    # among them, which no other scenario can show.
    Scenario: Notice and loss-type codes fire together with an absent loss date
      Given the notice type is "SUPPLEMENT"
      And the loss type is "watr_damage"
      And the loss date is "absent"
      When the candidate FNOL record is validated
      Then the blockers are:
        | code                     | field         |
        | NOTICE_TYPE_UNRECOGNIZED | notice_type   |
        | LOSS_TYPE_UNRECOGNIZED   | loss_type     |
        | MISSING_REQUIRED_FIELD   | loss_date     |
      And the reason codes are "NOTICE_TYPE_UNRECOGNIZED;LOSS_TYPE_UNRECOGNIZED;MISSING_REQUIRED_FIELD"
