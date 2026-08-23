Feature: Jurisdiction date resolution

  As a claims intake system operating in more than one U.S. timezone
  I need every UTC instant converted to a calendar date in the jurisdiction's
  own timezone before any domain rule receives it
  So that a notice is never judged against a date that depends on server
  local time, a single hardcoded zone, or the UTC calendar day

  # This function has exactly one job: given a timezone-aware UTC instant and
  # an IANA timezone name, return the calendar date in that zone. It does not
  # decide which zone a given notice gets - that lookup (risk location,
  # mailing address, or carrier configuration) is item 5c's, not this one's.
  # ASSUMPTIONS.md, "The jurisdiction timezone is a parameter of the
  # conversion, not a constant in it."

  # Getting this wrong in either direction produces a wrong
  # LOSS_DATE_IN_FUTURE determination on a field that already blocks intake
  # today: a zone behind the true jurisdiction produces false positives, and
  # using the UTC calendar date directly produces the inverse error,
  # accepting a date that is genuinely still in the future locally.
  # ASSUMPTIONS.md, "Timezone-correct 'now.'"

  # Rules 1 and 3 below fix the timezone to America/New_York because each is
  # about a different axis - local-vs-UTC divergence, then the offset change
  # within one zone - and holding the zone constant keeps that axis isolated.
  # Rule 2 is the one that varies the zone, because reading it as a parameter
  # rather than assuming Eastern is its entire subject. Florida's western
  # panhandle - Escambia, Santa Rosa, Okaloosa, and most of Walton - is
  # America/Chicago; the rest of the state is America/New_York.

  Rule: An instant resolves to the calendar date in the jurisdiction's timezone, which can differ from the UTC calendar date

    # An instant at 01:00 Eastern does not discriminate: 01:00 America/New_York
    # is always 05:00 or 06:00 UTC the same day, so the local and UTC dates
    # agree regardless of whether the timezone is honored at all. The first
    # row below is the instant that does discriminate - early enough in UTC
    # that Eastern is still on the previous day. The second row is late
    # enough in Eastern that it has already crossed into the next UTC day.
    # Between them, an implementation returning the UTC calendar date instead
    # of the local one is wrong on both rows, in the same direction.
    # ASSUMPTIONS.md, "Timezone-correct 'now,'" corrected 2026-08-23.
    Scenario Outline: An instant resolves to the calendar date in the jurisdiction's timezone, which can differ from the UTC calendar date
      Given the jurisdiction timezone is "America/New_York"
      When the instant <instant> is resolved to a calendar date
      Then the resolved date is <resolved_date>

      Examples:
        | instant              | resolved_date |
        | 2026-06-11T01:00Z    | 2026-06-10    |
        | 2026-06-21T02:00Z    | 2026-06-20    |

  Rule: The jurisdiction's timezone is a parameter the resolution reads, not a zone it assumes

    # The same instant, resolved under each of Florida's two timezones,
    # produces two different dates - Miami's and Pensacola's. A plain
    # scenario, not an outline, so every value below - the repeated instant,
    # both timezone names, and both resolved dates - is independently
    # reachable by mutation rather than sitting in a fixed Given an outline
    # would never mutate (docs/harness-findings.md, "Mutation cannot see a
    # fixed Given"). An implementation that hardcodes America/New_York passes
    # every scenario in the rule above and fails only here.
    Scenario: The same instant resolves to a different jurisdiction date depending on which timezone applies
      When the instant "2026-06-11T04:30Z" is resolved to a calendar date in the jurisdiction timezone "America/New_York"
      Then the resolved date is "2026-06-11"
      When the instant "2026-06-11T04:30Z" is resolved to a calendar date in the jurisdiction timezone "America/Chicago"
      Then the resolved date is "2026-06-10"

  Rule: The UTC offset in effect for a date, not proximity to a DST transition, is what can move the resolved date across a boundary

    # Neither of the two 2026 Eastern transitions sits anywhere near a local
    # midnight - spring forward runs 02:00 -> 03:00 local on 2026-03-08, fall
    # back runs 02:00 -> 01:00 local on 2026-11-01, both hours away from the
    # date changing - so no instant crossing either transition instant can
    # change which calendar date it resolves to. What moves a resolved date
    # is a change in which offset is in effect, which is why the four rows
    # below hold the same UTC wall-clock time steady at 04:30 across a winter
    # row (EST, UTC-5) and a summer row (EDT, UTC-4) and land on different
    # sides of local midnight only because the offset differs, then bracket
    # each with the minute on the other side of that same local midnight.
    # ASSUMPTIONS.md, "Timezone-correct 'now,'" corrected 2026-08-23, which
    # also records why the spring-forward gap and the fall-back ambiguous
    # hour are both real and both irrelevant here: a UTC instant can never
    # land in the skipped hour, and both readings of the repeated hour fall
    # on the same calendar date.
    Scenario Outline: The resolved date crosses local midnight when the UTC offset places it there, in either season
      Given the jurisdiction timezone is "America/New_York"
      When the instant <instant> is resolved to a calendar date
      Then the resolved date is <resolved_date>

      Examples:
        | instant              | resolved_date |
        | 2026-01-15T04:30Z    | 2026-01-14    |
        | 2026-01-15T05:01Z    | 2026-01-15    |
        | 2026-07-15T03:59Z    | 2026-07-14    |
        | 2026-07-15T04:30Z    | 2026-07-15    |
