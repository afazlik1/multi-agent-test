"""Synthetic tests that do not load the experiment objective."""
import json
import unittest
from workers.gradient.algorithm import optimize


class BoundedGradientTests(unittest.TestCase):
    def run_worker(self, budget, shared=None):
        calls = []
        def bowl(x, y):
            self.assertTrue(-5 <= x <= 5 and -5 <= y <= 5)
            calls.append((x, y))
            return -(x - 0.75) ** 2 - (y + 0.5) ** 2
        result = optimize(bowl, budget, 27, shared or [])
        self.assertEqual(len(calls), budget)
        self.assertEqual(len(result['observations']), budget)
        previous = 0
        for restart in result['diagnostics']['restarts']:
            self.assertEqual(restart['start_call_count'], previous)
            used = restart['end_call_count'] - previous
            self.assertGreater(used, 0)
            self.assertLessEqual(used, restart['evaluation_allowance'])
            self.assertLessEqual(used, 30)
            previous = restart['end_call_count']
        self.assertEqual(previous, budget)
        json.dumps(result, allow_nan=False)
        return result

    def test_budgets_bounds_and_determinism(self):
        for budget in [0, 1, 2, 3, 4, 5, 6, 29, 30, 31, 150]:
            with self.subTest(budget=budget):
                shared = [{'x': 5, 'y': -5, 'value': -10}]
                self.assertEqual(self.run_worker(budget, shared), self.run_worker(budget, shared))

    def test_multiple_restarts_and_independent_exploration(self):
        result = self.run_worker(120, [{'x': 5, 'y': 5, 'value': -1}])
        restarts = result['diagnostics']['restarts']
        self.assertGreaterEqual(len(restarts), 4)
        self.assertEqual(restarts[0]['source'], 'shared')
        self.assertEqual(restarts[1]['source'], 'random')
        tiny = self.run_worker(2, [{'x': 5, 'y': 5, 'value': -1}])
        self.assertEqual([r['source'] for r in tiny['diagnostics']['restarts']], ['shared', 'random'])

    def test_gradient_steps_improve_bowl(self):
        result = self.run_worker(90, [{'x': 4, 'y': -4, 'value': -100}])
        first = result['observations'][0]['value']
        best = max(row['value'] for row in result['observations'])
        self.assertGreater(best, first + 10)
        self.assertGreater(best, -0.1)
        self.assertGreater(sum(r['accepted_steps'] for r in result['diagnostics']['restarts']), 0)

    def test_rejects_invalid_budget(self):
        for budget in [-1, 1.5, True]:
            with self.assertRaises(ValueError):
                optimize(lambda x, y: 0, budget, 1, [])


if __name__ == '__main__':
    unittest.main()
