"""Thin, stable test API over the notice-intake shell."""

from claimgate.shell.notice_intake import (
    NoticeFields,
    NoticeView,
    SubmitNoticeResponse,
    get_notice,
    submit_notice,
)
from claimgate.shell.store import NoticeStore

__all__ = [
    "NoticeFields",
    "NoticeStore",
    "NoticeView",
    "SubmitNoticeResponse",
    "get_notice",
    "submit_notice",
]
