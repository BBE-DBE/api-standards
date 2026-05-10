"""Rule modules for bbe-comm.

Each module exposes per-block check functions named `check_NNN_<slug>(block)`
returning `list[Finding]`. The validator collects them via ALL_PER_BLOCK_CHECKS
plus the cross-block check (BBE-COMM-021) which receives `(block, all_blocks)`.

Adding a new rule:
1. Drop a new `check_NNN_<slug>` function in the appropriate category module
   (or create a new module).
2. Append to ALL_PER_BLOCK_CHECKS (or CROSS_BLOCK_CHECKS for graph-aware
   checks).
3. Add a positive + negative test in tests/test_rules_<category>.py.
4. Add an `examples/invalid/NNN-<slug>.txt` corpus file.
"""

from .structural   import ALL as STRUCTURAL_CHECKS, CROSS_BLOCK as STRUCTURAL_CROSS
from .header       import ALL as HEADER_CHECKS
from .ids          import ALL as ID_CHECKS
from .lineage      import ALL as LINEAGE_CHECKS
from .authorization import ALL as AUTHORIZATION_CHECKS
from .compliance   import ALL as COMPLIANCE_CHECKS
from .extensions   import ALL as EXTENSION_CHECKS

ALL_PER_BLOCK_CHECKS = (
    STRUCTURAL_CHECKS
    + HEADER_CHECKS
    + ID_CHECKS
    + LINEAGE_CHECKS
    + AUTHORIZATION_CHECKS
    + COMPLIANCE_CHECKS
    + EXTENSION_CHECKS
)

CROSS_BLOCK_CHECKS = STRUCTURAL_CROSS

__all__ = ["ALL_PER_BLOCK_CHECKS", "CROSS_BLOCK_CHECKS"]
