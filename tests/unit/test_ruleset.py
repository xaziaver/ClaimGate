"""The domain rule set's own label."""

from datetime import date

from claimgate.domain.ruleset import RULESET_VERSION


def test_the_ruleset_version_is_the_date_stamped_label_the_convention_requires() -> None:
    # A label that is not a date cannot answer "which rules were in force on the
    # day this row was written", which is the whole reason the convention picks
    # a date over a semantic version (ASSUMPTIONS.md, item 5f's ruleset-version
    # decision). fromisoformat refuses anything that is not one, and the
    # round-trip refuses a date spelled some other way.
    assert date.fromisoformat(RULESET_VERSION).isoformat() == RULESET_VERSION
