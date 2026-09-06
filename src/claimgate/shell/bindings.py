"""Per-carrier port bindings: which implementation of each port serves a
carrier, under what budget, resolved by lookup.

The third per-carrier mapping beside identity and rules (PHASE3_DESIGN.md,
"Configuration"), keyed by carrier_code, one entry per port:

    {"AAAA": {"policy": {"implementation": "live-query", "timeout_seconds": 2.0,
                         "history_horizon": "complete"},
              "claims": {"implementation": "live-query", "timeout_seconds": 2.0}}}

**A lookup, not a branch** (rules.py, "Two lookups, one shape"). The carrier
code selects an entry; the entry's implementation name selects a constructor
from a registry the deployment supplies; the constructor is handed the entry's
resolved parameters and nothing else. Nothing here reads the carrier code to
choose behaviour - it appears in the binding label only, so an answer can say
which configured binding produced it - and a fictional carrier whose entry
copies another's resolves to the same implementation under the same budget
(tests/shell/test_bindings.py). Where the mapping comes from is not this
module's concern, exactly as for the rules source.

**No default for anything.** An unknown carrier, a missing port entry, an
implementation name the registry does not hold, a missing or non-positive
timeout, a policy binding without a history horizon: each raises
DeploymentFaultError(PORT_BINDING_UNRESOLVABLE) - item 5i's pattern, our own
configuration's defect and never a 4xx (faults.py). Nothing on either endpoint
path resolves a binding until item 7f.

**The history horizon is required on the policy binding**: an ISO date or the
literal `complete`, carried by the implementation into every
TermHistory.history_from (None for complete). ASSUMPTIONS.md's
continuous-coverage decisions (2026-09-04) record that a port omitting its
horizon makes every derivation conclusive silently; requiring it here is how
that is made impossible rather than discouraged.

Keys beyond the three named above are the implementation's own parameters (an
extract's file set, item 7i) and pass through untouched. The clock is whatever
the deployment configured, passed in by the caller: nothing here reads one.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any, Final

from claimgate.shell.faults import PORT_BINDING_UNRESOLVABLE, DeploymentFaultError
from claimgate.shell.ports import ClaimsPort, Clock, PolicyPort

COMPLETE_HISTORY: Final = "complete"
_BINDING_KEYS: Final = frozenset({"implementation", "timeout_seconds", "history_horizon"})

BindingsSource = Mapping[str, Mapping[str, Mapping[str, Any]]]


@dataclass(frozen=True)
class PolicyBinding:
    """What a policy port implementation is constructed from. `binding` is the
    label every answer carries; `history_horizon` None asserts a complete
    history, and only because the entry said `complete` in so many words."""

    binding: str
    timeout_seconds: float
    history_horizon: date | None
    clock: Clock
    parameters: Mapping[str, Any]


@dataclass(frozen=True)
class ClaimsBinding:
    binding: str
    timeout_seconds: float
    clock: Clock
    parameters: Mapping[str, Any]


PolicyPortFactory = Callable[[PolicyBinding], PolicyPort]
ClaimsPortFactory = Callable[[ClaimsBinding], ClaimsPort]


@dataclass(frozen=True)
class ImplementationRegistry:
    """Implementation name to constructor, one mapping per port. The deployment
    builds it; a test builds one holding whatever it is exercising."""

    policy: Mapping[str, PolicyPortFactory]
    claims: Mapping[str, ClaimsPortFactory]


@dataclass(frozen=True)
class PortBindings:
    policy: PolicyPort
    claims: ClaimsPort


def resolve_port_bindings(
    carrier_code: str, source: BindingsSource, registry: ImplementationRegistry, clock: Clock
) -> PortBindings:
    return PortBindings(
        policy=resolve_policy_port(carrier_code, source, registry, clock),
        claims=resolve_claims_port(carrier_code, source, registry, clock),
    )


def resolve_policy_port(
    carrier_code: str, source: BindingsSource, registry: ImplementationRegistry, clock: Clock
) -> PolicyPort:
    entry = _port_entry(carrier_code, source, "policy")
    construct = _factory(registry.policy, entry)
    return construct(
        PolicyBinding(
            binding=_label(carrier_code, "policy", entry),
            timeout_seconds=_timeout(entry),
            history_horizon=_horizon(entry),
            clock=clock,
            parameters=_parameters(entry),
        )
    )


def resolve_claims_port(
    carrier_code: str, source: BindingsSource, registry: ImplementationRegistry, clock: Clock
) -> ClaimsPort:
    entry = _port_entry(carrier_code, source, "claims")
    construct = _factory(registry.claims, entry)
    return construct(
        ClaimsBinding(
            binding=_label(carrier_code, "claims", entry),
            timeout_seconds=_timeout(entry),
            clock=clock,
            parameters=_parameters(entry),
        )
    )


def _port_entry(carrier_code: str, source: BindingsSource, port: str) -> Mapping[str, Any]:
    carrier = source.get(carrier_code)
    entry = None if carrier is None else carrier.get(port)
    if not isinstance(entry, Mapping):
        raise DeploymentFaultError(PORT_BINDING_UNRESOLVABLE)
    return entry


def _factory[Factory: (PolicyPortFactory, ClaimsPortFactory)](
    implementations: Mapping[str, Factory], entry: Mapping[str, Any]
) -> Factory:
    name = entry.get("implementation")
    if not isinstance(name, str) or name not in implementations:
        raise DeploymentFaultError(PORT_BINDING_UNRESOLVABLE)
    return implementations[name]


def _timeout(entry: Mapping[str, Any]) -> float:
    # bool is a subclass of int and is excluded, as carrier_configuration.py
    # excludes it from day counts; zero is no budget at all, not a small one.
    value = entry.get("timeout_seconds")
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        raise DeploymentFaultError(PORT_BINDING_UNRESOLVABLE)
    return float(value)


def _horizon(entry: Mapping[str, Any]) -> date | None:
    value = entry.get("history_horizon")
    if value == COMPLETE_HISTORY:
        return None
    if not isinstance(value, str):
        raise DeploymentFaultError(PORT_BINDING_UNRESOLVABLE)
    try:
        return date.fromisoformat(value)
    except ValueError as malformed:
        raise DeploymentFaultError(PORT_BINDING_UNRESOLVABLE) from malformed


def _parameters(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    return {key: value for key, value in entry.items() if key not in _BINDING_KEYS}


def _label(carrier_code: str, port: str, entry: Mapping[str, Any]) -> str:
    # The configured binding by name - carrier, port, implementation - so a
    # stored answer still says what answered after a deployment swaps one.
    return f"{carrier_code}/{port}:{entry['implementation']}"
