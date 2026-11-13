"""Cost-curve chart: monthly cost vs billed utilization, per-token as a flat line."""

from .model import monthly_model_api_cost
from .rates import DAYS_PER_MONTH, GPU_RATES_PER_MINUTE, MINUTES_PER_DAY


def write_cost_curve(w, gpu, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rate = GPU_RATES_PER_MINUTE[gpu]
    api = monthly_model_api_cost(w)
    total_minutes = MINUTES_PER_DAY * DAYS_PER_MONTH

    utils = [i / 100 for i in range(0, 101)]
    dedicated = [u * total_minutes * rate for u in utils]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot([u * 100 for u in utils], dedicated, label=f"Dedicated {gpu} (autoscaled)")
    ax.axhline(api, color="tab:orange", label="Per-token Model API (flat)")
    ax.set_xlabel("Billed utilization (% of month)")
    ax.set_ylabel("Monthly cost (USD)")
    ax.set_title(f"Per-token vs dedicated {gpu} — monthly cost")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
