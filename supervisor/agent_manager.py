"""Ollama code authoring and restricted worker execution."""
import ast
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import time
import urllib.request

MODEL = 'qwen3.8:27b-mtp-q8_0'
CONTRACT = '''Write a complete Python module for an unknown deterministic 2D black-box MAXIMIZATION on [-5,5]^2.
Use ONLY numpy and Python standard library. Never inspect files, network, processes, or objective implementation.
Required signature: optimize(evaluate, budget, seed, shared).
evaluate(x,y) returns scalar and EVERY call counts. Make exactly budget calls, always within bounds.
shared is [] in independent phase; in collaborative phase it is a list of dicts {x,y,value,source} from prior independent experiments.
You may evaluate shared candidates (counts against budget), but do not treat imported values as your own evaluations.
Return a JSON-serializable dict with parameters, observations, proposed_improvements.
No printing. No main guard. No scipy/sklearn. No objective formula. Use a seeded numpy RNG.
Fit the entire implementation in at most 220 lines. Do not include long comments or deliberation. Count NEW evaluate calls separately from shared training points. Ensure GP variance uses sum(W*W, axis=0) for W=solve(L,K_cross.T); kernel diagonal must match covariance amplitude. Respond JSON with exactly {"code":"...", "rationale":"..."}.
'''

def author(method, phase, previous=None, shared=None, feedback=None):
    tasks = {
        'bayesian': 'Implement genuine Bayesian optimization with a Gaussian Process surrogate, RBF or Matern kernel and UCB or expected improvement acquisition. Use numpy linear algebra, candidate sampling, stable jitter; avoid expensive hyperparameter fitting. Include exploration. Normalize observations and adapt bounded anisotropic kernel length scales periodically using marginal likelihood; report selected scales.',
        'gradient': 'Implement multi-start numerical gradient ascent with central differences and bounded backtracking. Every finite difference and line-search call counts. Use small adaptive steps and multiple starts to handle local optima. Cap EVERY restart at 30 new calls including finite differences and line search, restart on stagnation, and reserve random starts after shared candidates.',
        'particle_swarm': 'Implement genuine particle swarm optimization with velocities, personal best and global best, inertia and cognitive/social terms. Keep a moderate population and clip boundaries. Decline inertia linearly from 0.9 to 0.4 across velocity updates, cap velocities, and report the inertia schedule.'
    }
    if previous is None:
        baseline=Path(__file__).resolve().parent.parent/'workers'/method/'algorithm.py'
        if baseline.exists():
            previous=baseline.read_text()
    prompt = CONTRACT + '\n' + tasks[method] + '\nPhase: ' + phase
    if previous:
        prompt += '\nImprove your previous implementation:\n' + previous
    if shared:
        prompt += '\nSupervisor guidance: use these measured candidates to improve your assigned algorithm while preserving exploration: ' + json.dumps(shared)
    if feedback:
        prompt += '\nPrevious attempt failed; fix this error: ' + feedback
    payload = {'model': MODEL, 'prompt':prompt, 'stream':False, 'think':False, 'format':'json', 'keep_alive':'30m', 'options':{'temperature':0.2, 'seed':42, 'num_ctx':16384, 'num_predict':6500}}
    req = urllib.request.Request('http://127.0.0.1:11434/api/generate', data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=1200) as response:
        result=json.load(response)
    answer=json.loads(result['response'])
    ast.parse(answer['code'])
    return answer, {k:result.get(k) for k in ('model','total_duration','prompt_eval_count','eval_count')}

def profile(worktree):
    # Deny private user/temp reads, all writes and networking. Keep OS loader access.
    import numpy
    packages = str(Path(numpy.__file__).parent.parent)
    numpy_dir = str(Path(numpy.__file__).parent)
    return f'''(version 1)
(allow default)
(deny network*)
(deny file-write*)
(deny file-read-data (subpath "/private/tmp") (subpath "/private/var/folders")
(require-all (subpath "/Users")
(require-not (literal "{packages}"))
(require-not (subpath "{numpy_dir}"))
(require-not (subpath "{worktree}"))))
'''

RUNNER = '''import json,sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).parent))\nsys.path.insert(0,NUMPY_PACKAGES)\nfrom algorithm import optimize\ndef evaluate(x,y):\n print(json.dumps({"evaluate":[float(x),float(y)]}),flush=True)\n response=json.loads(sys.stdin.readline())\n if "error" in response: raise RuntimeError(response["error"])\n return response["value"]\nconfig=json.loads(sys.stdin.readline())\nresult=optimize(evaluate,config["budget"],config["seed"],config["shared"])\nprint(json.dumps({"result":result}),flush=True)\n'''

def execute(worktree, directory, ledger, worker, phase, shared, seed=42, timeout=300):
    runner=directory/'runner.py'; runner.write_text(RUNNER.replace('NUMPY_PACKAGES', repr(str(Path(__import__('numpy').__file__).parent.parent))))
    policy=directory/'sandbox.sb'; policy.write_text(profile(worktree))
    env={'PATH':'/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE':'1', 'OPENBLAS_NUM_THREADS':'1', 'OMP_NUM_THREADS':'1', 'VECLIB_MAXIMUM_THREADS':'1'}
    process=subprocess.Popen(['/usr/bin/sandbox-exec','-f',str(policy),sys.executable,'-I','-u',str(runner)], cwd=directory, env=env, stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    events=queue.Queue()
    def pump():
        for line in process.stdout: events.put(line)
        events.put(None)
    threading.Thread(target=pump,daemon=True).start()
    existing=ledger.rows(worker,phase)
    process.stdin.write(json.dumps({'budget':150,'seed':seed,'shared':shared})+'\n');process.stdin.flush()
    start=time.monotonic(); replay=0; result=None
    try:
        while True:
            remaining=timeout-(time.monotonic()-start)
            if remaining<=0: raise TimeoutError('Worker execution timeout')
            line=events.get(timeout=remaining)
            if line is None: break
            item=json.loads(line)
            if 'evaluate' in item:
                x,y=item['evaluate']
                if replay<len(existing):
                    _,a,b,value,_=existing[replay]
                    if abs(x-a)>1e-12 or abs(y-b)>1e-12: raise RuntimeError('Recovery replay diverged; refusing extra budget')
                    replay+=1
                else:
                    value=ledger.evaluate(worker,phase,x,y,time.monotonic()-start)
                process.stdin.write(json.dumps({'value':value})+'\n');process.stdin.flush()
            elif 'result' in item: result=item['result']
            else: raise ValueError('Invalid worker protocol')
        process.wait(timeout=5)
        if process.returncode or result is None:
            raise RuntimeError(process.stderr.read()[-6000:])
        rows=ledger.rows(worker,phase)
        if len(rows)!=150: raise RuntimeError(f'Worker made {len(rows)} NEW objective calls; must make exactly 150 NEW calls. len(shared)={len(shared)} imported observations do NOT count. Track calls separately or set observation target to budget+len(shared).')
        best=max(rows,key=lambda r:r[3])
        return {'worker':worker,'phase':phase,'seed':seed,'best_x':best[1],'best_y':best[2],'best_value':best[3],'evaluations':len(rows),'runtime':max(r[4] for r in rows),'trajectory':[dict(zip(['evaluation','x','y','value','elapsed'],r)) for r in rows], 'details':result,'supervisor_instructions':shared}
    finally:
        if process.poll() is None: process.kill()
        process.wait()
        for stream in (process.stdin, process.stdout, process.stderr):
            stream.close()
