# Phase 1 business rule decisions

## Validation reporting window: 365 days

A claim reported up to 365 days after the loss date is still valid — carriers accept late FNOL.

## SIU late-reporting threshold: 30 days

Deliberately different from the 365-day validation window: validation asks "can we accept this,"
SIU asks "does this smell." A single shared threshold would mean the SIU flag could never fire on
a record that also passes validation — it needs to catch suspicious timing well before a claim
becomes outright unacceptable.

## Recent policy inception threshold: 30 days

A policy that incepted within 30 days of the loss is a standard fraud indicator (new-policy risk).

## Policy number LOB prefixes: HO, AU, CP, CA, GL

Homeowners, personal auto, commercial property, commercial auto, general liability — the lines of
business this carrier actually intakes; anything else is not a recognized policy number.

## Theft low-severity threshold: $500

Theft losses under $500 triage as low severity; at or above, they fall to the standard severity
default like every other non-injury, non-fire loss type.

## Duplicate detection window: 3 days

Same policy, same loss type, and a loss date within 3 days counts as a probable duplicate — tight
enough to avoid false positives on genuinely separate losses.

## LOB-vs-loss-type cross-validation: deferred

Not built in phase 1 (e.g. rejecting `auto_collision` on an `HO` policy) — a real rule, but out of
scope until a later phase.
