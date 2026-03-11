# Pair vs Simplex Holonomy Search

## Question

This search asks whether assignment plus pairwise nerve transport is already exact, or whether a deterministic local law can force runtime classes that survive inside a fixed assignment-plus-pair fiber.
The strongest witness is hidden future beyond pair transport: two prefixes with the same assignment, the same pair summary, and the same current output, but different futures under the same non-empty suffix.

## Scan Setup

- Base scan: exact normalized full-union antichains on `[p]` with `p <= 4` and `k <= 3`.
- Expanded scan: not run in this base exact pass; this artifact fixes the boundary on the full normalized base grid first.
- Dense overlap expansion triggered: `False`.
- Controls: `broadcast_control` stays flat, `committed_allocation` reproduces coordinate curvature while keeping assignment exact, and the pair-only laws test pairwise transport as the current exact object.
- Local law library: pair-only controls, pair-plus-simplex orientation laws, pair-plus-simplex commutator laws, triangle debt laws, and higher local interaction laws with tiny deterministic alphabets.
- Runtime quotient: exact continuation quotient; segment-row controls are analyzed by exact suffix rows, while tokenized laws are analyzed on reachable event-prefix automata.
- Canonical `first` order: `(p, k, |A|, pair alphabet, simplex alphabet, reachable states, witness length, family, semantics)` with witness-specific traces for assignment, hidden-future, pair, and hidden-future-beyond-pair searches.

## Semantics Library

- `broadcast_control` (`category=control`, `|Sigma_pair|=1`, `|Sigma_simplex|=1`): Negative control: broadcast presence semantics; edge choice never enters the carrier.
- `committed_allocation` (`category=control`, `|Sigma_pair|=1`, `|Sigma_simplex|=1`): Positive control: variable-to-edge assignment with disjoint-domain segment composition on the V-hypergraph.
- `pair_phase_exclusive_other_live_block_lower` (`category=pair_only`, `|Sigma_pair|=2`, `|Sigma_simplex|=1`): Pair phase mod 2 triggered only by exclusive claims into a live pair.
- `pair_phase_shared_other_live_block_lower` (`category=pair_only`, `|Sigma_pair|=2`, `|Sigma_simplex|=1`): Pair phase mod 2: a shared claim into the lower edge toggles when the upper edge is already live; odd phase suppresses lower completion.
- `pair_phase_any_other_live_block_lower` (`category=pair_only`, `|Sigma_pair|=2`, `|Sigma_simplex|=1`): Pair phase mod 2: any claim into a pair edge toggles once the opposite edge is already live; odd phase suppresses lower completion.
- `pair_phase_shared_other_live_block_lower__simplex_orient_two_live` (`category=pair_plus_simplex`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`): Pairwise shared-other-live phase toggles and suppresses lower completion. A triangle-orientation token records which edge created the second live edge of a 2-simplex and blocks that oriented edge on completion.
- `pair_phase_shared_other_live_block_lower__simplex_orient_three_live` (`category=pair_plus_simplex`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`): Pairwise shared-other-live phase toggles and suppresses lower completion. A triangle-orientation token records which edge completed the live 2-simplex and blocks that oriented edge on completion.
- `pair_phase_shared_other_live_block_lower__simplex_orient_second_or_third` (`category=pair_plus_simplex`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`): Pairwise shared-other-live phase toggles and suppresses lower completion. Triangle orientation updates on the second or third live edge and blocks the oriented edge on completion.
- `pair_phase_shared_other_live_block_lower__simplex_commutator_toggle` (`category=pair_plus_simplex`, `|Sigma_pair|=2`, `|Sigma_simplex|=2`): Pairwise shared-other-live phase toggles and suppresses lower completion. A simplex phase toggles when two active pair phases meet inside a live triangle; odd phase blocks the lowest edge.
- `pair_phase_shared_other_live_block_lower__triangle_debt` (`category=triangle_debt`, `|Sigma_pair|=2`, `|Sigma_simplex|=3`): Pairwise shared-other-live phase toggles and suppresses lower completion. Triangle-local debt accumulates when pair transport reaches a full triangle; debt level 2 blocks the lowest edge.
- `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` (`category=higher_local_interaction`, `|Sigma_pair|=2`, `|Sigma_simplex|=4`): Pairwise shared-other-live phase toggles and suppresses lower completion. Triangle orientation updates on the second or third live edge while active simplex tokens freeze further pair updates on incident overlaps.

## Summary Table

| Semantics | Category | `|Sigma_pair|` | `|Sigma_simplex|` | Seed counts `(runtime / assign / pair / simplex)` | First assignment split | First hidden future | First pair-insufficient split | First hidden-future-beyond-pair | Max pair gap | Pair exact on scan | Simplex exact on scan |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Broadcast` | `control` | `1` | `1` | `8 / 8 / 8 / 8` | `none` | `none` | `none` | `none` | `0.000` | `True` | `True` |
| `Committed Allocation` | `control` | `1` | `1` | `11 / 12 / 12 / 12` | `none` | `none` | `none` | `none` | `0.000` | `True` | `True` |
| `Pair Phase XL` | `pair_only` | `2` | `1` | `11 / 12 / 16 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `none` | `none` | `0.000` | `True` | `True` |
| `Pair Phase SL` | `pair_only` | `2` | `1` | `9 / 12 / 16 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `none` | `none` | `0.000` | `True` | `True` |
| `Pair Phase AL` | `pair_only` | `2` | `1` | `10 / 12 / 14 / 14` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=4, k=3) ((1, 2), (1, 3, 4))` | `none` | `none` | `0.000` | `True` | `True` |
| `Shared Pair Phase + 2-Live Orient` | `pair_plus_simplex` | `2` | `4` | `9 / 12 / 16 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3), (2, 3))` | `(p=3, k=2) ((1, 2), (1, 3), (2, 3))` | `0.000` | `False` | `True` |
| `Shared Pair Phase + 3-Live Orient` | `pair_plus_simplex` | `2` | `4` | `9 / 12 / 16 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=4, k=2) ((1, 2), (1, 3), (1, 4))` | `(p=4, k=2) ((1, 2), (1, 3), (1, 4))` | `0.000` | `False` | `True` |
| `Shared Pair Phase + 2/3-Live Orient` | `pair_plus_simplex` | `2` | `4` | `9 / 12 / 16 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3), (2, 3))` | `(p=3, k=2) ((1, 2), (1, 3), (2, 3))` | `0.000` | `False` | `True` |
| `Shared Pair Phase + Commutator Toggle` | `pair_plus_simplex` | `2` | `2` | `9 / 12 / 16 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `none` | `none` | `0.000` | `True` | `True` |
| `Shared Pair Phase + Triangle Debt` | `triangle_debt` | `2` | `3` | `9 / 12 / 16 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `none` | `none` | `0.000` | `True` | `True` |
| `Shared Pair Phase + Feedback Orient` | `higher_local_interaction` | `2` | `4` | `9 / 12 / 16 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3), (2, 3))` | `(p=3, k=2) ((1, 2), (1, 3), (2, 3))` | `0.000` | `False` | `True` |

## Controls

- `broadcast_control` stays flat: no assignment split, no pair split, and no hidden future on the scanned grid.
- `committed_allocation` reproduces the known assignment-level control: coordinate collapse fails, but both raw assignment and assignment-plus-pair remain exact.
- `pair_phase_exclusive_other_live_block_lower` and `pair_phase_shared_other_live_block_lower` provide the pairwise-holonomy controls: they break assignment exactness but keep assignment-plus-pair exact.

## Boundary Results

- First assignment split: `pair_phase_any_other_live_block_lower` on `((1, 2), (1, 3))` at `(p=3, k=2)`.
- First hidden future: `pair_phase_exclusive_other_live_block_lower` on `((1, 2), (1, 3))` at `(p=3, k=2)`.
- First pair-insufficient split: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` on `((1, 2), (1, 3), (2, 3))` at `(p=3, k=2)`, with pair gap `-0.907` bits.
- First hidden-future-beyond-pair split: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` on `((1, 2), (1, 3), (2, 3))` at `(p=3, k=2)`.

## First Pair-Insufficient Split

- semantics: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` (`|Sigma_pair|=2`, `|Sigma_simplex|=4`)
- family: `((1, 2), (1, 3), (2, 3))`
- counts: runtime `24`, assignment `27`, pair `45`, simplex `58`, full state `58`
- pair holonomy rank: `2`
- simplex holonomy rank: `1`
- pair gap: `-0.907` bits
- same assignment-plus-pair witness `u`: `[2->(1, 2), 3->(1, 3)]`
- same assignment-plus-pair witness `v`: `[3->(1, 3), 2->(1, 2)]`
- suffix `w`: `[1->(1, 2)]`
- pair fiber: `((-1, 0, 1), (0, 0, 0))`
- outputs now: `((1,), (1,))` versus `((1,), (1,))`
- outputs after suffix: `((),)` versus `()`

## First Hidden-Future-Beyond-Pair Split

- semantics: `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs` (`|Sigma_pair|=2`, `|Sigma_simplex|=4`)
- family: `((1, 2), (1, 3), (2, 3))`
- same assignment-plus-pair fiber: `((-1, 0, 1), (0, 0, 0))`
- left prefix `u`: `[2->(1, 2), 3->(1, 3)]`
- right prefix `v`: `[3->(1, 3), 2->(1, 2)]`
- shared current output: `((1,), (1,))`
- non-empty suffix `w`: `[1->(1, 2)]`
- future outputs: `((),)` versus `()`

## Interpretation

Pairwise nerve transport is not final on the scanned local law library.
The first counterexample already lives on the triangle family, so the next exact runtime object is assignment plus pair-plus-simplex transport rather than assignment plus pair transport alone.
The strongest witness is a hidden future beyond pair transport: the current output and the full pair fiber agree, but a non-empty suffix still separates the futures.

## Artifacts

- JSON: [pair_vs_simplex_holonomy_search.json](pair_vs_simplex_holonomy_search.json)
- Figure: [pair_vs_simplex_holonomy_search.svg](pair_vs_simplex_holonomy_search.svg)
- Note: [simplex-holonomy-boundary.md](../../../docs/writing/experiments/holonomy/simplex-holonomy-boundary.md)
