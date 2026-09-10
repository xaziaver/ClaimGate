"""The harness a port implementation is contract-tested through, and the list
of implementations the contract suite runs over.

tests/shell/test_port_contracts.py parametrizes over HARNESSES and nothing in
it names a shape. A shape joins by appending a builder here - item 7i's extract
shape stands its file set up behind the same SourceControls - and every
contract then runs against it with no test edited.

Each harness carries the instant its answers reflect under the suite's clock
(ASSUMPTIONS.md, 7i decision 3): the clock's own instant for a live query, and
for an extract the instant it was generated at, one day before the clock, so
the suite's `as_of` assertions test that the shape stamps what it reflects
rather than that a fixture agreed with the clock.

A plain module rather than conftest.py for the reason tests/shell/support.py
gives: a class defined in a conftest has two identities.
"""

import shutil
import tempfile
import time
import weakref
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from functools import partial
from pathlib import Path
from typing import Any, Protocol

from claimgate.shell.bindings import ClaimsPortFactory, PolicyPortFactory
from claimgate.shell.extract_ports import EXTRACT, ExtractClaimsPort, ExtractPolicyPort
from claimgate.shell.extract_source import MANIFEST, ExtractFileSet, read_file
from claimgate.shell.live_query_ports import LIVE_QUERY, LiveQueryClaimsPort, LiveQueryPolicyPort
from tests.fixtures.core_system import FixtureAddress, InProcessCoreSystem
from tests.fixtures.extract import NOT_THE_SHAPE, write_extract

# The suite's injected clock: an instant in the past, so a stamp from any wall
# clock fails equality. The extract is generated a day before it.
INSTANT = datetime(2024, 2, 29, 23, 59, 59, tzinfo=UTC)
EXTRACT_INSTANT = INSTANT - timedelta(days=1)


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
    # The instant this shape's answers reflect under the suite's clock.
    instant: datetime


class ExtractControls:
    """SourceControls over a file set regenerated from the held state at
    EXTRACT_INSTANT on every hold. The one-shot misbehaviours land at the
    reader, on the next data read, where an extract's own faults land - a
    file that is slow, unreadable, or not its shape - and never on the
    manifest, so every answer carries the extract's instant."""

    def __init__(self) -> None:
        self._system = InProcessCoreSystem()
        self._directory = Path(tempfile.mkdtemp(prefix="claimgate-extract-"))
        weakref.finalize(self, shutil.rmtree, self._directory, True)
        self._next: tuple[str, Any] | None = None
        # An extract with nothing in it is still an extract: written now, so
        # a search over nothing held is NOT_FOUND as of it, not no extract.
        self._write()

    def hold_policy(
        self,
        reference: str,
        number: str,
        named_insureds: Sequence[str],
        address: FixtureAddress,
        terms: Sequence[dict[str, Any]],
        prior_coverage: tuple[date, date] | None = None,
    ) -> None:
        self._system.hold_policy(reference, number, named_insureds, address, terms, prior_coverage)
        self._write()

    def hold_claim(self, reference: str, record: dict[str, Any]) -> None:
        self._system.hold_claim(reference, record)
        self._write()

    def sleep_on_next_call(self, seconds: float) -> None:
        self._next = ("sleep", seconds)

    def raise_on_next_call(self, error: Exception | None = None) -> None:
        self._next = ("raise", error if error is not None else OSError("extract read failure"))

    def answer_malformed_on_next_call(self) -> None:
        self._next = ("malformed", None)

    def without_name_search(self) -> None:
        self._system.without_name_search()
        self._write()

    def file_set(self) -> ExtractFileSet:
        return ExtractFileSet(self._directory, read_text=self._read)

    def _write(self) -> None:
        write_extract(self._system, self._directory, EXTRACT_INSTANT)

    def _read(self, path: Path) -> str:
        if path.name == MANIFEST or self._next is None:
            return read_file(path)
        kind, argument = self._next
        self._next = None
        if kind == "sleep":
            time.sleep(argument)
        elif kind == "raise":
            raise argument
        else:
            return NOT_THE_SHAPE
        return read_file(path)


def live_query() -> PortHarness:
    system = InProcessCoreSystem()
    return PortHarness(
        implementation=LIVE_QUERY,
        source=system,
        policy_port=partial(LiveQueryPolicyPort, system),
        claims_port=partial(LiveQueryClaimsPort, system),
        instant=INSTANT,
    )


def extract() -> PortHarness:
    controls = ExtractControls()
    return PortHarness(
        implementation=EXTRACT,
        source=controls,
        policy_port=partial(ExtractPolicyPort, controls.file_set()),
        claims_port=partial(ExtractClaimsPort, controls.file_set()),
        instant=EXTRACT_INSTANT,
    )


HARNESSES = [live_query, extract]
