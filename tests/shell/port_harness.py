"""The harness a port implementation is contract-tested through, and the list
of implementations the contract suite runs over.

tests/shell/test_port_contracts.py parametrizes over HARNESSES and nothing in
it names a shape. A shape joins by appending a builder here - item 7i's extract
shape stands its file set up behind the same SourceControls - and every
contract then runs against it with no test edited.

A plain module rather than conftest.py for the reason tests/shell/support.py
gives: a class defined in a conftest has two identities.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from functools import partial
from typing import Any, Protocol

from claimgate.shell.bindings import ClaimsPortFactory, PolicyPortFactory
from claimgate.shell.live_query_ports import LIVE_QUERY, LiveQueryClaimsPort, LiveQueryPolicyPort
from tests.fixtures.core_system import FixtureAddress, InProcessCoreSystem


class SourceControls(Protocol):
    """What every harness lets a contract do to the source behind its ports:
    put records in, and make the next call misbehave in each of the ways a
    port has to answer for."""

    def hold_policy(
        self,
        reference: str,
        number: str,
        named_insureds: Sequence[str],
        address: FixtureAddress,
        terms: Sequence[dict[str, Any]],
        prior_coverage: tuple[date, date] | None = None,
    ) -> None: ...

    def hold_claim(self, reference: str, record: dict[str, Any]) -> None: ...

    def sleep_on_next_call(self, seconds: float) -> None: ...

    def raise_on_next_call(self, error: Exception | None = None) -> None: ...

    def answer_malformed_on_next_call(self) -> None: ...

    def without_name_search(self) -> None: ...


@dataclass(frozen=True)
class PortHarness:
    implementation: str
    source: SourceControls
    policy_port: PolicyPortFactory
    claims_port: ClaimsPortFactory


def live_query() -> PortHarness:
    system = InProcessCoreSystem()
    return PortHarness(
        implementation=LIVE_QUERY,
        source=system,
        policy_port=partial(LiveQueryPolicyPort, system),
        claims_port=partial(LiveQueryClaimsPort, system),
    )


HARNESSES = [live_query]
