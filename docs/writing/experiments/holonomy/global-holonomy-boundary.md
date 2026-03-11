# Global Holonomy Boundary

## Thesis

This search crosses the next boundary: assignment plus pair plus simplex transport is not final.

## Exact Boundary

- First simplex-insufficient split: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux` on `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4))`.
- Token sizes: `|Sigma_pair| = 2`, `|Sigma_simplex| = 4`, and `|Sigma_extra| = 2`.
- Counts: runtime `98`, simplex `610`, full state `644`.
- Simplex gap: `-2.638` bits.

## Hidden Future Beyond Simplex

- First hidden-future-beyond-simplex split: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex` on `((1, 2, 3), (1, 4), (2, 4), (3, 4))`.
- The future remembers a transport token that both the full simplex fiber and the current readout erase.

## Open Seam

The next exact target is no longer whether simplex transport can fail. It is whether the new exact object is tetra transport, cycle holonomy, or something still more global.
