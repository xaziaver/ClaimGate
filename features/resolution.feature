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
  # WHAT THIS DRAFT DELIBERATELY DOES NOT COVER, and why - five points
  # PHASE2_DESIGN.md leaves open, escalated 2026-08-25 in ASSUMPTIONS.md's
  # "Open decisions" and not defaulted here. Every scenario below is
  # written to sit inside the intersection of the open readings, so that
  # none of them has to be decided before this file can be locked:
  #
  #   1. What a resolution payload may contain. "The supplemental field
  #      values" is never given a set. Every resolution below supplies only
  #      fields the notice's own recorded blockers name, which is allowed
  #      under both the narrow reading and the broad one. No scenario
  #      supplies a field that was not blocked.
  #   2. What a resolution is evaluated against - which rules re-run, and
  #      against which calendar date. Every resolution below either clears
  #      its blockers or leaves one of them standing, and none introduces a
  #      blocker the notice did not already have, so re-checking only the
  #      recorded blockers and re-running the whole validation agree on
  #      every row. No notice below is pended for LOSS_DATE_IN_FUTURE,
  #      which is the blocker whose truth changes with the calendar date
  #      alone and so is the one the second half of that question turns on.
  #   3. What happens to the payload of a resolution that is not applied.
  #      Rule 3 asserts the arrival sequence only for a resolution that was
  #      applied. Nothing below asserts whether a refused resolution's or a
  #      conflicted resolution's content is kept, or where.
  #   4. Whether the actor's type is a caller input, and what a refused
  #      actor gets. Every resolution below is a reviewer's, so every
  #      audited attempt is a USER one. There is no scenario for a
  #      SYSTEM-actor attempt at this transition: the Record state model
  #      says such an attempt is refused and audited, but the closed
  #      status-code table has no row for it, and inventing one is exactly
  #      what CLAUDE.md's never-default constraint forbids.
  #   5. Whether the 409 for "not currently PENDED" covers a notice still
  #      standing at RECEIVED. Rule 1's second row is a TRIAGED notice,
  #      which the table's row plainly covers. A RECEIVED notice - which
  #      item 5d's two-transaction receipt made observable at rest for the
  #      first time, after that row was written - has no row here.
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
    And the jurisdiction observes "America/New_York"
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
    # The second row is a TRIAGED notice, not a RECEIVED one. A RECEIVED
    # notice is the case escalated as open point 5 above and has no row
    # here.
    Scenario Outline: Whether a resolution is acted on depends on the state the notice is already in
      Given the notice reports a policy number of "<policy_number>"
      And the notice is submitted for intake
      And the notice's state is <state_before>
      When the reviewer supplies a policy number of "HO-7654321"
      And the reviewer's resolution is submitted at "2026-08-25T09:00Z"
      Then the response is <response>
      And the notice's state is <state_after>
      And the notice's audit trail <audit_effect>

      Examples:
        | policy_number | state_before | response | state_after | audit_effect                            |
        | absent        | PENDED       | 200      | TRIAGED     | gains a third entry, for the resolution |
        | HO-1234567    | TRIAGED      | 409      | TRIAGED     | still holds only its two intake entries |

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
    # notice was held for. Both supplied fields are named by the notice's
    # own blockers, and neither row can introduce a blocker the notice did
    # not already have, which is what keeps this rule inside open points 1
    # and 2 rather than deciding them. The blocker codes are
    # validation.feature's own, reused rather than reinvented - this
    # endpoint gets no blocker vocabulary of its own.
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
      When the reviewer supplies a policy number of "HO-7654321"
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
        | supplied_notice_type | response | state   | blockers                             | outcome | actor | entry_blockers                       |
        | SUPPLEMENTAL         | 200      | TRIAGED |                                      | APPLIED | USER  |                                      |
        | SUPPLEMENT           | 422      | PENDED  | NOTICE_TYPE_UNRECOGNIZED:notice_type | REFUSED | USER  | NOTICE_TYPE_UNRECOGNIZED:notice_type |

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
      And the <ordinal> record kept for the notice <origin>
      And no third record is kept for the notice
      And the notice's current view reports a policy number of "HO-7654321"

      Examples:
        | ordinal | recorded_policy_number | origin                                        |
        | first   | absent                 | is the submission the notice was created from |
        | second  | HO-7654321             | is the reviewer's resolution                  |

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
