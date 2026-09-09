"""Orchestration for POST /notices/{notice_id}/resolution.

PHASE2_DESIGN.md's pending-resolution section is the specification, and
ASSUMPTIONS.md's five item 5e decisions, ratified 2026-08-25, settle what it
left open. There is no HTTP layer anywhere in this project yet; a reviewer's
resolution arrives here as an ordinary call, the way a submission does.

PENDED -> TRIAGED is the only transition this module performs, and it is a USER
transition: releasing a pend is a human judging that what was missing has
actually arrived. There is still no rejected, invalid, or discarded state
(CLAUDE.md) - a resolution that does not clear the pend leaves the notice
exactly where it was, and is answered rather than discarded.

**The order the refusals run in, and why.** A body this endpoint cannot read
is refused first, before the notice is read at all - an identity nobody
supplied or a loss date that is not a date, both 400 with nothing persisted
(decisions 4 and (e)); a caller who has not said who they are does not get to
learn a notice's state. The rest is resolution_evaluation.py's, in two
transactions with the judgement between them (item 7g; PHASE3_DESIGN.md,
"Where the calls sit"). In the read transaction: an id nobody has is 404,
refused before any state is examined (decision (d)) - there is no pend to
release and nothing for the content to be the answer to - and a notice that
exists and is not pended is the 409, which decision 3 says persists nothing.
Item 5i's 500 is raised by the judgement, between the transactions, so it
refuses nothing the reviewer sent and writes nothing: this deployment could
not read its own configuration - the carrier's rules, the jurisdiction map,
or, since item 7g's re-search, the carrier's policy binding - and the notice
keeps the records and the trail it had (ruling 1). Last, in the write transaction, a notice that was
pended when it was read and has moved since is the same 409 - a second
reviewer's resolution committed first, and this one's decision was made about
a notice that no longer exists in that state. Nothing asserts the order
directly - each rule asserts its own answer, and reordering them would answer
one case with another's status.

Out of scope, deliberately: the pend instant and the instant of the resolution
that released the notice are recorded (resolution_evaluation.py writes the
second) and nothing whatever is computed from them, which is PHASE2_DESIGN.md's
"record precisely, compute nothing" - what the Fla. Stat. 627.70131(8)(b)
interval means is a downstream legal determination and no phase-2 code goes
near it.
Duplicate-candidate detection is untouched; and there is no
idempotency key on this endpoint - PHASE2_DESIGN.md scopes the header to
POST /notices, so a network retry of a resolution that already succeeded meets a
TRIAGED notice and is answered by the 409 above. No NotImplementedError remains
anywhere in this module: item 5i ratified the answer to every state that had
one.
"""

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from claimgate.shell import rules
from claimgate.shell.bindings import BindingsSource, ImplementationRegistry
from claimgate.shell.bundles import Resolution
from claimgate.shell.faults import DeploymentFaultError
from claimgate.shell.messages import ResolutionResponse
from claimgate.shell.resolution_evaluation import evaluate
from claimgate.shell.store import NoticeStore


def resolve_notice(
    store: NoticeStore,
    notice_id: str,
    *,
    actor_id: str | None,
    resolved_at: datetime,
    jurisdiction_reference: Mapping[str, Mapping[str, str]],
    carrier_rules_source: Mapping[str, Mapping[str, Any]],
    bindings_source: BindingsSource,
    implementation_registry: ImplementationRegistry,
    supplied: Mapping[str, Any],
    note: str | None = None,
) -> ResolutionResponse:
    reviewer = _reviewer_of(actor_id, supplied)
    if reviewer is None:
        return ResolutionResponse(status=400)
    resolution = Resolution(
        store=store, notice_id=notice_id, actor_id=reviewer, resolved_at=resolved_at,
        jurisdiction_reference=jurisdiction_reference, carrier_rules_source=carrier_rules_source,
        supplied=supplied, bindings_source=bindings_source,
        implementation_registry=implementation_registry, note=note,
    )
    return _answer(resolution)


def _answer(resolution: Resolution) -> ResolutionResponse:
    """Item 5i's 500, caught here and answered with the fault's code: the
    judgement raised it between the two transactions, so nothing was written
    and nothing the reviewer sent was refused (module docstring)."""
    try:
        return evaluate(resolution)
    except DeploymentFaultError as fault:
        return ResolutionResponse(status=500, error=fault.code)


def _reviewer_of(actor_id: str | None, supplied: Mapping[str, Any]) -> str | None:
    """The reviewer this body names, or None where the endpoint cannot read the
    body at all - which is the same 400 either way, before the notice is read.

    Two halves, both about the body. The reviewer's identity is required and
    caller-asserted (decision 4). A supplied loss date that is not a date at all
    is the same schema-invalid refusal (decision (e), 2026-08-25), checked here
    rather than deeper in: intake answers that input the same way at its own
    boundary, so no merged view can ever carry one and a parse over the merged
    view would sit on an input that cannot reach it."""
    if actor_id is None or not actor_id.strip():
        return None
    if rules.parse_loss_date(supplied.get("loss_date")).value == "UNPARSEABLE":
        return None
    return actor_id
