"""Thin, stable test API over the notice-intake shell."""

from claimgate.shell.notice_intake import (
    NoticeFields,
    NoticeView,
    SubmitNoticeResponse,
    get_notice,
    submit_notice,
)
from claimgate.shell.store import NoticeStore

# Acceptance steps open one database per scenario. ":memory:" keeps a scenario's
# store private to its own connection and gone when that connection closes -
# nothing a spec asserts depends on a file existing (ASSUMPTIONS.md,
# "Persistence engine"; the path is a constructor argument with no default).
IN_MEMORY_DATABASE = ":memory:"

__all__ = [
    "IN_MEMORY_DATABASE",
    "NoticeFields",
    "NoticeStore",
    "NoticeView",
    "SubmitNoticeResponse",
    "get_notice",
    "submit_notice",
]
