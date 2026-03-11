# Stark

**When a system has limited memory, can it still know _why_ it's right — or only _that_ it's right?**

Stark is an exact computational and theoretical investigation into what survives under finite memory: correct answers, the witnesses (reasons) behind them, or the full causal structure. Every result is verified by exhaustive finite search — no approximations, no sampling.

## The Core Finding

Under memory pressure, a system can remain **correct** long after it has lost track of **why** it's correct. We call this the **mirage shelf**: a measurable zone where answers survive but justifications don't.

This isn't a single result — it's a layered decomposition. Stark proves that memory structure is _not_ one thing but a **tower of quotients**, each capturing a different level of causal fidelity. The project traces exactly where each layer breaks, from bare thresholds through witness preservation, family contracts, runtime collapse, and transport holonomy.

## Key Results at a Glance

| Result | What it shows |
|--------|--------------|
| **Witness quotient is exact** | The protected-witness state count `\|Q_(k,p)\| = Σ (d+2)^p` is tight — no wasted states |
| **Causal factorization works** | On 89,291 unique-minimal causal queries, witness-faithful factorization has 0 failures |
| **Mirage shelf is real** | At 1 bit below threshold, answer fidelity = 0.999 while witness fidelity = 0.987 |
| **Hypergraph contracts needed** | Overlapping variable families force a hypergraph-valued contract layer |
| **Runtime stays simple** | Across 6,336 antichain configurations, runtime never exceeds coordinate tracking — 0 collapses |
| **Transport tower is strict** | Pair → simplex → global: each level captures structure the previous one misses |
| **Static ≠ dynamic obstructions** | The first "different now" failure (5 edges) and "different future" failure (4 edges) don't coincide |

## Figures

These five figures capture the program's geometry. Each is self-contained.

### 1. Memory Stratigraphy

How finite probes decompose memory into layers. The gap between "algebraic" and "joint" is structure invisible to probes. The gap between "joint" and "answer" is the mirage shelf — where answers survive but reasons don't.

![Memory stratigraphy](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/quotient-thresholds/separator-closure-experiment/memory_stratigraphy.svg)

### 2. Exact Pareto Frontier

The answer/witness trade-off under budget pressure. Solid lines = answer fidelity, dashed = witness fidelity. When solid rises above dashed, the system "knows" but can't justify. With abstention (right panel), the mirage vanishes.

![Exact Pareto frontier](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/quotient-thresholds/exact-pareto-frontier/exact_pareto_frontier.svg)

### 3. Runtime Collapse Boundary

Even when the contract layer is complex (hypergraph-valued), runtime memory stays simple — just depth and completed variables. 6,336 configurations tested, zero collapses. The first break requires changing the _carrier semantics_, not the combinatorics.

![Runtime-collapse boundary](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/family-runtime/runtime-collapse-boundary/runtime_collapse_boundary.svg)

### 4. Pair vs Simplex Holonomy

Where pairwise variable tracking breaks. The triangle family at (p=3, k=2) is the first exact structure where tracking pairs of variables isn't enough — you need triangle-local (simplex) transport.

![Pair vs simplex holonomy](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/holonomy/pair-vs-simplex-holonomy/pair_vs_simplex_holonomy_search.svg)

### 5. Global Holonomy Atlas

Beyond simplex transport, there are two kinds of failure: **static** (states differ right now) and **dynamic** (states differ in the future). These appear on structurally different families (5-edge cycle vs 4-edge mixed), and the raw global layer admits exact compression.

![Global holonomy atlas](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/holonomy/global-holonomy-atlas/global_holonomy_atlas.svg)

## Reading Guide

### New to the project?

1. **[Short overview](docs/writing/synthesis/selective-memory-master-synthesis-short.md)** — the full program in 3 pages
2. **[Master synthesis](docs/writing/synthesis/selective-memory-master-synthesis.md)** — complete narrative with proofs
3. **[Theorem ledger](docs/writing/synthesis/selective-memory-theorem-ledger.md)** — status of every claim (proved / exact computational / open)

### By question

<details>
<summary><strong>"What is the main theorem?"</strong></summary>

Memory quotients are contract-relative. The bare threshold quotient `M_k` has `((k+1)(k+4))/2` states. The witness quotient `Q_(k,p)` has `Σ (d+2)^p` states. Unique-minimal causal queries factor through the witness quotient exactly.

→ [Master synthesis](docs/writing/synthesis/selective-memory-master-synthesis.md) · [Theorem ledger](docs/writing/synthesis/selective-memory-theorem-ledger.md)
</details>

<details>
<summary><strong>"Why isn't bare memory enough for causality?"</strong></summary>

Bare tropical memory preserves capacity but not witness identity. Six collision groups in the bare quotient map to distinct witness signatures — the quotient is too coarse.

→ [Causal contract refinement](docs/writing/foundations/causal-contract-refinement.md) · [Witness-faithful factorization](docs/writing/foundations/witness-faithful-factorization.md) · [Referee report](results/referee/unique-minimal-referee/unique_minimal_referee.md)
</details>

<details>
<summary><strong>"Where does the mirage shelf come from?"</strong></summary>

The observational quotient tower — canonical → empirical → probe-joint → probe-answer — has strictly decreasing size. The gap between probe-answer and probe-joint is the shelf. It's intrinsic: even after separator closure, the Pareto frontier shows answer-perfect allocations with imperfect witness fidelity.

→ [Phase-transition sweep](results/quotient-thresholds/phase-transition-sweep/phase_transition_sweep.md) · [Pareto frontier](results/quotient-thresholds/exact-pareto-frontier/exact_pareto_frontier.md) · [Finite-probe tower](docs/writing/experiments/quotient-thresholds/finite-probe-quotient-tower.md)
</details>

<details>
<summary><strong>"Where do hypergraphs first matter?"</strong></summary>

Overlapping adjustment families can't be captured by union/core/size, degree signatures, intersection signatures, or orbit summaries. Only the full antichain is exact. But once the family is fixed, runtime collapses to coordinate state.

→ [Overlapping families](results/family-runtime/overlapping-adjustment-families/overlapping_adjustment_families.md) · [Family memory](results/family-runtime/family-memory-exact-search/family_memory_exact_search.md) · [Collapse boundary](results/family-runtime/runtime-collapse-boundary/runtime_collapse_boundary.md)
</details>

<details>
<summary><strong>"What is the current open problem?"</strong></summary>

The holonomy tower — coordinate → assignment → pair → simplex → global — is strict at every level, and static/dynamic obstructions already separate. The raw global layer is compressible. The open question: is the canonical runtime object a cycle/tetra-local quotient on the overlap complex, or something more global?

→ [Holonomy experiments](results/holonomy/) · [Global atlas](results/holonomy/global-holonomy-atlas/global_holonomy_atlas.md)
</details>

## Repo Structure

```
stark/
├── scripts/           # Runnable experiment scripts, grouped by layer
│   ├── referee/       #   Causal contract verification
│   ├── quotient-thresholds/  #   Phase sweeps, Pareto frontiers, separator closure
│   ├── family-runtime/       #   Overlapping families, runtime collapse
│   ├── runtime-semantics/    #   Semantic boundary, carrier experiments
│   └── holonomy/             #   Assignment → pair → simplex → global
├── results/           # Outputs: JSON data, markdown reports, SVG figures
│   └── (mirrors scripts/ layout)
└── docs/writing/      # Theory and synthesis
    ├── synthesis/     #   Master narrative, short overview, theorem ledger
    ├── foundations/   #   Contract refinement, factorization, representation
    └── experiments/   #   Per-layer experiment notes
```

Every script follows the same pattern: exact finite scan → JSON data → markdown report → SVG figure(s).

## Reproducibility

All experiments are exact and deterministic. Representative scripts:

- [`unique_minimal_referee.py`](scripts/referee/unique_minimal_referee.py) — verifies causal factorization on 325,404 queries
- [`phase_transition_sweep.py`](scripts/quotient-thresholds/phase_transition_sweep.py) — measures the mirage shelf
- [`exact_pareto_frontier.py`](scripts/quotient-thresholds/exact_pareto_frontier.py) — computes answer/witness trade-off envelopes
- [`runtime_collapse_boundary.py`](scripts/family-runtime/runtime_collapse_boundary.py) — tests 6,336 antichains for runtime collapse
- [`global_holonomy_atlas.py`](scripts/holonomy/global_holonomy_atlas.py) — classifies beyond-simplex obstructions

Verification: [`causal_contract_counterexamples.py`](scripts/referee/causal_contract_counterexamples.py) with [saved output](results/referee/causal-contract-counterexamples/causal_contract_counterexamples.txt).

## Current Boundary

The strongest clean statement:

> On the fixed witness carrier, pair transport breaks assignment exactness; simplex transport breaks pair exactness; and beyond simplex, static and dynamic obstructions separate on different family structures. The raw global layer admits exact compression. The next question is whether the canonical runtime object lives on a local quotient of the overlap complex or requires genuinely global tokens.
