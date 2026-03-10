# Runtime Hypergraph Curvature Search

## Question

This search asks for the first semantics where the full coordinate witness state stops being exact.
The smoking gun is a reachable triple `(u, v, w)` with the same full coordinate state at `u` and `v`, but different runtime behavior after the same suffix `w`.
For the committed-allocation positive control, the scan also tracks the stronger count-level invariant `kappa_pi = log2|Q_runtime| - log2|Q_coordinate|` from the earlier resource-carrier boundary.

## Scan Setup

- Families: exact full-union antichains on `[p]`, sorted lexicographically by family size, overlap, edge sizes, total size, and family tuple.
- Search grid: `p <= 4`, `k <= 3`.
- Seed crystal: `{{1,2}, {1,3}}`.
- Runtime quotient: exact continuation quotient on reachable prefix states; for `committed_allocation` this is computed directly from exact composition rows over all suffix segments.
- Coordinate quotient: quotient induced by the full coordinate witness state.
- New invariants: `coordinate_curvature_gap = log2|Q_runtime| - log2|Q_coordinate|` and `fiber_holonomy_rank = max_fiber |Q_runtime inside fiber|`.

## Semantics

- `broadcast_control`: Current coordinate-broadcast control: completed families depend only on present coordinates.
- `incidence_local_progress`: Track incidence-local progress, but broadcast every variable event to all incident edges.
- `exclusive_overlap_claim`: Each seen variable is routed to a single best-supported incident family edge.
- `shared_overlap_budget`: Each seen variable contributes one conserved credit routed to the least-funded incident edge.
- `committed_allocation`: Positive control: partial variable-to-edge assignments compose by disjoint-domain union on the V-hypergraph.

## Summary Table

| Semantics | Seed counts `(runtime / coordinate / incidence / family / full assignment)` | First split | First `kappa_pi > 0` | Max gap bits | Holonomy | Coordinate exact on scan | Full assignment exact on scan |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `Broadcast` | `8 / 8 / 8 / 7 / 8` | `none` | `none` | `0.000` | `1` | `True` | `True` |
| `Incidence Broadcast` | `8 / 8 / 8 / 7 / 8` | `none` | `none` | `0.000` | `1` | `True` | `True` |
| `Exclusive Claim` | `6 / 8 / 10 / 8 / 10` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=4, k=2) ((1, 2), (1, 3), (3, 4))` | `0.087` | `4` | `False` | `True` |
| `Budget Routing` | `8 / 8 / 10 / 7 / 10` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=4, k=2) ((1, 3), (2, 4), (3, 4))` | `0.322` | `3` | `False` | `True` |
| `Committed Allocation` | `11 / 8 / 12 / 7 / 12` | `(p=3, k=2) ((1, 2), (1, 3))` | `(p=3, k=2) ((1, 2), (1, 3))` | `2.883` | `12` | `False` | `True` |

## Controls

- `broadcast_control` stays flat on the full scan.
  Seed counts: runtime `8`, coordinate `8`, incidence `8`.
  `coordinate_curvature_gap = 0.000` and `fiber_holonomy_rank = 1`.
- `incidence_local_progress` stays flat on the full scan.
  Seed counts: runtime `8`, coordinate `8`, incidence `8`.
  `coordinate_curvature_gap = 0.000` and `fiber_holonomy_rank = 1`.

## First Positive Counterexamples

### `exclusive_overlap_claim`

- first coordinate split: `(p=3, k=2, |A|=2)` with family `((1, 2), (1, 3))`
- quotient counts: runtime `6`, coordinate `8`, old `8`, incidence `10`, family `8`, full assignment `10`
- curvature gap: `-0.415` bits
- fiber holonomy rank: `2`
- incidence exact: `True`
- family-local exact: `False`
- full assignment exact: `True`
- witness coordinate: `(1, 0, 1)`
- left trace `u`: `[1, 3]`
- right trace `v`: `[3, 1]`
- suffix `w`: `[]`
- outputs now: `()` versus `((1, 3),)`
- outputs after suffix: `()` versus `((1, 3),)`
- same-now / future-separate: `False`
- nontrivial coordinate fibers: `(1, 0, 1) -> 2, (1, 1, 1) -> 2`
- first positive `kappa_pi`: `(p=4, k=2)` with family `((1, 2), (1, 3), (3, 4))` and gap `0.087` bits

### `shared_overlap_budget`

- first coordinate split: `(p=3, k=2, |A|=2)` with family `((1, 2), (1, 3))`
- quotient counts: runtime `8`, coordinate `8`, old `8`, incidence `10`, family `7`, full assignment `10`
- curvature gap: `0.000` bits
- fiber holonomy rank: `2`
- incidence exact: `True`
- family-local exact: `False`
- full assignment exact: `True`
- witness coordinate: `(1, 1, 0)`
- left trace `u`: `[1, 2]`
- right trace `v`: `[2, 1]`
- suffix `w`: `[]`
- outputs now: `((1, 2),)` versus `()`
- outputs after suffix: `((1, 2),)` versus `()`
- same-now / future-separate: `False`
- nontrivial coordinate fibers: `(1, 1, 0) -> 2, (1, 1, 1) -> 2`
- first positive `kappa_pi`: `(p=4, k=2)` with family `((1, 3), (2, 4), (3, 4))` and gap `0.322` bits

### `committed_allocation`

- first coordinate split: `(p=3, k=2, |A|=2)` with family `((1, 2), (1, 3))`
- quotient counts: runtime `11`, coordinate `8`, old `8`, incidence `12`, family `7`, full assignment `12`
- curvature gap: `0.459` bits
- fiber holonomy rank: `2`
- incidence exact: `True`
- family-local exact: `False`
- full assignment exact: `True`
- witness coordinate: `(1, 0, 0)`
- left trace `u`: `[{1->(1, 2)}]`
- right trace `v`: `[{1->(1, 3)}]`
- suffix `w`: `[{2->(1, 2)}]`
- outputs now: `((2,),)` versus `((3,),)`
- outputs after suffix: `((),)` versus `((3,),)`
- same-now / future-separate: `False`
- nontrivial coordinate fibers: `(1, 0, 0) -> 2, (1, 0, 1) -> 2, (1, 1, 0) -> 2`
- first positive `kappa_pi`: `(p=3, k=2)` with family `((1, 2), (1, 3))` and gap `0.459` bits

## Overall First Coordinate Split

The lexicographically first world where full coordinate state fails is `((1, 2), (1, 3))` at `(p=3, k=2)`, reached by `exclusive_overlap_claim`.
It has `|Q_runtime| = 6` and `|Q_coordinate| = 8`, with `coordinate_curvature_gap = -0.415` bits.

## Overall First Positive Curvature Gap

The lexicographically first world with `kappa_pi > 0` is `((1, 2), (1, 3))` at `(p=3, k=2)`, reached by `committed_allocation`.
It has `|Q_runtime| = 11` and `|Q_coordinate| = 8`, so `coordinate_curvature_gap = 0.459` bits.

## Interpretation

No tested semantics on this library produced a world where `full_assignment` itself failed.
So the current search now separates two boundaries cleanly: coordinate state can fail, and `committed_allocation` reproduces the known positive `kappa_pi` gap, but the stronger global hypergraph-runtime theorem is still open.
On the scanned positives, the first exact runtime object is therefore closer to incidence transport on the hypergraph nerve than to an irreducibly global family state.

## Artifacts

- JSON: [runtime_hypergraph_curvature_search.json](runtime_hypergraph_curvature_search.json)
- Figure: [runtime_hypergraph_curvature_search.svg](runtime_hypergraph_curvature_search.svg)
- Note: [runtime-hypergraph-curvature.md](../docs/writing/runtime-hypergraph-curvature.md)
