---
name: gherkin-specs
description: Drafting and reviewing ClaimGate acceptance specifications — the naming prohibitions, the threshold rule, and the four measured shape constraints that decide whether a mutant dies or survives and costs a human approval. Use whenever writing, editing, or reviewing a .feature file, or before estimating the blast radius of a spec change.
---

# Writing a specification here

The spec is the human's artifact. You draft it; a human approves it. It states
business behaviour a claims manager would recognise, never implementation.

## Prohibitions

- No scenario names a function, class, table, or column.
- No scenario asserts an internal structure. Assert what the business observes.
- Example data must look real to a claims manager. `HO-1234567`, not `X1`.
- Reason-code enumerations are closed and scoped to one feature. A new
  enumeration is a business decision — escalate, do not invent one.
- Every threshold needs a scenario on **each side** of it. A threshold exercised
  in only one of its states is an asymmetry, and it is the defect this rule
  exists to catch.

## Measure the blast radius before drafting

    GAUNTLET_SRC=~/Code/agent-gauntlet/src .venv/bin/python \
        .claude/skills/gherkin-specs/scripts/measure_mutants.py features/your_file.feature

The project `.venv` does not install `gauntlet` — it is not in
`requirements-dev.txt` — so `GAUNTLET_SRC` points the script at the agent-gauntlet
checkout's `src/`; without it the import fails and the script says so.

Needs no approval and no gate run. Report counts **as measured**. Predicting a
survivor count is a different act from measuring one; both are useful, and a
guess reported as a measurement destroys the signal. Survivors cannot be known
until the spec is approved and step definitions exist.

## The four shape constraints

These are not style. They decide whether a mutant dies or survives, and every
survivor costs a human approval that must carry its own equivalence argument.

**1. Every value the specification is about belongs in an `Examples` cell.**
Background steps are never mutated, and a fixed `Given` above an `Examples` table
is never mutated either. A value stated only there is asserted by nothing — the
spec claims the rule while the harness protects none of it. This has already
happened once: a draft raised the mutant count while the actual subject of the
item sat outside mutation's reach entirely.

**2. Assert the value received, not merely that the operation succeeded.**
A row asserting only `accepted` leaves its value column inert: `true` mutates to
`false`, both are accepted, the mutant survives. A row asserting the value that
came out kills the same mutant.

**3. Prefer one table mixing outcomes over separate same-outcome tables.**
The engine picks a substitution from the column of the row that differs most
elsewhere, on the explicit theory that such a row expects a different outcome. In
a mixed table that choice kills the mutant. In a same-outcome table no
discriminating alternative exists and **every** swap is inert.

**4. Keep unavoidably same-outcome rows together in one scenario.**
`gauntlet mutant approve` scopes only by feature file and `--scenario`, so
survivors spread across scenarios cannot be given separate reasons. Group them so
one approval reason covers one equivalence argument.

## How a value is actually mutated

Knowing this is how you predict inertness:

- `true`/`false`, `yes`/`no`, `on`/`off` — negated.
- Numbers — incremented by one at matching decimal precision (`60` becomes `61`).
- Everything else — swapped for a value from the same column in another row,
  most-different row first; if no alternative exists, the marker `_gauntlet` is
  appended.
- An empty cell has no alternative of its own and takes the marker.

## Before handing a draft back

- Every threshold exercised on both sides?
- Every configured value reachable by mutation?
- Every accepting row asserting what it received?
- Measured count and per-scenario breakdown reported as measured?
- Anything the queue item left underspecified named rather than guessed?
