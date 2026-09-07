"""Pure policy-match rule: what the search's answer does to the notice.

PHASE3_DESIGN.md, "Coverage verification as an intake outcome", stated by
features/policy_match.feature. The search is the shell's - it reaches a policy
port - and this rule reads its answer as data: the policies it found, by the
source's own reference, and the source's reason where it could not be
evaluated. Exactly one reference is MATCHED and the notice proceeds. None is
NOT_MATCHED and several is AMBIGUOUS: each is a blocker a reviewer can act on -
correcting the identifiers, or choosing between the policies - so the notice
pends. A search that was not evaluated is NOT_EVALUATED with the source's reason
and is not a blocker, because nobody can supply an outage (ASSUMPTIONS.md, the
2026-09-01 port-fault entry and the 7f decisions of 2026-09-07).

The two blockers are this feature's own closed enumeration (CLAUDE.md), beside
policy_identification.py's POLICY_IDENTIFIERS_INSUFFICIENT and never merged
with it. They carry no field: the search failed on whatever identifiers the
notice carried, and naming one of them would claim to know which was wrong.

A notice without a single matched policy has no history to ask for. The
history such a notice carries is NOT_OBTAINED for the identification's own
reason - the source's where the search was not evaluated, the blocker's code
where it found none or several - so the term-in-force and continuous-coverage
rules record NOT_EVALUATED with a reason that says why, rather than a negative
or an empty result (CLAUDE.md).
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal

from claimgate.domain.coverage import TermHistory
from claimgate.domain.models import ValidationBlocker

MATCHED: Final = "MATCHED"
NOT_MATCHED: Final = "NOT_MATCHED"
AMBIGUOUS: Final = "AMBIGUOUS"
NOT_EVALUATED: Final = "NOT_EVALUATED"
PolicyMatchValue = Literal["MATCHED", "NOT_MATCHED", "AMBIGUOUS", "NOT_EVALUATED"]

POLICY_NOT_MATCHED: Final = "POLICY_NOT_MATCHED"
POLICY_AMBIGUOUS: Final = "POLICY_AMBIGUOUS"
_BLOCKER_CODES: Final[Mapping[str, str]] = {
    NOT_MATCHED: POLICY_NOT_MATCHED,
    AMBIGUOUS: POLICY_AMBIGUOUS,
}


@dataclass(frozen=True)
class PolicyMatch:
    # Same convention as the other domain results: policy_reference is set only
    # for MATCHED, reason only for NOT_EVALUATED - and it is the source's reason.
    value: PolicyMatchValue
    policy_reference: str | None = None
    reason: str | None = None


def match_policy(references: tuple[str, ...], reason: str | None) -> PolicyMatch:
    """`references` are the policies the search found, by the source's own
    identifier; `reason` is set where the search was not evaluated. A search
    that was not evaluated found nothing, so both at once is a caller contract
    violation rather than a case to choose between."""
    if reason is not None:
        if references:
            raise ValueError("a search that was not evaluated cannot have found a policy")
        return PolicyMatch(NOT_EVALUATED, reason=reason)
    if len(references) == 1:
        return PolicyMatch(MATCHED, policy_reference=references[0])
    if not references:
        return PolicyMatch(NOT_MATCHED)
    return PolicyMatch(AMBIGUOUS)


def match_blockers(match: PolicyMatch | None) -> tuple[ValidationBlocker, ...]:
    """The blocker a match contributes to the notice's list: one for
    NOT_MATCHED, one for AMBIGUOUS, none for MATCHED or NOT_EVALUATED. None is
    a notice no search has run over at all - nothing searchable on it, or from
    before the search existed - which contributes nothing, and is a different
    fact from a search that found nothing."""
    if match is None or match.value not in _BLOCKER_CODES:
        return ()
    return (ValidationBlocker(_BLOCKER_CODES[match.value], ""),)


def unobtained_history(match: PolicyMatch) -> TermHistory:
    """The term history of a notice with no single matched policy: not
    obtained, for the identification's own reason (module docstring). A matched
    policy's history is the source's to supply, never this rule's."""
    if match.value == MATCHED:
        raise ValueError("a matched policy's term history is the source's to supply")
    reason = match.reason if match.value == NOT_EVALUATED else _BLOCKER_CODES[match.value]
    return TermHistory(value="NOT_OBTAINED", reason=reason)
