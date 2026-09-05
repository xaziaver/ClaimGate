"""Unit tests for claimgate.domain.continuous_coverage.

The spec's scenarios are repeated here because unit tests call the domain
directly and never read feature files (docs/harness-findings.md, "A green gate
sometimes means nothing was checked"). The rest probes the three cases the
human decided beyond the spec on 2026-09-04, the judgments the implementation
made past those, input order, and the malformed histories that are errors.
"""

from datetime import date

import pytest

from claimgate.domain.continuous_coverage import (
    CONTINUOUS_COVERAGE_REASONS,
    DERIVED,
    HISTORY_MAY_PREDATE_SOURCE,
    NO_COVERAGE_ON_LOSS_DATE,
    ContinuousCoverageDerivation,
    derive_continuous_coverage,
)
from claimgate.domain.coverage import (
    CANCELLATION,
    NOT_EVALUATED,
    REINSTATEMENT,
    PolicyTerm,
    PriorCoverage,
    StatusChangeKind,
    TermHistory,
    TermStatusChange,
)


def term(effective: str, expiration: str, *changes: tuple[StatusChangeKind, str]) -> PolicyTerm:
    return PolicyTerm(
        effective=date.fromisoformat(effective),
        expiration=date.fromisoformat(expiration),
        status_changes=tuple(
            TermStatusChange(kind=kind, effective=date.fromisoformat(on)) for kind, on in changes
        ),
    )


def prior(effective: str, ending: str) -> PriorCoverage:
    return PriorCoverage(effective=date.fromisoformat(effective), ending=date.fromisoformat(ending))


def derive(
    terms: list[PolicyTerm],
    loss_date: str,
    *,
    history_from: str | None = None,
    prior_coverage: PriorCoverage | None = None,
) -> ContinuousCoverageDerivation:
    history = TermHistory(
        value="OBTAINED",
        terms=tuple(terms),
        history_from=None if history_from is None else date.fromisoformat(history_from),
        prior_coverage=prior_coverage,
    )
    return derive_continuous_coverage(history, date.fromisoformat(loss_date))


def since(value: str) -> ContinuousCoverageDerivation:
    return ContinuousCoverageDerivation(value="DERIVED", continuous_since=date.fromisoformat(value))


def not_evaluated(reason: str) -> ContinuousCoverageDerivation:
    return ContinuousCoverageDerivation(value="NOT_EVALUATED", reason=reason)


SINGLE = [term("2026-01-15", "2027-01-15")]
RENEWALS = [
    term("2023-02-01", "2024-02-01"),
    term("2024-02-01", "2025-02-01"),
    term("2025-02-01", "2026-02-01"),
]
TWO_LAPSES = [
    term("2021-04-01", "2022-04-01"),
    term("2022-05-01", "2023-05-01"),
    term("2023-05-01", "2024-05-01"),
    term("2024-06-01", "2025-06-01"),
    term("2025-06-01", "2026-06-01"),
]
LAPSED_LATER = [
    term("2024-02-01", "2025-02-01"),
    term("2025-02-01", "2026-02-01", (CANCELLATION, "2025-09-01"), (REINSTATEMENT, "2025-10-15")),
]
CANCELLED_FOR_GOOD = [
    term("2024-02-01", "2025-02-01"),
    term("2025-02-01", "2026-02-01", (CANCELLATION, "2025-06-10")),
]
CANCELLED_ONE = [term("2024-02-01", "2025-02-01", (CANCELLATION, "2024-11-01"))]
GAP = [term("2024-02-01", "2025-02-01"), term("2025-03-15", "2026-03-15")]
RENEWAL = [term("2024-02-01", "2025-02-01"), term("2025-02-01", "2026-02-01")]
REWRITE = [
    term("2024-06-10", "2025-06-10", (CANCELLATION, "2024-11-01")),
    term("2024-11-01", "2025-11-01"),
]
RESCINDED = [
    term("2024-02-01", "2025-02-01"),
    term("2025-02-01", "2026-02-01", (CANCELLATION, "2025-06-10"), (REINSTATEMENT, "2025-06-10")),
]
LAPSED = [
    term("2024-02-01", "2025-02-01"),
    term("2025-02-01", "2026-02-01", (CANCELLATION, "2025-06-10"), (REINSTATEMENT, "2025-07-20")),
]
TAKEOUT = [term("2023-02-01", "2024-02-01"), term("2024-02-01", "2025-02-01")]
AT_HORIZON = [term("2020-01-01", "2021-01-01"), term("2021-01-01", "2022-01-01")]
BEFORE_HORIZON = [term("2019-06-01", "2020-06-01"), term("2020-06-01", "2021-06-01")]
BEFORE_HORIZON_THEN_LAPSE = [term("2019-06-01", "2020-06-01"), term("2020-09-01", "2021-09-01")]
GAP_AFTER_HORIZON = [term("2020-03-01", "2021-03-01"), term("2021-04-01", "2022-04-01")]


@pytest.mark.parametrize(
    ("terms", "loss_date", "expected"),
    [
        # features/continuous_coverage.feature, rule by rule.
        (SINGLE, "2026-08-03", since("2026-01-15")),
        (RENEWALS, "2025-09-12", since("2023-02-01")),
        ([RENEWAL[0], term("2025-02-01", "2026-03-15")], "2025-10-05", since("2024-02-01")),
        ([RENEWAL[0], term("2025-02-02", "2026-03-15")], "2025-10-05", since("2025-02-02")),
        ([RENEWAL[0], term("2025-03-15", "2026-03-15")], "2025-10-05", since("2025-03-15")),
        (TWO_LAPSES, "2025-11-14", since("2024-06-01")),
        (LAPSED_LATER, "2025-04-18", since("2024-02-01")),
        (LAPSED_LATER, "2025-09-20", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
        (CANCELLED_FOR_GOOD, "2025-08-01", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
        (CANCELLED_ONE, "2024-11-01", since("2024-02-01")),
        (GAP, "2025-03-15", since("2025-03-15")),
        (RENEWAL, "2025-02-01", since("2024-02-01")),
        (REWRITE, "2025-03-03", since("2024-06-10")),
        (RESCINDED, "2025-11-02", since("2024-02-01")),
        (LAPSED, "2025-11-02", since("2025-07-20")),
        # Decided 2026-09-04 beyond the spec: (b) a loss on an expiration date
        # with no renewal derives that run's start; (c) a loss on the first
        # day of a first term derives that day. The day past each is uncovered.
        (SINGLE, "2027-01-15", since("2026-01-15")),
        (SINGLE, "2027-01-16", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
        (SINGLE, "2026-01-15", since("2026-01-15")),
        (SINGLE, "2026-01-14", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
        # A loss on a rescinded cancellation date is inside one run.
        (RESCINDED, "2025-06-10", since("2024-02-01")),
        # The day a lapse began and the day it ended each belong to a run; the
        # days between belong to none.
        (LAPSED, "2025-06-10", since("2024-02-01")),
        (LAPSED, "2025-06-11", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
        (LAPSED, "2025-07-19", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
        (LAPSED, "2025-07-20", since("2025-07-20")),
        # Only the most recent lapse before the loss resets; an earlier run
        # answers a loss inside it.
        (TWO_LAPSES, "2023-01-01", since("2022-05-01")),
        (TWO_LAPSES, "2022-04-15", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
        # A history with no terms holds no date.
        ([], "2025-01-01", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
    ],
)
def test_derivation_over_own_terms(
    terms: list[PolicyTerm], loss_date: str, expected: ContinuousCoverageDerivation
) -> None:
    assert derive(terms, loss_date) == expected


@pytest.mark.parametrize(
    ("terms", "loss_date", "expected"),
    [
        # The spec's Rule 5, horizon "2020-01-01".
        (AT_HORIZON, "2021-06-15", not_evaluated("HISTORY_MAY_PREDATE_SOURCE")),
        ([term("2020-01-02", "2021-01-02")], "2020-09-09", since("2020-01-02")),
        (BEFORE_HORIZON, "2021-03-03", not_evaluated("HISTORY_MAY_PREDATE_SOURCE")),
        (BEFORE_HORIZON_THEN_LAPSE, "2021-05-05", since("2020-09-01")),
        ([term("2022-05-01", "2023-05-01")], "2022-11-11", since("2022-05-01")),
        (
            [term("2020-03-01", "2021-03-01")],
            "2019-11-11",
            not_evaluated("HISTORY_MAY_PREDATE_SOURCE"),
        ),
        (GAP_AFTER_HORIZON, "2021-03-15", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
        # Decided 2026-09-04 beyond the spec: (a) a loss dated exactly on the
        # horizon day and covered by no supplied term is HISTORY_MAY_PREDATE_
        # SOURCE; the day after is a gap the source can see.
        (
            [term("2020-03-01", "2021-03-01")],
            "2020-01-01",
            not_evaluated("HISTORY_MAY_PREDATE_SOURCE"),
        ),
        (
            [term("2020-03-01", "2021-03-01")],
            "2020-01-02",
            not_evaluated("NO_COVERAGE_ON_LOSS_DATE"),
        ),
        # A loss covered by a supplied term from before the horizon is the
        # run-start test, not the uncovered one.
        (BEFORE_HORIZON, "2019-08-01", not_evaluated("HISTORY_MAY_PREDATE_SOURCE")),
        # No terms at all: the loss date decides which side of the horizon.
        ([], "2020-01-01", not_evaluated("HISTORY_MAY_PREDATE_SOURCE")),
        ([], "2020-01-02", not_evaluated("NO_COVERAGE_ON_LOSS_DATE")),
    ],
)
def test_derivation_against_the_history_horizon(
    terms: list[PolicyTerm], loss_date: str, expected: ContinuousCoverageDerivation
) -> None:
    assert derive(terms, loss_date, history_from="2020-01-01") == expected


@pytest.mark.parametrize(
    ("prior_coverage", "terms", "loss_date", "expected"),
    [
        # The spec's Rule 4.
        (prior("2017-05-20", "2023-02-01"), TAKEOUT, "2024-07-09", since("2017-05-20")),
        (prior("2017-05-20", "2023-01-31"), TAKEOUT, "2024-07-09", since("2023-02-01")),
        (prior("2017-05-20", "2023-02-10"), TAKEOUT[:1], "2023-09-30", since("2017-05-20")),
        # Beyond the spec. A prior interval ending inside an earlier run does not
        # reach the run the loss is in; one ending on or after that run began
        # covered the gap between them, so the risk was continuously covered.
        (prior("2017-05-20", "2024-07-01"), GAP, "2025-10-01", since("2025-03-15")),
        (prior("2017-05-20", "2025-03-14"), GAP, "2025-10-01", since("2025-03-15")),
        (prior("2017-05-20", "2025-03-15"), GAP, "2025-10-01", since("2017-05-20")),
        # "Reaches" is measured against the day the run began, which for a run
        # opened by a lapsed reinstatement is the reinstatement date.
        (prior("2017-05-20", "2025-07-20"), LAPSED, "2025-11-02", since("2017-05-20")),
        (prior("2017-05-20", "2025-07-19"), LAPSED, "2025-11-02", since("2025-07-20")),
        # A prior interval beginning after the run did cannot move the date later.
        (prior("2023-06-01", "2023-08-01"), TAKEOUT, "2024-07-09", since("2023-02-01")),
        (prior("2023-02-01", "2023-08-01"), TAKEOUT, "2024-07-09", since("2023-02-01")),
        # The prior interval extends a run; it is not one. A loss inside it and
        # before any own term has no run of this carrier's coverage.
        (
            prior("2017-05-20", "2023-02-01"),
            TAKEOUT,
            "2020-06-01",
            not_evaluated("NO_COVERAGE_ON_LOSS_DATE"),
        ),
    ],
)
def test_derivation_reaching_back_into_prior_coverage(
    prior_coverage: PriorCoverage,
    terms: list[PolicyTerm],
    loss_date: str,
    expected: ContinuousCoverageDerivation,
) -> None:
    assert derive(terms, loss_date, prior_coverage=prior_coverage) == expected


def test_the_horizon_is_tested_on_the_own_run_before_any_prior_extension() -> None:
    reaching = prior("2015-01-01", "2020-01-01")

    on_horizon = derive(
        AT_HORIZON, "2021-06-15", history_from="2020-01-01", prior_coverage=reaching
    )
    after = derive(
        [term("2020-01-02", "2021-01-02")],
        "2020-09-09",
        history_from="2020-01-01",
        prior_coverage=prior("2015-01-01", "2020-01-02"),
    )

    assert on_horizon == not_evaluated("HISTORY_MAY_PREDATE_SOURCE")
    # A stated prior interval is a data point, so it may reach before the horizon.
    assert after == since("2015-01-01")


def test_history_not_obtained_is_not_evaluated_with_the_source_reason() -> None:
    history = TermHistory(
        value="NOT_OBTAINED",
        reason="SOURCE_UNAVAILABLE",
        # Ignored, unvalidated: the source's reason is the answer.
        prior_coverage=prior("2023-02-01", "2022-02-01"),
    )

    derivation = derive_continuous_coverage(history, date(2025, 8, 1))

    assert derivation == not_evaluated("SOURCE_UNAVAILABLE")


def test_history_not_obtained_without_a_reason_is_an_error() -> None:
    with pytest.raises(ValueError, match=r"^term history not obtained states no reason"):
        derive_continuous_coverage(TermHistory(value="NOT_OBTAINED"), date(2025, 8, 1))


@pytest.mark.parametrize("loss_date", ["2023-01-01", "2024-06-01", "2025-11-14", "2025-03-03"])
def test_term_order_does_not_change_the_derivation(loss_date: str) -> None:
    for terms in (TWO_LAPSES, REWRITE, LAPSED):
        assert derive(list(reversed(terms)), loss_date) == derive(terms, loss_date)


@pytest.mark.parametrize(
    ("prior_coverage", "message"),
    [
        (
            prior("2023-02-01", "2023-01-31"),
            r"^prior coverage effective 2023-02-01 ends 2023-01-31, on or before it takes effect",
        ),
        (
            prior("2023-02-01", "2020-01-01"),
            r"^prior coverage effective 2023-02-01 ends 2020-01-01, on or before it takes effect",
        ),
        # A zero-day interval covers nothing: malformed, as a zero-day term is
        # (human-ratified 2026-09-05, reversing the first cut's acceptance).
        (
            prior("2023-02-01", "2023-02-01"),
            r"^prior coverage effective 2023-02-01 ends 2023-02-01, on or before it takes effect",
        ),
    ],
)
def test_a_prior_interval_ending_on_or_before_it_is_effective_is_an_error(
    prior_coverage: PriorCoverage, message: str
) -> None:
    # Whatever the loss date: malformed input is refused before it is read.
    with pytest.raises(ValueError, match=message):
        derive(TAKEOUT, "2020-06-01", prior_coverage=prior_coverage)


def test_a_malformed_term_history_is_an_error_here_as_in_the_term_in_force_rule() -> None:
    overlapping = [term("2026-01-15", "2027-01-15"), term("2026-06-01", "2027-06-01")]
    with pytest.raises(ValueError, match=r"^term history is inconsistent"):
        derive(overlapping, "2026-09-01")


def test_the_reason_enumeration_is_closed_and_spelled_as_the_spec_spells_it() -> None:
    assert frozenset(
        {"HISTORY_MAY_PREDATE_SOURCE", "NO_COVERAGE_ON_LOSS_DATE"}
    ) == CONTINUOUS_COVERAGE_REASONS
    assert (HISTORY_MAY_PREDATE_SOURCE, NO_COVERAGE_ON_LOSS_DATE) == (
        "HISTORY_MAY_PREDATE_SOURCE",
        "NO_COVERAGE_ON_LOSS_DATE",
    )
    assert (DERIVED, NOT_EVALUATED) == ("DERIVED", "NOT_EVALUATED")
