import numpy as np

def optimize(evaluate, budget, seed, shared):
    rng = np.random.default_rng(seed)
    bounds = np.array([[-5.0, -5.0], [5.0, 5.0]])
    n_particles = 10
    
    # Initialize population using shared data if available
    if shared:
        X = np.array([[s['x'], s['y']] for s in shared])
        # Pad or trim to n_particles
        if len(X) < n_particles:
            pad = rng.uniform(bounds[0], bounds[1], size=(n_particles - len(X), 2))
            X = np.vstack([X, pad])
        else:
            X = X[:n_particles]
    else:
        X = rng.uniform(bounds[0], bounds[1], size=(n_particles, 2))
    
    V = rng.uniform(-1.0, 1.0, size=(n_particles, 2))
    
    # Evaluate initial population
    values = np.array([evaluate(x, y) for x, y in X])
    calls = n_particles
    
    # Initialize personal and global bests
    pbest = X.copy()
    pbest_val = values.copy()
    gbest_idx = np.argmax(values)
    gbest = X[gbest_idx].copy()
    gbest_val = values[gbest_idx]
    
    # PSO parameters
    w = 0.9
    c1 = 1.5
    c2 = 1.5
    
    # Main loop
    while calls < budget:
        for i in range(n_particles):
            if calls >= budget:
                break
            
            # Update velocity
            r1 = rng.random(2)
            r2 = rng.random(2)
            V[i] = w * V[i] + c1 * r1 * (pbest[i] - X[i]) + c2 * r2 * (gbest - X[i])
            
            # Update position
            X[i] = X[i] + V[i]
            X[i] = np.clip(X[i], bounds[0], bounds[1])
            
            # Evaluate new position
            val = evaluate(X[i, 0], X[i, 1])
            calls += 1
            
            # Update personal best
            if val > pbest_val[i]:
                pbest_val[i] = val
                pbest[i] = X[i].copy()
            
            # Update global best
            if val > gbest_val:
                gbest_val = val
                gbest = X[i].copy()
    
    # Prepare observations
    observations = []
    for i in range(n_particles):
        observations.append({
            'x': float(pbest[i, 0]),
            'y': float(pbest[i, 1]),
            'value': float(pbest_val[i]),
            'source': 'collaborative' if shared else 'independent'
        })
    
    # Proposed improvements: top 3 particles
    sorted_indices = np.argsort(pbest_val)[::-1]
    proposed_improvements = []
    for idx in sorted_indices[:3]:
        proposed_improvements.append({
            'x': float(pbest[idx, 0]),
            'y': float(pbest[idx, 1]),
            'value': float(pbest_val[idx])
        })
    
    return {
        'parameters': {
            'n_particles': n_particles,
            'w': w,
            'c1': c1,
            'c2': c2,
            'budget': budget,
            'seed': seed
        },
        'observations': observations,
        'proposed_improvements': proposed_improvements
    }