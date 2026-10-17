import numpy as np
import json

def optimize(evaluate, budget, seed, shared):
    rng = np.random.default_rng(seed)
    observations = []
    calls = 0
    
    def eval_point(x, y):
        nonlocal calls
        if calls >= budget:
            return None
        val = evaluate(x, y)
        calls += 1
        observations.append({'x': float(x), 'y': float(y), 'value': float(val)})
        return val
    
    def gradient(x, y, h):
        xp, xm = min(5.0, x + h), max(-5.0, x - h)
        yp, ym = min(5.0, y + h), max(-5.0, y - h)
        fxp = eval_point(xp, y)
        fxm = eval_point(xm, y)
        fyp = eval_point(x, yp)
        fym = eval_point(x, ym)
        if fxp is None or fxm is None or fyp is None or fym is None:
            return None
        dx = 2 * h if -5 <= x - h and x + h <= 5 else xp - xm
        dy = 2 * h if -5 <= y - h and y + h <= 5 else yp - ym
        gx = (fxp - fxm) / dx
        gy = (fyp - fym) / dy
        return np.array([gx, gy])
    
    def line_search(x, y, fx, grad, step):
        nonlocal calls
        best_x, best_y, best_f = x, y, fx
        for _ in range(10):
            new_x = x + step * grad[0]
            new_y = y + step * grad[1]
            if new_x < -5 or new_x > 5 or new_y < -5 or new_y > 5:
                step *= 0.5
                continue
            f_new = eval_point(new_x, new_y)
            if f_new is None:
                break
            if f_new > best_f:
                best_x, best_y, best_f = new_x, new_y, f_new
            else:
                step *= 0.5
        return best_x, best_y, best_f
    
    def ascend(x, y, fx, max_iter):
        h = 0.01
        step = 0.1
        for _ in range(max_iter):
            if calls >= budget:
                break
            grad = gradient(x, y, h)
            if grad is None:
                break
            norm = np.linalg.norm(grad)
            if norm < 1e-6:
                break
            x, y, fx = line_search(x, y, fx, grad, step)
            if calls >= budget:
                break
        return x, y, fx
    
    starts = []
    if shared:
        for s in shared:
            starts.append((s['x'], s['y']))
    
    n_starts = min(5, max(1, budget // 20))
    for _ in range(n_starts):
        x = rng.uniform(-5, 5)
        y = rng.uniform(-5, 5)
        starts.append((x, y))
    
    best_x, best_y, best_val = None, None, -np.inf
    
    for sx, sy in starts:
        if calls >= budget:
            break
        fx = eval_point(sx, sy)
        if fx is None:
            break
        if fx > best_val:
            best_x, best_y, best_val = sx, sy, fx
        
        if calls >= budget:
            break
        
        max_iter = max(1, (budget - calls) // 10)
        ax, ay, af = ascend(sx, sy, fx, max_iter)
        if af > best_val:
            best_x, best_y, best_val = ax, ay, af
    
    if best_x is None:
        best_x, best_y, best_val = 0.0, 0.0, 0.0
    
    return {
        'parameters': {'x': float(best_x), 'y': float(best_y)},
        'observations': observations,
        'proposed_improvements': []
    }