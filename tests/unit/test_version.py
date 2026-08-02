from claimgate.version import version


def test_version_is_reported() -> None:
    assert version() == "0.1.0"
