"""Synthetic-only checks of the canonical particle swarm implementation."""
import json
import unittest

from workers.particle_swarm.algorithm import optimize


class DecliningSwarmTests(unittest.TestCase):
    def run_swarm(self, budget, shared=None, seed=42):
        calls = []

        def evaluate(x, y):
            self.assertTrue(-5.0 <= x <= 5.0)
            self.assertTrue(-5.0 <= y <= 5.0)
            value = -(x - 0.3) ** 2 - (y + 0.7) ** 2
            calls.append({"x": x, "y": y, "value": value,
                          "source": "particle_swarm"})
            return value

        result = optimize(evaluate, budget, seed, shared or [])
        self.assertEqual(len(calls), budget)
        self.assertEqual(result["observations"], calls)
        self.assertEqual(result["diagnostics"]["new_evaluations"], budget)
        self.assertEqual(result["parameters"]["n_particles"], min(10, budget))
        for row in result["proposed_improvements"]:
            self.assertIn(row, calls)
        json.dumps(result, allow_nan=False)
        return result

    def test_exact_small_and_partial_budgets(self):
        shared = [{"x": i, "y": -i, "value": 1e99} for i in range(30)]
        for budget in [0, 1, 2, 9, 10, 11, 12, 23, 150]:
            for candidates in [[], shared]:
                with self.subTest(budget=budget, shared=bool(candidates)):
                    self.run_swarm(budget, candidates)

    def test_inertia_schedule_endpoints(self):
        for budget in [12, 23, 150]:
            history = self.run_swarm(budget)["diagnostics"]["inertia_history"]
            self.assertEqual(len(history), budget - 10)
            self.assertAlmostEqual(history[0], 0.9)
            self.assertAlmostEqual(history[-1], 0.4)
            self.assertTrue(all(a >= b for a, b in zip(history, history[1:])))
        self.assertEqual(self.run_swarm(11)["diagnostics"]["inertia_history"], [0.9])
        self.assertEqual(self.run_swarm(10)["diagnostics"]["inertia_history"], [])

    def test_shared_seeds_clipped_with_random_exploration(self):
        shared = [{"x": 100, "y": -100, "value": 1e99}] * 30
        result = self.run_swarm(50, shared)
        initial = result["observations"][:10]
        self.assertTrue(all((p["x"], p["y"]) == (5, -5) for p in initial[:5]))
        self.assertTrue(all(-5 < p["x"] < 5 and -5 < p["y"] < 5
                            for p in initial[5:]))
        self.assertTrue(all(p["value"] < 1e99 for p in result["observations"]))

    def test_reproducible(self):
        self.assertEqual(self.run_swarm(70), self.run_swarm(70))
        self.assertNotEqual(self.run_swarm(70), self.run_swarm(70, seed=43))

    def test_invalid_budget(self):
        for budget in [-1, 1.5, True]:
            with self.assertRaises(ValueError):
                optimize(lambda x, y: 0.0, budget, 42, [])
