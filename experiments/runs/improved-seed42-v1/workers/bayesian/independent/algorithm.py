"""Bounded, normalized Gaussian-process Bayesian optimization (maximization)."""
import math
import numpy as np


def _triangular(matrix, rhs, transpose=False):
    """Small dense triangular solve, also supporting multiple right-hand sides."""
    answer = np.array(rhs, dtype=float, copy=True)
    order = range(len(matrix) - 1, -1, -1) if transpose else range(len(matrix))
    for i in order:
        if transpose:
            answer[i] = (answer[i] - np.sum(matrix[i + 1:, i].reshape((-1,) + (1,) * (answer.ndim - 1)) * answer[i + 1:], axis=0)) / matrix[i, i]
        else:
            answer[i] = (answer[i] - np.sum(matrix[i, :i].reshape((-1,) + (1,) * (answer.ndim - 1)) * answer[:i], axis=0)) / matrix[i, i]
    return answer


def _kernel(left, right, scales):
    distance = np.sqrt(np.sum(((left[:, None] - right[None, :]) / scales) ** 2, axis=2))
    radius = math.sqrt(3) * distance
    return (1 + radius) * np.exp(-radius)


def _fit(points, values, scales):
    centered = values - np.mean(values)
    scale = np.std(centered)
    normalized = centered / scale if scale > 0 else centered
    covariance = _kernel(points, points, scales)
    for jitter in (1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3):
        try:
            factor = np.linalg.cholesky(covariance + jitter * np.eye(len(points)))
            transformed = _triangular(factor, normalized)
            score = -.5 * float(transformed @ transformed) - float(np.log(np.diag(factor)).sum())
            return factor, _triangular(factor, transformed, transpose=True), score, jitter
        except np.linalg.LinAlgError:
            continue
    raise RuntimeError('Unable to stabilize Gaussian process covariance')


def optimize(evaluate, budget, seed, shared):
    """Spend exactly budget fresh calls; shared values are imported training data."""
    if isinstance(budget, bool) or not isinstance(budget, (int, np.integer)) or budget < 0:
        raise ValueError('budget must be a nonnegative integer')
    rng = np.random.default_rng(seed)
    imported = []
    seen = set()
    for item in shared or []:
        try:
            point = (float(item['x']), float(item['y']))
            value = float(item['value'])
        except (KeyError, TypeError, ValueError):
            continue
        if not all(math.isfinite(v) for v in (*point, value)) or any(abs(v) > 5 for v in point):
            continue
        if point not in seen:
            imported.append({'x': point[0], 'y': point[1], 'value': value})
            seen.add(point)
    observations = []
    history = []
    scales = np.array([1., 1.])
    settings = {'kernel': 'matern_3_2', 'normalize_outputs': True,
                'length_scale_bounds': [.15, 8.], 'adaptation_interval': 12,
                'max_training_points': 48, 'candidate_count': 256, 'ucb_beta': 2.0}
    all_rows = list(imported)
    for call in range(budget):
        if len(all_rows) < 5:
            candidate = rng.uniform(-5., 5., 2)
        else:
            # Keep the strongest half and most recent remainder for bounded cubic cost.
            ranked = sorted(range(len(all_rows)), key=lambda i: (-all_rows[i]['value'], i))
            selected = ranked[:24]
            selected += [i for i in range(len(all_rows) - 1, -1, -1) if i not in selected][:48-len(selected)]
            training = [all_rows[i] for i in selected]
            points = np.array([[row['x'], row['y']] for row in training])
            values = np.array([row['value'] for row in training])
            if not history or call - history[-1]['new_evaluations'] >= 12:
                candidates = [scales.copy()]
                for axis in range(2):
                    for multiplier in (.5, 2.):
                        proposal = scales.copy()
                        proposal[axis] *= multiplier
                        candidates.append(np.clip(proposal, .15, 8.))
                candidates.extend([np.array([v, v]) for v in (.3, 2., 6.)])
                fits = [_fit(points, values, proposal) for proposal in candidates]
                winner = max(range(len(fits)), key=lambda i: fits[i][2])
                scales = candidates[winner]
                factor, alpha, score, jitter = fits[winner]
                history.append({'new_evaluations': call, 'training_points': len(points),
                                'length_scales': scales.tolist(), 'log_marginal_likelihood_without_constant': score,
                                'jitter': jitter, 'candidates_tested': len(candidates)})
            else:
                factor, alpha, _, _ = _fit(points, values, scales)
            candidates = rng.uniform(-5., 5., (256, 2))
            best = np.array([all_rows[ranked[0]]['x'], all_rows[ranked[0]]['y']])
            candidates[:64] = np.clip(best + rng.normal(size=(64, 2)) * scales * .35, -5., 5.)
            cross = _kernel(points, candidates, scales)
            projection = _triangular(factor, cross)
            acquisition = np.sum(cross * alpha[:, None], axis=0) + 2. * np.sqrt(np.maximum(1. - np.sum(projection ** 2, axis=0), 0.))
            for i, point in enumerate(candidates):
                if tuple(point) in seen:
                    acquisition[i] = -np.inf
            candidate = candidates[int(np.argmax(acquisition))]
        # Random fallback also covers clipped duplicate local candidates.
        while tuple(candidate) in seen:
            candidate = rng.uniform(-5., 5., 2)
        value = float(evaluate(float(candidate[0]), float(candidate[1])))
        if not math.isfinite(value):
            raise ValueError('evaluate must return finite objective values')
        row = {'x': float(candidate[0]), 'y': float(candidate[1]), 'value': value}
        observations.append(row)
        all_rows.append(row)
        seen.add(tuple(candidate))
    best = max(observations, key=lambda row: row['value']) if observations else None
    return {'parameters': {'x': best['x'], 'y': best['y']} if best else None,
            'best_value': best['value'] if best else None,
            'observations': observations, 'imported_observations': imported,
            'settings': settings, 'kernel_adaptation_history': history,
            'proposed_improvements': []}
