"""Pure identifier-sufficiency rule: whether a notice carries enough to search
for its policy.

PHASE3_DESIGN.md, "Identifiers: search, not fetch", stated by
features/policy_identification.feature and by ASSUMPTIONS.md's 2026-09-05
identifier-sufficiency entry. A notice can be searched if it carries a policy
number, or an insured name together with a risk postal code; otherwise it pends
on POLICY_IDENTIFIERS_INSUFFICIENT naming every absent identifier field, so the
reviewer resolving the pend knows what to ask for. Whitespace is absence and a
present identifier is carried trimmed - validation.py's convention for every
field it checks. Nothing is checked for shape: a mistyped number beside a
correct name and postal code is a search, not a pend, and whether a number
finds a policy is the search's answer (items 7d and 7f).

Not wired until item 7g, which also retires policy_number as a required field;
until then the second arm cannot be reached at intake (PHASE3_DESIGN.md's
2026-09-05 annotation). No decision changes here, so RULESET_VERSION does not.
"""

from dataclasses import dataclass
from typing import Final, Literal

# The two ways a notice can be searchable, in the order a result reports them
# when both hold. The list is every satisfied arm, not a preference: the search
# takes whatever identifiers the notice carries.
POLICY_NUMBER: Final = "POLICY_NUMBER"
INSURED_NAME_AND_POSTAL_CODE: Final = "INSURED_NAME_AND_POSTAL_CODE"

# The one blocker this rule raises - its own closed enumeration of one
# (CLAUDE.md: reason-code enumerations are closed and scoped to one feature).
# POLICY_NOT_MATCHED and POLICY_AMBIGUOUS are the search's outcomes, item 7f's,
# and never this rule's.
POLICY_IDENTIFIERS_INSUFFICIENT: Final = "POLICY_IDENTIFIERS_INSUFFICIENT"

IdentifierSufficiencyValue = Literal["SEARCHABLE", "INSUFFICIENT"]


@dataclass(frozen=True)
class SearchIdentifiers:
    """What the search will carry, trimmed. The insured name and the risk
    postal code travel together or not at all: a name without a postal code is
    not a search input, so beside a policy number it is dropped, not carried."""

    policy_number: str | None = None
    insured_name: str | None = None
    risk_postal_code: str | None = None


@dataclass(frozen=True)
class IdentificationBlocker:
    code: str
    # Every absent identifier field, in the order policy_number, insured_name,
    # risk_postal_code - never only the cheapest completion, which would hide
    # that a name beside the postal code is also a route.
    fields: tuple[str, ...]


@dataclass(frozen=True)
class IdentifierSufficiency:
    # Same convention as the other domain results: arms and search are set
    # only when value is SEARCHABLE, blocker only when it is INSUFFICIENT.
    value: IdentifierSufficiencyValue
    arms: tuple[str, ...] = ()
    search: SearchIdentifiers | None = None
    blocker: IdentificationBlocker | None = None


def evaluate_identifier_sufficiency(
    policy_number: str | None, insured_name: str | None, risk_postal_code: str | None
) -> IdentifierSufficiency:
    """Reads the notice and nothing else: no search runs here."""
    number = _present(policy_number)
    name = _present(insured_name)
    postal = _present(risk_postal_code)
    arms = _satisfied_arms(number, name, postal)
    if not arms:
        return IdentifierSufficiency("INSUFFICIENT", blocker=_blocker(name, postal))
    if INSURED_NAME_AND_POSTAL_CODE not in arms:
        name, postal = None, None
    return IdentifierSufficiency(
        "SEARCHABLE", arms=arms, search=SearchIdentifiers(number, name, postal)
    )


def _satisfied_arms(number: str | None, name: str | None, postal: str | None) -> tuple[str, ...]:
    arms: list[str] = []
    if number is not None:
        arms.append(POLICY_NUMBER)
    if name is not None and postal is not None:
        arms.append(INSURED_NAME_AND_POSTAL_CODE)
    return tuple(arms)


def _blocker(name: str | None, postal: str | None) -> IdentificationBlocker:
    """Reached only with no policy number - a present one is an arm by itself -
    so the number is absent by construction and only the pair is asked. Passing
    it in anyway bred an equivalent code mutant (docs/harness-findings.md, the
    `key=` lambda entry: restructure, do not approve)."""
    named = (("insured_name", name), ("risk_postal_code", postal))
    absent = ("policy_number", *(field for field, value in named if value is None))
    return IdentificationBlocker(POLICY_IDENTIFIERS_INSUFFICIENT, absent)


def _present(value: str | None) -> str | None:
    """Whitespace is absence, and a present value is carried trimmed."""
    stripped = (value or "").strip()
    return stripped or None
