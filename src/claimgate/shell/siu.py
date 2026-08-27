"""When a notice's SIU indicators are evaluated, and what gets written down.

Its own module rather than a branch inside each endpoint. ASSUMPTIONS.md's item
5f decision 1 puts the evaluation on *every* transition into TRIAGED, on both
paths, and one function called from both is how that stays a single rule instead
of two implementations free to drift apart.

**Called inside the transaction that triages**, after validation has returned no
blocker, and never on a pend, a refusal or an idempotent replay - none of those
transitions, and a pended notice is an incomplete intake record rather than a
claim. The events and the transition they belong to therefore commit or roll
back together: a notice that is TRIAGED with no evaluation beside it is not a
state either caller can leave behind.

**Two instants, deliberately not the same one** (decision 2). The interval late
reporting measures is counted from the jurisdiction date of the notice's own
receipt instant - notice given is notice received, and a pend is the carrier
asking for more rather than the reporter arriving late - while `evaluated_at` is
the instant of the transaction doing the evaluating. They coincide on the intake
path and do not on the resolution path, where collapsing them would over-report
lateness on every notice that ever sat pended.

**One instant, but not one timezone** (item 5g, ASSUMPTIONS.md 2026-08-26).
Decision 2 fixed the instant and said nothing about the zone that instant is
converted under, a gap that only opens once the zone comes from the property's
state rather than from the submission. The jurisdiction handed in here is the
one the *calling transaction* selected from the notice's merged current view, so
a reviewer who supplies the property state makes an interval computable that was
not computable at receipt. Where none was selected the caller hands in None and
the interval has no day to count to, which the indicator records as
NOT_EVALUATED with its own reason rather than as a negative.

**The rules are the ones the triaging transaction resolved** (decision 6), handed
in by the caller rather than read again here, so a threshold a carrier configured
while the notice sat pended is the one its evaluation uses and the number stored
beside the outcome is the number that produced it.

Nothing here decides anything about a claim or a claimant. An indicator is a
factual observation with a code, the arithmetic is domain/siu.py's and is not
repeated, and the two names below are the trail's own vocabulary - the same two
indicators siu_indicators.feature specifies and no others.
"""

from datetime import datetime

from claimgate.domain.models import Candidate, CarrierRules, Jurisdiction, SiuIndicators
from claimgate.domain.ruleset import RULESET_VERSION
from claimgate.domain.siu import compute_siu_indicators
from claimgate.shell.records import SiuIndicatorObservation
from claimgate.shell.rules import resolve_today
from claimgate.shell.store import NoticeStore

LATE_REPORTING = "late_reporting"
RECENT_POLICY_INCEPTION = "recent_policy_inception"


def record_evaluation(
    store: NoticeStore, notice_id: str, *, candidate: Candidate, rules: CarrierRules,
    received_at: datetime, jurisdiction: Jurisdiction | None, evaluated_at: datetime,
) -> None:
    """`received_at` is the notice's receipt instant and `evaluated_at` this
    transaction's own; passing one value for both is correct on the intake path
    alone, where they are the same event."""
    indicators = compute_siu_indicators(
        candidate,
        resolve_today(received_at, jurisdiction),
        rules.late_reporting_threshold_days,
        rules.recent_inception_threshold_days,
    )
    store.append_siu_events(
        notice_id, _observations(indicators, rules),
        ruleset_version=RULESET_VERSION, evaluated_at=evaluated_at,
    )


def _observations(
    indicators: SiuIndicators, rules: CarrierRules
) -> tuple[SiuIndicatorObservation, ...]:
    """Both indicators every time, FALSE and NOT_EVALUATED included (decision
    3), each beside the threshold its own evaluation was given - null where the
    carrier configured none, because an absent rule and a zero-day one are
    different facts."""
    return (
        SiuIndicatorObservation(
            LATE_REPORTING, indicators.late_reporting, rules.late_reporting_threshold_days
        ),
        SiuIndicatorObservation(
            RECENT_POLICY_INCEPTION,
            indicators.recent_policy_inception,
            rules.recent_inception_threshold_days,
        ),
    )
