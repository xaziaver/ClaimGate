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
  # PHASE2_DESIGN.md's status-code table also lists a fourth idempotency
  # outcome this file does not draft: "idempotency key reused with a
  # different payload" -> 409, distinct from an ordinary replay's 200.
  # Nothing in the Idempotency section says how the two are told apart -
  # whether by comparing the submitted content, and if so by what rule - so
  # every scenario below resubmits the Background's own notice content
  # unchanged, and no scenario here claims the 409 case. Drafting one would
  # mean inventing that comparison, which is exactly the kind of undecided
  # behavior CLAUDE.md's standing constraints forbid defaulting. Escalated,
  # not built.
  #
  # A replay is not a state transition: PHASE2_DESIGN.md, "Replays stay out
  # of the audit trail... since a replay isn't a state transition." The
  # first rule below is where that is proven, on the notice its own replay
  # returns rather than as a claim asserted in isolation.

  Background:
    Given the carrier "AAAA" requires the claimant name
    And "AAAA" does not require the claimant contact
    And "AAAA" recognizes the policy-number prefixes "HO;DP"
    And "AAAA" configures a duplicate match window of 60 days
    And the carrier "BBBB" requires the claimant name
    And "BBBB" does not require the claimant contact
    And "BBBB" recognizes the policy-number prefixes "HO;DP"
    And "BBBB" configures a duplicate match window of 60 days
    And the notice is submitted by carrier "AAAA"
    And the jurisdiction observes "America/New_York"
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
    # The instants just inside and just outside the boundary are each a
    # full minute from the 24-hour mark, not a single second, so the exact
    # instant - whether a submission arriving at precisely 24:00:00 later
    # counts as within the window or past it - is not asserted either side.
    # Nothing read while drafting this decides that tie, and guessing it
    # would default a retention behavior CLAUDE.md's standing constraints
    # forbid defaulting.
    Scenario Outline: How long after the original submission a replay arrives decides whether it returns that notice or creates a new one
      Given the notice is submitted with the idempotency key "K-100"
      And the notice is submitted for intake
      And that submission is remembered as the original
      When the notice is submitted at "<replay_submitted_at>"
      And the notice is submitted for intake
      Then the response is <response>
      And the response <notice_relation>
      And the response <timestamp_relation>
      And the audit trail holds no entry beyond those two
      And the notice can be retrieved afterward, showing state TRIAGED

      Examples:
        | replay_submitted_at | response | notice_relation                            | timestamp_relation                     |
        | 2026-08-25T15:59Z   | 200      | identifies the original notice             | reports the original receipt timestamp |
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
