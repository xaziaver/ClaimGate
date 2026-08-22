Feature: Carrier configuration loading

  As a claims intake system administering more than one carrier
  I need each carrier's own required-field, threshold, and window rules
  resolved before any domain rule runs
  So that no domain function is ever called with a value nobody configured,
  and a carrier this deployment has no usable rules for is refused before
  that ever happens

  # The six values loaded here are every caller-supplied value phase 1 moved
  # out of the domain with no default, verified against the three signatures
  # on main rather than counted from QUEUE.md: validate's
  # claimant_name_required, claimant_contact_required, and
  # recognized_policy_number_prefixes (items 4g, 4j); compute_siu_indicators's
  # late_reporting_threshold_days and recent_inception_threshold_days (item
  # 2); find_duplicates's window_days (item 3). Nothing below calls any of
  # those three functions - this is the layer that resolves what they will be
  # called with, and the shell cannot call any of them until it does
  # (QUEUE.md item 5a).

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
  # CARRIER_NOT_CONFIGURED and INVALID_REQUIRED_CONFIGURATION are the
  # complete set today. The second is a rename of an earlier draft's
  # MISSING_REQUIRED_CONFIGURATION, widened to cover what this draft adds -
  # see the note below on malformed values - because "missing" stopped being
  # true of everything the code has to name once a present-but-malformed
  # value is also refused under it. Escalate before adding a third code.

  # A required value is refused whether it is absent from a recognized
  # carrier's entry or present in a shape the receiving function cannot use.
  # What counts as malformed follows from each value's own type, not a new
  # vocabulary: a non-boolean where claimant_name_required or
  # claimant_contact_required needs a boolean, a non-integer or negative
  # number where late_reporting_threshold_days, recent_inception_threshold_days,
  # or window_days needs a day count, an empty collection where
  # recognized_policy_number_prefixes needs at least one recognized prefix.
  # ASSUMPTIONS.md, "A configuration value that is present but malformed is
  # refused at load, alongside an absent one." Two of the six - both SIU
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
      And "AAAA" recognizes the policy-number prefixes "HO;AU"
      And "AAAA" configures a late reporting threshold of 45 days
      And "AAAA" configures a recent policy inception threshold of 30 days
      And "AAAA" configures a duplicate match window of 60 days
      When the carrier configuration for "AAAA" is loaded
      Then the claimant name is received as "required"
      And the claimant contact is received as "not required"
      And the recognized policy-number prefixes are received as "HO;AU"
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
      And "AAAA" recognizes the policy-number prefixes "HO;AU"
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

  Rule: A required configuration value that is missing or malformed refuses the load, and the refusal names every value it rejected

    # Two scenario outlines below each exercise one bad value at a time -
    # the degenerate case of a collection - and a plain scenario after them
    # proves the general case: several bad values in the same entry are all
    # named together, not just the first found. All three belong to this one
    # Rule and share one approval reason, per gauntlet mutant approve's
    # feature-and-scenario scoping (docs/harness-findings.md, "Approval
    # reasons decay in ways no key can catch"; QUEUE.md item 4c's recorded
    # cost at scale) and because a single-value refusal is a special case of
    # the general rule, not a separate one.
    #
    # The baseline values fixed in each row's own Given lines below (name,
    # contact, prefixes, window) are not columns in either outline and so
    # are not mutation targets there - deliberate, not the item 4g failure
    # mode: their own correctness is already proven independently by the
    # first rule's plain scenario. What each outline tests is a different
    # axis entirely, carried by the one column that varies.

    Scenario Outline: A single value missing from a recognized carrier's entry refuses the load, naming it
      Given "AAAA" requires the claimant name
      And "AAAA" does not require the claimant contact
      And "AAAA" recognizes the policy-number prefixes "HO;AU"
      And "AAAA" configures a duplicate match window of 60 days
      And "AAAA"'s configuration is missing the <field>
      When the carrier configuration for "AAAA" is loaded
      Then the load is <outcome>

      Examples:
        | field                              | outcome                                                            |
        |                                     |                                                                     |
        | claimant name                       | INVALID_REQUIRED_CONFIGURATION:claimant name                       |
        | claimant contact                    | INVALID_REQUIRED_CONFIGURATION:claimant contact                    |
        | recognized policy-number prefixes   | INVALID_REQUIRED_CONFIGURATION:recognized policy-number prefixes   |
        | duplicate match window              | INVALID_REQUIRED_CONFIGURATION:duplicate match window              |

    # A malformed value is present but unusable, never absent - the other
    # half of ASSUMPTIONS.md's "refused at load, alongside an absent one."
    # The two SIU thresholds appear only here, not in the outline above,
    # because their own absence is the prior rule's proven-fine case; what
    # this outline proves for them is narrower and different - a value that
    # is there but the wrong shape is refused exactly as it would be for the
    # four fields with no legitimate absent state at all.
    Scenario Outline: A single value present but malformed in a recognized carrier's entry refuses the load, naming it
      Given "AAAA" requires the claimant name
      And "AAAA" does not require the claimant contact
      And "AAAA" recognizes the policy-number prefixes "HO;AU"
      And "AAAA" configures a duplicate match window of 60 days
      And "AAAA" configures the <field> as <value>
      When the carrier configuration for "AAAA" is loaded
      Then the load is INVALID_REQUIRED_CONFIGURATION:<field>

      Examples:
        | field                              | value                        |
        | claimant name                       | neither yes nor no           |
        | claimant contact                    | neither yes nor no           |
        | recognized policy-number prefixes   | an empty set                 |
        | duplicate match window              | a negative number of days    |
        | late reporting threshold            | a negative number of days    |
        | recent policy inception threshold   | a negative number of days    |

    # Proves the collection behavior the two outlines above cannot: a
    # refusal is a list, and every entry on it is named, not only the one
    # encountered first. Mixes a missing value with two malformed ones
    # deliberately, so the same mechanism is shown covering both failure
    # kinds at once rather than only the kind each outline tests in
    # isolation.
    Scenario: Several missing and malformed values in the same entry are all named in one refusal
      Given "AAAA" requires the claimant name
      And "AAAA"'s configuration is missing the claimant contact
      And "AAAA" recognizes no policy-number prefixes
      And "AAAA" configures the duplicate match window as a negative number of days
      When the carrier configuration for "AAAA" is loaded
      Then every rejected value is named in the refusal:
        | INVALID_REQUIRED_CONFIGURATION | claimant contact                  |
        | INVALID_REQUIRED_CONFIGURATION | recognized policy-number prefixes |
        | INVALID_REQUIRED_CONFIGURATION | duplicate match window             |
