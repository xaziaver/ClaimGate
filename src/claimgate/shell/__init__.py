"""The phase-2 API shell: orchestration and persistence around the pure domain layer.

The domain package stays pure - no clock, no identifiers, no mutable state.
Everything in this package is the opposite: generated notice IDs, a SQLite
database, and the receipt instant a caller hands in. See PHASE2_DESIGN.md's
"Persistence engine" and ASSUMPTIONS.md's "Timezone-correct 'now'" and "One
receipt clock, not two" for why the split is drawn here and where the clock
stops being read.
"""
