<!-- gauntlet:begin -->
## Quality gates (Gauntlet)

This project is gated. Implementation code is yours; thresholds and approvals are
the human's.

- Run `gauntlet check` yourself before you say you are done. Do not wait for the
  Stop hook to tell you.
- Gate failures come back as JSON with a file, a symbol, a line, and a remedy.
  Act on the remedy rather than guessing.
- Never edit `gauntlet.toml`, `gauntlet.lock.json`, `.claude/settings.json`, or
  anything under `.gauntlet/`. Weakening a threshold is not a way to pass a gate.
  If you believe a threshold is genuinely wrong, say so and let the human decide.
- Write tests that would fail if the behavior were wrong. Coverage of code that
  asserts nothing is worthless and later gates are designed to catch it.
- Prefer extracting functions over suppressing a finding. `# noqa` and
  `# type: ignore` are last resorts, not shortcuts.
<!-- gauntlet:end -->

## Standing constraints (ClaimGate domain, decided in design conversation)

These survive context loss even when the conversation that produced them doesn't. Full reasoning
for each lives in `PHASE2_DESIGN.md`, `ASSUMPTIONS.md`, and `STATUTORY_REGISTER.md` — this is the
list to check before proposing anything that would violate one.

- Never default a threshold, state name, status code, or retention behaviour. Escalate instead. A
  defaulted rule is a rule nobody approved.
- There is no rejected, invalid, or discarded state anywhere in the record state model. A notice
  cannot be refused.
- SIU output records factual indicators only — never a conclusion, never the word "fraud" as a
  system-generated value — and is never a state or a routing destination.
- Claim lifecycle (open, reserved, in suit, closed, reopened) belongs to the policy administration
  system, not ClaimGate. ClaimGate does not mint claim numbers.
- No Gherkin scenario may name a function, class, table, or column.
- Every threshold needs a scenario on each side of the boundary.
- Regulatory values cite primary sources only — the Florida Legislature's statute text, enrolled
  bill text, FLOIR, or DFS — with a verified-on date. Never a law firm summary, a consumer blog, or
  a ratings site.
- When a recommendation follows from what the code currently does rather than from an independent
  judgment, say so explicitly instead of proposing around it.
- Spec approval, mutant approval, and mutant pruning are the human's calls, not something to run
  unprompted.
- **Commit granularity is what makes the log worth reading, not a record of it having happened.**
  One commit per reopening, or a small series within one — never a batch spanning several
  reopenings. Spec lock and implementation are separate commits, in that order, so the sequence is
  visible in the log itself rather than only asserted in a document. Commit messages carry the
  reasoning, not just the change: one line of what, one line of why. Shape to match — "remove
  365-day reporting gate: late notice is a coverage determination made downstream on prejudice and
  tolling, not an intake rule" — not "update validation.py."
