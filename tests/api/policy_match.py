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

Since item 7h every carrier stood up here is bound on both ports to its one
system (ASSUMPTIONS.md, 7h decisions 5 and 11): the claims entry sits beside
the policy entry under the same budget and the same source parameter, so the
"policy source" steps a locked Background states govern the claims side too,
and a carrier the deployment has not bound is unresolvable on both.

Item 7i adds the extract shape and the configuration the directory runs under
(ASSUMPTIONS.md, 7i decisions 2 and 4). CLAIMGATE_PORT_CONFIGURATION, read
once here and by no shell module, names the shape each port's entry selects -
`live/live` unless set, `extract/extract`, or `live/extract` for a live policy
port beside an extract claims port. The registry holds every shape regardless,
so the entry alone selects, exactly as a deployment's bindings file does. An
extract is generated into the scenario's temporary directory from the
carrier's held state when its binding is resolved - at submission, and again
at resolution - at the source's instant where "answers as of" set one and the
call's instant otherwise; a live source that is behind excludes the same
policies and, through its binding's clock, stamps the same instant.
"""

import os
import shutil
import tempfile
import weakref
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

from claimgate.shell.bindings import (
    BindingsSource,
    ClaimsBinding,
    ImplementationRegistry,
    PolicyBinding,
)
from claimgate.shell.coverage_verifications import CoverageVerificationView
from claimgate.shell.duplicate_evaluations import DuplicateEvaluationView
from claimgate.shell.extract_ports import EXTRACT, ExtractClaimsPort, ExtractPolicyPort
from claimgate.shell.extract_source import ExtractFileSet
from claimgate.shell.live_query_ports import LIVE_QUERY, LiveQueryClaimsPort, LiveQueryPolicyPort
from claimgate.shell.notice_intake import get_notice
from claimgate.shell.ports import ClaimsPort, Clock, PolicyPort
from claimgate.shell.store import NoticeStore
from tests.fixtures.core_system import FixtureAddress, InProcessCoreSystem, claim, term
from tests.fixtures.extract import reader_for, write_extract

TIMEOUT_SECONDS = 0.2
UNANSWERED_FOR_SECONDS = 1.0
_SOURCE = "source"
CONFIGURATION_VARIABLE = "CLAIMGATE_PORT_CONFIGURATION"
_SHAPES = {"live": LIVE_QUERY, "extract": EXTRACT}


def _configured(port: int) -> str:
    configuration = os.environ.get(CONFIGURATION_VARIABLE, "live/live")
    shapes = configuration.split("/")
    if len(shapes) != 2 or any(shape not in _SHAPES for shape in shapes):
        raise ValueError(f"{CONFIGURATION_VARIABLE} must be <policy>/<claims>, each live or extract")
    return _SHAPES[shapes[port]]


POLICY_IMPLEMENTATION = _configured(0)
CLAIMS_IMPLEMENTATION = _configured(1)
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

    def __init__(self, extract_root: Path | None = None) -> None:
        self._systems: dict[str, InProcessCoreSystem] = {}
        self._held: dict[tuple[str, str], dict[str, Any]] = {}
        self._last: tuple[str, str] | None = None
        self._extract_root = extract_root

    def system(self, carrier: str) -> InProcessCoreSystem:
        return self._systems.setdefault(carrier, InProcessCoreSystem())

    def hold_policy(
        self, carrier: str, reference: str, number: str, insured: str, postal_code: str
    ) -> None:
        """A policy with no terms yet; the term steps supply them."""
        self._held[(carrier, reference)] = {
            "number": number, "insured": insured, "postal_code": postal_code, "terms": [],
            "bound_on": None,
        }
        self._last = (carrier, reference)
        self._rehold(carrier, reference)

    def set_bound_on(self, bound_on: date) -> None:
        """The day "that policy" was bound (item 7i): a source answering as of
        an earlier instant does not hold it."""
        carrier, reference = self._that_policy()
        self._held[(carrier, reference)]["bound_on"] = bound_on
        self._rehold(carrier, reference)

    def answer_as_of(self, carrier: str, instant: datetime) -> None:
        """The carrier's source answers as of this instant rather than the
        call's (item 7i), on both ports, whichever shape serves them."""
        self.system(carrier).answer_as_of(instant)

    def add_term(self, effective: date, expiration: date) -> None:
        carrier, reference = self._that_policy()
        self._held[(carrier, reference)]["terms"].append(term(effective, expiration))
        self._rehold(carrier, reference)

    def set_only_term(self, effective: date, expiration: date) -> None:
        carrier, reference = self._that_policy()
        self._held[(carrier, reference)]["terms"] = [term(effective, expiration)]
        self._rehold(carrier, reference)

    def hold_claim(
        self, carrier: str, reference: str, claim_id: str, loss_date: date, loss_type: str
    ) -> None:
        """A claim on a policy this API holds, carrying that policy's number -
        the claims side keys by reference and the domain rule compares numbers
        (7h decision 4). A reference nothing holds is the caller's error."""
        held = self._held.get((carrier, reference))
        if held is None:
            raise ValueError(f"no policy {reference!r} is held for {carrier!r}")
        self.system(carrier).hold_claim(
            reference, claim(claim_id, held["number"], loss_date, loss_type)
        )

    def claims_unavailable(self, carrier: str) -> None:
        """The claims side down, the policy side answering (7h decision 5)."""
        self.system(carrier).raise_on_every_claims_call()

    def search_by_number_only(self, carrier: str) -> None:
        """A source with no insured-name search: the port answers a
        name-and-postal-code notice IDENTIFIERS_INSUFFICIENT (item 7g)."""
        self.system(carrier).without_name_search()

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
            carrier: {"policy": policy_entry(carrier), "claims": claims_entry(carrier)}
            for carrier in self._systems
            if carrier != unresolvable_for
        }

    def registry(self) -> ImplementationRegistry:
        """Every shape on every port; the entry selects."""
        return ImplementationRegistry(
            policy={LIVE_QUERY: self._live_query_port, EXTRACT: self._extract_policy_port},
            claims={LIVE_QUERY: self._live_query_claims_port, EXTRACT: self._extract_claims_port},
        )

    def _live_query_port(self, binding: PolicyBinding) -> PolicyPort:
        system = self.system(binding.parameters[_SOURCE])
        return LiveQueryPolicyPort(system, _stamping(binding, system))

    def _live_query_claims_port(self, binding: ClaimsBinding) -> ClaimsPort:
        system = self.system(binding.parameters[_SOURCE])
        return LiveQueryClaimsPort(system, _stamping(binding, system))

    def _extract_policy_port(self, binding: PolicyBinding) -> PolicyPort:
        return ExtractPolicyPort(self._extract("policy", binding.parameters[_SOURCE], binding.clock), binding)

    def _extract_claims_port(self, binding: ClaimsBinding) -> ClaimsPort:
        return ExtractClaimsPort(self._extract("claims", binding.parameters[_SOURCE], binding.clock), binding)

    def _extract(self, port: str, carrier: str, clock: Clock) -> ExtractFileSet:
        """Generated now from the carrier's held state, at the source's instant
        or the call's (7i decision 4), one directory per carrier and port."""
        system = self.system(carrier)
        directory = self._root() / carrier / port
        write_extract(system, directory, system.as_of if system.as_of is not None else clock())
        return ExtractFileSet(directory, read_text=reader_for(system))

    def _root(self) -> Path:
        if self._extract_root is None:
            self._extract_root = Path(tempfile.mkdtemp(prefix="claimgate-extracts-"))
            weakref.finalize(self, shutil.rmtree, self._extract_root, True)
        return self._extract_root

    def _that_policy(self) -> tuple[str, str]:
        if self._last is None:
            raise ValueError("no policy has been held yet")
        return self._last

    def _rehold(self, carrier: str, reference: str) -> None:
        held = self._held[(carrier, reference)]
        self.system(carrier).hold_policy(
            reference, held["number"], [held["insured"]],
            FixtureAddress(_RISK_LINE, _RISK_CITY, _RISK_STATE, held["postal_code"]),
            held["terms"], bound_on=held["bound_on"],
        )


def _stamping[Binding: (PolicyBinding, ClaimsBinding)](
    binding: Binding, system: InProcessCoreSystem
) -> Binding:
    """The binding whose clock is the source's instant where one was set: a
    live source that is behind stamps the instant its answers reflect."""
    instant = system.as_of
    if instant is None:
        return binding
    return replace(binding, clock=lambda: instant)


def policy_entry(carrier: str, *, timeout_seconds: float = TIMEOUT_SECONDS) -> dict[str, Any]:
    return {
        "implementation": POLICY_IMPLEMENTATION,
        "timeout_seconds": timeout_seconds,
        "history_horizon": "complete",
        _SOURCE: carrier,
    }


def claims_entry(carrier: str, *, timeout_seconds: float = TIMEOUT_SECONDS) -> dict[str, Any]:
    return {
        "implementation": CLAIMS_IMPLEMENTATION, "timeout_seconds": timeout_seconds, _SOURCE: carrier,
    }


def duplicate_evaluation(store: NoticeStore, notice_id: str) -> DuplicateEvaluationView | None:
    """What the notice shows about duplicate detection on GET /notices/{id}:
    None where it has not been triaged, else the latest evaluation."""
    view = get_notice(store, notice_id)
    if view is None:
        raise ValueError(f"no notice {notice_id!r}")
    return view.duplicate_evaluation


def bound_sources(carriers: Sequence[str]) -> PolicySources:
    """Sources for the named carriers, each stood up empty and available: what
    a test that wants a real search starts from."""
    sources = PolicySources()
    for carrier in carriers:
        sources.system(carrier)
    return sources


__all__ = [
    "CONFIGURATION_VARIABLE",
    "FAULTS",
    "CoverageVerificationView",
    "DuplicateEvaluationView",
    "PolicySources",
    "bound_sources",
    "claims_entry",
    "duplicate_evaluation",
    "policy_entry",
]
