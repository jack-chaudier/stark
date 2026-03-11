# Global Holonomy Atlas

## Scope

- EXACT COMPUTATIONAL RESULT on the normalized base grid `p <= 4` and `k <= 3`, plus the named seed families used in the atlas.
- The larger normalized `p <= 5, k <= 4` follow-up is intentionally omitted here because the `p = 4` scan already fixes the minimal-boundary winners in canonical first order.

## First Static Obstruction

- EXACT COMPUTATIONAL RESULT: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux` first breaks current-output exactness beyond `assignment + pair + simplex` on `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4))`.
- Overlap kind: `cycle_of_triangles`.

## First Dynamic Obstruction

- EXACT COMPUTATIONAL RESULT: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex` first yields a same-now / future-separate witness on `((1, 2, 3), (1, 4), (2, 4), (3, 4))`.
- Overlap kind: `mixed`.

## Observed Boundary

- Static and dynamic first winners differ: `True`.
- The first global current-output obstruction and the first same-now / future-separate obstruction do not coincide.
- This supports a local-to-global holonomy tower on the overlap complex: a current-output obstruction can appear before the strongest hidden-future obstruction does.
