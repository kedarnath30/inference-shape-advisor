"""Cost / latency model for per-token vs dedicated-GPU serving shapes.

Stdlib only. All money in USD, all times in minutes unless suffixed _s.
"""

from dataclasses import dataclass, field

from .rates import (
    DAYS_PER_MONTH,
    GPU_RATES_PER_MINUTE,
    MINUTES_PER_DAY,
    SCALE_DOWN_DELAY_MINUTES,
)


@dataclass
class Workload:
    requests_per_day: float
    avg_input_tokens: float
    avg_output_tokens: float
    active_minutes_per_day: float  # minutes with traffic, total across bursts
    bursts_per_day: float  # evenly spaced bursts totalling active_minutes_per_day
    latency_target_s: float
    cold_start_s: float = 60.0
    api_input_usd_per_1m: float = 0.10  # example: GPT OSS 120B on Baseten Model APIs
    api_output_usd_per_1m: float = 0.50

    def __post_init__(self):
        if self.requests_per_day < 0 or self.avg_input_tokens < 0 or self.avg_output_tokens < 0:
            raise ValueError("requests and token volumes must be non-negative")
        if not (0 < self.active_minutes_per_day <= MINUTES_PER_DAY):
            raise ValueError("active_minutes_per_day must be in (0, 1440]")
        if self.bursts_per_day < 1:
            raise ValueError("bursts_per_day must be >= 1")
        if self.latency_target_s <= 0:
            raise ValueError("latency_target_s must be positive")


@dataclass
class ShapeCost:
    label: str
    monthly_usd: float
    notes: list = field(default_factory=list)


def monthly_model_api_cost(w: Workload) -> float:
    """Per-token Model API monthly cost."""
    daily = (
        w.requests_per_day * w.avg_input_tokens * w.api_input_usd_per_1m / 1_000_000
        + w.requests_per_day * w.avg_output_tokens * w.api_output_usd_per_1m / 1_000_000
    )
    return daily * DAYS_PER_MONTH


def billed_minutes_per_day(w: Workload) -> float:
    """Minutes per day a replica is billed under scale-to-zero autoscaling.

    Bursts are evenly spaced. Each burst bills for its own duration plus the
    scale-down tail, capped so billed time never exceeds the gap before the
    next burst (idle gaps under the delay bill in full, never double-counted).
    """
    burst_minutes = w.active_minutes_per_day / w.bursts_per_day
    gap_minutes = MINUTES_PER_DAY / w.bursts_per_day
    billed_per_burst = min(burst_minutes + SCALE_DOWN_DELAY_MINUTES, gap_minutes)
    return billed_per_burst * w.bursts_per_day


def monthly_dedicated_cost(w: Workload, gpu: str, min_replicas: int) -> float:
    """Monthly dedicated cost: autoscaled billed minutes plus any warm floor."""
    rate = GPU_RATES_PER_MINUTE[gpu]
    autoscaled = billed_minutes_per_day(w) * DAYS_PER_MONTH
    warm_floor = min_replicas * MINUTES_PER_DAY * DAYS_PER_MONTH
    billed = max(autoscaled, warm_floor)
    return billed * rate


def cold_start_fits(w: Workload) -> bool:
    """True if a scale-from-zero cold start fits inside the latency target."""
    return w.cold_start_s <= w.latency_target_s


def crossover_utilization(w: Workload, gpu: str):
    """Billed fraction of the month at which dedicated == per-token cost.

    Returns None if per-token cost is zero (nothing to cross over).
    """
    api = monthly_model_api_cost(w)
    if api <= 0:
        return None
    rate = GPU_RATES_PER_MINUTE[gpu]
    minutes_at_crossover = api / rate
    total_minutes = MINUTES_PER_DAY * DAYS_PER_MONTH
    return minutes_at_crossover / total_minutes


def compare_shapes(w: Workload, gpu: str):
    """All shapes for one GPU tier, as ShapeCost objects."""
    shapes = [
        ShapeCost(
            "Per-token Model API",
            monthly_model_api_cost(w),
            ["Pay per token; no idle cost; no cold start."],
        )
    ]
    for mr in (0, 1, 2):
        notes = []
        if mr == 0:
            notes.append(
                f"Scale-to-zero with {SCALE_DOWN_DELAY_MINUTES}-min scale-down delay modelled."
            )
            if not cold_start_fits(w):
                notes.append(
                    f"Cold start ({w.cold_start_s:.0f}s assumed) exceeds latency target "
                    f"({w.latency_target_s:.0f}s) — first request after idle waits or retries."
                )
        else:
            notes.append(f"{mr} warm replica(s) floor the bill at {mr}x always-on.")
        shapes.append(
            ShapeCost(f"Dedicated {gpu}, min_replicas={mr}", monthly_dedicated_cost(w, gpu, mr), notes)
        )
    return shapes
