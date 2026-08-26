Feature: Keeping SIU indicators off the notice

  As a claims intake system
  I need every SIU indicator this system records to be written once, when the
  notice becomes something an investigator would look at, and to be readable
  by nobody who reads an ordinary notice
  So that a trained investigator has a dated record of what was observed and
  under which rules, and a reporter, an adjuster, or an auditor reading the
  notice learns nothing about it at all

  # PHASE2_DESIGN.md's "SIU handling" section is this file's specification
  # input, together with its Audit log section and the Record state model's
  # transitions into TRIAGED. The vocabulary is siu_indicators.feature's and
  # is not reinvented here: the indicators are the late reporting indicator
  # and the recent policy inception indicator, their values are TRUE, FALSE,
  # and NOT_EVALUATED with a reason, and the reason codes are the closed pair
  # NO_THRESHOLD_CONFIGURED and NO_CONTINUOUS_COVERAGE_DATE. Nothing below
  # adds an indicator, a value, or a reason code; adding one is a business
  # decision and an escalation, not a drafting choice.
  #
  # The system records observations. It does not identify fraud, does not
  # identify fraud-prone patterns, and reaches no conclusion about any claim
  # or claimant. Where siu_indicators.feature specifies what each indicator
  # resolves to from a given set of inputs, this file specifies four
  # different things: when an indicator is evaluated at all, what is written
  # down when it is, which day the interval is counted from, and who can see
  # the result. An indicator's arithmetic is not re-proven here.
  #
  # WHAT THIS FILE DECIDES, and where it was decided - six points
  # PHASE2_DESIGN.md left open were ratified 2026-08-25 and are recorded in
  # full, with their reasoning, in ASSUMPTIONS.md under "Item 5f, SIU
  # separation". One line each here, so a reader knows which behaviour below
  # is a decision and which is a consequence of one:
  #
  #   1. Indicators are evaluated on every transition into TRIAGED, on both
  #      paths, inside that transaction, on the merged current view - never
  #      at RECEIVED and never at PENDED. A pended notice is an incomplete
  #      intake record, not a claim.
  #   2. Late reporting is measured from the original receipt instant's
  #      jurisdiction date, never from the resolution instant. Notice given
  #      is notice received; a pend does not make the reporter late.
  #   3. One event per indicator per evaluation, including FALSE and
  #      NOT_EVALUATED. Unevaluated is not negative, and that is only
  #      auditable if unevaluated is written down. Append-only: nothing below
  #      updates or removes one, and no path to do either exists.
  #   4. No read surface in phase 2 beyond the restricted read the scenarios
  #      below use. There is no route to these events until an authenticated
  #      identity exists to log a read against.
  #   5. The leak assertions are outcome negatives on four surfaces, for a
  #      notice that actually has something to leak.
  #   6. The rules applied are the carrier's configuration as resolved at the
  #      transaction that triaged the notice - read then, not snapshotted when
  #      the notice arrived, so a threshold configured while a notice sits
  #      pended is the one its evaluation uses.
  #
  # WHAT VERSION AN EVENT RECORDS, decided 2026-08-25 and recorded in
  # ASSUMPTIONS.md under "Item 5f, one point the six decisions do not cover".
  # The ruleset version is the version of the domain rule set - the code that
  # evaluated the indicator - and never the carrier's configured numbers,
  # which have no version and do not acquire one for this. It is a
  # date-stamped label declared once in the domain package, and the same
  # label reaches every audit entry and every SIU event written in the same
  # transaction, which is why the scenarios below tie an evaluation's events
  # to the audit entry that moved the notice rather than to a literal. No
  # scenario states the label itself: it changes whenever a domain rule's
  # behaviour changes, so a spec that named one would be stale by
  # construction, and notice_intake.feature declined to name it for the same
  # reason.
  #
  # Reproducing a recorded evaluation comes from recording what was applied,
  # not from versioning the configuration: each event also carries the
  # threshold that evaluation used, and no threshold where none was
  # configured. That is what makes a row answerable a year later without
  # anyone having to reconstruct which carrier configuration was in force -
  # the two facts together, the rule version and the number it was given.
  #
  # There is no HTTP layer anywhere in this project yet, and no
  # authentication; notice_intake.feature, idempotency.feature and
  # resolution.feature all say the same about the carrier code, the
  # submission instant, the idempotency key and the reviewer's identity.
  # Every step below states its input as a plain business fact.

  Background:
    # Carried from resolution.feature, which carried it from
    # notice_intake.feature and idempotency.feature, so that the same words
    # keep meaning the same thing across all four. The claimant-name
    # requirement never fires anywhere in this file: it applies only to a
    # Section II loss, and every notice below reports wind_hail, a Section I
    # property peril.
    #
    # No late reporting threshold is configured here. Each rule below states
    # its own, because a threshold stated in a Background is a threshold
    # mutation cannot reach (docs/harness-findings.md, "Mutation cannot see a
    # fixed Given") and every late reporting threshold in this file is the
    # subject of the rule that states it. The recent policy inception
    # threshold is different and is configured here at 30, matching
    # notice_intake.feature: no rule in this file is about it, and
    # configuring it leaves the continuous coverage date as the single
    # absent input behind every NOT_EVALUATED that indicator records below.
    # That is what keeps this file's reason codes readable from its own text
    # rather than from a precedence rule specified in another file.
    Given the carrier "AAAA" requires the claimant name
    And "AAAA" does not require the claimant contact
    And "AAAA" recognizes the policy-number prefixes "HO;DP"
    And "AAAA" has no late reporting threshold configured
    And "AAAA" configures a recent policy inception threshold of 30 days
    And "AAAA" configures a duplicate match window of 60 days
    And the notice is submitted by carrier "AAAA"
    And the jurisdiction observes "America/New_York"
    And the notice is submitted at "2026-08-24T16:00Z"
    And the notice reports a policy number of "HO-1234567"
    And the notice reports a loss date of "2026-06-01"
    And the notice reports a loss type of "wind_hail"
    And the notice reports a notice type of "INITIAL"
    And the reviewer is identified as "adjuster-4471"

  Rule: A notice triaged at intake records one event per indicator, stamped with its own receipt

    # Decision 1's first path: a notice with no blocker reaches TRIAGED in
    # the request that created it, so its indicators are evaluated in that
    # same transaction and stamped with the instant the caller supplied for
    # it - 2026-08-24T16:00Z, from the Background. That instant is
    # 12:00 in America/New_York, so the jurisdiction date every interval
    # below is counted from is 2026-08-24.
    #
    # Both thresholds below are illustrative, exactly as
    # siu_indicators.feature says of its own 45: no late reporting threshold
    # has been approved for any carrier, and the values here exist to prove
    # that the boundary is where the carrier's configuration puts it, not to
    # propose one. 45 and 44 are adjacent on purpose - one day apart is what
    # makes the third row a boundary probe rather than a second unrelated
    # example - and both are deliberately not 30, which is the recent policy
    # inception threshold this file's own Background configures, so an
    # implementation crossing the two thresholds cannot pass by coincidence.
    # The 7-day threshold two rules below is not 30 either, for the same
    # reason.
    #
    # Arithmetic, recomputed rather than carried over: 2026-07-10 is 45 days
    # before 2026-08-24 and 2026-07-09 is 46. Late reporting fires when the
    # interval is more than the threshold, so 45 days against a 45-day
    # threshold is FALSE and 46 days against it is TRUE, and 45 days against
    # a 44-day threshold is TRUE. The first and third rows share a loss date
    # and differ only in the threshold, which is what makes the threshold
    # column discriminating rather than decorative.
    #
    # The recent policy inception indicator is NOT_EVALUATED on every notice
    # this system processes, and that is the correct answer rather than a
    # stub (ASSUMPTIONS.md, 2026-08-22): the continuous coverage date arrives
    # by an adapter lookup that phase 2 does not have, so the input is
    # genuinely absent. The Background configures the threshold, so the
    # coverage date is the only input this indicator is missing anywhere in
    # this file and NO_CONTINUOUS_COVERAGE_DATE follows from that one absence
    # rather than from any ordering between two of them. That is deliberate:
    # siu_indicators.feature specifies which reason wins when both inputs are
    # gone, and a file whose every scenario depended on that ordering would
    # be asserting another file's rule in every one of its own.
    #
    # The threshold the late reporting event records is asserted against the
    # same placeholder that configured it. That is deliberate and it is a
    # relational tie rather than a second threshold: it adds no mutant of its
    # own, and the threshold column's existing mutants now move the
    # configured value and the recorded one together, so what the tie
    # protects is that the event reports the number the evaluation was
    # actually given rather than a constant. An implementation recording a
    # hardcoded 45 fails the 44-day row. The verdicts on those mutants are
    # unchanged by the tie; they are still decided by the outcome column.
    #
    # The two version assertions are deliberately both present even though
    # the second implies the first. They fail differently and a reader should
    # be able to tell which broke: two events disagreeing with each other is
    # an evaluation that read the label twice, while two events agreeing with
    # each other and not with the audit entry is a transaction that wrote the
    # SIU trail from a different read than the one it audited.
    #
    # Two assertions below are fixed steps rather than columns and the engine
    # therefore cannot mutate them: the recent policy inception result, which
    # is identical on every row and would be an inert column if it were one
    # (docs/harness-findings.md, "A same-outcome column is sometimes the
    # point of the rule"), and the stamp, whose value is the Background's own
    # submission instant. They execute on every row and are the point of the
    # rule; they are simply not protected by mutation, and that is recorded
    # here rather than left for a reader to discover from a count.
    Scenario Outline: What a notice triaged at intake records for each indicator
      Given "AAAA" configures a late reporting threshold of <threshold> days
      And the notice reports a loss date of "<loss_date>"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the late reporting indicator recorded for the notice is <late_reporting>
      And the recent policy inception indicator recorded for the notice is NOT_EVALUATED with reason NO_CONTINUOUS_COVERAGE_DATE
      And exactly two SIU indicator events are recorded for the notice
      And each of those events is stamped "2026-08-24T16:00Z"
      And those two events record the same ruleset version as each other
      And those two events record the same ruleset version as the audit entry that triaged the notice
      And the late reporting event records a threshold of <threshold> days

      Examples:
        | threshold | loss_date  | late_reporting |
        | 45        | 2026-07-10 | FALSE          |
        | 45        | 2026-07-09 | TRUE           |
        | 44        | 2026-07-10 | TRUE           |

    # The other side of the threshold's existence, and it cannot be a fourth
    # row above: "no threshold at all" has no numeral, so it cannot share a
    # column with 45 and 44 without inventing a sentinel word for a value
    # carrier_configuration.feature already has a locked phrase for. This
    # scenario uses that phrase. siu_indicators.feature is laid out the same
    # way, for the same reason, one layer down.
    #
    # The loss date is 2026-07-09 - 46 days, which would be TRUE against the
    # 45-day threshold the scenario above configures - so this cannot pass by
    # coincidence with a FALSE result standing in for an unevaluated one.
    # That is the whole point of the rule: an absent threshold is never read
    # as "not late", and the event is written anyway, because an evaluation
    # that did not happen is a fact worth recording and an absent row would
    # be indistinguishable from an evaluation nobody ran.
    #
    # The event records no threshold rather than a zero. A configured zero is
    # a real carrier choice that makes every notice late
    # (carrier_configuration.feature), so writing zero here would record a
    # rule nobody configured - the same failure, one field along, that
    # NOT_EVALUATED exists to prevent on the value itself.
    Scenario: A carrier with no late reporting threshold still records both events
      Given "AAAA" has no late reporting threshold configured
      And the notice reports a loss date of "2026-07-09"
      When the notice is submitted for intake
      Then the notice's state is TRIAGED
      And the late reporting indicator recorded for the notice is NOT_EVALUATED with reason NO_THRESHOLD_CONFIGURED
      And the recent policy inception indicator recorded for the notice is NOT_EVALUATED with reason NO_CONTINUOUS_COVERAGE_DATE
      And exactly two SIU indicator events are recorded for the notice
      And each of those events is stamped "2026-08-24T16:00Z"
      And those two events record the same ruleset version as the audit entry that triaged the notice
      And the late reporting event records no threshold

  Rule: Nothing is recorded until the notice reaches TRIAGED

    # Decision 1's second path and its negative half together. A pended
    # notice is an incomplete intake record, not a claim, and carriers score
    # indicators on the claim; a resolution that corrects the loss date
    # changes the interval, so an evaluation at pend time would record a
    # determination on data a human later corrected. A refused resolution
    # records nothing for the same reason a replay does - it does not
    # transition - not because a refusal is a lesser event: the refusal is
    # still audited, and its data is still kept and still part of what the
    # notice says (resolution.feature).
    #
    # One table mixing the two outcomes rather than two same-outcome
    # scenarios (.claude/skills/gherkin-specs, constraint 3): the refused row
    # and the applied row differ in the state, the status and what was
    # recorded at once, so a substitution between them lands on a row that
    # expects something different and is killed.
    #
    # The notice is pended for two things - an absent policy number and a
    # notice type of SUPPLEMENT, which is not a recognized value - so that a
    # reviewer can supply one of them and still be refused. That is
    # resolution.feature's own device, reused rather than reinvented.
    #
    # The applied row's events are stamped with the resolution's instant,
    # 2026-08-25T09:00Z, not with the receipt: the evaluation happened then.
    # Rule 3 is where the stamp and the interval are shown to come from
    # different instants deliberately.
    #
    # The ruleset-version tie lives inside the applied row's cell rather than
    # in a step of its own, because the refused row has no event for it to be
    # about and a step asserting something of every event would pass over an
    # empty set there and prove nothing. Keeping it in the column also keeps
    # it mutable: the two cells swap against each other, and either direction
    # lands on a row that expects the other outcome.
    Scenario Outline: Whether a resolution records an evaluation depends on whether it releases the notice
      Given "AAAA" configures a late reporting threshold of 45 days
      And the notice reports a policy number of "absent"
      And the notice reports a notice type of "SUPPLEMENT"
      And the notice is submitted for intake
      And the notice's state is PENDED
      And no SIU indicator event is recorded for the notice
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer supplies a notice type of "<supplied_notice_type>"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is <response>
      And the notice's state is <state>
      And the SIU indicator events recorded for the notice <events>

      Examples:
        | supplied_notice_type | response | state   | events                                                                                                        |
        | SUPPLEMENT           | 422      | PENDED  | are none                                                                                                      |
        | SUPPLEMENTAL         | 200      | TRIAGED | are two, both stamped "2026-08-25T09:00Z" and both carrying the ruleset version of the entry that released it  |

  Rule: Late reporting is counted from the day the notice was received, not the day it was released

    # Decision 2. Notice given is notice received: the reporter told the
    # carrier on the receipt date, and a pend is the carrier asking for more,
    # not the reporter arriving late. The one-receipt-clock entry in
    # ASSUMPTIONS.md implies this and did not state it, which is why it is a
    # decision and why it has a rule of its own.
    #
    # Arithmetic, recomputed here rather than carried from the decision.
    # 2026-08-24T16:00Z is 12:00 in America/New_York, so the receipt's
    # jurisdiction date is 2026-08-24. 2026-10-01T14:00Z is 10:00 Eastern, so
    # the resolution's is 2026-10-01. First row: the loss is 2026-08-15, 9
    # days before receipt and 47 days before the resolution. Against a 45-day
    # threshold the receipt clock says FALSE and the resolution clock says
    # TRUE, so an implementation that counts from the wrong instant fails
    # this row. Second row: the loss is 2026-07-09, 46 days before receipt
    # and 84 before the resolution - TRUE either way.
    #
    # Only the first row discriminates the two clocks, and that is not a
    # defect in the second: a resolution can never precede the receipt it
    # resolves, so the resolution-measured interval is always the larger one
    # and the error this rule exists to catch can only ever over-report
    # lateness, never under-report it. There is no loss date that fails the
    # other way, so no row can be written for it. The second row is here to
    # keep the outcome column mixed, which is what kills a substitution
    # between the two loss dates and between the two results.
    #
    # Both events are still stamped with the resolution's instant. The stamp
    # says when the evaluation happened; the interval says what was measured.
    # This scenario is the one place the two differ, and asserting both is
    # what keeps an implementation from collapsing them into one instant.
    Scenario Outline: Which day the late reporting interval is counted from
      Given "AAAA" configures a late reporting threshold of 45 days
      And the notice reports a policy number of "absent"
      And the notice reports a loss date of "<loss_date>"
      And the notice is submitted for intake
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer's resolution is submitted at "2026-10-01T14:00Z"
      Then the response is 200
      And the notice's state is TRIAGED
      And the late reporting indicator recorded for the notice is <late_reporting>
      And exactly two SIU indicator events are recorded for the notice
      And each of those events is stamped "2026-10-01T14:00Z"
      And those two events record the same ruleset version as the audit entry that released the notice

      Examples:
        | loss_date  | late_reporting |
        | 2026-08-15 | FALSE          |
        | 2026-07-09 | TRUE           |

  Rule: The rules applied are the carrier's configuration at the transaction that triages, not at intake

    # Decision 6. Every other scenario in this file configures the carrier
    # before the notice arrives and never changes it, so all of them pass
    # identically against an implementation that reads the configuration once
    # at intake and carries that reading forward to the resolution. This
    # scenario is the one that tells the two apart: the carrier has no late
    # reporting threshold when the notice arrives and has one by the time a
    # reviewer releases it, so an implementation holding the arrival-time
    # reading records NOT_EVALUATED with NO_THRESHOLD_CONFIGURED, and one
    # reading the configuration in the transaction that triages records TRUE.
    # Nothing else in the file distinguishes them.
    #
    # A carrier changing a threshold while a notice sits pended is ordinary
    # operational reality, not a contrived setup: a pend can last weeks, and
    # a deployment that rolled out a new configuration in that window has to
    # answer which one the evaluation used. Decision 6 answers it, and this
    # is where the answer is checked.
    #
    # Arithmetic, recomputed rather than carried: 2026-08-16 is 8 days before
    # the receipt's jurisdiction date of 2026-08-24. Against a 7-day
    # threshold that is more than the threshold, so TRUE. 7 is chosen for
    # that reason and not for being a round number - the engine mutates a
    # bare number by incrementing it, and 8 days against an 8-day threshold
    # is FALSE, so the one mutant this scenario has is killed by the result
    # it asserts. It is illustrative exactly like every other late reporting
    # threshold in this file: no such value has been approved for any
    # carrier.
    #
    # The threshold the event records is stated as its own literal here, not
    # as a placeholder shared with the configuring step the way Rule 1's is.
    # A plain scenario has no columns to share, and the difference is worth
    # having: the two numbers mutate independently, so a mutant that raises
    # the configured threshold leaves the assertion expecting the old one and
    # dies twice over - once on the result and once on the number the event
    # reports. That is the check that an implementation echoing back a
    # constant rather than what it applied cannot pass.
    #
    # This scenario says nothing about which instant the interval is counted
    # from - both clocks read TRUE here, 8 days from the receipt and 46 from
    # the resolution. That is Rule 3's question and it is deliberately not
    # re-asked, so a failure here means the configuration was read at the
    # wrong time rather than the interval counted from the wrong day.
    Scenario: A threshold configured while the notice is pended is the one the evaluation uses
      Given the notice reports a policy number of "absent"
      And the notice reports a loss date of "2026-08-16"
      And the notice is submitted for intake
      And the notice's state is PENDED
      And no SIU indicator event is recorded for the notice
      And "AAAA" configures a late reporting threshold of 7 days
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer's resolution is submitted at "2026-10-01T14:00Z"
      Then the response is 200
      And the notice's state is TRIAGED
      And the late reporting indicator recorded for the notice is TRUE
      And the late reporting event records a threshold of 7 days
      And exactly two SIU indicator events are recorded for the notice
      And each of those events is stamped "2026-10-01T14:00Z"
      And those two events record the same ruleset version as the audit entry that released the notice

  Rule: A replay records nothing; a resubmission past the window is a new notice and records its own

    # Decision 1 again, from the third direction: a replay returns the notice
    # that already exists and moves nothing, so there is nothing to evaluate.
    # Without this rule an implementation that evaluated on every request
    # rather than on every transition would pass every other scenario in this
    # file - the values would be identical, and only the count would betray
    # it. That is why the assertion here is a count rather than a value.
    #
    # The window boundary itself is idempotency.feature's, proven there and
    # relied on here: a repeated key is a replay strictly before the 24-hour
    # mark and a fresh submission at the mark itself. The rows sit either
    # side of it for the same reason, and this rule re-asserts which side a
    # request lands on only because the count it is really about is
    # meaningless without it.
    #
    # The second row's total is four, not two: the resubmission creates its
    # own notice, which reaches TRIAGED on its own receipt and records its
    # own pair. That is the column that discriminates - a replay adding a
    # pair, or a resubmission adding none, both land on the wrong total.
    #
    # The ruleset-version tie is written to hold on both rows without going
    # vacuous on either: each event is tied to the entry that triaged the
    # notice it belongs to, which on the first row is the original notice and
    # on the second is the original and the new notice separately. An
    # implementation that stamped the new notice's events from the original's
    # transaction fails the second row.
    Scenario Outline: Whether a repeated submission records a second evaluation
      Given "AAAA" configures a late reporting threshold of 45 days
      And the notice is submitted with the idempotency key "K-800"
      And the notice is submitted for intake
      And that submission is remembered as the original
      When the notice is submitted at "<replay_submitted_at>"
      And the notice is submitted for intake
      Then the response is <response>
      And the response <notice_relation>
      And the original notice still has exactly two SIU indicator events
      And <recorded_in_all> SIU indicator events have been recorded in all
      And every recorded event carries the ruleset version of the audit entry that triaged its own notice

      Examples:
        | replay_submitted_at | response | notice_relation                           | recorded_in_all |
        | 2026-08-25T15:59Z   | 200      | identifies the original notice            | two             |
        | 2026-08-25T16:00Z   | 201      | identifies a new notice, not the original | four            |

  Rule: Nothing about SIU reaches any surface an ordinary reader sees

    # Decision 5, and PHASE2_DESIGN.md's points 2 and 3: response
    # serializers are allow-list based, SIU codes never appear among
    # reason codes, and SIU detail never appears in a standard audit
    # entry, which would otherwise make the audit endpoint the leak path.
    #
    # These assertions are meaningful only from this item onward, because
    # before it there was nothing to leak. Both scenarios below therefore
    # establish that there is: each asserts, through the restricted read,
    # that the notice really does carry a late reporting indicator of TRUE
    # and a recent policy inception indicator of NOT_EVALUATED before it
    # asserts that none of it is visible anywhere else. A leak test on a
    # notice with nothing recorded passes for the wrong reason and would
    # keep passing if the evaluation were deleted entirely.
    #
    # Four surfaces between the two scenarios: the intake response, the
    # resolution response, the notice's own view, and every entry in its
    # audit trail. Two scenarios rather than one outline over a surface
    # column, because the rule is symmetric across surfaces by design -
    # every swap in such a column is inert and each one costs a human
    # approval carrying the same equivalence argument
    # (docs/harness-findings.md, "A same-outcome column is sometimes the
    # point of the rule"; .claude/skills/gherkin-specs, constraint 4).
    # Splitting by path instead puts the two responses in the two places
    # they can actually be produced.
    #
    # Every assertion in both scenarios is a fixed step. Mutation cannot
    # reach a step that is not an Examples cell, so what protects this rule
    # is that the steps run at all, not that a mutant dies: the negatives are
    # written to read the whole surface and assert the absence of both
    # indicator names and both reason codes, so a field added carelessly
    # later is caught by the assertion rather than by its name being listed
    # here. The threshold literal is the one value here mutation does reach,
    # and the TRUE assertion above each negative is what kills it - a
    # 45-day threshold against a 46-day interval is TRUE, a 46-day one is
    # not.
    #
    # The reason-code exclusion is asserted on the pended path only, and
    # deliberately: a triaged notice carries no blockers at all, so the same
    # assertion there would pass over an empty list and prove nothing. The
    # pended intake response carries a real one.
    Scenario: A notice triaged at intake shows nothing about SIU on any surface
      Given "AAAA" configures a late reporting threshold of 45 days
      And the notice reports a loss date of "2026-07-09"
      When the notice is submitted for intake
      Then the response is 201
      And the notice's state is TRIAGED
      And the late reporting indicator recorded for the notice is TRUE
      And the recent policy inception indicator recorded for the notice is NOT_EVALUATED with reason NO_CONTINUOUS_COVERAGE_DATE
      And the response names no SIU indicator and no SIU reason code
      And the notice's own view names no SIU indicator and no SIU reason code
      And every entry in the audit trail names no SIU indicator and no SIU reason code

    Scenario: A notice released by a reviewer shows nothing about SIU on any surface
      Given "AAAA" configures a late reporting threshold of 45 days
      And the notice reports a loss date of "2026-07-09"
      And the notice reports a policy number of "absent"
      And the notice is submitted for intake
      And the response is 201
      And the blockers in that response name no SIU reason code
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is 200
      And the notice's state is TRIAGED
      And the late reporting indicator recorded for the notice is TRUE
      And the recent policy inception indicator recorded for the notice is NOT_EVALUATED with reason NO_CONTINUOUS_COVERAGE_DATE
      And the response names no SIU indicator and no SIU reason code
      And the notice's own view names no SIU indicator and no SIU reason code
      And every entry in the audit trail names no SIU indicator and no SIU reason code
