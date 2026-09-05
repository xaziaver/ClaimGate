"""Thin, stable test API over the policy identification domain area."""

from claimgate.domain.policy_identification import IdentifierSufficiency
from claimgate.domain.policy_identification import (
    evaluate_identifier_sufficiency as _evaluate_identifier_sufficiency,
)


def evaluate_identifier_sufficiency(
    policy_number: str, insured_name: str, risk_postal_code: str
) -> IdentifierSufficiency:
    return _evaluate_identifier_sufficiency(policy_number, insured_name, risk_postal_code)
