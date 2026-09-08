"""Thin, stable test API over the policy match at intake.

What a scenario needs that no other API carries: a core system for its carrier
to be bound to - tests.fixtures.core_system, in process, one per carrier code -
the bindings and the registry submit_notice takes to reach it through the
live-query policy port, the ways that source can hold a policy or misbehave,
and the verification the notice shows afterward on GET /notices/{id}.

The budget is small and the sleep that exceeds it larger, as the contract suite
has them, so "does not answer within its budget" is a real timeout and not a
simulated one; the fixture answers in microseconds, so the budget is not close
for any other scenario. A fault holds for the rest of the scenario: five locked
specs declare an unavailable source in their Backgrounds and submit more than
once, and a fault that cleared after one call would let a second submission
search an empty source and pend on POLICY_NOT_MATCHED where the spec expects
TRIAGED.

The bindings entry names its source through a parameter of its own, `source`,
the way a real live-query binding names its endpoint: keys a binding does not
recognise pass through to the implementation (bindings.py), and this registry's
live-query factory reads that one to pick the carrier's system.
"""

from collections.abc import Callable, Sequence
from datetime import date
from typing import Any

from claimgate.shell.bindings import BindingsSource, ImplementationRegistry, PolicyBinding
from claimgate.shell.coverage_verifications import CoverageVerificationView
from claimgate.shell.live_query_ports import LIVE_QUERY, LiveQueryPolicyPort
from claimgate.shell.ports import PolicyPort
from tests.fixtures.core_system import FixtureAddress, InProcessCoreSystem, term

TIMEOUT_SECONDS = 0.2
UNANSWERED_FOR_SECONDS = 1.0
_SOURCE = "source"
# The address a held policy sits at, beyond the postal code the search reads.
# Fabricated (ASSUMPTIONS.md, "Synthetic data").
_RISK_LINE = "4140 Bayshore Loop"
_RISK_CITY = "North Port"
_RISK_STATE = "FL"


def _unavailable(system: InProcessCoreSystem) -> None:
    system.raise_on_every_call()


def _unanswering(system: InProcessCoreSystem) -> None:
    system.sleep_on_every_call(UNANSWERED_FOR_SECONDS)


def _malformed(system: InProcessCoreSystem) -> None:
    system.answer_malformed_on_every_call()


# The three faults as features/policy_match.feature and the five locked
# Backgrounds state them, in the spec's words.
FAULTS: dict[str, Callable[[InProcessCoreSystem], None]] = {
    "is unavailable": _unavailable,
    "does not answer within its budget": _unanswering,
    "answers in a shape that is not its own": _malformed,
}


class PolicySources:
    """The core systems a scenario's carriers are bound to, by carrier code,
    and the policy most recently held on any of them - "that policy" in the
    spec's later steps."""

    def __init__(self) -> None:
        self._systems: dict[str, InProcessCoreSystem] = {}
        self._held: dict[tuple[str, str], dict[str, Any]] = {}
        self._last: tuple[str, str] | None = None

    def system(self, carrier: str) -> InProcessCoreSystem:
        return self._systems.setdefault(carrier, InProcessCoreSystem())

    def hold_policy(
        self, carrier: str, reference: str, number: str, insured: str, postal_code: str
    ) -> None:
        """A policy with no terms yet; the term steps supply them."""
        self._held[(carrier, reference)] = {
            "number": number, "insured": insured, "postal_code": postal_code, "terms": [],
        }
        self._last = (carrier, reference)
        self._rehold(carrier, reference)

    def add_term(self, effective: date, expiration: date) -> None:
        carrier, reference = self._that_policy()
        self._held[(carrier, reference)]["terms"].append(term(effective, expiration))
        self._rehold(carrier, reference)

    def set_only_term(self, effective: date, expiration: date) -> None:
        carrier, reference = self._that_policy()
        self._held[(carrier, reference)]["terms"] = [term(effective, expiration)]
        self._rehold(carrier, reference)

    def fault(self, carrier: str, phrase: str) -> None:
        if phrase not in FAULTS:
            raise ValueError(f"unrecognized policy source fault: {phrase!r}")
        FAULTS[phrase](self.system(carrier))

    def bindings_source(self, *, unresolvable_for: str | None = None) -> BindingsSource:
        """One live-query policy entry per system stood up so far, under the
        budget above and a complete history. The carrier named unresolvable has
        no entry at all - a carrier this deployment administers but has not
        bound, which is the deployment fault and not a source fault."""
        return {
            carrier: {"policy": policy_entry(carrier)}
            for carrier in self._systems
            if carrier != unresolvable_for
        }

    def registry(self) -> ImplementationRegistry:
        return ImplementationRegistry(policy={LIVE_QUERY: self._live_query_port}, claims={})

    def _live_query_port(self, binding: PolicyBinding) -> PolicyPort:
        return LiveQueryPolicyPort(self.system(binding.parameters[_SOURCE]), binding)

    def _that_policy(self) -> tuple[str, str]:
        if self._last is None:
            raise ValueError("no policy has been held yet")
        return self._last

    def _rehold(self, carrier: str, reference: str) -> None:
        held = self._held[(carrier, reference)]
        self.system(carrier).hold_policy(
            reference, held["number"], [held["insured"]],
            FixtureAddress(_RISK_LINE, _RISK_CITY, _RISK_STATE, held["postal_code"]),
            held["terms"],
        )


def policy_entry(carrier: str, *, timeout_seconds: float = TIMEOUT_SECONDS) -> dict[str, Any]:
    return {
        "implementation": LIVE_QUERY,
        "timeout_seconds": timeout_seconds,
        "history_horizon": "complete",
        _SOURCE: carrier,
    }


def bound_sources(carriers: Sequence[str]) -> PolicySources:
    """Sources for the named carriers, each stood up empty and available: what
    a test that wants a real search starts from."""
    sources = PolicySources()
    for carrier in carriers:
        sources.system(carrier)
    return sources


__all__ = [
    "FAULTS",
    "CoverageVerificationView",
    "PolicySources",
    "bound_sources",
    "policy_entry",
]
