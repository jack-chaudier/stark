# Runtime Hypergraph Curvature

## Thesis

The current curvature scan suggests that the first true runtime object beyond the flat coordinate carrier is incidence transport on the hypergraph nerve, not yet a genuinely global family state.

## Source Basis

- [runtime_hypergraph_curvature_search.md](../../../../results/runtime-semantics/runtime-hypergraph-curvature/runtime_hypergraph_curvature_search.md)
- [runtime_hypergraph_curvature_search.json](../../../../results/runtime-semantics/runtime-hypergraph-curvature/runtime_hypergraph_curvature_search.json)
- [resource_carrier_boundary.md](../../../../results/runtime-semantics/resource-carrier-boundary/resource_carrier_boundary.md)
- [semantic-boundary-atlas.md](semantic-boundary-atlas.md)

## Exact Scan Boundary

On the scanned library:

- `broadcast_control` and `incidence_local_progress` have zero coordinate curvature everywhere.
- `committed_allocation` reproduces the known positive `kappa_pi` gap from the resource-carrier boundary; on the scanned grid its first positive world is `{{1,2}, {1,3}}`.
- `exclusive_overlap_claim` and `shared_overlap_budget` also create coordinate splits, but they do not improve the positive-control boundary.
- in every positive world on the scan, `full_assignment` remains exact.

So the current evidence is:

> overlap can force runtime curvature beyond the full coordinate witness state, but the first curved runtime object still factors through incidence-resolved assignment rather than a genuinely global hypergraph memory state.

The committed-allocation control reaches `max kappa_pi = 2.883` bits on the scanned grid.

## Conjecture Template

For deterministic prefix-compositional carriers built from per-variable overlap transport on a fixed antichain family, the first exact runtime object is the incidence-transport quotient on the hypergraph nerve.

Equivalently:

- coordinate state can be too coarse,
- family-local summaries can be too coarse,
- but incidence-resolved assignment remains exact on the scanned library.

The next true runtime-hypergraph theorem would therefore require a carrier or composition law where even incidence-resolved assignment has nontrivial holonomy.
