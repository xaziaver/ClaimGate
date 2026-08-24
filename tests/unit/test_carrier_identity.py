"""Unit tests for claimgate.domain.carrier_identity."""

from claimgate.domain.carrier_identity import CARRIER_IDENTITY_REFERENCE, resolve_carrier_identity


def test_a_recognized_carrier_resolves_its_identity() -> None:
    result = resolve_carrier_identity("AAAA", CARRIER_IDENTITY_REFERENCE)

    assert result.value == "RESOLVED"
    assert result.identity is not None
    assert result.identity.name == "Placeholder Carrier A"
    assert result.identity.naic == 10001
    assert result.identity.naic_group == 4001


def test_a_carrier_with_a_null_naic_group_resolves_it_as_none() -> None:
    result = resolve_carrier_identity("CCCC", CARRIER_IDENTITY_REFERENCE)

    assert result.value == "RESOLVED"
    assert result.identity is not None
    assert result.identity.naic_group is None


def test_an_unrecognized_carrier_is_refused() -> None:
    result = resolve_carrier_identity("ZZZZ", CARRIER_IDENTITY_REFERENCE)

    assert result.value == "REFUSED"
    assert result.identity is None
