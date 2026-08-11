"""Thin, stable test API over the duplicate-claim detection domain area."""

from dataclasses import dataclass
from datetime import date

from claimgate.domain.duplicates import find_duplicates as _find_duplicates
from claimgate.domain.models import Candidate, DuplicateMatchResult, ExistingClaim


@dataclass(frozen=True)
class ExistingClaimRecord:
    claim_id: str
    policy_number: str
    loss_date: date
    loss_type: str


def find_duplicates(
    *,
    policy_number: str,
    loss_date: date,
    loss_type: str,
    notice_type: str,
    window_days: int,
    existing_claims: list[ExistingClaimRecord],
) -> DuplicateMatchResult:
    candidate = Candidate(
        policy_number=policy_number,
        loss_date=loss_date,
        loss_type=loss_type,
        notice_type=notice_type,
    )
    claims = [
        ExistingClaim(
            claim_id=record.claim_id,
            policy_number=record.policy_number,
            loss_date=record.loss_date,
            loss_type=record.loss_type,
        )
        for record in existing_claims
    ]
    return _find_duplicates(candidate, claims, window_days)
