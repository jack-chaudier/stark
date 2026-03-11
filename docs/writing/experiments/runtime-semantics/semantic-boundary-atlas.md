# Semantic Boundary Atlas

## Thesis

The new atlas sharpens the family-memory program one step further.

We no longer only know that:

- the contract can already be hypergraph-valued,
- the old runtime summary can fail after semantic enrichment,
- and overlap can matter.

We now know where those effects separate.

> On the fixed witness carrier, readout-only semantic enrichment can break the old runtime quotient, open a real family-runtime tax over the old variable channel, and even make overlap necessary for the first break. But it still cannot force genuinely non-coordinate runtime state. Hypergraph complexity enters the contract layer immediately, the teaching layer next, and the runtime automaton only after the carrier or composition law itself changes.

That is the boundary result the new atlas adds.

## Source Basis

This note uses only local artifacts already generated in the workspace:

- [family-memory-contract-and-runtime.md](../family-runtime/family-memory-contract-and-runtime.md)
- [runtime-collapse-boundary.md](../family-runtime/runtime-collapse-boundary.md)
- [semantic_boundary_atlas.md](../../../../results/runtime-semantics/semantic-boundary-atlas/semantic_boundary_atlas.md)
- [semantic_boundary_atlas.json](../../../../results/runtime-semantics/semantic-boundary-atlas/semantic_boundary_atlas.json)
- [semantic_boundary_atlas.svg](../../../../results/runtime-semantics/semantic-boundary-atlas/semantic_boundary_atlas.svg)
- [semantic_runtime_thresholds.svg](../../../../results/runtime-semantics/semantic-boundary-atlas/semantic_runtime_thresholds.svg)
- [semantic_teaching_atlas.svg](../../../../results/runtime-semantics/semantic-boundary-atlas/semantic_teaching_atlas.svg)

## 1. What The Atlas Actually Varies

The carrier and composition law stay fixed throughout:

- witness states are still `(depth, coords)`,
- composition is still the existing witness semigroup,
- the old runtime variable channel still means the completed-variable channel induced by that carrier.

Only the family readout changes.

The atlas scans:

- the binary baseline,
- additive partial activation,
- capped additive activation,
- heterogeneous variable weights,
- heterogeneous family thresholds,
- order-sensitive completion,
- multilevel local progress,
- overlap bonus,
- overlap exclusion.

The exact search range is:

- `p in {2,3,4}`,
- `k <= 3`,
- exact full-union antichains on `[p]`.

So this is not a vague qualitative sweep.
It is an exact small-world atlas over a finite semantic library.

## 2. The First Breaks Already Separate Into Three Kinds

The new atlas finds three distinct minimal break types.

### Coordinate-level

Several enrichments break as soon as a single non-singleton family edge can read partial progress:

- `additive_partial_activation`,
- `capped_additive_activation`,
- `heterogeneous_variable_weights`,
- `order_sensitive_completion`,
- `multilevel_local_progress`.

Their smallest break is the same exact world:

- `(p=2, k=2)`,
- family `{{1,2}}`.

So partial progress alone is enough to destroy the old runtime quotient.

### Family-specific but not overlap-specific

`heterogeneous_family_thresholds` is the first exact counterexample where multiple families matter before overlap does.

Its smallest break is:

- `(p=3, k=2)`,
- family `{{1,2}, {3}}`.

That is the first non-overlap family-specific runtime break in the current program.

### Genuinely hypergraph-specific

The first overlap-required runtime breaks appear exactly where they should:

- `overlap_bonus`,
- `overlap_exclusion`.

Both first break on:

- `(p=3, k=2)`,
- family `{{1,2}, {1,3}}`.

So overlap is now experimentally visible at runtime.
But it is visible in the **readout semantics**, not yet in the runtime carrier.

## 3. What Is Proved Versus What Is Observed

### Exact by construction

For every readout in the atlas, full coordinate state is exact.

That part is not merely empirical.
It is immediate from the setup:

- the carrier is fixed,
- composition is fixed,
- each enriched output is a deterministic function of the composed witness state and the fixed family parameter.

So any such readout still factors through `(depth, coords)`.

This gives the clean negative statement:

> No readout-only enrichment on the fixed witness carrier can force genuinely non-coordinate runtime state.

That is an exact proposition, not just a scan result.

### Observed on the exact atlas

What the scan adds is the fine structure *inside* that theorem-shaped boundary:

- which enrichments break first,
- which require overlap for the first break,
- which open a positive family-runtime tax over the old variable channel,
- and which change the teaching layer.

Those are exact on the scanned finite worlds, but not yet proved in closed form beyond the scan.

## 4. Runtime Complexity Now Has A New Taxonomy

The old runtime boundary already said:

- binary completion collapses to `(depth, completed-variable set)`.

The atlas now says more.

### Binary completion is the unique stable point in the current library

The binary baseline is the only scanned semantics with:

- no old-summary break,
- no family-runtime tax over the old variable channel.

### Family-runtime tax is real but not uniform

Some enrichments open a family-runtime tax immediately:

- `capped_additive_activation`,
- `order_sensitive_completion`,
- `multilevel_local_progress`,
- `overlap_bonus`,
- `overlap_exclusion`.

Some do not at their smallest break:

- `additive_partial_activation` first breaks at `(2,2,{{1,2}})` with family bits still below variable bits.

So there are now two different questions:

1. when does the old summary fail,
2. when does family runtime become strictly more expensive than the old variable channel.

Those thresholds do not coincide.

### Strict answer < variable < family worlds do exist

The atlas also finds exact worlds with a full three-rung chain:

- `additive_partial_activation`,
- `heterogeneous_variable_weights`,
- `heterogeneous_family_thresholds`,
- `order_sensitive_completion`,
- `multilevel_local_progress`.

So the old intuition about staged loss is now visible even inside the readout-only regime.

But it is not universal.

For `overlap_bonus` and `overlap_exclusion`, the robust signature is weaker:

- `family > variable`,
- while answer can remain comparatively rich.

So the clean runtime law is not one single chain.
It is a family of chain types indexed by semantics.

## 5. Teaching Complexity Splits Away From Runtime Complexity

This is one of the strongest surprises in the atlas.

The old subset-probe bank does not respond uniformly to semantic enrichment.

### Family teaching stays trivial for many enrichments

On the scanned nontrivial classes:

- additive,
- capped,
- weighted,
- family-threshold,
- multilevel,
- overlap bonus

all still have family basis size `1`.

So even after the old runtime summary fails, family teaching can remain cheap.

### Family teaching becomes genuinely nontrivial under exclusion

`overlap_exclusion` is the first atlas case where family teaching is no longer trivial.

At `(p=3, k=2)`:

- family basis size jumps to `3`,
- family teaching remains exact.

So exclusion is the first semantics where overlap matters not only for runtime breaking, but also for how the family must be taught.

### Order-sensitive completion is stronger still

On the same nontrivial class:

- answer teaching is inexact under the old subset probes,
- variable teaching is inexact,
- family teaching is inexact.

So order sensitivity produces the first clear observational blind spot:

> runtime remains coordinate-exact, but the old subset-probe bank is no longer family-exact at all.

That is a different kind of boundary from the runtime tax.

## 6. The New Three-Layer Boundary

The atlas now supports a sharper hierarchy.

### Layer 1: contract hypergraph

This was already visible before the atlas:

- raw antichains are exact at the contract layer,
- coarse contract summaries fail.

### Layer 2: teaching / observation

The atlas adds that semantic enrichment can make observation harder even before it changes the runtime carrier:

- family teaching can stay trivial,
- become nontrivial,
- or fail under the old probe bank.

So the observational layer has its own boundary, separate from runtime quotient size.

### Layer 3: runtime automaton

The runtime layer now splits in two:

- the old completed-set quotient fails quickly under enrichment,
- but the full coordinate carrier still remains exact throughout the atlas.

So hypergraph complexity has still **not** entered the runtime automaton itself on the fixed carrier.

That is the deepest boundary sentence the current artifacts support.

## 7. What The Next Theorem Must Change

The previous open question was:

- can overlapping families force a new runtime object?

The atlas answers:

- not by readout enrichment alone.

If the goal is true runtime hypergraph memory, the next theorem has to leave the readout-only regime.

The minimal next move is no longer:

- add another output channel.

It is:

- enrich the carrier,
- or enrich composition,
- so that future behavior is no longer a function of named coordinate progress alone.

That is where family-specific residual deficits, overlap-conditioned latent state, or edge-memory carriers become mathematically necessary.

So the semantic boundary atlas does not close the program.
It tells us exactly where to dig next.

## 8. Takeaways

- Binary completion is special: it is the only scanned semantics that preserves the old runtime collapse.
- Readout-only enrichment can create coordinate-level, family-specific, and overlap-required breaks.
- Overlap can already be necessary for the first runtime break.
- But fixed-carrier readout enrichment still cannot force non-coordinate runtime state.
- Teaching complexity can split away from runtime complexity before the carrier changes.
- `overlap_exclusion` is the first semantics with nontrivial exact family teaching.
- `order_sensitive_completion` is the first semantics where the old subset-probe bank becomes family-inexact.
- The next true runtime hypergraph theorem must change the carrier or the composition law, not just the readout.
