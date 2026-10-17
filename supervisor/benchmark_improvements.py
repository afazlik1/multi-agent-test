"""Run reviewed algorithms in a new isolated ledger and compare with the original run."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sqlite3
from .agent_manager import execute
from .coordinator import Ledger, guidance
from .git_manager import git, publish
from .orchestrator import WORKERS, atomic
from .reviewed_algorithms import stage_reviewed


def summarize(history, worker):
    trials=[r for r in history if r['worker']==worker]
    best=max(trials,key=lambda r:r['best_value'])
    values=[p['value'] for r in trials for p in r['trajectory']]
    return {'best_x':best['best_x'],'best_y':best['best_y'],'best_value':best['best_value'],
            'evaluations':len(values),'runtime':sum(r['runtime'] for r in trials),
            'first_19':next((i+1 for i,v in enumerate(values) if v>=19),None),
            'first_19_99':next((i+1 for i,v in enumerate(values) if v>=19.99),None)}


def report(root,run,history,baseline):
    import csv
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    comparisons=[]
    for worker in WORKERS:
        old=summarize(baseline,worker);new=summarize(history,worker)
        comparisons.append({'worker':worker,'original':old,'improved':new,'change':new['best_value']-old['best_value']})
    atomic(run/'comparison.json',comparisons)
    with (run/'comparison.csv').open('w') as stream:
        writer=csv.writer(stream);writer.writerow(['worker','version','best_x','best_y','best_value','evaluations','runtime','first_19','first_19_99'])
        for row in comparisons:
            for version in ('original','improved'):
                r=row[version];writer.writerow([row['worker'],version,*[r[k] for k in ('best_x','best_y','best_value','evaluations','runtime','first_19','first_19_99')]])
    text='# Improved algorithm benchmark\n\n'
    text+='The reviewed implementations ran against the same hidden objective, bounds, seed 42, and 150 independent + 150 collaborative evaluations per method as the original experiment. The collaborative phase receives only the three best candidates from this new independent phase. No original-run candidates, known optimum, landscape, or source were given to the algorithms. The original experiment files are unchanged.\n\n'
    text+='| Method | Original best | Improved best | Change | Improved x | Improved y | Calls |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for row in comparisons:
        r=row['improved'];text+=f"| {row['worker']} | {row['original']['best_value']:.10f} | {r['best_value']:.10f} | {row['change']:+.10f} | {r['best_x']:.8f} | {r['best_y']:.8f} | {r['evaluations']} |\n"
    worse=[row['worker'] for row in comparisons if row['change'] < -1e-9]
    better=[row['worker'] for row in comparisons if row['change'] > 1e-9]
    text+=f"\nFinal-value improvements: {', '.join(better) or 'none'}. Regressions: {', '.join(worse) or 'none'}. Keep the original results as the demonstrated stronger final-value benchmark for methods that regressed.\n"
    text+='\n## Independent phase\n\n| Method | Original best | Improved best |\n|---|---:|---:|\n'
    for worker in WORKERS:
        a=next(r for r in baseline if r['worker']==worker and r['phase']=='independent')
        b=next(r for r in history if r['worker']==worker and r['phase']=='independent')
        text+=f"| {worker} | {a['best_value']:.10f} | {b['best_value']:.10f} |\n"
    text+='\n## Evaluation efficiency\n\n| Method | Version | First call ≥19 | First call ≥19.99 | Optimization seconds |\n|---|---|---:|---:|---:|\n'
    for row in comparisons:
        for version in ('original','improved'):
            r=row[version];text+=f"| {row['worker']} | {version} | {r['first_19'] or 'not reached'} | {r['first_19_99'] or 'not reached'} | {r['runtime']:.4f} |\n"
    text+='\n## Interpretation\n\nPositive changes indicate better final values; earlier threshold crossings indicate greater evaluation efficiency at that target. Runtime includes worker startup and evaluator communication, excludes model authoring and Git, and can vary with machine load. This is one seed and one original-vs-reviewed comparison, not evidence of statistical superiority. All three methods changed together, so a collaborative change can also reflect different candidates supplied by another method; per-change causal effects require ablations.\n\nReviewed source is fixed across phases: these runs test the code improvements, without Ollama rewriting or additional cloud model calls. Each worker re-evaluates or explicitly imports shared data according to its algorithm; reported best values come exclusively from its own evaluator ledger. Every logged point was independently revalidated by the supervisor.\n'
    (run/'report.md').write_text(text)
    fig,axes=plt.subplots(1,3,figsize=(15,4.5))
    for ax,worker in zip(axes,WORKERS):
        for label,rows in [('original',baseline),('improved',history)]:
            values=[p['value'] for r in rows if r['worker']==worker for p in r['trajectory']]
            ax.plot(np.arange(1,len(values)+1),np.maximum.accumulate(values),label=label)
        ax.axvline(150,color='gray',ls='--',alpha=.7);ax.set_title(worker);ax.set_xlabel('Objective evaluations');ax.set_ylabel('Best measured value');ax.legend()
    fig.tight_layout();fig.savefig(run/'convergence_comparison.png',dpi=150);plt.close(fig)
    return comparisons


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--objective',required=True);parser.add_argument('--run-id',default='improved-seed42-v1');args=parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}',args.run_id):raise ValueError('Invalid run ID')
    root=Path.cwd();worktrees=root.parent/'multi-agent-worktrees';objective=Path(args.objective).resolve()
    if git(root,'branch','--show-current')!='main':raise RuntimeError('Supervisor requires main')
    if objective.is_relative_to(root) or objective.is_relative_to(worktrees) or not any(objective.is_relative_to(Path(p)) for p in ('/Users','/private/tmp','/private/var/folders')):raise RuntimeError('Objective must be external and sandbox-protected')
    for worker,(folder,branch) in WORKERS.items():
        if git(worktrees/folder,'branch','--show-current')!=branch:raise RuntimeError('Worker branch mismatch')
    run=root/'experiments'/'runs'/args.run_id;run.mkdir(parents=True,exist_ok=True)
    config={'experiment_id':args.run_id,'seed':42,'budget_per_phase':150,'source_sha256':{w:hashlib.sha256((root/'workers'/w/'algorithm.py').read_bytes()).hexdigest() for w in WORKERS},'objective_sha256':hashlib.sha256(objective.read_bytes()).hexdigest(),'baseline_history_sha256':hashlib.sha256((root/'experiments'/'experiment_history.json').read_bytes()).hexdigest()}
    manifest=run/'config.json'
    if manifest.exists() and json.loads(manifest.read_text())!=config:raise RuntimeError('Run config changed; use a new run ID')
    atomic(manifest,config)
    spec=importlib.util.spec_from_file_location('private_benchmark',objective);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    ledger=Ledger(run/'experiments.sqlite',module.black_box_function);history=[]
    baseline=json.loads((root/'experiments'/'experiment_history.json').read_text())
    for phase in ('independent','collaborative'):
        shared=[] if phase=='independent' else guidance(history)
        def job(worker):
            folder,branch=WORKERS[worker];wt=worktrees/folder
            relative=f'workers/{worker}/runs/{args.run_id}/{phase}';directory=wt/relative;directory.mkdir(parents=True,exist_ok=True)
            stage_reviewed(root,worker,phase,directory)
            result=execute(wt,directory,ledger,worker,phase,shared)
            result['experiment_id']=args.run_id;result['source_sha256']=config['source_sha256'][worker]
            atomic(directory/'result.json',result)
            # Verify before publishing any reported numerical results.
            for point in result['trajectory']:
                if abs(module.black_box_function(point['x'],point['y'])-point['value'])>1e-9:raise RuntimeError('Objective validation failed')
            result['commit']=publish(wt,branch,[relative],f'{args.run_id}: {phase} benchmark results')
            destination=run/'workers'/worker/phase;destination.mkdir(parents=True,exist_ok=True)
            for name in ('algorithm.py','development.json'):shutil.copy2(directory/name,destination/name)
            atomic(destination/'result.json',result)
            print(worker,phase,result['best_value'],flush=True)
            return result
        with ThreadPoolExecutor(max_workers=3) as pool:history.extend(pool.map(job,WORKERS))
        atomic(run/'experiment_history.json',history)
    ledger.db.execute('CREATE TABLE IF NOT EXISTS runs (worker TEXT, phase TEXT, record_json TEXT, PRIMARY KEY(worker,phase))')
    for result in history:ledger.db.execute('INSERT OR REPLACE INTO runs VALUES (?,?,?)',(result['worker'],result['phase'],json.dumps(result)))
    ledger.db.commit();ledger.db.close()
    print(json.dumps(report(root,run,history,baseline),indent=2),flush=True)

if __name__=='__main__':main()
