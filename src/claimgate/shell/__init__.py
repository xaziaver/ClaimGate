"""The phase-2 API shell: orchestration and persistence around the pure domain layer.

The domain package stays pure - no clock, no identifiers, no mutable state.
Everything in this package is the opposite: wall-clock timestamps, generated
notice IDs, and an in-memory store. See PHASE2_DESIGN.md and ASSUMPTIONS.md's
"Timezone-correct 'now'" for why the split is drawn here.
"""
