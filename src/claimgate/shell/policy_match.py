"""The policy check on both endpoint paths: identifier sufficiency, the search,
and what they leave for the decision to record.

PHASE3_DESIGN.md, "Where the calls sit": between the receipt transaction and
the decision transaction at intake, and between the read and the write on
resolution (item 7g), holding no lock, in the order the data forces.
Identifier sufficiency (domain/policy_identification.py) decides whether there
is anything to search on - and, where there is not, the blocker the notice
carries instead, which validation stopped raising at 7g; the search answers
with references and the basis each was found on; a single reference is what
the term history is asked for; and the two coverage rules (domain/coverage.py,
domain/continuous_coverage.py) read that history against the loss date. The
domain reads every answer as data. This module is the only place a port is
called on either path except the claims port, which duplicate_evaluations.py
calls with its one consumer (item 7h); the found policy's number rides on the
verification for that call.

**The search runs whenever the notice can be searched and states a loss
date, whatever else blocks it** (ASSUMPTIONS.md, 7f decision 4). An injury
notice pending on a missing claimant name is searched all the same, so the
reviewer clearing that pend sees the match beside it. Where the notice cannot
be searched - too little to search on, which is the identification blocker
(7g decision 4), or no loss date - nothing is asked and nothing is recorded:
the term rules take a loss date and have no vocabulary for a notice that
gives none, exactly as the SIU rules raise rather than record one
(domain/siu.py), and inventing a reason code is an escalation, not an edit
(CLAUDE.md). Both notices pend on their own blocker regardless, so neither
rests TRIAGED unverified; the re-search on resolution verifies them once a
reviewer has supplied what was missing.

**A port fault is a value here, never an exception** (ports.py). A search that
was not evaluated is a NOT_EVALUATED match carrying the source's reason - a
source that cannot search on the identifiers it was given answers
IDENTIFIERS_INSUFFICIENT and the notice proceeds exactly as under the three
fault reasons (7g decision 4) - and a notice with no single matched policy has
a history that was not obtained for the identification's own reason
(domain/policy_match.py), so both coverage rules answer NOT_EVALUATED with a
reason that says why and the notice proceeds or pends on the match alone.

`as_of` and `binding` are the search answer's: one answer, one instant, one
configured source, with the history fetched from the same binding immediately
after. The live-query shape stamps both from the clock the binding was
constructed with - the submission instant at intake (7f decision 9), the
resolution's own instant on resolution (item 7g).
"""

from dataclasses import dataclass
from datetime import date
from typing import TypeGuard

from claimgate.domain.continuous_coverage import derive_continuous_coverage
from claimgate.domain.coverage import TermHistory, determine_term_in_force
from claimgate.domain.models import ValidationBlocker
from claimgate.domain.policy_identification import (
    SearchIdentifiers,
    evaluate_identifier_sufficiency,
    identification_blockers,
)
from claimgate.domain.policy_match import (
    NOT_EVALUATED,
    FoundPolicy,
    PolicyMatch,
    match_policy,
    unobtained_history,
)
from claimgate.shell.coverage_verifications import Verification
from claimgate.shell.messages import NoticeFields
from claimgate.shell.ports import PolicyCandidate, PolicyPort


@dataclass(frozen=True)
class PolicyCheck:
    """What the check leaves for the decision: the identification's blocker
    where the notice could not be searched, and the verification where it
    was - never both, and neither where the notice states no loss date."""

    blockers: tuple[ValidationBlocker, ...]
    verification: Verification | None


def check_policy(port: PolicyPort, fields: NoticeFields, loss_date: date | None) -> PolicyCheck:
    """Sufficiency first, on the notice alone; then the search, only where
    there is something to search on and a loss date to read the answer
    against (module docstring)."""
    sufficiency = evaluate_identifier_sufficiency(
        fields.policy_number, fields.insured_name, fields.risk_postal_code
    )
    blockers = identification_blockers(sufficiency)
    if sufficiency.search is None or loss_date is None:
        return PolicyCheck(blockers, None)
    return PolicyCheck(blockers, _verify(port, sufficiency.search, loss_date))


def answered(verification: Verification | None) -> TypeGuard[Verification]:
    """Whether a search produced an answer the rules act on: a match other than
    NOT_EVALUATED. No search at all is not an answer either."""
    return verification is not None and verification.match.value != NOT_EVALUATED


def _verify(port: PolicyPort, search: SearchIdentifiers, loss_date: date) -> Verification:
    answer = port.search(search)
    match = match_policy(
        tuple(
            FoundPolicy(candidate.policy_reference, candidate.match_basis)
            for candidate in answer.candidates
        ),
        answer.reason,
    )
    history = _history_for(port, match)
    return Verification(
        match=match,
        term=determine_term_in_force(history, loss_date),
        coverage=derive_continuous_coverage(history, loss_date),
        as_of=answer.as_of,
        binding=answer.binding,
        policy_number=_found_number(answer.candidates, match),
    )


def _found_number(candidates: tuple[PolicyCandidate, ...], match: PolicyMatch) -> str | None:
    """The matched policy's own number, for duplicate detection to compare
    against (item 7h, decisions 4 and 9). Only a MATCHED result names a
    reference, so any other match finds nothing here and carries None."""
    for candidate in candidates:
        if candidate.policy_reference == match.policy_reference:
            return candidate.policy_number
    return None


def _history_for(port: PolicyPort, match: PolicyMatch) -> TermHistory:
    """A single matched policy's history is the source's to supply; any other
    match already says why there is none."""
    if match.policy_reference is None:
        return unobtained_history(match)
    return port.term_history(match.policy_reference).history
