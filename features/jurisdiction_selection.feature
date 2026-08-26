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
  # reference recognizes whose rules cannot be resolved is QUEUE.md item 5i's
  # undecided status code, which no scenario in this file may reach. That
  # claim is left to the carrier-set swappability test, which is where an
  # absence of hardcoding is proven structurally rather than by example.

  # "Today" reaches the domain from the jurisdiction's own timezone, never
  # from server local time or the UTC calendar day - jurisdiction_date.feature
  # specifies that conversion in isolation, and this file specifies where the
  # timezone it converts under comes from. Before this item, a caller supplied
  # the timezone name on every submission; that was scaffolding, and
  # ASSUMPTIONS.md's "Timezone-correct 'now'" has always had the name arriving
  # from configuration rather than from a reporter.

  # A known limit of one entry per jurisdiction, recorded rather than
  # discovered later: Florida spans two timezones. The western panhandle -
  # Escambia, Santa Rosa, Okaloosa and most of Walton - is America/Chicago and
  # the rest of the state is America/New_York (ASSUMPTIONS.md, "The
  # jurisdiction timezone is a parameter of the conversion, not a constant in
  # it"). A jurisdiction keyed by state holds one timezone, so a notice on a
  # Pensacola risk is dated Eastern here. That is a real wrong answer around
  # midnight Central on the field that already drives LOSS_DATE_IN_FUTURE, and
  # no scenario below asserts it either way.

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
    # the instant the notice arrived; between them, an implementation reading
    # the UTC calendar date instead of Florida's is wrong on both, in the same
    # direction. 2026-06-11T04:30Z is 00:30 on 2026-06-11 in Florida, so a
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

      Examples:
        | submitted_at      | state   | blockers                      |
        | 2026-06-11T04:30Z | TRIAGED |                               |
        | 2026-06-11T02:30Z | PENDED  | LOSS_DATE_IN_FUTURE:loss_date |

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

      Examples:
        | property_state | response | state   | jurisdiction_marking     |
        | FL             | 201      | TRIAGED | none                     |
        | GA             | 201      | TRIAGED | jurisdiction_unsupported |
        | absent         | 201      | TRIAGED | jurisdiction_unsupported |

  Rule: A determination that needs the jurisdiction's calendar date is recorded as not evaluated, naming what was missing

    # RECOMMENDED, NOT RATIFIED - every row in this rule's two scenarios.
    # PHASE2_DESIGN.md's "Jurisdiction axis" predates the machinery it
    # collides with here and is silent on it: an unsupported property state
    # means no jurisdiction, so no timezone, so no jurisdiction today, and
    # "today" is what the future-dated-loss determination and the late
    # reporting indicator are both counted against. The shape below follows
    # the closest thing on file - "Notice type and window selection"'s rule
    # that a LOSS_ASSESSMENT notice's late-notice attribute resolves to an
    # explicit not-computable outcome with a reason, never a silent fallback -
    # and CLAUDE.md's standing constraint that a result which was not computed
    # is never reported as a negative. It is a recommendation until a human
    # ratifies it, and the reason code it introduces belongs to a closed
    # enumeration that only a human may add to.

    # The determination has to be recorded as its own three-valued outcome
    # because the place a positive one goes - the notice's blockers - is the
    # place that would block, and an unsupported jurisdiction must not block.
    # An absent blocker would then be the only trace, and an absent blocker is
    # exactly what "the loss date was checked and is not ahead of today" looks
    # like. Both rows below report a loss date past the Background's arrival
    # instant, so the two rows differ in nothing but where the property is.
    Scenario Outline: A future-dated loss on a notice with no supported jurisdiction is recorded as not evaluated rather than as not future
      Given the insured property is in "<property_state>"
      And the notice reports a loss date of "2026-09-01"
      When the notice is submitted for intake
      Then the notice's state is <state>
      And the notice's blockers are <blockers>
      And the future-dated-loss determination recorded for the notice is <determination>

      Examples:
        | property_state | state   | blockers                      | determination                      |
        | FL             | PENDED  | LOSS_DATE_IN_FUTURE:loss_date | TRUE                               |
        | GA             | TRIAGED |                               | NOT_EVALUATED:NO_JURISDICTION_DATE |

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
