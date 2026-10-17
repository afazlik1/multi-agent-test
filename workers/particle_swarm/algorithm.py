"""Budget-exact particle swarm with declining inertia for bounded maximization."""
import numpy as np


def optimize(evaluate, budget, seed, shared):
    if isinstance(budget, (bool, np.bool_)) or not isinstance(budget, (int, np.integer)) or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    rng = np.random.default_rng(seed)
    count = min(10, budget)
    parameters = {
        "n_particles": int(count), "budget": int(budget), "seed": int(seed),
        "inertia_start": 0.9, "inertia_end": 0.4,
        "c1": 1.5, "c2": 1.5, "velocity_cap": 2.0,
        "bounds": [-5.0, 5.0],
    }
    observations = []
    inertia_history = []
    if count:
        positions = rng.uniform(-5.0, 5.0, size=(count, 2))
        # Reserve at least half for exploration when the population has >=2 particles.
        shared_limit = max(1, count // 2)
        used_shared = 0
        for candidate in shared or []:
            point = np.array([candidate["x"], candidate["y"]], dtype=float)
            if not np.all(np.isfinite(point)):
                continue
            positions[used_shared] = np.clip(point, -5.0, 5.0)
            used_shared += 1
            if used_shared == shared_limit:
                break
        velocities = rng.uniform(-2.0, 2.0, size=(count, 2))

        def measure(point):
            x, y = map(float, point)
            value = float(evaluate(x, y))
            observations.append({"x": x, "y": y, "value": value,
                                 "source": "particle_swarm"})
            return value

        personal_positions = positions.copy()
        personal_values = np.array([measure(point) for point in positions])
        best_index = int(np.argmax(personal_values))
        best_position = personal_positions[best_index].copy()
        best_value = float(personal_values[best_index])
        updates = budget - count
        for step in range(updates):
            # One schedule step per NEW evaluation, including partial sweeps.
            inertia = 0.9 - 0.5 * step / max(1, updates - 1)
            inertia_history.append(float(inertia))
            i = step % count
            velocities[i] = np.clip(
                inertia * velocities[i]
                + 1.5 * rng.random(2) * (personal_positions[i] - positions[i])
                + 1.5 * rng.random(2) * (best_position - positions[i]),
                -2.0, 2.0,
            )
            proposed = positions[i] + velocities[i]
            positions[i] = np.clip(proposed, -5.0, 5.0)
            velocities[i][proposed != positions[i]] = 0.0
            value = measure(positions[i])
            if value > personal_values[i]:
                personal_values[i] = value
                personal_positions[i] = positions[i].copy()
            if value > best_value:
                best_value = value
                best_position = positions[i].copy()
    return {
        "parameters": parameters,
        "observations": observations,
        "proposed_improvements": sorted(
            observations, key=lambda row: row["value"], reverse=True
        )[:3],
        "diagnostics": {"inertia_history": inertia_history,
                        "new_evaluations": len(observations)},
    }
