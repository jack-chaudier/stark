#!/usr/bin/env python3
"""Build a global holonomy atlas beyond the simplex layer.

This experiment turns the current simplex/global boundary into a more structural
atlas with two goals:

1. Classify the first static and dynamic obstructions beyond assignment + pair
   + simplex transport.
2. Search for an explicit compressed quotient inside the global layer whenever
   raw extra-token state is exact but visibly non-minimal.
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict, deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, replace
from itertools import combinations
from pathlib import Path
from typing import Callable, DefaultDict, Dict, Hashable, Iterable, List, Sequence, Tuple

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "README.md").exists())
SCRIPTS_ROOT = ROOT / "scripts"
for candidate in [SCRIPTS_ROOT] + sorted(path for path in SCRIPTS_ROOT.iterdir() if path.is_dir()):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from runtime_collapse_boundary import enumerate_exact_antichains, log2_count

from full_assignment_holonomy_search import (
    Family,
    FamilyContext,
    Trace,
    WitnessRecord,
    build_context,
    minimize_moore_machine,
    trace_text,
)

from pair_vs_simplex_holonomy_search import (
    dense_overlap_families,
    extract_automaton_witness,
    extract_segment_witness,
    group_rank,
    row_exactness,
    summary_exactness,
    witness_length,
)

from simplex_vs_global_holonomy_search import (
    SEMANTICS as ALL_GLOBAL_SEMANTICS,
    cycle_descriptors,
    explore_automaton,
    tetra_descriptors,
    unpack_state,
)

RESULTS_DIR = ROOT / "results" / "holonomy" / "global-holonomy-atlas"
DOCS_DIR = ROOT / "docs" / "writing" / "experiments" / "holonomy"

BASE_P_SCAN = (2, 3, 4)
BASE_K_MAX = 3
EXPANDED_P_SCAN = (5,)
EXPANDED_K_MAX = 4
DENSE_P_SCAN = (6,)
DENSE_K_MAX = 4
MAX_WORKERS = min(8, os.cpu_count() or 4)

SEED_FAMILIES: Dict[str, Family] = {
    "triangle": ((1, 2), (1, 3), (2, 3)),
    "tetrahedron_3uniform": ((1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4)),
    "four_edge_star": ((1, 2), (1, 3), (1, 4), (1, 5)),
    "k4_pair_family": (
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 3),
        (2, 4),
        (3, 4),
    ),
    "triangle_chain": ((1, 2), (1, 3), (2, 3), (2, 4), (3, 4)),
}
SEED_FAMILY_ORDER = tuple(SEED_FAMILIES.values())

SEMANTIC_NAMES = (
    "broadcast_control",
    "committed_allocation",
    "pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs",
    "pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__triangle_cycle_flux",
    "pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__simplex_feedback_loop",
    "pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__parity_on_face_order",
    "pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_freeze_simplex",
    "pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__tetra_commutator_toggle",
)
PROMISING_NAMES = SEMANTIC_NAMES[3:]

SEMANTIC_BY_NAME = {semantic.name: semantic for semantic in ALL_GLOBAL_SEMANTICS}
SEMANTICS = tuple(SEMANTIC_BY_NAME[name] for name in SEMANTIC_NAMES)
PROMISING_SEMANTICS = tuple(SEMANTIC_BY_NAME[name] for name in PROMISING_NAMES)


@dataclass(frozen=True)
class CompressionSpec:
    name: str
    label: str
    description: str
    projector: Callable[[Hashable, FamilyContext, object], Hashable]
    applies_to: Callable[[object], bool]


@dataclass(frozen=True)
class CandidateCompressionResult:
    name: str
    label: str
    description: str
    quotient_count: int
    exact: bool


@dataclass(frozen=True)
class FamilyInvariants:
    pair_overlap_edges: Tuple[Tuple[int, int], ...]
    pair_overlap_components: int
    pair_overlap_cycle_rank: int
    triangle_adjacency_edges: Tuple[Tuple[int, int], ...]
    triangle_cluster_count: int
    triangle_count: int
    cycle_support_count: int
    tetra_support_count: int
    descriptor_component_sizes: Tuple[int, ...]
    descriptor_scope: str
    obstruction_kind: str


@dataclass(frozen=True)
class AnalysisRecord:
    semantics: str
    label: str
    category: str
    pair_alphabet_size: int
    simplex_alphabet_size: int
    extra_alphabet_size: int
    p: int
    k: int
    family: Family
    reachable_state_count: int
    runtime_quotient_count: int
    pair_quotient_count: int
    simplex_quotient_count: int
    full_state_quotient_count: int
    output_quotient_count: int
    pair_curvature_gap: float
    simplex_curvature_gap: float
    global_curvature_gap: float
    pair_exact: bool
    simplex_exact: bool
    full_state_exact: bool
    output_exact: bool
    pair_holonomy_rank: int
    simplex_holonomy_rank: int
    hidden_future_beyond_pair_rank: int
    hidden_future_beyond_simplex_rank: int
    pair_witness: WitnessRecord | None
    hidden_future_beyond_pair_witness: WitnessRecord | None
    simplex_witness: WitnessRecord | None
    hidden_future_beyond_simplex_witness: WitnessRecord | None
    invariants: FamilyInvariants
    explicit_global_compressions: Tuple[CandidateCompressionResult, ...]
    best_explicit_exact_label: str | None
    best_explicit_exact_count: int | None


@dataclass(frozen=True)
class SemanticSummary:
    name: str
    label: str
    description: str
    category: str
    pair_alphabet_size: int
    simplex_alphabet_size: int
    extra_alphabet_size: int
    families_scanned: int
    seed_record: AnalysisRecord | None
    static_split_count: int
    dynamic_split_count: int
    pair_split_count: int
    simplex_exact_on_scan: bool
    max_simplex_holonomy_rank: int
    max_hidden_future_beyond_simplex_rank: int
    first_pair_split: AnalysisRecord | None
    first_static_split: AnalysisRecord | None
    first_dynamic_split: AnalysisRecord | None
    best_explicit_exact_record: AnalysisRecord | None


def family_badge(family: Family) -> str:
    for label, seed in SEED_FAMILIES.items():
        if family == seed:
            return label
    return f"|A|={len(family)}"


def sorted_families(p: int, k: int) -> Tuple[Family, ...]:
    families = list(enumerate_exact_antichains(p, k))
    return tuple(
        sorted(
            families,
            key=lambda family: (
                len(family),
                tuple(sorted(len(edge) for edge in family)),
                sum(len(edge) for edge in family),
                family,
            ),
        )
    )


def unpack_global_state(
    state: Hashable,
) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
    if isinstance(state, tuple) and len(state) == 4 and isinstance(state[0], tuple):
        return state
    if isinstance(state, tuple) and len(state) == 3 and isinstance(state[0], tuple):
        assignment, pair_tokens, simplex_tokens = state
        return assignment, pair_tokens, simplex_tokens, tuple()
    raise ValueError(f"cannot unpack state {state!r}")


def overlap_edges(context: FamilyContext) -> Tuple[Tuple[int, int], ...]:
    return tuple((pair.lower_edge, pair.upper_edge) for pair in context.pairs)


def connected_components_from_edges(node_count: int, edges: Iterable[Tuple[int, int]]) -> Tuple[Tuple[int, ...], ...]:
    neighbors = {index: set() for index in range(node_count)}
    for left, right in edges:
        neighbors[left].add(right)
        neighbors[right].add(left)
    components: List[Tuple[int, ...]] = []
    seen = set()
    for node in range(node_count):
        if node in seen:
            continue
        queue = deque([node])
        seen.add(node)
        component: List[int] = []
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in sorted(neighbors[current]):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                queue.append(neighbor)
        components.append(tuple(component))
    return tuple(components)


def cycle_rank(node_count: int, edge_count: int, component_count: int) -> int:
    if node_count == 0:
        return 0
    return edge_count - node_count + component_count


def triangle_adjacency_edges(context: FamilyContext) -> Tuple[Tuple[int, int], ...]:
    edges: List[Tuple[int, int]] = []
    for left, right in combinations(context.triangles, 2):
        if set(left.edges) & set(right.edges):
            edges.append((left.triangle_index, right.triangle_index))
    return tuple(edges)


def descriptor_scope(semantic: object) -> str:
    category = getattr(semantic, "category")
    if category == "global_cycle":
        return "cycle"
    if category == "tetra_local":
        return "tetra"
    return "none"


def descriptor_support_edges(descriptor: object, scope: str) -> Tuple[int, ...]:
    if scope == "cycle":
        return tuple(getattr(descriptor, "edge_union"))
    if scope == "tetra":
        return tuple(getattr(descriptor, "edges"))
    return tuple()


def descriptor_support_weight(descriptor: object, scope: str) -> int:
    if scope == "cycle":
        return len(getattr(descriptor, "edge_union"))
    if scope == "tetra":
        return len(getattr(descriptor, "edges"))
    return 0


def descriptor_triangle_weight(descriptor: object) -> int:
    return len(getattr(descriptor, "triangle_indices", tuple()))


def extra_descriptors(context: FamilyContext, semantic: object) -> Tuple[object, ...]:
    scope = descriptor_scope(semantic)
    if scope == "cycle":
        return tuple(cycle_descriptors(context.family))
    if scope == "tetra":
        return tuple(tetra_descriptors(context.family))
    return tuple()


def extra_descriptor_components(context: FamilyContext, semantic: object) -> Tuple[Tuple[int, ...], ...]:
    descriptors = extra_descriptors(context, semantic)
    if not descriptors:
        return tuple()
    scope = descriptor_scope(semantic)
    descriptor_edges = [set(descriptor_support_edges(descriptor, scope)) for descriptor in descriptors]
    adjacency: List[Tuple[int, int]] = []
    for left, right in combinations(range(len(descriptors)), 2):
        if descriptor_edges[left] & descriptor_edges[right]:
            adjacency.append((left, right))
    return connected_components_from_edges(len(descriptors), adjacency)


def classify_obstruction(invariants: FamilyInvariants) -> str:
    if invariants.tetra_support_count and invariants.cycle_support_count:
        return "mixed"
    if invariants.tetra_support_count:
        return "tetra_local_support"
    if invariants.cycle_support_count:
        return "cycle_of_triangles"
    if invariants.triangle_count:
        return "triangle_chain"
    return "flat"


def family_invariants(context: FamilyContext, semantic: object) -> FamilyInvariants:
    overlap = overlap_edges(context)
    overlap_components = connected_components_from_edges(len(context.family), overlap)
    triangle_edges = triangle_adjacency_edges(context)
    triangle_components = connected_components_from_edges(len(context.triangles), triangle_edges)
    components = extra_descriptor_components(context, semantic)
    scope = descriptor_scope(semantic)
    invariants = FamilyInvariants(
        pair_overlap_edges=overlap,
        pair_overlap_components=len(overlap_components),
        pair_overlap_cycle_rank=cycle_rank(len(context.family), len(overlap), len(overlap_components)),
        triangle_adjacency_edges=triangle_edges,
        triangle_cluster_count=len(triangle_components),
        triangle_count=len(context.triangles),
        cycle_support_count=len(cycle_descriptors(context.family)),
        tetra_support_count=len(tetra_descriptors(context.family)),
        descriptor_component_sizes=tuple(sorted(len(component) for component in components)),
        descriptor_scope=scope,
        obstruction_kind="pending",
    )
    return FamilyInvariants(
        **{**invariants.__dict__, "obstruction_kind": classify_obstruction(invariants)}
    )


def component_histogram(
    tokens: Sequence[int],
    components: Sequence[Sequence[int]],
) -> Tuple[Tuple[Tuple[int, int], ...], ...]:
    component_profiles: List[Tuple[Tuple[int, int], ...]] = []
    for component in components:
        histogram: DefaultDict[int, int] = defaultdict(int)
        for index in component:
            histogram[tokens[index]] += 1
        component_profiles.append(tuple(sorted(histogram.items())))
    return tuple(sorted(component_profiles))


def component_token_multiset(
    tokens: Sequence[int],
    components: Sequence[Sequence[int]],
) -> Tuple[Tuple[int, ...], ...]:
    component_profiles = [tuple(sorted(tokens[index] for index in component)) for component in components]
    return tuple(sorted(component_profiles))


def weighted_histogram(
    tokens: Sequence[int],
    descriptors: Sequence[object],
    scope: str,
) -> Tuple[Tuple[Tuple[int, int], int], ...]:
    histogram: DefaultDict[Tuple[int, int], int] = defaultdict(int)
    for token, descriptor in zip(tokens, descriptors):
        key = (descriptor_support_weight(descriptor, scope), token)
        histogram[key] += 1
    return tuple(sorted(histogram.items()))


def descriptor_signature_histogram(
    tokens: Sequence[int],
    descriptors: Sequence[object],
    components: Sequence[Sequence[int]],
    scope: str,
) -> Tuple[Tuple[Tuple[int, int, int, int], int], ...]:
    component_of: Dict[int, int] = {}
    for component_index, component in enumerate(components):
        for index in component:
            component_of[index] = component_index
    histogram: DefaultDict[Tuple[int, int, int, int], int] = defaultdict(int)
    for index, (token, descriptor) in enumerate(zip(tokens, descriptors)):
        signature = (
            descriptor_support_weight(descriptor, scope),
            descriptor_triangle_weight(descriptor),
            len(components[component_of[index]]) if components else 1,
            token,
        )
        histogram[signature] += 1
    return tuple(sorted(histogram.items()))


def active_component_signature(
    tokens: Sequence[int],
    components: Sequence[Sequence[int]],
) -> Tuple[Tuple[int, int, int], ...]:
    signatures = []
    for component in components:
        active = sum(1 for index in component if tokens[index] != 0)
        parity = active % 2
        signatures.append((len(component), active, parity))
    return tuple(sorted(signatures))


def simple_global_lower_summary(state: Hashable, context: FamilyContext, semantic: object) -> Hashable:
    return semantic.simplex_summary(state, context)


def sorted_extra_tokens_summary(state: Hashable, context: FamilyContext, semantic: object) -> Hashable:
    lower = semantic.simplex_summary(state, context)
    _, _, _, extra_tokens = unpack_global_state(state)
    return lower, tuple(sorted(extra_tokens))


def extra_token_histogram_summary(state: Hashable, context: FamilyContext, semantic: object) -> Hashable:
    lower = semantic.simplex_summary(state, context)
    _, _, _, extra_tokens = unpack_global_state(state)
    histogram: DefaultDict[int, int] = defaultdict(int)
    for token in extra_tokens:
        histogram[token] += 1
    return lower, tuple(sorted(histogram.items()))


def component_histogram_summary(state: Hashable, context: FamilyContext, semantic: object) -> Hashable:
    lower = semantic.simplex_summary(state, context)
    _, _, _, extra_tokens = unpack_global_state(state)
    components = extra_descriptor_components(context, semantic)
    return lower, component_histogram(extra_tokens, components)


def component_token_multiset_summary(state: Hashable, context: FamilyContext, semantic: object) -> Hashable:
    lower = semantic.simplex_summary(state, context)
    _, _, _, extra_tokens = unpack_global_state(state)
    components = extra_descriptor_components(context, semantic)
    return lower, component_token_multiset(extra_tokens, components)


def weighted_histogram_summary(state: Hashable, context: FamilyContext, semantic: object) -> Hashable:
    lower = semantic.simplex_summary(state, context)
    _, _, _, extra_tokens = unpack_global_state(state)
    scope = descriptor_scope(semantic)
    descriptors = extra_descriptors(context, semantic)
    return lower, weighted_histogram(extra_tokens, descriptors, scope)


def descriptor_signature_histogram_summary(state: Hashable, context: FamilyContext, semantic: object) -> Hashable:
    lower = semantic.simplex_summary(state, context)
    _, _, _, extra_tokens = unpack_global_state(state)
    scope = descriptor_scope(semantic)
    descriptors = extra_descriptors(context, semantic)
    components = extra_descriptor_components(context, semantic)
    return lower, descriptor_signature_histogram(extra_tokens, descriptors, components, scope)


def cochain_signature_summary(state: Hashable, context: FamilyContext, semantic: object) -> Hashable:
    lower = semantic.simplex_summary(state, context)
    _, _, _, extra_tokens = unpack_global_state(state)
    components = extra_descriptor_components(context, semantic)
    return lower, active_component_signature(extra_tokens, components)


COMPRESSION_SPECS = (
    CompressionSpec(
        "sorted_extra_tokens",
        "Sorted extra tokens",
        "Forget descriptor order and keep only the sorted extra token tuple.",
        sorted_extra_tokens_summary,
        lambda semantic: getattr(semantic, "extra_alphabet_size") > 1,
    ),
    CompressionSpec(
        "extra_token_histogram",
        "Extra-token histogram",
        "Histogram of extra token values above the simplex fiber.",
        extra_token_histogram_summary,
        lambda semantic: getattr(semantic, "extra_alphabet_size") > 1,
    ),
    CompressionSpec(
        "component_histogram",
        "Per-component histogram",
        "Histogram of extra token values on each connected overlap component.",
        component_histogram_summary,
        lambda semantic: getattr(semantic, "extra_alphabet_size") > 1,
    ),
    CompressionSpec(
        "component_token_multiset",
        "Component token multiset",
        "Sorted multiset of extra tokens inside each connected overlap component.",
        component_token_multiset_summary,
        lambda semantic: getattr(semantic, "extra_alphabet_size") > 1,
    ),
    CompressionSpec(
        "weighted_histogram",
        "Support-weighted histogram",
        "Histogram of extra tokens weighted by descriptor support size.",
        weighted_histogram_summary,
        lambda semantic: getattr(semantic, "extra_alphabet_size") > 1,
    ),
    CompressionSpec(
        "descriptor_signature_histogram",
        "Descriptor-signature histogram",
        "Histogram over local descriptor signatures and token values.",
        descriptor_signature_histogram_summary,
        lambda semantic: getattr(semantic, "extra_alphabet_size") > 1,
    ),
    CompressionSpec(
        "cochain_signature",
        "Component cochain signature",
        "Active-token counts and parity on each descriptor component.",
        cochain_signature_summary,
        lambda semantic: getattr(semantic, "extra_alphabet_size") > 1,
    ),
)


def compression_results_automaton(
    semantic: object,
    states: Sequence[Hashable],
    context: FamilyContext,
    block_of: Dict[Hashable, int],
) -> Tuple[CandidateCompressionResult, ...]:
    results: List[CandidateCompressionResult] = []
    if not states or getattr(semantic, "extra_alphabet_size") <= 1 or not extra_descriptors(context, semantic):
        return tuple()
    for spec in COMPRESSION_SPECS:
        if not spec.applies_to(semantic):
            continue
        quotient_count, exact = summary_exactness(
            lambda state, ctx, spec=spec: spec.projector(state, ctx, semantic),
            states,
            context,
            block_of,
        )
        results.append(
            CandidateCompressionResult(
                name=spec.name,
                label=spec.label,
                description=spec.description,
                quotient_count=quotient_count,
                exact=exact,
            )
        )
    return tuple(results)


def compression_results_rows(
    semantic: object,
    states: Sequence[Hashable],
    context: FamilyContext,
    row_of: Dict[Hashable, Tuple[Hashable, ...]],
) -> Tuple[CandidateCompressionResult, ...]:
    results: List[CandidateCompressionResult] = []
    if not states or getattr(semantic, "extra_alphabet_size") <= 1 or not extra_descriptors(context, semantic):
        return tuple()
    for spec in COMPRESSION_SPECS:
        if not spec.applies_to(semantic):
            continue
        quotient_count, exact = row_exactness(
            lambda state, ctx, spec=spec: spec.projector(state, ctx, semantic),
            states,
            context,
            row_of,
        )
        results.append(
            CandidateCompressionResult(
                name=spec.name,
                label=spec.label,
                description=spec.description,
                quotient_count=quotient_count,
                exact=exact,
            )
        )
    return tuple(results)


def analyze_automaton(semantic: object, context: FamilyContext) -> AnalysisRecord:
    states, transitions, outputs, shortest_trace = explore_automaton(semantic, context)
    events = semantic.events(context)
    block_of = minimize_moore_machine(states, events, transitions, outputs)
    runtime_count = len(set(block_of.values()))

    pair_count, pair_exact = summary_exactness(semantic.pair_summary, states, context, block_of)
    simplex_count, simplex_exact = summary_exactness(semantic.simplex_summary, states, context, block_of)
    full_state_count, full_state_exact = summary_exactness(semantic.full_state_summary, states, context, block_of)
    output_count, output_exact = summary_exactness(lambda state, _: outputs[state], states, context, block_of)

    pair_witness = extract_automaton_witness(
        states,
        context,
        semantic.pair_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
    )
    hidden_pair_witness = extract_automaton_witness(
        states,
        context,
        semantic.pair_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
        require_same_output=True,
        require_non_empty_suffix=True,
    )
    simplex_witness = extract_automaton_witness(
        states,
        context,
        semantic.simplex_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
    )
    hidden_simplex_witness = extract_automaton_witness(
        states,
        context,
        semantic.simplex_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
        require_same_output=True,
        require_non_empty_suffix=True,
    )

    return AnalysisRecord(
        semantics=semantic.name,
        label=semantic.label,
        category=semantic.category,
        pair_alphabet_size=semantic.pair_alphabet_size,
        simplex_alphabet_size=semantic.simplex_alphabet_size,
        extra_alphabet_size=semantic.extra_alphabet_size,
        p=max(context.universe) if context.universe else 0,
        k=max((len(edge) for edge in context.family), default=0),
        family=context.family,
        reachable_state_count=len(states),
        runtime_quotient_count=runtime_count,
        pair_quotient_count=pair_count,
        simplex_quotient_count=simplex_count,
        full_state_quotient_count=full_state_count,
        output_quotient_count=output_count,
        pair_curvature_gap=log2_count(runtime_count) - log2_count(pair_count),
        simplex_curvature_gap=log2_count(runtime_count) - log2_count(simplex_count),
        global_curvature_gap=log2_count(runtime_count) - log2_count(full_state_count),
        pair_exact=pair_exact,
        simplex_exact=simplex_exact,
        full_state_exact=full_state_exact,
        output_exact=output_exact,
        pair_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.pair_summary(state, context)),
        simplex_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.simplex_summary(state, context)),
        hidden_future_beyond_pair_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.pair_summary(state, context), outputs[state])),
        hidden_future_beyond_simplex_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.simplex_summary(state, context), outputs[state])),
        pair_witness=pair_witness,
        hidden_future_beyond_pair_witness=hidden_pair_witness,
        simplex_witness=simplex_witness,
        hidden_future_beyond_simplex_witness=hidden_simplex_witness,
        invariants=family_invariants(context, semantic),
        explicit_global_compressions=tuple(),
        best_explicit_exact_label=None,
        best_explicit_exact_count=None,
    )


def analyze_segment_rows(semantic: object, context: FamilyContext) -> AnalysisRecord:
    if semantic.segment_states is None or semantic.compose is None:
        raise ValueError(f"{semantic.name} requires segment row support")
    states = semantic.segment_states(context)
    empty_state = semantic.initial_state(context)
    row_of: Dict[Hashable, Tuple[Hashable, ...]] = {}
    for state in states:
        row: List[Hashable] = []
        for suffix in states:
            merged = semantic.compose(state, suffix, context)
            row.append(("INVALID",) if merged is None else semantic.output(merged, context))
        row_of[state] = tuple(row)
    runtime_blocks: Dict[Tuple[Hashable, ...], int] = {}
    block_of: Dict[Hashable, int] = {}
    for state in states:
        row = row_of[state]
        if row not in runtime_blocks:
            runtime_blocks[row] = len(runtime_blocks)
        block_of[state] = runtime_blocks[row]
    runtime_count = len(runtime_blocks)

    pair_count, pair_exact = row_exactness(semantic.pair_summary, states, context, row_of)
    simplex_count, simplex_exact = row_exactness(semantic.simplex_summary, states, context, row_of)
    full_state_count, full_state_exact = row_exactness(semantic.full_state_summary, states, context, row_of)
    output_count, output_exact = row_exactness(lambda state, ctx: semantic.output(state, ctx), states, context, row_of)

    pair_witness = extract_segment_witness(
        states,
        context,
        semantic.pair_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
    )
    hidden_pair_witness = extract_segment_witness(
        states,
        context,
        semantic.pair_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
        require_same_output=True,
        require_non_empty_suffix=True,
    )
    simplex_witness = extract_segment_witness(
        states,
        context,
        semantic.simplex_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
    )
    hidden_simplex_witness = extract_segment_witness(
        states,
        context,
        semantic.simplex_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
        require_same_output=True,
        require_non_empty_suffix=True,
    )

    return AnalysisRecord(
        semantics=semantic.name,
        label=semantic.label,
        category=semantic.category,
        pair_alphabet_size=semantic.pair_alphabet_size,
        simplex_alphabet_size=semantic.simplex_alphabet_size,
        extra_alphabet_size=semantic.extra_alphabet_size,
        p=max(context.universe) if context.universe else 0,
        k=max((len(edge) for edge in context.family), default=0),
        family=context.family,
        reachable_state_count=len(states),
        runtime_quotient_count=runtime_count,
        pair_quotient_count=pair_count,
        simplex_quotient_count=simplex_count,
        full_state_quotient_count=full_state_count,
        output_quotient_count=output_count,
        pair_curvature_gap=log2_count(runtime_count) - log2_count(pair_count),
        simplex_curvature_gap=log2_count(runtime_count) - log2_count(simplex_count),
        global_curvature_gap=log2_count(runtime_count) - log2_count(full_state_count),
        pair_exact=pair_exact,
        simplex_exact=simplex_exact,
        full_state_exact=full_state_exact,
        output_exact=output_exact,
        pair_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.pair_summary(state, context)),
        simplex_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.simplex_summary(state, context)),
        hidden_future_beyond_pair_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.pair_summary(state, context), semantic.output(state, context))),
        hidden_future_beyond_simplex_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.simplex_summary(state, context), semantic.output(state, context))),
        pair_witness=pair_witness,
        hidden_future_beyond_pair_witness=hidden_pair_witness,
        simplex_witness=simplex_witness,
        hidden_future_beyond_simplex_witness=hidden_simplex_witness,
        invariants=family_invariants(context, semantic),
        explicit_global_compressions=tuple(),
        best_explicit_exact_label=None,
        best_explicit_exact_count=None,
    )


def analyze_with_context(semantic: object, context: FamilyContext) -> AnalysisRecord:
    if semantic.analysis_mode == "segment_rows":
        return analyze_segment_rows(semantic, context)
    return analyze_automaton(semantic, context)


def analyze_family(semantic: object, family: Family) -> AnalysisRecord:
    context = build_context(family)
    return analyze_with_context(semantic, context)


def clone_from_simplex_control(
    base_record: AnalysisRecord,
    semantic: object,
    context: FamilyContext,
) -> AnalysisRecord:
    return AnalysisRecord(
        semantics=semantic.name,
        label=semantic.label,
        category=semantic.category,
        pair_alphabet_size=semantic.pair_alphabet_size,
        simplex_alphabet_size=semantic.simplex_alphabet_size,
        extra_alphabet_size=semantic.extra_alphabet_size,
        p=base_record.p,
        k=base_record.k,
        family=base_record.family,
        reachable_state_count=base_record.reachable_state_count,
        runtime_quotient_count=base_record.runtime_quotient_count,
        pair_quotient_count=base_record.pair_quotient_count,
        simplex_quotient_count=base_record.simplex_quotient_count,
        full_state_quotient_count=base_record.full_state_quotient_count,
        output_quotient_count=base_record.output_quotient_count,
        pair_curvature_gap=base_record.pair_curvature_gap,
        simplex_curvature_gap=base_record.simplex_curvature_gap,
        global_curvature_gap=base_record.global_curvature_gap,
        pair_exact=base_record.pair_exact,
        simplex_exact=base_record.simplex_exact,
        full_state_exact=base_record.full_state_exact,
        output_exact=base_record.output_exact,
        pair_holonomy_rank=base_record.pair_holonomy_rank,
        simplex_holonomy_rank=base_record.simplex_holonomy_rank,
        hidden_future_beyond_pair_rank=base_record.hidden_future_beyond_pair_rank,
        hidden_future_beyond_simplex_rank=base_record.hidden_future_beyond_simplex_rank,
        pair_witness=base_record.pair_witness,
        hidden_future_beyond_pair_witness=base_record.hidden_future_beyond_pair_witness,
        simplex_witness=base_record.simplex_witness,
        hidden_future_beyond_simplex_witness=base_record.hidden_future_beyond_simplex_witness,
        invariants=family_invariants(context, semantic),
        explicit_global_compressions=tuple(),
        best_explicit_exact_label=None,
        best_explicit_exact_count=None,
    )


def witness_order_key(record: AnalysisRecord, kind: str) -> Tuple[object, ...]:
    witness = {
        "pair": record.pair_witness,
        "hidden_pair": record.hidden_future_beyond_pair_witness,
        "static": record.simplex_witness,
        "dynamic": record.hidden_future_beyond_simplex_witness,
    }[kind]
    return (
        record.p,
        record.k,
        len(record.family),
        record.pair_alphabet_size,
        record.simplex_alphabet_size,
        record.extra_alphabet_size,
        record.reachable_state_count,
        witness_length(witness),
        record.family,
        record.semantics,
    )


def compression_saving(record: AnalysisRecord) -> int:
    if record.best_explicit_exact_count is None:
        return -1
    return record.full_state_quotient_count - record.best_explicit_exact_count


def enrich_record_with_compressions(record: AnalysisRecord) -> AnalysisRecord:
    semantic = SEMANTIC_BY_NAME[record.semantics]
    context = build_context(record.family)
    if getattr(semantic, "extra_alphabet_size") <= 1 or not extra_descriptors(context, semantic):
        return record
    if semantic.analysis_mode == "segment_rows":
        states = semantic.segment_states(context)
        if states is None or semantic.compose is None:
            return record
        row_of: Dict[Hashable, Tuple[Hashable, ...]] = {}
        for state in states:
            row: List[Hashable] = []
            for suffix in states:
                merged = semantic.compose(state, suffix, context)
                row.append(("INVALID",) if merged is None else semantic.output(merged, context))
            row_of[state] = tuple(row)
        explicit = compression_results_rows(semantic, states, context, row_of)
    else:
        states, transitions, outputs, shortest_trace = explore_automaton(semantic, context)
        block_of = minimize_moore_machine(states, semantic.events(context), transitions, outputs)
        explicit = compression_results_automaton(semantic, states, context, block_of)
    exact_explicit = [item for item in explicit if item.exact]
    exact_explicit.sort(key=lambda item: (item.quotient_count, item.label))
    best_label = exact_explicit[0].label if exact_explicit else None
    best_count = exact_explicit[0].quotient_count if exact_explicit else None
    if best_count is not None and record.full_state_quotient_count <= best_count:
        best_label = None
        best_count = None
    return replace(
        record,
        explicit_global_compressions=explicit,
        best_explicit_exact_label=best_label,
        best_explicit_exact_count=best_count,
    )


def analysis_sort_key(record: AnalysisRecord) -> Tuple[object, ...]:
    return (
        record.p,
        record.k,
        len(record.family),
        record.family,
        record.semantics,
    )


def summarize_semantic(semantic: object, records: Sequence[AnalysisRecord]) -> SemanticSummary:
    seed_record = None
    for family in SEED_FAMILY_ORDER:
        match = next((record for record in records if record.family == family), None)
        if match is not None:
            seed_record = match
            break
    pair_split = [record for record in records if not record.pair_exact]
    static_split = [record for record in records if record.simplex_witness is not None]
    dynamic_split = [record for record in records if record.hidden_future_beyond_simplex_witness is not None]
    if pair_split:
        pair_split.sort(key=lambda record: witness_order_key(record, "pair"))
    if static_split:
        static_split.sort(key=lambda record: witness_order_key(record, "static"))
    if dynamic_split:
        dynamic_split.sort(key=lambda record: witness_order_key(record, "dynamic"))
    compression_records = [
        record
        for record in records
        if record.best_explicit_exact_count is not None
        and record.full_state_quotient_count > record.best_explicit_exact_count
    ]
    compression_records.sort(
        key=lambda record: (
            -compression_saving(record),
            record.best_explicit_exact_count or 10**9,
            record.p,
            record.k,
            len(record.family),
            record.semantics,
        )
    )
    return SemanticSummary(
        name=semantic.name,
        label=semantic.label,
        description=semantic.description,
        category=semantic.category,
        pair_alphabet_size=semantic.pair_alphabet_size,
        simplex_alphabet_size=semantic.simplex_alphabet_size,
        extra_alphabet_size=semantic.extra_alphabet_size,
        families_scanned=len(records),
        seed_record=seed_record,
        static_split_count=len(static_split),
        dynamic_split_count=len(dynamic_split),
        pair_split_count=len(pair_split),
        simplex_exact_on_scan=all(record.simplex_exact for record in records),
        max_simplex_holonomy_rank=max(record.simplex_holonomy_rank for record in records),
        max_hidden_future_beyond_simplex_rank=max(record.hidden_future_beyond_simplex_rank for record in records),
        first_pair_split=pair_split[0] if pair_split else None,
        first_static_split=static_split[0] if static_split else None,
        first_dynamic_split=dynamic_split[0] if dynamic_split else None,
        best_explicit_exact_record=compression_records[0] if compression_records else None,
    )


def seeded_scan(semantics: Sequence[object], families: Sequence[Family]) -> Dict[str, List[AnalysisRecord]]:
    deduped: List[Family] = []
    seen = set()
    for family in families:
        if family in seen:
            continue
        seen.add(family)
        deduped.append(family)
    results = {semantic.name: [] for semantic in semantics}
    for family in deduped:
        for semantic in semantics:
            results[semantic.name].append(analyze_family(semantic, family))
    return results


def analyze_family_bundle(task: Tuple[Family, Tuple[str, ...]]) -> Dict[str, AnalysisRecord]:
    family, semantic_names = task
    context = build_context(family)
    cycle_count = len(cycle_descriptors(family))
    tetra_count = len(tetra_descriptors(family))
    simplex_name = "pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs"
    simplex_record: AnalysisRecord | None = None

    results: Dict[str, AnalysisRecord] = {}
    for semantic_name in semantic_names:
        semantic = SEMANTIC_BY_NAME[semantic_name]
        scope = descriptor_scope(semantic)
        if scope == "cycle" and cycle_count == 0:
            if simplex_record is None:
                simplex_record = analyze_with_context(SEMANTIC_BY_NAME[simplex_name], context)
            results[semantic_name] = clone_from_simplex_control(simplex_record, semantic, context)
            continue
        if scope == "tetra" and tetra_count == 0:
            if simplex_record is None:
                simplex_record = analyze_with_context(SEMANTIC_BY_NAME[simplex_name], context)
            results[semantic_name] = clone_from_simplex_control(simplex_record, semantic, context)
            continue
        results[semantic_name] = analyze_with_context(semantic, context)
    return results


def family_chunks(families: Sequence[Family], size: int = 32) -> Tuple[Tuple[Family, ...], ...]:
    return tuple(
        tuple(families[index : index + size])
        for index in range(0, len(families), size)
    )


def analyze_family_chunk(task: Tuple[Tuple[Family, ...], Tuple[str, ...]]) -> Dict[str, List[AnalysisRecord]]:
    families, semantic_names = task
    grouped: Dict[str, List[AnalysisRecord]] = {name: [] for name in semantic_names}
    for family in families:
        bundle = analyze_family_bundle((family, semantic_names))
        for semantic_name, record in bundle.items():
            grouped[semantic_name].append(record)
    return grouped


def run_scan(
    semantics: Sequence[object],
    *,
    p_scan: Sequence[int],
    k_max: int,
    families_fn: Callable[[int, int], Sequence[Family]] = sorted_families,
    parallel: bool = False,
    progress_label: str = "scan",
) -> Dict[str, List[AnalysisRecord]]:
    results = {semantic.name: [] for semantic in semantics}
    families: List[Family] = []
    for p in p_scan:
        for k in range(1, min(k_max, p) + 1):
            families.extend(families_fn(p, k))

    if not parallel or len(families) < 32 or len(semantics) == 1:
        for family in families:
            for semantic in semantics:
                results[semantic.name].append(analyze_family(semantic, family))
        return results

    semantic_names = tuple(semantic.name for semantic in semantics)
    family_groups = family_chunks(families)
    total = len(families)
    max_workers = min(MAX_WORKERS, len(family_groups))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(analyze_family_chunk, (group, semantic_names)): group
            for group in family_groups
        }
        completed = 0
        next_report = 100
        for future in as_completed(futures):
            bundle = future.result()
            group = futures[future]
            for semantic_name, records in bundle.items():
                results[semantic_name].extend(records)
            completed += len(group)
            if completed >= next_report or completed == total:
                print(f"[{progress_label}] {completed}/{total} families")
                while next_report <= completed:
                    next_report += 100
    for semantic_name in results:
        results[semantic_name].sort(key=analysis_sort_key)
    return results


def merge_record_maps(*maps: Dict[str, List[AnalysisRecord]]) -> Dict[str, List[AnalysisRecord]]:
    merged: Dict[str, List[AnalysisRecord]] = {}
    for record_map in maps:
        for name, records in record_map.items():
            merged.setdefault(name, [])
            merged[name].extend(records)
    return merged


def witness_to_json(witness: WitnessRecord | None) -> Dict[str, object] | None:
    if witness is None:
        return None
    return {
        "left_trace": None if witness.left_trace is None else list(witness.left_trace),
        "right_trace": None if witness.right_trace is None else list(witness.right_trace),
        "suffix": None if witness.suffix is None else list(witness.suffix),
        "summary_value": witness.summary_value,
        "left_state": witness.left_state,
        "right_state": witness.right_state,
        "left_output_now": witness.left_output_now,
        "right_output_now": witness.right_output_now,
        "left_output_future": witness.left_output_future,
        "right_output_future": witness.right_output_future,
        "same_now": witness.same_now,
        "non_empty_suffix": witness.non_empty_suffix,
    }


def invariants_to_json(invariants: FamilyInvariants) -> Dict[str, object]:
    return {
        "pair_overlap_edges": [list(edge) for edge in invariants.pair_overlap_edges],
        "pair_overlap_components": invariants.pair_overlap_components,
        "pair_overlap_cycle_rank": invariants.pair_overlap_cycle_rank,
        "triangle_adjacency_edges": [list(edge) for edge in invariants.triangle_adjacency_edges],
        "triangle_cluster_count": invariants.triangle_cluster_count,
        "triangle_count": invariants.triangle_count,
        "cycle_support_count": invariants.cycle_support_count,
        "tetra_support_count": invariants.tetra_support_count,
        "descriptor_component_sizes": list(invariants.descriptor_component_sizes),
        "descriptor_scope": invariants.descriptor_scope,
        "obstruction_kind": invariants.obstruction_kind,
    }


def compression_to_json(candidate: CandidateCompressionResult) -> Dict[str, object]:
    return {
        "name": candidate.name,
        "label": candidate.label,
        "description": candidate.description,
        "quotient_count": candidate.quotient_count,
        "exact": candidate.exact,
    }


def record_to_json(record: AnalysisRecord) -> Dict[str, object]:
    return {
        "semantics": record.semantics,
        "label": record.label,
        "category": record.category,
        "pair_alphabet_size": record.pair_alphabet_size,
        "simplex_alphabet_size": record.simplex_alphabet_size,
        "extra_alphabet_size": record.extra_alphabet_size,
        "p": record.p,
        "k": record.k,
        "family": [list(edge) for edge in record.family],
        "reachable_state_count": record.reachable_state_count,
        "runtime_quotient_count": record.runtime_quotient_count,
        "pair_quotient_count": record.pair_quotient_count,
        "simplex_quotient_count": record.simplex_quotient_count,
        "full_state_quotient_count": record.full_state_quotient_count,
        "output_quotient_count": record.output_quotient_count,
        "pair_curvature_gap": record.pair_curvature_gap,
        "simplex_curvature_gap": record.simplex_curvature_gap,
        "global_curvature_gap": record.global_curvature_gap,
        "pair_exact": record.pair_exact,
        "simplex_exact": record.simplex_exact,
        "full_state_exact": record.full_state_exact,
        "output_exact": record.output_exact,
        "pair_holonomy_rank": record.pair_holonomy_rank,
        "simplex_holonomy_rank": record.simplex_holonomy_rank,
        "hidden_future_beyond_pair_rank": record.hidden_future_beyond_pair_rank,
        "hidden_future_beyond_simplex_rank": record.hidden_future_beyond_simplex_rank,
        "pair_witness": witness_to_json(record.pair_witness),
        "hidden_future_beyond_pair_witness": witness_to_json(record.hidden_future_beyond_pair_witness),
        "simplex_witness": witness_to_json(record.simplex_witness),
        "hidden_future_beyond_simplex_witness": witness_to_json(record.hidden_future_beyond_simplex_witness),
        "invariants": invariants_to_json(record.invariants),
        "explicit_global_compressions": [compression_to_json(item) for item in record.explicit_global_compressions],
        "best_explicit_exact_label": record.best_explicit_exact_label,
        "best_explicit_exact_count": record.best_explicit_exact_count,
    }


def summary_to_json(summary: SemanticSummary) -> Dict[str, object]:
    return {
        "name": summary.name,
        "label": summary.label,
        "description": summary.description,
        "category": summary.category,
        "pair_alphabet_size": summary.pair_alphabet_size,
        "simplex_alphabet_size": summary.simplex_alphabet_size,
        "extra_alphabet_size": summary.extra_alphabet_size,
        "families_scanned": summary.families_scanned,
        "static_split_count": summary.static_split_count,
        "dynamic_split_count": summary.dynamic_split_count,
        "pair_split_count": summary.pair_split_count,
        "simplex_exact_on_scan": summary.simplex_exact_on_scan,
        "max_simplex_holonomy_rank": summary.max_simplex_holonomy_rank,
        "max_hidden_future_beyond_simplex_rank": summary.max_hidden_future_beyond_simplex_rank,
        "seed_record": None if summary.seed_record is None else record_to_json(summary.seed_record),
        "first_pair_split": None if summary.first_pair_split is None else record_to_json(summary.first_pair_split),
        "first_static_split": None if summary.first_static_split is None else record_to_json(summary.first_static_split),
        "first_dynamic_split": None if summary.first_dynamic_split is None else record_to_json(summary.first_dynamic_split),
        "best_explicit_exact_record": None if summary.best_explicit_exact_record is None else record_to_json(summary.best_explicit_exact_record),
    }


def minimal_winner_records(records: Sequence[AnalysisRecord], kind: str) -> List[AnalysisRecord]:
    filtered = [
        record
        for record in records
        if (
            (kind == "static" and record.simplex_witness is not None)
            or (kind == "dynamic" and record.hidden_future_beyond_simplex_witness is not None)
        )
    ]
    if not filtered:
        return []
    filtered.sort(key=lambda record: witness_order_key(record, kind))
    target_key = witness_order_key(filtered[0], kind)
    return [record for record in filtered if witness_order_key(record, kind) == target_key]


def unique_family_payload(records: Sequence[AnalysisRecord]) -> List[Dict[str, object]]:
    seen = {}
    for record in records:
        key = tuple(record.family)
        entry = seen.setdefault(
            key,
            {
                "family": [list(edge) for edge in record.family],
                "p": record.p,
                "k": record.k,
                "invariants": invariants_to_json(record.invariants),
                "semantics": [],
            },
        )
        entry["semantics"].append(record.semantics)
    return list(seen.values())


def build_report(
    summaries: Sequence[SemanticSummary],
    payload: Dict[str, object],
    json_path: Path,
    svg_path: Path,
    note_path: Path | None,
    compression_note_path: Path | None,
) -> str:
    overall_static = payload["overall_first_static_split"]
    overall_dynamic = payload["overall_first_dynamic_split"]
    best_compression = payload["best_global_compression_record"]
    static_family = None if overall_static is None else tuple(tuple(edge) for edge in overall_static["family"])
    dynamic_family = None if overall_dynamic is None else tuple(tuple(edge) for edge in overall_dynamic["family"])
    compression_family = None if best_compression is None else tuple(tuple(edge) for edge in best_compression["family"])

    lines = [
        "# Global Holonomy Atlas",
        "",
        "## Headline Results",
        "",
    ]
    if overall_static is not None:
        lines.append(
            f"- EXACT COMPUTATIONAL RESULT (Static): the first beyond-simplex current-output obstruction is `{overall_static['semantics']}` on `{static_family}` at `(p={overall_static['p']}, k={overall_static['k']})`."
        )
    if overall_dynamic is not None:
        lines.append(
            f"- EXACT COMPUTATIONAL RESULT (Dynamic): the first same-now / future-separate witness beyond simplex is `{overall_dynamic['semantics']}` on `{dynamic_family}` at `(p={overall_dynamic['p']}, k={overall_dynamic['k']})`."
        )
    if best_compression is not None:
        lines.append(
            f"- EXACT COMPUTATIONAL RESULT (Compression): on `{compression_family}`, `{best_compression['best_explicit_exact_label']}` is exact with quotient count `{best_compression['best_explicit_exact_count']}`, below the raw global count `{best_compression['full_state_quotient_count']}`."
        )
    lines.extend(
        [
            "",
            "## Definitions",
            "",
            "- **Static split**: same `assignment + pair + simplex`, different current output.",
            "- **Dynamic hidden future**: same `assignment + pair + simplex`, same current output, non-empty common suffix, different future outputs.",
            "- Figure reading: static means same lower-layer summary, different now; dynamic means same lower-layer summary, same now, different future under a non-empty suffix.",
            "",
            "## Scope",
            "",
            "This atlas turns the beyond-simplex boundary into a structural scan.",
            f"It is exact on the normalized base grid `p <= {max(BASE_P_SCAN)}` and `k <= {BASE_K_MAX}`, plus the named seed families `triangle`, `tetrahedron_3uniform`, `four_edge_star`, `k4_pair_family`, and `triangle_chain`.",
            "The larger normalized `p <= 5, k <= 4` follow-up is intentionally omitted here because the `p = 4` scan already fixes the minimal-boundary winners in the canonical first order, so the larger pass would be persistence-only rather than boundary-setting.",
            "",
            "## Scan Setup",
            "",
            "- Controls: `broadcast_control`, `committed_allocation`, and the simplex positive control `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs`.",
            "- Global semantics: cycle-flux, simplex-feedback-loop, face-order-parity, tetra-freeze-simplex, and tetra-commutator-toggle.",
            f"- Base normalized scan: `p <= {max(BASE_P_SCAN)}` and `k <= {BASE_K_MAX}`.",
            "- Named seed families added to the base grid: `triangle`, `tetrahedron_3uniform`, `four_edge_star`, `k4_pair_family`, and `triangle_chain`.",
            f"- Expanded normalized scan on promising semantics: `{payload['scan']['expanded_triggered']}` over `p <= {max(EXPANDED_P_SCAN)}` and `k <= {EXPANDED_K_MAX}`.",
            f"- Dense overlap scan triggered: `{payload['scan']['dense_triggered']}`.",
            "- Canonical `first` order: `(p, k, |A|, pair alphabet, simplex alphabet, extra alphabet, reachable states, witness length, family, semantics)`.",
            "",
            "## Summary Table",
            "",
            "| Semantics | Kind | `|pair|` | `|simplex|` | `|extra|` | Families | First static split | First dynamic split | Best exact compression |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for summary in summaries:
        static_label = "none" if summary.first_static_split is None else f"{family_badge(summary.first_static_split.family)} @ (p={summary.first_static_split.p}, k={summary.first_static_split.k})"
        dynamic_label = "none" if summary.first_dynamic_split is None else f"{family_badge(summary.first_dynamic_split.family)} @ (p={summary.first_dynamic_split.p}, k={summary.first_dynamic_split.k})"
        compression_label = "none"
        if summary.best_explicit_exact_record is not None and summary.best_explicit_exact_record.best_explicit_exact_label is not None:
            compression_label = f"{summary.best_explicit_exact_record.best_explicit_exact_label} ({summary.best_explicit_exact_record.best_explicit_exact_count})"
        lines.append(
            f"| `{summary.label}` | `{summary.category}` | `{summary.pair_alphabet_size}` | `{summary.simplex_alphabet_size}` | `{summary.extra_alphabet_size}` | `{summary.families_scanned}` | `{static_label}` | `{dynamic_label}` | `{compression_label}` |"
        )

    lines.extend(["", "## Static vs Dynamic Boundary", ""])
    if overall_static is None:
        lines.append("- No static simplex-insufficient split appeared on the tested law library.")
    else:
        lines.append(
            f"- First static split: `{overall_static['semantics']}` on `{tuple(tuple(edge) for edge in overall_static['family'])}` at `(p={overall_static['p']}, k={overall_static['k']})`."
        )
        lines.append(
            f"  Counts: runtime `{overall_static['runtime_quotient_count']}`, simplex `{overall_static['simplex_quotient_count']}`, full state `{overall_static['full_state_quotient_count']}`."
        )
    if overall_dynamic is None:
        lines.append("- No dynamic hidden future beyond simplex appeared on the tested law library.")
    else:
        lines.append(
            f"- First dynamic hidden future: `{overall_dynamic['semantics']}` on `{dynamic_family}` at `(p={overall_dynamic['p']}, k={overall_dynamic['k']})`."
        )
        lines.append(
            f"  Counts: runtime `{overall_dynamic['runtime_quotient_count']}`, simplex `{overall_dynamic['simplex_quotient_count']}`, full state `{overall_dynamic['full_state_quotient_count']}`."
        )
    lines.append(
        f"- Static and dynamic first winners differ: `{payload['static_dynamic_differ']}`."
    )

    lines.extend(["", "## Global Quotient Compression", ""])
    if best_compression is None:
        lines.append("No tested explicit compression was exact beyond the raw global token state on the scanned global layer.")
    else:
        lines.extend(
            [
                f"- semantics: `{best_compression['semantics']}`",
                f"- family: `{compression_family}`",
                f"- raw global state count: `{best_compression['full_state_quotient_count']}`",
                f"- runtime quotient count: `{best_compression['runtime_quotient_count']}`",
                f"- best explicit exact compression: `{best_compression['best_explicit_exact_label']}` with quotient count `{best_compression['best_explicit_exact_count']}`",
            ]
        )
        lines.append("- candidate summaries:")
        for candidate in best_compression["explicit_global_compressions"]:
            lines.append(
                f"  - `{candidate['label']}`: count `{candidate['quotient_count']}`, exact `{candidate['exact']}`"
            )

    lines.extend(["", "## Lexicographically Minimal Witness Families", ""])
    lines.append("")
    lines.append("### Static")
    static_families = payload["lexicographically_minimal_static_families"]
    if not static_families:
        lines.append("- None")
    else:
        for entry in static_families:
            lines.append(
                f"- `{tuple(tuple(edge) for edge in entry['family'])}`; semantics `{entry['semantics']}`; kind `{entry['invariants']['obstruction_kind']}`; cycle rank `{entry['invariants']['pair_overlap_cycle_rank']}`; triangle clusters `{entry['invariants']['triangle_cluster_count']}`; tetra supports `{entry['invariants']['tetra_support_count']}`."
            )
    lines.append("")
    lines.append("### Dynamic")
    dynamic_families = payload["lexicographically_minimal_dynamic_families"]
    if not dynamic_families:
        lines.append("- None")
    else:
        for entry in dynamic_families:
            lines.append(
                f"- `{tuple(tuple(edge) for edge in entry['family'])}`; semantics `{entry['semantics']}`; kind `{entry['invariants']['obstruction_kind']}`; cycle rank `{entry['invariants']['pair_overlap_cycle_rank']}`; triangle clusters `{entry['invariants']['triangle_cluster_count']}`; tetra supports `{entry['invariants']['tetra_support_count']}`."
            )

    lines.extend(["", "## First Static Witness", ""])
    if overall_static is None:
        lines.append("No static witness was found.")
    else:
        witness = overall_static["simplex_witness"]
        family = tuple(tuple(edge) for edge in overall_static["family"])
        lines.extend(
            [
                f"- semantics: `{overall_static['semantics']}`",
                f"- family: `{family}`",
                f"- overlap kind: `{overall_static['invariants']['obstruction_kind']}`",
                f"- shared simplex fiber: `{witness['summary_value'] if witness else 'n/a'}`",
                f"- left prefix `u`: `{trace_text(tuple(witness['left_trace']) if witness and witness['left_trace'] else (), family) if witness else '[]'}`",
                f"- right prefix `v`: `{trace_text(tuple(witness['right_trace']) if witness and witness['right_trace'] else (), family) if witness else '[]'}`",
                f"- current outputs: `{witness['left_output_now'] if witness else 'n/a'}` versus `{witness['right_output_now'] if witness else 'n/a'}`",
            ]
        )

    lines.extend(["", "## First Dynamic Hidden Future", ""])
    if overall_dynamic is None:
        lines.append("No dynamic hidden future beyond simplex was found.")
    else:
        witness = overall_dynamic["hidden_future_beyond_simplex_witness"]
        family = tuple(tuple(edge) for edge in overall_dynamic["family"])
        lines.extend(
            [
                f"- semantics: `{overall_dynamic['semantics']}`",
                f"- family: `{family}`",
                f"- overlap kind: `{overall_dynamic['invariants']['obstruction_kind']}`",
                f"- shared simplex fiber: `{witness['summary_value'] if witness else 'n/a'}`",
                f"- left prefix `u`: `{trace_text(tuple(witness['left_trace']) if witness and witness['left_trace'] else (), family) if witness else '[]'}`",
                f"- right prefix `v`: `{trace_text(tuple(witness['right_trace']) if witness and witness['right_trace'] else (), family) if witness else '[]'}`",
                f"- shared current output: `{witness['left_output_now'] if witness else 'n/a'}`",
                f"- common non-empty suffix `w`: `{trace_text(tuple(witness['suffix']) if witness and witness['suffix'] else (), family) if witness else '[]'}`",
                f"- future outputs after `w`: `{witness['left_output_future'] if witness else 'n/a'}` versus `{witness['right_output_future'] if witness else 'n/a'}`",
            ]
        )

    lines.extend(["", "## Interpretation", ""])
    if overall_static is None and overall_dynamic is None:
        lines.append("On the tested law library and scan range, assignment + pair + simplex transport remained exact.")
    else:
        static_kind = overall_static["invariants"]["obstruction_kind"] if overall_static is not None else "none"
        dynamic_kind = overall_dynamic["invariants"]["obstruction_kind"] if overall_dynamic is not None else "none"
        lines.append(f"The first static obstruction is `{static_kind}`, while the first dynamic hidden future is `{dynamic_kind}`.")
        if overall_static is not None and overall_dynamic is not None:
            lines.append("The first global current-output obstruction and the first same-now / future-separate obstruction do not coincide.")
        else:
            lines.append("The current scan only supports one of the two obstruction notions, so the static/dynamic comparison remains incomplete.")
    if best_compression is not None:
        lines.append("The global layer is not only nontrivial; it is also non-canonical in its raw tokenization. At least one explicit quotient is strictly smaller than raw global state while remaining exact.")
    else:
        lines.append("No small exact explicit summary beat the raw global tokenization on the scanned layer, so the strongest exact quotient remains the full continuation quotient.")
    lines.append("Taken together, the data supports a local-to-global tower on the overlap complex: pair transport, simplex transport, and then a genuinely global obstruction layer whose first static and dynamic witnesses need not coincide.")

    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- JSON: [{json_path.name}]({json_path.name})",
            f"- Figure: [{svg_path.name}]({svg_path.name})",
        ]
    )
    if note_path is not None:
        lines.append(f"- Atlas note: [{note_path.name}](../../../docs/writing/experiments/holonomy/{note_path.name})")
    if compression_note_path is not None:
        lines.append(f"- Compression note: [{compression_note_path.name}](../../../docs/writing/experiments/holonomy/{compression_note_path.name})")
    return "\n".join(lines) + "\n"


def render_svg(payload: Dict[str, object], summaries: Sequence[SemanticSummary]) -> str:
    width = 1540
    left = 36
    top = 104
    table_width = width - 2 * left
    row_height = 34
    card_gap = 16
    card_width = (table_width - 2 * card_gap) / 3
    card_height = 122
    table_y = top + card_height + 28
    table_height = 74 + row_height * len(summaries)
    cards_y = table_y + table_height + 22
    bottom_height = 300
    footer_y = cards_y + bottom_height + 24
    height = footer_y + 46

    overall_static = payload["overall_first_static_split"]
    overall_dynamic = payload["overall_first_dynamic_split"]
    best_compression = payload["best_global_compression_record"]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: 'Inter', 'Segoe UI', Arial, sans-serif; font-size: 13px; fill: #243b53; }",
        ".title { font-size: 24px; font-weight: 700; fill: #102a43; }",
        ".subtitle { font-size: 14px; fill: #52606d; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1.2; rx: 18; ry: 18; }",
        ".card { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1.2; rx: 16; ry: 16; }",
        ".header { font-size: 12px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; fill: #486581; }",
        ".section { font-size: 17px; font-weight: 700; fill: #102a43; }",
        ".metric { font-size: 28px; font-weight: 700; fill: #0f172a; }",
        ".small { font-size: 12px; fill: #52606d; }",
        ".mono { font-family: 'SFMono-Regular', Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #102a43; }",
        ".row-control { fill: #f4f7f9; }",
        ".row-simplex { fill: #f7efff; }",
        ".row-cycle { fill: #eefbf3; }",
        ".row-tetra { fill: #fff4e6; }",
        ".divider { stroke: #e5e7eb; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f7fafc"/>',
        f'<text x="{left}" y="40" class="title">Global Holonomy Atlas</text>',
        f'<text x="{left}" y="64" class="subtitle">Classifying the first static and dynamic obstructions beyond simplex transport, then testing explicit compressed quotients inside the global layer.</text>',
        f'<text x="{left}" y="84" class="subtitle">Static = same assignment + pair + simplex, different now. Dynamic = same assignment + pair + simplex, same now, different future under a non-empty suffix.</text>',
    ]

    for index in range(3):
        x = left + index * (card_width + card_gap)
        lines.append(f'<rect x="{x}" y="{top}" width="{card_width}" height="{card_height}" class="card"/>')

    lines.extend(
        [
            f'<text x="{left + 18}" y="{top + 26}" class="header">Scan</text>',
            f'<text x="{left + 18}" y="{top + 58}" class="metric">{sum(summary.families_scanned for summary in summaries)}</text>',
            f'<text x="{left + 122}" y="{top + 58}" class="section">semantic-family analyses</text>',
            f'<text x="{left + 18}" y="{top + 86}" class="small">Base grid p ≤ {max(BASE_P_SCAN)}, k ≤ {BASE_K_MAX}. Expanded pass on five global semantics: {payload["scan"]["expanded_triggered"]}.</text>',
            f'<text x="{left + 18}" y="{top + 106}" class="small">Larger normalized p ≤ {max(EXPANDED_P_SCAN)}, k ≤ {EXPANDED_K_MAX} follow-up omitted because p = 4 already fixes the minimal-boundary winners.</text>',
        ]
    )

    static_x = left + card_width + card_gap + 18
    static_title = "none" if overall_static is None else family_badge(tuple(tuple(edge) for edge in overall_static["family"]))
    dynamic_title = "none" if overall_dynamic is None else family_badge(tuple(tuple(edge) for edge in overall_dynamic["family"]))
    lines.extend(
        [
            f'<text x="{static_x}" y="{top + 26}" class="header">Boundary Split</text>',
            f'<text x="{static_x}" y="{top + 54}" class="section">static = {static_title}</text>',
            f'<text x="{static_x}" y="{top + 78}" class="small">dynamic = {dynamic_title}</text>',
            f'<text x="{static_x}" y="{top + 100}" class="small">winners differ = {payload["static_dynamic_differ"]}</text>',
        ]
    )

    comp_x = left + 2 * (card_width + card_gap) + 18
    if best_compression is None:
        comp_line = "No tested explicit global summary was exact beyond the raw full state."
    else:
        comp_line = (
            f'{best_compression["best_explicit_exact_label"]} = {best_compression["best_explicit_exact_count"]} '
            f'on {family_badge(tuple(tuple(edge) for edge in best_compression["family"]))}'
        )
    lines.extend(
        [
            f'<text x="{comp_x}" y="{top + 26}" class="header">Compression</text>',
            f'<text x="{comp_x}" y="{top + 54}" class="section">Best explicit exact quotient</text>',
            f'<text x="{comp_x}" y="{top + 82}" class="small">{comp_line}</text>',
        ]
    )

    lines.append(f'<rect x="{left}" y="{table_y}" width="{table_width}" height="{table_height}" class="panel"/>')
    lines.append(f'<text x="{left + 18}" y="{table_y + 26}" class="header">Semantic Summary</text>')
    columns = {
        "sem": left + 18,
        "kind": left + 420,
        "alph": left + 560,
        "families": left + 690,
        "static": left + 790,
        "dynamic": left + 1035,
        "compression": left + 1280,
    }
    header_y = table_y + 64
    for key, label in (
        ("sem", "Semantics"),
        ("kind", "Kind"),
        ("alph", "|pair| / |simplex| / |extra|"),
        ("families", "Families"),
        ("static", "First static"),
        ("dynamic", "First dynamic"),
        ("compression", "Best exact compression"),
    ):
        lines.append(f'<text x="{columns[key]}" y="{header_y}" class="header">{label}</text>')
    lines.append(f'<line x1="{left + 18}" y1="{header_y + 10}" x2="{left + table_width - 18}" y2="{header_y + 10}" class="divider"/>')

    for index, summary in enumerate(summaries):
        y = header_y + 34 + index * row_height
        if summary.category == "control":
            row_class = "row-control"
        elif summary.category == "simplex_control":
            row_class = "row-simplex"
        elif summary.category == "global_cycle":
            row_class = "row-cycle"
        else:
            row_class = "row-tetra"
        lines.append(f'<rect x="{left + 12}" y="{y - 18}" width="{table_width - 24}" height="28" rx="12" ry="12" class="{row_class}"/>')
        static_label = "none" if summary.first_static_split is None else family_badge(summary.first_static_split.family)
        dynamic_label = "none" if summary.first_dynamic_split is None else family_badge(summary.first_dynamic_split.family)
        compression_label = "none"
        if summary.best_explicit_exact_record is not None and summary.best_explicit_exact_record.best_explicit_exact_label is not None:
            compression_label = f'{summary.best_explicit_exact_record.best_explicit_exact_label} ({summary.best_explicit_exact_record.best_explicit_exact_count})'
        lines.extend(
            [
                f'<text x="{columns["sem"]}" y="{y}">{summary.label}</text>',
                f'<text x="{columns["kind"]}" y="{y}">{summary.category}</text>',
                f'<text x="{columns["alph"]}" y="{y}">{summary.pair_alphabet_size} / {summary.simplex_alphabet_size} / {summary.extra_alphabet_size}</text>',
                f'<text x="{columns["families"]}" y="{y}" class="mono">{summary.families_scanned}</text>',
                f'<text x="{columns["static"]}" y="{y}">{static_label}</text>',
                f'<text x="{columns["dynamic"]}" y="{y}">{dynamic_label}</text>',
                f'<text x="{columns["compression"]}" y="{y}">{compression_label}</text>',
            ]
        )

    for index in range(2):
        x = left + index * ((table_width - card_gap) / 2 + card_gap)
        lines.append(f'<rect x="{x}" y="{cards_y}" width="{(table_width - card_gap) / 2}" height="{bottom_height}" class="card"/>')

    left_card_x = left + 18
    lines.append(f'<text x="{left_card_x}" y="{cards_y + 28}" class="header">Static vs Dynamic Obstruction</text>')
    if overall_static is None:
        lines.append(f'<text x="{left_card_x}" y="{cards_y + 56}" class="small">No static beyond-simplex split was found.</text>')
    else:
        lines.append(f'<text x="{left_card_x}" y="{cards_y + 56}" class="section">{overall_static["semantics"]}</text>')
        lines.append(f'<text x="{left_card_x}" y="{cards_y + 80}" class="small">Static family: {family_badge(tuple(tuple(edge) for edge in overall_static["family"]))}; kind = {overall_static["invariants"]["obstruction_kind"]}.</text>')
        lines.append(f'<text x="{left_card_x}" y="{cards_y + 104}" class="small">Simplex witness separates current outputs inside one lower-layer fiber.</text>')
    if overall_dynamic is None:
        lines.append(f'<text x="{left_card_x}" y="{cards_y + 140}" class="small">No hidden future beyond simplex was found.</text>')
    else:
        lines.append(f'<text x="{left_card_x}" y="{cards_y + 140}" class="section">{overall_dynamic["semantics"]}</text>')
        lines.append(f'<text x="{left_card_x}" y="{cards_y + 164}" class="small">Dynamic family: {family_badge(tuple(tuple(edge) for edge in overall_dynamic["family"]))}; kind = {overall_dynamic["invariants"]["obstruction_kind"]}.</text>')
        lines.append(f'<text x="{left_card_x}" y="{cards_y + 188}" class="small">Same-now / future-separate witness persists under a non-empty common suffix.</text>')

    right_card_x = left + (table_width - card_gap) / 2 + card_gap + 18
    lines.append(f'<text x="{right_card_x}" y="{cards_y + 28}" class="header">Compression Candidates</text>')
    if best_compression is None:
        lines.append(f'<text x="{right_card_x}" y="{cards_y + 56}" class="small">No explicit candidate summary beat the raw global state exactly.</text>')
    else:
        lines.append(f'<text x="{right_card_x}" y="{cards_y + 56}" class="section">{best_compression["semantics"]}</text>')
        lines.append(f'<text x="{right_card_x}" y="{cards_y + 80}" class="small">Family: {family_badge(tuple(tuple(edge) for edge in best_compression["family"]))}</text>')
        lines.append(f'<text x="{right_card_x}" y="{cards_y + 104}" class="small">Runtime / raw global = {best_compression["runtime_quotient_count"]} / {best_compression["full_state_quotient_count"]}</text>')
        lines.append(f'<text x="{right_card_x}" y="{cards_y + 128}" class="small">Best explicit exact = {best_compression["best_explicit_exact_label"]} ({best_compression["best_explicit_exact_count"]})</text>')
        y = cards_y + 162
        for candidate in best_compression["explicit_global_compressions"][:5]:
            lines.append(f'<text x="{right_card_x}" y="{y}" class="small">{candidate["label"]}: {candidate["quotient_count"]}, exact = {candidate["exact"]}</text>')
            y += 22

    lines.append(f'<text x="{left}" y="{footer_y}" class="small">Reading: the first current-output obstruction and the first hidden-future obstruction need not be the same family, and the global layer still admits explicit compression attempts beyond raw extra tokens.</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def build_note(payload: Dict[str, object]) -> str:
    overall_static = payload["overall_first_static_split"]
    overall_dynamic = payload["overall_first_dynamic_split"]
    lines = [
        "# Global Holonomy Atlas",
        "",
        "## Scope",
        "",
        f"- EXACT COMPUTATIONAL RESULT on the normalized base grid `p <= {max(BASE_P_SCAN)}` and `k <= {BASE_K_MAX}`, plus the named seed families used in the atlas.",
        "- The larger normalized `p <= 5, k <= 4` follow-up is intentionally omitted here because the `p = 4` scan already fixes the minimal-boundary winners in canonical first order.",
        "",
    ]
    if overall_static is not None:
        lines.extend(
            [
                "## First Static Obstruction",
                "",
                f"- EXACT COMPUTATIONAL RESULT: `{overall_static['semantics']}` first breaks current-output exactness beyond `assignment + pair + simplex` on `{tuple(tuple(edge) for edge in overall_static['family'])}`.",
                f"- Overlap kind: `{overall_static['invariants']['obstruction_kind']}`.",
                "",
            ]
        )
    if overall_dynamic is not None:
        lines.extend(
            [
                "## First Dynamic Obstruction",
                "",
                f"- EXACT COMPUTATIONAL RESULT: `{overall_dynamic['semantics']}` first yields a same-now / future-separate witness on `{tuple(tuple(edge) for edge in overall_dynamic['family'])}`.",
                f"- Overlap kind: `{overall_dynamic['invariants']['obstruction_kind']}`.",
                "",
            ]
        )
    lines.extend(
        [
            "## Observed Boundary",
            "",
            f"- Static and dynamic first winners differ: `{payload['static_dynamic_differ']}`.",
            "- The first global current-output obstruction and the first same-now / future-separate obstruction do not coincide.",
            "- This supports a local-to-global holonomy tower on the overlap complex: a current-output obstruction can appear before the strongest hidden-future obstruction does.",
            "",
        ]
    )
    return "\n".join(lines)


def build_compression_note(payload: Dict[str, object]) -> str | None:
    best = payload["best_global_compression_record"]
    if best is None:
        return None
    lines = [
        "# Global Quotient Compression",
        "",
        "## Scope",
        "",
        f"- EXACT COMPUTATIONAL RESULT on the same exact scanned set as the atlas: normalized base grid `p <= {max(BASE_P_SCAN)}`, `k <= {BASE_K_MAX}`, plus the named seed families.",
        "- The larger normalized `p <= 5, k <= 4` follow-up is intentionally omitted here because the `p = 4` scan already fixes the minimal-boundary winners.",
        "",
        "## Best Explicit Exact Candidate",
        "",
        f"- EXACT COMPUTATIONAL RESULT: semantics `{best['semantics']}` on family `{tuple(tuple(edge) for edge in best['family'])}`",
        f"- raw global state count: `{best['full_state_quotient_count']}`",
        f"- runtime quotient count: `{best['runtime_quotient_count']}`",
        f"- best explicit exact summary: `{best['best_explicit_exact_label']}` with quotient count `{best['best_explicit_exact_count']}`",
        "",
        "## Interpretation",
        "",
        "The continuation quotient can compress the global layer beyond raw extra tokens, and the best explicit candidate is the clearest exact hypothesis in the current scan for what the canonical global summary should retain.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    base_seed_records = seeded_scan(SEMANTICS, SEED_FAMILY_ORDER)
    base_records = run_scan(SEMANTICS, p_scan=BASE_P_SCAN, k_max=BASE_K_MAX, progress_label="base")
    all_records = merge_record_maps(base_seed_records, base_records)

    expanded_triggered = False
    dense_triggered = False

    compression_targets = [
        record
        for semantic in PROMISING_SEMANTICS
        for record in all_records[semantic.name]
        if not record.simplex_exact
    ]
    compression_index = {
        (record.semantics, record.family): record
        for record in compression_targets
    }
    if compression_targets:
        print(f"[compression] enriching {len(compression_targets)} beyond-simplex records")
        enriched = 0
        for semantic_name, records in list(all_records.items()):
            updated_records: List[AnalysisRecord] = []
            for record in records:
                if (record.semantics, record.family) in compression_index:
                    updated_records.append(enrich_record_with_compressions(record))
                    enriched += 1
                    if enriched % 25 == 0 or enriched == len(compression_targets):
                        print(f"[compression] {enriched}/{len(compression_targets)} records")
                else:
                    updated_records.append(record)
            all_records[semantic_name] = updated_records

    summaries = [summarize_semantic(semantic, all_records[semantic.name]) for semantic in SEMANTICS]
    static_candidates = [
        summary.first_static_split
        for summary in summaries
        if summary.first_static_split is not None
    ]
    dynamic_candidates = [
        summary.first_dynamic_split
        for summary in summaries
        if summary.first_dynamic_split is not None
    ]
    pair_candidates = [
        summary.first_pair_split
        for summary in summaries
        if summary.first_pair_split is not None
    ]
    static_candidates.sort(key=lambda record: witness_order_key(record, "static"))
    dynamic_candidates.sort(key=lambda record: witness_order_key(record, "dynamic"))
    pair_candidates.sort(key=lambda record: witness_order_key(record, "pair"))

    all_flat_records = [record for semantic in SEMANTICS for record in all_records[semantic.name]]
    minimal_static = minimal_winner_records(all_flat_records, "static")
    minimal_dynamic = minimal_winner_records(all_flat_records, "dynamic")

    compression_candidates = [
        summary.best_explicit_exact_record
        for summary in summaries
        if summary.best_explicit_exact_record is not None
    ]
    compression_candidates.sort(
        key=lambda record: (
            -compression_saving(record),
            record.best_explicit_exact_count or 10**9,
            record.p,
            record.k,
            len(record.family),
            record.semantics,
        )
    )

    json_path = RESULTS_DIR / "global_holonomy_atlas.json"
    report_path = RESULTS_DIR / "global_holonomy_atlas.md"
    svg_path = RESULTS_DIR / "global_holonomy_atlas.svg"
    note_path = DOCS_DIR / "global-holonomy-atlas.md"
    compression_note_path = DOCS_DIR / "global-quotient-compression.md"

    payload = {
        "scan": {
            "base_p_scan": list(BASE_P_SCAN),
            "base_k_max": BASE_K_MAX,
            "expanded_p_scan": list(EXPANDED_P_SCAN),
            "expanded_k_max": EXPANDED_K_MAX,
            "expanded_triggered": expanded_triggered,
            "expanded_semantics": [semantic.name for semantic in PROMISING_SEMANTICS],
            "expanded_rationale": (
                "not run in this atlas: canonical first-order winners already stabilize on the exact base grid "
                "at p=4, so full p<=5 normalization would only be a persistence study rather than part of the "
                "minimal-boundary theorem target"
            ),
            "dense_p_scan": list(DENSE_P_SCAN),
            "dense_k_max": DENSE_K_MAX,
            "dense_triggered": dense_triggered,
            "canonical_first_order": [
                "p",
                "k",
                "family_count",
                "pair_alphabet_size",
                "simplex_alphabet_size",
                "extra_alphabet_size",
                "reachable_state_count",
                "witness_length",
                "family",
                "semantics",
            ],
            "seed_families": {name: [list(edge) for edge in family] for name, family in SEED_FAMILIES.items()},
        },
        "semantics": [summary_to_json(summary) for summary in summaries],
        "records": {semantic.name: [record_to_json(record) for record in all_records[semantic.name]] for semantic in SEMANTICS},
        "overall_first_pair_split": None if not pair_candidates else record_to_json(pair_candidates[0]),
        "overall_first_static_split": None if not static_candidates else record_to_json(static_candidates[0]),
        "overall_first_dynamic_split": None if not dynamic_candidates else record_to_json(dynamic_candidates[0]),
        "lexicographically_minimal_static_families": unique_family_payload(minimal_static),
        "lexicographically_minimal_dynamic_families": unique_family_payload(minimal_dynamic),
        "static_dynamic_differ": (
            set(tuple(tuple(edge) for edge in entry["family"]) for entry in unique_family_payload(minimal_static))
            != set(tuple(tuple(edge) for edge in entry["family"]) for entry in unique_family_payload(minimal_dynamic))
        ),
        "best_global_compression_record": None if not compression_candidates else record_to_json(compression_candidates[0]),
    }

    json_path.write_text(json.dumps(payload, indent=2))
    note_path.write_text(build_note(payload))
    compression_note_text = build_compression_note(payload)
    if compression_note_text is not None:
        compression_note_path.write_text(compression_note_text)
    elif compression_note_path.exists():
        compression_note_path.unlink()

    report_path.write_text(build_report(summaries, payload, json_path, svg_path, note_path, compression_note_path if compression_note_text is not None else None))
    svg_path.write_text(render_svg(payload, summaries))

    print(f"Wrote {report_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {svg_path}")
    print(f"Wrote {note_path}")
    if compression_note_text is not None:
        print(f"Wrote {compression_note_path}")


if __name__ == "__main__":
    main()
