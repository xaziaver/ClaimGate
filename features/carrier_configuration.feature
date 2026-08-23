Feature: Carrier configuration loading

  As a claims intake system administering more than one carrier
  I need each carrier's own required-field, threshold, and window rules
  resolved before any domain rule runs
  So that no domain function is ever called with a value nobody configured,
  and a carrier this deployment has no usable rules for is refused before
  that ever happens

  # The six values loaded here are every caller-supplied value phase 1 moved
  # out of the domain with no default. Names verified 2026-08-22: validate,
  # compute_siu_indicators, and find_duplicates are current as of that date;
  # the argument here is about the values these signatures locate, not the
  # signatures themselves, and survives their renaming. They hold,
  # respectively: claimant_name_required, claimant_contact_required, and
  # recognized_policy_number_prefixes (items 4g, 4j);
  # late_reporting_threshold_days and recent_inception_threshold_days (item
  # 2); and window_days (item 3). Nothing below calls any of those three
  # functions - this is the layer that resolves what they will be called
  # with, and the shell cannot call any of them until it does (QUEUE.md item
  # 5a).

  # The per-carrier rules file loaded here is physically separate from the
  # carrier identity reference (carrier_code to NAIC company and group) that
  # PHASE2_DESIGN.md's carrier-reference section describes and item 5c owns -
  # a carrier's NAIC number and a carrier's duplicate match window are
  # different kinds of fact, and one file holding both is what would make
  # carrier_code look branchable. A lookup keyed by carrier_code is not a
  # branch on carrier_code: every value below is selected by key and passed
  # through unchanged, and no code path here or in the domain reads
  # carrier_code to choose behavior. See ASSUMPTIONS.md, "The per-carrier
  # rules file moves from phase 3 into phase 2."

  # Refusing to load a carrier's rules is not the notice-lifecycle refusal
  # CLAUDE.md's record state model forbids. A malformed or absent
  # configuration value never reaches a domain call (ASSUMPTIONS.md, "A
  # carrier configuration crosses into the domain already resolved") -
  # refusing it refuses nothing a reporter sent and creates no statutory
  # duty. This is not item 5c's 400 on an unknown or malformed carrier_code
  # against the identity reference, either: that is a different file, a
  # different check, owned there. This is one layer earlier - whether the
  # rules file this deployment ships has anything usable for the requested
  # carrier at all.

  # Reason codes are a closed enumeration, like every other feature file's:
  # CARRIER_NOT_CONFIGURED, MALFORMED_REQUIRED_CONFIGURATION, and
  # MISSING_REQUIRED_CONFIGURATION are the complete set today, in that
  # canonical order - malformed before missing, mirroring
  # POLICY_NUMBER_MALFORMED's position ahead of MISSING_REQUIRED_FIELD in
  # validation.feature's own declared order. An absent value and a malformed
  # one are different defects with different fixes: an absent value means
  # this carrier was never onboarded into the rules file, a malformed one
  # means it was onboarded wrongly. ASSUMPTIONS.md, "A missing configuration
  # value and a malformed one are different reason codes." Escalate before
  # adding a fourth code.

  # A required value is refused whether it is absent from a recognized
  # carrier's entry or present in a shape the receiving function cannot use.
  # What counts as malformed follows from each value's own type, not a new
  # vocabulary: a non-boolean where claimant_name_required or
  # claimant_contact_required needs a boolean, a non-integer or negative
  # number where late_reporting_threshold_days, recent_inception_threshold_days,
  # or window_days needs a day count, an empty collection where
  # recognized_policy_number_prefixes needs at least one recognized prefix.
  # Zero is neither non-integer nor negative, and is proven a valid day
  # count rather than a malformed one in the rule below. ASSUMPTIONS.md, "A
  # configuration value that is present but malformed is refused at load,
  # alongside an absent one" and "A day count of zero is a valid
  # configuration, not a malformed one." Two of the six - both SIU
  # thresholds - accept a genuinely absent state and are proven so in the
  # rule below; a malformed value in either of those two is refused exactly
  # like the other four's absence, because "absent" and "wrong shape" are
  # different questions even for a value allowed to be absent.

  Background:
    Given the carrier rules source recognizes "AAAA", with a complete and valid entry for every one of the six values

  Rule: A recognized carrier's rules resolve to every value the domain will receive

    # Asserted per value, not as a single loaded/refused result. An
    # accept-or-refuse assertion alone would leave every one of these six
    # values free to swap for another valid one of the same shape and the
    # load would still succeed - the same inert-value-column failure item
    # 4g's first draft hit (docs/harness-findings.md, "Mutation cannot see a
    # fixed Given"). This is a plain scenario, not an outline, so every
    # quoted or numeric value below - on both the Given and the Then side -
    # is independently reachable by mutation without needing an Examples
    # table (docs/harness-findings.md, "Mutation cannot see a fixed Given":
    # a plain scenario's own quoted/numeric literals are mutation targets;
    # only Background and a fixed Given above an outline's Examples table
    # are not).
    #
    # 45 for the late reporting threshold is illustrative only, exactly as
    # in siu_indicators.feature: no late-reporting value has been agreed
    # (ASSUMPTIONS.md), it exists here solely to prove a configured value of
    # that kind resolves correctly, and it is deliberately not 30, so a
    # defect that wired the two thresholds to each other's field would still
    # be visible. 30 for recent policy inception is the real, kept value,
    # also matching siu_indicators.feature. The rule below covers the other
    # side of both fields - genuinely unconfigured - so between the two
    # scenarios each threshold is proven both ways.
    Scenario: A recognized carrier's rules resolve to every value the domain will receive
      Given the carrier "AAAA" requires the claimant name
      And "AAAA" does not require the claimant contact
      And "AAAA" recognizes the policy-number prefixes "HO;DP"
      And "AAAA" configures a late reporting threshold of 45 days
      And "AAAA" configures a recent policy inception threshold of 30 days
      And "AAAA" configures a duplicate match window of 60 days
      When the carrier configuration for "AAAA" is loaded
      Then the claimant name is received as "required"
      And the claimant contact is received as "not required"
      And the recognized policy-number prefixes are received as "HO;DP"
      And the late reporting threshold is received as 45 days
      And the recent policy inception threshold is received as 30 days
      And the duplicate match window is received as 60 days

  Rule: Either SIU threshold may be genuinely unconfigured without refusing the load

    # late_reporting_threshold_days and recent_inception_threshold_days are
    # the only two of the six values typed to accept an absent state -
    # compute_siu_indicators's signature on main takes int | None for both,
    # while validate's Collection[str] and two bools and find_duplicates's
    # plain int have no such affordance. ASSUMPTIONS.md says so explicitly:
    # an unsupplied value on those other four "has no analogue to
    # siu_indicators.feature's 'no threshold configured' scenarios - an
    # indicator can meaningfully resolve NOT_EVALUATED, while validation
    # must return blockers or none." The rule above proves the configured
    # side of both fields; item 2's own status also records the
    # late-reporting threshold shipping unconfigured today, which is the
    # side this scenario proves, for both fields at once, mirroring
    # siu_indicators.feature's own "Neither recent policy inception input is
    # present" - the same genuinely-optional shape, one layer earlier, where
    # refusing would be wrong in the opposite direction from the rule below.
    Scenario: A recognized carrier's rules load with neither SIU threshold configured
      Given the carrier "AAAA" requires the claimant name
      And "AAAA" does not require the claimant contact
      And "AAAA" recognizes the policy-number prefixes "HO;DP"
      And "AAAA" has no late reporting threshold configured
      And "AAAA" has no recent policy inception threshold configured
      And "AAAA" configures a duplicate match window of 60 days
      When the carrier configuration for "AAAA" is loaded
      Then the late reporting threshold is received as "not configured"
      And the recent policy inception threshold is received as "not configured"

  Rule: A carrier with no entry in the rules source has nothing to load

    # This is the loading-boundary rejection ASSUMPTIONS.md names as an
    # unwatched gap ("A carrier configuration crosses into the domain
    # already resolved") landing where that entry says it has to: at the
    # lookup itself, before any of the six values are read. The blank first
    # row keeps this table mixed rather than uniformly refused, giving the
    # engine a row with a different outcome to swap against - the same
    # technique validation.feature's outlines use (docs/harness-findings.md,
    # "A same-outcome column is sometimes the point of the rule, not a table
    # defect"). It relies on the Background's "AAAA" entry being complete
    # and valid, since this scenario states no value of its own.
    Scenario Outline: An unrecognized carrier code has no rules to load
      When the carrier configuration for "<carrier_code>" is loaded
      Then the load is <outcome>

      Examples:
        | carrier_code | outcome                |
        | AAAA         |                        |
        | ZZZZ         | CARRIER_NOT_CONFIGURED |

  Rule: A day count of zero is a valid configuration value, not a malformed one

    # A duplicate match window of zero compares only same-day notices, a
    # late reporting threshold of zero makes every notice late, a recent
    # policy inception threshold of zero counts only a same-day inception as
    # recent. Each is a carrier choice a deployment might make deliberately,
    # not a value a configuration loader has standing to refuse; whether it
    # is sensible carrier policy is a different question asked elsewhere.
    # ASSUMPTIONS.md, "A day count of zero is a valid configuration, not a
    # malformed one." This is a plain scenario for the same reason the first
    # rule's is: every value below, on both the Given and the Then side, is
    # then independently reachable by mutation. It states only the three
    # day-count fields under test, not the other three values - the
    # Background's carrier already has a complete and valid entry for those,
    # and restating them here without asserting them back would leave those
    # restated literals unreachable by mutation for no reason, the same gap
    # the first rule's own scenario exists to close for the values it does
    # assert. The rule below proves the other side of this same boundary - a
    # negative day count refuses the load - for all three fields this
    # applies to.
    Scenario: A day count of zero is accepted for every value that measures one
      Given "AAAA" configures a late reporting threshold of 0 days
      And "AAAA" configures a recent policy inception threshold of 0 days
      And "AAAA" configures a duplicate match window of 0 days
      When the carrier configuration for "AAAA" is loaded
      Then the late reporting threshold is received as 0 days
      And the recent policy inception threshold is received as 0 days
      And the duplicate match window is received as 0 days

  Rule: A required configuration value that is missing or malformed refuses the load, and the refusal names every value it rejected

    # The outline below and the plain scenario after it belong to this one
    # Rule and share one approval reason, per gauntlet mutant approve's
    # feature-and-scenario scoping (docs/harness-findings.md, "Approval
    # reasons decay in ways no key can catch"; QUEUE.md item 4c's recorded
    # cost at scale): the outline proves a single value's absence or
    # malformation refuses the load and names it correctly; the scenario
    # after it proves the general case, that several bad values in the same
    # entry are all named together rather than only the first found. A
    # single-value refusal is the degenerate case of the general rule, not a
    # separate one.
    #
    # An absent value and a malformed value are different reason codes
    # (ASSUMPTIONS.md, above), so this outline mixes both failure kinds,
    # plus one fully valid row, into a single table rather than splitting
    # them into same-outcome tables of their own: a same-outcome table gives
    # the engine no discriminating row to swap against, and every swap
    # inside it is inert (docs/harness-findings.md, "A same-outcome column
    # is sometimes the point of the rule, not a table defect"). Mixed here,
    # a swap of which field is named, what is wrong with it, or the blank
    # valid row all move the actual outcome away from what is asserted.
    #
    # The two SIU thresholds have no legitimate absent state to test here -
    # their absence is the prior rule's proven-fine case - so they carry a
    # malformed row each but no missing row, unlike the other four fields.
    #
    # The baseline values fixed in the Given lines below (name, contact,
    # prefixes, window) are not columns and so are not mutation targets here
    # - deliberate, not the item 4g failure mode: their own correctness is
    # already proven independently by the first rule's plain scenario. What
    # each row tests is carried entirely by its own <field> and <value>
    # cells, both blank together on exactly one row - the valid load - which
    # is why "absent" is a value a field can be configured as rather than a
    # separate step of its own: one override line, not two, means a row can
    # go wrong in only the two ways this Rule's title names, never in a
    # third way where one cell is blank and the other is not.
    Scenario Outline: A single value absent or malformed in a recognized carrier's entry refuses the load, naming it
      Given "AAAA" requires the claimant name
      And "AAAA" does not require the claimant contact
      And "AAAA" recognizes the policy-number prefixes "HO;DP"
      And "AAAA" configures a duplicate match window of 60 days
      And "AAAA" configures the <field> as <value>
      When the carrier configuration for "AAAA" is loaded
      Then the load is <outcome>

      Examples:
        | field                              | value                        | outcome                                                            |
        | claimant name                       | absent                      | MISSING_REQUIRED_CONFIGURATION:claimant name                      |
        | claimant name                       | neither yes nor no          | MALFORMED_REQUIRED_CONFIGURATION:claimant name                    |
        | claimant contact                    | absent                      | MISSING_REQUIRED_CONFIGURATION:claimant contact                   |
        | claimant contact                    | neither yes nor no          | MALFORMED_REQUIRED_CONFIGURATION:claimant contact                 |
        | recognized policy-number prefixes   | absent                      | MISSING_REQUIRED_CONFIGURATION:recognized policy-number prefixes  |
        | recognized policy-number prefixes   | an empty set                | MALFORMED_REQUIRED_CONFIGURATION:recognized policy-number prefixes|
        | late reporting threshold            | a negative number of days   | MALFORMED_REQUIRED_CONFIGURATION:late reporting threshold         |
        | recent policy inception threshold   | a negative number of days   | MALFORMED_REQUIRED_CONFIGURATION:recent policy inception threshold|
        | duplicate match window              | absent                      | MISSING_REQUIRED_CONFIGURATION:duplicate match window             |
        | duplicate match window              | a negative number of days   | MALFORMED_REQUIRED_CONFIGURATION:duplicate match window           |
        |                                      |                              |                                                                    |

    # Proves the collection behavior the outline above cannot: a refusal is
    # a list, and every entry on it is named, not only the one encountered
    # first. Mixes a missing value with two malformed ones deliberately, so
    # the same mechanism is shown covering both failure kinds at once rather
    # than only the kind each row above tests in isolation.
    #
    # A step's data table is discarded before the Gherkin IR ever sees it -
    # gauntlet.acceptance.gherkin.Step carries only keyword, text, line, and
    # column - so the assertion below is carried in an Examples column
    # instead, in the compact CODE:field form validation.feature's own "the
    # blockers are <compact>" step already uses, pairs joined by ";"
    # (docs/harness-findings.md, "Acceptance mutation does not see
    # everything").
    #
    # The order itself is a business decision, the same one that gave this
    # file two reason codes rather than one: malformed before missing,
    # because a carrier onboarded wrongly and a carrier never onboarded are
    # different defects found by different people. Within a code, values are
    # sorted on the field name as this specification writes it - the
    # business term the CODE:field pair renders - not on any internal key,
    # so the order stays checkable from the specification alone.
    # ASSUMPTIONS.md, "A missing configuration value and a malformed one are
    # different reason codes." As a dated consistency check rather than the
    # reason for the rule: validate()'s own sort key agrees with this one on
    # today's six values (verified 2026-08-22), though it sorts on the
    # model's snake_case field name, a different string that need not always
    # agree with the rendered one.
    #
    # This scenario is a plain scenario, not an outline, so the quoted
    # refusal string below is independently reachable by mutation
    # (docs/harness-findings.md, "Acceptance mutation does not see
    # everything", the correction on a one-row outline forfeiting its own
    # step literals for one marker substitution). Mutation cannot permute a
    # list, so this row alone proves only that the assertion is read, not
    # that the order is enforced; the scenario after it supplies the row
    # mutation cannot.
    Scenario: Several missing and malformed values in the same entry are all named in one refusal, in canonical order
      Given "AAAA"'s configuration is missing the claimant contact
      And "AAAA" recognizes no policy-number prefixes
      And "AAAA" configures the duplicate match window as a negative number of days
      When the carrier configuration for "AAAA" is loaded
      Then every rejected value is named in the refusal as "MALFORMED_REQUIRED_CONFIGURATION:duplicate match window;MALFORMED_REQUIRED_CONFIGURATION:recognized policy-number prefixes;MISSING_REQUIRED_CONFIGURATION:claimant contact"

    # Isolates alphabetical-within-a-code from the rule above: both values
    # here are the same code, so this row cannot pass by malformed-before-
    # missing alone, and the Given lines name them in the opposite order
    # from the one the refusal asserts, so appending in check order - or in
    # Given order - fails it. validation.feature's equivalent rule carries
    # one scenario per isolated property; this is the property the scenario
    # above cannot isolate on its own.
    Scenario: Two values missing from the same entry are named in alphabetical order, not the order they were found
      Given "AAAA"'s configuration is missing the claimant name
      And "AAAA"'s configuration is missing the claimant contact
      When the carrier configuration for "AAAA" is loaded
      Then every rejected value is named in the refusal as "MISSING_REQUIRED_CONFIGURATION:claimant contact;MISSING_REQUIRED_CONFIGURATION:claimant name"
