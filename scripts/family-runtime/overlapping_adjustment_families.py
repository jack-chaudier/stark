#!/usr/bin/env python3
"""Exploratory search for overlapping minimal-adjustment families.

This is the first explicit step toward the `Q_(k, A)` program.

We search ordered DAG queries for cases with multiple overlapping minimal
adjustment sets, then look for collisions showing that variable-wise survivor
information is too coarse to preserve family survival.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "README.md").exists())
SCRIPTS_ROOT = ROOT / "scripts"
for candidate in [SCRIPTS_ROOT] + sorted(path for path in SCRIPTS_ROOT.iterdir() if path.is_dir()):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from unique_minimal_referee import graph_from_mask, has_directed_path, minimal_adjustment_sets, ordered_dag_id

RESULTS_DIR = ROOT / "results" / "family-runtime" / "overlapping-adjustment-families"

Graph = Dict[int, Set[int]]


def edges_of(graph: Graph) -> List[Tuple[int, int]]:
    return sorted((src, dst) for src, dests in graph.items() for dst in dests)


def overlap_family(family: Sequence[Tuple[int, ...]]) -> bool:
    sets = [set(item) for item in family]
    for left, right in combinations(sets, 2):
        if left != right and left & right:
            return True
    return False


def family_survival_signature(
    family: Sequence[Tuple[int, ...]],
    universe: Sequence[int],
) -> Tuple[Tuple[int, ...], ...]:
    signature = []
    family_sets = [set(item) for item in family]
    for mask in range(1 << len(universe)):
        survivors = {universe[index] for index in range(len(universe)) if mask & (1 << index)}
        surviving_edges = tuple(sorted(tuple(edge) for edge in family if set(edge).issubset(survivors)))
        signature.append(surviving_edges)
    return tuple(signature)


def render_svg(counterexample_pairs: Sequence[Dict[str, object]]) -> str:
    width = 980
    height = 280
    panel_width = 430
    panel_gap = 44
    left_margin = 42
    top = 54
    radius = 18
    colors = {
        "node": "#22577a",
        "edge": "#c44536",
        "frame": "#d9e2ec",
    }
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #1f2933; }",
        ".title { font-size: 14px; font-weight: 700; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fffdf8"/>',
        f'<text x="{left_margin}" y="24" class="title">Overlapping Adjustment Families: Same Variables, Different Hypergraphs</text>',
    ]
    for pair_index, example in enumerate(counterexample_pairs[:2]):
        x0 = left_margin + pair_index * (panel_width + panel_gap)
        lines.append(f'<rect x="{x0}" y="{top}" width="{panel_width}" height="186" fill="#ffffff" stroke="{colors["frame"]}" stroke-width="1"/>')
        lines.append(f'<text x="{x0 + 10}" y="{top - 12}" class="title">{example["label"]}</text>')
        lines.append(f'<text x="{x0 + 10}" y="{top + 18}">family {example["family"]}</text>')
        universe = list(example["universe"])
        positions = {
            universe[0]: (x0 + 110, top + 102),
            universe[1]: (x0 + 206, top + 60),
            universe[2]: (x0 + 302, top + 102),
        }
        for edge in example["family"]:
            a, b = edge
            xa, ya = positions[a]
            xb, yb = positions[b]
            lines.append(f'<line x1="{xa}" y1="{ya}" x2="{xb}" y2="{yb}" stroke="{colors["edge"]}" stroke-width="5" stroke-linecap="round" opacity="0.75"/>')
        for node, (x, y) in positions.items():
            lines.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{colors["node"]}"/>')
            lines.append(f'<text x="{x - 4}" y="{y + 4}" fill="#ffffff">{node}</text>')
        lines.append(f'<text x="{x0 + 10}" y="{top + 154}">survivors (0,2): {example["survivor_test"]}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    overlap_examples = []
    counts_by_n = Counter()
    family_pattern_counts = Counter()
    counterexample_pairs = []

    by_union_and_sizes: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]], List[Dict[str, object]]] = defaultdict(list)

    for n in range(3, 7):
        dag_count = 1 << (n * (n - 1) // 2)
        for mask in range(dag_count):
            graph = graph_from_mask(n, mask)
            for treatment in range(n):
                for outcome in range(n):
                    if treatment == outcome or not has_directed_path(graph, treatment, outcome):
                        continue
                    family = tuple(sorted(minimal_adjustment_sets(graph, treatment, outcome)))
                    if len(family) <= 1 or not overlap_family(family):
                        continue
                    counts_by_n[n] += 1
                    union = tuple(sorted(set().union(*map(set, family))))
                    sizes = tuple(sorted(len(item) for item in family))
                    core = tuple(sorted(set.intersection(*map(set, family))))
                    record = {
                        "n": n,
                        "graph_id": ordered_dag_id(n, mask),
                        "treatment": treatment,
                        "outcome": outcome,
                        "edges": edges_of(graph),
                        "family": [list(item) for item in family],
                        "union": list(union),
                        "sizes": list(sizes),
                        "core": list(core),
                    }
                    if len(overlap_examples) < 16:
                        overlap_examples.append(record)
                    family_pattern_counts[(n, family)] += 1
                    by_union_and_sizes[(union, sizes)].append(record)

    smallest_overlap_n = min(counts_by_n) if counts_by_n else None

    for key, group in sorted(by_union_and_sizes.items(), key=lambda item: (len(item[1]), item[0]), reverse=True):
        distinct_families = {
            tuple(tuple(edge) for edge in item["family"])
            for item in group
        }
        if len(distinct_families) <= 1:
            continue
        exemplar_by_family = {}
        for item in group:
            family = tuple(tuple(edge) for edge in item["family"])
            exemplar_by_family.setdefault(family, item)
        exemplars = list(exemplar_by_family.values())
        if len(exemplars) >= 2:
            left = exemplars[0]
            right = exemplars[1]
            universe = left["union"]
            survivor_set = [universe[0], universe[2]] if len(universe) >= 3 else universe
            left_survival = [
                edge for edge in left["family"] if set(edge).issubset(set(survivor_set))
            ]
            right_survival = [
                edge for edge in right["family"] if set(edge).issubset(set(survivor_set))
            ]
            counterexample_pairs = [
                {
                    "label": left["graph_id"],
                    "family": left["family"],
                    "universe": universe,
                    "survivor_test": left_survival,
                    "record": left,
                },
                {
                    "label": right["graph_id"],
                    "family": right["family"],
                    "universe": universe,
                    "survivor_test": right_survival,
                    "record": right,
                },
            ]
            break

    payload = {
        "smallest_overlap_n": smallest_overlap_n,
        "counts_by_n": dict(sorted(counts_by_n.items())),
        "top_family_patterns": [
            {
                "pattern": {
                    "n": n,
                    "family": [list(edge) for edge in family],
                },
                "count": count,
            }
            for (n, family), count in family_pattern_counts.most_common(20)
        ],
        "example_queries": overlap_examples,
        "counterexample_pairs": counterexample_pairs,
    }

    md_lines = [
        "# Overlapping Adjustment Families",
        "",
        "This report is the first explicit search step toward a family-level causal memory object `Q_(k, A)`.",
        "",
        "## Aggregate signal",
        "",
        f"- first overlaps appear at `n = {smallest_overlap_n}`",
        f"- overlap counts by `n`: `{dict(sorted(counts_by_n.items()))}`",
        "",
        "## Why variable-wise summaries are too coarse",
        "",
        "The current witness-coordinate quotient only remembers which named variables survive.",
        "That is enough on the unique-minimal class, but it is not enough once multiple overlapping minimal adjustment sets are admissible.",
        "",
    ]
    if counterexample_pairs:
        left, right = counterexample_pairs
        md_lines.extend(
            [
                f"- `{left['label']}` has family `{left['family']}` on universe `{left['universe']}`.",
                f"- `{right['label']}` has family `{right['family']}` on the same universe.",
                "- In both cases every variable in the universe matters individually, so a flat survivor vector cannot tell the two apart.",
                f"- But under the survivor set `{[left['universe'][0], left['universe'][2]]}`, the first family leaves `{left['survivor_test']}` while the second leaves `{right['survivor_test']}`.",
                "",
                "So family survival is genuinely hypergraph-valued: the exact object must remember admissible witness families, not only which variables are available one by one.",
                "",
            ]
        )

    md_lines.extend(
        [
            "## Small explicit examples",
            "",
        ]
    )
    for example in overlap_examples[:8]:
        md_lines.append(
            f"- `{example['graph_id']}` query `({example['treatment']}, {example['outcome']})` -> family `{example['family']}`, union `{example['union']}`, core `{example['core']}`"
        )

    md_lines.extend(
        [
            "",
            "## Experimental implication",
            "",
            "A compact exploratory state representation for this regime is the antichain hypergraph of minimal adjustment families itself, or an equivalent family-survival function on survivor subsets.",
            "",
            "The current search does not prove that the hypergraph antichain is minimal.",
            "It does show that coordinate-wise witness availability is already too coarse on the smallest overlapping cases.",
            "",
        ]
    )

    json_path = RESULTS_DIR / "overlapping_adjustment_families.json"
    md_path = RESULTS_DIR / "overlapping_adjustment_families.md"
    svg_path = RESULTS_DIR / "overlapping_adjustment_families.svg"
    json_path.write_text(json.dumps(payload, indent=2))
    md_path.write_text("\n".join(md_lines))
    if counterexample_pairs:
        svg_path.write_text(render_svg(counterexample_pairs))

    print(
        json.dumps(
            {
                "counts_by_n": dict(sorted(counts_by_n.items())),
                "json_path": str(json_path),
                "md_path": str(md_path),
                "svg_path": str(svg_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
