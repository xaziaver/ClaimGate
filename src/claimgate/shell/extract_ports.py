"""The extract shape of both ports: answers from a generated file set, and
every answer reflects the instant the file set was generated.

PHASE3_DESIGN.md, "Swappability proof": the second conforming shape per port.
It promises what the live-query pair promises - the not-evaluated value in
place of any failure, the binding's label on every answer, the binding's
horizon on every term history - with one difference, which is the point of
the shape: `as_of` is the manifest's generation instant, not the clock's,
so a stored verification says how old the answer it rests on is
(ports.py, "an extract stamps its generation instant").

**Two reads under one budget.** Every operation first reads and parses the
manifest, then reads the file the operation needs, each on a worker thread
through live_query_ports.py's `guarded`, the second under whatever the budget
has left. The manifest goes first so that a data file that is missing, slow
or not its shape still answers with the extract's instant - the reviewer
sees how old the extract that failed them was. An extract that cannot be
opened at all - no directory, no manifest, a manifest that is not its shape,
a manifest read that exhausts the budget - has no instant to answer with,
and that not-evaluated answer carries the call instant, the only one there
is. That is a judgment (ASSUMPTIONS.md, 7i), recorded rather than assumed.

The file set is a parameter of the constructor: the deployment's registry
builds one from the binding's own parameters (an extract's directory), the
way the live-query factory hands its port a source.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Final

from claimgate.domain.coverage import TermHistory
from claimgate.domain.policy_identification import SearchIdentifiers
from claimgate.shell.bindings import ClaimsBinding, PolicyBinding
from claimgate.shell.extract_source import ExtractFileSet, ExtractManifest, parse_manifest
from claimgate.shell.live_query_ports import guarded
from claimgate.shell.live_query_source import parse_candidates, parse_claims, parse_term_history
from claimgate.shell.ports import (
    FOUND,
    NOT_EVALUATED,
    NOT_FOUND,
    NOT_OBTAINED,
    OBTAINED,
    Clock,
    ExistingClaimsAnswer,
    SearchAnswer,
    TermHistoryAnswer,
)

# The implementation name a bindings entry uses to select this shape.
EXTRACT: Final = "extract"


@dataclass(frozen=True)
class _Read[Parsed]:
    # as_of is the manifest's instant once the manifest was read, else the
    # clock's; value and reason as live_query_ports.Guarded has them.
    as_of: datetime
    value: Parsed | None = None
    reason: str | None = None


def _read[Parsed](
    file_set: ExtractFileSet,
    budget_seconds: float,
    clock: Clock,
    select: Callable[[ExtractManifest], object],
    parse: Callable[[object], Parsed],
) -> _Read[Parsed]:
    started = perf_counter()
    opened = guarded(budget_seconds, file_set.manifest, parse_manifest)
    if opened.value is None:
        return _Read(as_of=clock(), reason=opened.reason)
    manifest = opened.value
    remaining = max(budget_seconds - (perf_counter() - started), 0.0)
    got = guarded(remaining, lambda: select(manifest), parse)
    return _Read(as_of=manifest.generated_at, value=got.value, reason=got.reason)


class ExtractPolicyPort:
    def __init__(self, file_set: ExtractFileSet, binding: PolicyBinding) -> None:
        self._file_set = file_set
        self._binding = binding

    def search(self, identifiers: SearchIdentifiers) -> SearchAnswer:
        read = _read(
            self._file_set,
            self._binding.timeout_seconds,
            self._binding.clock,
            lambda manifest: self._file_set.candidates(manifest, identifiers),
            parse_candidates,
        )
        label = self._binding.binding
        if read.value is None:
            return SearchAnswer(
                value=NOT_EVALUATED, reason=read.reason, as_of=read.as_of, binding=label
            )
        return SearchAnswer(
            value=FOUND if read.value else NOT_FOUND,
            candidates=read.value,
            as_of=read.as_of,
            binding=label,
        )

    def term_history(self, policy_reference: str) -> TermHistoryAnswer:
        horizon = self._binding.history_horizon
        read = _read(
            self._file_set,
            self._binding.timeout_seconds,
            self._binding.clock,
            lambda _: self._file_set.history(policy_reference),
            lambda raw: parse_term_history(raw, horizon),
        )
        history = read.value
        if history is None:
            history = TermHistory(value=NOT_OBTAINED, reason=read.reason, history_from=horizon)
        return TermHistoryAnswer(history=history, as_of=read.as_of, binding=self._binding.binding)


class ExtractClaimsPort:
    def __init__(self, file_set: ExtractFileSet, binding: ClaimsBinding) -> None:
        self._file_set = file_set
        self._binding = binding

    def existing_claims(self, policy_reference: str) -> ExistingClaimsAnswer:
        read = _read(
            self._file_set,
            self._binding.timeout_seconds,
            self._binding.clock,
            lambda _: self._file_set.claims(policy_reference),
            parse_claims,
        )
        label = self._binding.binding
        if read.value is None:
            return ExistingClaimsAnswer(
                value=NOT_OBTAINED, reason=read.reason, as_of=read.as_of, binding=label
            )
        return ExistingClaimsAnswer(
            value=OBTAINED, claims=read.value, as_of=read.as_of, binding=label
        )
