# inference-shape-advisor

A small cost-and-latency advisor for one question an AI solutions architect
answers on almost every discovery call:

> **Given your traffic shape, should you pay per token (Model API), or
> dedicate a GPU and how warm should it stay?**

Feed it a workload profile; it compares, side by side:

1. **Per-token Model API cost** (monthly, from your token volumes).
2. **Dedicated GPU-minute cost** at `min_replicas` 0 / 1 / 2, with the
   15-minute scale-down delay modelled honestly — idle gaps shorter than
   15 minutes bill in full.
3. **Cold-start exposure** against your latency target.
4. **The crossover utilization** where dedicated beats per-token,
   per GPU tier.

It models cost and latency from published list rates. It does not deploy
models, benchmark GPUs, or use any customer data.

## Rates used (all published list rates, verify before budgeting)

Dedicated deployments bill per GPU-minute per replica. Rates below are from
Baseten's pricing page as reported by multiple independent analyses checked
in November 2026 (Baseten's own page renders as a JavaScript shell, so the
rate card could not be read directly — see Sources):

| GPU | $/min | $/hr (rate×60) | Source note |
|---|---|---|---|
| T4 16 GiB | 0.01052 | 0.63 | Spheron / Runpod / AnchorTerminal, checked Oct–Nov 2026 |
| L4 24 GiB | 0.01414 | 0.85 | same |
| A10G 24 GiB | 0.02012 | 1.21 | same |
| H100 MIG 40 GiB | 0.0625 | 3.75 | same |
| A100 80 GiB | 0.06667 | 4.00 | same |
| H100 80 GiB | 0.10833 | 6.50 | same |
| B200 180 GiB | 0.16633 | 9.98 | same |

Other modelled assumptions (each is a labelled parameter, not a hidden
constant):

- **Scale-down delay: 15 minutes.** A replica stays billed for 15 minutes
  after traffic stops. Idle gaps under 15 minutes bill in full.
- **Month = 30 days** (43,200 minutes) for monthly figures, matching the
  published "one warm H100 ≈ $4,680/month" arithmetic.
- **Cold start: 30–90s+ on large models.** Default assumption 60s,
  override with `--cold-start-s`. This is a modelling assumption from
  published analyses, not a measured Baseten figure.
- **Production guidance `min_replicas ≥ 2`** is from Baseten's own
  autoscaling documentation as reported in those analyses.

Example Model-API pricing used in the worked example: GPT OSS 120B at
$0.10 / $0.50 per 1M input/output tokens (Baseten Model APIs, as reported
Nov 2026). Override with `--api-input-usd-per-1m` / `--api-output-usd-per-1m`.

## Quick start

```bash
python -m inference_shape_advisor \
  --requests-per-day 20000 \
  --avg-input-tokens 800 \
  --avg-output-tokens 300 \
  --active-minutes-per-day 240 \
  --bursts-per-day 40 \
  --gpu H100 \
  --latency-target-s 2 \
  --out report.md
```

Traffic is modelled as `bursts-per-day` evenly spaced bursts totalling
`active-minutes-per-day` minutes of traffic. Each burst keeps the replica
billed for its own duration plus the 15-minute scale-down tail.

## What the report says

- Monthly cost for each shape, at each `min_replicas` level.
- Whether a scale-from-zero cold start fits inside your latency target.
- The utilization (billed fraction of the month) at which dedicated
  crosses below per-token, per GPU tier.
- A cost-curve chart (PNG) when matplotlib is available.

## Sources

- Baseten Solutions Architect posting (live on Baseten's Ashby board,
  checked 2026-11-13): https://jobs.ashbyhq.com/baseten/c64515f9-a8f7-4633-9340-17cda56b1ef0
- Spheron, "Baseten Pricing 2026": https://www.spheron.network/blog/baseten-pricing-2026-model-serving-cost/
- Runpod vs Baseten comparison (rates re-verified 15 Oct 2026): https://www.runpod.io/articles/comparison/runpod-vs-baseten
- AnchorTerminal Baseten review (facts verified 30 Sep 2026): https://www.anchorterminal.com/tools/baseten
- HostFleet Baseten pricing guide (rates rechecked 7 Nov 2026): https://www.hostfleet.net/baseten-pricing-guide-2026/

## Honest bounds

Published list rates only; every rate is cited with its source and check
date in the README and in the generated report. No customer data, no
invented benchmarks. GPU selection advice (H100 vs B200, latency- vs
throughput-optimized) is presented as cost/latency tradeoffs to discuss
with the customer, not as measured performance claims.
