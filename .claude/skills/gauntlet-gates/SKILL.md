---
name: gauntlet-gates
description: How the Gauntlet harness behaves when working in ClaimGate — what each gate checks, which commands belong to the agent and which to the human, why a gate is red, and which source files to read when the answer is not here. Use when a gate fails, when estimating what a change will disturb, when a remedy message tells you to run something, or when tempted to read the agent-gauntlet source tree to find out how the harness works.
---

# Working under Gauntlet

**Provenance.** Written against `agent-gauntlet` at the commit recorded in
`scripts/verify.sh`. Every load-bearing claim below is asserted by that script.
Run it before trusting this file. If it fails, this document is stale and the
source wins — fix the document, do not work around it.

## Read this before reading the source

The reason this skill exists: understanding the harness by scanning
`agent-gauntlet/src` costs a large fraction of a session's context every time,
and the answer is usually one of the facts below or one command away. Read at
most the three files named at the bottom, and only for semantics.

For current *state* rather than semantics, ask the tool, not the source:

    gauntlet status --json     # gates, pending approvals, recent activity
    gauntlet spec list         # every discovered spec and whether it is approved
    gauntlet doctor            # environment and toolchain
    cat gauntlet.toml          # the thresholds actually in force

## Commands: whose is whose

Yours: `gauntlet check`, `verify`, `status`, `doctor`, `events`, `spec list`.

The human's, never yours: `gauntlet spec approve`, `mutant approve`,
`mutant prune`, `review`, `lock`.

**One remedy message names the wrong command.** Both the unapproved-spec and the
modified-spec diagnostics tell the reader a human must run `gauntlet lock`. That
is wrong. `gauntlet lock` re-approves the protected config paths — the guardrail
against threshold tampering — and would not approve a spec. The correct command
is `gauntlet spec approve`, and it is the human's. Acting on the message
literally re-baselines the protection and approves nothing. Report and stop.

## Why the acceptance gate is red

It runs three stages in order and returns on the first failure:

1. **Approval.** Every discovered spec must be present in the ledger with a
   matching hash. Any unapproved or modified spec fails here — and because it
   returns immediately, **the scenarios never run and mutation never runs.** A
   newly drafted spec therefore produces `N unapproved or modified spec(s)` and
   no information about whether the spec works. That is expected, not a defect.
2. **Baseline.** The bound scenarios must pass. Collecting nothing is a failure,
   not a pass.
3. **Mutation.** Every mutant of a specification value must fail. A survivor
   means the scenario passes regardless of the value it claims to test.

**A feature file joins the suite only through an explicit
`scenarios("../../features/x.feature")` call in a test module.** With no binding
module the file is not collected by pytest at all, so a green test run says
nothing about it.

## What mutation cannot see

- `Feature.background` is never passed to the mutation engine, so **Background
  steps are never mutation targets** in any scenario.
- Literal mutation returns early for outline scenarios, so **a value hardcoded in
  a fixed `Given` above an `Examples` table is never a target either.**

The consequence is counterintuitive and it drives spec shape: the values a
feature leans on hardest are often the ones nothing checks. See the
`gherkin-specs` skill for what to do about it.

## The boundary gate is narrower than it sounds

It walks **only** the steps directory and flags absolute imports whose top-level
root matches a top-level importable name under `src/` — in this project exactly
one name, `claimgate`. `tests/api/` is not walked. An import of anything not
named `claimgate` is invisible to it. So a step file that imports an HTTP client
and builds its own client passes the gate while binding the suite to transport
detail. That discipline is held by review, not by the gate.

## Protected paths: two lists, not one

`[gates.protect]` has two independent keys and they do different jobs.

- **`paths`** — files an agent must not edit at all. Defaults to `gauntlet.toml`,
  `.gauntlet/`, `.claude/settings.json`, and `gauntlet.lock.json`.
- **`verify`** — files whose *content* the gate hashes and checks each run. This
  is the `N/N paths unchanged` figure. Defaults to `gauntlet.toml`,
  **`pyproject.toml`**, and `.claude/settings.json`.

`pyproject.toml` appears only in the second list, and that is what guards the
pinned toolchain: `requires-python` cannot drift without the gate noticing.
`gauntlet.lock.json` appears only in the first — blocked from editing, not
content-verified, because the ledger changes legitimately whenever the human
approves something.

**Neither list contains anything under `.claude/skills/`.** These skill files are
unprotected and un-verified: an agent can rewrite the document that constrains it
and no gate will report it. Blocking that is `paths`; noticing it is `verify`;
both are changes to `gauntlet.toml`, which is itself protected, so both are the
human's to make with `gauntlet lock`.

## The project interpreter

`requires-python` is `>= 3.12`. A system `python3` older than 3.11 fails on
`import tomllib` — a standard-library module — which reads like a missing
dependency and is not one. Run project tooling through the venv
(`.venv/bin/python`, or activate it first), never through bare `python3`.
Installing a newer system Python does not help and is not the fix.

## When the answer is not here

Read these three files, not the tree:

- `gauntlet/gates/acceptance.py` — stage order, diagnostics, survivor handling
- `gauntlet/acceptance/mutation.py` — what becomes a mutant and how it is changed
- `gauntlet/gates/boundary.py` — the import rule, in full, in 134 lines

Then correct this document in the same commit.
