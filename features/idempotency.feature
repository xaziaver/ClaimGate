Feature: Idempotency on notice submission

  As a claims intake system
  I need a repeated submission carrying the same idempotency key to return
  the notice it already created, not a second one
  So that a caller's network retry of a submission never produces a
  duplicate notice, without either caller or carrier losing the receipt
  the first attempt already earned

  # PHASE2_DESIGN.md's Idempotency section is this file's specification
  # input, closed before this draft started. There is no HTTP layer
  # anywhere in this project yet - features/notice_intake.feature's own
  # opening comment says the same about the carrier code and the
  # submission instant. An idempotency key arrives as an ordinary input to
  # intake, the same way those two already do, not as a header this file
  # has any machinery to represent. Every scenario below states it as a
  # plain business fact of the submission for that reason.
  #
  # Uniqueness is the pair (carrier_code, idempotency_key), enforced by a
  # database constraint rather than a check-then-write - a concurrency
  # mechanism, not a caller-observable behavior, and nothing below asserts
  # it directly, for the same reason nothing in carrier_configuration.feature
  # names the loader that enforces its own constraints.
  #
  # The key is envelope, like the carrier code: it is examined after the
  # carrier-identity check and before the loss-date schema boundary, so a
  # repeated key is answered - as a replay or as a conflict - before the
  # content it accompanies is judged. A key is remembered only by the notice
  # it created; a submission refused at the schema boundary creates no
  # notice, and its key is not remembered against the refusal. Both decided
  # 2026-08-24, recorded in ASSUMPTIONS.md, "Idempotency: what a repeated
  # key is compared against".
  #
  # A replay is not a state transition: PHASE2_DESIGN.md, "Replays stay out
  # of the audit trail... since a replay isn't a state transition." The
  # first rule below is where that is proven, on the notice its own replay
  # returns rather than as a claim asserted in isolation.

  Background:
    Given the carrier "AAAA" requires the claimant name
    And "AAAA" does not require the claimant contact
    And "AAAA" configures a duplicate match window of 60 days
    And the carrier "BBBB" requires the claimant name
    And "BBBB" does not require the claimant contact
    And "BBBB" configures a duplicate match window of 60 days
    And the notice is submitted by carrier "AAAA"
    And the insured property is in "FL"
    And the notice is submitted at "2026-08-24T16:00Z"
    And the notice reports a policy number of "HO-1234567"
    And the notice reports a loss date of "2026-06-01"
    And the notice reports a loss type of "wind_hail"
    And the notice reports a notice type of "INITIAL"

  Rule: A repeated idempotency key returns the original notice within its 24-hour window, and a fresh one once that window has passed

    # PHASE2_DESIGN.md, verbatim: keys expire after 24 hours, because past
    # that window a resubmission "isn't a network retry anymore, it's a
    # resubmission" - and a resubmission goes through business duplicate
    # detection, not idempotency (QUEUE.md item 3's find_duplicates, not
    # built here). This rule asserts only which side of that boundary a
    # replay lands on, not what happens to it on the far side: the row past
    # the boundary creates its own new notice exactly the way a first-ever
    # submission would, because past the window there is no idempotency
    # record left to find. It does not re-assert that a fresh notice
    # reaches TRIAGED or PENDED correctly - notice_intake.feature already
    # proves that.
    #
    # The window is half-open: a replay is within it strictly before the
    # 24-hour mark and past it at the mark itself. The middle row lands at
    # exactly 24 hours and is expired. Decided 2026-08-24 on the convention
    # every caller's HTTP stack already applies - RFC 9111 section 4.2, a
    # stored response is fresh only while its lifetime exceeds its age, and
    # stale at equality - recorded in ASSUMPTIONS.md. The rows either side
    # sit a full minute away so that the boundary itself is the middle
    # row's job and nothing else's.
    Scenario Outline: How long after the original submission a replay arrives decides whether it returns that notice or creates a new one
      Given the notice is submitted with the idempotency key "K-100"
      And the notice is submitted for intake
      And that submission is remembered as the original
      When the notice is submitted at "<replay_submitted_at>"
      And the notice is submitted for intake
      Then the response is <response>
      And the response <notice_relation>
      And the response <timestamp_relation>
      And the original notice's audit trail still holds exactly its two entries
      And the original notice can still be retrieved, showing state TRIAGED

      Examples:
        | replay_submitted_at | response | notice_relation                            | timestamp_relation                     |
        | 2026-08-25T15:59Z   | 200      | identifies the original notice             | reports the original receipt timestamp |
        | 2026-08-25T16:00Z   | 201      | identifies a new notice, not the original  | reports its own new receipt timestamp  |
        | 2026-08-25T16:01Z   | 201      | identifies a new notice, not the original  | reports its own new receipt timestamp  |

  Rule: The same idempotency key from two different carriers is not a collision

    # PHASE2_DESIGN.md, verbatim: "The same key from two different
    # carriers is not a collision." Uniqueness is the pair (carrier_code,
    # idempotency_key), not the key alone - a second, independent axis from
    # the rule above's elapsed-time boundary, proven in its own table
    # rather than folded into that one: combining both axes in one outline
    # would let a mutant on either axis borrow the other axis's row and
    # still land on the same "a new notice" outcome, the exact borrowed-row
    # failure notice_intake.feature's own Rule 4 found and split apart for.
    Scenario Outline: Whether a second submission collides with the first depends on whether it names the same carrier
      Given the notice is submitted with the idempotency key "K-200"
      And the notice is submitted for intake
      And that submission is remembered as the original
      When the notice is submitted by carrier "<carrier_code>"
      And the notice is submitted for intake
      Then the response is <response>
      And the response <notice_relation>

      Examples:
        | carrier_code | response | notice_relation                            |
        | AAAA         | 200      | identifies the original notice             |
        | BBBB         | 201      | identifies a new notice, not the original  |

  Rule: A submission with no idempotency key is never treated as a replay

    # PHASE2_DESIGN.md: "POST /notices accepts an optional Idempotency-Key
    # header." Its absence has to mean something specific and provable, not
    # merely untested: a caller that stops sending the key it used the
    # first time gets ordinary at-least-once semantics on that call, the
    # same behavior notice_intake.feature already proves for a caller that
    # never sends one at all. A third independent axis from the two rules
    # above, kept in its own table for the same borrowed-row reason.
    #
    # The original submission's own key is held fixed here rather than
    # varied alongside the second submission's: measured and simulated
    # before this was written to disk, varying both columns together over
    # an absent/absent row made each key column's value irrelevant to the
    # other whenever either one was absent, so a mutant swapping either
    # half of that row left the actual outcome unchanged - the same
    # symmetric-blank-row failure item 5a's refusal outline found. Fixing
    # the original key and varying only the second submission's removes the
    # symmetry: every swap now either turns a matching replay into a
    # mismatched one or the reverse.
    Scenario Outline: Whether the second submission repeats the notice depends on whether it supplies the original key
      Given the notice is submitted with the idempotency key "K-300"
      And the notice is submitted for intake
      And that submission is remembered as the original
      When the notice is submitted with the idempotency key "<second_key>"
      And the notice is submitted for intake
      Then the response is <response>
      And the response <notice_relation>

      Examples:
        | second_key | response | notice_relation                            |
        | K-300      | 200      | identifies the original notice             |
        | absent     | 201      | identifies a new notice, not the original  |

  Rule: A replay reports the notice's state as it stands now, not as it stood when first processed

    # PHASE2_DESIGN.md, verbatim: a replay carries "the current state, not
    # the state at first processing - the notice may have moved since." No
    # notice can move yet - the PENDED-to-TRIAGED transition is item 5e's
    # endpoint, not built - so the only observable today is that the state
    # a replay reports comes from the notice rather than from a constant: a
    # notice that landed PENDED replays as PENDED. The post-resolution case
    # is item 5e's to prove, recorded there as a carried requirement.
    Scenario Outline: What state a replay reports depends on where the original notice landed
      Given the notice reports a policy number of "<policy_number>"
      And the notice is submitted with the idempotency key "K-500"
      And the notice is submitted for intake
      And that submission is remembered as the original
      When the notice is submitted for intake
      Then the response is 200
      And the response identifies the original notice
      And the notice's state is <state>

      Examples:
        | policy_number | state   |
        | HO-1234567    | TRIAGED |
        | absent        | PENDED  |

  Rule: A repeated idempotency key carrying different notice content is a conflict, not a replay

    # PHASE2_DESIGN.md's status-code table: "idempotency key reused with a
    # different payload" -> 409. "Different" means the resubmission's payload
    # reference - the recipe ASSUMPTIONS.md already records under "The
    # payload reference recipe" - differs from the reference linked to the
    # notice the key resolves to. One recipe, already persisted on every
    # notice; no second definition of "the same submission". A conflict
    # creates no notice and adds nothing to the original's trail, but the
    # conflicting content is kept with a reference of its own, the way a
    # schema-invalid submission's is - this is an administered carrier and
    # the content may be a real loss whose caller mis-keyed it. Decided
    # 2026-08-24, recorded in ASSUMPTIONS.md.
    Scenario Outline: Whether a repeated key is honoured as a replay depends on whether the notice content is unchanged
      Given the notice is submitted with the idempotency key "K-400"
      And the notice is submitted for intake
      And that submission is remembered as the original
      When the notice reports a loss type of "<second_loss_type>"
      And the notice is submitted for intake
      Then the response is <response>
      And the response <notice_relation>
      And the original notice's audit trail still holds exactly its two entries

      Examples:
        | second_loss_type | response | notice_relation                |
        | wind_hail        | 200      | identifies the original notice |
        | fire             | 409      | identifies no notice at all    |

  Rule: An idempotency key is remembered only by the notice it created

    # A submission refused at the schema boundary (notice_intake.feature,
    # "A notice is created only if its loss date is a real date") creates
    # no notice, so there is nothing for its key to name. The key is not
    # remembered against the refusal: the caller's next use of it is judged
    # on its own, and a corrected resubmission under the same key creates
    # the notice the first attempt could not. This is what places the
    # uniqueness constraint on the notice itself rather than on a record of
    # attempts.
    #
    # The third row is item 5i's, and it is the row this file could not
    # carry before that item existed. A first use that ended in this
    # deployment's own defect created no notice, so its key names nothing
    # and the retry is judged on its own - the same rule the second row
    # states, reached by a different route. What makes it a separate proof
    # rather than a second copy is that the retry's payload is identical to
    # the first attempt's: the first submission was never wrong, only
    # unanswerable, so the reporter sends exactly what they sent before.
    # An implementation that remembered a key against the submission's
    # payload reference instead of against the notice it created would
    # answer that identical retry 200 with nothing created, and the second
    # row cannot catch it, because a corrected resubmission necessarily
    # carries a different payload. Item 5i's own decision that a
    # deployment fault creates no notice is what makes this row true; the
    # opposite answer - a notice left behind at RECEIVED with its key
    # remembered - would make the retry a replay of a notice no rule ever
    # ran over, and the reporter's corrected deployment would never
    # produce a decision at all.
    #
    # The 500 fault is set on the loss date the first row uses, not the
    # second's, because the schema boundary is checked before the
    # configuration is read: a submission whose loss date does not parse is
    # answered 400 whether or not this deployment can load the carrier's
    # rules. Two substitutions between rows survive for exactly that reason
    # and are equivalent - swapping the fault onto the not-a-date row, or
    # the not-a-date onto the fault row, produces a row whose first attempt
    # still creates nothing and whose retry still creates. They sit in one
    # scenario so one approval reason covers the single argument
    # (.claude/skills/gherkin-specs, constraint 4).
    Scenario Outline: Whether a repeated key finds a notice depends on whether its first use created one
      Given the notice reports a loss date of "<first_loss_date>"
      And <deployment_fault>
      And the notice is submitted with the idempotency key "K-600"
      And the notice is submitted for intake
      And that submission is remembered as the original
      When this deployment is configured correctly
      And the notice reports a loss date of "2026-06-01"
      And the notice is submitted for intake
      Then the response is <response>
      And the response <notice_relation>

      Examples:
        | first_loss_date | deployment_fault                             | response | notice_relation                            |
        | 2026-06-01      | this deployment is configured correctly      | 200      | identifies the original notice             |
        | not-a-date      | this deployment is configured correctly      | 201      | identifies a new notice, not the original  |
        | 2026-06-01      | the carrier's rules entry cannot be resolved | 201      | identifies a new notice, not the original  |
