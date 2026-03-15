# Stark

**Stark investigates a simple question about memory and reasoning: when a system runs low on memory, can it still know _why_ it's right — or only _that_ it's right?**

Think of a statistical model that adjusts for confounders to get the right causal answer. Under memory pressure, it may still produce correct answers long after it has lost track of _which_ confounders justified those answers. Stark makes this phenomenon precise, proves where each layer of reasoning breaks, and measures the gap between "correct" and "justified" exactly.

Every result is verified by exhaustive finite search — no approximations, no sampling.

## What Stark Finds

Under memory constraints, correctness and justification come apart in a structured way. Stark proves that memory is not one thing but a **tower of layers**, each preserving a different level of causal fidelity. The main results:

1. **A system can be right without knowing why.** There is a measurable zone — the *mirage shelf* — where answers survive but the reasons behind them don't. For the `Q_(5,3)` witness quotient at 1 bit below its 10-bit threshold under prefix forcing, answer accuracy is 0.999 while justification accuracy drops to 0.987; neighboring forcing modes at the same threshold are materially lower (suffix: 0.909 / 0.733, interleaved: 0.995 / 0.970).

2. **The right memory structure depends on the task.** There is no universal "right" memory format. A bare count of predecessors is enough to know _whether_ an answer exists, but preserving _which_ specific variables justify it requires a richer state — the *witness quotient* — with a precisely calculated cost.

3. **Complexity enters in layers.** Contract-level memory (what the system promises to track) can require complex hypergraph structure. Runtime memory (what the system actually computes with) stays simple — just depth and completed variables — across all 6,336 configurations tested. The boundary between simple and complex is semantic, not combinatorial.

## Key Terminology

| Term | Meaning |
|------|---------|
| **Quotient** | A compressed representation of memory that keeps only the information a given task needs |
| **Witness** | A specific variable (e.g., a confounder) whose identity must be preserved for causal reasoning |
| **Contract** | The promise a memory system makes about what information it will preserve |
| **Mirage shelf** | The zone where a system gives correct answers but has lost the justification for them |
| **Tropical** | Refers to the algebraic framework (max-plus algebra) underlying the memory composition |

## Evidence Summary

| Result | What it shows |
|--------|--------------|
| **Witness quotient is exact** | The witness-preserving state count `\|Q_(k,p)\| = Σ (d+2)^p` is tight — no wasted states |
| **Causal factorization works** | On 89,291 unique-minimal causal queries, witness-faithful factorization has 0 failures |
| **Mirage shelf is real** | On `Q_(5,3)` prefix forcing at 1 bit below the 10-bit threshold, answer fidelity = 0.999 while witness fidelity = 0.987 |
| **Public Grok bridge** | In the companion `dreams` experiment bundle, answer accuracy falls from 0.825 to 0.775 while witness fidelity falls from 0.7867 to 0.5533 as context grows from 4K to 512K |
| **Hypergraph contracts needed** | Overlapping variable families force a hypergraph-valued contract layer |
| **Runtime stays simple** | Across 6,336 antichain configurations, runtime never exceeds coordinate tracking — 0 collapses |
| **Transport tower is strict** | Pair → simplex → global: each level captures structure the previous one misses |
| **Static ≠ dynamic obstructions** | The first "different now" failure (5 edges) and "different future" failure (4 edges) don't coincide |

## Theory To Evidence

The exact-search shelf in `stark` is a theorem-level statement about how answer fidelity can outrun witness fidelity under memory pressure. The companion public experiment in `dreams` measures the same qualitative separation on a frontier model rather than a finite quotient family.

On the March 2026 Grok run in `dreams`, normal-condition answer accuracy falls only from `0.825` at `4K` to `0.775` at `512K`, while witness fidelity falls from `0.7867` to `0.5533`. That widens the empirical mirage gap from `+0.0383` to `+0.2217`. In the witness-removed control, answer accuracy drops to `0.315` at `4K` and `0.275` at `256K`, which is consistent with the broader Stark claim that preserving answerability and preserving the governing witness are different memory tasks.

- Public page: <https://dreams-dun.vercel.app/mirage-shelf-grok-2026-03>
- Artifact bundle: <https://github.com/jack-chaudier/dreams/tree/main/results/mirage-shelf-grok-2026-03>

## Start Here

If you're new to the project, read these in order:

1. **[Short overview](docs/writing/synthesis/selective-memory-master-synthesis-short.md)** — the full program in 3 pages
2. **[Master synthesis](docs/writing/synthesis/selective-memory-master-synthesis.md)** — complete narrative with proofs
3. **[Theorem ledger](docs/writing/synthesis/selective-memory-theorem-ledger.md)** — status of every claim (proved / exact computational / open)

## Figures

These five figures capture the geometry of the program. Each is self-contained.

### 1. Memory Stratigraphy

How different layers of memory separate under finite observation. The gap between "algebraic" (full theoretical state) and "joint" (what finite probes can distinguish) is structure invisible to bounded observers. The gap between "joint" and "answer" is the mirage shelf — correct answers persist but justifications are lost.

![Memory stratigraphy](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/quotient-thresholds/separator-closure-experiment/memory_stratigraphy.svg)

### 2. Exact Pareto Frontier

The trade-off between answer accuracy and justification accuracy under a memory budget. Solid lines = answer fidelity, dashed = witness fidelity. When the solid line rises above the dashed line, the system "knows" but can't justify. The right panel shows that allowing the system to abstain (say "I don't know") eliminates the mirage.

![Exact Pareto frontier](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/quotient-thresholds/exact-pareto-frontier/exact_pareto_frontier.svg)

### 3. Runtime Collapse Boundary

Even when the contract layer is complex (requiring hypergraph structure to specify), the actual runtime memory stays simple — just tracking depth and which variables are completed. 6,336 configurations tested, zero exceptions. The first situation that breaks this simplicity requires changing the _meaning_ of completion, not the combinatorial structure.

![Runtime-collapse boundary](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/family-runtime/runtime-collapse-boundary/runtime_collapse_boundary.svg)

### 4. Pair vs Simplex Holonomy

Where pairwise variable tracking breaks down. At parameters (p=3, k=2), the triangle family is the first exact case where tracking pairs of variables is insufficient — you need triangle-local (simplex) transport to capture the full structure.

![Pair vs simplex holonomy](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/holonomy/pair-vs-simplex-holonomy/pair_vs_simplex_holonomy_search.svg)

### 5. Global Holonomy Atlas

Beyond simplex transport, there are two kinds of failure: **static** (states disagree right now) and **dynamic** (states will diverge in the future). These appear on structurally different families (5-edge cycle vs 4-edge mixed graph), and the raw global layer admits exact compression.

![Global holonomy atlas](https://raw.githubusercontent.com/jack-chaudier/stark/main/results/holonomy/global-holonomy-atlas/global_holonomy_atlas.svg)

## Deeper Questions

<details>
<summary><strong>"What is the main theorem?"</strong></summary>

Memory quotients are contract-relative: changing the task changes the optimal memory structure. For the bare threshold contract, the canonical quotient `M_k` has `((k+1)(k+4))/2` states. For the witness-preserving contract, `Q_(k,p)` has `Σ (d+2)^p` states. On the class of causal queries with a unique minimal adjustment set, the causal contract factors exactly through the witness quotient.

> [Master synthesis](docs/writing/synthesis/selective-memory-master-synthesis.md) · [Theorem ledger](docs/writing/synthesis/selective-memory-theorem-ledger.md)
</details>

<details>
<summary><strong>"Why isn't bare memory enough for causality?"</strong></summary>

Bare tropical memory preserves how many predecessors exist but not which ones they are. Six collision groups in the bare quotient map to distinct witness signatures — the quotient is too coarse to distinguish causal scenarios that require different adjustments.

> [Causal contract refinement](docs/writing/foundations/causal-contract-refinement.md) · [Witness-faithful factorization](docs/writing/foundations/witness-faithful-factorization.md) · [Referee report](results/referee/unique-minimal-referee/unique_minimal_referee.md)
</details>

<details>
<summary><strong>"Where does the mirage shelf come from?"</strong></summary>

The observational quotient tower — canonical → empirical → probe-joint → probe-answer — has strictly decreasing size. The gap between probe-answer and probe-joint is the shelf: the set of states where answers are preserved but justifications are not. Even after closing probing deficiencies, the Pareto frontier shows that some memory budgets achieve perfect answers with imperfect witness recovery.

> [Phase-transition sweep](results/quotient-thresholds/phase-transition-sweep/phase_transition_sweep.md) · [Pareto frontier](results/quotient-thresholds/exact-pareto-frontier/exact_pareto_frontier.md) · [Finite-probe tower](docs/writing/experiments/quotient-thresholds/finite-probe-quotient-tower.md)
</details>

<details>
<summary><strong>"Where do hypergraphs first matter?"</strong></summary>

When causal variables form overlapping groups (e.g., variable 1 appears in two different adjustment sets), simple summaries like union/core/size, degree signatures, and orbit summaries all fail. Only the full family structure (antichain) is exact. But once the family is fixed, runtime collapses to simple coordinate state.

> [Overlapping families](results/family-runtime/overlapping-adjustment-families/overlapping_adjustment_families.md) · [Family memory](results/family-runtime/family-memory-exact-search/family_memory_exact_search.md) · [Collapse boundary](results/family-runtime/runtime-collapse-boundary/runtime_collapse_boundary.md)
</details>

<details>
<summary><strong>"What is the current open problem?"</strong></summary>

The holonomy tower — coordinate → assignment → pair → simplex → global — is strict at every level, and static/dynamic obstructions already separate. The raw global layer is compressible. The open question: is the canonical runtime object a local quotient on the overlap complex, or does it require genuinely global tokens?

> [Holonomy experiments](results/holonomy/) · [Global atlas](results/holonomy/global-holonomy-atlas/global_holonomy_atlas.md)
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

## Setup

Requires Python 3.10+. All scripts use only the standard library — no external dependencies.

```bash
git clone https://github.com/jack-chaudier/stark.git
cd stark

# Run any experiment script directly:
python scripts/referee/unique_minimal_referee.py
```

Each script writes its outputs (JSON data, markdown report, SVG figures) to the corresponding directory under `results/`.

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
