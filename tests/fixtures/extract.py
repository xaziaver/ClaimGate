"""The extract file set, generated from the in-process fixture's held state.

What tests/fixtures/core_system.py holds for the live-query shape is written
here as the files extract_source.py reads, at one instant: the policies bound
by that instant, their term histories and their claims, under a manifest that
names the instant. The contract harness (tests/shell/port_harness.py) and the
acceptance test API (tests/api/policy_match.py) both generate through this,
so the two shapes answer from one record set and the same holds (item 7i,
ASSUMPTIONS.md decision 4).

The fixture's standing faults become the file set's own: a source that is
unavailable is an extract with no data files behind its manifest; one that
answers a shape not its own is data files that are not JSON; the claims side
down is a missing claims file. The manifest is always written, so every such
answer still carries the extract's instant. No file is slow on its own, so a
source that does not answer within its budget is the reader's doing
(`sleeping_reader`), which the test API hands the file set - the port's
budget is enforced on real elapsed time either way.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from claimgate.shell.bindings import COMPLETE_HISTORY
from claimgate.shell.extract_source import (
    BY_INSURED_NAME_AND_POSTAL_CODE,
    BY_POLICY_NUMBER,
    CLAIMS,
    MANIFEST,
    POLICIES,
    TERMS,
    Reader,
    read_file,
)
from tests.fixtures.core_system import InProcessCoreSystem, bound_by

NOT_THE_SHAPE = "this is not one of the extract's documents"
_DATA_FILES = (POLICIES, TERMS, CLAIMS)


def write_extract(system: InProcessCoreSystem, directory: Path, generated_at: datetime) -> None:
    """The file set for the fixture's held state as of `generated_at`, replacing
    whatever the directory held: policies bound after that instant are left
    out, which is the extract shape's one user-visible behaviour."""
    directory.mkdir(parents=True, exist_ok=True)
    for stale in _DATA_FILES:
        (directory / stale).unlink(missing_ok=True)
    arms = [BY_POLICY_NUMBER]
    if system.searches_by_name:
        arms.append(BY_INSURED_NAME_AND_POSTAL_CODE)
    _write(
        directory / MANIFEST,
        {"generated_at": generated_at.isoformat(), "history_from": COMPLETE_HISTORY, "searchable_by": arms},
    )
    fault = system.standing_fault
    if fault is not None and fault[0] == "raise":
        return
    present = {
        reference: policy
        for reference, policy in system.policies().items()
        if bound_by(policy, generated_at)
    }
    documents: dict[str, Any] = {
        POLICIES: [_policy(reference, policy) for reference, policy in present.items()],
        TERMS: {reference: policy["history"] for reference, policy in present.items()},
        CLAIMS: {reference: list(system.claims().get(reference, [])) for reference in present},
    }
    if system.claims_side_down:
        del documents[CLAIMS]
    malformed = fault is not None and fault[0] == "malformed"
    for name, document in documents.items():
        if malformed:
            (directory / name).write_text(NOT_THE_SHAPE, encoding="utf-8")
        else:
            _write(directory / name, document)


def reader_for(system: InProcessCoreSystem) -> Reader:
    """The file set's reader under the fixture's standing fault: every data
    read sleeps where the source "does not answer within its budget"; the
    plain reader otherwise."""
    fault = system.standing_fault
    if fault is not None and fault[0] == "sleep":
        return sleeping_reader(fault[1])
    return read_file


def sleeping_reader(seconds: float) -> Reader:
    """A reader that sleeps before every data read and never before the
    manifest's, so a timed-out answer still carries the extract's instant."""

    def read(path: Path) -> str:
        if path.name != MANIFEST:
            time.sleep(seconds)
        return read_file(path)

    return read


def _policy(reference: str, policy: Any) -> dict[str, Any]:
    return {
        "policy_reference": reference,
        "policy_number": policy["policy_number"],
        "named_insureds": list(policy["named_insureds"]),
        "risk_postal_code": policy["address"].postal_code,
    }


def _write(path: Path, document: Any) -> None:
    path.write_text(json.dumps(document, indent=1), encoding="utf-8")
