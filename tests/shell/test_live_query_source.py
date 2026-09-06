"""The live-query wire shape's translation, tested at the parsers: anything
that is not the shape raises, so live_query_ports.py answers SOURCE_MALFORMED
for it, and the shape itself round-trips into the domain's types.

The contract suite reaches the malformed path with one garbage answer; these
reach each way a single field can be wrong, which is what a real source's
drift looks like.
"""

from datetime import date
from typing import Any

import pytest

from claimgate.domain.coverage import CANCELLATION, PolicyTerm, TermHistory, TermStatusChange
from claimgate.domain.models import ExistingClaim
from claimgate.domain.policy_identification import POLICY_NUMBER
from claimgate.shell.live_query_source import parse_candidates, parse_claims, parse_term_history
from claimgate.shell.ports import OBTAINED, PolicyCandidate

NOT_THE_SHAPE = (TypeError, KeyError, ValueError)
CANDIDATE: dict[str, Any] = {
    "policy_reference": "src-ref-000001",
    "policy_number": "HO-1234567",
    "named_insureds": ["Dana Alvarez"],
    "matched_by": "policy_number",
}
TERM: dict[str, Any] = {
    "effective": "2025-10-01",
    "expiration": "2026-10-01",
    "status_changes": [{"kind": "cancellation", "effective": "2026-01-15"}],
}
HISTORY: dict[str, Any] = {"terms": [TERM], "prior_coverage": None}
CLAIM: dict[str, Any] = {
    "claim_id": "CLM-1",
    "policy_number": "HO-1234567",
    "loss_date": "2026-03-02",
    "loss_type": "wind_hail",
}


def without(record: dict[str, Any], key: str) -> dict[str, Any]:
    return {k: v for k, v in record.items() if k != key}


def test_a_well_formed_candidate_parses() -> None:
    assert parse_candidates([CANDIDATE]) == (
        PolicyCandidate("src-ref-000001", "HO-1234567", ("Dana Alvarez",), POLICY_NUMBER),
    )


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param("HO-1234567", id="text where a sequence is expected"),
        pytest.param(["HO-1234567"], id="text where a record is expected"),
        pytest.param([{**CANDIDATE, "policy_reference": 7}], id="a number where text is expected"),
        pytest.param([{**CANDIDATE, "named_insureds": "Dana Alvarez"}], id="text for the insureds"),
        pytest.param([{**CANDIDATE, "named_insureds": [7]}], id="a number among the insureds"),
        pytest.param([{**CANDIDATE, "matched_by": "phone"}], id="a basis outside the vocabulary"),
        pytest.param([without(CANDIDATE, "policy_number")], id="a missing key"),
    ],
)
def test_a_candidate_outside_the_wire_shape_raises(raw: object) -> None:
    with pytest.raises(NOT_THE_SHAPE):
        parse_candidates(raw)


def test_a_well_formed_history_parses_under_the_horizon_it_is_given() -> None:
    assert parse_term_history(HISTORY, date(2019, 1, 1)) == TermHistory(
        value=OBTAINED,
        terms=(
            PolicyTerm(
                date(2025, 10, 1),
                date(2026, 10, 1),
                (TermStatusChange(CANCELLATION, date(2026, 1, 15)),),
            ),
        ),
        history_from=date(2019, 1, 1),
    )


def history_of(*terms: dict[str, Any]) -> dict[str, Any]:
    return {"terms": list(terms), "prior_coverage": None}


LAPSE = {"kind": "lapse", "effective": "2026-01-15"}


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param([TERM], id="a sequence where a record is expected"),
        pytest.param({**HISTORY, "terms": TERM}, id="one term where a sequence is expected"),
        pytest.param({"terms": [TERM]}, id="prior coverage not stated at all"),
        pytest.param({**HISTORY, "prior_coverage": {"ending": "2024-10-01"}}, id="prior partial"),
        pytest.param(history_of({**TERM, "effective": "2026-13-01"}), id="not a date"),
        pytest.param(history_of({**TERM, "status_changes": [LAPSE]}), id="unknown status kind"),
        pytest.param(history_of(without(TERM, "status_changes")), id="status changes missing"),
    ],
)
def test_a_history_outside_the_wire_shape_raises(raw: object) -> None:
    with pytest.raises(NOT_THE_SHAPE):
        parse_term_history(raw, None)


def test_well_formed_claims_parse() -> None:
    assert parse_claims([CLAIM]) == (
        ExistingClaim("CLM-1", "HO-1234567", date(2026, 3, 2), "wind_hail"),
    )


@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(CLAIM, id="one record where a sequence is expected"),
        pytest.param([{**CLAIM, "loss_date": "March 2nd"}], id="a loss date that is not a date"),
        pytest.param([{**CLAIM, "claim_id": 1}], id="a number where text is expected"),
        pytest.param([without(CLAIM, "loss_type")], id="a missing key"),
    ],
)
def test_a_claim_outside_the_wire_shape_raises(raw: object) -> None:
    with pytest.raises(NOT_THE_SHAPE):
        parse_claims(raw)
