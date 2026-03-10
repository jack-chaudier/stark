# Selective Memory Master Synthesis: Short Overview

## Abstract

This note is the concise companion to the full synthesis in [selective-memory-master-synthesis.md](selective-memory-master-synthesis.md).
It records the shortest version of what the repository now supports.

The program began with bare tropical threshold memory and asked whether that memory could preserve causal justification.
The answer is now clear.
Bare tropical memory is exact for a bare threshold contract, but it is too coarse for named causal identity.
The correct repair is a protected-witness quotient, and on the unique-minimal causal class that repair is exact.
The later experiments then showed that finite memory fails in layers: answers can remain right before reasons remain identifiable.
The current boundary result is that hypergraph complexity is already exact at the contract layer, can appear at the teaching/probe layer, but has not yet been forced into genuinely non-coordinate runtime state on the fixed witness carrier.

## Executive Thesis

The repository now supports three distinct claims.

First, contract-relative canonicality is real.
There is no single “right” memory quotient independent of task.
For the bare threshold contract the canonical two-sided quotient is `M_k`, with exact state count

`|M_k| = ((k + 1)(k + 4)) / 2`.

For the protected-witness contract the canonical quotient is `Q_(k,p)`, with exact state count

`|Q_(k,p)| = sum_(d=0)^k (d + 2)^p`.

Second, the first positive causal bridge is now exact on a real class.
On witness-faithful unique-minimal causal queries, the causal contract factors through `Q_(k,p)`.
The ordered-DAG referee scanned `325404` treatment-outcome queries, found `89291` unique non-empty minimal cases, admitted all `89291` into the witness-faithful prefix class, and saw `0` residual `Q_(k,p)` failures.

Third, finite memory failure is layered.
The phase sweeps, finite-probe tower, separator-closure experiment, and exact Pareto frontiers show that under budget pressure the answer channel can remain exact before the witness channel does.
That is the current mirage law:

> a system can still be right before it still knows why.

## The Program In One Line

The project moved through the following sequence:

1. bare threshold quotient,
2. witness-preserving repair,
3. unique-minimal causal factorization,
4. phase-transition sweep and mirage shelf,
5. finite-probe quotient tower,
6. separator closure and exact Pareto frontiers,
7. overlapping-family contract memory,
8. runtime-collapse boundary,
9. semantic boundary atlas.

Each layer repaired a specific failure of the previous target.

## Core Exact Results

### Bare and witness quotients

- `|M_3| = 14`, so exact turn-on occurs at `4` bits.
- `|Q_(3,2)| = 54`, so exact turn-on occurs at `6` bits.
- `|Q_(5,3)| = 783`, so exact turn-on occurs at `10` bits.

### Unique-minimal causal factorization

- treatment-outcome queries with directed path: `325404`
- unique non-empty minimal queries: `89291`
- admitted prefix-witness queries: `89291`
- exact `Q_(k,p)` recovery rate: `1.000`
- residual `Q_(k,p)` failures: `0`
- bare collision groups with distinct witness signatures: `6`

### Mirage shelf and quotient tower

The phase sweep shows a robust pre-threshold mirage shelf.
At `Q_(5,3)` one bit below the canonical threshold:

- prefix forcing: answer / witness `0.999 / 0.987`
- suffix forcing: `0.909 / 0.733`
- interleaved forcing: `0.995 / 0.970`

The measured quotient-tower counts make the same point structurally:

- `Q_(5,3)`: canonical `783`, probe-joint `13`, probe-answer `7`
- `causal_referee`: canonical upper bound `2532`, empirical support `15`, probe-joint `15`, probe-answer `4`

with

- `delta(Q_(5,3), P) = 5.912` bits
- `omega(Q_(5,3), P) = 0.893` bits
- `delta(causal_referee, P) = 7.399` bits
- `omega(causal_referee, P) = 1.907` bits

where

- `delta(C, P) = log_2 |Q_C| - log_2 |Q_(C,P)^joint|`
- `omega(C, P) = log_2 |Q_(C,P)^joint| - log_2 |Q_(C,P)^answer|`.

### Separator closure and intrinsic shelf

On the tested synthetic witness families:

- `Q_(3,2)` closes after `3` left actions,
- `Q_(4,2)` after `4`,
- `Q_(5,3)` after `5`,

and the minimal exact basis is the depth ladder `[(1, BOT^p), ..., (k, BOT^p)]`.

Closure eliminates probe deficiency, but does not eliminate the potential mirage interval.
For `Q_(5,3)`, shelf width grows from `0.893` to `4.858` bits along exact closure.

The exact Pareto frontier then shows that the shelf is intrinsic on the measured observational state spaces.
For example:

- on `Q_(5,3)` at `3` bits, perfect answer is achievable while witness-at-perfect-answer is only `0.982`
- on `causal_referee` at `2` bits, perfect answer is achievable while witness-at-perfect-answer is only `0.641`

### Family memory

Overlapping minimal adjustment families force a new contract object.
Across `52` normalized overlapping-family worlds:

- `union/core/size` fails,
- degree and intersection signatures fail,
- orbit summaries fail,
- the full antichain is exact.

But at runtime, once the family is fixed, the scanned worlds collapse:

- exact runtime state factors through `(depth, completed-variable set)`
- observed family-runtime count law is `k + 2^p`
- variable-runtime and family-runtime thresholds match on the scanned worlds

So the split is:

> hypergraph-valued contract, variable-valued fixed-family runtime.

### Runtime-collapse boundary

The collapse survives passage to arbitrary antichains under current binary-completion semantics.
On exact full-union antichains with `p <= 5`, `k <= 3`:

- exact `(p,k)` classes scanned: `11`
- exact antichains scanned: `6336`
- runtime-collapse failures: `0`

The observed exact family-runtime law remains `k + 2^p`.
This moved the boundary from combinatorics to semantics.

### Semantic boundary atlas

The semantic atlas varies only the readout on the fixed witness carrier.
It finds three kinds of first break:

1. coordinate-level,
2. family-specific but non-overlap,
3. overlap-required.

The first overlap-required breaks occur for `overlap_bonus` and `overlap_exclusion` at `(p=3, k=2, A={{1,2},{1,3}})`.
But no scanned readout-only enrichment forces genuinely non-coordinate runtime state, because full coordinate progress remains exact by construction.

## Current Boundary Result

The strongest clean statement now supported is:

> On the fixed witness carrier, hypergraph complexity is exact at the contract layer, can become visible at the teaching/probe layer, and readout-only enrichment can break the old runtime quotient and even require overlap for the first break. But no scanned readout-only enrichment forces genuinely non-coordinate runtime state. Therefore the next true runtime-hypergraph theorem must change the carrier or the composition law, not just the readout.

## What Is Proved, Exact, And Open

### Proved

- bare threshold quotient ladder
- protected-witness quotient and symmetry count
- witness-faithful factorization on the unique-minimal class
- fixed-carrier proposition: readout-only enrichment still factors through full coordinate state

### Exact computational

- unique-minimal referee
- phase sweep and geometry sweep
- finite-probe quotient tower counts
- separator closure
- exact Pareto frontier
- family-memory exact search
- arbitrary-antichain runtime-collapse boundary
- semantic boundary atlas

### Open seam

The next disciplined target is no longer to ask whether hypergraphs matter.
They already do.
The real open seam is:

> what carrier or composition enrichment is the first to force genuinely non-coordinate runtime memory?

## Figure Guide

The strongest starting figures are:

1. [memory_stratigraphy.svg](../../results/memory_stratigraphy.svg)
2. [separator_closure_deficiency.svg](../../results/separator_closure_deficiency.svg)
3. [exact_pareto_frontier.svg](../../results/exact_pareto_frontier.svg)
4. [family_memory_thresholds.svg](../../results/family_memory_thresholds.svg)
5. [runtime_collapse_boundary.svg](../../results/runtime_collapse_boundary.svg)
6. [semantic_boundary_atlas.svg](../../results/semantic_boundary_atlas.svg)

## Companion Files

- Full synthesis: [selective-memory-master-synthesis.md](selective-memory-master-synthesis.md)
- Theorem/status ledger: [selective-memory-theorem-ledger.md](selective-memory-theorem-ledger.md)
