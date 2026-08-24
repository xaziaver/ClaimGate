"""Carrier identity reference: carrier_code to carrier name, NAIC company, and NAIC group.

A static, version-controlled file, separate from the per-carrier rules file
(domain/carrier_configuration.py) that holds the six caller-supplied
configuration values (ASSUMPTIONS.md, "A carrier configuration crosses into
the domain already resolved"). Identity and rules stay physically separate
so carrier_code cannot look branchable (PHASE2_DESIGN.md, "Carrier
reference"). carrier_code is envelope, not notice content, validated against
this list for attribution only and never branched on: this module answers
only "is this carrier one this deployment administers," nothing else.

Item 5c's 400 on an unknown or malformed carrier_code validates against this
reference, not the rules file (ASSUMPTIONS.md, "Item 5c's 400 validates
against the identity reference, not the rules source"). A malformed code is
definitionally absent from this reference - there is no separate malformed
check.
"""

from collections.abc import Mapping

from claimgate.domain.models import CarrierIdentity, CarrierIdentityResult

# Every value in this table is synthetic (PHASE2_DESIGN.md, "Carrier
# reference") and a real deployment substitutes its own at integration. The
# null naic_group on CCCC is deliberate and must survive substitution: a
# member-owned reciprocal may be grouped by management rather than
# ownership, so a shared administrator does not imply a shared group.
CARRIER_IDENTITY_REFERENCE: Mapping[str, CarrierIdentity] = {
    "AAAA": CarrierIdentity(name="Placeholder Carrier A", naic=10001, naic_group=4001),
    "BBBB": CarrierIdentity(name="Placeholder Carrier B", naic=10002, naic_group=4001),
    "CCCC": CarrierIdentity(name="Placeholder Carrier C", naic=10003, naic_group=None),
}


def resolve_carrier_identity(
    carrier_code: str, reference: Mapping[str, CarrierIdentity]
) -> CarrierIdentityResult:
    identity = reference.get(carrier_code)
    if identity is None:
        return CarrierIdentityResult("REFUSED")
    return CarrierIdentityResult("RESOLVED", identity=identity)
