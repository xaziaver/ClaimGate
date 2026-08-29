Feature: Jurisdiction selection

  As a claims intake system administering carriers that write in more than one
  state
  I need the jurisdiction that governs a notice to be selected from where the
  insured property is, and a property outside the jurisdictions this deployment
  supports to be marked for a human rather than blocked or judged under a
  calendar nobody chose for it
  So that a notice is never dated by an assumption, and a notice this
  deployment cannot yet judge is still received, still triaged, and visible as
  needing a person

  # PHASE2_DESIGN.md's "Jurisdiction axis": statutory rules vary by
  # jurisdiction, not by carrier. Jurisdiction is derived from the insured
  # risk's property location - the property's state - never from the
  # carrier's domicile and never from the reporter's address. Exactly one
  # jurisdiction is populated here, Florida; the requirement is that Florida
  # is one entry in a keyed structure, not that a second jurisdiction exists.

  # Two of that section's three negatives are not assertable by any scenario
  # in this file, and saying so is not a gap being papered over. The
  # carrier's domicile is not an input anywhere in phase 2 - the carrier
  # reference carries name, NAIC company and NAIC group and no location - and
  # the reporter's address is not captured at all, so neither can be varied
  # against a fixed property state to show it does not move the outcome. The
  # third negative, that the carrier does not select the jurisdiction, is
  # assertable in principle but not affordably here: a second carrier reaches
  # intake only with a full rules entry of its own, and a carrier the identity
  # reference recognizes whose rules cannot be resolved is a decided answer as
  # of 2026-08-28 - 500 with CARRIER_RULES_UNRESOLVABLE, this deployment's own
  # fault and not the reporter's - stated by the specs that own the
  # deployment-fault subject rather than by this one. No scenario here reaches
  # it, and that is a scope choice rather than a consequence of the question
  # having been open: a carrier whose rules will not load is answered before a
  # jurisdiction is ever selected, so such a scenario would have no selection
  # left to assert. That claim is left to the carrier-set swappability test,
  # which is where an absence of hardcoding is proven structurally rather than
  # by example.

  # "Today" reaches the domain from the jurisdiction's own timezone, never
  # from server local time or the UTC calendar day - jurisdiction_date.feature
  # specifies that conversion in isolation, and this file specifies where the
  # timezone it converts under comes from. Before this item, a caller supplied
  # the timezone name on every submission; that was scaffolding, and
  # ASSUMPTIONS.md's "Timezone-correct 'now'" has always had the name arriving
  # from configuration rather than from a reporter.

  # A known limit of one entry per jurisdiction, recorded rather than
  # discovered later: Florida spans two timezones. The America/Chicago zone is
  # Escambia, Santa Rosa, Okaloosa, Walton, Holmes, Washington, Bay, Jackson
  # and Calhoun entirely, plus the part of Gulf County west of the boundary -
  # the line is 49 CFR 71.5(f), running down the Apalachicola River to the
  # Jackson River, along the Intracoastal Waterway to the west line of Gulf
  # County, then south - and the rest of the state is America/New_York
  # (ASSUMPTIONS.md, "The jurisdiction timezone is a parameter of the
  # conversion, not a constant in it"). The affected book includes Panama
  # City, Panama City Beach, Destin and Fort Walton Beach - coastal
  # wind-exposed residential territory, not a Pensacola footnote. A
  # jurisdiction keyed by state holds one timezone, so a notice on a
  # Pensacola risk is dated Eastern here. For one hour a day that skews two
  # answers, both in the tolerant direction: a loss dated tomorrow by the
  # Central clock passes the future-date check unflagged (Eastern's today has
  # already reached it), and the late reporting interval reads up to one day
  # long, which flags early on an advisory indicator. No false block is
  # possible - Eastern's date is never behind Central's. Ratified as
  # acceptable for phase 2; recorded in ASSUMPTIONS.md, and no scenario below
  # asserts the skew either way.

  Background:
    # Carrier configuration is carrier_configuration.feature's subject and is
    # stated here only so intake can run. The claimant-name requirement never
    # fires anywhere below: every notice reports wind_hail, a Section I
    # property peril, and the requirement applies to Section II losses.
    Given the carrier "AAAA" requires the claimant name
    And "AAAA" does not require the claimant contact
    And "AAAA" recognizes the policy-number prefixes "HO;DP"
    And "AAAA" has no late reporting threshold configured
    And "AAAA" configures a recent policy inception threshold of 30 days
    And "AAAA" configures a duplicate match window of 60 days
    And the notice is submitted by carrier "AAAA"
    And the insured property is in "FL"
    And the notice is submitted at "2026-08-24T16:00Z"
    And the notice reports a policy number of "HO-1234567"
    And the notice reports a loss date of "2026-06-01"
    And the notice reports a loss type of "wind_hail"
    And the notice reports a notice type of "INITIAL"

  Rule: A notice is judged against the calendar date of the jurisdiction the insured property is in

    # This is the proof that the jurisdiction actually supplies the date the
    # domain receives, rather than the date being derived some other way that
    # happens to agree. Both rows report the same loss date and differ only in
    # the instant the notice arrived; between them, only the 02:30Z row
    # separates the two calendars - at 04:30Z the UTC date and Florida's agree
    # - so that row alone is the discriminator, and the 04:30Z row is here to
    # prove the agreement case rather than to catch anyone.
    # 2026-06-11T04:30Z is 00:30 on 2026-06-11 in Florida, so a
    # loss on 2026-06-11 is today rather than ahead of it; 2026-06-11T02:30Z
    # is still 22:30 on 2026-06-10 there, so the same loss date is ahead of
    # the jurisdiction's today and blocks.
    #
    # The instants and the blocker are notice_intake.feature's own proven pair
    # rather than new ones. What differs, and what this file adds, is where
    # the timezone comes from: there, a caller stated it on the submission;
    # here, nothing states it and the jurisdiction the property sits in
    # supplies it.
    Scenario Outline: The jurisdiction's calendar date, not the UTC calendar date, decides whether a loss date is ahead of today
      Given the notice is submitted at "<submitted_at>"
      And the notice reports a loss date of "2026-06-11"
      When the notice is submitted for intake
      Then the notice's state is <state>
      And the notice's blockers are <blockers>
      And the future-dated-loss determination recorded for the notice is <determination>

      Examples:
        | submitted_at      | state   | blockers                      | determination |
        | 2026-06-11T04:30Z | TRIAGED |                               | FALSE         |
        | 2026-06-11T02:30Z | PENDED  | LOSS_DATE_IN_FUTURE:loss_date | TRUE          |

  Rule: A property state this deployment supports no jurisdiction for does not block the notice, it marks it for a person

    # There is no rejected, invalid or discarded state and there will not be
    # one (CLAUDE.md): notice given is notice received, and the Fla. Stat.
    # 627.70131(1)(a) acknowledgment clock starts at receipt regardless of
    # whether this deployment knows the law where the property sits. So an
    # unsupported property state is not a blocker and not a refusal - the
    # notice is created, triaged, and carries a marking that a person can
    # search on.
    #
    # A state this deployment has no entry for and no state at all are the
    # same marking deliberately, and grouping them in one scenario is what
    # lets one equivalence reason cover both if a substitution between them
    # survives: they differ in what is known about the risk, and nothing
    # downstream of this file does anything different with the two. Whether
    # they should be distinguishable at all - two markings rather than one -
    # is not something this draft decides.
    Scenario Outline: A notice whose property state has no supported jurisdiction is still created and triaged
      Given the insured property is in "<property_state>"
      When the notice is submitted for intake
      Then the response is <response>
      And the notice's state is <state>
      And the notice's jurisdiction marking is <jurisdiction_marking>

      # The lookup is exact-match and its misses are marked for a person, never
      # normalized into a guess about what the reporter meant.
      Examples:
        | property_state | response | state   | jurisdiction_marking     |
        | FL             | 201      | TRIAGED | none                     |
        | GA             | 201      | TRIAGED | jurisdiction_unsupported |
        | absent         | 201      | TRIAGED | jurisdiction_unsupported |
        | fl             | 201      | TRIAGED | jurisdiction_unsupported |

  Rule: A determination that needs the jurisdiction's calendar date is recorded as not evaluated, naming what was missing

    # RATIFIED 2026-08-26, advisor-recommended - every row in this rule's two scenarios.
    # PHASE2_DESIGN.md's "Jurisdiction axis" predates the machinery it
    # collides with here and is silent on it: an unsupported property state
    # means no jurisdiction, so no timezone, so no jurisdiction today, and
    # "today" is what the future-dated-loss determination and the late
    # reporting indicator are both counted against. The shape below follows
    # the closest thing on file - "Notice type and window selection"'s rule
    # that a LOSS_ASSESSMENT notice's late-notice attribute resolves to an
    # explicit not-computable outcome with a reason, never a silent fallback -
    # and CLAUDE.md's standing constraint that a result which was not computed
    # is never reported as a negative. The human ratified it on 2026-08-26,
    # and the ratification is what adds the reason code: NO_JURISDICTION_DATE
    # enters two closed enumerations as two codes of one spelling - the
    # future-dated-loss determination's reasons and the SIU indicator reasons -
    # by that ratification and by nothing else.

    # The determination has to be recorded as its own three-valued outcome
    # because the place a positive one goes - the notice's blockers - is the
    # place that would block, and an unsupported jurisdiction must not block.
    # An absent blocker would then be the only trace, and an absent blocker is
    # exactly what "the loss date was checked and is not ahead of today" looks
    # like. The first two rows report a loss date past the Background's arrival
    # instant and differ in nothing but where the property is.
    #
    # DRAFTED FOR REVIEW, item 5j, 2026-08-28. Not ratified. The third row is
    # the both-absent case - no loss date and no supported jurisdiction - and
    # which reason it names is the whole of what it is for. NO_LOSS_DATE
    # outranks NO_JURISDICTION_DATE (ASSUMPTIONS.md, "Item 5h, three
    # decisions", decision 2, ratified 2026-08-27): the loss date is this
    # determination's subject and today only the yardstick it is held against,
    # so the missing subject is the more basic absence. Nothing states that
    # ordering today. validation.feature's rows always have a today, so its
    # absent-loss-date row cannot separate the two reasons, and that file says
    # so and leaves the row to this one; a reordering of the two checks
    # therefore fails no test, and mutation does not reorder statements. That
    # is item 4k's shape, and closing it is why this row exists.
    #
    # The loss date moves out of the fixed Given and into a column so that the
    # absence is a value the specification carries rather than a sentence about
    # it. A fixed Given above an Examples table is never mutated, so stating
    # the row's subject there would have left it asserted by nothing.
    #
    # Both of the row's other facts are stated rather than inferred: an absent
    # loss date is a blocker in its own right, so the state and blocker columns
    # move with the determination, and the second row remains what shows that
    # an unsupported jurisdiction on its own does not block.
    Scenario Outline: What the future-dated-loss determination records when it evaluates, when the jurisdiction date is missing, and when the loss date is missing too
      Given the insured property is in "<property_state>"
      And the notice reports a loss date of "<loss_date>"
      When the notice is submitted for intake
      Then the notice's state is <state>
      And the notice's blockers are <blockers>
      And the future-dated-loss determination recorded for the notice is <determination>

      Examples:
        | property_state | loss_date  | state   | blockers                         | determination                      |
        | FL             | 2026-09-01 | PENDED  | LOSS_DATE_IN_FUTURE:loss_date    | TRUE                               |
        | GA             | 2026-09-01 | TRIAGED |                                  | NOT_EVALUATED:NO_JURISDICTION_DATE |
        | GA             | absent     | PENDED  | MISSING_REQUIRED_FIELD:loss_date | NOT_EVALUATED:NO_LOSS_DATE         |

    # The same gap reaching the SIU trail. Item 5f requires an evaluation on
    # every transition into TRIAGED, and an unsupported-jurisdiction notice
    # is triaged, so the event is written either way and only what it says
    # changes. The Florida row's reason is the one the Background already
    # produces - this carrier has no late reporting threshold configured - and
    # it is here to show that the unsupported row's reason is a different
    # fact, not the same silence spelled differently.
    #
    # Which reason a doubly-unevaluable indicator names is settled by the
    # precedence already ratified for the recent policy inception indicator
    # (ASSUMPTIONS.md, carried requirements): the reason names the gap that
    # would still block evaluation if the other were closed. A configured
    # threshold cannot help without a date to count to, so the missing
    # jurisdiction date is named and the absent threshold is not.
    Scenario Outline: A late reporting indicator with no jurisdiction date to count to names that gap, not the absent threshold
      Given the insured property is in "<property_state>"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the late reporting indicator recorded for the notice is NOT_EVALUATED with reason <reason>

      Examples:
        | property_state | reason                  |
        | FL             | NO_THRESHOLD_CONFIGURED |
        | GA             | NO_JURISDICTION_DATE    |

    # The corner the pair above cannot reach: its only unsupported row also
    # has no threshold configured, so nothing there separates "the reason
    # names the date that is missing" from "the reason names whichever gap
    # this carrier happens to have." Here the carrier does have a threshold -
    # the Background clears it and this scenario's own Given puts one back -
    # and the unsupported row still names the missing jurisdiction date,
    # while the supported row evaluates against that same threshold and
    # returns a value, which is what shows the threshold is really there.
    #
    # The two spellings sharing one column are both spellings this project
    # already states elsewhere, rendered whole rather than assembled from
    # parts: siu_separation.feature asserts a recorded indicator as a bare
    # value on one scenario and as not evaluated with a named reason on
    # another. Neither is the compact NOT_EVALUATED:CODE form the
    # future-dated-loss determination uses above, and that separation is
    # deliberate - two subjects, two spellings.
    #
    # Arithmetic, recomputed rather than carried: 2026-07-09 is 46 days
    # before the receipt's jurisdiction date of 2026-08-24, which is more
    # than 45, so TRUE. 45 is chosen for that and not for being a round
    # number - 46 days against a 46-day threshold is FALSE, so the asserted
    # result pins the threshold rather than tolerating it. It is
    # illustrative: no such value has been approved for any carrier.
    Scenario Outline: A carrier that does have a late reporting threshold still has the missing jurisdiction date named
      Given "AAAA" configures a late reporting threshold of 45 days
      And the notice reports a loss date of "2026-07-09"
      And the insured property is in "<property_state>"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the late reporting indicator recorded for the notice is <late_reporting>

      Examples:
        | property_state | late_reporting                                 |
        | FL             | TRUE                                           |
        | GA             | NOT_EVALUATED with reason NO_JURISDICTION_DATE |

  Rule: The jurisdiction is read from the notice's merged current view, not from what was known at receipt

    # RATIFIED 2026-08-26, advisor-recommended - both scenarios in this rule.
    # ASSUMPTIONS.md, same date: the zone that dates a resolution's SIU
    # interval comes from the notice's merged view rather than from what was
    # known when it arrived. Item 5f decision 2 fixed the instant an interval
    # is counted from and left the timezone open; this rule closes it, and it
    # closes the same gap for the future-dated-loss determination in the same
    # breath, because both are counted against one jurisdiction today.
    #
    # There is one reachable way into this state and both scenarios below are
    # built that way. A notice that reached TRIAGED with no supported
    # jurisdiction can never be told where the property is afterwards:
    # resolution.feature's first rule answers a resolution on any notice that
    # is not PENDED with 409 and persists nothing. So the notice here arrives
    # with its property state absent AND its policy number absent. It pends
    # for MISSING_REQUIRED_FIELD:policy_number - a blocker with nothing to do
    # with the jurisdiction, which is the point, since an unsupported
    # jurisdiction never blocks - while carrying jurisdiction_unsupported,
    # and the reviewer's resolution supplies both fields together.
    #
    # An implementation that resolves the timezone once, at receipt, passes
    # every other scenario in this file and fails the first row of each
    # scenario below: it had no jurisdiction when the notice arrived, so it
    # records NOT_EVALUATED on both rows and the computed value the FL row
    # asserts never appears.

    Scenario Outline: A future-dated-loss determination is made under the jurisdiction the resolution supplies
      Given the insured property is in "absent"
      And the notice reports a policy number of "absent"
      And the notice is submitted for intake
      And the notice's state is PENDED
      And the notice's jurisdiction marking is jurisdiction_unsupported
      And the reviewer is identified as "adjuster-4471"
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer supplies a property state of "<supplied_property_state>"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is 200
      And the notice's state is TRIAGED
      And the future-dated-loss determination recorded for the notice is <determination>

      Examples:
        | supplied_property_state | determination                      |
        | FL                      | FALSE                              |
        | absent                  | NOT_EVALUATED:NO_JURISDICTION_DATE |

    # The same gap reaching the SIU trail, on the transition item 5f requires
    # an evaluation on: PENDED to TRIAGED. The interval is counted from the
    # jurisdiction date of the instant the notice was received, not of the
    # instant the reviewer released it - item 5f decision 2, inherited here
    # rather than re-proven, which is siu_separation.feature's own subject.
    # What this scenario adds is the timezone that date is read in, which
    # decision 2 left open: it comes from the property state the resolution
    # supplied, so the row that supplies none has no date to count to and
    # says so.
    #
    # Arithmetic, recomputed rather than carried: the receipt instant is
    # 12:00 on 2026-08-24 in Florida, and 2026-07-09 is 46 days before it,
    # which is more than 45, so TRUE. The threshold is pinned by that result
    # the same way the scenario above pins it, and the second row cannot pass
    # by coincidence with a FALSE standing in for an unevaluated one, because
    # FALSE is not what it asserts.
    Scenario Outline: A late reporting interval is counted under the jurisdiction the resolution supplies
      Given "AAAA" configures a late reporting threshold of 45 days
      And the notice reports a loss date of "2026-07-09"
      And the insured property is in "absent"
      And the notice reports a policy number of "absent"
      And the notice is submitted for intake
      And the notice's state is PENDED
      And the notice's jurisdiction marking is jurisdiction_unsupported
      And the reviewer is identified as "adjuster-4471"
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer supplies a property state of "<supplied_property_state>"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is 200
      And the notice's state is TRIAGED
      And the late reporting indicator recorded for the notice is <late_reporting>

      Examples:
        | supplied_property_state | late_reporting                                 |
        | FL                      | TRUE                                           |
        | absent                  | NOT_EVALUATED with reason NO_JURISDICTION_DATE |
