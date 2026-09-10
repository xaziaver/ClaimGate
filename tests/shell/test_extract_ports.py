"""The extract shape at the file set: every way a generated file set can be
missing, slow or not its shape, and what the port answers with and as of when.

The contract suite (test_port_contracts.py) proves the extract keeps the port
promise over a well-formed file set with one-shot faults at the reader; these
reach the real files - a directory that is not there, a manifest that is not
JSON, a policies file that is a mapping - and the one judgment the contract
cannot see: an extract that cannot be opened has no instant, so that answer
carries the call instant, while any failure past the manifest carries the
extract's (ASSUMPTIONS.md, 7i).
"""

import json
import time
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest

from claimgate.domain.policy_identification import SearchIdentifiers
from claimgate.shell.bindings import ClaimsBinding, PolicyBinding
from claimgate.shell.extract_ports import ExtractClaimsPort, ExtractPolicyPort
from claimgate.shell.extract_source import (
    CLAIMS,
    MANIFEST,
    POLICIES,
    TERMS,
    ExtractFileSet,
    parse_manifest,
    read_file,
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
)

CLOCK = datetime(2026, 8, 24, 16, 0, tzinfo=UTC)
GENERATED_AT = datetime(2026, 8, 23, 4, 0, tzinfo=UTC)
REFERENCE = "src-ref-000001"
NUMBER = "HO-4471209"
MANIFEST_DOCUMENT: dict[str, Any] = {
    "generated_at": GENERATED_AT.isoformat(),
    "history_from": "complete",
    "searchable_by": ["policy_number", "insured_name_and_postal_code"],
}
POLICY: dict[str, Any] = {
    "policy_reference": REFERENCE,
    "policy_number": NUMBER,
    "named_insureds": ["Marisol Quintero"],
    "risk_postal_code": "34287",
}
HISTORY: dict[str, Any] = {
    "terms": [{"effective": "2026-01-15", "expiration": "2027-01-15", "status_changes": []}],
    "prior_coverage": None,
}
CLAIM: dict[str, Any] = {
    "claim_id": "CLM-1", "policy_number": NUMBER, "loss_date": "2026-03-02", "loss_type": "water",
}
BY_NUMBER = SearchIdentifiers(policy_number=NUMBER)
BY_NAME = SearchIdentifiers(insured_name="marisol quintero", risk_postal_code="34287")


def write(directory: Path, name: str, document: Any) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    text = document if isinstance(document, str) else json.dumps(document)
    (directory / name).write_text(text, encoding="utf-8")


def whole(directory: Path, manifest: dict[str, Any] = MANIFEST_DOCUMENT) -> Path:
    write(directory, MANIFEST, manifest)
    write(directory, POLICIES, [POLICY])
    write(directory, TERMS, {REFERENCE: HISTORY})
    write(directory, CLAIMS, {REFERENCE: [CLAIM]})
    return directory


def policy_port(file_set: ExtractFileSet, *, budget: float = 1.0) -> ExtractPolicyPort:
    binding = PolicyBinding(
        binding="AAAA/policy:extract",
        timeout_seconds=budget,
        history_horizon=None,
        clock=lambda: CLOCK,
        parameters={},
    )
    return ExtractPolicyPort(file_set, binding)


def claims_port(file_set: ExtractFileSet) -> ExtractClaimsPort:
    binding = ClaimsBinding(
        binding="AAAA/claims:extract", timeout_seconds=1.0, clock=lambda: CLOCK, parameters={}
    )
    return ExtractClaimsPort(file_set, binding)


# -- an extract that cannot be opened answers as of the call ------------------------


def test_a_directory_that_is_not_there_is_unavailable_as_of_the_call(tmp_path: Path) -> None:
    answer = policy_port(ExtractFileSet(tmp_path / "absent")).search(BY_NUMBER)
    assert (answer.value, answer.reason, answer.as_of) == (
        NOT_EVALUATED, SOURCE_UNAVAILABLE, CLOCK
    )


def test_a_manifest_that_is_not_json_is_malformed_as_of_the_call(tmp_path: Path) -> None:
    write(tmp_path, MANIFEST, "{not json")
    answer = policy_port(ExtractFileSet(tmp_path)).search(BY_NUMBER)
    assert (answer.value, answer.reason, answer.as_of) == (NOT_EVALUATED, SOURCE_MALFORMED, CLOCK)


@pytest.mark.parametrize(
    "manifest",
    [
        {**MANIFEST_DOCUMENT, "generated_at": "2026-08-23T04:00:00"},
        {**MANIFEST_DOCUMENT, "generated_at": "yesterday"},
        {**MANIFEST_DOCUMENT, "history_from": "always"},
        {**MANIFEST_DOCUMENT, "history_from": 2019},
        {**MANIFEST_DOCUMENT, "searchable_by": []},
        {**MANIFEST_DOCUMENT, "searchable_by": ["vin"]},
        {**MANIFEST_DOCUMENT, "searchable_by": "policy_number"},
        {key: value for key, value in MANIFEST_DOCUMENT.items() if key != "generated_at"},
        [MANIFEST_DOCUMENT],
    ],
    ids=[
        "instant without offset", "instant not an instant", "horizon a word", "horizon a number",
        "no arms", "an arm this shape has not", "arms not a list", "no instant", "not a record",
    ],
)
def test_a_manifest_that_is_not_its_shape_is_malformed_as_of_the_call(
    tmp_path: Path, manifest: Any
) -> None:
    whole(tmp_path, manifest)
    answer = policy_port(ExtractFileSet(tmp_path)).term_history(REFERENCE)
    assert (answer.history.value, answer.history.reason) == (NOT_OBTAINED, SOURCE_MALFORMED)
    assert answer.as_of == CLOCK


def test_parse_manifest_takes_the_manifests_text_and_nothing_else() -> None:
    with pytest.raises(TypeError):
        parse_manifest(MANIFEST_DOCUMENT)


def test_a_manifest_read_that_exhausts_the_budget_is_a_timeout_as_of_the_call(
    tmp_path: Path,
) -> None:
    whole(tmp_path)

    def slow(path: Path) -> str:
        time.sleep(0.3)
        return read_file(path)

    answer = policy_port(ExtractFileSet(tmp_path, read_text=slow), budget=0.05).search(BY_NUMBER)
    assert (answer.value, answer.reason, answer.as_of) == (NOT_EVALUATED, SOURCE_TIMEOUT, CLOCK)


# -- past the manifest, every answer is as of the extract ---------------------------


def test_a_data_file_that_is_not_there_is_unavailable_as_of_the_extract(tmp_path: Path) -> None:
    write(tmp_path, MANIFEST, MANIFEST_DOCUMENT)
    file_set = ExtractFileSet(tmp_path)
    search = policy_port(file_set).search(BY_NUMBER)
    history = policy_port(file_set).term_history(REFERENCE)
    claims = claims_port(file_set).existing_claims(REFERENCE)
    assert (search.value, search.reason, search.as_of) == (
        NOT_EVALUATED, SOURCE_UNAVAILABLE, GENERATED_AT
    )
    assert (history.history.value, history.history.reason, history.as_of) == (
        NOT_OBTAINED, SOURCE_UNAVAILABLE, GENERATED_AT
    )
    assert (claims.value, claims.reason, claims.as_of) == (
        NOT_OBTAINED, SOURCE_UNAVAILABLE, GENERATED_AT
    )


@pytest.mark.parametrize(
    "policies",
    [
        "{not json",
        {"policies": [POLICY]},
        ["not a record"],
        [{key: value for key, value in POLICY.items() if key != "policy_number"}],
        [{**POLICY, "named_insureds": "Marisol Quintero"}],
        [{**POLICY, "named_insureds": [7]}],
        [{**POLICY, "policy_number": 4471209}],
    ],
    ids=[
        "not json", "a record where a list is expected", "an item that is not a record",
        "a record without its number", "insureds that are not a list", "an insured that is not text",
        "a number that is not text",
    ],
)
def test_a_policies_file_that_is_not_its_shape_is_malformed_as_of_the_extract(
    tmp_path: Path, policies: Any
) -> None:
    whole(tmp_path)
    write(tmp_path, POLICIES, policies)
    answer = policy_port(ExtractFileSet(tmp_path)).search(BY_NAME)
    assert (answer.value, answer.reason, answer.as_of) == (
        NOT_EVALUATED, SOURCE_MALFORMED, GENERATED_AT
    )


@pytest.mark.parametrize("terms", ["{not json", [HISTORY]], ids=["not json", "not a mapping"])
def test_a_terms_file_that_is_not_its_shape_is_malformed_as_of_the_extract(
    tmp_path: Path, terms: Any
) -> None:
    whole(tmp_path)
    write(tmp_path, TERMS, terms)
    answer = policy_port(ExtractFileSet(tmp_path)).term_history(REFERENCE)
    assert (answer.history.value, answer.history.reason) == (NOT_OBTAINED, SOURCE_MALFORMED)
    assert answer.as_of == GENERATED_AT


def test_a_claims_file_that_is_not_a_mapping_is_malformed_as_of_the_extract(
    tmp_path: Path,
) -> None:
    whole(tmp_path)
    write(tmp_path, CLAIMS, [CLAIM])
    answer = claims_port(ExtractFileSet(tmp_path)).existing_claims(REFERENCE)
    assert (answer.value, answer.reason, answer.as_of) == (
        NOT_OBTAINED, SOURCE_MALFORMED, GENERATED_AT
    )


def test_a_reference_no_file_holds_is_the_extracts_own_failure(tmp_path: Path) -> None:
    file_set = ExtractFileSet(whole(tmp_path))
    history = policy_port(file_set).term_history("src-ref-unknown")
    claims = claims_port(file_set).existing_claims("src-ref-unknown")
    assert (history.history.value, history.history.reason) == (NOT_OBTAINED, SOURCE_UNAVAILABLE)
    assert (claims.value, claims.reason) == (NOT_OBTAINED, SOURCE_UNAVAILABLE)
    assert (history.as_of, claims.as_of) == (GENERATED_AT, GENERATED_AT)


# -- what a well-formed extract answers -----------------------------------------------


def test_a_number_the_extract_does_not_hold_is_not_found_as_of_the_extract(
    tmp_path: Path,
) -> None:
    answer = policy_port(ExtractFileSet(whole(tmp_path))).search(
        SearchIdentifiers(policy_number="HO-4471290")
    )
    assert (answer.value, answer.candidates, answer.as_of) == (NOT_FOUND, (), GENERATED_AT)


def test_a_name_search_over_an_extract_of_numbers_only_is_identifiers_insufficient(
    tmp_path: Path,
) -> None:
    whole(tmp_path, {**MANIFEST_DOCUMENT, "searchable_by": ["policy_number"]})
    port = policy_port(ExtractFileSet(tmp_path))
    by_name = port.search(BY_NAME)
    assert (by_name.value, by_name.reason, by_name.as_of) == (
        NOT_EVALUATED, IDENTIFIERS_INSUFFICIENT, GENERATED_AT
    )
    assert port.search(BY_NUMBER).value == FOUND
    # A number that misses beside a name the extract cannot search on is a
    # miss, not a name match.
    mistyped = SearchIdentifiers(
        policy_number="HO-4471290", insured_name="Marisol Quintero", risk_postal_code="34287"
    )
    assert port.search(mistyped).value == NOT_FOUND


def test_the_extracts_own_horizon_is_read_and_the_bindings_is_stamped(tmp_path: Path) -> None:
    # The manifest states how far back the extract goes; the port stamps the
    # binding's horizon, as the protocol requires (bindings.py). The two
    # disagreeing is an open decision, not a rule here.
    whole(tmp_path, {**MANIFEST_DOCUMENT, "history_from": "2019-01-01"})
    file_set = ExtractFileSet(tmp_path)
    manifest = parse_manifest(file_set.manifest())
    answer = policy_port(file_set).term_history(REFERENCE)
    assert manifest.history_from == date(2019, 1, 1)
    assert (answer.history.value, answer.history.history_from) == (OBTAINED, None)
    assert answer.as_of == GENERATED_AT
