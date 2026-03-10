#!/usr/bin/env python3
"""Exhaustive small-world referee for the unique-minimal witness theorem.

This script works in the narrow regime we can defend cleanly:
- finite ordered DAGs on n <= max_n nodes
- causal queries (T, Y) with a unique non-empty minimal adjustment set
- witness-faithful topological linearizations that place all witnesses before T
- k = |A*| for the causal identification contract

It checks:
1. how many unique-minimal queries fall into the prefix-witness class,
2. how often bare L2 collides across different exact witness targets,
3. whether the witness-refined summary Q_(k,p) recovers the unique set exactly,
4. whether the symmetry quotient recovers the orbit exactly.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

NEG_INF = float("-inf")
BOT = -1
ROOT = Path("/Users/jackg/stark")
RESULTS_DIR = ROOT / "results"

Graph = Dict[int, Set[int]]


@dataclass(frozen=True)
class QueryRecord:
    n: int
    graph_id: str
    treatment: int
    outcome: int
    witness_set: Tuple[int, ...]
    prefix_len: int
    k: int
    bare_state: Tuple[Tuple[int | str, ...], int]
    q_state: Tuple[int, Tuple[int, ...]]
    q_orbit: Tuple[int, ...]
    word: Tuple[str, ...]


def descendants(graph: Graph, start: int) -> Set[int]:
    out: Set[int] = set()
    stack = [start]
    while stack:
        node = stack.pop()
        for child in graph.get(node, set()):
            if child not in out:
                out.add(child)
                stack.append(child)
    out.discard(start)
    return out


def parents(graph: Graph) -> Dict[int, Set[int]]:
    rev = {node: set() for node in graph}
    for src, dests in graph.items():
        for dst in dests:
            rev[dst].add(src)
    return rev


def ancestors_of_set(graph: Graph, nodes: Iterable[int]) -> Set[int]:
    rev = parents(graph)
    out = set(nodes)
    stack = list(nodes)
    while stack:
        node = stack.pop()
        for par in rev.get(node, set()):
            if par not in out:
                out.add(par)
                stack.append(par)
    return out


def moralized_ancestral_graph(graph: Graph, x: int, y: int, z: Set[int]) -> Dict[int, Set[int]]:
    relevant = ancestors_of_set(graph, {x, y, *z})
    rev = parents(graph)
    undirected = {node: set() for node in relevant}

    for src in relevant:
        for dst in graph[src]:
            if dst in relevant:
                undirected[src].add(dst)
                undirected[dst].add(src)

    for child in relevant:
        pars = sorted(par for par in rev.get(child, set()) if par in relevant)
        for a, b in combinations(pars, 2):
            undirected[a].add(b)
            undirected[b].add(a)

    for blocked in z:
        undirected.pop(blocked, None)
    for node in list(undirected):
        undirected[node].difference_update(z)

    return undirected


def is_d_separated(graph: Graph, x: int, y: int, z: Set[int]) -> bool:
    if x in z or y in z:
        return True
    moral = moralized_ancestral_graph(graph, x, y, z)
    if x not in moral or y not in moral:
        return True
    seen = {x}
    stack = [x]
    while stack:
        node = stack.pop()
        if node == y:
            return False
        for nxt in moral.get(node, set()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return True


def manipulated_graph(graph: Graph, treatment: int) -> Graph:
    out = {node: set(dests) for node, dests in graph.items()}
    out[treatment] = set()
    return out


def is_valid_adjustment_set(graph: Graph, treatment: int, outcome: int, subset: Set[int]) -> bool:
    if descendants(graph, treatment) & subset:
        return False
    g_do = manipulated_graph(graph, treatment)
    return is_d_separated(g_do, treatment, outcome, subset)


def has_directed_path(graph: Graph, start: int, end: int) -> bool:
    stack = [start]
    seen = {start}
    while stack:
        node = stack.pop()
        if node == end:
            return True
        for nxt in graph[node]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return False


def minimal_adjustment_sets(graph: Graph, treatment: int, outcome: int) -> List[Tuple[int, ...]]:
    candidate_nodes = sorted(set(graph) - {treatment, outcome} - descendants(graph, treatment))
    valid: List[Tuple[int, ...]] = []
    for size in range(len(candidate_nodes) + 1):
        for combo in combinations(candidate_nodes, size):
            subset = set(combo)
            if not is_valid_adjustment_set(graph, treatment, outcome, subset):
                continue
            if any(set(prev).issubset(subset) for prev in valid):
                continue
            valid = [prev for prev in valid if not subset.issubset(set(prev))]
            valid.append(combo)
    return valid


def graph_from_mask(n: int, mask: int) -> Graph:
    graph: Graph = {i: set() for i in range(n)}
    bit = 0
    for src in range(n):
        for dst in range(src + 1, n):
            if mask & (1 << bit):
                graph[src].add(dst)
            bit += 1
    return graph


def ordered_dag_id(n: int, mask: int) -> str:
    return f"n{n}_m{mask}"


def build_prefix_witness_order(graph: Graph, treatment: int, witnesses: Set[int]) -> Optional[List[int]]:
    indeg = {node: 0 for node in graph}
    for src in graph:
        for dst in graph[src]:
            indeg[dst] += 1

    available = {node for node in graph if indeg[node] == 0}
    order: List[int] = []

    def priority(node: int) -> Tuple[int, int]:
        if node in witnesses:
            return (0, node)
        if node == treatment:
            return (2, node)
        return (1, node)

    while available:
        candidates = sorted(available, key=priority)
        pick = candidates[0]
        available.remove(pick)
        order.append(pick)
        for dst in graph[pick]:
            indeg[dst] -= 1
            if indeg[dst] == 0:
                available.add(dst)

    if len(order) != len(graph):
        return None

    t_index = order.index(treatment)
    if any(order.index(w) > t_index for w in witnesses):
        return None
    return order


def linearize_prefix_witness(order: Sequence[int], treatment: int, witnesses: Set[int]) -> Tuple[str, ...]:
    word: List[str] = []
    for node in order:
        if node == treatment:
            word.append("T")
            break
        if node in witnesses:
            word.append(f"W{node}")
        else:
            word.append("N")
    return tuple(word)


def bare_l2_state(word: Sequence[str], k: int) -> Tuple[Tuple[int | str, ...], int]:
    prefix = 0
    for token in word:
        if token == "T":
            break
        prefix += 1
    weights = tuple(1 if j <= min(prefix, k) else "-inf" for j in range(k + 1))
    return weights, prefix


def q_state(word: Sequence[str], witnesses: Sequence[int], k: int) -> Tuple[int, Tuple[int, ...]]:
    d = 0
    seen: Set[int] = set()
    coords = {w: BOT for w in witnesses}
    for token in word:
        if token == "N":
            d = min(k, d + 1)
            continue
        if token.startswith("W"):
            d = min(k, d + 1)
            seen.add(int(token[1:]))
            continue
        if token == "T":
            for w in seen:
                coords[w] = max(coords[w], d)
            break
    return d, tuple(coords[w] for w in witnesses)


def q_orbit_from_coords(coords: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(sorted(coords))


def recover_witnesses(witnesses: Sequence[int], coords: Tuple[int, ...]) -> Tuple[int, ...]:
    return tuple(w for w, c in zip(witnesses, coords) if c != BOT)


def enumerate_unique_minimal_queries(max_n: int = 6) -> Tuple[List[QueryRecord], Dict[str, object]]:
    records: List[QueryRecord] = []
    stats: Dict[str, object] = {
        "max_n": max_n,
        "ordered_dag_counts": {},
        "queries_with_path": 0,
        "unique_nonempty_queries": 0,
        "prefix_witness_queries": 0,
        "residual_q_failures": 0,
        "residual_orbit_failures": 0,
    }

    for n in range(3, max_n + 1):
        dag_count = 1 << (n * (n - 1) // 2)
        stats["ordered_dag_counts"][str(n)] = dag_count
        for mask in range(dag_count):
            graph = graph_from_mask(n, mask)
            gid = ordered_dag_id(n, mask)
            for treatment in range(n):
                for outcome in range(n):
                    if treatment == outcome:
                        continue
                    if not has_directed_path(graph, treatment, outcome):
                        continue
                    stats["queries_with_path"] += 1
                    adj_sets = minimal_adjustment_sets(graph, treatment, outcome)
                    if len(adj_sets) != 1 or len(adj_sets[0]) == 0:
                        continue
                    stats["unique_nonempty_queries"] += 1
                    witnesses = tuple(sorted(adj_sets[0]))
                    order = build_prefix_witness_order(graph, treatment, set(witnesses))
                    if order is None:
                        continue
                    stats["prefix_witness_queries"] += 1
                    k = len(witnesses)
                    word = linearize_prefix_witness(order, treatment, set(witnesses))
                    bare = bare_l2_state(word, k)
                    q = q_state(word, witnesses, k)
                    orbit = q_orbit_from_coords(q[1])

                    if recover_witnesses(witnesses, q[1]) != witnesses:
                        stats["residual_q_failures"] += 1
                    if orbit != tuple([k] * len(witnesses)):
                        stats["residual_orbit_failures"] += 1

                    records.append(
                        QueryRecord(
                            n=n,
                            graph_id=gid,
                            treatment=treatment,
                            outcome=outcome,
                            witness_set=witnesses,
                            prefix_len=sum(1 for token in word if token != "T"),
                            k=k,
                            bare_state=bare,
                            q_state=q,
                            q_orbit=orbit,
                            word=word,
                        )
                    )

    return records, stats


def summarize(records: List[QueryRecord], stats: Dict[str, object]) -> Dict[str, object]:
    by_p: Dict[int, List[QueryRecord]] = defaultdict(list)
    collision_groups: Dict[Tuple[int, Tuple[Tuple[int | str, ...], int]], List[QueryRecord]] = defaultdict(list)

    for record in records:
        by_p[record.k].append(record)
        collision_groups[(record.k, record.bare_state)].append(record)

    bare_collision_examples = []
    collision_count = 0
    label_distinct_collision_count = 0
    for key, group in collision_groups.items():
        witness_signatures = {record.witness_set for record in group}
        if len(group) >= 2:
            collision_count += 1
        if len(group) >= 2 and len(witness_signatures) >= 2:
            label_distinct_collision_count += 1
            if len(bare_collision_examples) < 8:
                distinct_examples = []
                seen_signatures = set()
                for record in group:
                    signature = record.witness_set
                    if signature in seen_signatures:
                        continue
                    seen_signatures.add(signature)
                    distinct_examples.append(record)
                    if len(distinct_examples) == 4:
                        break
                if not distinct_examples:
                    distinct_examples = group[:4]
                bare_collision_examples.append(
                    {
                        "k": key[0],
                        "bare_state": {"weights": list(key[1][0]), "d_total": key[1][1]},
                        "examples": [
                            {
                                "graph_id": r.graph_id,
                                "query": [r.treatment, r.outcome],
                                "witness_set": list(r.witness_set),
                                "word": list(r.word),
                            }
                            for r in distinct_examples
                        ],
                    }
                )

    summary = {
        **stats,
        "total_prefix_witness_records": len(records),
        "exact_q_recovery_rate": 1.0 if records and stats["residual_q_failures"] == 0 else 0.0,
        "exact_orbit_recovery_rate": 1.0 if records and stats["residual_orbit_failures"] == 0 else 0.0,
        "bare_collision_group_count": collision_count,
        "label_distinct_bare_collision_group_count": label_distinct_collision_count,
        "records_by_k": {
            str(k): {
                "count": len(group),
                "prefix_len_min": min(r.prefix_len for r in group),
                "prefix_len_max": max(r.prefix_len for r in group),
            }
            for k, group in sorted(by_p.items())
        },
        "bare_collision_examples": bare_collision_examples,
    }
    return summary


def render_markdown(summary: Dict[str, object]) -> str:
    lines = [
        "# Unique-Minimal Referee",
        "",
        "This report exhaustively checks the narrow theorem regime implemented by",
        "`scripts/unique_minimal_referee.py`.",
        "",
        "## Scope",
        "",
        f"- Ordered DAGs up to `n = {summary['max_n']}`",
        "- Queries `(T, Y)` with a directed path `T -> ... -> Y`",
        "- Unique, non-empty minimal adjustment sets",
        "- Witness-faithful topological linearizations",
        "- Causal contract instantiated at `k = |A*|`",
        "",
        "## Aggregate counts",
        "",
        f"- Queries with directed treatment-outcome path: `{summary['queries_with_path']}`",
        f"- Unique non-empty minimal queries: `{summary['unique_nonempty_queries']}`",
        f"- Prefix-witness queries admitted by the theorem class: `{summary['prefix_witness_queries']}`",
        f"- Exact `Q_(k,p)` recovery rate: `{summary['exact_q_recovery_rate']:.3f}`",
        f"- Exact orbit recovery rate: `{summary['exact_orbit_recovery_rate']:.3f}`",
        f"- Residual `Q_(k,p)` failures: `{summary['residual_q_failures']}`",
        f"- Bare collision groups across distinct query instances: `{summary['bare_collision_group_count']}`",
        f"- Bare collision groups with distinct witness signatures: `{summary['label_distinct_bare_collision_group_count']}`",
        "",
        "## By k",
        "",
    ]
    for k, data in summary["records_by_k"].items():
        lines.append(
            f"- `k = {k}`: `{data['count']}` records, prefix length range `{data['prefix_len_min']}` to `{data['prefix_len_max']}`"
        )

    lines.extend(["", "## Collision examples", ""])
    if not summary["bare_collision_examples"]:
        lines.append("- No bare collisions were found in this regime.")
    else:
        for example in summary["bare_collision_examples"]:
            lines.append(
                f"- `k = {example['k']}`, bare state `{example['bare_state']}`"
            )
            for item in example["examples"]:
                lines.append(
                    f"  query `{item['graph_id']} : {tuple(item['query'])}` -> witnesses `{tuple(item['witness_set'])}`, word `{tuple(item['word'])}`"
                )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    records, stats = enumerate_unique_minimal_queries(max_n=6)
    summary = summarize(records, stats)

    json_path = RESULTS_DIR / "unique_minimal_referee.json"
    md_path = RESULTS_DIR / "unique_minimal_referee.md"

    with json_path.open("w") as fh:
        json.dump(summary, fh, indent=2)
    with md_path.open("w") as fh:
        fh.write(render_markdown(summary))

    print(json.dumps(summary, indent=2))
    print()
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
