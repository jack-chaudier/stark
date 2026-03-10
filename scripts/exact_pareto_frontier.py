#!/usr/bin/env python3
"""Exact small-scale Pareto frontiers for selective-memory compressors.

This script solves the partition optimization problem exactly on the models
where that is tractable:

- `M_3` on the full canonical quotient,
- `Q_(3,2)`, `Q_(4,2)`, `Q_(5,3)` on the current probe-joint observational
  quotient,
- `causal_referee` on empirical support.

The result is a true partition frontier for the chosen atomic state space:
for each bucket budget `K`, it enumerates all clusterings into at most `K`
blocks via an exact dynamic program and reports the non-dominated
answer/witness tradeoffs under both forced and breach decoding.
"""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from phase_transition_sweep import (
    DatasetSpec,
    Output,
    build_causal_referee_spec,
    build_compositional_spec_bare,
    build_compositional_spec_witness,
    dataset_tower,
    output_bare,
)

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"


@dataclass(frozen=True)
class FrontierModel:
    label: str
    scope: str
    has_witness_channel: bool
    rows: Tuple[Tuple[Output, ...], ...]
    state_weights: Tuple[int, ...]
    answer_threshold_bits: float
    joint_threshold_bits: float


@dataclass(frozen=True)
class FrontierSummary:
    budget_bits: int
    bucket_limit: int
    frontier_size: int
    best_answer: float
    best_witness: float
    witness_at_perfect_answer: float | None
    answer_at_perfect_witness: float | None


def output_mode(values: Iterable[str | Tuple[int, ...]]) -> str | Tuple[int, ...]:
    counts = Counter(values)
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def pareto_prune(points: Iterable[Tuple[int, int]]) -> Tuple[Tuple[int, int], ...]:
    unique = sorted(set(points), reverse=True)
    frontier: List[Tuple[int, int]] = []
    best_witness = -1
    for answer_score, witness_score in unique:
        if witness_score > best_witness:
            frontier.append((answer_score, witness_score))
            best_witness = witness_score
    return tuple(frontier)


def compress_columns(rows: Sequence[Sequence[Output]]) -> List[Tuple[int, Tuple[Output, ...]]]:
    if not rows:
        return []
    column_count = len(rows[0])
    grouped: Dict[Tuple[Output, ...], int] = defaultdict(int)
    for column_index in range(column_count):
        signature = tuple(row[column_index] for row in rows)
        grouped[signature] += 1
    return sorted(
        ((count, signature) for signature, count in grouped.items()),
        key=lambda item: (str(item[1]), item[0]),
    )


def build_canonical_bare_model(k: int) -> FrontierModel:
    spec = build_compositional_spec_bare(k)
    grouped: Dict[Tuple[Output, ...], List[int]] = defaultdict(list)
    for state_index, row in enumerate(spec.outcomes):
        grouped[tuple(row)].append(state_index)
    representatives = [
        members[0]
        for _, members in sorted(grouped.items(), key=lambda item: (str(item[0]), item[1][0]))
    ]
    rows = tuple(tuple(spec.outcomes[index]) for index in representatives)
    weights = tuple(len(grouped[tuple(spec.outcomes[index])]) for index in representatives)
    return FrontierModel(
        label=spec.label,
        scope="canonical_row_aggregated",
        has_witness_channel=False,
        rows=rows,
        state_weights=weights,
        answer_threshold_bits=math.log2(len(rows)),
        joint_threshold_bits=math.log2(spec.exact_state_count),
    )


def build_probe_joint_model(k: int, p: int) -> FrontierModel:
    spec = build_compositional_spec_witness(k, p)
    grouped: Dict[Tuple[Tuple[str, Tuple[int, ...]], ...], List[int]] = defaultdict(list)
    for state_index, row in enumerate(spec.outcomes):
        grouped[tuple((output.answer, output.witness) for output in row)].append(state_index)
    representatives = [
        members[0]
        for _, members in sorted(grouped.items(), key=lambda item: (str(item[0]), item[1][0]))
    ]
    rows = tuple(tuple(spec.outcomes[index]) for index in representatives)
    weights = tuple(len(grouped[tuple((output.answer, output.witness) for output in spec.outcomes[index])]) for index in representatives)
    answer_count = len({tuple(output.answer for output in row) for row in rows})
    return FrontierModel(
        label=spec.label,
        scope="probe_joint",
        has_witness_channel=True,
        rows=rows,
        state_weights=weights,
        answer_threshold_bits=math.log2(answer_count),
        joint_threshold_bits=math.log2(len(rows)),
    )


def build_dataset_support_model(spec: DatasetSpec) -> FrontierModel:
    rows = tuple((output,) for output in spec.support_outputs)
    answer_count = len({output.answer for output in spec.support_outputs})
    joint_count = len(spec.support_outputs)
    return FrontierModel(
        label=spec.label,
        scope="empirical_support",
        has_witness_channel=True,
        rows=rows,
        state_weights=tuple(spec.support_weights),
        answer_threshold_bits=math.log2(answer_count),
        joint_threshold_bits=math.log2(joint_count),
    )


def cluster_scores(model: FrontierModel, policy: str) -> List[Tuple[int, int]]:
    state_count = len(model.rows)
    column_groups = compress_columns(model.rows)
    scores = [(0, 0)] * (1 << state_count)
    for mask in range(1, 1 << state_count):
        answer_correct = 0
        witness_correct = 0
        chosen_indices = [index for index in range(state_count) if mask & (1 << index)]
        total_weight = sum(model.state_weights[index] for index in chosen_indices)
        for multiplicity, signature in column_groups:
            outputs = [signature[index] for index in chosen_indices]
            weights = [model.state_weights[index] for index in chosen_indices]
            if policy == "breach":
                unanimous = len(set(outputs)) == 1 if model.has_witness_channel else len({output.answer for output in outputs}) == 1
                if unanimous:
                    answer_correct += total_weight * multiplicity
                    witness_correct += total_weight * multiplicity
                continue
            answer_counts = Counter()
            for output, weight in zip(outputs, weights):
                answer_counts[output.answer] += weight
            predicted_answer = sorted(answer_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
            answer_matches = sum(
                weight for output, weight in zip(outputs, weights) if output.answer == predicted_answer
            )
            answer_correct += answer_matches * multiplicity
            if model.has_witness_channel:
                if predicted_answer == "blocked":
                    predicted_witness: Tuple[int, ...] = ()
                else:
                    witness_counts = Counter()
                    for output, weight in zip(outputs, weights):
                        if output.answer == predicted_answer:
                            witness_counts[output.witness] += weight
                    predicted_witness = sorted(
                        witness_counts.items(),
                        key=lambda item: (-item[1], item[0]),
                    )[0][0]
                witness_matches = sum(
                    weight for output, weight in zip(outputs, weights) if output.witness == predicted_witness
                )
                witness_correct += witness_matches * multiplicity
            else:
                witness_correct += answer_matches * multiplicity
        scores[mask] = (answer_correct, witness_correct)
    return scores


def solve_frontier(model: FrontierModel, policy: str) -> Dict[int, Tuple[Tuple[int, int], ...]]:
    state_count = len(model.rows)
    full_mask = (1 << state_count) - 1
    subset_scores = cluster_scores(model, policy)

    @lru_cache(maxsize=None)
    def solve(mask: int, buckets: int) -> Tuple[Tuple[int, int], ...]:
        if mask == 0:
            return ((0, 0),) if buckets == 0 else ()
        if buckets == 0:
            return ()
        anchor = mask & -mask
        points: List[Tuple[int, int]] = []
        submask = mask
        while submask:
            if submask & anchor:
                remainder = mask ^ submask
                for answer_score, witness_score in solve(remainder, buckets - 1):
                    cluster_answer, cluster_witness = subset_scores[submask]
                    points.append(
                        (answer_score + cluster_answer, witness_score + cluster_witness)
                    )
            submask = (submask - 1) & mask
        return pareto_prune(points)

    frontiers: Dict[int, Tuple[Tuple[int, int], ...]] = {}
    for bucket_limit in range(1, state_count + 1):
        points: List[Tuple[int, int]] = []
        for buckets in range(1, bucket_limit + 1):
            points.extend(solve(full_mask, buckets))
        frontiers[bucket_limit] = pareto_prune(points)
    return frontiers


def summarize_frontier(
    model: FrontierModel,
    frontiers: Dict[int, Tuple[Tuple[int, int], ...]],
) -> List[FrontierSummary]:
    total_interactions = sum(model.state_weights) * len(model.rows[0])
    max_bucket_limit = len(model.rows)
    max_budget_bits = max(1, math.ceil(math.log2(max_bucket_limit)))
    summaries: List[FrontierSummary] = []
    for budget_bits in range(max_budget_bits + 1):
        bucket_limit = min(max_bucket_limit, 1 << budget_bits)
        points = frontiers[bucket_limit]
        best_answer = max(answer for answer, _ in points) / total_interactions
        best_witness = max(witness for _, witness in points) / total_interactions
        answer_target = [
            witness for answer, witness in points if answer == total_interactions
        ]
        witness_target = [
            answer for answer, witness in points if witness == total_interactions
        ]
        summaries.append(
            FrontierSummary(
                budget_bits=budget_bits,
                bucket_limit=bucket_limit,
                frontier_size=len(points),
                best_answer=best_answer,
                best_witness=best_witness,
                witness_at_perfect_answer=(
                    max(answer_target) / total_interactions if answer_target else None
                ),
                answer_at_perfect_witness=(
                    max(witness_target) / total_interactions if witness_target else None
                ),
            )
        )
    return summaries


def render_json(
    model_payloads: Sequence[Dict[str, object]],
) -> str:
    return json.dumps({"models": list(model_payloads)}, indent=2)


def render_markdown(model_payloads: Sequence[Dict[str, object]]) -> str:
    lines = [
        "# Exact Pareto Frontiers",
        "",
        "This report computes exact partition frontiers for the atomic state spaces listed below.",
        "",
        "Scope matters:",
        "",
        "- `M_3` is solved exactly after lossless aggregation of identical output rows for the frontier objective.",
        "- `Q_(3,2)`, `Q_(4,2)`, and `Q_(5,3)` are solved exactly on the current probe-joint observational quotient.",
        "- `causal_referee` is solved exactly on empirical support.",
        "",
    ]
    for payload in model_payloads:
        lines.append(f"## `{payload['label']}` ({payload['scope']})")
        lines.append("")
        lines.append(
            f"- atomic states: `{payload['state_count']}`"
        )
        lines.append(
            f"- answer threshold: `{payload['answer_threshold_bits']:.3f}` bits"
        )
        lines.append(
            f"- joint threshold: `{payload['joint_threshold_bits']:.3f}` bits"
        )
        lines.append("")
        for policy in ("forced", "breach"):
            lines.append(f"### `{policy}`")
            lines.append("")
            lines.append(
                "| bits | bucket limit | frontier size | best answer | best witness | witness at perfect answer | answer at perfect witness |"
            )
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            for row in payload["summaries"][policy]:
                witness_at_perfect_answer = row["witness_at_perfect_answer"]
                answer_at_perfect_witness = row["answer_at_perfect_witness"]
                witness_cell = (
                    f"`{witness_at_perfect_answer:.3f}`"
                    if witness_at_perfect_answer is not None
                    else "`-`"
                )
                answer_cell = (
                    f"`{answer_at_perfect_witness:.3f}`"
                    if answer_at_perfect_witness is not None
                    else "`-`"
                )
                lines.append(
                    f"| `{row['budget_bits']}` | `{row['bucket_limit']}` | `{row['frontier_size']}` | "
                    f"`{row['best_answer']:.3f}` | `{row['best_witness']:.3f}` | "
                    f"{witness_cell} | {answer_cell} |"
                )
            lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "The exact frontier tells us whether the shelf is a compressor artifact or an intrinsic underbudget tradeoff on the chosen atomic state space.",
            "",
            "The strongest observational cases are the families where `answer_threshold_bits < joint_threshold_bits`. There, the exact frontier should admit budgets where perfect answerability is possible but perfect witness recovery is not. That is the intrinsic shelf for the measured quotient tower.",
            "",
        ]
    )
    return "\n".join(lines)


def render_svg(model_payloads: Sequence[Dict[str, object]]) -> str:
    width = 1040
    height = 600
    margin_left = 88
    margin_top = 54
    panel_gap = 44
    panel_width = (width - margin_left - 40 - panel_gap) / 2
    panel_height = height - margin_top - 92
    colors = {
        "M_3": "#102a43",
        "Q_(3,2)": "#0b6e4f",
        "Q_(4,2)": "#c44536",
        "Q_(5,3)": "#22577a",
        "causal_referee": "#f4a261",
    }

    def x_for(step: int, max_bits: int, left: float) -> float:
        usable = panel_width - 30
        return left + 15 + usable * (step / max_bits if max_bits else 0.0)

    def y_for(value: float, top: float) -> float:
        usable = panel_height - 28
        return top + 12 + usable * (1 - value)

    max_bits = max(
        max(row["budget_bits"] for row in payload["summaries"]["forced"])
        for payload in model_payloads
    )
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text { font-family: Menlo, Monaco, Consolas, monospace; font-size: 11px; fill: #1f2933; }",
        ".title { font-size: 14px; font-weight: 700; }",
        ".axis { stroke: #9fb3c8; stroke-width: 1; }",
        ".grid { stroke: #d9e2ec; stroke-width: 1; stroke-dasharray: 4 4; }",
        ".panel { fill: #ffffff; stroke: #d9e2ec; stroke-width: 1; }",
        "</style>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fbfbff"/>',
        f'<text x="{margin_left}" y="26" class="title">Exact Pareto Frontier Envelopes</text>',
    ]
    for panel_index, policy in enumerate(("forced", "breach")):
        left = margin_left + panel_index * (panel_width + panel_gap)
        lines.append(f'<rect x="{left}" y="{margin_top}" width="{panel_width}" height="{panel_height}" class="panel"/>')
        lines.append(f'<text x="{left + 10}" y="{margin_top - 10}" class="title">{policy}</text>')
        for tick in range(max_bits + 1):
            x = x_for(tick, max_bits, left)
            lines.append(f'<line x1="{x:.2f}" y1="{margin_top}" x2="{x:.2f}" y2="{margin_top + panel_height}" class="grid"/>')
            lines.append(f'<text x="{x - 4:.2f}" y="{margin_top + panel_height + 18}">{tick}</text>')
        for tick in range(0, 11):
            value = tick / 10
            y = y_for(value, margin_top)
            lines.append(f'<line x1="{left}" y1="{y:.2f}" x2="{left + panel_width}" y2="{y:.2f}" class="grid"/>')
            lines.append(f'<text x="{left - 28}" y="{y + 4:.2f}">{value:.1f}</text>')
        lines.append(f'<line x1="{left}" y1="{margin_top + panel_height}" x2="{left + panel_width}" y2="{margin_top + panel_height}" class="axis"/>')
        lines.append(f'<line x1="{left}" y1="{margin_top}" x2="{left}" y2="{margin_top + panel_height}" class="axis"/>')
        lines.append(f'<text x="{left + panel_width / 2 - 20:.2f}" y="{height - 26}">bits</text>')
        for payload in model_payloads:
            color = colors[payload["label"]]
            answer_points = []
            witness_points = []
            for row in payload["summaries"][policy]:
                answer_points.append(
                    f"{x_for(row['budget_bits'], max_bits, left):.2f},{y_for(row['best_answer'], margin_top):.2f}"
                )
                witness_points.append(
                    f"{x_for(row['budget_bits'], max_bits, left):.2f},{y_for(row['best_witness'], margin_top):.2f}"
                )
            lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{" ".join(answer_points)}"/>')
            lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="7 5" points="{" ".join(witness_points)}"/>')
    legend_x = width - 278
    legend_y = 42
    for index, payload in enumerate(model_payloads):
        color = colors[payload["label"]]
        y = legend_y + index * 18
        lines.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 24}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<line x1="{legend_x}" y1="{y + 7}" x2="{legend_x + 24}" y2="{y + 7}" stroke="{color}" stroke-width="2" stroke-dasharray="7 5"/>')
        lines.append(f'<text x="{legend_x + 34}" y="{y + 5}">{payload["label"]}</text>')
    lines.append(f'<text x="{width - 278}" y="{height - 52}">solid = best answer</text>')
    lines.append(f'<text x="{width - 278}" y="{height - 36}">dashed = best witness</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    models = [
        build_canonical_bare_model(3),
        build_probe_joint_model(3, 2),
        build_probe_joint_model(4, 2),
        build_probe_joint_model(5, 3),
        build_dataset_support_model(build_causal_referee_spec()),
    ]

    payloads = []
    for model in models:
        summaries = {}
        for policy in ("forced", "breach"):
            frontiers = solve_frontier(model, policy)
            summaries[policy] = [
                {
                    "budget_bits": row.budget_bits,
                    "bucket_limit": row.bucket_limit,
                    "frontier_size": row.frontier_size,
                    "best_answer": row.best_answer,
                    "best_witness": row.best_witness,
                    "witness_at_perfect_answer": row.witness_at_perfect_answer,
                    "answer_at_perfect_witness": row.answer_at_perfect_witness,
                }
                for row in summarize_frontier(model, frontiers)
            ]
        payloads.append(
            {
                "label": model.label,
                "scope": model.scope,
                "state_count": len(model.rows),
                "answer_threshold_bits": model.answer_threshold_bits,
                "joint_threshold_bits": model.joint_threshold_bits,
                "summaries": summaries,
            }
        )

    json_path = RESULTS_DIR / "exact_pareto_frontier.json"
    md_path = RESULTS_DIR / "exact_pareto_frontier.md"
    svg_path = RESULTS_DIR / "exact_pareto_frontier.svg"

    json_path.write_text(render_json(payloads))
    md_path.write_text(render_markdown(payloads))
    svg_path.write_text(render_svg(payloads))

    print(
        json.dumps(
            {
                "models": [payload["label"] for payload in payloads],
                "json_path": str(json_path),
                "md_path": str(md_path),
                "svg_path": str(svg_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
