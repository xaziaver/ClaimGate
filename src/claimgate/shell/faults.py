"""The three ways this deployment's own configuration can be unreadable, and the
closed set of codes that name them.

Shell vocabulary, deliberately (ASSUMPTIONS.md, "Item 5i decisions", ruling 6).
No code here names an outcome a rule under src/claimgate/domain/ computed - each
names a fault in what this deployment was configured with - so no stored
decision's meaning changes because one exists, and RULESET_VERSION does not bump
for any of them. A code produced by or stored through the domain layer would be
a different claim entirely, and that is a stop-and-escalate rather than an edit.

**The enumeration is closed and scoped to the intake and resolution surfaces.**
Both share it because it is one vocabulary for one fault class; it is not
duplicate detection's and not SIU's, and adding a code to it is an escalation the
way adding one to either of those is (CLAUDE.md).

**One status carries all of them** - 500 on either surface - and the code is what
tells them apart. A caller's client branches on status to decide whether to
retry, and the answer is the same for every fault here: not until someone fixes
this deployment. A second status would be a distinction with no consequence,
which is the argument PHASE2_DESIGN.md already makes for the two identical 201s.

What each surface then does is not shared and is not here. An intake submission
is a reporter's statutory communication and is receipted anyway; a reviewer's
resolution attempt leaves nothing behind, because the notice's receipt duty was
discharged long before. See notice_intake.py and resolution.py.

PORT_BINDING_UNRESOLVABLE is item 7e's: a carrier's port bindings (bindings.py)
name no implementation this deployment holds, or omit a budget or a history
horizon (PHASE3_DESIGN.md, "Configuration"). Since item 7f the intake path
resolves the carrier's policy binding beside its rules and jurisdiction, before
any notice exists, and answers this code the way it answers the other two -
notice_intake.feature's deployment-fault table has the row. The resolution path
resolves no binding until item 7g re-searches on that path.
"""

CARRIER_RULES_UNRESOLVABLE = "CARRIER_RULES_UNRESOLVABLE"
JURISDICTION_MAP_UNUSABLE = "JURISDICTION_MAP_UNUSABLE"
PORT_BINDING_UNRESOLVABLE = "PORT_BINDING_UNRESOLVABLE"


class DeploymentFaultError(Exception):
    """Raised where this deployment cannot read its own configuration, and
    caught at the two endpoint boundaries that answer it.

    It carries the code rather than prose because the code is what crosses the
    boundary: the response names it, and on the intake path so does the
    receipted payload record. Three lookups raise it from two modules - the
    carrier rules and the jurisdiction map from rules.py, the port bindings from
    bindings.py - and the guarantee that matters is not where the raise lives
    but that both endpoints catch this one class, so neither can answer one
    fault and miss another.
    """

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
