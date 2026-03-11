# Simplex vs Global Holonomy Search

## Question

This search asks whether assignment plus pair plus simplex transport is already final, or whether a deterministic local law can force a hidden future beyond the simplex layer.
In parallel, it searches for smaller exact quotients inside the simplex layer whenever raw simplex transport is exact but clearly non-minimal.

## Scan Setup

- Controls: `broadcast_control`, `committed_allocation`, `pair_phase_exclusive_other_live_block_lower`, and `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs`.
- Extra law library: tetra-local commutator, orientation, debt, and freeze laws; plus cycle-flux, feedback-loop, and face-order parity laws.
- Base normalized scan: `p <= 4` and `k <= 3`.
- Expanded scan triggered: `False` on semantics `['pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_commutator_toggle', 'pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex', 'pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux', 'pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__simplex_feedback_loop', 'pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__parity_on_face_order']`.
- Dense overlap scan triggered: `False`.
- Canonical `first` order: `(p, k, |A|, pair alphabet, simplex alphabet, extra alphabet, reachable states, witness length, family, semantics)`.

## Seed Families

- `triangle` = `((1, 2), (1, 3), (2, 3))`
- `tetrahedron_3uniform` = `((1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4))`
- `four_edge_star` = `((1, 2), (1, 3), (1, 4), (1, 5))`
- `k4_pair_family` = `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4))`
- `triangle_chain` = `((1, 2), (1, 3), (2, 3), (2, 4), (3, 4))`

## Semantics Library

- `broadcast_control` (`category=control`, `|Sigma_pair|=1`, `|Sigma_simplex|=1`, `|Sigma_extra|=1`): Negative control: broadcast presence semantics; edge choice never enters the carrier.
- `committed_allocation` (`category=control`, `|Sigma_pair|=1`, `|Sigma_simplex|=1`, `|Sigma_extra|=1`): Positive control: variable-to-edge assignment with disjoint-domain segment composition on the V-hypergraph.
- `pair_phase_exclusive_other_live_block_lower` (`category=pair_control`, `|Sigma_pair|=2`, `|Sigma_simplex|=1`, `|Sigma_extra|=1`): Pair phase mod 2 triggered only by exclusive claims into a live pair.
- `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` (`category=simplex_control`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`, `|Sigma_extra|=1`): Pairwise shared-other-live phase toggles and suppresses lower completion. Triangle orientation updates on the second or third live edge while active simplex tokens freeze further pair updates on incident overlaps.
- `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_commutator_toggle` (`category=tetra_local`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`, `|Sigma_extra|=2`): Shared-other-live pair phase with simplex orientation/freeze, extended by a tetra-local toggle that activates once multiple simplex faces are live inside a 4-clique and blocks the lowest edge on completion.
- `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_orient_second_or_third` (`category=tetra_local`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`, `|Sigma_extra|=5`): Shared-other-live pair phase with simplex orientation/freeze, extended by a tetra orientation token that records which edge carried the third or fourth live face into a 4-clique and blocks that edge on completion.
- `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_debt` (`category=tetra_local`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`, `|Sigma_extra|=3`): Shared-other-live pair phase with simplex orientation/freeze, extended by a capped tetra debt that accumulates when simplex transport closes a 4-clique and blocks the lowest edge at debt level 2.
- `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex` (`category=tetra_local`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`, `|Sigma_extra|=2`): Shared-other-live pair phase with simplex orientation/freeze, extended by a tetra-local toggle that later freezes incident simplex updates and blocks the lowest edge while active.
- `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux` (`category=global_cycle`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`, `|Sigma_extra|=2`): Shared-other-live pair phase with simplex orientation/freeze, extended by a cycle flux bit attached to a triangle cycle; odd flux blocks the lowest cycle edge on completion.
- `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__simplex_feedback_loop` (`category=global_cycle`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`, `|Sigma_extra|=2`): Shared-other-live pair phase with simplex orientation/freeze, extended by a cycle-local feedback bit that can freeze simplex updates along an active triangle cycle.
- `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__parity_on_face_order` (`category=global_cycle`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`, `|Sigma_extra|=2`): Shared-other-live pair phase with simplex orientation/freeze, extended by a cycle parity bit that records odd face-order circulation across an active triangle cycle and blocks the cycle minimum edge on completion.

## Summary Table

| Semantics | Kind | `|pair|` | `|simplex|` | `|extra|` | Seed counts `(runtime / pair / simplex / full)` | First pair split | First simplex split | Hidden beyond simplex | Best explicit exact compression |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Broadcast` | `control` | `1` | `1` | `1` | `8 / 8 / 8 / 8` | `none` | `none` | `none` | `none` |
| `Committed Allocation` | `control` | `1` | `1` | `1` | `21 / 27 / 27 / 27` | `none` | `none` | `none` | `none` |
| `Pair Phase XL` | `pair_control` | `2` | `1` | `1` | `22 / 49 / 49 / 49` | `none` | `none` | `none` | `none` |
| `Shared Pair Phase + Feedback Orient` | `simplex_control` | `2` | `4` | `1` | `24 / 45 / 58 / 58` | `triangle @ (p=3, k=2)` | `none` | `none` | `Simplex histogram (599)` |
| `Feedback Orient + Tetra Toggle` | `tetra_local` | `2` | `4` | `2` | `24 / 45 / 58 / 58` | `triangle @ (p=3, k=2)` | `|A|=4 @ (p=4, k=3)` | `four_edge_star @ (p=5, k=2)` | `Simplex histogram (599)` |
| `Feedback Orient + Tetra Orient` | `tetra_local` | `2` | `4` | `5` | `24 / 45 / 58 / 58` | `triangle @ (p=3, k=2)` | `none` | `none` | `Simplex histogram (599)` |
| `Feedback Orient + Tetra Debt` | `tetra_local` | `2` | `4` | `3` | `24 / 45 / 58 / 58` | `triangle @ (p=3, k=2)` | `none` | `none` | `Simplex histogram (599)` |
| `Feedback Orient + Tetra Freeze` | `tetra_local` | `2` | `4` | `2` | `24 / 45 / 58 / 58` | `triangle @ (p=3, k=2)` | `|A|=4 @ (p=4, k=3)` | `|A|=4 @ (p=4, k=3)` | `Simplex histogram (599)` |
| `Feedback Orient + Cycle Flux` | `global_cycle` | `2` | `4` | `2` | `24 / 45 / 58 / 58` | `triangle @ (p=3, k=2)` | `|A|=5 @ (p=4, k=2)` | `|A|=4 @ (p=4, k=3)` | `Simplex histogram (226)` |
| `Feedback Orient + Feedback Loop` | `global_cycle` | `2` | `4` | `2` | `24 / 45 / 58 / 58` | `triangle @ (p=3, k=2)` | `|A|=5 @ (p=4, k=2)` | `|A|=4 @ (p=4, k=3)` | `Simplex histogram (226)` |
| `Feedback Orient + Face-Order Parity` | `global_cycle` | `2` | `4` | `2` | `24 / 45 / 58 / 58` | `triangle @ (p=3, k=2)` | `|A|=5 @ (p=4, k=2)` | `|A|=4 @ (p=4, k=3)` | `Simplex histogram (226)` |

## Boundary Results

- First pair-insufficient split: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` on `((1, 2), (1, 3), (2, 3))` at `(p=3, k=2)`.
- First hidden future beyond pair: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` on `((1, 2), (1, 3), (2, 3))` at `(p=3, k=2)`.
- First simplex-insufficient split: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux` on `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4))` at `(p=4, k=2)`, with simplex gap `-2.638` bits.
- First hidden future beyond simplex: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex` on `((1, 2, 3), (1, 4), (2, 4), (3, 4))` at `(p=4, k=3)`.

## First Simplex-Insufficient Split

- semantics: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux`
- family: `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4))`
- counts: runtime `98`, pair `374`, simplex `610`, full state `644`
- same assignment+pair+simplex witness `u`: `[1->(1, 2), 2->(1, 2), 4->(1, 4)]`
- same assignment+pair+simplex witness `v`: `[1->(1, 2), 4->(1, 4), 2->(1, 2)]`
- suffix `w`: `[]`
- shared simplex fiber: `((0, 0, -1, 2), (0, 0, 0, 0, 0, 0, 0, 0), (3, 0, 2, 0))`
- current outputs: `((),)` versus `()`
- future outputs: `((),)` versus `()`

## First Hidden Future Beyond Simplex

- semantics: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex`
- family: `((1, 2, 3), (1, 4), (2, 4), (3, 4))`
- left prefix `u`: `[2->(1, 2, 3), 3->(1, 2, 3), 4->(1, 4)]`
- right prefix `v`: `[2->(1, 2, 3), 4->(1, 4), 3->(1, 2, 3)]`
- shared simplex fiber: `((-1, 0, 0, 1), (0, 0, 0, 0, 0, 0), (2, 2, 0, 0))`
- shared current output: `((1,), (1,))`
- non-empty suffix `w`: `[1->(1, 2, 3)]`
- future outputs after `w`: `()` versus `((),)`

## Best Compression Inside the Simplex Layer

- semantics: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs`
- family: `((1, 2), (1, 3), (1, 4), (2, 3), (2, 4))`
- raw simplex quotient count: `610`
- runtime quotient count: `106`
- best explicit exact compression: `Simplex histogram` with quotient count `599`
- compressed simplex gap: `-2.498` bits

## Interpretation

The simplex layer is not final on the tested law library: a hidden future survives inside a fixed assignment-plus-pair-plus-simplex fiber.
The winning witness is a true hidden future beyond simplex transport: the current output and the full simplex fiber agree, but a non-empty common suffix still separates the futures.
At the same time, the raw simplex carrier is not canonical: even where it is exact, a smaller exact quotient exists inside the simplex layer.

## Artifacts

- JSON: [simplex_vs_global_holonomy_search.json](simplex_vs_global_holonomy_search.json)
- Figure: [simplex_vs_global_holonomy_search.svg](simplex_vs_global_holonomy_search.svg)
- Boundary note: [global-holonomy-boundary.md](../../../docs/writing/experiments/holonomy/global-holonomy-boundary.md)
- Compression note: [simplex-quotient-compression.md](../../../docs/writing/experiments/holonomy/simplex-quotient-compression.md)
