Feature: Carrier configuration loading

  As a claims intake system administering more than one carrier
  I need each carrier's own required-field, threshold, and window rules
  resolved before any domain rule runs
  So that no domain function is ever called with a value nobody configured,
  and a carrier this deployment has no rules for is refused before that
  ever happens

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
  # CARRIER_NOT_CONFIGURED and MISSING_REQUIRED_CONFIGURATION are the
  # complete set today. Escalate before adding to it.

  # Only presence is specified below for the four values with no legitimate
  # absent state - not the shape of a present-but-malformed value (a string
  # where a boolean is expected, an empty prefix collection, a negative
  # window). Absence is the one case every "no domain default" item so far
  # has actually decided (items 2, 3, 4g, 4j); a malformed-but-present value
  # is a caller-contract question this draft does not answer and flags
  # rather than guesses at.

  Background:
    Given the carrier rules source recognizes "AAAA"

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
    # refusing would be wrong in the opposite direction from Rule 4 below.
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
    # defect").
    Scenario Outline: An unrecognized carrier code has no rules to load
      When the carrier configuration for "<carrier_code>" is loaded
      Then the load is <outcome>

      Examples:
        | carrier_code | outcome                |
        | AAAA         |                        |
        | ZZZZ         | CARRIER_NOT_CONFIGURED |

  Rule: A required value missing from a recognized carrier's entry refuses the load

    # The four values with no absent-and-legitimate state, per the rule
    # above: claimant_name_required, claimant_contact_required,
    # recognized_policy_number_prefixes, and window_days. Kept together in
    # one scenario rather than one per field - they are inherently a family
    # of same-shaped refusals, and gauntlet mutant approve scopes only by
    # feature file and --scenario, so scattering them across scenarios would
    # cost one approval reason per field for what is the same argument each
    # time (docs/harness-findings.md, "Approval reasons decay in ways no key
    # can catch"; QUEUE.md item 4c's recorded cost at scale). The first row
    # is fully configured and loads, keeping this table mixed for the same
    # reason the rule above's table is.
    #
    # The baseline values fixed in each row's own Given lines below (name,
    # contact, prefixes, window) are not columns here and so are not
    # mutation targets in this scenario - that is deliberate, not the item
    # 4g failure mode: their own correctness is already proven independently
    # by the plain scenario above. What this outline tests is a different
    # axis entirely - presence - carried by the missing_field column, which
    # is the one that varies and the one this outline is about.
    Scenario Outline: A required configuration value must be present in a recognized carrier's entry
      Given "AAAA" requires the claimant name
      And "AAAA" does not require the claimant contact
      And "AAAA" recognizes the policy-number prefixes "HO;AU"
      And "AAAA" configures a duplicate match window of 60 days
      And the "AAAA" configuration is missing "<missing_field>"
      When the carrier configuration for "AAAA" is loaded
      Then the load is <outcome>

      Examples:
        | missing_field                     | outcome                                                           |
        |                                   |                                                                   |
        | claimant_name_required            | MISSING_REQUIRED_CONFIGURATION:claimant_name_required             |
        | claimant_contact_required         | MISSING_REQUIRED_CONFIGURATION:claimant_contact_required          |
        | recognized_policy_number_prefixes | MISSING_REQUIRED_CONFIGURATION:recognized_policy_number_prefixes  |
        | window_days                       | MISSING_REQUIRED_CONFIGURATION:window_days                        |
