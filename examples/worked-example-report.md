# Inference shape recommendation

## Workload profile (as given)

- Requests/day: 20,000
- Avg input tokens/request: 800
- Avg output tokens/request: 300
- Active minutes/day: 240 across 40 bursts
- Latency target: 2s
- Assumed cold start (scale from zero): 60s
- Example Model-API pricing: $0.10 in / $0.50 out per 1M tokens

## Monthly cost by shape

| Shape | Monthly USD | Notes |
|---|---:|---|
| Per-token Model API | $138.00 | Pay per token; no idle cost; no cold start. |
| Dedicated H100, min_replicas=0 | $2,729.92 | Scale-to-zero with 15-min scale-down delay modelled. Cold start (60s assumed) exceeds latency target (2s) — first request after idle waits or retries. |
| Dedicated H100, min_replicas=1 | $4,679.86 | 1 warm replica(s) floor the bill at 1x always-on. |
| Dedicated H100, min_replicas=2 | $9,359.71 | 2 warm replica(s) floor the bill at 2x always-on. |

## Crossover

On H100 at $0.10833/min, dedicated crosses below per-token when billed utilization exceeds **2.9% of the month** (21.2 billed hours/month). Below that, per-token wins on cost; above it, dedicated wins — before counting cold-start or availability needs.

## Rates and assumptions

- Baseten pricing page, as reported by Spheron / Runpod / AnchorTerminal / HostFleet, checked Oct-Nov 2026. Baseten's page renders as a JS shell; re-verify before budgeting.
- Scale-down delay modelled at 15 minutes: idle gaps shorter than that bill in full. Month = 30 days.
- Cold start is a modelling assumption (published analyses report 30-90s+ on large models), not a measured figure. Override with --cold-start-s.
- This tool models cost and latency from published list rates. It does not deploy models or measure GPU performance; GPU-tier advice (H100 vs B200, latency- vs throughput-optimized) is a tradeoff to discuss, not a benchmark claim.

Per-token monthly cost for reference: $138.00.
