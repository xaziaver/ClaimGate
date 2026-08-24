"""Per-carrier configuration resolution.

Resolves a carrier's raw rules-source entry to the six values phase 1 moved
out of the domain with no default - validate's claimant_name_required,
claimant_contact_required, and recognized_policy_number_prefixes;
compute_siu_indicators's late_reporting_threshold_days and
recent_inception_threshold_days; find_duplicates's window_days - or refuses
the load, naming every value it rejected. A carrier configuration crosses
into those domain calls already resolved (ASSUMPTIONS.md, "A carrier
configuration crosses into the domain already resolved"), so this is the
layer that does the resolving. Where the rules-source mapping itself comes
from (a TOML file, a database row) is deliberately not this module's concern
- see ASSUMPTIONS.md, "The per-carrier rules file is TOML."
"""

from collections.abc import Mapping
from typing import Any

from claimgate.domain.models import (
    CarrierConfigurationResult,
    CarrierRules,
    ConfigurationRejection,
)

CARRIER_NOT_CONFIGURED = "CARRIER_NOT_CONFIGURED"
MALFORMED_REQUIRED_CONFIGURATION = "MALFORMED_REQUIRED_CONFIGURATION"
MISSING_REQUIRED_CONFIGURATION = "MISSING_REQUIRED_CONFIGURATION"

# Declared order, not detection order - mirrors validation.py's
# _CANONICAL_CODE_ORDER. ASSUMPTIONS.md, "A missing configuration value and a
# malformed one are different reason codes."
_CANONICAL_CODE_ORDER = (
    CARRIER_NOT_CONFIGURED,
    MALFORMED_REQUIRED_CONFIGURATION,
    MISSING_REQUIRED_CONFIGURATION,
)


def _is_boolean(value: Any) -> bool:
    return isinstance(value, bool)


def _is_valid_day_count(value: Any) -> bool:
    # bool is a subclass of int - excluded explicitly, or True/False would
    # pass as 1/0. Zero itself is valid (ASSUMPTIONS.md, "A day count of zero
    # is a valid configuration, not a malformed one").
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


# Every value with no legitimate absent state: missing the key refuses with
# MISSING_REQUIRED_CONFIGURATION, present but failing is_valid refuses with
# MALFORMED_REQUIRED_CONFIGURATION. The two SIU thresholds are not here - see
# _resolve_optional_thresholds.
_REQUIRED_FIELDS: tuple[tuple[str, str, Any], ...] = (
    ("claimant_name_required", "claimant name", _is_boolean),
    ("claimant_contact_required", "claimant contact", _is_boolean),
    ("recognized_policy_number_prefixes", "recognized policy-number prefixes", bool),
    ("window_days", "duplicate match window", _is_valid_day_count),
)

_OPTIONAL_THRESHOLD_FIELDS = (
    ("late_reporting_threshold_days", "late reporting threshold"),
    ("recent_inception_threshold_days", "recent policy inception threshold"),
)


def resolve_carrier_configuration(
    carrier_code: str, rules_source: Mapping[str, Mapping[str, Any]]
) -> CarrierConfigurationResult:
    entry = rules_source.get(carrier_code)
    if entry is None:
        return CarrierConfigurationResult(
            "REFUSED", rejections=(ConfigurationRejection(CARRIER_NOT_CONFIGURED),)
        )

    rejections = _check_required_fields(entry)
    thresholds, threshold_rejections = _resolve_optional_thresholds(entry)
    rejections += threshold_rejections
    if rejections:
        return CarrierConfigurationResult("REFUSED", rejections=tuple(_canonical_order(rejections)))
    return CarrierConfigurationResult("RESOLVED", rules=_build_rules(entry, thresholds))


def _build_rules(entry: Mapping[str, Any], thresholds: dict[str, int | None]) -> CarrierRules:
    return CarrierRules(
        claimant_name_required=entry["claimant_name_required"],
        claimant_contact_required=entry["claimant_contact_required"],
        recognized_policy_number_prefixes=frozenset(entry["recognized_policy_number_prefixes"]),
        late_reporting_threshold_days=thresholds["late_reporting_threshold_days"],
        recent_inception_threshold_days=thresholds["recent_inception_threshold_days"],
        window_days=entry["window_days"],
    )


def _check_required_fields(entry: Mapping[str, Any]) -> list[ConfigurationRejection]:
    rejections = []
    for key, field, is_valid in _REQUIRED_FIELDS:
        if key not in entry:
            rejections.append(ConfigurationRejection(MISSING_REQUIRED_CONFIGURATION, field))
        elif not is_valid(entry[key]):
            rejections.append(ConfigurationRejection(MALFORMED_REQUIRED_CONFIGURATION, field))
    return rejections


def _resolve_optional_thresholds(
    entry: Mapping[str, Any],
) -> tuple[dict[str, int | None], list[ConfigurationRejection]]:
    resolved: dict[str, int | None] = {}
    rejections = []
    for key, field in _OPTIONAL_THRESHOLD_FIELDS:
        value = entry.get(key)
        if value is None:
            resolved[key] = None
        elif _is_valid_day_count(value):
            resolved[key] = value
        else:
            # No entry for key: read only from the RESOLVED path below, which
            # is unreachable whenever a rejection was appended.
            rejections.append(ConfigurationRejection(MALFORMED_REQUIRED_CONFIGURATION, field))
    return resolved, rejections


def _canonical_order(rejections: list[ConfigurationRejection]) -> list[ConfigurationRejection]:
    return sorted(rejections, key=lambda r: (_CANONICAL_CODE_ORDER.index(r.code), r.field))
