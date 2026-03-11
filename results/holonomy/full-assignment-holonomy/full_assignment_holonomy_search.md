# Full Assignment Holonomy Search

## Question

This search asks for the first deterministic prefix-compositional semantics where raw committed assignment is no longer exact.
The strongest witness is hidden future: two prefixes with the same full assignment and the same current output, but different futures under the same non-empty suffix.

## Scan Setup

- Base scan: exact normalized full-union antichains on `[p]` with `p <= 4` and `k <= 3`.
- Expanded scan triggered: `False`.
- Controls: `broadcast_control` as the flat negative control and `committed_allocation` as the positive control for coordinate curvature.
- Holonomy library: generated pairwise and simplex transport laws with tiny token alphabets.
- Runtime quotient: exact continuation quotient; segment-row controls are analyzed by exact suffix rows, while tokenized laws are analyzed on reachable event-prefix automata.
- Canonical `first` order: `(p, k, |A|, token alphabet, reachable states, witness length, family, semantics)` with witness-specific traces for coordinate, assignment, and hidden-future searches.
- Tie handling: several pair laws hit the same seed family, but the overall winner is chosen by the full canonical order above rather than by family size alone.

## Semantics Library

- `broadcast_control` (`scope=none`, `|Sigma|=1`): Negative control: broadcast presence semantics; edge choice never enters the carrier.
- `committed_allocation` (`scope=none`, `|Sigma|=1`): Positive control: variable-to-edge assignment with disjoint-domain segment composition on the V-hypergraph.
- `pair_phase_shared_other_live_block_lower` (`scope=pair`, `|Sigma|=2`): Pair phase mod 2: a shared claim into the lower edge toggles when the upper edge is already live; odd phase suppresses lower completion.
- `pair_phase_shared_other_live_block_upper` (`scope=pair`, `|Sigma|=2`): Pair phase mod 2 with upper-edge suppression.
- `pair_phase_any_other_live_block_lower` (`scope=pair`, `|Sigma|=2`): Pair phase mod 2: any claim into a pair edge toggles once the opposite edge is already live; odd phase suppresses lower completion.
- `pair_phase_exclusive_other_live_block_lower` (`scope=pair`, `|Sigma|=2`): Pair phase mod 2 triggered only by exclusive claims into a live pair.
- `braid_orientation_shared_other_live` (`scope=pair`, `|Sigma|=3`): Orientation token records which pair edge received the decisive shared claim once the other edge is live; the oriented edge is blocked on completion.
- `transport_debt_shared_other_live` (`scope=pair`, `|Sigma|=3`): Capped debt token increments when a shared claim lands across a live overlap; level 2 debt blocks lower-edge completion.
- `catalytic_pair_activation` (`scope=pair`, `|Sigma|=2`): A latent pair catalyst latches when the overlap pair first becomes jointly live; active catalyst blocks lower-edge completion.
- `simplex_phase_triangle_activate` (`scope=simplex`, `|Sigma|=2`): Triangle-phase mod 2 toggles when a nerve triangle first becomes jointly live; odd phase blocks the lowest edge completion.
- `simplex_orientation_triangle_activate` (`scope=simplex`, `|Sigma|=4`): Triangle orientation remembers which edge activated the live 2-simplex; that edge is blocked on completion.

## Summary Table

| Semantics | Scope | `|Sigma|` | Seed counts `(runtime / coord / assign / token)` | First coordinate split | First `kappa_pi > 0` | First assignment split | First hidden future | Max assignment gap | Full assignment exact on scan |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Broadcast` | `none` | `1` | `8 / 8 / 8 / 8` | `none` | `none` | `none` | `none` | `0.000` | `True` |
| `Committed Allocation` | `none` | `1` | `11 / 8 / 12 / 12` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `none` | `none` | `0.000` | `True` |
| `Pair Phase SL` | `pair` | `2` | `9 / 8 / 12 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `0.000` | `False` |
| `Pair Phase SU` | `pair` | `2` | `9 / 8 / 12 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `0.000` | `False` |
| `Pair Phase AL` | `pair` | `2` | `10 / 8 / 12 / 14` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=4, k=3) ((1, 2), (1, 3, 4))` | `0.000` | `False` |
| `Pair Phase XL` | `pair` | `2` | `11 / 8 / 12 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `0.115` | `False` |
| `Braid Orient` | `pair` | `3` | `10 / 8 / 12 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `0.000` | `False` |
| `Debt Shared` | `pair` | `3` | `7 / 8 / 12 / 16` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3), (2, 3))` | `(p=4, k=3) ((1, 2, 3), (1, 2, 4))` | `(p=4, k=3) ((1, 2, 3), (1, 2, 4))` | `0.000` | `False` |
| `Catalytic Pair` | `pair` | `2` | `10 / 8 / 12 / 12` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `none` | `none` | `0.000` | `True` |
| `Simplex Phase` | `simplex` | `2` | `7 / 8 / 12 / 12` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3), (2, 3))` | `none` | `none` | `0.000` | `True` |
| `Simplex Orient` | `simplex` | `4` | `7 / 8 / 12 / 12` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3), (2, 3))` | `(p=4, k=2) ((1, 2), (1, 3), (1, 4))` | `(p=4, k=2) ((1, 2), (1, 3), (1, 4))` | `0.000` | `False` |

## Controls

- `broadcast_control` stays flat: no coordinate split, no assignment split, and no hidden future on the scanned grid.
- `committed_allocation` reproduces the known positive coordinate gap on `{{1,2},{1,3}}`, but still keeps full assignment exact on the scanned grid.

## Boundary Results

- First coordinate split: `committed_allocation` on `((1, 2), (1, 3))` at `(p=3, k=2)`.
- First positive coordinate `kappa_pi`: `committed_allocation` on `((1, 2), (1, 3))` with gap `0.459` bits.
- First full-assignment split: `pair_phase_any_other_live_block_lower` on `((1, 2), (1, 3))` at `(p=3, k=2)`, with assignment gap `-0.263` bits.
- First hidden-future split: `pair_phase_exclusive_other_live_block_lower` on `((1, 2), (1, 3))` at `(p=3, k=2)`.

## First Full-Assignment Split

- semantics: `pair_phase_any_other_live_block_lower` (`scope=pair`, `|Sigma|=2`)
- family: `((1, 2), (1, 3))`
- counts: runtime `10`, coordinate `8`, assignment `12`, token `14`, family `7`
- assignment holonomy rank: `2`
- hidden future rank: `1`
- assignment gap: `-0.263` bits, so exactness can fail before the count-level assignment gap turns positive
- same-assignment witness `u`: `[1->(1, 2), 2->(1, 2), 3->(1, 3)]`
- same-assignment witness `v`: `[1->(1, 2), 3->(1, 3), 2->(1, 2)]`
- suffix `w`: `[]`
- outputs now: `()` versus `((),)`
- outputs after suffix: `()` versus `((),)`

## First Hidden-Future Split

- semantics: `pair_phase_exclusive_other_live_block_lower` (`scope=pair`, `|Sigma|=2`)
- family: `((1, 2), (1, 3))`
- full assignment fiber: `{1->(1, 2), 3->(1, 3)}`
- left prefix `u`: `[1->(1, 2), 3->(1, 3)]`
- right prefix `v`: `[3->(1, 3), 1->(1, 2)]`
- non-empty suffix `w`: `[2->(1, 2)]`
- shared current output: `((2,),)`
- future outputs: `((),)` versus `()`

## Interpretation

Pairwise nerve holonomy is already enough.
The first full-assignment split appears on the seed V-hypergraph, so simplex transport is not necessary for the first runtime holonomy effect.
On the scanned library, the new exact runtime object is therefore assignment plus pair-transport token, not yet a fully global hypergraph state.
The stronger hidden-future witness shows the future can remember a local transport phase that the current output and the raw assignment both erase.

## Artifacts

- JSON: [full_assignment_holonomy_search.json](full_assignment_holonomy_search.json)
- Figure: [full_assignment_holonomy_search.svg](full_assignment_holonomy_search.svg)
- Note: [full-assignment-holonomy.md](../../../docs/writing/experiments/holonomy/full-assignment-holonomy.md)
