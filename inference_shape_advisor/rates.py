"""Published Baseten dedicated-GPU list rates ($ per GPU-minute per replica).

Baseten's own pricing page renders as a JavaScript shell, so these rates are
as reported by independent analyses that cite that page, all checked
Oct-Nov 2026. Verify against the live pricing page before budgeting.

Sources:
- Spheron, "Baseten Pricing 2026" (https://www.spheron.network/blog/baseten-pricing-2026-model-serving-cost/)
- Runpod vs Baseten (rates re-verified 15 Oct 2026) (https://www.runpod.io/articles/comparison/runpod-vs-baseten)
- AnchorTerminal Baseten review (facts verified 30 Sep 2026) (https://www.anchorterminal.com/tools/baseten)
- HostFleet Baseten pricing guide (rates rechecked 7 Nov 2026) (https://www.hostfleet.net/baseten-pricing-guide-2026/)
"""

GPU_RATES_PER_MINUTE = {
    "T4": 0.01052,
    "L4": 0.01414,
    "A10G": 0.02012,
    "H100 MIG": 0.0625,
    "A100": 0.06667,
    "H100": 0.10833,
    "B200": 0.16633,
}

RATE_PROVENANCE = (
    "Baseten pricing page, as reported by Spheron / Runpod / AnchorTerminal / "
    "HostFleet, checked Oct-Nov 2026. Baseten's page renders as a JS shell; "
    "re-verify before budgeting."
)

DAYS_PER_MONTH = 30
MINUTES_PER_DAY = 24 * 60
SCALE_DOWN_DELAY_MINUTES = 15
DEFAULT_COLD_START_SECONDS = 60  # modelling assumption; published analyses say 30-90s+ on large models
