import numpy as np

def optimize(evaluate, budget, seed, shared):
    rng = np.random.default_rng(seed)
    X = []
    y = []
    if shared:
        for item in shared:
            X.append([np.clip(item['x'], -5.0, 5.0), np.clip(item['y'], -5.0, 5.0)])
            y.append(item['value'])
    X = np.array(X) if X else np.empty((0, 2))
    y = np.array(y) if y else np.empty(0)
    n_init = 5
    if len(X) < n_init:
        n_add = n_init - len(X)
        init_X = rng.uniform(-5.0, 5.0, size=(n_add, 2))
        init_y = np.array([evaluate(x, y) for x, y in init_X])
        X = np.vstack([X, init_X]) if len(X) > 0 else init_X
        y = np.concatenate([y, init_y]) if len(y) > 0 else init_y
    length_scale = 1.0
    signal_var = 1.0
    noise_var = 1e-6
    beta = 2.0
    def matern_kernel(X1, X2):
        diff = X1[:, np.newaxis, :] - X2[np.newaxis, :, :]
        dist = np.sqrt(np.sum(diff**2, axis=-1))
        r = dist / length_scale
        return np.exp(-r * np.sqrt(3)) * (1 + r * np.sqrt(3))
    def update_gp(X_obs, y_obs):
        K = matern_kernel(X_obs, X_obs)
        K += (noise_var + 1e-8) * np.eye(len(X_obs))
        try:
            L = np.linalg.cholesky(K)
        except np.linalg.LinAlgError:
            K += 1e-6 * np.eye(len(X_obs))
            L = np.linalg.cholesky(K)
        return L
    def acquisition_function(X_cand, X_obs, y_obs, L):
        K_cand = matern_kernel(X_cand, X_obs)
        v = np.linalg.solve(L, y_obs)
        alpha = np.linalg.solve(L.T, v)
        mu = K_cand @ alpha
        W = np.linalg.solve(L, K_cand.T)
        var = signal_var - np.sum(W * W, axis=0)
        var = np.maximum(var, 1e-10)
        std = np.sqrt(var)
        return mu + beta * std
    n_candidates = 2000
    while len(X) < budget:
        L = update_gp(X, y)
        X_cand = rng.uniform(-5.0, 5.0, size=(n_candidates, 2))
        acq_vals = acquisition_function(X_cand, X, y, L)
        best_idx = np.argmax(acq_vals)
        x_new = X_cand[best_idx]
        y_new = evaluate(x_new[0], x_new[1])
        X = np.vstack([X, x_new])
        y = np.append(y, y_new)
    best_idx = np.argmax(y)
    best_x = X[best_idx]
    observations = [{'x': float(x), 'y': float(y), 'value': float(v)} for x, y, v in zip(X[:, 0], X[:, 1], y)]
    return {
        'parameters': {'x': float(best_x[0]), 'y': float(best_x[1])},
        'observations': observations,
        'proposed_improvements': []
    }