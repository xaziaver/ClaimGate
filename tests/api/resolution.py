"""Thin, stable test API over the resolution shell.

The reads here exist because features/resolution.feature asserts things no
response carries: what each payload record kept for a notice holds, what the
notice says once those records are overlaid, and the two instants
PHASE2_DESIGN.md's tolling paragraph wants recorded on the notice itself.

payload_reference is exposed for one reason: a step that asks which arrival a
record in a given position came from has to answer it against what actually
arrived, not against the position it just used to select the record. The hash is
the design's own identity for a payload, so the step names the arrival and
checks the record references it.
"""

from claimgate.shell.messages import NoticeFields, ResolutionResponse
from claimgate.shell.records import NoticeRecord, PayloadRecord, payload_reference
from claimgate.shell.resolution import merged_view, notice_records, resolve_notice
from claimgate.shell.store import NoticeStore


def notice_record(store: NoticeStore, notice_id: str) -> NoticeRecord | None:
    """The stored notice, not the retrieval view: the view is what
    GET /notices/{id} shows, and pended_at and resolved_at are not in it."""
    return store.get_notice(notice_id)


__all__ = [
    "NoticeFields",
    "NoticeRecord",
    "NoticeStore",
    "PayloadRecord",
    "ResolutionResponse",
    "merged_view",
    "notice_record",
    "notice_records",
    "payload_reference",
    "resolve_notice",
]
