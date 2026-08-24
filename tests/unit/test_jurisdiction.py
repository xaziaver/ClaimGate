"""Unit tests for claimgate.domain.jurisdiction."""

from datetime import datetime

import pytest

from claimgate.domain.jurisdiction import (
    JURISDICTION_TIMEZONE_UNRECOGNIZED,
    resolve_jurisdiction_date,
)


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
