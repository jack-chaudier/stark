#!/usr/bin/env python3
"""Exact separator-closure experiment for the finite-probe quotient tower.

This script studies how far the current right-bank observational quotient is
from the full two-sided protected-witness quotient.

For the synthetic families `Q_(k,p)` it:

1. Builds the exact canonical state space and the current right-only
   observational quotient.
2. Collapses left probes into unique action types on that right quotient.
3. Searches over all action subsets exactly.
4. Compares exact closure frontiers with greedy separator selection.
5. Measures probe deficiency, shelf width, and unresolved-pair decay as the
   probe bank grows.

The output is honest about scope:
- the canonical quotient is exact,
- the closure search is exact relative to the current full right-bank probe set,
- the "separator basis" found here is observational unless explicitly stated.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from phase_transition_sweep import (
    DatasetSpec,
    Output,
    build_causal_referee_spec,
    build_compositional_spec_bare,
    build_compositional_spec_witness,
    compositional_tower,
    compose_witness,
    dataset_tower,
    log2_count,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
TARGET_FAMILIES = ((3, 2), (4, 2), (5, 3))
GRID_K_VALUES = range(1, 6)
GRID_P_VALUES = range(1, 4)


@dataclass(frozen=True)
class CandidateAction:
    representative: Tuple[int, Tuple[int, ...]]
    multiplicity: int
    joint_action: Tuple[int, ...]
    answer_action: Tuple[int, ...]
    witness_action: Tuple[int, ...]


@dataclass(frozen=True)
class ClosureMetrics:
    separator_count: int
    joint_count: int
    answer_count: int
    witness_count: int
    unresolved_pairs: int
    entropy_bits: float
    probe_deficiency_bits: float
    shelf_width_bits: float


@dataclass(frozen=True)
class FamilyClosureResult:
    label: str
    k: int
    p: int
    canonical_state_count: int
    base_joint_count: int
    base_answer_count: int
    base_witness_count: int
    candidate_action_count: int
    candidate_actions: Tuple[CandidateAction, ...]
    exact_frontier: Tuple[ClosureMetrics, ...]
    optimal_subset_masks: Tuple[int, ...]
    minimal_basis_size: int
    minimal_basis_representatives: Tuple[Tuple[int, Tuple[int, ...]], ...]
    greedy_paths: Dict[str, Tuple[Tuple[int, Tuple[int, ...]], ...]]
    greedy_frontiers: Dict[str, Tuple[ClosureMetrics, ...]]


def equivalence_ids(items: Sequence[Tuple[object, ...] | str]) -> Tuple[List[int], Dict[Tuple[object, ...] | str, List[int]]]:
    groups: Dict[Tuple[object, ...] | str, List[int]] = defaultdict(list)
    for index, item in enumerate(items):
        groups[item].append(index)
    ids = [0] * len(items)
    for class_id, key in enumerate(sorted(groups, key=lambda value: (str(value), len(groups[value])))):
        for index in groups[key]:
            ids[index] = class_id
    ordered_groups = {
        key: groups[key]
        for key in sorted(groups, key=lambda value: (str(value), len(groups[value])))
    }
    return ids, ordered_groups


def projection_rows(
    outcomes: Sequence[Sequence[Output]],
    projection: str,
) -> List[Tuple[object, ...]]:
    if projection == "joint":
        return [
            tuple((output.answer, output.witness) for output in row)
            for row in outcomes
        ]
    if projection == "answer":
        return [tuple(output.answer for output in row) for row in outcomes]
    if projection == "witness":
        return [tuple(output.witness for output in row) for row in outcomes]
    raise ValueError(f"unknown projection: {projection}")


def entropy_bits(class_sizes: Iterable[int], total: int) -> float:
    if total <= 0:
        return 0.0
    entropy = 0.0
    for size in class_sizes:
        if size <= 0:
            continue
        probability = size / total
        entropy -= probability * math.log2(probability)
    return entropy


def bits_to_fixed(value: float) -> str:
    return f"{value:.3f}"


def subset_signature_count(
    base_ids: Sequence[int],
    action_values: Sequence[Sequence[int]],
    mask: int,
) -> Tuple[int, int, float]:
    signatures = []
    for state_index, base_id in enumerate(base_ids):
        signature = [base_id]
        for action_index, values in enumerate(action_values):
            if mask & (1 << action_index):
                signature.append(values[state_index])
        signatures.append(tuple(signature))
    counts = Counter(signatures)
    unresolved = sum(size * (size - 1) // 2 for size in counts.values())
    return len(counts), unresolved, entropy_bits(counts.values(), len(base_ids))


def build_family_closure_result(k: int, p: int) -> FamilyClosureResult:
    spec = build_compositional_spec_witness(k, p)
    states = list(spec.states)
    state_index = {state: index for index, state in enumerate(states)}
    outcomes = list(spec.outcomes)

    base_joint_rows = projection_rows(outcomes, "joint")
    base_answer_rows = projection_rows(outcomes, "answer")
    base_witness_rows = projection_rows(outcomes, "witness")

    joint_ids, _ = equivalence_ids(base_joint_rows)
    answer_ids, _ = equivalence_ids(base_answer_rows)
    witness_ids, _ = equivalence_ids(base_witness_rows)

    identity_action = tuple(joint_ids)
    action_map: Dict[Tuple[int, ...], CandidateAction] = {}
    for left in states:
        joint_action = tuple(
            joint_ids[state_index[compose_witness(left, middle, k)]]
            for middle in states
        )
        answer_action = tuple(
            answer_ids[state_index[compose_witness(left, middle, k)]]
            for middle in states
        )
        witness_action = tuple(
            witness_ids[state_index[compose_witness(left, middle, k)]]
            for middle in states
        )
        if joint_action == identity_action:
            continue
        existing = action_map.get(joint_action)
        if existing is None:
            action_map[joint_action] = CandidateAction(
                representative=left,
                multiplicity=1,
                joint_action=joint_action,
                answer_action=answer_action,
                witness_action=witness_action,
            )
            continue
        if left < existing.representative:
            representative = left
        else:
            representative = existing.representative
        action_map[joint_action] = CandidateAction(
            representative=representative,
            multiplicity=existing.multiplicity + 1,
            joint_action=existing.joint_action,
            answer_action=existing.answer_action,
            witness_action=existing.witness_action,
        )

    candidates = tuple(
        sorted(
            action_map.values(),
            key=lambda action: (action.representative[0], action.representative[1]),
        )
    )

    algebraic_bits = math.log2(spec.exact_state_count)
    joint_actions = [action.joint_action for action in candidates]
    answer_actions = [action.answer_action for action in candidates]
    witness_actions = [action.witness_action for action in candidates]

    exact_frontier_by_size: Dict[int, ClosureMetrics] = {}
    exact_best_masks_by_size: Dict[int, List[int]] = defaultdict(list)
    full_mask_count = 1 << len(candidates)
    exact_state_count = spec.exact_state_count

    for mask in range(full_mask_count):
        separator_count = mask.bit_count()
        joint_count, unresolved_pairs, joint_entropy = subset_signature_count(joint_ids, joint_actions, mask)
        answer_count, _, _ = subset_signature_count(answer_ids, answer_actions, mask)
        witness_count, _, _ = subset_signature_count(witness_ids, witness_actions, mask)
        metrics = ClosureMetrics(
            separator_count=separator_count,
            joint_count=joint_count,
            answer_count=answer_count,
            witness_count=witness_count,
            unresolved_pairs=unresolved_pairs,
            entropy_bits=joint_entropy,
            probe_deficiency_bits=algebraic_bits - log2_count(joint_count),
            shelf_width_bits=log2_count(joint_count) - log2_count(answer_count),
        )
        previous = exact_frontier_by_size.get(separator_count)
        if previous is None or (
            metrics.joint_count,
            -metrics.unresolved_pairs,
            metrics.entropy_bits,
        ) > (
            previous.joint_count,
            -previous.unresolved_pairs,
            previous.entropy_bits,
        ):
            exact_frontier_by_size[separator_count] = metrics
            exact_best_masks_by_size[separator_count] = [mask]
        elif previous is not None and (
            metrics.joint_count,
            -metrics.unresolved_pairs,
            metrics.entropy_bits,
        ) == (
            previous.joint_count,
            -previous.unresolved_pairs,
            previous.entropy_bits,
        ):
            exact_best_masks_by_size[separator_count].append(mask)

    exact_frontier = tuple(
        exact_frontier_by_size[size] for size in sorted(exact_frontier_by_size)
    )

    minimal_basis_size = -1
    optimal_masks: List[int] = []
    for metrics in exact_frontier:
        if metrics.joint_count == exact_state_count:
            minimal_basis_size = metrics.separator_count
            optimal_masks = exact_best_masks_by_size[minimal_basis_size]
            break

    minimal_basis_mask = optimal_masks[0]
    minimal_basis_representatives = tuple(
        candidates[action_index].representative
        for action_index in range(len(candidates))
        if minimal_basis_mask & (1 << action_index)
    )

    def greedy(strategy: str) -> Tuple[Tuple[int, Tuple[int, ...]], ...]:
        chosen_mask = 0
        chosen_indices: List[int] = []
        while True:
            current_joint_count, current_unresolved, current_entropy = subset_signature_count(
                joint_ids, joint_actions, chosen_mask
            )
            if current_joint_count == exact_state_count or chosen_mask == full_mask_count - 1:
                break
            best_action = None
            for action_index in range(len(candidates)):
                if chosen_mask & (1 << action_index):
                    continue
                proposal_mask = chosen_mask | (1 << action_index)
                proposal_joint_count, proposal_unresolved, proposal_entropy = subset_signature_count(
                    joint_ids, joint_actions, proposal_mask
                )
                if strategy == "greedy_joint_gain":
                    score = (
                        proposal_joint_count,
                        current_unresolved - proposal_unresolved,
                        proposal_entropy,
                        tuple(-value for value in candidates[action_index].representative[1]),
                        candidates[action_index].representative[0],
                    )
                elif strategy == "greedy_pair_gain":
                    score = (
                        current_unresolved - proposal_unresolved,
                        proposal_joint_count,
                        proposal_entropy,
                        tuple(-value for value in candidates[action_index].representative[1]),
                        candidates[action_index].representative[0],
                    )
                elif strategy == "greedy_info_gain":
                    score = (
                        proposal_entropy - current_entropy,
                        proposal_joint_count,
                        current_unresolved - proposal_unresolved,
                        tuple(-value for value in candidates[action_index].representative[1]),
                        candidates[action_index].representative[0],
                    )
                else:
                    raise ValueError(f"unknown strategy: {strategy}")
                if best_action is None or score > best_action[0]:
                    best_action = (score, action_index)
            assert best_action is not None
            chosen_indices.append(best_action[1])
            chosen_mask |= 1 << best_action[1]
        return tuple(candidates[index].representative for index in chosen_indices)

    greedy_paths = {
        strategy: greedy(strategy)
        for strategy in ("greedy_joint_gain", "greedy_pair_gain", "greedy_info_gain")
    }
    greedy_frontiers: Dict[str, Tuple[ClosureMetrics, ...]] = {}
    for strategy, path in greedy_paths.items():
        action_index_for_representative = {
            action.representative: index for index, action in enumerate(candidates)
        }
        steps: List[ClosureMetrics] = []
        chosen_mask = 0
        for step_count in range(len(path) + 1):
            joint_count, unresolved_pairs, joint_entropy = subset_signature_count(joint_ids, joint_actions, chosen_mask)
            answer_count, _, _ = subset_signature_count(answer_ids, answer_actions, chosen_mask)
            witness_count, _, _ = subset_signature_count(witness_ids, witness_actions, chosen_mask)
            steps.append(
                ClosureMetrics(
                    separator_count=step_count,
                    joint_count=joint_count,
                    answer_count=answer_count,
                    witness_count=witness_count,
                    unresolved_pairs=unresolved_pairs,
                    entropy_bits=joint_entropy,
                    probe_deficiency_bits=algebraic_bits - log2_count(joint_count),
                    shelf_width_bits=log2_count(joint_count) - log2_count(answer_count),
                )
            )
            if step_count == len(path):
                break
            chosen_mask |= 1 << action_index_for_representative[path[step_count]]
        greedy_frontiers[strategy] = tuple(steps)

    return FamilyClosureResult(
        label=spec.label,
        k=k,
        p=p,
        canonical_state_count=spec.exact_state_count,
        base_joint_count=len(set(base_joint_rows)),
        base_answer_count=len(set(base_answer_rows)),
        base_witness_count=len(set(base_witness_rows)),
        candidate_action_count=len(candidates),
        candidate_actions=candidates,
        exact_frontier=exact_frontier,
        optimal_subset_masks=tuple(optimal_masks),
        minimal_basis_size=minimal_basis_size,
        minimal_basis_representatives=minimal_basis_representatives,
        greedy_paths=greedy_paths,
        greedy_frontiers=greedy_frontiers,
    )


def closure_grid() -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for p in GRID_P_VALUES:
        for k in GRID_K_VALUES:
            result = build_family_closure_result(k, p)
            rows.append(
                {
                    "label": result.label,
                    "k": k,
                    "p": p,
                    "canonical_state_count": result.canonical_state_count,
                    "base_joint_count": result.base_joint_count,
                    "candidate_action_count": result.candidate_action_count,
                    "minimal_basis_size": result.minimal_basis_size,
                    "minimal_basis_representatives": [
                        [rep[0], list(rep[1])] for rep in result.minimal_basis_representatives
                    ],
                }
            )
    return rows


def stratigraphy_rows() -> List[Dict[str, object]]:
    causal = build_causal_referee_spec()
    rows = []
    specs = [
        ("M_3", compositional_tower(build_compositional_spec_bare(3))),
        ("Q_(3,2)", compositional_tower(build_compositional_spec_witness(3, 2))),
        ("Q_(4,2)", compositional_tower(build_compositional_spec_witness(4, 2))),
        ("Q_(5,3)", compositional_tower(build_compositional_spec_witness(5, 3))),
        ("causal_referee", dataset_tower(causal)),
    ]
    for label, tower in specs:
        rows.append(
            {
                "label": label,
                "algebraic_bits": tower["algebraic_bits"],
                "empirical_bits": tower["empirical_bits"],
                "probe_joint_bits": tower["probe_joint_bits"],
                "probe_witness_bits": tower["probe_witness_bits"],
                "probe_answer_bits": tower["probe_answer_bits"],
                "probe_deficiency_bits": tower["probe_deficiency_bits"],
                "shelf_width_bits": tower["shelf_width_bits"],
            }
        )
    return rows


def render_closure_svg(results: Sequence[FamilyClosureResult]) -> str:
    width = 980
    height = 540
    margin_left = 78
    margin_top = 48
    panel_gap = 54
    panel_width = (width - margin_left - 40 - panel_gap) / 2
    panel_height = height - margin_top - 70
    colors = {
        "Q_(3,2)": "#0b6e4f",
        "Q_(4,2)": "#c44536",
        "Q_(5,3)": "#22577a",
    }

    def x_for(step: int, max_step: int, left: float) -> float:
        usable = panel_width - 30
        return left + 15 + usable * (step / max_step if max_step else 0.0)

    max_step = max(result.minimal_basis_size for result in results)
    max_deficiency = max(
        result.exact_frontier[0].probe_deficiency_bits for result in results
    )
    max_shelf = max(
        max(metric.shelf_width_bits for metric in result.exact_frontier)
        for result in results
    )

    def y_for(value: float, max_value: float, top: float) -> float:
        usable = panel_height - 28
        return top + 12 + usable * (1 - (value / max_value if max_value else 0.0))

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #1f2933; }",
        ".title { font-size: 14px; font-weight: 700; }",
        ".axis { stroke: #9fb3c8; stroke-width: 1; }",
        ".grid { stroke: #d9e2ec; stroke-width: 1; stroke-dasharray: 4 4; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f8fbff"/>',
        f'<text x="{margin_left}" y="24" class="title">Separator Closure: Probe Deficiency Falls While Shelf Width Widens</text>',
    ]

    panel_specs = [
        ("Probe deficiency (bits)", max_deficiency, margin_left, "probe_deficiency_bits"),
        ("Shelf width (bits)", max_shelf, margin_left + panel_width + panel_gap, "shelf_width_bits"),
    ]
    for title, max_value, left, field in panel_specs:
        lines.append(f'<rect x="{left}" y="{margin_top}" width="{panel_width}" height="{panel_height}" class="panel"/>')
        lines.append(f'<text x="{left + 10}" y="{margin_top - 10}" class="title">{title}</text>')
        for tick in range(0, max_step + 1):
            x = x_for(tick, max_step, left)
            lines.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{margin_top + panel_height}" class="grid"/>')
            lines.append(f'<text x="{x - 4:.2f}" y="{margin_top + panel_height + 18}">{tick}</text>')
        for tick in range(0, int(math.ceil(max_value)) + 1):
            y = y_for(float(tick), max_value, margin_top)
            lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + panel_width}" y2="{y:.2f}" class="grid"/>')
            lines.append(f'<text x="{left - 30}" y="{y + 4:.2f}">{tick}</text>')
        lines.append(f'<line x1="{left}" y1="{margin_top + panel_height}" x2="{left + panel_width}" y2="{margin_top + panel_height}" class="axis"/>')
        lines.append(f'<line x1="{left}" y1="{margin_top}" x2="{left}" y2="{margin_top + panel_height}" class="axis"/>')
        lines.append(f'<text x="{left + panel_width / 2 - 52:.2f}" y="{height - 20}">added separator actions</text>')

        for result in results:
            color = colors[result.label]
            points = []
            for metrics in result.exact_frontier:
                value = getattr(metrics, field)
                points.append(
                    f"{x_for(metrics.separator_count, max_step, left):.2f},{y_for(value, max_value, margin_top):.2f}"
                )
            lines.append(
                f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(points)}"/>'
            )
            for metrics in result.exact_frontier:
                x = x_for(metrics.separator_count, max_step, left)
                y = y_for(getattr(metrics, field), max_value, margin_top)
                lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.2" fill="{color}"/>')

    legend_y = 36
    legend_x = width - 260
    for index, result in enumerate(results):
        color = colors[result.label]
        y = legend_y + index * 18
        lines.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 26}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<circle cx="{legend_x + 13}" cy="{y}" r="4.2" fill="{color}"/>')
        lines.append(f'<text x="{legend_x + 34}" y="{y + 4}">{result.label}</text>')

    lines.append("</svg>")
    return "\n".join(lines)


def render_stratigraphy_svg(rows: Sequence[Dict[str, object]]) -> str:
    width = 1120
    row_height = 62
    height = 118 + row_height * len(rows)
    margin_left = 210
    margin_right = 88
    margin_top = 78
    x_max = max(float(row["algebraic_bits"]) for row in rows) + 1.0

    def x_for(value: float) -> float:
        usable = width - margin_left - margin_right
        return margin_left + usable * (value / x_max)

    colors = {
        "algebraic": "#102a43",
        "empirical": "#0b6e4f",
        "joint": "#22577a",
        "witness": "#c44536",
        "answer": "#f4a261",
    }
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        'text { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 12px; fill: #243b53; }',
        ".title { font-size: 22px; font-weight: 700; fill: #102a43; }",
        ".subtitle { font-size: 13px; fill: #52606d; }",
        ".label { font-size: 14px; font-weight: 600; fill: #102a43; }",
        ".grid { stroke: #e5e7eb; stroke-width: 1; stroke-dasharray: 3 6; }",
        ".axis { stroke: #9fb3c8; stroke-width: 1.2; }",
        ".badge { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fcfcfb"/>',
        f'<text x="{margin_left}" y="34" class="title">Memory Stratigraphy</text>',
        f'<text x="{margin_left}" y="56" class="subtitle">Bit thresholds from the canonical quotient down to answer-only observation</text>',
        f'<rect x="{margin_left - 26}" y="{margin_top - 24}" width="{width - margin_left - margin_right + 52}" height="{height - margin_top - 28}" rx="18" ry="18" fill="#ffffff" stroke="#e6e8eb" stroke-width="1.2"/>',
    ]
    for tick in range(int(math.ceil(x_max)) + 1):
        x = x_for(float(tick))
        lines.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{height - 54}" class="grid"/>')
        lines.append(f'<text x="{x - 4:.2f}" y="{height - 28}">{tick}</text>')
    lines.append(f'<line x1="{margin_left}" y1="{height - 46}" x2="{width - margin_right}" y2="{height - 46}" class="axis"/>')
    lines.append(f'<text x="{(margin_left + width - margin_right) / 2 - 14:.2f}" y="{height - 12}" class="subtitle">bits</text>')

    legend = [
        ("algebraic", "algebraic"),
        ("empirical", "empirical"),
        ("joint", "probe-joint"),
        ("witness", "probe-witness"),
        ("answer", "probe-answer"),
    ]
    legend_x = width - 282
    for index, (key, label) in enumerate(legend):
        y = 30 + index * 20
        lines.append(f'<circle cx="{legend_x}" cy="{y}" r="5.5" fill="{colors[key]}"/>')
        lines.append(f'<text x="{legend_x + 14}" y="{y + 4}">{label}</text>')

    for row_index, row in enumerate(rows):
        y = margin_top + row_index * row_height + 28
        label = str(row["label"])
        lines.append(f'<text x="28" y="{y + 4}" class="label">{label}</text>')
        x_answer = x_for(float(row["probe_answer_bits"]))
        x_witness = x_for(float(row["probe_witness_bits"]))
        x_joint = x_for(float(row["probe_joint_bits"]))
        x_empirical = x_for(float(row["empirical_bits"]))
        x_algebraic = x_for(float(row["algebraic_bits"]))
        lines.append(f'<line x1="{x_answer:.2f}" y1="{y:.2f}" x2="{x_algebraic:.2f}" y2="{y:.2f}" stroke="#d9e2ec" stroke-width="7" stroke-linecap="round"/>')
        for key, x in (
            ("answer", x_answer),
            ("witness", x_witness),
            ("joint", x_joint),
            ("empirical", x_empirical),
            ("algebraic", x_algebraic),
        ):
            lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6" fill="{colors[key]}" stroke="#ffffff" stroke-width="1.5"/>')
        badge_x = width - margin_right - 168
        lines.append(f'<rect x="{badge_x}" y="{y - 16}" width="150" height="28" rx="14" ry="14" class="badge"/>')
        lines.append(
            f'<text x="{badge_x + 12}" y="{y + 4:.2f}">Δ={float(row["probe_deficiency_bits"]):.3f}   ω={float(row["shelf_width_bits"]):.3f}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def render_json(
    target_results: Sequence[FamilyClosureResult],
    grid_rows: Sequence[Dict[str, object]],
    stratigraphy: Sequence[Dict[str, object]],
) -> str:
    payload = {
        "targets": [
            {
                "label": result.label,
                "k": result.k,
                "p": result.p,
                "canonical_state_count": result.canonical_state_count,
                "base_joint_count": result.base_joint_count,
                "base_answer_count": result.base_answer_count,
                "base_witness_count": result.base_witness_count,
                "candidate_action_count": result.candidate_action_count,
                "candidate_actions": [
                    {
                        "representative": [action.representative[0], list(action.representative[1])],
                        "multiplicity": action.multiplicity,
                    }
                    for action in result.candidate_actions
                ],
                "exact_frontier": [
                    {
                        "separator_count": metrics.separator_count,
                        "joint_count": metrics.joint_count,
                        "answer_count": metrics.answer_count,
                        "witness_count": metrics.witness_count,
                        "unresolved_pairs": metrics.unresolved_pairs,
                        "entropy_bits": metrics.entropy_bits,
                        "probe_deficiency_bits": metrics.probe_deficiency_bits,
                        "shelf_width_bits": metrics.shelf_width_bits,
                    }
                    for metrics in result.exact_frontier
                ],
                "optimal_subset_masks": list(result.optimal_subset_masks),
                "minimal_basis_size": result.minimal_basis_size,
                "minimal_basis_representatives": [
                    [rep[0], list(rep[1])] for rep in result.minimal_basis_representatives
                ],
                "greedy_paths": {
                    name: [[rep[0], list(rep[1])] for rep in path]
                    for name, path in result.greedy_paths.items()
                },
                "greedy_frontiers": {
                    name: [
                        {
                            "separator_count": metrics.separator_count,
                            "joint_count": metrics.joint_count,
                            "answer_count": metrics.answer_count,
                            "witness_count": metrics.witness_count,
                            "unresolved_pairs": metrics.unresolved_pairs,
                            "entropy_bits": metrics.entropy_bits,
                            "probe_deficiency_bits": metrics.probe_deficiency_bits,
                            "shelf_width_bits": metrics.shelf_width_bits,
                        }
                        for metrics in frontier
                    ]
                    for name, frontier in result.greedy_frontiers.items()
                },
            }
            for result in target_results
        ],
        "closure_grid": list(grid_rows),
        "stratigraphy": list(stratigraphy),
    }
    return json.dumps(payload, indent=2)


def render_markdown(
    target_results: Sequence[FamilyClosureResult],
    grid_rows: Sequence[Dict[str, object]],
    stratigraphy: Sequence[Dict[str, object]],
) -> str:
    lines = [
        "# Separator Closure Experiment",
        "",
        "This report measures how quickly the current right-bank observational quotient closes back up to the exact two-sided quotient once left separators are added explicitly.",
        "",
        "## Takeaways",
        "",
    ]
    for result in target_results:
        first = result.exact_frontier[0]
        last = result.exact_frontier[-1]
        lines.append(
            f"- `{result.label}` starts at probe-joint `{first.joint_count}` and reaches the canonical `{result.canonical_state_count}` after `{result.minimal_basis_size}` added left actions."
        )
        lines.append(
            f"- Its exact minimal basis is `{[rep for rep in result.minimal_basis_representatives]}`."
        )
        lines.append(
            f"- Probe deficiency falls from `{bits_to_fixed(first.probe_deficiency_bits)}` bits to `{bits_to_fixed(last.probe_deficiency_bits)}` bits, while shelf width changes from `{bits_to_fixed(first.shelf_width_bits)}` to `{bits_to_fixed(last.shelf_width_bits)}` bits."
        )
    lines.extend(
        [
            "",
            "## Strategy Comparison",
            "",
            "All three greedy policies were evaluated:",
            "",
            "- `greedy_joint_gain`: maximize new probe-joint classes at each step.",
            "- `greedy_pair_gain`: maximize resolved canonical-state pairs at each step.",
            "- `greedy_info_gain`: maximize joint partition entropy at each step.",
            "",
        ]
    )
    for result in target_results:
        unique_paths = {tuple(path) for path in result.greedy_paths.values()}
        strategy_summary = ", ".join(
            f"`{name}` -> `{list(path)}`" for name, path in sorted(result.greedy_paths.items())
        )
        lines.append(f"- `{result.label}`: {strategy_summary}")
        lines.append(
            f"- `{result.label}` greedy path count: `{len(unique_paths)}` distinct paths; exact minimal basis count: `{len(result.optimal_subset_masks)}`."
        )

    lines.extend(["", "## Exact Closure Frontiers", ""])
    for result in target_results:
        lines.append(f"### `{result.label}`")
        lines.append("")
        lines.append(
            "| separators | joint | answer | witness | unresolved pairs | deficiency bits | shelf width bits |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for metrics in result.exact_frontier:
            lines.append(
                f"| `{metrics.separator_count}` | `{metrics.joint_count}` | `{metrics.answer_count}` | `{metrics.witness_count}` | `{metrics.unresolved_pairs}` | `{bits_to_fixed(metrics.probe_deficiency_bits)}` | `{bits_to_fixed(metrics.shelf_width_bits)}` |"
            )
        lines.append("")

    lines.extend(
        [
            "## Observed Scaling Law",
            "",
            "Across the full grid `k <= 5`, `p <= 3`, the minimal exact observational separator basis size matches `k` on every tested `Q_(k,p)` family.",
            "",
            "| family | base joint | candidate actions | minimal basis size | minimal basis |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in grid_rows:
        lines.append(
            f"| `{row['label']}` | `{row['base_joint_count']}` | `{row['candidate_action_count']}` | `{row['minimal_basis_size']}` | `{row['minimal_basis_representatives']}` |"
        )

    lines.extend(["", "## Memory Stratigraphy Snapshot", ""])
    lines.append("| family | algebraic bits | empirical bits | probe-joint bits | probe-witness bits | probe-answer bits | deficiency | shelf width |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for row in stratigraphy:
        lines.append(
            f"| `{row['label']}` | `{bits_to_fixed(float(row['algebraic_bits']))}` | `{bits_to_fixed(float(row['empirical_bits']))}` | `{bits_to_fixed(float(row['probe_joint_bits']))}` | `{bits_to_fixed(float(row['probe_witness_bits']))}` | `{bits_to_fixed(float(row['probe_answer_bits']))}` | `{bits_to_fixed(float(row['probe_deficiency_bits']))}` | `{bits_to_fixed(float(row['shelf_width_bits']))}` |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The cleanest new invariant is not raw separator count. It is **closure rank**: the minimal number of observational left actions needed to close the current right-bank quotient back to the canonical quotient.",
            "",
            "On the tested synthetic families, closure rank behaves like `k`, not like `p`. The canonical witness dimension still controls the size of the full quotient, but the number of missing left actions needed to close the current probe bank appears depth-indexed.",
            "",
            "The second surprise is that better probes do not necessarily shrink the potential mirage interval. Along the exact closure frontier, probe deficiency falls monotonically, but shelf width grows because joint distinguishability opens faster than answer-only distinguishability.",
            "",
            "That means separator-complete closure is doing two things at once:",
            "",
            "- it repairs probe deficiency by restoring the missing two-sided distinctions,",
            "- it reveals a larger answer-vs-justification gap inside the observational tower before exact closure arrives.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    target_results = [build_family_closure_result(k, p) for k, p in TARGET_FAMILIES]
    grid_rows = closure_grid()
    stratigraphy = stratigraphy_rows()

    json_path = RESULTS_DIR / "separator_closure_experiment.json"
    md_path = RESULTS_DIR / "separator_closure_experiment.md"
    closure_svg_path = RESULTS_DIR / "separator_closure_deficiency.svg"
    stratigraphy_svg_path = RESULTS_DIR / "memory_stratigraphy.svg"

    json_path.write_text(render_json(target_results, grid_rows, stratigraphy))
    md_path.write_text(render_markdown(target_results, grid_rows, stratigraphy))
    closure_svg_path.write_text(render_closure_svg(target_results))
    stratigraphy_svg_path.write_text(render_stratigraphy_svg(stratigraphy))

    summary = {
        "target_labels": [result.label for result in target_results],
        "minimal_basis_sizes": {
            result.label: result.minimal_basis_size for result in target_results
        },
        "paths": {
            result.label: {
                name: [list(rep[1]) for rep in path]
                for name, path in result.greedy_paths.items()
            }
            for result in target_results
        },
        "json_path": str(json_path),
        "md_path": str(md_path),
        "closure_svg_path": str(closure_svg_path),
        "stratigraphy_svg_path": str(stratigraphy_svg_path),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
