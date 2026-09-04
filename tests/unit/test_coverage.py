"""Unit tests for claimgate.domain.coverage.

The spec's rows are repeated here because unit tests call the domain directly
and never read feature files (docs/harness-findings.md, "A green gate sometimes
means nothing was checked"). The rest probes what Gherkin does not: citations
the spec leaves unstated, input order, histories a source system could deliver
that the spec never states, and the malformed histories that are errors.
"""

from datetime import date

import pytest

from claimgate.domain.coverage import (
    BOUNDARY_DAY,
    CANCELLATION,
    IN_FORCE,
    NOT_EVALUATED,
    NOT_IN_FORCE,
    REINSTATEMENT,
    PolicyTerm,
    PriorCoverage,
    StatusChangeKind,
    TermHistory,
    TermInForceDetermination,
    TermStatusChange,
    determine_term_in_force,
    in_force_periods,
)


def term(effective: str, expiration: str, *changes: tuple[StatusChangeKind, str]) -> PolicyTerm:
    return PolicyTerm(
        effective=date.fromisoformat(effective),
        expiration=date.fromisoformat(expiration),
        status_changes=tuple(
            TermStatusChange(kind=kind, effective=date.fromisoformat(on)) for kind, on in changes
        ),
    )


def determine(terms: list[PolicyTerm], loss_date: str) -> TermInForceDetermination:
    history = TermHistory(value="OBTAINED", terms=tuple(terms))
    return determine_term_in_force(history, date.fromisoformat(loss_date))


SINGLE = term("2026-01-15", "2027-01-15")
CANCELLED = term("2026-01-15", "2027-01-15", (CANCELLATION, "2026-06-10"))
REINSTATED_WITH_LAPSE = term(
    "2026-01-15", "2027-01-15", (CANCELLATION, "2026-06-10"), (REINSTATEMENT, "2026-07-20")
)
REINSTATED_RETROACTIVELY = term(
    "2026-01-15", "2027-01-15", (CANCELLATION, "2026-06-10"), (REINSTATEMENT, "2026-06-10")
)
CANCELLED_TWICE = term(
    "2026-01-15",
    "2027-01-15",
    (CANCELLATION, "2026-06-10"),
    (REINSTATEMENT, "2026-07-20"),
    (CANCELLATION, "2026-09-01"),
)
CANCELLED_FLAT = term("2026-01-15", "2027-01-15", (CANCELLATION, "2026-01-15"))
CANCELLED_ON_EXPIRATION = term("2026-01-15", "2027-01-15", (CANCELLATION, "2027-01-15"))
GAP = [term("2025-01-15", "2026-01-15"), term("2026-03-01", "2027-03-01")]
RENEWAL = [term("2025-06-01", "2026-06-01"), term("2026-06-01", "2027-06-01")]
# Cancelled mid-term and rewritten the same day: the spans overlap, the
# coverage does not.
REWRITE = [
    term("2026-01-01", "2027-01-01", (CANCELLATION, "2026-05-15")),
    term("2026-05-15", "2027-05-15"),
]
REWRITE_THEN_CANCELLED = [
    term("2026-01-01", "2027-01-01", (CANCELLATION, "2026-05-15")),
    term("2026-05-15", "2027-05-15", (CANCELLATION, "2026-08-01")),
]


@pytest.mark.parametrize(
    ("terms", "loss_date", "expected"),
    [
        ([SINGLE], "2026-01-14", NOT_IN_FORCE),
        ([SINGLE], "2026-01-15", BOUNDARY_DAY),
        ([SINGLE], "2026-01-16", IN_FORCE),
        ([SINGLE], "2026-07-04", IN_FORCE),
        ([SINGLE], "2027-01-14", IN_FORCE),
        ([SINGLE], "2027-01-15", BOUNDARY_DAY),
        ([SINGLE], "2027-01-16", NOT_IN_FORCE),
        (GAP, "2024-12-31", NOT_IN_FORCE),
        (GAP, "2026-02-01", NOT_IN_FORCE),
        (GAP, "2026-06-01", IN_FORCE),
        (GAP, "2027-04-01", NOT_IN_FORCE),
        (RENEWAL, "2026-06-01", BOUNDARY_DAY),
        ([CANCELLED], "2026-01-20", IN_FORCE),
        ([CANCELLED], "2026-06-09", IN_FORCE),
        ([CANCELLED], "2026-06-10", BOUNDARY_DAY),
        ([CANCELLED], "2026-06-11", NOT_IN_FORCE),
        ([CANCELLED], "2026-12-01", NOT_IN_FORCE),
        ([REINSTATED_WITH_LAPSE], "2026-07-01", NOT_IN_FORCE),
        ([REINSTATED_WITH_LAPSE], "2026-07-20", BOUNDARY_DAY),
        ([REINSTATED_WITH_LAPSE], "2026-07-21", IN_FORCE),
        ([REINSTATED_WITH_LAPSE], "2026-12-01", IN_FORCE),
        ([REINSTATED_RETROACTIVELY], "2026-07-01", IN_FORCE),
        ([REINSTATED_RETROACTIVELY], "2026-06-10", IN_FORCE),
        # Beyond the spec: histories a source system could deliver.
        ([], "2026-06-01", NOT_IN_FORCE),
        ([CANCELLED], "2027-01-15", NOT_IN_FORCE),
        ([CANCELLED_FLAT], "2026-01-15", NOT_IN_FORCE),
        ([CANCELLED_FLAT], "2026-01-16", NOT_IN_FORCE),
        ([CANCELLED_ON_EXPIRATION], "2026-06-01", IN_FORCE),
        ([CANCELLED_ON_EXPIRATION], "2027-01-15", BOUNDARY_DAY),
        ([CANCELLED_TWICE], "2026-08-01", IN_FORCE),
        ([CANCELLED_TWICE], "2026-09-01", BOUNDARY_DAY),
        ([CANCELLED_TWICE], "2026-10-01", NOT_IN_FORCE),
        (REWRITE, "2026-04-01", IN_FORCE),
        (REWRITE, "2026-05-15", BOUNDARY_DAY),
        (REWRITE, "2026-09-01", IN_FORCE),
    ],
)
def test_determination_value(terms: list[PolicyTerm], loss_date: str, expected: str) -> None:
    assert determine(terms, loss_date).value == expected


@pytest.mark.parametrize(
    ("terms", "loss_date", "expected_term", "expected_cancellation"),
    [
        (RENEWAL, "2026-09-15", RENEWAL[1], None),
        (REWRITE, "2026-09-01", REWRITE[1], None),
        ([CANCELLED], "2026-08-01", CANCELLED, "2026-06-10"),
        ([CANCELLED], "2027-01-15", CANCELLED, "2026-06-10"),
        ([CANCELLED_FLAT], "2026-01-15", CANCELLED_FLAT, "2026-01-15"),
        ([REINSTATED_WITH_LAPSE], "2026-07-01", REINSTATED_WITH_LAPSE, "2026-06-10"),
        # The cancellation cited is the one whose lapse the date is in, not the
        # first on the term and not the first term's.
        ([CANCELLED_TWICE], "2026-07-01", CANCELLED_TWICE, "2026-06-10"),
        ([CANCELLED_TWICE], "2026-10-01", CANCELLED_TWICE, "2026-09-01"),
        (REWRITE_THEN_CANCELLED, "2026-09-01", REWRITE_THEN_CANCELLED[1], "2026-08-01"),
        # No term decided: nothing is cited.
        (GAP, "2026-02-01", None, None),
        ([SINGLE], "2026-01-14", None, None),
        (RENEWAL, "2026-06-01", None, None),
    ],
)
def test_determination_cites_the_deciding_term_and_cancellation(
    terms: list[PolicyTerm],
    loss_date: str,
    expected_term: PolicyTerm | None,
    expected_cancellation: str | None,
) -> None:
    determination = determine(terms, loss_date)

    assert determination.term == expected_term
    expected = None if expected_cancellation is None else date.fromisoformat(expected_cancellation)
    assert determination.cancellation_effective == expected
    assert determination.reason is None


def test_history_not_obtained_is_not_evaluated_with_the_source_reason() -> None:
    history = TermHistory(value="NOT_OBTAINED", reason="SOURCE_TIMEOUT")

    determination = determine_term_in_force(history, date(2026, 6, 1))

    assert determination == TermInForceDetermination(value=NOT_EVALUATED, reason="SOURCE_TIMEOUT")


def test_history_not_obtained_without_a_reason_is_an_error() -> None:
    with pytest.raises(ValueError, match=r"^term history not obtained states no reason"):
        determine_term_in_force(TermHistory(value="NOT_OBTAINED"), date(2026, 6, 1))


@pytest.mark.parametrize("loss_date", ["2026-02-01", "2026-06-01", "2026-05-15", "2026-09-01"])
def test_term_order_does_not_change_the_determination(loss_date: str) -> None:
    for terms in (GAP, REWRITE, REWRITE_THEN_CANCELLED):
        assert determine(list(reversed(terms)), loss_date) == determine(terms, loss_date)


def outcome(determination: TermInForceDetermination) -> tuple[str, date | None, date | None]:
    """What a determination says, without the cited term's own change order -
    the term is cited as supplied, so two orderings of one history cite two
    equal terms whose tuples differ."""
    cited = None if determination.term is None else determination.term.effective
    return (determination.value, cited, determination.cancellation_effective)


@pytest.mark.parametrize("loss_date", ["2026-06-10", "2026-07-01", "2026-07-20", "2026-10-01"])
def test_status_change_order_does_not_change_the_determination(loss_date: str) -> None:
    for ordered in (REINSTATED_WITH_LAPSE, REINSTATED_RETROACTIVELY, CANCELLED_TWICE):
        shuffled = PolicyTerm(
            effective=ordered.effective,
            expiration=ordered.expiration,
            status_changes=tuple(reversed(ordered.status_changes)),
        )
        assert outcome(determine([shuffled], loss_date)) == outcome(determine([ordered], loss_date))


@pytest.mark.parametrize(
    ("terms", "message"),
    [
        ([term("2026-01-15", "2026-01-15")], r"^term effective 2026-01-15 expires on or before"),
        ([term("2026-01-15", "2025-01-15")], r"^term effective 2026-01-15 expires on or before"),
        (
            [term("2026-01-15", "2027-01-15", (CANCELLATION, "2026-01-14"))],
            r"^cancellation effective 2026-01-14 is dated outside its term 2026-01-15",
        ),
        (
            [term("2026-01-15", "2027-01-15", (CANCELLATION, "2027-01-16"))],
            r"^cancellation effective 2027-01-16 is dated outside its term",
        ),
        (
            [
                term(
                    "2026-01-15",
                    "2027-01-15",
                    (CANCELLATION, "2026-06-10"),
                    (REINSTATEMENT, "2027-01-16"),
                )
            ],
            r"^reinstatement effective 2027-01-16 is dated outside its term",
        ),
        (
            [term("2026-01-15", "2027-01-15", (REINSTATEMENT, "2026-07-20"))],
            r"^reinstatement effective 2026-07-20 with no cancellation to reinstate",
        ),
        (
            [
                term(
                    "2026-01-15",
                    "2027-01-15",
                    (CANCELLATION, "2026-07-20"),
                    (REINSTATEMENT, "2026-06-10"),
                )
            ],
            r"^reinstatement effective 2026-06-10 with no cancellation to reinstate",
        ),
        (
            [
                term(
                    "2026-01-15",
                    "2027-01-15",
                    (CANCELLATION, "2026-06-10"),
                    (CANCELLATION, "2026-09-01"),
                )
            ],
            r"^cancellation effective 2026-09-01 on a term already cancelled",
        ),
        (
            [term("2026-01-15", "2027-01-15"), term("2026-06-01", "2027-06-01")],
            r"^term history is inconsistent: terms effective 2026-01-15 and 2026-06-01 were both",
        ),
    ],
)
def test_malformed_history_is_an_error_not_a_determination(
    terms: list[PolicyTerm], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        determine(terms, "2026-09-01")


# The advisor's probe: two terms in force at once, both cancelled the same day.
# Whichever is stated first, the history is malformed - two terms in force on
# one day - and no loss date answers it, covered or lapsed.
OVERLAPPING = [
    term("2026-01-01", "2027-01-01", (CANCELLATION, "2026-06-01")),
    term("2026-03-01", "2027-03-01", (CANCELLATION, "2026-06-01")),
]
# A rewrite voided on its own effective date: no day in force is shared, so the
# overlap rule does not see it, and the two cancellations tie on the date.
REWRITE_VOIDED = [
    term("2026-01-01", "2027-01-01", (CANCELLATION, "2026-06-01")),
    term("2026-06-01", "2027-06-01", (CANCELLATION, "2026-06-01")),
]


@pytest.mark.parametrize("loss_date", ["2026-04-01", "2026-08-01"])
@pytest.mark.parametrize("reverse", [False, True])
def test_terms_in_force_on_the_same_day_are_an_error_in_either_order(
    loss_date: str, reverse: bool
) -> None:
    terms = list(reversed(OVERLAPPING)) if reverse else OVERLAPPING
    message = r"^term history is inconsistent: terms effective 2026-01-01 and 2026-03-01 were both"
    with pytest.raises(ValueError, match=message):
        determine(terms, loss_date)


@pytest.mark.parametrize("reverse", [False, True])
def test_two_terms_cancelled_the_same_day_holding_the_loss_date_are_an_error(
    reverse: bool,
) -> None:
    terms = list(reversed(REWRITE_VOIDED)) if reverse else REWRITE_VOIDED
    message = r"^term history is inconsistent: 2 terms cancelled 2026-06-01 hold 2026-08-01"
    with pytest.raises(ValueError, match=message):
        determine(terms, "2026-08-01")


# Item 7b: the history carries what the continuous-coverage rule reads - the
# source's horizon and any prior-carrier coverage - and this rule reads terms
# only. Prior-carrier days are never in force with this carrier, so a stated
# prior interval decides nothing here: not IN_FORCE, not a boundary, and never
# an overlap with the own term it meets.
PRIOR_CARRIER = PriorCoverage(effective=date(2017, 5, 20), ending=date(2023, 2, 10))
TAKEOUT = term("2023-02-01", "2024-02-01")


@pytest.mark.parametrize(
    ("loss_date", "expected"),
    [
        ("2020-06-01", NOT_IN_FORCE),
        ("2023-01-31", NOT_IN_FORCE),
        ("2023-02-01", BOUNDARY_DAY),
        ("2023-02-05", IN_FORCE),
        ("2023-02-10", IN_FORCE),
        ("2023-02-11", IN_FORCE),
    ],
)
def test_prior_carrier_coverage_and_the_horizon_never_decide_the_determination(
    loss_date: str, expected: str
) -> None:
    history = TermHistory(
        value="OBTAINED",
        terms=(TAKEOUT,),
        history_from=date(2020, 1, 1),
        prior_coverage=PRIOR_CARRIER,
    )
    bare = TermHistory(value="OBTAINED", terms=(TAKEOUT,))

    determination = determine_term_in_force(history, date.fromisoformat(loss_date))

    assert determination.value == expected
    assert determination == determine_term_in_force(bare, date.fromisoformat(loss_date))
    assert determination.term == (TAKEOUT if expected == IN_FORCE else None)


@pytest.mark.parametrize(
    ("terms", "expected"),
    [
        ([SINGLE], [("2026-01-15", "2027-01-15")]),
        ([CANCELLED], [("2026-01-15", "2026-06-10")]),
        ([REINSTATED_WITH_LAPSE], [("2026-01-15", "2026-06-10"), ("2026-07-20", "2027-01-15")]),
        ([REINSTATED_RETROACTIVELY], [("2026-01-15", "2027-01-15")]),
        ([CANCELLED_FLAT], []),
        (REWRITE, [("2026-01-01", "2026-05-15"), ("2026-05-15", "2027-05-15")]),
        (list(reversed(REWRITE)), [("2026-01-01", "2026-05-15"), ("2026-05-15", "2027-05-15")]),
        (list(reversed(GAP)), [("2025-01-15", "2026-01-15"), ("2026-03-01", "2027-03-01")]),
        ([], []),
    ],
)
def test_in_force_periods_are_the_days_each_term_ran_earliest_first(
    terms: list[PolicyTerm], expected: list[tuple[str, str]]
) -> None:
    history = TermHistory(value="OBTAINED", terms=tuple(terms))

    periods = in_force_periods(history)

    assert periods == [(date.fromisoformat(a), date.fromisoformat(b)) for a, b in expected]


def test_in_force_periods_refuse_a_malformed_history_like_the_determination() -> None:
    with pytest.raises(ValueError, match=r"^term history is inconsistent"):
        in_force_periods(TermHistory(value="OBTAINED", terms=tuple(OVERLAPPING)))
