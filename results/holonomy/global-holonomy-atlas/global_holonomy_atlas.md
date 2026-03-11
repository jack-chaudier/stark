# Global Holonomy Atlas

## Headline Results

- EXACT COMPUTATIONAL RESULT (Static): the first beyond-simplex current-output obstruction is `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux` on `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4))` at `(p=4, k=2)`.
- EXACT COMPUTATIONAL RESULT (Dynamic): the first same-now / future-separate witness beyond simplex is `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex` on `((1, 2, 3), (1, 4), (2, 4), (3, 4))` at `(p=4, k=3)`.
- EXACT COMPUTATIONAL RESULT (Compression): on `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4))`, `Component cochain signature` is exact with quotient count `1774`, below the raw global count `1942`.

## Definitions

- **Static split**: same `assignment + pair + simplex`, different current output.
- **Dynamic hidden future**: same `assignment + pair + simplex`, same current output, non-empty common suffix, different future outputs.
- Figure reading: static means same lower-layer summary, different now; dynamic means same lower-layer summary, same now, different future under a non-empty suffix.

## Scope

This atlas turns the beyond-simplex boundary into a structural scan.
It is exact on the normalized base grid `p <= 4` and `k <= 3`, plus the named seed families `triangle`, `tetrahedron_3uniform`, `four_edge_star`, `k4_pair_family`, and `triangle_chain`.
The larger normalized `p <= 5, k <= 4` follow-up is intentionally omitted here because the `p = 4` scan already fixes the minimal-boundary winners in the canonical first order, so the larger pass would be persistence-only rather than boundary-setting.

## Scan Setup

- Controls: `broadcast_control`, `committed_allocation`, and the simplex positive control `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs`.
- Global semantics: cycle-flux, simplex-feedback-loop, face-order-parity, tetra-freeze-simplex, and tetra-commutator-toggle.
- Base normalized scan: `p <= 4` and `k <= 3`.
- Named seed families added to the base grid: `triangle`, `tetrahedron_3uniform`, `four_edge_star`, `k4_pair_family`, and `triangle_chain`.
- Expanded normalized scan on promising semantics: `False` over `p <= 5` and `k <= 4`.
- Dense overlap scan triggered: `False`.
- Canonical `first` order: `(p, k, |A|, pair alphabet, simplex alphabet, extra alphabet, reachable states, witness length, family, semantics)`.

## Summary Table

| Semantics | Kind | `|pair|` | `|simplex|` | `|extra|` | Families | First static split | First dynamic split | Best exact compression |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Broadcast` | `control` | `1` | `1` | `1` | `129` | `none` | `none` | `none` |
| `Committed Allocation` | `control` | `1` | `1` | `1` | `129` | `none` | `none` | `none` |
| `Shared Pair Phase + Feedback Orient` | `simplex_control` | `2` | `4` | `1` | `129` | `none` | `none` | `none` |
| `Feedback Orient + Cycle Flux` | `global_cycle` | `2` | `4` | `2` | `129` | `|A|=5 @ (p=4, k=2)` | `|A|=4 @ (p=4, k=3)` | `none` |
| `Feedback Orient + Feedback Loop` | `global_cycle` | `2` | `4` | `2` | `129` | `|A|=5 @ (p=4, k=2)` | `|A|=4 @ (p=4, k=3)` | `none` |
| `Feedback Orient + Face-Order Parity` | `global_cycle` | `2` | `4` | `2` | `129` | `|A|=5 @ (p=4, k=2)` | `|A|=4 @ (p=4, k=3)` | `Component cochain signature (1774)` |
| `Feedback Orient + Tetra Freeze` | `tetra_local` | `2` | `4` | `2` | `129` | `|A|=4 @ (p=4, k=3)` | `|A|=4 @ (p=4, k=3)` | `none` |
| `Feedback Orient + Tetra Toggle` | `tetra_local` | `2` | `4` | `2` | `129` | `|A|=4 @ (p=4, k=3)` | `four_edge_star @ (p=5, k=2)` | `none` |

## Static vs Dynamic Boundary

- First static split: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux` on `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4))` at `(p=4, k=2)`.
  Counts: runtime `98`, simplex `610`, full state `644`.
- First dynamic hidden future: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex` on `((1, 2, 3), (1, 4), (2, 4), (3, 4))` at `(p=4, k=3)`.
  Counts: runtime `81`, simplex `461`, full state `494`.
- Static and dynamic first winners differ: `True`.

## Global Quotient Compression

- semantics: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__parity_on_face_order`
- family: `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4))`
- raw global state count: `1942`
- runtime quotient count: `156`
- best explicit exact compression: `Component cochain signature` with quotient count `1774`
- candidate summaries:
  - `Sorted extra tokens`: count `1774`, exact `True`
  - `Extra-token histogram`: count `1774`, exact `True`
  - `Per-component histogram`: count `1774`, exact `True`
  - `Component token multiset`: count `1774`, exact `True`
  - `Support-weighted histogram`: count `1828`, exact `True`
  - `Descriptor-signature histogram`: count `1848`, exact `True`
  - `Component cochain signature`: count `1774`, exact `True`

## Lexicographically Minimal Witness Families


### Static
- `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4))`; semantics `['pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux']`; kind `cycle_of_triangles`; cycle rank `4`; triangle clusters `1`; tetra supports `0`.

### Dynamic
- `((1, 2, 3), (1, 4), (2, 4), (3, 4))`; semantics `['pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex']`; kind `mixed`; cycle rank `3`; triangle clusters `1`; tetra supports `1`.

## First Static Witness

- semantics: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux`
- family: `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4))`
- overlap kind: `cycle_of_triangles`
- shared simplex fiber: `((0, 0, -1, 2), (0, 0, 0, 0, 0, 0, 0, 0), (3, 0, 2, 0))`
- left prefix `u`: `[1->(1, 2), 2->(1, 2), 4->(1, 4)]`
- right prefix `v`: `[1->(1, 2), 4->(1, 4), 2->(1, 2)]`
- current outputs: `((),)` versus `()`

## First Dynamic Hidden Future

- semantics: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex`
- family: `((1, 2, 3), (1, 4), (2, 4), (3, 4))`
- overlap kind: `mixed`
- shared simplex fiber: `((-1, 0, 0, 1), (0, 0, 0, 0, 0, 0), (2, 2, 0, 0))`
- left prefix `u`: `[2->(1, 2, 3), 3->(1, 2, 3), 4->(1, 4)]`
- right prefix `v`: `[2->(1, 2, 3), 4->(1, 4), 3->(1, 2, 3)]`
- shared current output: `((1,), (1,))`
- common non-empty suffix `w`: `[1->(1, 2, 3)]`
- future outputs after `w`: `()` versus `((),)`

## Interpretation

The first static obstruction is `cycle_of_triangles`, while the first dynamic hidden future is `mixed`.
The first global current-output obstruction and the first same-now / future-separate obstruction do not coincide.
The global layer is not only nontrivial; it is also non-canonical in its raw tokenization. At least one explicit quotient is strictly smaller than raw global state while remaining exact.
Taken together, the data supports a local-to-global tower on the overlap complex: pair transport, simplex transport, and then a genuinely global obstruction layer whose first static and dynamic witnesses need not coincide.

## Artifacts

- JSON: [global_holonomy_atlas.json](global_holonomy_atlas.json)
- Figure: [global_holonomy_atlas.svg](global_holonomy_atlas.svg)
- Atlas note: [global-holonomy-atlas.md](../../../docs/writing/experiments/holonomy/global-holonomy-atlas.md)
- Compression note: [global-quotient-compression.md](../../../docs/writing/experiments/holonomy/global-quotient-compression.md)
