"""The two core-system ports the shell consumes, as protocols, and the
envelopes every answer arrives in.

PHASE3_DESIGN.md, "Two ports, not one adapter" and "Every port answer is
three-valued, carries an as-of instant, and never raises". Shell vocabulary:
the domain is not touched, and the two shapes it already owns cross these
envelopes as they are - `TermHistory` (domain/coverage.py, itself
OBTAINED/NOT_OBTAINED with the source's reason, its horizon and any prior
coverage) and `ExistingClaim` (domain/models.py, what find_duplicates takes).

**Never raises.** An implementation catches everything and answers the
not-evaluated value with a reason; nothing propagates through these methods.
notice_intake's contract is that an exception in evaluation means "the rules
could not be evaluated, leave the notice at RECEIVED, the retry replays"; a
port fault is not that - the notice must still be decided and the retry would
meet the same outage - and the standing rule that a result not computed is
never reported as a negative is why the fault is a value rather than an
exception or an empty result.

**The reason enumeration is this feature's own**, closed, and not duplicate
detection's, SIU's or coverage's (CLAUDE.md). IDENTIFIERS_INSUFFICIENT here is
the source's: it cannot search on the identifier combination it was handed - a
source with no insured-name search, say - and it is distinct from the domain's
POLICY_IDENTIFIERS_INSUFFICIENT, which is decided from the notice alone before
any search runs. Every answer sets `reason` only on its not-evaluated value,
the domain's convention.

**`as_of` on every answer**, the not-evaluated ones included: the instant the
answer reflects, read from a clock the deployment injects at construction -
the shell itself reads none (ASSUMPTIONS.md, "One receipt clock, not two").
A live query stamps the call instant; an extract stamps its generation
instant. **`binding`** names the configured binding that produced the answer
(bindings.py composes the label), so a stored row can say which configured
source answered and not only when.

`register_claim` is named on ClaimsPort below as phase 6's write and is not
defined: the read side is designed knowing that write is coming.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal, Protocol

from claimgate.domain.coverage import TermHistory
from claimgate.domain.models import ExistingClaim
from claimgate.domain.policy_identification import SearchIdentifiers

# The closed reason enumeration this feature owns.
SOURCE_UNAVAILABLE: Final = "SOURCE_UNAVAILABLE"
SOURCE_TIMEOUT: Final = "SOURCE_TIMEOUT"
SOURCE_MALFORMED: Final = "SOURCE_MALFORMED"
IDENTIFIERS_INSUFFICIENT: Final = "IDENTIFIERS_INSUFFICIENT"
PORT_REASONS: Final = frozenset(
    {SOURCE_UNAVAILABLE, SOURCE_TIMEOUT, SOURCE_MALFORMED, IDENTIFIERS_INSUFFICIENT}
)

FOUND: Final = "FOUND"
NOT_FOUND: Final = "NOT_FOUND"
NOT_EVALUATED: Final = "NOT_EVALUATED"
SearchValue = Literal["FOUND", "NOT_FOUND", "NOT_EVALUATED"]

OBTAINED: Final = "OBTAINED"
NOT_OBTAINED: Final = "NOT_OBTAINED"
ClaimsValue = Literal["OBTAINED", "NOT_OBTAINED"]

# The domain's two search arms (policy_identification.py), reused as the basis
# a candidate was matched on rather than a third vocabulary for the same fact.
MatchBasis = Literal["POLICY_NUMBER", "INSURED_NAME_AND_POSTAL_CODE"]

# What a deployment injects for "now". The shell never calls one of its own.
Clock = Callable[[], datetime]


@dataclass(frozen=True)
class PolicyCandidate:
    # The source system's own identifier, which is not necessarily the number
    # the reporter gave: every later call names the policy by this.
    policy_reference: str
    policy_number: str
    named_insureds: tuple[str, ...]
    match_basis: MatchBasis


@dataclass(frozen=True, kw_only=True)
class SearchAnswer:
    # FOUND with one or several candidates - how many is item 7f's question,
    # not the port's. candidates only for FOUND, reason only for NOT_EVALUATED.
    value: SearchValue
    candidates: tuple[PolicyCandidate, ...] = ()
    reason: str | None = None
    as_of: datetime
    binding: str


@dataclass(frozen=True, kw_only=True)
class TermHistoryAnswer:
    # The history is already three-valued and carries the source's reason and
    # its horizon itself, so this envelope adds only what every answer carries.
    history: TermHistory
    as_of: datetime
    binding: str


@dataclass(frozen=True, kw_only=True)
class ExistingClaimsAnswer:
    # OBTAINED with no claims is an answer - the source looked and found none.
    # claims only for OBTAINED, reason only for NOT_OBTAINED.
    value: ClaimsValue
    claims: tuple[ExistingClaim, ...] = ()
    reason: str | None = None
    as_of: datetime
    binding: str


class PolicyPort(Protocol):
    """The policy side of a core system: find the policy, then its terms."""

    def search(self, identifiers: SearchIdentifiers) -> SearchAnswer: ...

    def term_history(self, policy_reference: str) -> TermHistoryAnswer: ...


class ClaimsPort(Protocol):
    """The claims side of a core system. Read-only in phase 3: `register_claim`
    - hand the notice over, receive a claim number - is phase 6's write and is
    named here so no phase-3 shape makes it awkward; it is not defined."""

    def existing_claims(self, policy_reference: str) -> ExistingClaimsAnswer: ...
