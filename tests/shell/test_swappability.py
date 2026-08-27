"""The two proofs PHASE2_DESIGN.md's "Swappability proofs" section owes.

Both are demo artifacts proving the *absence* of hardcoding, not features, and
both are tests rather than feature files: a fictional second jurisdiction and an
alternative carrier set are not business rules of this product, and a spec that
stated them would be stating something no deployment is entitled to.

**What phase 1 already settled, and what these therefore have to prove.** Every
carrier-varying value is caller-supplied with no default, so a carrier difference
has nothing left in the domain to condition on; the domain half of the claim is
done. What was unproven until item 5g is the adapter half - that the shell can
carry a second carrier set and a second jurisdiction ruleset through to those
parameters without a branch of its own. Each test below therefore changes exactly
one mapping and nothing else: same function, same carrier, same instant, same
fields.

**The jurisdiction proof inherits an obligation, and it is the reason it is
written the way it is.** features/notice_intake.feature's former Rule 5 varied
America/New_York against America/Chicago and asserted that the same submission
instant is judged differently under each; it was deleted when the timezone left
the submission surface, and PHASE2_DESIGN.md re-homed that discrimination here.
So the fictional jurisdiction's entry has to hold a timezone that yields a
*different calendar date for the same instant*, and the test has to assert the
two different outcomes that follow. A fixture proving only that a second entry
can exist would not discharge it.
"""

from dataclasses import replace
from datetime import UTC, datetime

from claimgate.domain.models import CarrierIdentity, FutureDatedLossResult
from claimgate.shell.messages import SubmitNoticeResponse
from claimgate.shell.records import NoticeRecord
from claimgate.shell.store import NoticeStore
from tests.shell.support import DEFAULT_FIELDS, JURISDICTIONS, VALID_RULES, Submitter

# A carrier set with no code in common with the shipped reference, so nothing
# below can pass because a code happened to appear in both.
_ANOTHER_CARRIER_SET = {
    "WXYZ": CarrierIdentity(name="Substituted Carrier W", naic=20001, naic_group=None),
}
_ANOTHER_CARRIERS_RULES = {"WXYZ": VALID_RULES}

# 2026-06-11T02:30Z is 22:30 on 2026-06-10 in Florida and 16:30 on 2026-06-11 in
# Kiritimati, so the two entries put the same instant on different calendar
# days. ZZ is user-assigned in ISO 3166-1 and can never name a real
# jurisdiction. Pacific/Kiritimati is a real zone because ZoneInfo has to
# resolve it; what is fictional is the jurisdiction, not the timezone.
_TWO_JURISDICTIONS = {
    "FL": {"timezone": "America/New_York"},
    "ZZ": {"timezone": "Pacific/Kiritimati"},
}
_SUBMITTED_AT = datetime(2026, 6, 11, 2, 30, tzinfo=UTC)
_LOSS_ON_THE_DAY_THEY_DISAGREE = "2026-06-11"


def test_a_substituted_carrier_set_is_administered_exactly_as_the_shipped_one_is(
    store: NoticeStore, submit: Submitter
) -> None:
    shipped = submit()

    substituted = submit(
        carrier_code="WXYZ",
        carrier_identity_reference=_ANOTHER_CARRIER_SET,
        carrier_rules_source=_ANOTHER_CARRIERS_RULES,
    )

    assert _outcome(substituted) == _outcome(shipped)
    assert store.get_audit_trail(substituted.notice_id) != ()


def test_the_shipped_carrier_is_unknown_to_a_deployment_that_does_not_administer_it(
    store: NoticeStore, submit: Submitter
) -> None:
    # Without this the test above would pass over a reference nothing consults.
    # AAAA is administered under the shipped set and is not under this one, and
    # the only thing that differs between the two calls is which set was handed
    # in - not the code, not the rules, not the fields.
    refused = submit(
        carrier_code="AAAA",
        carrier_identity_reference=_ANOTHER_CARRIER_SET,
        carrier_rules_source={"AAAA": VALID_RULES},
    )

    assert refused.status == 400
    assert refused.notice_id is None
    assert store.count_notices() == 0


def test_a_second_jurisdictions_entry_supplies_the_calendar_the_notice_is_judged_against(
    store: NoticeStore, submit: Submitter
) -> None:
    fields = replace(
        DEFAULT_FIELDS, loss_date=_LOSS_ON_THE_DAY_THEY_DISAGREE, property_state="FL"
    )

    under_florida = submit(
        submitted_at=_SUBMITTED_AT, jurisdiction_reference=_TWO_JURISDICTIONS, fields=fields
    )
    under_the_second = submit(
        submitted_at=_SUBMITTED_AT,
        jurisdiction_reference=_TWO_JURISDICTIONS,
        fields=replace(fields, property_state="ZZ"),
    )

    # One instant, one loss date, two calendars: 2026-06-11 is still ahead of
    # Florida's today and has already arrived in the second jurisdiction's.
    assert under_florida.state == "PENDED"
    assert [b.code for b in under_florida.blockers] == ["LOSS_DATE_IN_FUTURE"]
    assert under_the_second.state == "TRIAGED"
    assert under_the_second.blockers == ()
    # The state and the blockers alone do not discharge the obligation, and
    # this assertion is here because writing it without them did not: a notice
    # whose property state selects *no* jurisdiction also reaches TRIAGED with
    # no blockers, so an implementation ignoring the supplied map entirely made
    # the two assertions above pass. FALSE is the determination only a calendar
    # can produce - NOT_EVALUATED is what an absent entry gives - and the
    # marking says the entry was found rather than missed.
    assert _determination(store, under_the_second) == FutureDatedLossResult("FALSE")
    assert _marking(store, under_the_second) is None


def test_a_jurisdiction_the_deployment_holds_no_entry_for_is_marked_not_refused(
    store: NoticeStore, submit: Submitter
) -> None:
    # The other half of the same seam: the map decides which states are
    # supported, so a state supported under the two-entry map above is not
    # under the shipped one - and is marked rather than refused either way.
    supported = submit(fields=replace(DEFAULT_FIELDS, property_state="ZZ"),
                       jurisdiction_reference=_TWO_JURISDICTIONS)
    unsupported = submit(fields=replace(DEFAULT_FIELDS, property_state="ZZ"),
                         jurisdiction_reference=JURISDICTIONS)

    assert _marking(store, supported) is None
    assert _marking(store, unsupported) == "jurisdiction_unsupported"
    assert unsupported.status == 201
    assert unsupported.state == "TRIAGED"


def _outcome(response: SubmitNoticeResponse) -> tuple[object, ...]:
    """Everything the shell decided, minus the two things that are allowed to
    differ: the identifier it minted and the carrier it attributed the notice
    to. A carrier difference reaching anything else is the leak these tests
    exist to catch."""
    return (
        response.status, response.state, response.blockers,
        response.severity, response.queue, response.received_at,
    )


def _marking(store: NoticeStore, response: SubmitNoticeResponse) -> str | None:
    return _stored(store, response).jurisdiction_marking


def _determination(
    store: NoticeStore, response: SubmitNoticeResponse
) -> FutureDatedLossResult | None:
    return _stored(store, response).future_dated_loss


def _stored(store: NoticeStore, response: SubmitNoticeResponse) -> NoticeRecord:
    record = store.get_notice(response.notice_id)
    assert record is not None
    return record
