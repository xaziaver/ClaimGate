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

  # Two rules below fix the timezone to America/New_York, because each is
  # about a different axis - local-vs-UTC divergence, then the offset change
  # within one zone - and holding the zone constant keeps that axis isolated.
  # The other two vary it: one proves a well-formed zone changes the result
  # rather than being ignored, the other proves an unrecognized zone refuses
  # rather than silently falling back to the first two rules' constant.
  # Florida's western panhandle - Escambia, Santa Rosa, Okaloosa, and most of
  # Walton - is America/Chicago; the rest of the state is America/New_York.

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
    # produces two different dates - Miami's and Pensacola's. An outline now,
    # reversing the earlier choice here: a plain scenario's quoted literals
    # are mutable but vacuous - the marker lands outside the closing quote,
    # which no step definition in this project's house style can bind, so the
    # mutant dies at step resolution before the domain is ever called, and a
    # wrong implementation would have been killed identically
    # (docs/harness-findings.md, "Acceptance mutation does not see
    # everything," corrected 2026-08-23). An Examples column's sibling swap
    # stays well-formed - America/New_York for America/Chicago,
    # 2026-06-11 for 2026-06-10 - so it reaches the domain and is killed by
    # an actual mismatch instead. The instant stays fixed in the When step
    # rather than becoming a third column: it was one of the plain
    # scenario's six vacuous mutants, and an outline never mutates a fixed
    # value regardless, so nothing real is given up. An implementation that
    # hardcodes America/New_York passes every scenario in the rule above and
    # fails only here.
    Scenario Outline: The same instant resolves to a different jurisdiction date depending on which timezone applies
      When the instant "2026-06-11T04:30Z" is resolved to a calendar date in the jurisdiction timezone <timezone>
      Then the resolved date is <resolved_date>

      Examples:
        | timezone          | resolved_date |
        | America/New_York  | 2026-06-11    |
        | America/Chicago   | 2026-06-10    |

  Rule: An unrecognized jurisdiction timezone refuses the resolution rather than falling back to a default

    # Extends the rule above: reading the zone as a parameter means an
    # unusable one has to be rejected, not silently replaced with
    # America/New_York or any other constant - the same shape item 5a
    # settled one layer down, where a malformed configuration value is
    # refused and named rather than repaired. The well-formed row is what a
    # fallback would produce; the unrecognized row is what must happen
    # instead, and both sit in one table so a substitution between them is
    # an outcome mismatch, not a same-outcome swap. ASSUMPTIONS.md, "An
    # unrecognized jurisdiction timezone is refused, never defaulted."
    Scenario Outline: An unrecognized jurisdiction timezone refuses the resolution rather than falling back to a default
      When the instant "2026-06-11T04:30Z" is resolved to a calendar date in the jurisdiction timezone <timezone>
      Then the result is <outcome>

      Examples:
        | timezone         | outcome                            |
        | America/New_York | 2026-06-11                         |
        | America/NewYork  | JURISDICTION_TIMEZONE_UNRECOGNIZED |

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
