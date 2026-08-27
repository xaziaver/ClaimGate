"""The label a decision this package produced is recorded under.

PHASE2_DESIGN.md's audit-log schema names `ruleset_version` "a hand-declared
semantic label ... for the domain rules that produced a SYSTEM decision", and
ASSUMPTIONS.md's item 5f ruleset-version decision settles what it names: the
version of this package - the code that evaluated the rule - and never the
carrier's configured numbers, which have no version and do not acquire one for
this. Reproducing a recorded evaluation comes from storing the input that
evaluation applied beside its outcome, not from versioning configuration.

Date-stamped rather than semantic because the question a stored row has to
answer a year later is which rules were in force on the day it was written, and
a date answers that without anyone holding a changelog beside it.

**Any commit that changes a rule's behaviour under `src/claimgate/domain/` bumps
this label.** No gate can enforce that, which is why it is written down here and
in CLAUDE.md: a stale label makes every row written after it a claim about rules
that were not the ones applied.
"""

RULESET_VERSION = "2026-08-27"
