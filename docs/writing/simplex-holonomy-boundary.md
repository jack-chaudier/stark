# Simplex Holonomy Boundary

## Thesis

This search crosses the next boundary: assignment plus pairwise nerve transport is no longer exact.

## Exact Boundary

- First pair-insufficient split: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` on `((1, 2), (1, 3), (2, 3))`.
- Token sizes: `|Sigma_pair| = 2` and `|Sigma_simplex| = 4`.
- Counts: runtime `24`, pair `45`, simplex `58`.
- Pair gap: `-0.907` bits.

So the current exact runtime object on the scanned library is no longer assignment plus pair transport. It is assignment plus pair plus simplex transport.

## Hidden Future Beyond Pair

- First hidden-future-beyond-pair split: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` on `((1, 2), (1, 3), (2, 3))`.
- The future can remember a simplex-local transport state that both the pair fiber and the current readout erase.

## Open Seam

The next exact target is no longer whether pair transport can fail. It is whether assignment plus pair plus simplex transport is already final, or whether a deterministic local law can force genuinely more global holonomy beyond the 2-simplex layer.
