#!/usr/bin/env python3
"""Search beyond the simplex boundary.

This experiment asks two questions in parallel.

1. Is assignment + pair + simplex transport already exact, or can a deterministic
   local law force a hidden future beyond the simplex layer?
2. When simplex transport *is* exact, can the raw simplex carrier be compressed
   to a smaller exact quotient?
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import lru_cache
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
    PairDescriptor,
    TriangleDescriptor,
    Trace,
    WitnessRecord,
    build_context,
    edge_blocked_by_pair,
    edge_has_support,
    minimize_moore_machine,
    pair_triggered,
    trace_text,
    update_pair_token,
)

from pair_vs_simplex_holonomy_search import (
    SEMANTICS as PAIR_SIMPLEX_SEMANTICS,
    dense_overlap_families,
    edge_blocked_by_simplex,
    extract_automaton_witness,
    extract_segment_witness,
    group_rank,
    pair_feedback_allows,
    row_exactness,
    shortest_distinguishing_suffix,
    summary_exactness,
    triangle_pair_indices,
    triangle_triggered,
    update_simplex_token,
    witness_length,
)

RESULTS_DIR = ROOT / "results" / "holonomy" / "simplex-vs-global-holonomy"
DOCS_DIR = ROOT / "docs" / "writing" / "experiments" / "holonomy"

BASE_P_SCAN = (2, 3, 4)
BASE_K_MAX = 3
EXPANDED_P_SCAN = (5,)
EXPANDED_K_MAX = 4
DENSE_P_SCAN = (6,)
DENSE_K_MAX = 4

TRIANGLE_FAMILY: Family = ((1, 2), (1, 3), (2, 3))
TETRAHEDRON_3UNIFORM: Family = ((1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4))
FOUR_EDGE_STAR: Family = ((1, 2), (1, 3), (1, 4), (1, 5))
K4_PAIR_FAMILY: Family = (
    (1, 2),
    (1, 3),
    (1, 4),
    (2, 3),
    (2, 4),
    (3, 4),
)
TRIANGLE_CHAIN: Family = ((1, 2), (1, 3), (2, 3), (2, 4), (3, 4))
SEED_FAMILIES: Dict[str, Family] = {
    "triangle": TRIANGLE_FAMILY,
    "tetrahedron_3uniform": TETRAHEDRON_3UNIFORM,
    "four_edge_star": FOUR_EDGE_STAR,
    "k4_pair_family": K4_PAIR_FAMILY,
    "triangle_chain": TRIANGLE_CHAIN,
}
SEED_FAMILY_ORDER = tuple(SEED_FAMILIES.values())
PAIR_SIMPLEX_BY_NAME = {semantic.name: semantic for semantic in PAIR_SIMPLEX_SEMANTICS}


@dataclass(frozen=True)
class TetraDescriptor:
    tetra_index: int
    edges: Tuple[int, int, int, int]
    triangle_indices: Tuple[int, ...]


@dataclass(frozen=True)
class CycleDescriptor:
    cycle_index: int
    triangle_indices: Tuple[int, ...]
    edge_union: Tuple[int, ...]


@dataclass(frozen=True)
class ExtraSpec:
    name: str
    label: str
    description: str
    category: str
    scope: str
    alphabet_size: int
    trigger_kind: str
    update_kind: str
    gate_kind: str
    freeze_kind: str = "none"


@dataclass(frozen=True)
class CompressionSpec:
    name: str
    label: str
    projector: Callable[[Hashable, FamilyContext], Hashable]


@dataclass(frozen=True)
class SemanticDefinition:
    name: str
    label: str
    description: str
    category: str
    pair_alphabet_size: int
    simplex_alphabet_size: int
    extra_alphabet_size: int
    analysis_mode: str
    initial_state: Callable[[FamilyContext], Hashable]
    events: Callable[[FamilyContext], Tuple[Hashable, ...]]
    step: Callable[[Hashable, Hashable, FamilyContext], Hashable]
    output: Callable[[Hashable, FamilyContext], Hashable]
    assignment_summary: Callable[[Hashable, FamilyContext], Hashable]
    pair_summary: Callable[[Hashable, FamilyContext], Hashable]
    simplex_summary: Callable[[Hashable, FamilyContext], Hashable]
    full_state_summary: Callable[[Hashable, FamilyContext], Hashable]
    segment_states: Callable[[FamilyContext], Tuple[Hashable, ...]] | None = None
    compose: Callable[[Hashable, Hashable, FamilyContext], Hashable | None] | None = None


@dataclass(frozen=True)
class CandidateCompressionResult:
    name: str
    label: str
    quotient_count: int
    exact: bool


@dataclass(frozen=True)
class AnalysisRecord:
    semantics: str
    category: str
    pair_alphabet_size: int
    simplex_alphabet_size: int
    extra_alphabet_size: int
    p: int
    k: int
    family: Family
    reachable_state_count: int
    runtime_quotient_count: int
    assignment_quotient_count: int
    pair_quotient_count: int
    simplex_quotient_count: int
    full_state_quotient_count: int
    output_quotient_count: int
    assignment_curvature_gap: float
    pair_curvature_gap: float
    simplex_curvature_gap: float
    compressed_simplex_gap: float | None
    assignment_exact: bool
    pair_exact: bool
    simplex_exact: bool
    full_state_exact: bool
    output_exact: bool
    assignment_holonomy_rank: int
    pair_holonomy_rank: int
    simplex_holonomy_rank: int
    hidden_future_rank: int
    hidden_future_beyond_pair_rank: int
    hidden_future_beyond_simplex_rank: int
    assignment_witness: WitnessRecord | None
    hidden_future_witness: WitnessRecord | None
    pair_witness: WitnessRecord | None
    hidden_future_beyond_pair_witness: WitnessRecord | None
    simplex_witness: WitnessRecord | None
    hidden_future_beyond_simplex_witness: WitnessRecord | None
    explicit_compressions: Tuple[CandidateCompressionResult, ...]
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
    pair_split_count: int
    hidden_future_beyond_pair_count: int
    simplex_split_count: int
    hidden_future_beyond_simplex_count: int
    pair_exact_on_scan: bool
    simplex_exact_on_scan: bool
    max_pair_curvature_gap: float
    max_simplex_curvature_gap: float
    max_pair_holonomy_rank: int
    max_simplex_holonomy_rank: int
    max_hidden_future_beyond_pair_rank: int
    max_hidden_future_beyond_simplex_rank: int
    first_pair_split: AnalysisRecord | None
    first_hidden_future_beyond_pair_split: AnalysisRecord | None
    first_simplex_split: AnalysisRecord | None
    first_hidden_future_beyond_simplex_split: AnalysisRecord | None
    best_compression_record: AnalysisRecord | None


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


def family_badge(family: Family) -> str:
    for label, seed in SEED_FAMILIES.items():
        if family == seed:
            return label
    return f"|A|={len(family)}"


def unpack_state(state: Hashable) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
    if isinstance(state, tuple) and len(state) == 4 and isinstance(state[0], tuple):
        return state
    if isinstance(state, tuple) and len(state) == 3 and isinstance(state[0], tuple):
        assignment, pair_tokens, simplex_tokens = state
        return assignment, pair_tokens, simplex_tokens, tuple()
    raise ValueError(f"cannot unpack state {state!r}")


def empty_assignment(context: FamilyContext) -> Tuple[int, ...]:
    return tuple(-1 for _ in context.universe)


@lru_cache(maxsize=None)
def tetra_descriptors(family: Family) -> Tuple[TetraDescriptor, ...]:
    context = build_context(family)
    triangle_lookup = {tuple(sorted(triangle.edges)): triangle.triangle_index for triangle in context.triangles}
    descriptors: List[TetraDescriptor] = []
    for edges in combinations(range(len(family)), 4):
        if not all(set(family[left]) & set(family[right]) for left, right in combinations(edges, 2)):
            continue
        indices = []
        for triangle_edges in combinations(edges, 3):
            key = tuple(sorted(triangle_edges))
            if key not in triangle_lookup:
                break
            indices.append(triangle_lookup[key])
        else:
            descriptors.append(
                TetraDescriptor(
                    tetra_index=len(descriptors),
                    edges=tuple(edges),
                    triangle_indices=tuple(indices),
                )
            )
    return tuple(descriptors)


@lru_cache(maxsize=None)
def cycle_descriptors(family: Family) -> Tuple[CycleDescriptor, ...]:
    context = build_context(family)
    triangles = context.triangles
    if len(triangles) < 3:
        return tuple()

    adjacency: Dict[int, set[int]] = {triangle.triangle_index: set() for triangle in triangles}
    for left, right in combinations(triangles, 2):
        if set(left.edges) & set(right.edges):
            adjacency[left.triangle_index].add(right.triangle_index)
            adjacency[right.triangle_index].add(left.triangle_index)

    parent: Dict[int, int | None] = {}
    depth: Dict[int, int] = {}
    basis: Dict[frozenset[int], Tuple[int, ...]] = {}

    for start in adjacency:
        if start in parent:
            continue
        parent[start] = None
        depth[start] = 0
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for neighbor in sorted(adjacency[node]):
                if neighbor not in parent:
                    parent[neighbor] = node
                    depth[neighbor] = depth[node] + 1
                    queue.append(neighbor)
                    continue
                if parent[node] == neighbor or parent[neighbor] == node:
                    continue
                if depth[neighbor] > depth[node]:
                    continue
                left_path = [node]
                right_path = [neighbor]
                left_cursor = node
                right_cursor = neighbor
                while depth[left_cursor] > depth[right_cursor]:
                    left_cursor = parent[left_cursor]  # type: ignore[index]
                    left_path.append(left_cursor)
                while depth[right_cursor] > depth[left_cursor]:
                    right_cursor = parent[right_cursor]  # type: ignore[index]
                    right_path.append(right_cursor)
                while left_cursor != right_cursor:
                    left_cursor = parent[left_cursor]  # type: ignore[index]
                    right_cursor = parent[right_cursor]  # type: ignore[index]
                    left_path.append(left_cursor)
                    right_path.append(right_cursor)
                cycle = tuple(left_path[:-1] + list(reversed(right_path)))
                if len(cycle) < 3:
                    continue
                key = frozenset(cycle)
                if key in basis:
                    continue
                basis[key] = cycle

    descriptors: List[CycleDescriptor] = []
    for cycle in sorted(basis.values(), key=lambda cycle: (len(cycle), cycle)):
        edge_union = tuple(
            sorted(set().union(*(set(context.triangles[index].edges) for index in cycle)))
        )
        descriptors.append(
            CycleDescriptor(
                cycle_index=len(descriptors),
                triangle_indices=cycle,
                edge_union=edge_union,
            )
        )
    return tuple(descriptors)


def base_assignment_summary(state: Hashable, context: FamilyContext) -> Hashable:
    assignment, _, _, _ = unpack_state(state)
    return assignment


def base_pair_summary(state: Hashable, context: FamilyContext) -> Hashable:
    assignment, pair_tokens, _, _ = unpack_state(state)
    return assignment, pair_tokens


def base_simplex_summary(state: Hashable, context: FamilyContext) -> Hashable:
    assignment, pair_tokens, simplex_tokens, _ = unpack_state(state)
    return assignment, pair_tokens, simplex_tokens


def base_full_state_summary(state: Hashable, context: FamilyContext) -> Hashable:
    return state


def active_token(value: int) -> bool:
    return value != 0


def edge_blocked_by_extra(
    edge_index: int,
    extra_tokens: Sequence[int],
    family: Family,
    spec: ExtraSpec,
) -> bool:
    if not extra_tokens:
        return False
    if spec.scope == "tetra":
        descriptors = tetra_descriptors(family)
        for descriptor, token in zip(descriptors, extra_tokens):
            if token == 0:
                continue
            if spec.gate_kind == "block_lowest_complete":
                if edge_index == min(descriptor.edges):
                    return True
            elif spec.gate_kind == "block_oriented_complete":
                local_index = descriptor.edges.index(edge_index) + 1 if edge_index in descriptor.edges else -1
                if local_index == token:
                    return True
            elif spec.gate_kind == "block_debt2_lowest":
                if token == 2 and edge_index == min(descriptor.edges):
                    return True
            else:
                raise ValueError(f"unknown extra gate {spec.gate_kind}")
        return False
    descriptors = cycle_descriptors(family)
    for descriptor, token in zip(descriptors, extra_tokens):
        if token == 0:
            continue
        if spec.gate_kind == "block_cycle_lowest_complete":
            if edge_index == min(descriptor.edge_union):
                return True
        else:
            raise ValueError(f"unknown cycle gate {spec.gate_kind}")
    return False


def triangle_frozen_by_extra(
    triangle_index: int,
    extra_tokens: Sequence[int],
    family: Family,
    spec: ExtraSpec,
) -> bool:
    if not extra_tokens or spec.freeze_kind == "none":
        return False
    if spec.scope == "tetra":
        descriptors = tetra_descriptors(family)
        return any(
            token != 0 and triangle_index in descriptor.triangle_indices
            for descriptor, token in zip(descriptors, extra_tokens)
        )
    descriptors = cycle_descriptors(family)
    return any(
        token != 0 and triangle_index in descriptor.triangle_indices
        for descriptor, token in zip(descriptors, extra_tokens)
    )


def extra_triggered(
    spec: ExtraSpec,
    descriptor: TetraDescriptor | CycleDescriptor,
    assignment: Sequence[int],
    simplex_tokens: Sequence[int],
    event: Tuple[int, int],
) -> bool:
    _, chosen_edge = event
    if isinstance(descriptor, TetraDescriptor):
        if chosen_edge not in descriptor.edges:
            return False
        active_faces = sum(1 for index in descriptor.triangle_indices if simplex_tokens[index] != 0)
        live_before = sum(1 for edge_index in descriptor.edges if edge_has_support(assignment, edge_index))
        live_after = live_before + (0 if edge_has_support(assignment, chosen_edge) else 1)
        if spec.trigger_kind == "tetra_two_faces":
            return active_faces >= 2 and live_after >= 3
        if spec.trigger_kind == "tetra_full":
            return active_faces >= 1 and live_before == 3 and live_after == 4
        if spec.trigger_kind == "tetra_third_or_fourth":
            return active_faces >= 1 and (live_before, live_after) in {(2, 3), (3, 4)}
        if spec.trigger_kind == "tetra_face_order":
            return active_faces >= 2 and chosen_edge == min(descriptor.edges)
        raise ValueError(f"unknown tetra trigger {spec.trigger_kind}")
    if chosen_edge not in descriptor.edge_union:
        return False
    active_faces = sum(1 for index in descriptor.triangle_indices if simplex_tokens[index] != 0)
    if spec.trigger_kind == "cycle_flux":
        return active_faces >= 2 and chosen_edge == min(descriptor.edge_union)
    if spec.trigger_kind == "cycle_feedback":
        return active_faces >= 1 and chosen_edge in descriptor.edge_union
    if spec.trigger_kind == "cycle_parity":
        return active_faces % 2 == 1 and chosen_edge in descriptor.edge_union
    raise ValueError(f"unknown cycle trigger {spec.trigger_kind}")


def update_extra_token(
    current: int,
    spec: ExtraSpec,
    event: Tuple[int, int],
    descriptor: TetraDescriptor | CycleDescriptor,
) -> int:
    _, chosen_edge = event
    if spec.update_kind == "toggle_mod2":
        return current ^ 1
    if spec.update_kind == "orientation":
        if not isinstance(descriptor, TetraDescriptor):
            raise ValueError("orientation update only supported on tetra descriptors")
        return descriptor.edges.index(chosen_edge) + 1
    if spec.update_kind == "capped_inc2":
        return min(2, current + 1)
    raise ValueError(f"unknown extra update {spec.update_kind}")


def extra_initial(context: FamilyContext, spec: ExtraSpec) -> Tuple[int, ...]:
    descriptors = tetra_descriptors(context.family) if spec.scope == "tetra" else cycle_descriptors(context.family)
    return tuple(0 for _ in descriptors)


def make_global_semantic(spec: ExtraSpec) -> SemanticDefinition:
    def initial_state(context: FamilyContext) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
        return (
            tuple(-1 for _ in context.universe),
            tuple(0 for _ in context.pairs),
            tuple(0 for _ in context.triangles),
            extra_initial(context, spec),
        )

    def events(context: FamilyContext) -> Tuple[Tuple[int, int], ...]:
        return context.assignment_events

    def step(
        state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
        event: Tuple[int, int],
        context: FamilyContext,
    ) -> Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]]:
        assignment, pair_tokens, simplex_tokens, extra_tokens = state
        variable, chosen_edge = event
        if assignment[variable - 1] >= 0:
            return state

        updated_assignment = list(assignment)
        updated_pairs = list(pair_tokens)
        updated_simplex = list(simplex_tokens)
        updated_extra = list(extra_tokens)

        for pair in context.pairs:
            if not pair_feedback_allows("freeze_if_simplex_active", pair, simplex_tokens, context):
                continue
            if pair_triggered("shared_other_live", pair, assignment, event):
                updated_pairs[pair.pair_index] = update_pair_token(
                    updated_pairs[pair.pair_index],
                    "toggle_mod2",
                    chosen_edge,
                    pair,
                )

        for triangle in context.triangles:
            if triangle_frozen_by_extra(triangle.triangle_index, extra_tokens, context.family, spec):
                continue
            if triangle_triggered(
                "second_or_third",
                triangle,
                assignment,
                tuple(updated_pairs),
                simplex_tokens,
                event,
                context,
            ):
                updated_simplex[triangle.triangle_index] = update_simplex_token(
                    updated_simplex[triangle.triangle_index],
                    "orientation",
                    chosen_edge,
                    triangle,
                )

        descriptors: Sequence[TetraDescriptor | CycleDescriptor]
        descriptors = tetra_descriptors(context.family) if spec.scope == "tetra" else cycle_descriptors(context.family)
        for descriptor in descriptors:
            if extra_triggered(spec, descriptor, assignment, tuple(updated_simplex), event):
                index = descriptor.tetra_index if isinstance(descriptor, TetraDescriptor) else descriptor.cycle_index
                updated_extra[index] = update_extra_token(updated_extra[index], spec, event, descriptor)

        updated_assignment[variable - 1] = chosen_edge
        return tuple(updated_assignment), tuple(updated_pairs), tuple(updated_simplex), tuple(updated_extra)

    def output(
        state: Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
        context: FamilyContext,
    ) -> Family:
        assignment, pair_tokens, simplex_tokens, extra_tokens = state
        residuals: List[Tuple[int, ...]] = []
        for edge_index, edge in enumerate(context.family):
            live = True
            remaining: List[int] = []
            for variable in edge:
                value = assignment[variable - 1]
                if value == -1:
                    remaining.append(variable)
                elif value != edge_index:
                    live = False
                    break
            if not live:
                continue
            if not remaining:
                pair_blocked = any(
                    edge_blocked_by_pair(
                        edge_index,
                        context.pairs[pair_index],
                        pair_tokens[pair_index],
                        "toggle_mod2",
                        "block_lower_complete",
                    )
                    for pair_index in context.pair_indices_by_edge[edge_index]
                )
                simplex_blocked = any(
                    edge_blocked_by_simplex(
                        edge_index,
                        context.triangles[triangle_index],
                        simplex_tokens[triangle_index],
                        "block_oriented_complete",
                    )
                    for triangle_index in context.triangle_indices_by_edge[edge_index]
                )
                extra_blocked = edge_blocked_by_extra(edge_index, extra_tokens, context.family, spec)
                if pair_blocked or simplex_blocked or extra_blocked:
                    continue
            residuals.append(tuple(remaining))
        return tuple(residuals)

    return SemanticDefinition(
        name=f"pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs__{spec.name}",
        label=f"Feedback Orient + {spec.label}",
        description=(
            "Shared-other-live pair phase with simplex orientation/freeze, extended by "
            f"{spec.description}"
        ),
        category=spec.category,
        pair_alphabet_size=2,
        simplex_alphabet_size=4,
        extra_alphabet_size=spec.alphabet_size,
        analysis_mode="automaton",
        initial_state=initial_state,
        events=events,
        step=step,
        output=output,
        assignment_summary=base_assignment_summary,
        pair_summary=base_pair_summary,
        simplex_summary=base_simplex_summary,
        full_state_summary=base_full_state_summary,
    )


EXTRA_SPECS = (
    ExtraSpec(
        name="tetra_commutator_toggle",
        label="Tetra Toggle",
        description="a tetra-local toggle that activates once multiple simplex faces are live inside a 4-clique and blocks the lowest edge on completion.",
        category="tetra_local",
        scope="tetra",
        alphabet_size=2,
        trigger_kind="tetra_two_faces",
        update_kind="toggle_mod2",
        gate_kind="block_lowest_complete",
    ),
    ExtraSpec(
        name="tetra_orient_second_or_third",
        label="Tetra Orient",
        description="a tetra orientation token that records which edge carried the third or fourth live face into a 4-clique and blocks that edge on completion.",
        category="tetra_local",
        scope="tetra",
        alphabet_size=5,
        trigger_kind="tetra_third_or_fourth",
        update_kind="orientation",
        gate_kind="block_oriented_complete",
    ),
    ExtraSpec(
        name="tetra_debt",
        label="Tetra Debt",
        description="a capped tetra debt that accumulates when simplex transport closes a 4-clique and blocks the lowest edge at debt level 2.",
        category="tetra_local",
        scope="tetra",
        alphabet_size=3,
        trigger_kind="tetra_full",
        update_kind="capped_inc2",
        gate_kind="block_debt2_lowest",
    ),
    ExtraSpec(
        name="tetra_freeze_simplex",
        label="Tetra Freeze",
        description="a tetra-local toggle that later freezes incident simplex updates and blocks the lowest edge while active.",
        category="tetra_local",
        scope="tetra",
        alphabet_size=2,
        trigger_kind="tetra_face_order",
        update_kind="toggle_mod2",
        gate_kind="block_lowest_complete",
        freeze_kind="freeze_incident",
    ),
    ExtraSpec(
        name="triangle_cycle_flux",
        label="Cycle Flux",
        description="a cycle flux bit attached to a triangle cycle; odd flux blocks the lowest cycle edge on completion.",
        category="global_cycle",
        scope="cycle",
        alphabet_size=2,
        trigger_kind="cycle_flux",
        update_kind="toggle_mod2",
        gate_kind="block_cycle_lowest_complete",
    ),
    ExtraSpec(
        name="simplex_feedback_loop",
        label="Feedback Loop",
        description="a cycle-local feedback bit that can freeze simplex updates along an active triangle cycle.",
        category="global_cycle",
        scope="cycle",
        alphabet_size=2,
        trigger_kind="cycle_feedback",
        update_kind="toggle_mod2",
        gate_kind="block_cycle_lowest_complete",
        freeze_kind="freeze_incident",
    ),
    ExtraSpec(
        name="parity_on_face_order",
        label="Face-Order Parity",
        description="a cycle parity bit that records odd face-order circulation across an active triangle cycle and blocks the cycle minimum edge on completion.",
        category="global_cycle",
        scope="cycle",
        alphabet_size=2,
        trigger_kind="cycle_parity",
        update_kind="toggle_mod2",
        gate_kind="block_cycle_lowest_complete",
    ),
)


def adapt_existing(name: str, category: str) -> SemanticDefinition:
    base = PAIR_SIMPLEX_BY_NAME[name]
    return SemanticDefinition(
        name=base.name,
        label=base.label,
        description=base.description,
        category=category,
        pair_alphabet_size=base.pair_alphabet_size,
        simplex_alphabet_size=base.simplex_alphabet_size,
        extra_alphabet_size=1,
        analysis_mode=base.analysis_mode,
        initial_state=base.initial_state,
        events=base.events,
        step=base.step,
        output=base.output,
        assignment_summary=base.assignment_summary,
        pair_summary=base.pair_summary,
        simplex_summary=base.simplex_summary,
        full_state_summary=base.full_state_summary,
        segment_states=base.segment_states,
        compose=base.compose,
    )


SEMANTICS: Tuple[SemanticDefinition, ...] = (
    adapt_existing("broadcast_control", "control"),
    adapt_existing("committed_allocation", "control"),
    adapt_existing("pair_phase_exclusive_other_live_block_lower", "pair_control"),
    adapt_existing("pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs", "simplex_control"),
    *(make_global_semantic(spec) for spec in EXTRA_SPECS),
)


def simplex_presence_summary(state: Hashable, context: FamilyContext) -> Hashable:
    assignment, pair_tokens, simplex_tokens, _ = unpack_state(state)
    return assignment, pair_tokens, tuple(1 if token else 0 for token in simplex_tokens)


def simplex_histogram_summary(state: Hashable, context: FamilyContext) -> Hashable:
    assignment, pair_tokens, simplex_tokens, _ = unpack_state(state)
    histogram: DefaultDict[int, int] = defaultdict(int)
    for token in simplex_tokens:
        histogram[token] += 1
    return assignment, pair_tokens, tuple(sorted(histogram.items()))


def simplex_incidence_profile_summary(state: Hashable, context: FamilyContext) -> Hashable:
    assignment, pair_tokens, simplex_tokens, _ = unpack_state(state)
    profile = []
    for edge_index in range(len(context.family)):
        profile.append(
            sum(
                1
                for triangle_index in context.triangle_indices_by_edge[edge_index]
                if simplex_tokens[triangle_index] != 0
            )
        )
    return assignment, pair_tokens, tuple(profile)


def simplex_block_profile_summary(state: Hashable, context: FamilyContext) -> Hashable:
    assignment, pair_tokens, simplex_tokens, _ = unpack_state(state)
    profile = []
    for edge_index in range(len(context.family)):
        profile.append(
            sum(
                1
                for triangle_index in context.triangle_indices_by_edge[edge_index]
                if edge_blocked_by_simplex(
                    edge_index,
                    context.triangles[triangle_index],
                    simplex_tokens[triangle_index],
                    "block_oriented_complete",
                )
            )
        )
    return assignment, pair_tokens, tuple(profile)


def simplex_sorted_tokens_summary(state: Hashable, context: FamilyContext) -> Hashable:
    assignment, pair_tokens, simplex_tokens, _ = unpack_state(state)
    return assignment, pair_tokens, tuple(sorted(simplex_tokens))


COMPRESSION_SPECS = (
    CompressionSpec("simplex_presence", "Simplex presence", simplex_presence_summary),
    CompressionSpec("simplex_histogram", "Simplex histogram", simplex_histogram_summary),
    CompressionSpec("simplex_incidence_profile", "Triangle incidence profile", simplex_incidence_profile_summary),
    CompressionSpec("simplex_block_profile", "Blocked-edge profile", simplex_block_profile_summary),
    CompressionSpec("simplex_sorted_tokens", "Sorted simplex tokens", simplex_sorted_tokens_summary),
)


def explore_automaton(
    semantic: SemanticDefinition,
    context: FamilyContext,
) -> Tuple[
    Tuple[Hashable, ...],
    Dict[Hashable, Dict[Hashable, Hashable]],
    Dict[Hashable, Hashable],
    Dict[Hashable, Trace],
]:
    initial = semantic.initial_state(context)
    events = semantic.events(context)
    states: List[Hashable] = []
    transitions: Dict[Hashable, Dict[Hashable, Hashable]] = {}
    outputs: Dict[Hashable, Hashable] = {}
    shortest_trace: Dict[Hashable, Trace] = {initial: tuple()}
    queue = deque([initial])
    seen = {initial}
    while queue:
        state = queue.popleft()
        states.append(state)
        outputs[state] = semantic.output(state, context)
        transitions[state] = {}
        for event in events:
            next_state = semantic.step(state, event, context)
            transitions[state][event] = next_state
            if next_state not in seen:
                seen.add(next_state)
                shortest_trace[next_state] = shortest_trace[state] + (event,)
                queue.append(next_state)
    return tuple(states), transitions, outputs, shortest_trace


def compression_results(
    semantic: SemanticDefinition,
    states: Sequence[Hashable],
    context: FamilyContext,
    block_of: Dict[Hashable, int],
) -> Tuple[CandidateCompressionResult, ...]:
    results: List[CandidateCompressionResult] = []
    if not states:
        return tuple()
    try:
        unpack_state(states[0])
    except ValueError:
        return tuple()
    for spec in COMPRESSION_SPECS:
        quotient_count, exact = summary_exactness(spec.projector, states, context, block_of)
        results.append(
            CandidateCompressionResult(
                name=spec.name,
                label=spec.label,
                quotient_count=quotient_count,
                exact=exact,
            )
        )
    return tuple(results)


def analyze_automaton(semantic: SemanticDefinition, context: FamilyContext) -> AnalysisRecord:
    states, transitions, outputs, shortest_trace = explore_automaton(semantic, context)
    events = semantic.events(context)
    block_of = minimize_moore_machine(states, events, transitions, outputs)
    runtime_count = len(set(block_of.values()))

    assignment_count, assignment_exact = summary_exactness(semantic.assignment_summary, states, context, block_of)
    pair_count, pair_exact = summary_exactness(semantic.pair_summary, states, context, block_of)
    simplex_count, simplex_exact = summary_exactness(semantic.simplex_summary, states, context, block_of)
    full_state_count, full_state_exact = summary_exactness(semantic.full_state_summary, states, context, block_of)
    output_count, output_exact = summary_exactness(lambda state, _: outputs[state], states, context, block_of)

    assignment_witness = extract_automaton_witness(
        states,
        context,
        semantic.assignment_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
    )
    hidden_future_witness = extract_automaton_witness(
        states,
        context,
        semantic.assignment_summary,
        block_of,
        outputs,
        transitions,
        shortest_trace,
        events,
        require_same_output=True,
        require_non_empty_suffix=True,
    )
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
    hidden_future_beyond_pair_witness = extract_automaton_witness(
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
    hidden_future_beyond_simplex_witness = extract_automaton_witness(
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

    explicit = compression_results(semantic, states, context, block_of)
    exact_explicit = [item for item in explicit if item.exact]
    exact_explicit.sort(key=lambda item: (item.quotient_count, item.label))
    best_label = exact_explicit[0].label if exact_explicit else None
    best_count = exact_explicit[0].quotient_count if exact_explicit else None
    compressed_gap = None if best_count is None else log2_count(runtime_count) - log2_count(best_count)

    return AnalysisRecord(
        semantics=semantic.name,
        category=semantic.category,
        pair_alphabet_size=semantic.pair_alphabet_size,
        simplex_alphabet_size=semantic.simplex_alphabet_size,
        extra_alphabet_size=semantic.extra_alphabet_size,
        p=max(context.universe) if context.universe else 0,
        k=max((len(edge) for edge in context.family), default=0),
        family=context.family,
        reachable_state_count=len(states),
        runtime_quotient_count=runtime_count,
        assignment_quotient_count=assignment_count,
        pair_quotient_count=pair_count,
        simplex_quotient_count=simplex_count,
        full_state_quotient_count=full_state_count,
        output_quotient_count=output_count,
        assignment_curvature_gap=log2_count(runtime_count) - log2_count(assignment_count),
        pair_curvature_gap=log2_count(runtime_count) - log2_count(pair_count),
        simplex_curvature_gap=log2_count(runtime_count) - log2_count(simplex_count),
        compressed_simplex_gap=compressed_gap,
        assignment_exact=assignment_exact,
        pair_exact=pair_exact,
        simplex_exact=simplex_exact,
        full_state_exact=full_state_exact,
        output_exact=output_exact,
        assignment_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.assignment_summary(state, context)),
        pair_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.pair_summary(state, context)),
        simplex_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.simplex_summary(state, context)),
        hidden_future_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.assignment_summary(state, context), outputs[state])),
        hidden_future_beyond_pair_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.pair_summary(state, context), outputs[state])),
        hidden_future_beyond_simplex_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.simplex_summary(state, context), outputs[state])),
        assignment_witness=assignment_witness,
        hidden_future_witness=hidden_future_witness,
        pair_witness=pair_witness,
        hidden_future_beyond_pair_witness=hidden_future_beyond_pair_witness,
        simplex_witness=simplex_witness,
        hidden_future_beyond_simplex_witness=hidden_future_beyond_simplex_witness,
        explicit_compressions=explicit,
        best_explicit_exact_label=best_label,
        best_explicit_exact_count=best_count,
    )


def analyze_segment_rows(semantic: SemanticDefinition, context: FamilyContext) -> AnalysisRecord:
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

    assignment_count, assignment_exact = row_exactness(semantic.assignment_summary, states, context, row_of)
    pair_count, pair_exact = row_exactness(semantic.pair_summary, states, context, row_of)
    simplex_count, simplex_exact = row_exactness(semantic.simplex_summary, states, context, row_of)
    full_state_count, full_state_exact = row_exactness(semantic.full_state_summary, states, context, row_of)
    output_count, output_exact = row_exactness(lambda state, ctx: semantic.output(state, ctx), states, context, row_of)

    assignment_witness = extract_segment_witness(
        states,
        context,
        semantic.assignment_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
    )
    hidden_future_witness = extract_segment_witness(
        states,
        context,
        semantic.assignment_summary,
        row_of,
        block_of,
        semantic.output,
        states,
        semantic.compose,
        empty_state,
        require_same_output=True,
        require_non_empty_suffix=True,
    )
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
    hidden_future_beyond_pair_witness = extract_segment_witness(
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
    hidden_future_beyond_simplex_witness = extract_segment_witness(
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
        category=semantic.category,
        pair_alphabet_size=semantic.pair_alphabet_size,
        simplex_alphabet_size=semantic.simplex_alphabet_size,
        extra_alphabet_size=semantic.extra_alphabet_size,
        p=max(context.universe) if context.universe else 0,
        k=max((len(edge) for edge in context.family), default=0),
        family=context.family,
        reachable_state_count=len(states),
        runtime_quotient_count=runtime_count,
        assignment_quotient_count=assignment_count,
        pair_quotient_count=pair_count,
        simplex_quotient_count=simplex_count,
        full_state_quotient_count=full_state_count,
        output_quotient_count=output_count,
        assignment_curvature_gap=log2_count(runtime_count) - log2_count(assignment_count),
        pair_curvature_gap=log2_count(runtime_count) - log2_count(pair_count),
        simplex_curvature_gap=log2_count(runtime_count) - log2_count(simplex_count),
        compressed_simplex_gap=None,
        assignment_exact=assignment_exact,
        pair_exact=pair_exact,
        simplex_exact=simplex_exact,
        full_state_exact=full_state_exact,
        output_exact=output_exact,
        assignment_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.assignment_summary(state, context)),
        pair_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.pair_summary(state, context)),
        simplex_holonomy_rank=group_rank(states, block_of, key_fn=lambda state: semantic.simplex_summary(state, context)),
        hidden_future_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.assignment_summary(state, context), semantic.output(state, context))),
        hidden_future_beyond_pair_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.pair_summary(state, context), semantic.output(state, context))),
        hidden_future_beyond_simplex_rank=group_rank(states, block_of, key_fn=lambda state: (semantic.simplex_summary(state, context), semantic.output(state, context))),
        assignment_witness=assignment_witness,
        hidden_future_witness=hidden_future_witness,
        pair_witness=pair_witness,
        hidden_future_beyond_pair_witness=hidden_future_beyond_pair_witness,
        simplex_witness=simplex_witness,
        hidden_future_beyond_simplex_witness=hidden_future_beyond_simplex_witness,
        explicit_compressions=tuple(),
        best_explicit_exact_label=None,
        best_explicit_exact_count=None,
    )


def analyze_family(semantic: SemanticDefinition, family: Family) -> AnalysisRecord:
    context = build_context(family)
    if semantic.analysis_mode == "segment_rows":
        return analyze_segment_rows(semantic, context)
    return analyze_automaton(semantic, context)


def witness_key(record: AnalysisRecord, witness_kind: str) -> Tuple[object, ...]:
    if witness_kind == "pair":
        witness = record.pair_witness
    elif witness_kind == "hidden_pair":
        witness = record.hidden_future_beyond_pair_witness
    elif witness_kind == "simplex":
        witness = record.simplex_witness
    elif witness_kind == "hidden_simplex":
        witness = record.hidden_future_beyond_simplex_witness
    else:
        raise ValueError(f"unknown witness kind {witness_kind}")
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


def summarize_semantic(semantic: SemanticDefinition, records: Sequence[AnalysisRecord]) -> SemanticSummary:
    seed_record = None
    for family in SEED_FAMILY_ORDER:
        match = next((record for record in records if record.family == family), None)
        if match is not None:
            seed_record = match
            break

    pair_split = [record for record in records if not record.pair_exact]
    hidden_pair = [record for record in records if record.hidden_future_beyond_pair_witness is not None]
    simplex_split = [record for record in records if not record.simplex_exact]
    hidden_simplex = [record for record in records if record.hidden_future_beyond_simplex_witness is not None]
    if pair_split:
        pair_split.sort(key=lambda record: witness_key(record, "pair"))
    if hidden_pair:
        hidden_pair.sort(key=lambda record: witness_key(record, "hidden_pair"))
    if simplex_split:
        simplex_split.sort(key=lambda record: witness_key(record, "simplex"))
    if hidden_simplex:
        hidden_simplex.sort(key=lambda record: witness_key(record, "hidden_simplex"))

    simplex_exact_records = [
        record
        for record in records
        if record.simplex_exact
        and record.best_explicit_exact_count is not None
        and record.simplex_alphabet_size > 1
        and record.simplex_quotient_count > record.best_explicit_exact_count
    ]
    simplex_exact_records.sort(
        key=lambda record: (
            -(record.simplex_quotient_count - (record.best_explicit_exact_count or 0)),
            record.best_explicit_exact_count if record.best_explicit_exact_count is not None else 10**9,
            record.simplex_quotient_count,
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
        pair_split_count=len(pair_split),
        hidden_future_beyond_pair_count=len(hidden_pair),
        simplex_split_count=len(simplex_split),
        hidden_future_beyond_simplex_count=len(hidden_simplex),
        pair_exact_on_scan=all(record.pair_exact for record in records),
        simplex_exact_on_scan=all(record.simplex_exact for record in records),
        max_pair_curvature_gap=max(record.pair_curvature_gap for record in records),
        max_simplex_curvature_gap=max(record.simplex_curvature_gap for record in records),
        max_pair_holonomy_rank=max(record.pair_holonomy_rank for record in records),
        max_simplex_holonomy_rank=max(record.simplex_holonomy_rank for record in records),
        max_hidden_future_beyond_pair_rank=max(record.hidden_future_beyond_pair_rank for record in records),
        max_hidden_future_beyond_simplex_rank=max(record.hidden_future_beyond_simplex_rank for record in records),
        first_pair_split=pair_split[0] if pair_split else None,
        first_hidden_future_beyond_pair_split=hidden_pair[0] if hidden_pair else None,
        first_simplex_split=simplex_split[0] if simplex_split else None,
        first_hidden_future_beyond_simplex_split=hidden_simplex[0] if hidden_simplex else None,
        best_compression_record=simplex_exact_records[0] if simplex_exact_records else None,
    )


def seeded_scan(semantics: Sequence[SemanticDefinition], families: Sequence[Family]) -> Dict[str, List[AnalysisRecord]]:
    seen = set()
    deduped_families: List[Family] = []
    for family in families:
        if family in seen:
            continue
        seen.add(family)
        deduped_families.append(family)
    results: Dict[str, List[AnalysisRecord]] = {semantic.name: [] for semantic in semantics}
    for semantic in semantics:
        for family in deduped_families:
            results[semantic.name].append(analyze_family(semantic, family))
    return results


def merge_record_maps(*maps: Dict[str, List[AnalysisRecord]]) -> Dict[str, List[AnalysisRecord]]:
    merged: Dict[str, List[AnalysisRecord]] = {}
    for record_map in maps:
        for name, records in record_map.items():
            merged.setdefault(name, [])
            merged[name].extend(records)
    return merged


def run_scan(
    semantics: Sequence[SemanticDefinition],
    *,
    p_scan: Sequence[int],
    k_max: int,
    families_fn: Callable[[int, int], Sequence[Family]] = sorted_families,
) -> Dict[str, List[AnalysisRecord]]:
    results: Dict[str, List[AnalysisRecord]] = {semantic.name: [] for semantic in semantics}
    for semantic in semantics:
        for p in p_scan:
            for k in range(1, min(k_max, p) + 1):
                for family in families_fn(p, k):
                    results[semantic.name].append(analyze_family(semantic, family))
    return results


def candidate_to_json(candidate: CandidateCompressionResult) -> Dict[str, object]:
    return {
        "name": candidate.name,
        "label": candidate.label,
        "quotient_count": candidate.quotient_count,
        "exact": candidate.exact,
    }


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


def record_to_json(record: AnalysisRecord) -> Dict[str, object]:
    return {
        "semantics": record.semantics,
        "category": record.category,
        "pair_alphabet_size": record.pair_alphabet_size,
        "simplex_alphabet_size": record.simplex_alphabet_size,
        "extra_alphabet_size": record.extra_alphabet_size,
        "p": record.p,
        "k": record.k,
        "family": [list(edge) for edge in record.family],
        "reachable_state_count": record.reachable_state_count,
        "runtime_quotient_count": record.runtime_quotient_count,
        "assignment_quotient_count": record.assignment_quotient_count,
        "pair_quotient_count": record.pair_quotient_count,
        "simplex_quotient_count": record.simplex_quotient_count,
        "full_state_quotient_count": record.full_state_quotient_count,
        "output_quotient_count": record.output_quotient_count,
        "assignment_curvature_gap": record.assignment_curvature_gap,
        "pair_curvature_gap": record.pair_curvature_gap,
        "simplex_curvature_gap": record.simplex_curvature_gap,
        "compressed_simplex_gap": record.compressed_simplex_gap,
        "assignment_exact": record.assignment_exact,
        "pair_exact": record.pair_exact,
        "simplex_exact": record.simplex_exact,
        "full_state_exact": record.full_state_exact,
        "output_exact": record.output_exact,
        "assignment_holonomy_rank": record.assignment_holonomy_rank,
        "pair_holonomy_rank": record.pair_holonomy_rank,
        "simplex_holonomy_rank": record.simplex_holonomy_rank,
        "hidden_future_rank": record.hidden_future_rank,
        "hidden_future_beyond_pair_rank": record.hidden_future_beyond_pair_rank,
        "hidden_future_beyond_simplex_rank": record.hidden_future_beyond_simplex_rank,
        "assignment_witness": witness_to_json(record.assignment_witness),
        "hidden_future_witness": witness_to_json(record.hidden_future_witness),
        "pair_witness": witness_to_json(record.pair_witness),
        "hidden_future_beyond_pair_witness": witness_to_json(record.hidden_future_beyond_pair_witness),
        "simplex_witness": witness_to_json(record.simplex_witness),
        "hidden_future_beyond_simplex_witness": witness_to_json(record.hidden_future_beyond_simplex_witness),
        "explicit_compressions": [candidate_to_json(candidate) for candidate in record.explicit_compressions],
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
        "pair_split_count": summary.pair_split_count,
        "hidden_future_beyond_pair_count": summary.hidden_future_beyond_pair_count,
        "simplex_split_count": summary.simplex_split_count,
        "hidden_future_beyond_simplex_count": summary.hidden_future_beyond_simplex_count,
        "pair_exact_on_scan": summary.pair_exact_on_scan,
        "simplex_exact_on_scan": summary.simplex_exact_on_scan,
        "max_pair_curvature_gap": summary.max_pair_curvature_gap,
        "max_simplex_curvature_gap": summary.max_simplex_curvature_gap,
        "max_pair_holonomy_rank": summary.max_pair_holonomy_rank,
        "max_simplex_holonomy_rank": summary.max_simplex_holonomy_rank,
        "max_hidden_future_beyond_pair_rank": summary.max_hidden_future_beyond_pair_rank,
        "max_hidden_future_beyond_simplex_rank": summary.max_hidden_future_beyond_simplex_rank,
        "seed_record": None if summary.seed_record is None else record_to_json(summary.seed_record),
        "first_pair_split": None if summary.first_pair_split is None else record_to_json(summary.first_pair_split),
        "first_hidden_future_beyond_pair_split": None if summary.first_hidden_future_beyond_pair_split is None else record_to_json(summary.first_hidden_future_beyond_pair_split),
        "first_simplex_split": None if summary.first_simplex_split is None else record_to_json(summary.first_simplex_split),
        "first_hidden_future_beyond_simplex_split": None if summary.first_hidden_future_beyond_simplex_split is None else record_to_json(summary.first_hidden_future_beyond_simplex_split),
        "best_compression_record": None if summary.best_compression_record is None else record_to_json(summary.best_compression_record),
    }


def build_report(
    summaries: Sequence[SemanticSummary],
    payload: Dict[str, object],
    note_path: Path | None,
    compression_note_path: Path | None,
    json_path: Path,
    svg_path: Path,
) -> str:
    overall_pair = payload["overall_first_pair_split"]
    overall_hidden_pair = payload["overall_first_hidden_future_beyond_pair_split"]
    overall_simplex = payload["overall_first_simplex_split"]
    overall_hidden_simplex = payload["overall_first_hidden_future_beyond_simplex_split"]
    best_compression = payload["best_compression_record"]

    lines = [
        "# Simplex vs Global Holonomy Search",
        "",
        "## Question",
        "",
        "This search asks whether assignment plus pair plus simplex transport is already final, or whether a deterministic local law can force a hidden future beyond the simplex layer.",
        "In parallel, it searches for smaller exact quotients inside the simplex layer whenever raw simplex transport is exact but clearly non-minimal.",
        "",
        "## Scan Setup",
        "",
        "- Controls: `broadcast_control`, `committed_allocation`, `pair_phase_exclusive_other_live_block_lower`, and `pair_phase_shared_other_live_block_lower__feedback_orient_freeze_pairs`.",
        "- Extra law library: tetra-local commutator, orientation, debt, and freeze laws; plus cycle-flux, feedback-loop, and face-order parity laws.",
        f"- Base normalized scan: `p <= {max(BASE_P_SCAN)}` and `k <= {BASE_K_MAX}`.",
        f"- Expanded scan triggered: `{payload['scan']['expanded_triggered']}` on semantics `{payload['scan']['promising_semantics']}`.",
        f"- Dense overlap scan triggered: `{payload['scan']['dense_triggered']}`.",
        "- Canonical `first` order: `(p, k, |A|, pair alphabet, simplex alphabet, extra alphabet, reachable states, witness length, family, semantics)`.",
        "",
        "## Seed Families",
        "",
    ]
    for label, family in SEED_FAMILIES.items():
        lines.append(f"- `{label}` = `{family}`")
    lines.extend(["", "## Semantics Library", ""])
    for summary in summaries:
        lines.append(
            f"- `{summary.name}` (`category={summary.category}`, `|Sigma_pair|={summary.pair_alphabet_size}`, `|Sigma_simplex|={summary.simplex_alphabet_size}`, `|Sigma_extra|={summary.extra_alphabet_size}`): {summary.description}"
        )

    lines.extend(
        [
            "",
            "## Summary Table",
            "",
            "| Semantics | Kind | `|pair|` | `|simplex|` | `|extra|` | Seed counts `(runtime / pair / simplex / full)` | First pair split | First simplex split | Hidden beyond simplex | Best explicit exact compression |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    def split_label(record: AnalysisRecord | None) -> str:
        if record is None:
            return "none"
        return f"{family_badge(record.family)} @ (p={record.p}, k={record.k})"

    for summary in summaries:
        seed = summary.seed_record
        seed_counts = "n/a"
        if seed is not None:
            seed_counts = (
                f"{seed.runtime_quotient_count} / {seed.pair_quotient_count} / "
                f"{seed.simplex_quotient_count} / {seed.full_state_quotient_count}"
            )
        compression = "none"
        if summary.best_compression_record is not None and summary.best_compression_record.best_explicit_exact_label is not None:
            compression = (
                f"{summary.best_compression_record.best_explicit_exact_label} "
                f"({summary.best_compression_record.best_explicit_exact_count})"
            )
        lines.append(
            f"| `{summary.label}` | `{summary.category}` | `{summary.pair_alphabet_size}` | `{summary.simplex_alphabet_size}` | `{summary.extra_alphabet_size}` | `{seed_counts}` | `{split_label(summary.first_pair_split)}` | `{split_label(summary.first_simplex_split)}` | `{split_label(summary.first_hidden_future_beyond_simplex_split)}` | `{compression}` |"
        )

    lines.extend(["", "## Boundary Results", ""])
    if overall_pair is None:
        lines.append("- No pair-insufficient split appeared in this scan.")
    else:
        lines.append(
            f"- First pair-insufficient split: `{overall_pair['semantics']}` on `{tuple(tuple(edge) for edge in overall_pair['family'])}` at `(p={overall_pair['p']}, k={overall_pair['k']})`."
        )
    if overall_hidden_pair is None:
        lines.append("- No hidden future beyond pair transport appeared in this scan.")
    else:
        lines.append(
            f"- First hidden future beyond pair: `{overall_hidden_pair['semantics']}` on `{tuple(tuple(edge) for edge in overall_hidden_pair['family'])}` at `(p={overall_hidden_pair['p']}, k={overall_hidden_pair['k']})`."
        )
    if overall_simplex is None:
        lines.append("- No simplex-insufficient split was found on the tested law library and scan range.")
    else:
        lines.append(
            f"- First simplex-insufficient split: `{overall_simplex['semantics']}` on `{tuple(tuple(edge) for edge in overall_simplex['family'])}` at `(p={overall_simplex['p']}, k={overall_simplex['k']})`, with simplex gap `{overall_simplex['simplex_curvature_gap']:.3f}` bits."
        )
    if overall_hidden_simplex is None:
        lines.append("- No hidden-future-beyond-simplex witness was found.")
    else:
        lines.append(
            f"- First hidden future beyond simplex: `{overall_hidden_simplex['semantics']}` on `{tuple(tuple(edge) for edge in overall_hidden_simplex['family'])}` at `(p={overall_hidden_simplex['p']}, k={overall_hidden_simplex['k']})`."
        )

    lines.extend(["", "## First Simplex-Insufficient Split", ""])
    if overall_simplex is None:
        strongest = max(
            summaries,
            key=lambda summary: (
                summary.max_hidden_future_beyond_simplex_rank,
                summary.max_simplex_holonomy_rank,
                summary.max_simplex_curvature_gap,
            ),
        )
        lines.extend(
            [
                "No semantics broke assignment plus pair plus simplex exactness on the tested library.",
                f"The strongest near-miss was `{strongest.name}` with `max simplex holonomy rank = {strongest.max_simplex_holonomy_rank}` and `max hidden-future-beyond-simplex rank = {strongest.max_hidden_future_beyond_simplex_rank}`.",
                "On the tested law library and scan range, assignment + pair + simplex transport is exact.",
            ]
        )
    else:
        witness = overall_simplex["simplex_witness"]
        family = tuple(tuple(edge) for edge in overall_simplex["family"])
        lines.extend(
            [
                f"- semantics: `{overall_simplex['semantics']}`",
                f"- family: `{family}`",
                f"- counts: runtime `{overall_simplex['runtime_quotient_count']}`, pair `{overall_simplex['pair_quotient_count']}`, simplex `{overall_simplex['simplex_quotient_count']}`, full state `{overall_simplex['full_state_quotient_count']}`",
                f"- same assignment+pair+simplex witness `u`: `{trace_text(tuple(witness['left_trace']) if witness and witness['left_trace'] else (), family) if witness else '[]'}`",
                f"- same assignment+pair+simplex witness `v`: `{trace_text(tuple(witness['right_trace']) if witness and witness['right_trace'] else (), family) if witness else '[]'}`",
                f"- suffix `w`: `{trace_text(tuple(witness['suffix']) if witness and witness['suffix'] else (), family) if witness else '[]'}`",
                f"- shared simplex fiber: `{witness['summary_value'] if witness else 'n/a'}`",
                f"- current outputs: `{witness['left_output_now'] if witness else 'n/a'}` versus `{witness['right_output_now'] if witness else 'n/a'}`",
                f"- future outputs: `{witness['left_output_future'] if witness else 'n/a'}` versus `{witness['right_output_future'] if witness else 'n/a'}`",
            ]
        )

    lines.extend(["", "## First Hidden Future Beyond Simplex", ""])
    if overall_hidden_simplex is None:
        lines.append("No same-now / future-separate witness beyond the simplex layer appeared on the tested library.")
    else:
        witness = overall_hidden_simplex["hidden_future_beyond_simplex_witness"]
        family = tuple(tuple(edge) for edge in overall_hidden_simplex["family"])
        lines.extend(
            [
                f"- semantics: `{overall_hidden_simplex['semantics']}`",
                f"- family: `{family}`",
                f"- left prefix `u`: `{trace_text(tuple(witness['left_trace']) if witness and witness['left_trace'] else (), family) if witness else '[]'}`",
                f"- right prefix `v`: `{trace_text(tuple(witness['right_trace']) if witness and witness['right_trace'] else (), family) if witness else '[]'}`",
                f"- shared simplex fiber: `{witness['summary_value'] if witness else 'n/a'}`",
                f"- shared current output: `{witness['left_output_now'] if witness else 'n/a'}`",
                f"- non-empty suffix `w`: `{trace_text(tuple(witness['suffix']) if witness and witness['suffix'] else (), family) if witness else '[]'}`",
                f"- future outputs after `w`: `{witness['left_output_future'] if witness else 'n/a'}` versus `{witness['right_output_future'] if witness else 'n/a'}`",
            ]
        )

    lines.extend(["", "## Best Compression Inside the Simplex Layer", ""])
    if best_compression is None:
        lines.append("No simplex-exact semantics produced an interpretable exact compression candidate beyond the raw simplex summary.")
    else:
        lines.extend(
            [
                f"- semantics: `{best_compression['semantics']}`",
                f"- family: `{tuple(tuple(edge) for edge in best_compression['family'])}`",
                f"- raw simplex quotient count: `{best_compression['simplex_quotient_count']}`",
                f"- runtime quotient count: `{best_compression['runtime_quotient_count']}`",
                f"- best explicit exact compression: `{best_compression['best_explicit_exact_label']}` with quotient count `{best_compression['best_explicit_exact_count']}`",
                f"- compressed simplex gap: `{best_compression['compressed_simplex_gap']:.3f}` bits" if best_compression["compressed_simplex_gap"] is not None else "- compressed simplex gap: `n/a`",
            ]
        )

    lines.extend(["", "## Interpretation", ""])
    if overall_simplex is None:
        lines.append("On the tested law library and scan range, assignment + pair + simplex transport is exact.")
    else:
        lines.append("The simplex layer is not final on the tested law library: a hidden future survives inside a fixed assignment-plus-pair-plus-simplex fiber.")
    if overall_hidden_simplex is not None:
        lines.append("The winning witness is a true hidden future beyond simplex transport: the current output and the full simplex fiber agree, but a non-empty common suffix still separates the futures.")
    if best_compression is not None:
        lines.append("At the same time, the raw simplex carrier is not canonical: even where it is exact, a smaller exact quotient exists inside the simplex layer.")

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
        lines.append(f"- Boundary note: [{note_path.name}](../../../docs/writing/experiments/holonomy/{note_path.name})")
    if compression_note_path is not None:
        lines.append(f"- Compression note: [{compression_note_path.name}](../../../docs/writing/experiments/holonomy/{compression_note_path.name})")
    return "\n".join(lines) + "\n"


def render_svg(summaries: Sequence[SemanticSummary], payload: Dict[str, object]) -> str:
    width = 1640
    left = 40
    top = 84
    table_width = width - 2 * left
    row_height = 36
    card_gap = 16
    overall_simplex = payload["overall_first_simplex_split"]
    overall_hidden_simplex = payload["overall_first_hidden_future_beyond_simplex_split"]
    best_compression = payload["best_compression_record"]

    table_y = top + 154
    table_height = 78 + row_height * len(summaries)
    bottom_y = table_y + table_height + 22
    witness_height = 338
    footer_y = bottom_y + witness_height + 24
    height = footer_y + 50

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
        ".metric { font-size: 30px; font-weight: 700; fill: #0f172a; }",
        ".small { font-size: 12px; fill: #52606d; }",
        ".cell { font-size: 12px; fill: #102a43; }",
        ".mono { font-family: 'SFMono-Regular', Menlo, Monaco, Consolas, monospace; font-size: 12px; fill: #102a43; }",
        ".control-row { fill: #f4f7f9; }",
        ".pair-row { fill: #eff6ff; }",
        ".simplex-row { fill: #f7efff; }",
        ".global-row { fill: #eefbf3; }",
        ".divider { stroke: #e5e7eb; stroke-width: 1; }",
        ".chip-flat { fill: #f1f5f9; stroke: #cbd2d9; stroke-width: 1; }",
        ".chip-pair { fill: #dbeafe; stroke: #93c5fd; stroke-width: 1; }",
        ".chip-simplex { fill: #ede9fe; stroke: #c4b5fd; stroke-width: 1; }",
        ".chip-global { fill: #dcfce7; stroke: #86efac; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f7fafc"/>',
        f'<text x="{left}" y="40" class="title">Simplex vs Global Holonomy Search</text>',
        f'<text x="{left}" y="64" class="subtitle">Does a hidden future survive beyond assignment + pair + simplex transport, and if not, how much of the simplex layer can be compressed exactly?</text>',
    ]

    card_width = (table_width - 2 * card_gap) / 3
    card_y = top
    card_height = 126
    for idx in range(3):
        x = left + idx * (card_width + card_gap)
        lines.append(f'<rect x="{x}" y="{card_y}" width="{card_width}" height="{card_height}" class="card"/>')

    lines.extend(
        [
            f'<text x="{left + 18}" y="{card_y + 26}" class="header">Scan</text>',
            f'<text x="{left + 18}" y="{card_y + 60}" class="metric">{summaries[0].families_scanned if summaries else 0}</text>',
            f'<text x="{left + 100}" y="{card_y + 60}" class="section">families per semantics</text>',
            f'<text x="{left + 18}" y="{card_y + 86}" class="small">Base grid: p in {tuple(BASE_P_SCAN)}, k ≤ {BASE_K_MAX}. Expanded pass: {payload["scan"]["expanded_triggered"]}. Dense pass: {payload["scan"]["dense_triggered"]}.</text>',
            f'<text x="{left + 18}" y="{card_y + 108}" class="small">{len(summaries)} semantics = 4 controls plus {len(EXTRA_SPECS)} tetra/global laws.</text>',
        ]
    )

    boundary_x = left + card_width + card_gap + 18
    if overall_simplex is None:
        boundary_title = "No simplex split"
        boundary_line_1 = "Assignment + pair + simplex stayed exact on the tested library."
        boundary_line_2 = "The strongest action moved to compression, not a new boundary."
    else:
        boundary_title = "First simplex split"
        boundary_line_1 = (
            f'{overall_simplex["semantics"]} on {family_badge(tuple(tuple(edge) for edge in overall_simplex["family"]))} '
            f'@ (p={overall_simplex["p"]}, k={overall_simplex["k"]})'
        )
        boundary_line_2 = (
            f'counts = {overall_simplex["runtime_quotient_count"]} / {overall_simplex["pair_quotient_count"]} / '
            f'{overall_simplex["simplex_quotient_count"]} / {overall_simplex["full_state_quotient_count"]}'
        )
    lines.extend(
        [
            f'<text x="{boundary_x}" y="{card_y + 26}" class="header">Boundary</text>',
            f'<text x="{boundary_x}" y="{card_y + 54}" class="section">{boundary_title}</text>',
            f'<text x="{boundary_x}" y="{card_y + 82}" class="small">{boundary_line_1}</text>',
            f'<text x="{boundary_x}" y="{card_y + 104}" class="small">{boundary_line_2}</text>',
        ]
    )

    comp_x = left + 2 * (card_width + card_gap) + 18
    if best_compression is None:
        comp_title = "No explicit compression"
        comp_line_1 = "None of the scanned simplex-exact cases produced an interpretable explicit quotient smaller than raw simplex transport."
        comp_line_2 = "The Moore quotient still certifies non-minimality whenever runtime < simplex."
    else:
        comp_title = "Best simplex compression"
        comp_line_1 = (
            f'{best_compression["semantics"]} on {family_badge(tuple(tuple(edge) for edge in best_compression["family"]))}: '
            f'{best_compression["best_explicit_exact_label"]} = {best_compression["best_explicit_exact_count"]}'
        )
        comp_line_2 = (
            f'raw simplex = {best_compression["simplex_quotient_count"]}, runtime = '
            f'{best_compression["runtime_quotient_count"]}'
        )
    lines.extend(
        [
            f'<text x="{comp_x}" y="{card_y + 26}" class="header">Compression</text>',
            f'<text x="{comp_x}" y="{card_y + 54}" class="section">{comp_title}</text>',
            f'<text x="{comp_x}" y="{card_y + 82}" class="small">{comp_line_1}</text>',
            f'<text x="{comp_x}" y="{card_y + 104}" class="small">{comp_line_2}</text>',
        ]
    )

    lines.append(f'<rect x="{left}" y="{table_y}" width="{table_width}" height="{table_height}" class="panel"/>')
    lines.append(f'<text x="{left + 18}" y="{table_y + 26}" class="header">Semantic Library</text>')
    lines.append(f'<text x="{left + 18}" y="{table_y + 50}" class="small">Seed counts are runtime / pair / simplex / full. The last column shows the smallest explicit exact quotient discovered inside the simplex layer.</text>')

    columns = {
        "sem": left + 20,
        "kind": left + 410,
        "tokens": left + 545,
        "seed": left + 680,
        "pair": left + 860,
        "simplex": left + 1035,
        "hidden": left + 1215,
        "compression": left + 1385,
    }
    header_y = table_y + 82
    for key, label in (
        ("sem", "Semantics"),
        ("kind", "Kind"),
        ("tokens", "|pair| / |simplex| / |extra|"),
        ("seed", "Seed q"),
        ("pair", "Pair split"),
        ("simplex", "Simplex split"),
        ("hidden", "Hidden beyond simplex"),
        ("compression", "Exact compression"),
    ):
        lines.append(f'<text x="{columns[key]}" y="{header_y}" class="header">{label}</text>')
    lines.append(
        f'<line x1="{left + 18}" y1="{header_y + 10}" x2="{left + table_width - 18}" y2="{header_y + 10}" class="divider"/>'
    )

    def status_chip(summary: SemanticSummary) -> Tuple[str, str]:
        if summary.first_hidden_future_beyond_simplex_split is not None:
            return "hidden future", "chip-global"
        if summary.first_simplex_split is not None:
            return "simplex split", "chip-simplex"
        if summary.first_pair_split is not None:
            return "pair split", "chip-pair"
        return "flat", "chip-flat"

    for index, summary in enumerate(summaries):
        y = header_y + 34 + index * row_height
        status, chip_class = status_chip(summary)
        if summary.category == "control":
            row_class = "control-row"
        elif summary.first_hidden_future_beyond_simplex_split is not None:
            row_class = "global-row"
        elif summary.first_simplex_split is not None:
            row_class = "simplex-row"
        else:
            row_class = "pair-row"
        lines.append(f'<rect x="{left + 12}" y="{y - 18}" width="{table_width - 24}" height="28" rx="12" ry="12" class="{row_class}"/>')
        seed = summary.seed_record
        seed_text = "n/a"
        if seed is not None:
            seed_text = (
                f"{seed.runtime_quotient_count} / {seed.pair_quotient_count} / "
                f"{seed.simplex_quotient_count} / {seed.full_state_quotient_count}"
            )
        compression = "none"
        if summary.best_compression_record is not None and summary.best_compression_record.best_explicit_exact_label is not None:
            compression = f'{summary.best_compression_record.best_explicit_exact_label} ({summary.best_compression_record.best_explicit_exact_count})'
        lines.extend(
            [
                f'<text x="{columns["sem"]}" y="{y}" class="cell">{summary.label}</text>',
                f'<text x="{columns["kind"]}" y="{y}" class="cell">{summary.category}</text>',
                f'<text x="{columns["tokens"]}" y="{y}" class="cell">{summary.pair_alphabet_size} / {summary.simplex_alphabet_size} / {summary.extra_alphabet_size}</text>',
                f'<text x="{columns["seed"]}" y="{y}" class="mono">{seed_text}</text>',
                f'<text x="{columns["pair"]}" y="{y}" class="cell">{family_badge(summary.first_pair_split.family) if summary.first_pair_split else "none"}</text>',
                f'<text x="{columns["simplex"]}" y="{y}" class="cell">{family_badge(summary.first_simplex_split.family) if summary.first_simplex_split else "none"}</text>',
                f'<text x="{columns["hidden"]}" y="{y}" class="cell">{family_badge(summary.first_hidden_future_beyond_simplex_split.family) if summary.first_hidden_future_beyond_simplex_split else "none"}</text>',
                f'<text x="{columns["compression"]}" y="{y}" class="cell">{compression}</text>',
            ]
        )
        chip_x = left + table_width - 140
        lines.append(f'<rect x="{chip_x}" y="{y - 15}" width="112" height="22" rx="11" ry="11" class="{chip_class}"/>')
        lines.append(f'<text x="{chip_x + 12}" y="{y}" class="cell">{status}</text>')

    card_width = (table_width - card_gap) / 2
    for idx in range(2):
        x = left + idx * (card_width + card_gap)
        lines.append(f'<rect x="{x}" y="{bottom_y}" width="{card_width}" height="{witness_height}" class="card"/>')

    left_card_x = left + 18
    lines.append(f'<text x="{left_card_x}" y="{bottom_y + 28}" class="header">Simplex Boundary Witness</text>')
    if overall_hidden_simplex is None:
        lines.append(f'<text x="{left_card_x}" y="{bottom_y + 58}" class="small">No hidden future beyond simplex transport appeared on the tested library.</text>')
    else:
        witness = overall_hidden_simplex["hidden_future_beyond_simplex_witness"]
        family = tuple(tuple(edge) for edge in overall_hidden_simplex["family"])
        lines.extend(
            [
                f'<text x="{left_card_x}" y="{bottom_y + 58}" class="section">{overall_hidden_simplex["semantics"]}</text>',
                f'<text x="{left_card_x}" y="{bottom_y + 82}" class="small">{family_badge(family)} family at (p={overall_hidden_simplex["p"]}, k={overall_hidden_simplex["k"]}). This is the first witness where the full simplex fiber and current output agree but the future still remembers more.</text>',
                f'<text x="{left_card_x}" y="{bottom_y + 118}" class="mono">u = {trace_text(tuple(witness["left_trace"]) if witness and witness["left_trace"] else (), family) if witness else "[]"}</text>',
                f'<text x="{left_card_x}" y="{bottom_y + 142}" class="mono">v = {trace_text(tuple(witness["right_trace"]) if witness and witness["right_trace"] else (), family) if witness else "[]"}</text>',
                f'<text x="{left_card_x}" y="{bottom_y + 166}" class="mono">w = {trace_text(tuple(witness["suffix"]) if witness and witness["suffix"] else (), family) if witness else "[]"}</text>',
                f'<text x="{left_card_x}" y="{bottom_y + 200}" class="small">Shared simplex fiber: {witness["summary_value"] if witness else "n/a"}</text>',
                f'<text x="{left_card_x}" y="{bottom_y + 224}" class="small">Shared current output: {witness["left_output_now"] if witness else "n/a"}</text>',
                f'<text x="{left_card_x}" y="{bottom_y + 248}" class="small">Future outputs after non-empty w: {witness["left_output_future"] if witness else "n/a"} vs {witness["right_output_future"] if witness else "n/a"}</text>',
            ]
        )

    right_card_x = left + card_width + card_gap + 18
    lines.append(f'<text x="{right_card_x}" y="{bottom_y + 28}" class="header">Best Explicit Compression</text>')
    if best_compression is None:
        lines.append(f'<text x="{right_card_x}" y="{bottom_y + 58}" class="small">No explicit candidate beat the raw simplex summary on the tested simplex-exact cases.</text>')
    else:
        family = tuple(tuple(edge) for edge in best_compression["family"])
        lines.extend(
            [
                f'<text x="{right_card_x}" y="{bottom_y + 58}" class="section">{best_compression["semantics"]}</text>',
                f'<text x="{right_card_x}" y="{bottom_y + 82}" class="small">{family_badge(family)} family; best explicit exact quotient = {best_compression["best_explicit_exact_label"]} ({best_compression["best_explicit_exact_count"]}).</text>',
                f'<text x="{right_card_x}" y="{bottom_y + 118}" class="small">Runtime quotient: {best_compression["runtime_quotient_count"]}</text>',
                f'<text x="{right_card_x}" y="{bottom_y + 142}" class="small">Raw simplex quotient: {best_compression["simplex_quotient_count"]}</text>',
                f'<text x="{right_card_x}" y="{bottom_y + 166}" class="small">Compressed gap: {best_compression["compressed_simplex_gap"]:.3f}</text>' if best_compression["compressed_simplex_gap"] is not None else f'<text x="{right_card_x}" y="{bottom_y + 166}" class="small">Compressed gap: n/a</text>',
            ]
        )
        y = bottom_y + 210
        for candidate in best_compression["explicit_compressions"]:
            lines.append(
                f'<text x="{right_card_x}" y="{y}" class="small">{candidate["label"]}: count {candidate["quotient_count"]}, exact = {candidate["exact"]}</text>'
            )
            y += 22

    canonical_order = "p, k, family_count, pair_alphabet_size, simplex_alphabet_size, extra_alphabet_size, reachable_state_count, witness_length, family, semantics"
    lines.extend(
        [
            f'<text x="{left}" y="{footer_y}" class="small">Canonical first-order for ties: {canonical_order}.</text>',
            f'<text x="{left}" y="{footer_y + 22}" class="small">Reading: pair-only controls stop at assignment curvature, simplex transport fixes the triangle boundary, and the new question is whether tetra/global tokens create a genuinely deeper hidden future or whether simplex transport merely needs compression.</text>',
        ]
    )
    lines.append("</svg>")
    return "\n".join(lines)


def build_note(payload: Dict[str, object]) -> str:
    overall_simplex = payload["overall_first_simplex_split"]
    overall_hidden_simplex = payload["overall_first_hidden_future_beyond_simplex_split"]
    if overall_simplex is None:
        lines = [
            "# Simplex Holonomy Sufficiency",
            "",
            "## Thesis",
            "",
            "On the tested tetra-local and cycle-local law library and scan range, assignment plus pair plus simplex transport is exact.",
            "",
            "## Boundary",
            "",
            "- No same-assignment-plus-pair-plus-simplex continuation split appeared on the tested families.",
            "- No hidden future beyond the simplex layer appeared under a non-empty common suffix.",
            "",
            "## Open Seam",
            "",
            "The next exact target is no longer whether simplex transport can fail on these local laws. It is whether a larger local carrier or a more global composition law can force a genuinely deeper holonomy layer.",
            "",
        ]
        return "\n".join(lines)
    lines = [
        "# Global Holonomy Boundary",
        "",
        "## Thesis",
        "",
        "This search crosses the next boundary: assignment plus pair plus simplex transport is not final.",
        "",
        "## Exact Boundary",
        "",
        f"- First simplex-insufficient split: `{overall_simplex['semantics']}` on `{tuple(tuple(edge) for edge in overall_simplex['family'])}`.",
        f"- Token sizes: `|Sigma_pair| = {overall_simplex['pair_alphabet_size']}`, `|Sigma_simplex| = {overall_simplex['simplex_alphabet_size']}`, and `|Sigma_extra| = {overall_simplex['extra_alphabet_size']}`.",
        f"- Counts: runtime `{overall_simplex['runtime_quotient_count']}`, simplex `{overall_simplex['simplex_quotient_count']}`, full state `{overall_simplex['full_state_quotient_count']}`.",
        f"- Simplex gap: `{overall_simplex['simplex_curvature_gap']:.3f}` bits.",
    ]
    if overall_hidden_simplex is not None:
        lines.extend(
            [
                "",
                "## Hidden Future Beyond Simplex",
                "",
                f"- First hidden-future-beyond-simplex split: `{overall_hidden_simplex['semantics']}` on `{tuple(tuple(edge) for edge in overall_hidden_simplex['family'])}`.",
                "- The future remembers a transport token that both the full simplex fiber and the current readout erase.",
            ]
        )
    lines.extend(
        [
            "",
            "## Open Seam",
            "",
            "The next exact target is no longer whether simplex transport can fail. It is whether the new exact object is tetra transport, cycle holonomy, or something still more global.",
            "",
        ]
    )
    return "\n".join(lines)


def build_compression_note(payload: Dict[str, object]) -> str | None:
    best_compression = payload["best_compression_record"]
    if best_compression is None:
        return None
    lines = [
        "# Simplex Quotient Compression",
        "",
        "## Thesis",
        "",
        "Even where assignment plus pair plus simplex transport is exact, the raw simplex carrier is not canonical. A smaller exact quotient exists inside the simplex layer.",
        "",
        "## Best Exact Compression",
        "",
        f"- semantics: `{best_compression['semantics']}`",
        f"- family: `{tuple(tuple(edge) for edge in best_compression['family'])}`",
        f"- raw simplex quotient count: `{best_compression['simplex_quotient_count']}`",
        f"- runtime quotient count: `{best_compression['runtime_quotient_count']}`",
        f"- best explicit exact quotient: `{best_compression['best_explicit_exact_label']}` with count `{best_compression['best_explicit_exact_count']}`",
        "",
        "## Interpretation",
        "",
        "The raw simplex tokenization is an exact carrier, but not the final quotient. Continuation minimization exposes a smaller exact object, and explicit summary projectors can sometimes approximate it cleanly.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    base_records = seeded_scan(SEMANTICS, SEED_FAMILY_ORDER)
    normalized_records = run_scan(SEMANTICS, p_scan=BASE_P_SCAN, k_max=BASE_K_MAX)
    all_records = merge_record_maps(base_records, normalized_records)

    summaries = [summarize_semantic(semantic, all_records[semantic.name]) for semantic in SEMANTICS]
    simplex_candidates = [summary.first_simplex_split for summary in summaries if summary.first_simplex_split is not None]

    promising_semantics = [
        semantic
        for semantic, summary in zip(SEMANTICS, summaries)
        if summary.first_simplex_split is not None
        or summary.max_hidden_future_beyond_simplex_rank > 1
        or summary.max_simplex_holonomy_rank > 1
    ]
    expanded_triggered = False
    if not simplex_candidates and promising_semantics:
        expanded_triggered = True
        expanded_seed_records = seeded_scan(promising_semantics, (FOUR_EDGE_STAR,))
        expanded_records = run_scan(promising_semantics, p_scan=EXPANDED_P_SCAN, k_max=EXPANDED_K_MAX)
        for semantic in promising_semantics:
            all_records[semantic.name].extend(expanded_seed_records[semantic.name])
            all_records[semantic.name].extend(expanded_records[semantic.name])

    summaries = [summarize_semantic(semantic, all_records[semantic.name]) for semantic in SEMANTICS]

    simplex_candidates = [summary.first_simplex_split for summary in summaries if summary.first_simplex_split is not None]
    hidden_simplex_candidates = [
        summary.first_hidden_future_beyond_simplex_split
        for summary in summaries
        if summary.first_hidden_future_beyond_simplex_split is not None
    ]
    pair_candidates = [summary.first_pair_split for summary in summaries if summary.first_pair_split is not None]
    hidden_pair_candidates = [
        summary.first_hidden_future_beyond_pair_split
        for summary in summaries
        if summary.first_hidden_future_beyond_pair_split is not None
    ]
    if simplex_candidates:
        simplex_candidates.sort(key=lambda record: witness_key(record, "simplex"))
    if hidden_simplex_candidates:
        hidden_simplex_candidates.sort(key=lambda record: witness_key(record, "hidden_simplex"))
    if pair_candidates:
        pair_candidates.sort(key=lambda record: witness_key(record, "pair"))
    if hidden_pair_candidates:
        hidden_pair_candidates.sort(key=lambda record: witness_key(record, "hidden_pair"))

    dense_triggered = False
    if not simplex_candidates:
        dense_semantics = tuple(
            semantic
            for semantic, summary in zip(SEMANTICS, summaries)
            if summary.max_simplex_holonomy_rank > 1 or summary.max_hidden_future_beyond_simplex_rank > 1
        )
        if dense_semantics:
            dense_triggered = True
            dense_records = run_scan(dense_semantics, p_scan=DENSE_P_SCAN, k_max=DENSE_K_MAX, families_fn=dense_overlap_families)
            for semantic in dense_semantics:
                all_records[semantic.name].extend(dense_records[semantic.name])
            summaries = [summarize_semantic(semantic, all_records[semantic.name]) for semantic in SEMANTICS]
            simplex_candidates = [summary.first_simplex_split for summary in summaries if summary.first_simplex_split is not None]
            hidden_simplex_candidates = [
                summary.first_hidden_future_beyond_simplex_split
                for summary in summaries
                if summary.first_hidden_future_beyond_simplex_split is not None
            ]
            if simplex_candidates:
                simplex_candidates.sort(key=lambda record: witness_key(record, "simplex"))
            if hidden_simplex_candidates:
                hidden_simplex_candidates.sort(key=lambda record: witness_key(record, "hidden_simplex"))

    compression_records = [
        summary.best_compression_record
        for summary in summaries
        if summary.best_compression_record is not None
        and summary.best_compression_record.best_explicit_exact_count is not None
        and summary.best_compression_record.simplex_alphabet_size > 1
        and summary.best_compression_record.simplex_quotient_count > summary.best_compression_record.best_explicit_exact_count
    ]
    compression_records.sort(
        key=lambda record: (
            -(record.simplex_quotient_count - (record.best_explicit_exact_count or 0)),
            record.best_explicit_exact_count if record.best_explicit_exact_count is not None else 10**9,
            record.simplex_quotient_count,
            record.p,
            record.k,
            len(record.family),
            record.semantics,
        )
    )

    json_path = RESULTS_DIR / "simplex_vs_global_holonomy_search.json"
    report_path = RESULTS_DIR / "simplex_vs_global_holonomy_search.md"
    svg_path = RESULTS_DIR / "simplex_vs_global_holonomy_search.svg"
    note_path = DOCS_DIR / ("global-holonomy-boundary.md" if simplex_candidates else "simplex-holonomy-sufficiency.md")
    compression_note_path = DOCS_DIR / "simplex-quotient-compression.md"
    note_candidates = ("global-holonomy-boundary.md", "simplex-holonomy-sufficiency.md")

    payload = {
        "scan": {
            "base_p_scan": list(BASE_P_SCAN),
            "base_k_max": BASE_K_MAX,
            "expanded_p_scan": list(EXPANDED_P_SCAN),
            "expanded_k_max": EXPANDED_K_MAX,
            "expanded_triggered": expanded_triggered,
            "promising_semantics": [semantic.name for semantic in promising_semantics],
            "dense_p_scan": list(DENSE_P_SCAN),
            "dense_k_max": DENSE_K_MAX,
            "dense_triggered": dense_triggered,
            "seed_families": {name: [list(edge) for edge in family] for name, family in SEED_FAMILIES.items()},
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
        },
        "semantics": [summary_to_json(summary) for summary in summaries],
        "records": {semantic.name: [record_to_json(record) for record in all_records[semantic.name]] for semantic in SEMANTICS},
        "overall_first_pair_split": None if not pair_candidates else record_to_json(pair_candidates[0]),
        "overall_first_hidden_future_beyond_pair_split": None if not hidden_pair_candidates else record_to_json(hidden_pair_candidates[0]),
        "overall_first_simplex_split": None if not simplex_candidates else record_to_json(simplex_candidates[0]),
        "overall_first_hidden_future_beyond_simplex_split": None if not hidden_simplex_candidates else record_to_json(hidden_simplex_candidates[0]),
        "best_compression_record": None if not compression_records else record_to_json(compression_records[0]),
    }
    json_path.write_text(json.dumps(payload, indent=2))

    for stale_name in note_candidates:
        stale_path = DOCS_DIR / stale_name
        if stale_path.is_symlink():
            stale_path.unlink()
    if compression_note_path.is_symlink():
        compression_note_path.unlink()

    note_path.write_text(build_note(payload))
    compression_note_text = build_compression_note(payload)
    if compression_note_text is not None:
        compression_note_path.write_text(compression_note_text)
    elif compression_note_path.exists():
        compression_note_path.unlink()

    report_path.write_text(build_report(summaries, payload, note_path, compression_note_path if compression_note_text is not None else None, json_path, svg_path))
    svg_path.write_text(render_svg(summaries, payload))

    print(f"Wrote {report_path}")
    print(f"Wrote {json_path}")
    print(f"Wrote {svg_path}")
    print(f"Wrote {note_path}")
    if compression_note_text is not None:
        print(f"Wrote {compression_note_path}")


if __name__ == "__main__":
    main()
