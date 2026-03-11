# Full Assignment Holonomy

## Thesis

The current search breaks the next boundary: raw committed assignment is no longer exact.

## Exact Boundary

- First full-assignment split: `pair_phase_any_other_live_block_lower` on `((1, 2), (1, 3))`.
- Token scope: `pair` with local alphabet size `2`.
- Counts: runtime `10`, assignment `12`, token `14`.
- Assignment gap: `-0.263` bits.

The key structural fact is that pairwise nerve holonomy already suffices.

## Hidden Future

- First hidden-future split: `pair_phase_exclusive_other_live_block_lower` on `((1, 2), (1, 3))`.
- So the future can remember a local transport state that both the raw assignment and the current readout erase.

## Open Seam

The next exact target is no longer whether assignment can fail. It is whether pair-token transport is already final, or whether there are deterministic local laws where even assignment plus pair transport fails and 2-simplex or higher holonomy becomes necessary.
