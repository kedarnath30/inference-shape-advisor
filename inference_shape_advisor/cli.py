"""CLI: compare per-token vs dedicated serving shapes for a workload profile."""

import argparse
import sys

from .model import Workload
from .rates import GPU_RATES_PER_MINUTE
from .report import render_report


def build_parser():
    p = argparse.ArgumentParser(
        prog="inference-shape-advisor",
        description="Compare per-token Model API cost vs dedicated GPU-minute cost.",
    )
    p.add_argument("--requests-per-day", type=float, required=True)
    p.add_argument("--avg-input-tokens", type=float, required=True)
    p.add_argument("--avg-output-tokens", type=float, required=True)
    p.add_argument("--active-minutes-per-day", type=float, required=True)
    p.add_argument("--bursts-per-day", type=float, default=24)
    p.add_argument("--gpu", choices=sorted(GPU_RATES_PER_MINUTE), default="H100")
    p.add_argument("--latency-target-s", type=float, required=True)
    p.add_argument("--cold-start-s", type=float, default=60.0)
    p.add_argument("--api-input-usd-per-1m", type=float, default=0.10)
    p.add_argument("--api-output-usd-per-1m", type=float, default=0.50)
    p.add_argument("--out", default=None, help="Write markdown report to this path (default: stdout)")
    p.add_argument("--chart", default=None, help="Write cost-curve PNG to this path (needs matplotlib)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        w = Workload(
            requests_per_day=args.requests_per_day,
            avg_input_tokens=args.avg_input_tokens,
            avg_output_tokens=args.avg_output_tokens,
            active_minutes_per_day=args.active_minutes_per_day,
            bursts_per_day=args.bursts_per_day,
            latency_target_s=args.latency_target_s,
            cold_start_s=args.cold_start_s,
            api_input_usd_per_1m=args.api_input_usd_per_1m,
            api_output_usd_per_1m=args.api_output_usd_per_1m,
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    text = render_report(w, args.gpu)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)

    if args.chart:
        try:
            from .chart import write_cost_curve

            write_cost_curve(w, args.gpu, args.chart)
        except ImportError:
            print("matplotlib not available; skipping chart", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
