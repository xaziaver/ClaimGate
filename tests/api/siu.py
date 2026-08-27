"""Thin, stable test API over the SIU indicator domain area and its trail.

The domain call below is what siu_indicators.feature exercises: the arithmetic,
with every input handed in.

The rest is item 5f's, and it is deliberately the whole read surface phase 2
has. ASSUMPTIONS.md's item 5f decision 4: no route to these events exists until
an authenticated identity exists to log a read against, so the only way to see
one is from here, and features/siu_separation.feature's scenarios are the only
readers. The leak negatives in the same spec need two more things - the names an
ordinary surface must never mention, and the serialized form of the surfaces
themselves - and both come from the code that defines them rather than from
literals a step file would have to keep in step by hand.
"""

from collections.abc import Mapping
from datetime import date
from typing import Any

from claimgate.domain.models import Candidate, SiuIndicators
from claimgate.domain.siu import (
    NO_CONTINUOUS_COVERAGE_DATE,
    NO_JURISDICTION_DATE,
    NO_THRESHOLD_CONFIGURED,
)
from claimgate.domain.siu import compute_siu_indicators as _compute_siu_indicators
from claimgate.shell.records import AuditEntry, SiuIndicatorEvent
from claimgate.shell.serialization import (
    serialize_audit_entry,
    serialize_notice_view,
    serialize_response,
)
from claimgate.shell.siu import LATE_REPORTING, RECENT_POLICY_INCEPTION
from claimgate.shell.store import NoticeStore

LATE_REPORTING_INDICATOR = LATE_REPORTING
RECENT_POLICY_INCEPTION_INDICATOR = RECENT_POLICY_INCEPTION
SIU_INDICATOR_NAMES = (LATE_REPORTING, RECENT_POLICY_INCEPTION)
# The complete set of SIU indicator reason codes, taken from the module that
# declares them so the leak negatives cannot fall behind it. This set is not
# the future-dated-loss determination's, which contains a code of the same
# spelling as the third member here and is a different enumeration (CLAUDE.md).
SIU_REASON_CODES = (NO_THRESHOLD_CONFIGURED, NO_CONTINUOUS_COVERAGE_DATE, NO_JURISDICTION_DATE)


def siu_indicators(
    *,
    now: date,
    loss_date: date,
    late_reporting_threshold_days: int | None,
    recent_inception_threshold_days: int | None,
    continuous_coverage_date: date | None = None,
) -> SiuIndicators:
    candidate = Candidate(loss_date=loss_date, continuous_coverage_date=continuous_coverage_date)
    return _compute_siu_indicators(
        candidate,
        now,
        late_reporting_threshold_days,
        recent_inception_threshold_days,
    )


def siu_indicator_events(store: NoticeStore, notice_id: str) -> tuple[SiuIndicatorEvent, ...]:
    """One notice's trail, in the order it was written. The restricted read, and
    the only one there is."""
    return store.get_siu_events(notice_id)


def all_siu_indicator_events(store: NoticeStore) -> tuple[SiuIndicatorEvent, ...]:
    """Every event this deployment holds. A scenario asking what was recorded
    "in all" is asking about the database and not about one notice - a stray
    evaluation against some other notice is exactly what it exists to catch."""
    return store.list_siu_events()


def serialized_response(response: Any) -> Mapping[str, Any]:
    return serialize_response(response)


def serialized_notice_view(view: Any) -> Mapping[str, Any]:
    return serialize_notice_view(view)


def serialized_audit_entry(entry: AuditEntry) -> Mapping[str, Any]:
    return serialize_audit_entry(entry)
