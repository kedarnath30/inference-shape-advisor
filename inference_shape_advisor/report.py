"""Markdown report rendering for shape comparisons."""

from .model import Workload, compare_shapes, crossover_utilization, monthly_model_api_cost
from .rates import GPU_RATES_PER_MINUTE, RATE_PROVENANCE


def render_report(w: Workload, gpu: str) -> str:
    shapes = compare_shapes(w, gpu)
    api = monthly_model_api_cost(w)
    xo = crossover_utilization(w, gpu)
    lines = []
    lines.append("# Inference shape recommendation")
    lines.append("")
    lines.append("## Workload profile (as given)")
    lines.append("")
    lines.append(f"- Requests/day: {w.requests_per_day:,.0f}")
    lines.append(f"- Avg input tokens/request: {w.avg_input_tokens:,.0f}")
    lines.append(f"- Avg output tokens/request: {w.avg_output_tokens:,.0f}")
    lines.append(f"- Active minutes/day: {w.active_minutes_per_day:,.0f} across {w.bursts_per_day:,.0f} bursts")
    lines.append(f"- Latency target: {w.latency_target_s:.0f}s")
    lines.append(f"- Assumed cold start (scale from zero): {w.cold_start_s:.0f}s")
    lines.append(
        f"- Example Model-API pricing: ${w.api_input_usd_per_1m:.2f} in / "
        f"${w.api_output_usd_per_1m:.2f} out per 1M tokens"
    )
    lines.append("")
    lines.append("## Monthly cost by shape")
    lines.append("")
    lines.append("| Shape | Monthly USD | Notes |")
    lines.append("|---|---:|---|")
    for s in shapes:
        notes = " ".join(s.notes)
        lines.append(f"| {s.label} | ${s.monthly_usd:,.2f} | {notes} |")
    lines.append("")
    if xo is not None:
        lines.append("## Crossover")
        lines.append("")
        lines.append(
            f"On {gpu} at ${GPU_RATES_PER_MINUTE[gpu]:.5f}/min, dedicated crosses below "
            f"per-token when billed utilization exceeds **{xo * 100:.1f}% of the month** "
            f"({xo * 24 * 30:.1f} billed hours/month). Below that, per-token wins on cost; "
            "above it, dedicated wins — before counting cold-start or availability needs."
        )
        lines.append("")
    lines.append("## Rates and assumptions")
    lines.append("")
    lines.append(f"- {RATE_PROVENANCE}")
    lines.append(
        "- Scale-down delay modelled at 15 minutes: idle gaps shorter than that "
        "bill in full. Month = 30 days."
    )
    lines.append(
        "- Cold start is a modelling assumption (published analyses report 30-90s+ "
        "on large models), not a measured figure. Override with --cold-start-s."
    )
    lines.append(
        "- This tool models cost and latency from published list rates. It does not "
        "deploy models or measure GPU performance; GPU-tier advice (H100 vs B200, "
        "latency- vs throughput-optimized) is a tradeoff to discuss, not a benchmark claim."
    )
    lines.append("")
    lines.append(f"Per-token monthly cost for reference: ${api:,.2f}.")
    lines.append("")
    return "\n".join(lines)
