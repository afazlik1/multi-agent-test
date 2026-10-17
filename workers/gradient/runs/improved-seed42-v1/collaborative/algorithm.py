"""Finite-difference ascent with bounded, independently seeded restarts."""
import numpy as np


def optimize(evaluate, budget, seed, shared):
    if isinstance(budget, bool) or not isinstance(budget, (int, np.integer)) or budget < 0:
        raise ValueError('budget must be a nonnegative integer')
    budget = int(budget)
    rng = np.random.default_rng(seed)
    observations, restarts = [], []
    settings = {'bounds': [-5.0, 5.0], 'max_evaluations_per_restart': 30,
                'difference_step': 0.001, 'initial_step': 0.25,
                'max_backtracks': 8, 'gradient_tolerance': 1e-8,
                'improvement_tolerance': 1e-12}
    candidates = []
    for point in shared or []:
        try:
            position = np.array([point['x'], point['y']], dtype=float)
            if np.all(np.isfinite(position)):
                candidates.append((float(point.get('value', -float('inf'))),
                                   np.clip(position, -5.0, 5.0)))
        except (KeyError, TypeError, ValueError):
            continue
    candidates.sort(key=lambda item: item[0], reverse=True)
    shared_index = 0
    while len(observations) < budget:
        start_calls = len(observations)
        # Alternate shared starts and independent exploration; even a small
        # budget of two leaves one evaluation for an independent start.
        use_shared = bool(candidates) and len(restarts) % 2 == 0 and shared_index < len(candidates)
        if use_shared:
            point = candidates[shared_index][1].copy()
            shared_index += 1
            source = 'shared'
        else:
            point = rng.uniform(-5.0, 5.0, size=2)
            source = 'random'
        allowance = min(settings['max_evaluations_per_restart'], budget - start_calls)
        if use_shared:
            allowance = min(allowance, max(1, (budget - start_calls) // 2))
        limit = start_calls + allowance
        start_parameters = {'x': float(point[0]), 'y': float(point[1])}

        def sample(position):
            if len(observations) >= limit:
                raise RuntimeError('restart allowance exceeded')
            position = np.clip(position, -5.0, 5.0)
            value = float(evaluate(float(position[0]), float(position[1])))
            observations.append({'x': float(position[0]), 'y': float(position[1]), 'value': value})
            return value

        value = sample(point)
        reason = 'restart_evaluation_limit'
        accepted_steps = 0
        while len(observations) < limit:
            gradient = np.zeros(2)
            complete = True
            for axis in range(2):
                if limit - len(observations) < 2:
                    complete = False
                    break
                plus, minus = point.copy(), point.copy()
                plus[axis] = min(5.0, point[axis] + settings['difference_step'])
                minus[axis] = max(-5.0, point[axis] - settings['difference_step'])
                gradient[axis] = (sample(plus) - sample(minus)) / (plus[axis] - minus[axis])
            if not complete:
                # A remaining call is still a valid boundary-safe directional probe.
                if len(observations) < limit:
                    probe = point.copy()
                    probe[0] = np.clip(point[0] + (0.001 if point[0] < 5 else -0.001), -5, 5)
                    sample(probe)
                break
            if np.linalg.norm(gradient) < settings['gradient_tolerance']:
                reason = 'stationary_gradient'
                break
            step = settings['initial_step']
            improved = False
            for _ in range(settings['max_backtracks']):
                if len(observations) >= limit:
                    break
                proposal = np.clip(point + step * gradient, -5.0, 5.0)
                if np.array_equal(proposal, point):
                    step *= 0.5
                    continue
                proposed_value = sample(proposal)
                if proposed_value > value + settings['improvement_tolerance']:
                    point, value = proposal, proposed_value
                    accepted_steps += 1
                    improved = True
                    break
                step *= 0.5
            if not improved:
                reason = ('restart_evaluation_limit' if len(observations) >= limit
                          else 'stagnation')
                break
        if len(observations) >= budget:
            reason = 'budget_exhausted'
        restarts.append({'start_call_count': start_calls, 'end_call_count': len(observations),
                         'evaluation_allowance': allowance, 'source': source,
                         'start_parameters': start_parameters,
                         'end_parameters': {'x': float(point[0]), 'y': float(point[1])},
                         'accepted_steps': accepted_steps, 'termination_reason': reason})
    best = max(observations, key=lambda row: row['value']) if observations else None
    return {'parameters': {'x': best['x'], 'y': best['y']} if best else None,
            'observations': observations, 'proposed_improvements': [],
            'diagnostics': {'settings': settings, 'evaluations': len(observations),
                            'restarts': restarts}}
