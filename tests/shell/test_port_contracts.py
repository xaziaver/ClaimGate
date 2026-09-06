"""The contract every port implementation keeps, run over every shape in
tests/shell/port_harness.py.

What a port promises is in ports.py's docstring; this suite is that promise
made executable, and item 7i's extract shape passes it unchanged or is not a
conforming implementation. Every fault answers the not-evaluated value with a
reason from the closed enumeration and nothing propagates; the budget is
enforced, not simulated; `as_of` is the injected clock's instant and `binding`
the binding's label on every answer including the not-evaluated ones; every
term history carries the configured horizon.

The clock and binding assertions follow docs/harness-findings.md, "A
swappability proof can pass without the thing being swapped": the observable
that differs between "clock supplied" and "clock absent" is the stamped
instant itself, so the fixed instant is one no wall clock can produce again,
and the label is one no implementation would invent.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime

import pytest

from claimgate.domain.coverage import (
    CANCELLATION,
    REINSTATEMENT,
    PolicyTerm,
    PriorCoverage,
    TermHistory,
    TermStatusChange,
)
from claimgate.domain.models import ExistingClaim
from claimgate.domain.policy_identification import (
    INSURED_NAME_AND_POSTAL_CODE,
    POLICY_NUMBER,
    SearchIdentifiers,
)
from claimgate.shell.bindings import ClaimsBinding, PolicyBinding
from claimgate.shell.ports import (
    FOUND,
    IDENTIFIERS_INSUFFICIENT,
    NOT_EVALUATED,
    NOT_FOUND,
    NOT_OBTAINED,
    OBTAINED,
    SOURCE_MALFORMED,
    SOURCE_TIMEOUT,
    SOURCE_UNAVAILABLE,
    ClaimsPort,
    ExistingClaimsAnswer,
    PolicyCandidate,
    PolicyPort,
    SearchAnswer,
    TermHistoryAnswer,
)
from tests.fixtures.core_system import FixtureAddress, claim, term
from tests.shell.port_harness import HARNESSES, PortHarness, SourceControls

# An instant in the past, so a stamp from any wall clock fails equality.
INSTANT = datetime(2024, 2, 29, 23, 59, 59, tzinfo=UTC)
POLICY_LABEL = "AAAA/policy:under-test"
CLAIMS_LABEL = "AAAA/claims:under-test"
REFERENCE = "src-ref-000001"
NUMBER = "HO-1234567"
INSUREDS = ("Dana Alvarez", "Ruth Alvarez")
ADDRESS = FixtureAddress(line="12 Palm Court", city="Naples", state="FL", postal_code="34102")
TERM = term(date(2025, 10, 1), date(2026, 10, 1))
BY_NUMBER = SearchIdentifiers(policy_number=NUMBER)
BY_NAME = SearchIdentifiers(insured_name="dana alvarez", risk_postal_code="34102")
# The budget the timeout contracts run under, and the sleep that exceeds it.
BUDGET = 0.05
SLEEP = 0.5
BOUNDED_BY = 0.4


def fixed_clock() -> datetime:
    return INSTANT


@dataclass(frozen=True)
class Ports:
    policy: PolicyPort
    claims: ClaimsPort


@dataclass(frozen=True)
class Outcome:
    value: str
    reason: str | None
    as_of: datetime
    binding: str


@dataclass(frozen=True)
class Operation:
    name: str
    call: Callable[[Ports], Outcome]
    unevaluated: str
    label: str


@dataclass(frozen=True)
class Misbehaviour:
    name: str
    arm: Callable[[SourceControls], None]
    budget: float
    reason: str | None


def outcome(answer: SearchAnswer | TermHistoryAnswer | ExistingClaimsAnswer) -> Outcome:
    if isinstance(answer, TermHistoryAnswer):
        history = answer.history
        return Outcome(history.value, history.reason, answer.as_of, answer.binding)
    return Outcome(answer.value, answer.reason, answer.as_of, answer.binding)


OPERATIONS = [
    Operation("search", lambda p: outcome(p.policy.search(BY_NUMBER)), NOT_EVALUATED, POLICY_LABEL),
    Operation(
        "term_history",
        lambda p: outcome(p.policy.term_history(REFERENCE)),
        NOT_OBTAINED,
        POLICY_LABEL,
    ),
    Operation(
        "existing_claims",
        lambda p: outcome(p.claims.existing_claims(REFERENCE)),
        NOT_OBTAINED,
        CLAIMS_LABEL,
    ),
]
MISBEHAVIOURS = [
    Misbehaviour("answers", lambda source: None, 1.0, None),
    Misbehaviour("raises", lambda source: source.raise_on_next_call(), 1.0, SOURCE_UNAVAILABLE),
    Misbehaviour(
        "answers malformed",
        lambda source: source.answer_malformed_on_next_call(),
        1.0,
        SOURCE_MALFORMED,
    ),
    Misbehaviour(
        "sleeps past the budget",
        lambda source: source.sleep_on_next_call(SLEEP),
        BUDGET,
        SOURCE_TIMEOUT,
    ),
]
HORIZONS = [None, date(2019, 1, 1)]


def build(
    harness: PortHarness, *, budget: float = 1.0, horizon: date | None = None
) -> Ports:
    policy = PolicyBinding(
        binding=POLICY_LABEL,
        timeout_seconds=budget,
        history_horizon=horizon,
        clock=fixed_clock,
        parameters={},
    )
    claims = ClaimsBinding(
        binding=CLAIMS_LABEL, timeout_seconds=budget, clock=fixed_clock, parameters={}
    )
    return Ports(policy=harness.policy_port(policy), claims=harness.claims_port(claims))


@pytest.fixture(params=HARNESSES, ids=lambda builder: builder.__name__)
def harness(request: pytest.FixtureRequest) -> PortHarness:
    built: PortHarness = request.param()
    return built


@pytest.fixture
def held(harness: PortHarness) -> PortHarness:
    """The harness holding one policy and no claims, so an answered call has
    something to answer with on every operation."""
    harness.source.hold_policy(REFERENCE, NUMBER, INSUREDS, ADDRESS, [TERM])
    return harness


operation = pytest.mark.parametrize("operation", OPERATIONS, ids=lambda o: o.name)
misbehaviour = pytest.mark.parametrize("misbehaviour", MISBEHAVIOURS, ids=lambda m: m.name)


# -- every operation, every fault -------------------------------------------------


@operation
def test_a_raising_source_answers_the_not_evaluated_value_with_source_unavailable(
    held: PortHarness, operation: Operation
) -> None:
    held.source.raise_on_next_call()
    result = operation.call(build(held))
    assert (result.value, result.reason) == (operation.unevaluated, SOURCE_UNAVAILABLE)


@operation
def test_a_source_past_its_budget_answers_source_timeout_within_a_bounded_time(
    held: PortHarness, operation: Operation
) -> None:
    held.source.sleep_on_next_call(SLEEP)
    ports = build(held, budget=BUDGET)
    started = time.perf_counter()
    result = operation.call(ports)
    elapsed = time.perf_counter() - started
    assert (result.value, result.reason) == (operation.unevaluated, SOURCE_TIMEOUT)
    assert elapsed < BOUNDED_BY, f"{operation.name} took {elapsed:.3f}s against a {BUDGET}s budget"


@operation
def test_a_malformed_source_answer_is_source_malformed(
    held: PortHarness, operation: Operation
) -> None:
    held.source.answer_malformed_on_next_call()
    result = operation.call(build(held))
    assert (result.value, result.reason) == (operation.unevaluated, SOURCE_MALFORMED)


@operation
@misbehaviour
def test_as_of_is_the_injected_clocks_instant_on_every_answer(
    held: PortHarness, operation: Operation, misbehaviour: Misbehaviour
) -> None:
    misbehaviour.arm(held.source)
    result = operation.call(build(held, budget=misbehaviour.budget))
    assert result.reason == misbehaviour.reason
    assert result.as_of == INSTANT


@operation
@misbehaviour
def test_binding_names_the_binding_that_produced_every_answer(
    held: PortHarness, operation: Operation, misbehaviour: Misbehaviour
) -> None:
    misbehaviour.arm(held.source)
    result = operation.call(build(held, budget=misbehaviour.budget))
    assert result.reason == misbehaviour.reason
    assert result.binding == operation.label


def test_a_source_raising_its_own_timeout_is_source_timeout(held: PortHarness) -> None:
    held.source.raise_on_next_call(TimeoutError("upstream gave up"))
    answer = build(held).policy.search(BY_NUMBER)
    assert (answer.value, answer.reason) == (NOT_EVALUATED, SOURCE_TIMEOUT)


# -- policy port -------------------------------------------------------------------


@misbehaviour
@pytest.mark.parametrize("horizon", HORIZONS, ids=["complete", "from a date"])
def test_every_term_history_carries_the_configured_horizon(
    held: PortHarness, misbehaviour: Misbehaviour, horizon: date | None
) -> None:
    misbehaviour.arm(held.source)
    answer = build(held, budget=misbehaviour.budget, horizon=horizon).policy.term_history(
        REFERENCE
    )
    assert answer.history.reason == misbehaviour.reason
    assert answer.history.history_from == horizon


def test_zero_candidates_is_not_found_with_no_reason(harness: PortHarness) -> None:
    answer = build(harness).policy.search(BY_NUMBER)
    assert answer == SearchAnswer(
        value=NOT_FOUND, candidates=(), reason=None, as_of=INSTANT, binding=POLICY_LABEL
    )


def test_one_candidate_is_found_with_its_reference_number_insureds_and_basis(
    held: PortHarness,
) -> None:
    answer = build(held).policy.search(BY_NUMBER)
    assert answer.value == FOUND
    assert answer.candidates == (PolicyCandidate(REFERENCE, NUMBER, INSUREDS, POLICY_NUMBER),)


def test_several_candidates_are_all_returned(held: PortHarness) -> None:
    held.source.hold_policy("src-ref-000002", "HO-7654321", ("Ruth Alvarez",), ADDRESS, [TERM])
    shared = SearchIdentifiers(insured_name="Ruth Alvarez", risk_postal_code="34102")
    answer = build(held).policy.search(shared)
    assert answer.value == FOUND
    assert {c.policy_reference for c in answer.candidates} == {REFERENCE, "src-ref-000002"}
    assert {c.match_basis for c in answer.candidates} == {INSURED_NAME_AND_POSTAL_CODE}


def test_a_mistyped_number_beside_a_correct_name_and_postal_code_matches_on_the_name(
    held: PortHarness,
) -> None:
    mistyped = SearchIdentifiers(
        policy_number="HO-1234576", insured_name="Dana Alvarez", risk_postal_code="34102"
    )
    answer = build(held).policy.search(mistyped)
    assert answer.value == FOUND
    assert [c.match_basis for c in answer.candidates] == [INSURED_NAME_AND_POSTAL_CODE]


def test_a_source_without_name_search_answers_identifiers_insufficient_for_a_name_search(
    held: PortHarness,
) -> None:
    held.source.without_name_search()
    ports = build(held)
    by_name = ports.policy.search(BY_NAME)
    assert (by_name.value, by_name.reason) == (NOT_EVALUATED, IDENTIFIERS_INSUFFICIENT)
    assert ports.policy.search(BY_NUMBER).value == FOUND


def test_an_obtained_history_carries_terms_status_changes_and_prior_coverage(
    harness: PortHarness,
) -> None:
    first = term(date(2024, 10, 1), date(2025, 10, 1))
    second = term(
        date(2025, 10, 1),
        date(2026, 10, 1),
        [("cancellation", date(2026, 1, 15)), ("reinstatement", date(2026, 1, 15))],
    )
    harness.source.hold_policy(
        REFERENCE, NUMBER, INSUREDS, ADDRESS, [first, second],
        prior_coverage=(date(2021, 10, 1), date(2024, 10, 1)),
    )
    answer = build(harness, horizon=date(2019, 1, 1)).policy.term_history(REFERENCE)
    assert answer.history == TermHistory(
        value=OBTAINED,
        terms=(
            PolicyTerm(date(2024, 10, 1), date(2025, 10, 1)),
            PolicyTerm(
                date(2025, 10, 1),
                date(2026, 10, 1),
                (
                    TermStatusChange(CANCELLATION, date(2026, 1, 15)),
                    TermStatusChange(REINSTATEMENT, date(2026, 1, 15)),
                ),
            ),
        ),
        history_from=date(2019, 1, 1),
        prior_coverage=PriorCoverage(date(2021, 10, 1), date(2024, 10, 1)),
    )


def test_a_reference_the_source_does_not_know_is_the_sources_failure(held: PortHarness) -> None:
    answer = build(held).policy.term_history("src-ref-unknown")
    assert (answer.history.value, answer.history.reason) == (NOT_OBTAINED, SOURCE_UNAVAILABLE)


# -- claims port -------------------------------------------------------------------


def test_no_claims_on_the_policy_is_obtained_with_none(held: PortHarness) -> None:
    answer = build(held).claims.existing_claims(REFERENCE)
    assert answer == ExistingClaimsAnswer(
        value=OBTAINED, claims=(), reason=None, as_of=INSTANT, binding=CLAIMS_LABEL
    )


def test_several_claims_arrive_as_existing_claim_records(held: PortHarness) -> None:
    held.source.hold_claim(REFERENCE, claim("CLM-1", NUMBER, date(2026, 3, 2), "wind_hail"))
    held.source.hold_claim(REFERENCE, claim("CLM-2", NUMBER, date(2026, 5, 9), "water"))
    answer = build(held).claims.existing_claims(REFERENCE)
    assert answer.value == OBTAINED
    assert answer.claims == (
        ExistingClaim("CLM-1", NUMBER, date(2026, 3, 2), "wind_hail"),
        ExistingClaim("CLM-2", NUMBER, date(2026, 5, 9), "water"),
    )
