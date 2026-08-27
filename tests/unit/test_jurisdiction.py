"""Unit tests for claimgate.domain.jurisdiction."""

from datetime import datetime

import pytest

from claimgate.domain.jurisdiction import (
    JURISDICTION_REFERENCE,
    JURISDICTION_TIMEZONE_UNRECOGNIZED,
    resolve_jurisdiction_date,
    select_jurisdiction,
)

# A fictional second jurisdiction, so the selection tests below ask which entry
# a key selected rather than only whether one exists. ZZ is user-assigned in
# ISO 3166-1 and can never be a real one.
_TWO_JURISDICTIONS = {
    "FL": {"timezone": "America/New_York"},
    "ZZ": {"timezone": "Pacific/Kiritimati"},
}


@pytest.mark.parametrize(
    ("instant", "timezone_name", "expected_date"),
    [
        ("2026-06-11T01:00Z", "America/New_York", "2026-06-10"),
        ("2026-06-21T02:00Z", "America/New_York", "2026-06-20"),
        ("2026-06-11T04:30Z", "America/New_York", "2026-06-11"),
        ("2026-06-11T04:30Z", "America/Chicago", "2026-06-10"),
        ("2026-01-15T04:30Z", "America/New_York", "2026-01-14"),
        ("2026-01-15T05:01Z", "America/New_York", "2026-01-15"),
        ("2026-07-15T03:59Z", "America/New_York", "2026-07-14"),
        ("2026-07-15T04:30Z", "America/New_York", "2026-07-15"),
    ],
)
def test_resolves_to_the_local_calendar_date(
    instant: str, timezone_name: str, expected_date: str
) -> None:
    result = resolve_jurisdiction_date(datetime.fromisoformat(instant), timezone_name)

    assert result.value == "RESOLVED"
    assert result.resolved_date is not None
    assert result.resolved_date.isoformat() == expected_date
    assert result.reason is None


@pytest.mark.parametrize(
    "timezone_name",
    [
        "America/Nowhere",
        "Not A Zone",
        "america/new_york",
    ],
)
def test_unrecognized_zone_name_is_refused(timezone_name: str) -> None:
    result = resolve_jurisdiction_date(datetime.fromisoformat("2026-06-11T04:30Z"), timezone_name)

    assert result.value == "REFUSED"
    assert result.resolved_date is None
    assert result.reason == JURISDICTION_TIMEZONE_UNRECOGNIZED


@pytest.mark.parametrize(
    "timezone_name",
    [
        "../../etc/passwd",
        "",
    ],
)
def test_malformed_zone_name_is_refused(timezone_name: str) -> None:
    result = resolve_jurisdiction_date(datetime.fromisoformat("2026-06-11T04:30Z"), timezone_name)

    assert result.value == "REFUSED"
    assert result.resolved_date is None
    assert result.reason == JURISDICTION_TIMEZONE_UNRECOGNIZED


@pytest.mark.parametrize(
    ("jurisdiction_code", "expected_timezone"),
    [
        ("FL", "America/New_York"),
        ("ZZ", "Pacific/Kiritimati"),
    ],
)
def test_a_populated_code_selects_that_entrys_timezone(
    jurisdiction_code: str, expected_timezone: str
) -> None:
    # Two entries, so the assertion is that the value came from the entry the
    # key selected and not from whatever the map happens to hold first. The
    # reference is handed in, which is the whole point of the shape.
    result = select_jurisdiction(jurisdiction_code, _TWO_JURISDICTIONS)

    assert result.value == "SELECTED"
    assert result.jurisdiction is not None
    assert result.jurisdiction.timezone == expected_timezone


@pytest.mark.parametrize(
    "jurisdiction_code",
    [
        "GA",
        "fl",
        "Florida",
        " FL",
        "FL ",
        "",
        None,
    ],
)
def test_anything_but_an_exact_key_selects_no_jurisdiction(jurisdiction_code: str | None) -> None:
    # ASSUMPTIONS.md, ratified 2026-08-26: the match is exact and a miss is
    # marked rather than normalized. Case folding and trimming are each a first
    # step toward inferring what the reporter meant, on the field that decides
    # which state's law applies, so each spelling here has to miss.
    result = select_jurisdiction(jurisdiction_code, _TWO_JURISDICTIONS)

    assert result.value == "UNSUPPORTED"
    assert result.jurisdiction is None


def test_the_shipped_reference_holds_florida_and_nothing_else() -> None:
    # PHASE2_DESIGN.md: exactly one entry populated, and it is a real lookup
    # rather than a constant dressed as one - which the parametrized selection
    # above establishes against a two-entry map. This pins what ships.
    assert dict(JURISDICTION_REFERENCE) == {"FL": {"timezone": "America/New_York"}}


def test_an_entry_naming_no_timezone_is_malformed_and_not_a_miss() -> None:
    # A configured jurisdiction whose entry cannot be read is our defect, and
    # it has to stay distinguishable from a state we hold no entry for: the
    # first escalates, the second marks the notice and lets it through. There
    # is no default timezone to fall back to, deliberately - a defaulted zone
    # would date a notice under a calendar nobody chose for it.
    result = select_jurisdiction("FL", {"FL": {}})

    assert result.value == "MALFORMED"
    assert result.jurisdiction is None
