"""The live-query shape of both ports: answers at call time from a source
reached in-process, under a per-call budget that is enforced, not simulated.

PHASE3_DESIGN.md, "Swappability proof": the first of two conforming shapes per
port, the extract shape being item 7i's. The source is anything satisfying
live_query_source.py's protocols; that module owns the wire shape and its
translation, and this one owns what every port answer promises - the
not-evaluated value in place of any failure, the injected clock's instant as
`as_of`, the binding's label as `binding`, and the binding's horizon as
`history_from` on every term history, obtained or not.

**The budget is enforced.** Each source call runs on a worker thread and is
waited on with `future.result(timeout=budget)`. A budget exceeded answers
SOURCE_TIMEOUT - so does a source that raises TimeoutError itself, a timeout
of its own being the same fact seen from the other side. A source that raises
anything else answers SOURCE_UNAVAILABLE; one that cannot search on the
identifiers it was handed (UnsupportedSearchError) answers
IDENTIFIERS_INSUFFICIENT; an answer that does not parse answers
SOURCE_MALFORMED. One guard, `_guarded`, serves all three operations, so the
four mappings are written once.

**The abandoned worker keeps running to completion.** The executor is released
without waiting, so a source call that returns after the budget returns into
nothing, and a source that never returns holds a thread for as long as it
takes. Acceptable for an in-process fixture; a real adapter has to cancel or
bound its own I/O, and this module does not pretend to do that for it.

Nothing here reads a clock of its own: `as_of` is the binding's clock, read
once at the start of every operation, so the not-evaluated answers are stamped
exactly as the answered ones are.
"""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Final

from claimgate.domain.coverage import TermHistory
from claimgate.domain.policy_identification import SearchIdentifiers
from claimgate.shell.bindings import ClaimsBinding, PolicyBinding
from claimgate.shell.live_query_source import (
    ClaimsSource,
    PolicySource,
    UnsupportedSearchError,
    parse_candidates,
    parse_claims,
    parse_term_history,
)
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
    ExistingClaimsAnswer,
    SearchAnswer,
    TermHistoryAnswer,
)

# The implementation name a bindings entry uses to select this shape.
LIVE_QUERY: Final = "live-query"


@dataclass(frozen=True)
class _Guarded[Parsed]:
    # value is set only when the source answered and the answer parsed; reason
    # is set otherwise, from this feature's closed enumeration (ports.py).
    value: Parsed | None = None
    reason: str | None = None


def _guarded[Parsed](
    budget_seconds: float, call: Callable[[], object], parse: Callable[[object], Parsed]
) -> _Guarded[Parsed]:
    executor = ThreadPoolExecutor(max_workers=1)
    try:
        raw = executor.submit(call).result(timeout=budget_seconds)
    except TimeoutError:
        return _Guarded(reason=SOURCE_TIMEOUT)
    except UnsupportedSearchError:
        return _Guarded(reason=IDENTIFIERS_INSUFFICIENT)
    except Exception:
        return _Guarded(reason=SOURCE_UNAVAILABLE)
    finally:
        executor.shutdown(wait=False)
    try:
        return _Guarded(value=parse(raw))
    except Exception:
        return _Guarded(reason=SOURCE_MALFORMED)


class LiveQueryPolicyPort:
    def __init__(self, source: PolicySource, binding: PolicyBinding) -> None:
        self._source = source
        self._binding = binding

    def search(self, identifiers: SearchIdentifiers) -> SearchAnswer:
        as_of = self._binding.clock()
        found = _guarded(
            self._binding.timeout_seconds,
            lambda: self._source.search(
                identifiers.policy_number, identifiers.insured_name, identifiers.risk_postal_code
            ),
            parse_candidates,
        )
        if found.value is None:
            return SearchAnswer(
                value=NOT_EVALUATED, reason=found.reason, as_of=as_of, binding=self._binding.binding
            )
        return SearchAnswer(
            value=FOUND if found.value else NOT_FOUND,
            candidates=found.value,
            as_of=as_of,
            binding=self._binding.binding,
        )

    def term_history(self, policy_reference: str) -> TermHistoryAnswer:
        as_of = self._binding.clock()
        horizon = self._binding.history_horizon
        obtained = _guarded(
            self._binding.timeout_seconds,
            lambda: self._source.term_history(policy_reference),
            lambda raw: parse_term_history(raw, horizon),
        )
        history = obtained.value
        if history is None:
            history = TermHistory(value=NOT_OBTAINED, reason=obtained.reason, history_from=horizon)
        return TermHistoryAnswer(history=history, as_of=as_of, binding=self._binding.binding)


class LiveQueryClaimsPort:
    def __init__(self, source: ClaimsSource, binding: ClaimsBinding) -> None:
        self._source = source
        self._binding = binding

    def existing_claims(self, policy_reference: str) -> ExistingClaimsAnswer:
        as_of = self._binding.clock()
        obtained = _guarded(
            self._binding.timeout_seconds,
            lambda: self._source.existing_claims(policy_reference),
            parse_claims,
        )
        if obtained.value is None:
            return ExistingClaimsAnswer(
                value=NOT_OBTAINED,
                reason=obtained.reason,
                as_of=as_of,
                binding=self._binding.binding,
            )
        return ExistingClaimsAnswer(
            value=OBTAINED, claims=obtained.value, as_of=as_of, binding=self._binding.binding
        )
