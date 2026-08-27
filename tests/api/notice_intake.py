"""Thin, stable test API over the notice-intake shell.

The two configuration sources are re-exported here for the reason
tests/api/siu.py re-exports the SIU vocabulary: a step file holding its own copy
of the shipped map would keep passing after the shipped one changed. Both are
ordinary values the caller passes on every call - neither has a default inside
the domain - so a test that wants a different deployment hands over a different
mapping rather than patching a module.
"""

from claimgate.domain.carrier_identity import CARRIER_IDENTITY_REFERENCE as _IDENTITY
from claimgate.domain.jurisdiction import JURISDICTION_REFERENCE as _JURISDICTIONS
from claimgate.shell.messages import NoticeFields, NoticeView, SubmitNoticeResponse
from claimgate.shell.notice_intake import get_notice, submit_notice
from claimgate.shell.store import NoticeStore

# Acceptance steps open one database per scenario. ":memory:" keeps a scenario's
# store private to its own connection and gone when that connection closes -
# nothing a spec asserts depends on a file existing (ASSUMPTIONS.md,
# "Persistence engine"; the path is a constructor argument with no default).
IN_MEMORY_DATABASE = ":memory:"
CARRIER_IDENTITY_REFERENCE = _IDENTITY
JURISDICTION_REFERENCE = _JURISDICTIONS

__all__ = [
    "CARRIER_IDENTITY_REFERENCE",
    "IN_MEMORY_DATABASE",
    "JURISDICTION_REFERENCE",
    "NoticeFields",
    "NoticeStore",
    "NoticeView",
    "SubmitNoticeResponse",
    "get_notice",
    "submit_notice",
]
