"""Thin, stable test API over the carrier-configuration domain area."""

from collections.abc import Mapping
from typing import Any

from claimgate.domain.carrier_configuration import (
    resolve_carrier_configuration as _resolve_carrier_configuration,
)
from claimgate.domain.models import CarrierConfigurationResult


def resolve_carrier_configuration(
    carrier_code: str, rules_source: Mapping[str, Mapping[str, Any]]
) -> CarrierConfigurationResult:
    return _resolve_carrier_configuration(carrier_code, rules_source)
