"""The bindings resolver: a lookup by carrier code and implementation name,
with no default for anything and a typed deployment fault for every gap.

The stub ports below record the binding they were constructed from and do
nothing else, because the resolver's subject is selection and parameter
passing, not answering. One test at the end runs the live-query shape through
the same registry so the label a real answer carries is tied to what the
resolver composed.
"""

from datetime import UTC, date, datetime
from functools import partial
from typing import Any

import pytest

from claimgate.domain.policy_identification import SearchIdentifiers
from claimgate.shell.bindings import (
    ClaimsBinding,
    ImplementationRegistry,
    PolicyBinding,
    resolve_claims_port,
    resolve_policy_port,
    resolve_port_bindings,
)
from claimgate.shell.faults import PORT_BINDING_UNRESOLVABLE, DeploymentFaultError
from claimgate.shell.live_query_ports import LIVE_QUERY, LiveQueryClaimsPort, LiveQueryPolicyPort
from claimgate.shell.ports import NOT_FOUND, ExistingClaimsAnswer, SearchAnswer, TermHistoryAnswer
from tests.fixtures.core_system import InProcessCoreSystem

INSTANT = datetime(2026, 9, 6, 15, 0, tzinfo=UTC)


def fixed_clock() -> datetime:
    return INSTANT


class RecordingPolicyPort:
    def __init__(self, binding: PolicyBinding) -> None:
        self.binding = binding

    def search(self, identifiers: SearchIdentifiers) -> SearchAnswer:
        raise NotImplementedError

    def term_history(self, policy_reference: str) -> TermHistoryAnswer:
        raise NotImplementedError


class OtherPolicyPort(RecordingPolicyPort):
    pass


class RecordingClaimsPort:
    def __init__(self, binding: ClaimsBinding) -> None:
        self.binding = binding

    def existing_claims(self, policy_reference: str) -> ExistingClaimsAnswer:
        raise NotImplementedError


class OtherClaimsPort(RecordingClaimsPort):
    pass


REGISTRY = ImplementationRegistry(
    policy={"recording": RecordingPolicyPort, "other": OtherPolicyPort},
    claims={"recording": RecordingClaimsPort, "other": OtherClaimsPort},
)
POLICY_ENTRY: dict[str, Any] = {
    "implementation": "recording",
    "timeout_seconds": 2.0,
    "history_horizon": "complete",
}
CLAIMS_ENTRY: dict[str, Any] = {"implementation": "recording", "timeout_seconds": 1.5}
SOURCE = {"AAAA": {"policy": POLICY_ENTRY, "claims": CLAIMS_ENTRY}}


def unresolvable(entry: dict[str, Any], **changes: Any) -> dict[str, Any]:
    changed = {**entry, **changes}
    return {key: value for key, value in changed.items() if value is not ...}


def test_a_carrier_resolves_its_policy_and_claims_bindings_as_configured() -> None:
    bindings = resolve_port_bindings("AAAA", SOURCE, REGISTRY, fixed_clock)
    assert isinstance(bindings.policy, RecordingPolicyPort)
    assert isinstance(bindings.claims, RecordingClaimsPort)
    assert bindings.policy.binding == PolicyBinding(
        binding="AAAA/policy:recording",
        timeout_seconds=2.0,
        history_horizon=None,
        clock=fixed_clock,
        parameters={},
    )
    assert bindings.claims.binding == ClaimsBinding(
        binding="AAAA/claims:recording", timeout_seconds=1.5, clock=fixed_clock, parameters={}
    )


def test_a_date_horizon_resolves_to_that_date() -> None:
    source = {"AAAA": {"policy": {**POLICY_ENTRY, "history_horizon": "2019-01-01"}}}
    port = resolve_policy_port("AAAA", source, REGISTRY, fixed_clock)
    assert isinstance(port, RecordingPolicyPort)
    assert port.binding.history_horizon == date(2019, 1, 1)


def test_keys_beyond_the_bindings_own_pass_through_as_the_implementations_parameters() -> None:
    source = {"AAAA": {"claims": {**CLAIMS_ENTRY, "extract_path": "/var/extracts/claims"}}}
    port = resolve_claims_port("AAAA", source, REGISTRY, fixed_clock)
    assert isinstance(port, RecordingClaimsPort)
    assert port.binding.parameters == {"extract_path": "/var/extracts/claims"}


# Each change to the policy entry that leaves it unresolvable; ... removes the key.
GAPS: list[tuple[str, dict[str, Any]]] = [
    ("unknown implementation", {"implementation": "mainframe"}),
    ("implementation not a name", {"implementation": 7}),
    ("missing implementation", {"implementation": ...}),
    ("missing timeout", {"timeout_seconds": ...}),
    ("zero timeout", {"timeout_seconds": 0}),
    ("negative timeout", {"timeout_seconds": -1.0}),
    ("boolean timeout", {"timeout_seconds": True}),
    ("textual timeout", {"timeout_seconds": "2"}),
    ("missing history horizon", {"history_horizon": ...}),
    ("horizon not a date", {"history_horizon": "yesterday"}),
    ("horizon not text", {"history_horizon": 2019}),
]


def with_policy(entry: dict[str, Any]) -> dict[str, Any]:
    return {"AAAA": {"policy": entry, "claims": CLAIMS_ENTRY}}


@pytest.mark.parametrize(
    "source",
    [
        pytest.param({}, id="unknown carrier"),
        pytest.param({"AAAA": {"claims": CLAIMS_ENTRY}}, id="missing policy entry"),
        pytest.param({"AAAA": {"policy": POLICY_ENTRY}}, id="missing claims entry"),
        pytest.param(
            {"AAAA": {"policy": "live", "claims": CLAIMS_ENTRY}}, id="entry not a mapping"
        ),
        *(
            pytest.param(with_policy(unresolvable(POLICY_ENTRY, **change)), id=label)
            for label, change in GAPS
        ),
        pytest.param(
            {
                "AAAA": {
                    "policy": POLICY_ENTRY,
                    "claims": unresolvable(CLAIMS_ENTRY, timeout_seconds=...),
                }
            },
            id="claims missing timeout",
        ),
    ],
)
def test_every_gap_in_a_binding_is_the_one_deployment_fault(source: dict[str, Any]) -> None:
    with pytest.raises(DeploymentFaultError) as raised:
        resolve_port_bindings("AAAA", source, REGISTRY, fixed_clock)
    assert raised.value.code == PORT_BINDING_UNRESOLVABLE


def test_policy_and_claims_bindings_resolve_independently() -> None:
    policy_only = {"AAAA": {"policy": POLICY_ENTRY}}
    claims_only = {"AAAA": {"claims": CLAIMS_ENTRY}}
    policy = resolve_policy_port("AAAA", policy_only, REGISTRY, fixed_clock)
    claims = resolve_claims_port("AAAA", claims_only, REGISTRY, fixed_clock)
    assert isinstance(policy, RecordingPolicyPort)
    assert isinstance(claims, RecordingClaimsPort)
    with pytest.raises(DeploymentFaultError):
        resolve_claims_port("AAAA", policy_only, REGISTRY, fixed_clock)
    with pytest.raises(DeploymentFaultError):
        resolve_policy_port("AAAA", claims_only, REGISTRY, fixed_clock)


def budgets(policy: object, claims: object) -> tuple[float, float]:
    assert isinstance(policy, RecordingPolicyPort)
    assert isinstance(claims, RecordingClaimsPort)
    return policy.binding.timeout_seconds, claims.binding.timeout_seconds


def test_two_carriers_with_different_bindings_resolve_to_different_ports_and_budgets() -> None:
    source = {
        **SOURCE,
        "BBBB": {
            "policy": {**POLICY_ENTRY, "implementation": "other", "timeout_seconds": 0.25},
            "claims": {**CLAIMS_ENTRY, "implementation": "other", "timeout_seconds": 0.75},
        },
    }
    first = resolve_port_bindings("AAAA", source, REGISTRY, fixed_clock)
    second = resolve_port_bindings("BBBB", source, REGISTRY, fixed_clock)
    assert (type(first.policy), type(first.claims)) == (RecordingPolicyPort, RecordingClaimsPort)
    assert (type(second.policy), type(second.claims)) == (OtherPolicyPort, OtherClaimsPort)
    assert budgets(first.policy, first.claims) == (2.0, 1.5)
    assert budgets(second.policy, second.claims) == (0.25, 0.75)


def test_the_carrier_code_selects_an_entry_and_decides_nothing_else() -> None:
    """A fictional carrier whose entry copies AAAA's resolves to the same
    implementations under the same budgets and horizon: the code is a lookup
    key, and the only place it surfaces is the label naming the entry."""
    source = {**SOURCE, "ZZZZ": {"policy": dict(POLICY_ENTRY), "claims": dict(CLAIMS_ENTRY)}}
    real = resolve_port_bindings("AAAA", source, REGISTRY, fixed_clock)
    fictional = resolve_port_bindings("ZZZZ", source, REGISTRY, fixed_clock)
    assert isinstance(real.policy, RecordingPolicyPort)
    assert isinstance(fictional.policy, RecordingPolicyPort)
    assert isinstance(real.claims, RecordingClaimsPort)
    assert isinstance(fictional.claims, RecordingClaimsPort)
    assert type(fictional.policy) is type(real.policy)
    assert type(fictional.claims) is type(real.claims)
    assert fictional.policy.binding == PolicyBinding(
        binding="ZZZZ/policy:recording",
        timeout_seconds=real.policy.binding.timeout_seconds,
        history_horizon=real.policy.binding.history_horizon,
        clock=real.policy.binding.clock,
        parameters=real.policy.binding.parameters,
    )
    assert fictional.claims.binding == ClaimsBinding(
        binding="ZZZZ/claims:recording",
        timeout_seconds=real.claims.binding.timeout_seconds,
        clock=real.claims.binding.clock,
        parameters=real.claims.binding.parameters,
    )


def test_the_live_query_shape_resolves_through_the_registry_and_answers_under_its_label() -> None:
    system = InProcessCoreSystem()
    registry = ImplementationRegistry(
        policy={LIVE_QUERY: partial(LiveQueryPolicyPort, system)},
        claims={LIVE_QUERY: partial(LiveQueryClaimsPort, system)},
    )
    source = {
        "AAAA": {
            "policy": {**POLICY_ENTRY, "implementation": LIVE_QUERY},
            "claims": {**CLAIMS_ENTRY, "implementation": LIVE_QUERY},
        }
    }
    bindings = resolve_port_bindings("AAAA", source, registry, fixed_clock)
    answer = bindings.policy.search(SearchIdentifiers(policy_number="HO-0000000"))
    assert answer == SearchAnswer(
        value=NOT_FOUND, as_of=INSTANT, binding=f"AAAA/policy:{LIVE_QUERY}"
    )
