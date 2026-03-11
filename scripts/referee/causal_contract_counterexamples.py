#!/usr/bin/env python3
"""Toy verification for the causal contract refinement note.

This script checks two claims:
1. A confounded graph and a clean graph can have identical bare L2 summaries.
2. Their minimal adjustment sets can still differ, so no decoder from bare L2
   can universally recover adjustment-set identity.

It also prints a mixed-prefix example showing why a bare predecessor-prefix
extraction naturally over-recovers irrelevant predecessors.
"""

from __future__ import annotations

from itertools import combinations
from typing import Dict, Iterable, List, Sequence, Set, Tuple

NEG_INF = float("-inf")
Graph = Dict[str, Set[str]]


def parents(graph: Graph) -> Dict[str, Set[str]]:
    rev = {node: set() for node in graph}
    for src, dests in graph.items():
        for dst in dests:
            rev.setdefault(dst, set()).add(src)
    return rev


def descendants(graph: Graph, start: str) -> Set[str]:
    out: Set[str] = set()
    stack = [start]
    while stack:
        node = stack.pop()
        for child in graph.get(node, set()):
            if child not in out:
                out.add(child)
                stack.append(child)
    out.discard(start)
    return out


def ancestors_of_set(graph: Graph, nodes: Iterable[str]) -> Set[str]:
    rev = parents(graph)
    out: Set[str] = set(nodes)
    stack = list(nodes)
    while stack:
        node = stack.pop()
        for par in rev.get(node, set()):
            if par not in out:
                out.add(par)
                stack.append(par)
    return out


def moralized_ancestral_graph(graph: Graph, x: str, y: str, z: Set[str]) -> Dict[str, Set[str]]:
    relevant = ancestors_of_set(graph, {x, y, *z})
    rev = parents(graph)
    undirected = {node: set() for node in relevant}

    for src in relevant:
        for dst in graph.get(src, set()):
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


def is_d_separated(graph: Graph, x: str, y: str, z: Set[str]) -> bool:
    if x in z or y in z:
        return True
    moral = moralized_ancestral_graph(graph, x, y, z)
    if x not in moral or y not in moral:
        return True
    stack = [x]
    seen = {x}
    while stack:
        node = stack.pop()
        if node == y:
            return False
        for nxt in moral.get(node, set()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return True


def manipulated_graph(graph: Graph, treatment: str) -> Graph:
    out: Graph = {node: set(dests) for node, dests in graph.items()}
    out[treatment] = set()
    return out


def is_valid_adjustment_set(graph: Graph, treatment: str, outcome: str, subset: Set[str]) -> bool:
    if descendants(graph, treatment) & subset:
        return False
    g_do = manipulated_graph(graph, treatment)
    return is_d_separated(g_do, treatment, outcome, subset)


def minimal_adjustment_sets(graph: Graph, treatment: str, outcome: str) -> List[Tuple[str, ...]]:
    candidates = sorted(set(graph) - {treatment, outcome} - descendants(graph, treatment))
    valid: List[Tuple[str, ...]] = []
    for size in range(len(candidates) + 1):
        for combo in combinations(candidates, size):
            subset = set(combo)
            if not is_valid_adjustment_set(graph, treatment, outcome, subset):
                continue
            if any(set(prev).issubset(subset) for prev in valid):
                continue
            valid = [prev for prev in valid if not subset.issubset(set(prev))]
            valid.append(combo)
    return valid


def compose_l2(left: Tuple[List[float], int], right: Tuple[List[float], int], k: int) -> Tuple[List[float], int]:
    w_left, d_left = left
    w_right, d_right = right
    out = []
    for j in range(k + 1):
        out.append(max(w_left[j], w_right[max(0, j - d_left)]))
    return out, d_left + d_right


def event_context(kind: str, weight: float | None, k: int) -> Tuple[List[float], int]:
    if kind == "nonfocal":
        return [NEG_INF] * (k + 1), 1
    if kind == "focal":
        vec = [NEG_INF] * (k + 1)
        vec[0] = float(weight)
        return vec, 0
    raise ValueError(f"unknown kind: {kind}")


def summarize_sequence(sequence: Sequence[Tuple[str, str, float | None]], k: int) -> Tuple[List[float], int]:
    state = ([NEG_INF] * (k + 1), 0)
    for _, kind, weight in sequence:
        state = compose_l2(state, event_context(kind, weight, k), k)
    return state


def fmt_l2(state: Tuple[List[float], int]) -> str:
    weights, d_total = state
    rendered = ["-inf" if v == NEG_INF else str(int(v)) for v in weights]
    return f"W={rendered}, d_total={d_total}"


def q_count(k: int, p: int) -> int:
    return sum((d + 2) ** p for d in range(k + 1))


def q_sym_count(k: int, p: int) -> int:
    # Hockey-stick identity from the note:
    # sum_{d=0}^k C(d+p+1, p) = C(k+p+2, p+1) - 1
    from math import comb

    return comb(k + p + 2, p + 1) - 1


def main() -> None:
    k = 1

    confounded: Graph = {
        "C": {"T", "Y"},
        "T": {"Y"},
        "Y": set(),
    }
    clean: Graph = {
        "U": {"T"},
        "T": {"Y"},
        "Y": set(),
    }
    mixed: Graph = {
        "C": {"T", "Y"},
        "U": {"T"},
        "T": {"Y"},
        "Y": set(),
    }

    seq_conf = [
        ("C", "nonfocal", None),
        ("T", "focal", 100.0),
        ("Y", "focal", 50.0),
    ]
    seq_clean = [
        ("U", "nonfocal", None),
        ("T", "focal", 100.0),
        ("Y", "focal", 50.0),
    ]

    adj_conf = minimal_adjustment_sets(confounded, "T", "Y")
    adj_clean = minimal_adjustment_sets(clean, "T", "Y")
    adj_mixed = minimal_adjustment_sets(mixed, "T", "Y")

    l2_conf = summarize_sequence(seq_conf, k)
    l2_clean = summarize_sequence(seq_clean, k)

    print("Example 1: bare L2 collision")
    print(f"  confounded minimal adjustment sets: {adj_conf}")
    print(f"  clean minimal adjustment sets:      {adj_clean}")
    print(f"  confounded bare L2:                {fmt_l2(l2_conf)}")
    print(f"  clean bare L2:                     {fmt_l2(l2_clean)}")
    print(f"  same bare L2 summary?              {l2_conf == l2_clean}")
    print(f"  same causal answer?                {adj_conf == adj_clean}")
    print()

    assert adj_conf == [("C",)]
    assert adj_clean == [()]
    assert l2_conf == l2_clean
    assert adj_conf != adj_clean

    print("Example 2: over-recovery pressure in a mixed prefix")
    print(f"  mixed minimal adjustment sets:     {adj_mixed}")
    print("  pre-pivot non-focal prefix:        ['C', 'U']")
    print("  bare L2 can see the count 2, but not which predecessor is the confounder.")
    print()

    assert adj_mixed == [("C",)]

    print("Example 3: witness quotient counts")
    print(f"  |Q_(3,1)| = {q_count(3, 1)} (matches |M_3| = 14)")
    print(f"  |Q_(2,2)| = {q_count(2, 2)}")
    print(f"  |Q_(2,2)^sym| = {q_sym_count(2, 2)}")
    print()

    assert q_count(3, 1) == (3 + 1) * (3 + 4) // 2
    assert q_count(2, 2) == 29
    assert q_sym_count(2, 2) == 19

    print("All checks passed.")


if __name__ == "__main__":
    main()
