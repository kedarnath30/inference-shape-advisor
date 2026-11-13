import unittest

from inference_shape_advisor.model import (
    Workload,
    billed_minutes_per_day,
    cold_start_fits,
    crossover_utilization,
    monthly_dedicated_cost,
    monthly_model_api_cost,
)
from inference_shape_advisor.rates import GPU_RATES_PER_MINUTE


def make_workload(**kw):
    base = dict(
        requests_per_day=10000,
        avg_input_tokens=500,
        avg_output_tokens=200,
        active_minutes_per_day=120,
        bursts_per_day=12,
        latency_target_s=2,
    )
    base.update(kw)
    return Workload(**base)


class TestModelApiCost(unittest.TestCase):
    def test_known_value(self):
        # 10k req/day * (500*0.10 + 200*0.50)/1e6 = 10k*150/1e6 = $1.50/day -> $45/month
        self.assertAlmostEqual(monthly_model_api_cost(make_workload()), 45.0, places=6)

    def test_zero_requests(self):
        self.assertEqual(monthly_model_api_cost(make_workload(requests_per_day=0)), 0.0)


class TestBilledMinutes(unittest.TestCase):
    def test_scale_down_tail_added(self):
        # 12 bursts of 10 min each, gaps of 120 min: billed = 12*(10+15)=300
        self.assertEqual(billed_minutes_per_day(make_workload()), 300)

    def test_gap_caps_billing(self):
        # 48 bursts of 2.5 min, gaps of 30 min: billed = 48*min(17.5,30)=840
        w = make_workload(bursts_per_day=48)
        self.assertEqual(billed_minutes_per_day(w), 840)

    def test_never_exceeds_day(self):
        w = make_workload(active_minutes_per_day=1400, bursts_per_day=100)
        self.assertLessEqual(billed_minutes_per_day(w), 1440)


class TestDedicatedCost(unittest.TestCase):
    def test_warm_floor_dominates_when_traffic_low(self):
        w = make_workload(active_minutes_per_day=60, bursts_per_day=60)
        # autoscaled billed ~ 60*(1+15)=960/day*30=28800 min; warm floor 1 replica = 43200 min
        cost0 = monthly_dedicated_cost(w, "H100", 0)
        cost1 = monthly_dedicated_cost(w, "H100", 1)
        self.assertGreater(cost1, cost0)
        self.assertAlmostEqual(cost1, 43200 * GPU_RATES_PER_MINUTE["H100"], places=6)

    def test_two_replicas_double_floor(self):
        w = make_workload(active_minutes_per_day=60, bursts_per_day=60)
        c1 = monthly_dedicated_cost(w, "H100", 1)
        c2 = monthly_dedicated_cost(w, "H100", 2)
        self.assertAlmostEqual(c2, 2 * c1, places=6)

    def test_always_on_h100_matches_published_monthly(self):
        # One warm H100 for a 30-day month: 43200 * 0.10833 = $4,679.86 (published ~$4,680)
        w = make_workload(active_minutes_per_day=1440, bursts_per_day=24)
        cost = monthly_dedicated_cost(w, "H100", 1)
        self.assertAlmostEqual(cost, 4679.86, delta=0.01)


class TestColdStartAndCrossover(unittest.TestCase):
    def test_cold_start_fits(self):
        self.assertTrue(cold_start_fits(make_workload(cold_start_s=1, latency_target_s=2)))
        self.assertFalse(cold_start_fits(make_workload(cold_start_s=60, latency_target_s=2)))

    def test_crossover_none_when_no_api_cost(self):
        self.assertIsNone(crossover_utilization(make_workload(requests_per_day=0), "H100"))

    def test_crossover_in_range(self):
        xo = crossover_utilization(make_workload(), "H100")
        self.assertIsNotNone(xo)
        self.assertGreater(xo, 0)
        self.assertLessEqual(xo, 1)


class TestValidation(unittest.TestCase):
    def test_bad_active_minutes(self):
        with self.assertRaises(ValueError):
            make_workload(active_minutes_per_day=0)

    def test_bad_latency(self):
        with self.assertRaises(ValueError):
            make_workload(latency_target_s=0)


if __name__ == "__main__":
    unittest.main()
