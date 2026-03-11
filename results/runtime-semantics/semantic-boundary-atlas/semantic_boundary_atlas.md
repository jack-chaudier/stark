# Semantic Boundary Atlas

This atlas keeps the witness carrier and the witness composition law fixed, and varies only the family readout.

The exact boundary question is no longer whether overlapping families matter in the abstract. It is where they first become computationally necessary: in the contract, in the probe bank, or in the runtime automaton itself.

## Scope

This artifact is exact on the scanned semantic library and on the reported exact antichain search range `p in [2, 3, 4]`, `k <= 3`.

## Aggregate boundary

- semantic enrichments scanned: `8` plus the binary baseline
- exact antichain search range: `p in [2, 3, 4]`, `k <= 3`
- old-summary runtime collapse survives only for the binary baseline
- every readout-only enrichment still factors exactly through the full coordinate carrier `(depth, coords)`
- no scanned readout-only enrichment produced a genuinely non-coordinate runtime counterexample
- overlap-required runtime breaks first appear in the `overlap_bonus` and `overlap_exclusion` readouts
- the old subset-probe teaching bank stays trivial for many enrichments, becomes nontrivial for `overlap_exclusion`, and becomes inexact for `order_sensitive_completion`

## First Breaks

| semantics | first old-summary break | break type | answer bits | variable bits | family bits | first family>variable gap | same-now / future-separate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `binary_completion` | none on scan | `preserved` | - | - | - | none on scan | - |
| `additive_partial_activation` | `(p=2, k=2)`, `((1, 2),)` | `coordinate_level` | `2.322` | `2.585` | `2.322` | `(p=3, k=2)` | `True` |
| `capped_additive_activation` | `(p=2, k=2)`, `((1, 2),)` | `coordinate_level` | `3.170` | `2.585` | `3.170` | `(p=2, k=2)` | `True` |
| `heterogeneous_variable_weights` | `(p=2, k=2)`, `((1, 2),)` | `coordinate_level` | `2.585` | `2.585` | `2.585` | `(p=3, k=2)` | `True` |
| `heterogeneous_family_thresholds` | `(p=3, k=2)`, `((1, 2), (3,))` | `family_specific_not_overlap_specific` | `2.585` | `3.322` | `3.322` | `(p=3, k=2)` | `True` |
| `order_sensitive_completion` | `(p=2, k=2)`, `((1, 2),)` | `coordinate_level` | `3.170` | `2.585` | `3.170` | `(p=2, k=2)` | `True` |
| `multilevel_local_progress` | `(p=2, k=2)`, `((1, 2),)` | `coordinate_level` | `3.700` | `2.585` | `3.700` | `(p=2, k=2)` | `True` |
| `overlap_bonus` | `(p=3, k=2)`, `((1, 2), (1, 3))` | `genuinely_hypergraph_specific` | `4.392` | `3.322` | `4.858` | `(p=3, k=2)` | `True` |
| `overlap_exclusion` | `(p=3, k=2)`, `((1, 2), (1, 3))` | `genuinely_hypergraph_specific` | `4.087` | `3.322` | `4.087` | `(p=3, k=2)` | `True` |

### Interpretation

- `additive`, `capped`, `weights`, `order`, and `multilevel` all break at the coordinate level on the smallest non-singleton world `(p=2, k=2, A={{1,2}})`.
- `heterogeneous_family_thresholds` first breaks on a family-specific but non-overlap world: multiple families matter, but overlap is not yet required.
- `overlap_bonus` and `overlap_exclusion` are the first readouts whose smallest break already requires overlapping families.
- No semantic in the atlas produced a runtime failure of the full coordinate summary. That is structural: every readout here is still a deterministic function of the composed witness state and the fixed family parameter.

## Runtime Threshold Comparisons

The variable channel keeps its old meaning throughout this atlas: it is still the completed-variable runtime channel induced by the fixed witness carrier. The family channel is the enriched family readout. So a positive `family - variable` bit gap measures how much more runtime information the readout needs than the old witness-visible variable channel preserves.

| semantics | world used | answer bits | variable bits | family bits | family - variable | family - answer | strict answer < variable < family |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `binary_completion` | `(p=3, k=2)`, `((1,), (2, 3))` | `2.585` | `3.322` | `3.322` | `0.000` | `0.737` | `False` |
| `additive_partial_activation` | `(p=3, k=2)`, `((1, 2), (1, 3))` | `2.322` | `3.322` | `3.459` | `0.138` | `1.138` | `True` |
| `capped_additive_activation` | `(p=2, k=2)`, `((1, 2),)` | `3.170` | `2.585` | `3.170` | `0.585` | `0.000` | `True` |
| `heterogeneous_variable_weights` | `(p=3, k=2)`, `((1,), (2, 3))` | `2.807` | `3.322` | `3.459` | `0.138` | `0.652` | `True` |
| `heterogeneous_family_thresholds` | `(p=3, k=2)`, `((1, 2), (1, 3))` | `2.322` | `3.322` | `3.585` | `0.263` | `1.263` | `True` |
| `order_sensitive_completion` | `(p=2, k=2)`, `((1, 2),)` | `3.170` | `2.585` | `3.170` | `0.585` | `0.000` | `True` |
| `multilevel_local_progress` | `(p=2, k=2)`, `((1, 2),)` | `3.700` | `2.585` | `3.700` | `1.115` | `0.000` | `True` |
| `overlap_bonus` | `(p=3, k=2)`, `((1, 2), (1, 3))` | `4.392` | `3.322` | `4.858` | `1.536` | `0.466` | `False` |
| `overlap_exclusion` | `(p=3, k=2)`, `((1, 2), (1, 3))` | `4.087` | `3.322` | `4.087` | `0.766` | `0.000` | `False` |

### Runtime observations

- `additive_partial_activation` is the cleanest first break of the old summary, but its smallest exact world still has `family bits < variable bits`; it breaks the old summary without yet opening a family-runtime tax.
- `capped_additive_activation`, `order_sensitive_completion`, `multilevel_local_progress`, `overlap_bonus`, and `overlap_exclusion` all open a positive family-runtime tax over the old variable channel.
- Strict `answer < variable < family` worlds do appear for several enrichments, including `additive_partial_activation`, `heterogeneous_variable_weights`, `heterogeneous_family_thresholds`, `order_sensitive_completion`, and `multilevel_local_progress`.
- That strict chain is not universal, though. The robust boundary statement on the fixed carrier is still weaker and cleaner: semantic enrichment can force `family > variable` without ever defeating full coordinate exactness.

## Candidate Runtime Summaries

Each first-break world was tested against the same summary candidates:

- `old_summary = (depth, completed set)`
- `present_complete = (depth, present set, completed set)`
- `trinary_progress = (depth, named 0/1/2 progress levels)`
- `full_progress = (depth, coords)`
- `sorted_progress` and `progress_histogram` as exchangeable compressions

The exact lesson is stable:

- `old_summary` fails on every enriched first-break world,
- `full_progress` is exact everywhere by construction,
- exchangeable compressions fail quickly once variable identity or order matters,
- some overlap-driven readouts already collapse to `present_complete` on their smallest break worlds, so not every enrichment needs the full coordinate vector on its first counterexample.

## Teaching Complexity Follow-up

Teaching uses the same subset-probe bank as the contract-layer scans: each probe completes exactly a chosen survivor subset and reads out answer / variable / family responses under the enriched semantics.

| semantics | group | families | answer basis | variable basis | family basis | family exact | first family-teaching change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `binary_completion` | `(p=3, k=2)` | `7` | `6` | `3` | `1` | `True` | none on scanned nontrivial groups |
| `additive_partial_activation` | `(p=3, k=2)` | `7` | `None` | `2` | `1` | `True` | none on scanned nontrivial groups |
| `capped_additive_activation` | `(p=3, k=2)` | `7` | `6` | `3` | `1` | `True` | none on scanned nontrivial groups |
| `heterogeneous_variable_weights` | `(p=3, k=2)` | `7` | `None` | `2` | `1` | `True` | none on scanned nontrivial groups |
| `heterogeneous_family_thresholds` | `(p=3, k=2)` | `7` | `None` | `4` | `1` | `True` | none on scanned nontrivial groups |
| `order_sensitive_completion` | `(p=3, k=2)` | `7` | `None` | `None` | `None` | `False` | `(p=3, k=2)` inexact |
| `multilevel_local_progress` | `(p=3, k=2)` | `7` | `6` | `3` | `1` | `True` | none on scanned nontrivial groups |
| `overlap_bonus` | `(p=3, k=2)` | `7` | `6` | `3` | `1` | `True` | none on scanned nontrivial groups |
| `overlap_exclusion` | `(p=3, k=2)` | `7` | `6` | `3` | `3` | `True` | `(p=3, k=2)` basis `3` |

### Teaching observations

- For many enrichments the family channel is still trivial to teach with the old subset probes: one full-union probe already reveals the family output signature exactly on the scanned nontrivial classes.
- `overlap_exclusion` is the first atlas case where family teaching becomes genuinely nontrivial under the old probe bank.
- `order_sensitive_completion` is stronger still: on the scanned nontrivial classes, the old subset-probe bank is not family-exact at all. Runtime stays coordinate-exact, but observation becomes blind.
- So semantic enrichment does not only move runtime thresholds. It can also split teaching complexity away from runtime complexity.

## Strongest Honest Boundary Statement

What the atlas supports is a three-layer boundary.

1. **Binary completion** is the special case where runtime family state collapses to the old witness-visible summary.
2. **Readout-only enrichments** can break that collapse, widen a real family-runtime tax over the old variable channel, and even make overlap necessary for the first break.
3. **But no readout-only enrichment on the fixed carrier can force non-coordinate runtime state.** To get genuinely hypergraph-valued runtime memory, the carrier or composition law itself must change, not just the readout.

So hypergraph complexity has now been located more sharply:

- it is already exact at the contract layer,
- it can become visible at the teaching layer under semantic enrichment,
- but on the fixed witness carrier it still has not entered the runtime automaton itself.

## Per-Semantic Counterexamples

### `binary_completion`

- description: Baseline current semantics: an edge survives iff every member is complete.
- first break: `none on scan`
- break type: `preserved`
- shared old summary: `n/a`
- left state: `n/a`
- alternate state: `n/a`
- continuation: `n/a`
- now(left) / now(alternate): `n/a`
- future(left) / future(alternate): `n/a`
- same-now / future-separate: `n/a`

### `additive_partial_activation`

- description: Non-singleton edges can activate from summed partial progress.
- first break: `(p=2, k=2)`, family `((1, 2),)`
- break type: `coordinate_level`
- shared old summary: `{'depth': 0, 'completed_variables': []}`
- left state: `(0, (-1, -1))`
- alternate state: `(0, (-1, 0))`
- continuation: `(0, (0, -1))`
- now(left) / now(alternate): `()` / `()`
- future(left) / future(alternate): `()` / `((1, 2),)`
- same-now / future-separate: `True`

### `capped_additive_activation`

- description: Partial progress contributes, but local credit is capped before readout.
- first break: `(p=2, k=2)`, family `((1, 2),)`
- break type: `coordinate_level`
- shared old summary: `{'depth': 0, 'completed_variables': []}`
- left state: `(0, (-1, -1))`
- alternate state: `(0, (-1, 0))`
- continuation: `(1, (1, -1))`
- now(left) / now(alternate): `()` / `()`
- future(left) / future(alternate): `()` / `((1, 2),)`
- same-now / future-separate: `True`

### `heterogeneous_variable_weights`

- description: Variables contribute with fixed heterogeneous weights.
- first break: `(p=2, k=2)`, family `((1, 2),)`
- break type: `coordinate_level`
- shared old summary: `{'depth': 0, 'completed_variables': []}`
- left state: `(0, (-1, -1))`
- alternate state: `(0, (-1, 0))`
- continuation: `(0, (0, -1))`
- now(left) / now(alternate): `()` / `()`
- future(left) / future(alternate): `()` / `((1, 2),)`
- same-now / future-separate: `True`

### `heterogeneous_family_thresholds`

- description: One lexicographically favored family edge activates earlier than the rest.
- first break: `(p=3, k=2)`, family `((1, 2), (3,))`
- break type: `family_specific_not_overlap_specific`
- shared old summary: `{'depth': 0, 'completed_variables': []}`
- left state: `(0, (-1, -1, -1))`
- alternate state: `(0, (-1, 0, -1))`
- continuation: `(0, (0, -1, -1))`
- now(left) / now(alternate): `()` / `()`
- future(left) / future(alternate): `()` / `((1, 2),)`
- same-now / future-separate: `True`

### `order_sensitive_completion`

- description: Non-singleton edges survive only when local progress rises in edge order.
- first break: `(p=2, k=2)`, family `((1, 2),)`
- break type: `coordinate_level`
- shared old summary: `{'depth': 0, 'completed_variables': []}`
- left state: `(0, (-1, -1))`
- alternate state: `(0, (0, -1))`
- continuation: `(1, (-1, 1))`
- now(left) / now(alternate): `()` / `()`
- future(left) / future(alternate): `()` / `((1, 2),)`
- same-now / future-separate: `True`

### `multilevel_local_progress`

- description: Edges read three local progress levels instead of a binary completed/not-completed flag.
- first break: `(p=2, k=2)`, family `((1, 2),)`
- break type: `coordinate_level`
- shared old summary: `{'depth': 0, 'completed_variables': []}`
- left state: `(0, (-1, -1))`
- alternate state: `(0, (-1, 0))`
- continuation: `(2, (2, -1))`
- now(left) / now(alternate): `()` / `()`
- future(left) / future(alternate): `()` / `((1, 2),)`
- same-now / future-separate: `True`

### `overlap_bonus`

- description: Overlap can rescue a present but not-yet-complete edge.
- first break: `(p=3, k=2)`, family `((1, 2), (1, 3))`
- break type: `genuinely_hypergraph_specific`
- shared old summary: `{'depth': 0, 'completed_variables': []}`
- left state: `(0, (-1, -1, -1))`
- alternate state: `(0, (-1, -1, 0))`
- continuation: `(0, (0, 0, -1))`
- now(left) / now(alternate): `()` / `()`
- future(left) / future(alternate): `()` / `((1, 2), (1, 3))`
- same-now / future-separate: `True`

### `overlap_exclusion`

- description: Overlap can suppress an otherwise complete edge.
- first break: `(p=3, k=2)`, family `((1, 2), (1, 3))`
- break type: `genuinely_hypergraph_specific`
- shared old summary: `{'depth': 0, 'completed_variables': []}`
- left state: `(0, (-1, -1, -1))`
- alternate state: `(0, (-1, -1, 0))`
- continuation: `(2, (2, 2, -1))`
- now(left) / now(alternate): `()` / `()`
- future(left) / future(alternate): `((1, 2),)` / `()`
- same-now / future-separate: `True`

## Artifacts

- Figure: [semantic_boundary_atlas.svg](semantic_boundary_atlas.svg)
- Figure: [semantic_runtime_thresholds.svg](semantic_runtime_thresholds.svg)
- Figure: [semantic_teaching_atlas.svg](semantic_teaching_atlas.svg)
- JSON: [semantic_boundary_atlas.json](semantic_boundary_atlas.json)
