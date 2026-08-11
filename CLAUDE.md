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
- **If an operation crosses an approval boundary by accident, reverse it and escalate. Do not
  correct it in place.** An accurate reason on an unauthorized approval is still an unauthorized
  approval.
- **Commit granularity is what makes the log worth reading, not a record of it having happened.**
  One commit per reopening, or a small series within one — never a batch spanning several
  reopenings. Spec lock and implementation are separate commits, in that order, so the sequence is
  visible in the log itself rather than only asserted in a document. Commit messages carry the
  reasoning, not just the change: one line of what, one line of why. Shape to match — "remove
  365-day reporting gate: late notice is a coverage determination made downstream on prejudice and
  tolling, not an intake rule" — not "update validation.py."
- **Main is always green.** Spec lock and implementation being separate commits means there is a
  legitimately red state between them — a spec drafted ahead of its approval or implementation.
  That state lives on a branch named `reopening/<name>`, never on `main`. A reopening merges to
  `main` only when its spec is locked, its implementation is complete, and `gauntlet check` is
  green. This follows directly from the commit-granularity rule above, not a separate policy.
- **Reopening branches stay a superset of main.** Documentation commits land on main; reopening
  work stays on its branch. After any commit to main, merge main into the active reopening branch
  so the branch remains a superset. A checked-out reopening branch should always show current
  documentation.
- **A result that was not computed is never reported as a negative.** An
  indicator whose input is missing, or a comparison that was deliberately not
  run, resolves to a distinct not-evaluated value with a reason code — never to
  false, never to an empty result. Two reopenings have now turned on this
  (`siu_indicators.feature`'s three-valued indicators, `duplicates.feature`'s
  notice-type rule). It applies to anything phase 2 serializes, not only to
  these two.
- **Reason-code enumerations are closed and scoped to one feature.** Duplicate
  detection's codes are not SIU's, even though both use the same
  not-evaluated-plus-reason convention; the two sets grow independently and
  neither file's "complete set" claim constrains the other. Escalate before
  adding a code to any of them, and never merge two enumerations to avoid
  editing a locked spec.
- **A gate failure awaiting a human decision is not a failure to retry.** A spec
  drafted or awaiting approval, a stale or unreviewed mutant approval, a
  dangling approval key — none of these clear from your side, and the
  separate-commits rule above guarantees the first one on every reopening.
  Report the condition and stop on the first occurrence. Do not spend the retry
  budget counting down toward a state only the human can change.
- **Exporting a file at a ref means `git show <ref>:<path> > <file> && wc -l`.**
  Reading the working tree and reporting it as the export is not the same
  operation. They agree exactly when the tree is clean, which is when the
  protocol is least needed, and diverge in precisely the case it exists to
  catch.
- **Gauntlet's commands are split by owner, and the split is not guessable from
  the CLI.** Yours to run: `gauntlet check`, `gauntlet verify`, `gauntlet status`,
  `gauntlet doctor`, `gauntlet events`. Mine, never run unprompted:
  `gauntlet spec approve`, `gauntlet mutant approve`, `gauntlet review`, and
  `gauntlet lock`. `gauntlet lock` in particular does not approve a
  specification — it re-approves the current content of the protected paths,
  which are the files you are forbidden to edit. The acceptance gate's own
  remedy text currently names it for a modified spec; that text is wrong, and
  the correct command is `gauntlet spec approve`, which is mine.
- **"Act on the remedy" stops at the approval boundary.** If a remedy names a
  command from my list above, the remedy is addressed to me: report it and stop.
  A remedy you cannot run is not an instruction to find something adjacent that
  you can.
