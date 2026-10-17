import numpy as np

def optimize(evaluate, budget, seed, shared):
    rng = np.random.default_rng(seed)
    X = []
    y = []
    
    # Process shared data
    if shared:
        for item in shared:
            x_val = np.clip(item['x'], -5.0, 5.0)
            y_val = np.clip(item['y'], -5.0, 5.0)
            X.append([x_val, y_val])
            y.append(item['value'])
    
    X = np.array(X) if X else np.empty((0, 2))
    y = np.array(y) if y else np.empty(0)
    
    # Initial random sampling
    min_init = 5
    if len(X) < min_init:
        n_init = min_init - len(X)
        init_X = rng.uniform(-5.0, 5.0, size=(n_init, 2))
        init_y = np.array([evaluate(x, y) for x, y in init_X])
        X = np.vstack([X, init_X]) if len(X) > 0 else init_X
        y = np.concatenate([y, init_y]) if len(y) > 0 else init_y
    
    # Fixed hyperparameters for stability
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
        # Solve L @ v = y_obs
        v = np.linalg.solve(L, y_obs)
        # alpha = L^{-T} v
        alpha = np.linalg.solve(L.T, v)
        
        mu = K_cand @ alpha
        
        # Compute variance: var = signal_var - K_cand @ K^{-1} @ K_cand.T
        # K^{-1} = L^{-T} L^{-1}
        # Let W = L^{-1} K_cand.T  (shape: n_obs x n_cand)
        W = np.linalg.solve(L, K_cand.T)
        # var_i = signal_var - sum_j (K_cand[i,j] * W[j,i])
        # Note: K_cand is (n_cand, n_obs), W is (n_obs, n_cand)
        # We need element-wise product summed over obs axis.
        # K_cand * W.T gives (n_cand, n_cand) if we are not careful.
        # Actually, K_cand @ W.T is (n_cand, n_cand) which is wrong.
        # We want sum over j for each i: sum_j K_cand[i,j] * W[j,i]
        # This is equivalent to np.sum(K_cand * W.T, axis=1) ? No.
        # Let's check shapes:
        # K_cand: (N, M)
        # W: (M, N)
        # We want vector of length N where out[i] = sum_j K_cand[i,j] * W[j,i]
        # This is the diagonal of K_cand @ W.T? No.
        # K_cand @ W.T is (N, N). The diagonal is sum_j K_cand[i,j] * (W.T)[j,i] = sum_j K_cand[i,j] * W[i,j].
        # Wait, W[j,i] is the element at row j, col i of W.
        # (W.T)[i,j] = W[j,i].
        # So (K_cand @ W.T)[i,i] = sum_j K_cand[i,j] * (W.T)[j,i] = sum_j K_cand[i,j] * W[i,j].
        # This is NOT what we want. We want sum_j K_cand[i,j] * W[j,i].
        # Let's re-evaluate the matrix multiplication for variance.
        # var = k(x,x) - k(x,X) K(X,X)^{-1} k(X,x)
        # k(X,x) is column vector (M, 1). k(x,X) is row vector (1, M).
        # K^{-1} = L^{-T} L^{-1}.
        # Let A = L^{-1} k(X,x). A is (M, 1).
        # Then K^{-1} k(X,x) = L^{-T} A.
        # Let B = L^{-T} A. B is (M, 1).
        # Then k(x,X) B is scalar.
        # For multiple candidates:
        # K_cand is (N, M).
        # We want V = K_cand @ (K^{-1} @ K_cand.T).
        # Let C = K_cand.T (M, N).
        # Solve L @ W = C => W = L^{-1} C (M, N).
        # Then K^{-1} C = L^{-T} W.
        # Let Z = L^{-T} W (M, N).
        # Then V = K_cand @ Z (N, N).
        # The variance for candidate i is signal_var - V[i,i].
        # So we need the diagonal of K_cand @ Z.
        
        W = np.linalg.solve(L, K_cand.T) # (M, N)
        Z = np.linalg.solve(L.T, W)      # (M, N)
        V = K_cand @ Z                   # (N, N)
        var = signal_var - np.diag(V)
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