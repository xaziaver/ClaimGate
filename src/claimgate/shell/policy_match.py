"""The policy search at intake, and what it leaves for the decision to record.

PHASE3_DESIGN.md, "Where the calls sit": between the receipt transaction and
the decision transaction, holding no lock, in the order the data forces.
Identifier sufficiency (domain/policy_identification.py) decides whether there
is anything to search on; the search answers with references; a single
reference is what the term history is asked for; and the two coverage rules
(domain/coverage.py, domain/continuous_coverage.py) read that history against
the loss date. The domain reads every answer as data. This module is the only
place a port is called on the intake path, and the claims port is not called
here at all: item 7h owns it, with its one consumer.

**The verification runs whenever the notice can be searched and states a loss
date, whatever else blocks it** (ASSUMPTIONS.md, 7f decision 4). An injury
notice pending on a missing claimant name is searched all the same, so the
reviewer clearing that pend sees the match beside it and the port call is spent
once, at intake. Where the notice cannot be searched - no policy number, which
validation pends on its own until item 7g retires that requirement, the
insured-name arm being 7g's too - or states no loss date, nothing is asked and
nothing is recorded. The term rules take a loss date and have no vocabulary for
a notice that gives none, exactly as the SIU rules raise rather than record one
(domain/siu.py), and inventing a reason code for either is an escalation, not
an edit (CLAUDE.md). Both notices pend on validation's own blocker regardless,
so neither rests TRIAGED unverified at intake; 7g's re-search on resolution is
what verifies them later. Recorded as a judgment in QUEUE.md's 7f
implementation paragraph.

**A port fault is a value here, never an exception** (ports.py). A search that
was not evaluated is a NOT_EVALUATED match carrying the source's reason, and a
notice with no single matched policy has a history that was not obtained for
the identification's own reason (domain/policy_match.py), so both coverage
rules answer NOT_EVALUATED with a reason that says why and the notice proceeds
or pends on the match alone.

`as_of` and `binding` are the search answer's: one answer, one instant, one
configured source, with the history fetched from the same binding immediately
after. The live-query shape stamps both from the clock the binding was
constructed with, which on this path is the submission instant (7f decision 9;
receipt.py hands it in).
"""

from datetime import date

from claimgate.domain.continuous_coverage import derive_continuous_coverage
from claimgate.domain.coverage import TermHistory, determine_term_in_force
from claimgate.domain.policy_identification import evaluate_identifier_sufficiency
from claimgate.domain.policy_match import PolicyMatch, match_policy, unobtained_history
from claimgate.shell.coverage_verifications import Verification
from claimgate.shell.messages import NoticeFields
from claimgate.shell.ports import PolicyPort


def verify_policy(
    port: PolicyPort, fields: NoticeFields, loss_date: date | None
) -> Verification | None:
    """None where the notice cannot be verified at all (module docstring);
    every other outcome, a source fault included, is a Verification."""
    if loss_date is None:
        return None
    sufficiency = evaluate_identifier_sufficiency(
        fields.policy_number, fields.insured_name, fields.risk_postal_code
    )
    if sufficiency.search is None:
        return None
    answer = port.search(sufficiency.search)
    match = match_policy(
        tuple(candidate.policy_reference for candidate in answer.candidates), answer.reason
    )
    history = _history_for(port, match)
    return Verification(
        match=match,
        term=determine_term_in_force(history, loss_date),
        coverage=derive_continuous_coverage(history, loss_date),
        as_of=answer.as_of,
        binding=answer.binding,
    )


def _history_for(port: PolicyPort, match: PolicyMatch) -> TermHistory:
    """A single matched policy's history is the source's to supply; any other
    match already says why there is none."""
    if match.policy_reference is None:
        return unobtained_history(match)
    return port.term_history(match.policy_reference).history
