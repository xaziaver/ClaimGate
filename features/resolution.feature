Feature: Resolving a pended notice

  As a claims reviewer
  I need to supply what a pended notice was missing and have the notice move
  only when nothing is missing any more
  So that a notice held for a specific thing is released by a human judging
  that the thing has actually arrived, and every attempt to release it -
  including the ones that fail - is on the record

  # PHASE2_DESIGN.md's "Pending resolution and tolling" section is this
  # file's specification input, together with the Record state model's
  # PENDED -> TRIAGED row and the closed status-code table under HTTP
  # surface. There is no HTTP layer anywhere in this project yet;
  # notice_intake.feature and idempotency.feature both say the same about
  # the carrier code, the submission instant, and the idempotency key. A
  # reviewer's resolution arrives as an ordinary input the same way those
  # do, and every scenario below states it as a plain business fact.
  #
  # PENDED -> TRIAGED is the only transition this file is about, and it is
  # a USER transition: resolving a pend means a human judging whether
  # newly-supplied information actually satisfies what was missing, not a
  # re-run of the same deterministic rules that produced the pend. There is
  # still no rejected, invalid, or discarded state (CLAUDE.md) - a
  # resolution that does not clear the pend leaves the notice exactly where
  # it was, PENDED, and is answered rather than discarded.
  #
  # Tolling is recorded and never computed. Fla. Stat. 627.70131(8)(b)
  # tolls the section's deadlines while a policyholder has not supplied
  # requested material information, and 627.70131(4)(b)6 requires records
  # of the start and end of a tolling period - but whether tolling applies
  # is a downstream legal determination, so this file asserts only that the
  # two instants something downstream would compute it from are recorded
  # and unambiguous. No scenario below names tolling, and nothing in phase
  # 2 does.
  #
  # WHAT THIS FILE DECIDES, and where it was decided - the five points this
  # draft escalated on 2026-08-25 were ratified the same day. Each is
  # recorded in full, with its reasoning, in ASSUMPTIONS.md's "Open
  # decisions", under the item 5e entry; one line each here so a reader of
  # the spec knows which behaviour below is a decision and which is a
  # consequence:
  #
  #   1. A resolution may supply any notice-content field, not only the
  #      ones its blockers name - overlaid field by field in arrival order,
  #      a field it omits keeping its prior value, and no way to blank a
  #      field, only to replace it.
  #   2. The full validation runs over the merged current view, on the
  #      jurisdiction date of the resolution's own caller-supplied instant.
  #      One definition of "no blocker", the same one intake uses. A
  #      blocker the resolution introduces is not a new outcome; it is
  #      simply among "the current blockers" the 422 reports.
  #   3. A refused resolution's data is kept, in sequence, and is part of
  #      the current view - the release was refused, not the data. The 409
  #      persists nothing at all.
  #   4. The actor's type is not a caller input; this endpoint stamps USER.
  #      The reviewer's identity is a required caller-asserted string, and
  #      a body without one is schema-invalid: 400, nothing persisted.
  #   5. A notice at rest in RECEIVED gets the existing 409, whose body
  #      carries the notice's current state. No new status row. That
  #      scenario is owed to item 5i, which is what makes the state
  #      reachable by a specified path; today it is only producible by an
  #      exception from unbuilt code.
  #
  # One correction the ratification forced, recorded here because this
  # header is where the wrong claim was made: the 2026-08-25 draft said it
  # decided none of the five and sat inside the intersection of every open
  # reading. That was false for point 3. Rule 2's refused row asserts the
  # notice's blockers as NOTICE_TYPE_UNRECOGNIZED:notice_type alone, which
  # is only true if the refused resolution's policy number had already
  # entered the current view - the draft had decided point 3, in the
  # direction since ratified, without saying so.
  #
  # Duplicate candidates and SIU indicators are asserted nowhere below, for
  # the same reasons notice_intake.feature gives: SIU is item 5f's
  # entirely, and nothing this file read decides whether a resolution
  # re-opens duplicate detection.

  Background:
    # The claimant-name requirement never fires anywhere in this file: it
    # applies only to a Section II loss, and every notice below reports
    # wind_hail, a Section I property peril. Carried verbatim from
    # notice_intake.feature and idempotency.feature so that the same words
    # keep meaning the same thing across all three.
    Given the carrier "AAAA" requires the claimant name
    And "AAAA" does not require the claimant contact
    And "AAAA" recognizes the policy-number prefixes "HO;DP"
    And "AAAA" configures a duplicate match window of 60 days
    And the notice is submitted by carrier "AAAA"
    And the insured property is in "FL"
    And the notice is submitted at "2026-08-24T16:00Z"
    And the notice reports a policy number of "HO-1234567"
    And the notice reports a loss date of "2026-06-01"
    And the notice reports a loss type of "wind_hail"
    And the notice reports a notice type of "INITIAL"
    And the reviewer is identified as "adjuster-4471"

  Rule: A resolution is acted on only while the notice is still pended

    # PHASE2_DESIGN.md's status-code table: "notice not currently PENDED"
    # -> 409, and its own bullet adds "no state change, no audit entry."
    # That check runs before anything the resolution carries is looked at,
    # which is why both rows below can supply the same policy number and
    # only the state the notice was already in decides what happens to it.
    #
    # One table mixing the two outcomes rather than two same-outcome
    # scenarios (.claude/skills/gherkin-specs, constraint 3): a substitution
    # between the pended row and the triaged one moves the actual result
    # instead of swapping between two rows that already agree.
    #
    # The state column after the attempt reads TRIAGED on both rows and
    # means two different things - the first row moved there, the second was
    # already there and did not move. That is the point of pairing it with
    # the audit column: an implementation that quietly re-applied a
    # resolution to an already-triaged notice would look identical on state
    # alone and is caught by the trail.
    #
    # The second row is a TRIAGED notice, not a RECEIVED one. Decision 5
    # settles that a notice at rest in RECEIVED gets this same 409, with
    # its current state in the body and no new status row - but the
    # scenario for it belongs to item 5i, the item that makes that state
    # reachable by a specified path. Today the only way to produce it is an
    # exception raised from code nobody has written, and a scenario whose
    # setup depends on that is not a scenario. There is no row for it here.
    #
    # The records column is what turns the 409's "no state change, no audit
    # entry" into a complete claim rather than half of one. Decision 3
    # settles that this case persists nothing at all - no pend, no request
    # for information, nothing for a reviewer's content to be the answer
    # to, so unlike the 422 there is nothing here worth keeping. The audit
    # column on its own would pass an implementation that quietly kept the
    # refused content and merely declined to audit it, which is exactly the
    # thing decision 3 permits for the 422 and forbids here.
    Scenario Outline: Whether a resolution is acted on depends on the state the notice is already in
      Given the notice reports a policy number of "<policy_number>"
      And the notice is submitted for intake
      And the notice's state is <state_before>
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is <response>
      And the notice's state is <state_after>
      And the notice's audit trail <audit_effect>
      And the notice's records <records>

      Examples:
        | policy_number | state_before | response | state_after | audit_effect                            | records                                             |
        | absent        | PENDED       | 200      | TRIAGED     | gains a third entry, for the resolution | are two, the submission and the resolution           |
        | HO-1234567    | TRIAGED      | 409      | TRIAGED     | still holds only its two intake entries | are one, the submission it was created from          |

  Rule: A resolution with no reviewer behind it is refused before anything is written

    # Decision 4: the actor's type is not a caller input - this endpoint
    # stamps USER, because an unauthenticated caller asserting SYSTEM would
    # be asserting something nothing in phase 2 can check. What the caller
    # does supply is the reviewer's own identity: required, caller-asserted,
    # recorded unverified. A body without one is schema-invalid, and that is
    # the single row decision 4 added to a status-code table
    # PHASE2_DESIGN.md otherwise calls closed - 400, nothing persisted.
    #
    # There is deliberately no scenario for a SYSTEM-actor attempt at this
    # transition. PHASE2_DESIGN.md's Record state model says such an attempt
    # is refused and audited, and that sentence now carries a dated
    # annotation saying what it actually describes: a guard for a future
    # system re-evaluation path, with no producer anywhere in phase 2. A
    # scenario for it would be specifying code nobody can reach.
    #
    # 400 rather than 422 is the distinction between a body that cannot be
    # read and a body that was read and did not clear the pend. Persisting
    # nothing follows the unknown-carrier 400's reasoning rather than the
    # schema-invalid one's: there is no reviewer here for an attempt to be
    # attributed to, so an audit entry would have to name someone nobody
    # supplied.
    #
    # The Background identifies a reviewer for every other rule in this
    # file; this rule's own Given overrides it per row, and "absent" means
    # the identity is not in the body at all - the same sentinel intake's
    # own steps already give the word.
    Scenario Outline: Whether a resolution is read at all depends on whether it says who is making it
      Given the notice reports a policy number of "absent"
      And the notice is submitted for intake
      And the reviewer is identified as "<reviewer>"
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is <response>
      And the notice's state is <state>
      And the notice's audit trail <audit_effect>
      And the notice's records <records>

      Examples:
        | reviewer      | response | state   | audit_effect                            | records                                              |
        | adjuster-4471 | 200      | TRIAGED | gains a third entry, for the resolution | are two, the submission and the resolution           |
        | absent        | 400      | PENDED  | still holds only its two intake entries | are one, the submission it was created from          |

  Rule: The notice moves only when the resolution clears every blocker, and either way the attempt is audited

    # PHASE2_DESIGN.md: supplied data that clears every blocker moves the
    # notice PENDED -> TRIAGED with audit outcome=APPLIED and response 200;
    # supplied data that still leaves a blocker leaves the notice PENDED,
    # response 422 with the current blockers, and still writes an audit
    # entry with from=PENDED, to=TRIAGED, outcome=REFUSED carrying the
    # still-failing blockers. "A refused resolution attempt is itself an
    # audit event, not a non-event" - that sentence is this rule's second
    # row, and the reason the two outcomes share one table rather than
    # sitting in a rule each.
    #
    # The notice is pended for two blockers so that the refused row is a
    # reviewer who supplied part of what was missing rather than nothing at
    # all, which is the realistic shape of a refusal and the only one that
    # exercises "the still-failing blockers" as a proper subset of what the
    # notice was held for. The blocker codes are validation.feature's own,
    # reused rather than reinvented - this endpoint gets no blocker
    # vocabulary of its own.
    #
    # What the notice carries after a refusal is the full current set, not
    # the leftovers of the set it was pended for. Decision 2(a): the whole
    # validation re-runs over the merged current view, so the notice's
    # stored blockers are replaced by that run's result and the 422 body
    # and the record cannot disagree. The second row is where that is
    # visible: the notice was pended for two blockers, the reviewer's
    # policy number cleared one, and the notice is left carrying exactly
    # one - which is true only because what a refused resolution supplied
    # entered the current view. That is decision 3, and this row asserted
    # it before it was ratified, at a point when this file's own header
    # claimed to be deciding nothing; the header now records the
    # correction.
    #
    # The third row is decision 2(a)'s other half, and it is the one the
    # design had no word for before the ratification. The reviewer clears
    # the notice-type blocker and supplies a policy number that is itself
    # malformed, so the notice ends up carrying a blocker it never had at
    # intake. That is not a new outcome needing a new status: it is the
    # ordinary 422 "with the current blockers," and the row proves the
    # implementation re-ran the whole validation rather than ticking off
    # the two codes it started with - a blockers-only recheck would have
    # cleared both and answered 200.
    #
    # The entry's blockers are asserted as a literal set rather than
    # relationally against the notice's, which is the opposite of the
    # choice notice_intake.feature's Rule 2 made and is deliberate: there,
    # the two entries carried different things and the relation was the
    # discriminating fact. Here the entry and the notice carry the same set
    # on both rows, so a relational phrase ("the same ones the notice still
    # carries") is true on the applied row as well - hand-simulated before
    # this was written to disk, and it survives its own mutant for exactly
    # that reason. Two literal columns are redundant on their face and are
    # kept anyway: an implementation that gets the 422 body right and the
    # audit entry wrong, or the reverse, is caught by only one of them.
    #
    # The actor column reads USER on both rows and has no differing
    # alternative, so it mutates by marker rather than by swap. Kept
    # because USER-only is the transition's defining constraint and an
    # entry attributing a reviewer's action to the system would be a false
    # record in the log that is the statutory system of record. The
    # reviewer's own asserted identity is a fixed assertion below the
    # table, generating no mutant: there is no second reviewer here for the
    # engine to swap in, and the fact - that what the caller asserted is
    # what is recorded, unverified, because phase 2 verifies nothing - is
    # worth stating where mutation cannot check it.
    Scenario Outline: Whether the notice moves depends on whether the resolution clears every blocker it was held for
      Given the notice reports a policy number of "absent"
      And the notice reports a notice type of "SUPPLEMENT"
      And the notice is submitted for intake
      When the reviewer supplies a policy number of "<supplied_policy_number>"
      And the reviewer supplies a notice type of "<supplied_notice_type>"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is <response>
      And the notice's state is <state>
      And the notice's blockers are <blockers>
      And the audit trail's last entry records the outcome <outcome>
      And that entry is entered by <actor>
      And that entry's blockers are <entry_blockers>
      And that entry records the reviewer's own asserted identity, unverified

      Examples:
        | supplied_policy_number | supplied_notice_type | response | state   | blockers                             | outcome | actor | entry_blockers                       |
        | HO-7654321             | SUPPLEMENTAL         | 200      | TRIAGED |                                      | APPLIED | USER  |                                      |
        | HO-7654321             | SUPPLEMENT           | 422      | PENDED  | NOTICE_TYPE_UNRECOGNIZED:notice_type | REFUSED | USER  | NOTICE_TYPE_UNRECOGNIZED:notice_type |
        | HO-12                  | SUPPLEMENTAL         | 422      | PENDED  | POLICY_NUMBER_MALFORMED:policy_number | REFUSED | USER  | POLICY_NUMBER_MALFORMED:policy_number |

  Rule: A reviewer may correct a field the notice already had, not only supply one it was missing

    # Decision 1: a resolution may carry any notice-content field, not only
    # the ones the notice's blockers name, overlaid field by field in
    # arrival order. The reporter who left the policy number off also had
    # the peril wrong, and the narrow reading would have carried a value a
    # human knew was wrong through triage and on into the adapter.
    #
    # The accepted cost is exactly what the second row shows: correcting a
    # field nobody was holding the notice for moves severity and queue.
    # That is the strongest argument for the narrow reading, and it is not
    # a defect - it is why PENDED -> TRIAGED is a USER transition at all. A
    # human made the call, the entry names them, and the payload carrying
    # it is immutable and hashed like every other.
    #
    # The first row is where "a field the resolution omits keeps its prior
    # value" is asserted: the reviewer supplies only a policy number, the
    # loss type is not in the resolution at all, and the notice still
    # triages on the peril it was reported with. There is no way to blank a
    # field in phase 2, only to replace one, so "absent" in a
    # reviewer-supplies step means omitted and never means cleared.
    #
    # fire is a Section I peril, so no claimant-field requirement enters
    # with it and the second row stays about the overlay alone. Both
    # severities and both queues on those rows are triage.feature's own
    # values, reused rather than restated here as new behaviour, and "not
    # yet assigned" on the third is notice_intake.feature's own vocabulary
    # for what a pended notice carries instead of them.
    #
    # The third row is decision 2(a)'s proof, and it is the only thing in
    # this file that has one. Every other refusal here is caught by
    # validating what the reviewer supplied: Rule 2's third row supplies a
    # malformed policy number and the malformed policy number is what
    # blocks it, so "validate the supplied fields, then re-check the
    # recorded blockers" would answer every one of them identically. Here
    # the reviewer supplies a policy number and a loss type, both of them
    # individually fine, and the two blockers that hold the notice are on
    # claimant_name and incident_description - fields the reviewer never
    # touched, which the notice was never pended for, and which no amount
    # of checking the supplied values or the recorded blockers would ever
    # reach. Only a full run of the whole validation over the merged
    # current view finds them. That is the difference between decision
    # 2(a) and the cheaper reading it was chosen over, and without this row
    # the file states the decision without testing it.
    #
    # The callback that produces it is the ordinary one. The peril went
    # down as wind, the notice pended for a missing policy number, and when
    # the reviewer rings back for the policy number the reporter mentions
    # that a guest was hurt. That is a liability loss, not a wind one, and
    # a liability loss needs the claimant named and the incident described
    # before anyone can act on it - so correcting the peril is exactly what
    # opens the two requirements that now hold the notice. The reviewer has
    # made the notice more blocked than it was and has done the right
    # thing; PENDED is where a notice waits for what is missing, and it is
    # still not a rejection.
    #
    # The blockers are in validation.feature's canonical order - code
    # order first, then field - which is where this file takes both the
    # codes and their sequence from rather than declaring any of its own.
    Scenario Outline: What a corrected field does to the notice depends on which field the reviewer corrects
      Given the notice reports a policy number of "absent"
      And the notice is submitted for intake
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer supplies a loss type of "<supplied_loss_type>"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is <response>
      And the notice's state is <state>
      And the notice's blockers are <blockers>
      And the notice's severity is <severity>
      And the notice's queue is <queue>

      Examples:
        | supplied_loss_type | response | state   | blockers                                                                         | severity         | queue            |
        | absent             | 200      | TRIAGED |                                                                                  | standard         | standard         |
        | fire               | 200      | TRIAGED |                                                                                  | high             | complex          |
        | injury             | 422      | PENDED  | MISSING_REQUIRED_FIELD:claimant_name;MISSING_REQUIRED_FIELD:incident_description | not yet assigned | not yet assigned |

  Rule: A resolution is judged on the calendar date it arrives, not the one the notice was pended on

    # Decision 2(b): the full validation re-runs on the jurisdiction date of
    # the resolution's own caller-supplied instant, through the same
    # conversion intake performs. The frozen alternative - judging every
    # resolution on the date the notice was received - makes a pend for a
    # future loss date permanently unresolvable, because nothing a reviewer
    # supplies can move it, and a notice that can never leave PENDED is a
    # discarded state under another name.
    #
    # Nothing here clears by the mere passage of time. No rule runs without
    # a USER resolution, and the reviewer below supplies no field values at
    # all - which decision 2(b) settles is valid input, a human asserting on
    # the record that the notice is acceptable as it stands. Time alone
    # changes nothing; time plus a reviewer's judgment does.
    #
    # The arithmetic, stated so the rows can be checked without running
    # them: America/New_York is four hours behind UTC in August, so
    # 2026-08-26T03:59Z is 23:59 on the 25th there and 2026-08-26T04:00Z is
    # 00:00 on the 26th. The loss date is 2026-08-26. A loss date after
    # today is in the future; a loss date equal to today is not. The two
    # rows sit one minute either side of the only boundary this rule has,
    # and the notice is pended on that boundary at intake because the
    # Background's own instant falls on the 24th.
    #
    # That the reviewer supplies nothing is a fixed step rather than a
    # column: it is identical on both rows, so mutation cannot see it. The
    # rows carry the rule on the instant alone, which is the point - two
    # identical resolutions, one refused and one applied, differing in
    # nothing but when they arrived.
    Scenario Outline: Whether a future loss date still blocks depends on the date the resolution arrives
      Given the notice reports a loss date of "2026-08-26"
      And the notice is submitted for intake
      And the notice's state is PENDED
      When the reviewer supplies no field values
      And the reviewer's resolution is submitted at "<resolved_at>"
      Then the response is <response>
      And the notice's state is <state>
      And the notice's blockers are <blockers>

      Examples:
        | resolved_at       | response | state   | blockers                      |
        | 2026-08-26T03:59Z | 422      | PENDED  | LOSS_DATE_IN_FUTURE:loss_date |
        | 2026-08-26T04:00Z | 200      | TRIAGED |                               |

  Rule: What a reviewer supplies is added to the notice's record in arrival order, never written over what is already there

    # PHASE2_DESIGN.md: "Supplemental data never mutates the stored
    # payload. Each resolution writes its own immutable payload record with
    # its own hash, linked to the notice in arrival order; the current view
    # of a notice is derived from that ordered sequence, never from an
    # overwrite." The reason given there is the one that makes this a
    # business rule rather than a storage preference: audit has to be able
    # to show what was known at each point in time, and an overwrite
    # destroys that.
    #
    # An outline over the two records themselves, one row per record,
    # rather than a plain scenario naming both - the same shape
    # notice_intake.feature's Rule 2 arrived at for the same reason: a
    # fixed step inside a plain scenario is never mutated, and the ordinal
    # column is what makes the swap real. Asking for the wrong record's
    # content is precisely the failure an overwrite would produce, so the
    # mutant and the defect are the same shape.
    #
    # The first row is where "the stored original unchanged" is actually
    # asserted: the notice was created from a submission with no policy
    # number, and that record still reports none after a resolution has
    # supplied one. An implementation that updated the original in place
    # would pass every other assertion in this file and fail only here.
    #
    # The derived current view is a fixed assertion below the table rather
    # than a column, and generates no mutant: there is no row where a
    # different current value would be correct. Kept because it is the
    # other half of the design's sentence - the sequence is not merely
    # stored, it is what the notice's own answer is read from - and nothing
    # else in this file would notice if the sequence were written correctly
    # and then ignored.
    #
    # Only an applied resolution appears here. Whether a refused one takes
    # a position in this sequence at all is open point 3 above, and
    # asserting either answer would decide it.
    Scenario Outline: Each record kept for a notice holds what arrived in its own position, and keeps holding it
      Given the notice reports a policy number of "absent"
      And the notice is submitted for intake
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is 200
      And the <ordinal> record kept for the notice reports a policy number of <recorded_policy_number>
      And that record <origin>
      And no third record is kept for the notice
      And the notice's current view reports a policy number of "HO-7654321"

      Examples:
        | ordinal | recorded_policy_number | origin                                        |
        | first   | absent                 | is the submission the notice was created from |
        | second  | HO-7654321             | is the reviewer's resolution                  |

  Rule: What a refused resolution supplied is kept, in sequence, and counts toward what the notice says

    # Decision 3: the release was refused, not the data. What the reviewer
    # supplied is the reporter's answer to a request for information under
    # Fla. Stat. 627.70131(4)(b)3 and is received the moment it arrives.
    # The audit entry's REFUSED already records that the state did not
    # move, so an applied/unapplied marker on the record itself would be a
    # second place to say the same thing, and the two could disagree. The
    # sequence is the notice.
    #
    # This is the rule a reviewer's actual working pattern needs. Someone
    # who fixed one of two problems does not re-supply the fixed one on the
    # next attempt, and the second resolution below supplies only a notice
    # type. It clears the pend only because the policy number from the
    # refused first attempt is already part of what the notice says - which
    # is also the reason "422 with the current blockers" means anything at
    # all rather than reporting a set nobody can act on.
    #
    # Three records for one submission and two resolutions, and the third
    # reports its policy number as absent because the second resolution did
    # not carry one. That is decision 1's overlay seen from the other side:
    # each record holds what arrived in it and nothing more, and the
    # current view is read from the sequence rather than from any single
    # record in it. Four audit entries, because the refusal is an entry
    # too.
    Scenario Outline: Each record holds what arrived in it, and a refused resolution's record is one of them
      Given the notice reports a policy number of "absent"
      And the notice reports a notice type of "SUPPLEMENT"
      And the notice is submitted for intake
      And the reviewer supplies a policy number of "HO-7654321"
      And the reviewer supplies a notice type of "SUPPLEMENT"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      And the response is 422
      And the notice's current view reports a policy number of "HO-7654321"
      When the reviewer supplies a notice type of "SUPPLEMENTAL"
      And the reviewer's resolution is submitted at "2026-08-25T11:00Z"
      Then the response is 200
      And the notice's state is TRIAGED
      And the <ordinal> record kept for the notice reports a policy number of <recorded_policy_number>
      And that record <origin>
      And no fourth record is kept for the notice
      And the notice's audit trail holds four entries

      Examples:
        | ordinal | recorded_policy_number | origin                                        |
        | first   | absent                 | is the submission the notice was created from |
        | second  | HO-7654321             | is the reviewer's first resolution            |
        | third   | absent                 | is the reviewer's second resolution           |

  Rule: A replay of the original submission reports the state the notice is in now, not the one it landed in

    # Carried from item 5d, recorded in ASSUMPTIONS.md under "Idempotency:
    # what a repeated key is compared against" and in QUEUE.md's item 5e
    # entry. PHASE2_DESIGN.md says a replay carries "the current state, not
    # the state at first processing - the notice may have moved since."
    # idempotency.feature's own Rule 4 could only prove the half that was
    # reachable before this endpoint existed: that the state a replay
    # reports comes from the notice rather than from a constant, since a
    # PENDED original replays as PENDED. This rule is the other half - the
    # same notice, the same key, the same replay, reporting TRIAGED because
    # a resolution moved it in between.
    #
    # The two rows differ only in whether the resolution cleared the pend,
    # which is what makes this a proof about the replay rather than a
    # second copy of Rule 2: the refused row's replay still reports PENDED,
    # so an implementation that reported a constant, or that reported the
    # state at first processing, fails on exactly one row and is caught.
    #
    # The replay is submitted at the Background's own instant, so it is
    # well inside the 24-hour window and is a replay rather than a fresh
    # notice. Where that boundary lies is idempotency.feature's, proven
    # there and not restated here.
    Scenario Outline: What state a replay reports depends on whether the resolution moved the notice
      Given the notice reports a policy number of "absent"
      And the notice reports a notice type of "SUPPLEMENT"
      And the notice is submitted with the idempotency key "K-700"
      And the notice is submitted for intake
      And that submission is remembered as the original
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer supplies a notice type of "<supplied_notice_type>"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      And the notice is submitted for intake
      Then the response is 200
      And the response identifies the original notice
      And the notice's state is <state>

      Examples:
        | supplied_notice_type | state   |
        | SUPPLEMENTAL         | TRIAGED |
        | SUPPLEMENT           | PENDED  |

  Rule: A resolution is recorded at the instant its caller gives it, and the notice's own pend instant is untouched by it

    # PHASE2_DESIGN.md's tolling paragraph: "Record the pend timestamp and
    # the resolution-received timestamp precisely, in UTC, on the notice
    # and in the audit trail." Both ends of the interval something
    # downstream computes tolling from, and neither is computed here.
    #
    # These instants can be stated as spec literals where an intake
    # occurred_at could not. notice_intake.feature's Rule 2 records why it
    # left occurred_at unasserted - it is real wall-clock time at the
    # moment an acceptance run executes. That reasoning does not reach this
    # endpoint: every timestamp on the resolution path is the instant the
    # caller supplied for that call, never now(), per ASSUMPTIONS.md's "One
    # receipt clock, not two" as extended to the resolution path on
    # 2026-08-25. A literal is therefore exactly what the behaviour is, and
    # a scenario that could not assert it would be leaving the one thing
    # tolling needs unprotected.
    #
    # The supplied instant and the recorded instant are two columns holding
    # the same value rather than one column named twice. One column
    # appearing in both a When and a Then mutates on both sides at once and
    # is inert - the implementation agrees with the mutated spec, and the
    # mutant survives having proven nothing. Two columns break that: a swap
    # on either side alone puts the input and the assertion out of step.
    #
    # Both rows apply cleanly and the table is same-outcome in that sense,
    # which constraint 3 warns about. It does not bite here: the warning is
    # about outcome columns whose alternatives agree, and every column
    # below carries a value the other row contradicts. The pend instant is
    # the exception, identical on both rows by design - it is the fact
    # under test, that a resolution at any instant leaves it alone - and it
    # mutates by marker rather than by swap.
    Scenario Outline: The instant a resolution is submitted is what is recorded for it, whenever that is
      Given the notice reports a policy number of "absent"
      And the notice is submitted at "2026-08-24T16:00Z"
      And the notice is submitted for intake
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer's resolution is submitted at "<resolved_at>"
      Then the response is 200
      And the audit trail's last entry is stamped <recorded_at>
      And the notice's pend is still stamped <pended_at>

      Examples:
        | resolved_at       | recorded_at       | pended_at         |
        | 2026-08-25T09:00Z | 2026-08-25T09:00Z | 2026-08-24T16:00Z |
        | 2026-08-26T14:30Z | 2026-08-26T14:30Z | 2026-08-24T16:00Z |
