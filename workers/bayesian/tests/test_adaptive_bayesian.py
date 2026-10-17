"""Synthetic contract and normalization checks for the adaptive Bayesian worker."""
import json
import unittest
import numpy as np
from workers.bayesian.algorithm import optimize


def synthetic(x, y):
    return -(.2 * x * x + 3. * y * y)


class AdaptiveBayesianTests(unittest.TestCase):
    def test_exact_fresh_budgets_and_import_deduplication(self):
        shared = [{'x': 0., 'y': 0., 'value': 0.}] * 2
        for budget in (0, 1, 4, 7):
            calls = []
            def objective(x, y):
                self.assertTrue(np.isfinite([x, y]).all())
                self.assertTrue(-5 <= x <= 5 and -5 <= y <= 5)
                calls.append((x, y))
                return synthetic(x, y)
            result = optimize(objective, budget, 17, shared)
            self.assertEqual(len(calls), budget)
            self.assertEqual(len(set(calls)), budget)
            self.assertEqual(len(result['observations']), budget)
            self.assertEqual(len(result['imported_observations']), 1)
            self.assertNotIn((0., 0.), calls)
            json.dumps(result, allow_nan=False)
        empty = optimize(synthetic, 0, 1, [])
        self.assertIsNone(empty['best_value'])
        self.assertIsNone(empty['parameters'])

    def test_reported_best_is_measured_by_this_worker(self):
        shared = [{'x': 0., 'y': 0., 'value': 1e6}]
        empty = optimize(synthetic, 0, 7, shared)
        self.assertIsNone(empty['parameters'])
        self.assertIsNone(empty['best_value'])
        result = optimize(synthetic, 8, 7, shared)
        best = max(result['observations'], key=lambda row: row['value'])
        self.assertEqual(result['best_value'], best['value'])
        self.assertEqual(result['parameters'], {'x': best['x'], 'y': best['y']})
        self.assertEqual(result['imported_observations'], shared)

    def test_adaptation_is_bounded_and_periodic(self):
        result = optimize(synthetic, 32, 4, [])
        history = result['kernel_adaptation_history']
        self.assertEqual([entry['new_evaluations'] for entry in history], [5, 17, 29])
        for entry in history:
            self.assertGreater(entry['candidates_tested'], 1)
            self.assertLessEqual(entry['training_points'], 48)
            self.assertTrue(np.isfinite(entry['log_marginal_likelihood_without_constant']))
            self.assertTrue(all(.15 <= v <= 8. for v in entry['length_scales']))
            self.assertGreater(entry['jitter'], 0)

    def test_reproducibility_and_positive_affine_output_invariance(self):
        original = optimize(synthetic, 22, 28, [])
        self.assertEqual(original, optimize(synthetic, 22, 28, []))
        transformed = optimize(lambda x, y: 13. * synthetic(x, y) + 71., 22, 28, [])
        np.testing.assert_allclose(
            [[row['x'], row['y']] for row in original['observations']],
            [[row['x'], row['y']] for row in transformed['observations']], atol=1e-12)
        self.assertEqual(original['parameters'], transformed['parameters'])

    def test_constant_outputs_and_near_coincident_imports_are_stable(self):
        shared = [{'x': 0., 'y': 1e-12 * i, 'value': 3.} for i in range(6)]
        result = optimize(lambda x, y: 3., 3, 5, shared)
        json.dumps(result, allow_nan=False)
        self.assertEqual(len(result['observations']), 3)


if __name__ == '__main__':
    unittest.main()
