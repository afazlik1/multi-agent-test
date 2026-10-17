"""Supervisor-only validation, comparison and plotting."""
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate(root,history,objective):
    reports=root/'reports';plots=root/'visualizations'
    reports.mkdir(exist_ok=True);plots.mkdir(exist_ok=True)
    for result in history:
        for row in result['trajectory']:
            if abs(objective(row['x'],row['y'])-row['value'])>1e-9: raise RuntimeError('Independent validation failed')
    # Barrier-only metadata writes; evaluations remain exclusively owned by Ledger.
    import sqlite3
    db=sqlite3.connect(root/'experiments'/'experiments.sqlite')
    db.execute('CREATE TABLE IF NOT EXISTS runs (experiment_id TEXT, worker TEXT, phase TEXT, branch TEXT, commit_sha TEXT, record_json TEXT, PRIMARY KEY(experiment_id,worker,phase))')
    branches={'bayesian':'agent/bayesian-optimization','gradient':'agent/gradient-optimization','particle_swarm':'agent/particle-swarm-optimization'}
    for result in history:
        db.execute('INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?)',('local-blackbox-001',result['worker'],result['phase'],branches[result['worker']],result['commit'],json.dumps(result)))
    db.commit();db.close()
    fields=['worker','phase','best_x','best_y','best_value','evaluations','runtime','commit']
    with (root/'experiments'/'aggregated_results.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(history)
    header='| Algorithm | Phase | Best x | Best y | Best value | Evaluations | Runtime (s) | Error to 20 |\n|---|---|---:|---:|---:|---:|---:|---:|\n'
    table=header+'\n'.join('| {worker} | {phase} | {best_x:.8f} | {best_y:.8f} | {best_value:.8f} | {evaluations} | {runtime:.3f} | {error:.8f} |'.format(**r,error=20-r['best_value']) for r in history)
    best=max(history,key=lambda r:r['best_value'])
    text='# Multi-agent optimization report\n\n## Executive summary\n\n'
    text+=f"Best measured result: {best['worker']} ({best['phase']}), f={best['best_value']:.8f} at ({best['best_x']:.8f}, {best['best_y']:.8f}). All reported evaluations were independently recalculated by the supervisor.\n\n## Algorithm comparison\n\n"+table
    text+='\n\n## Independent vs. collaborative results\n\n'
    for name in sorted({r['worker'] for r in history}):
        rows=[r for r in history if r['worker']==name];ind=rows[0]
        if len(rows)>1:
            coll=rows[1];text+=f"- {name}: independent {ind['best_value']:.8f}; collaboration phase {coll['best_value']:.8f}; retained-best improvement {max(0,coll['best_value']-ind['best_value']):.8f}. Total 300 evaluations.\n"
    text+='\n## Supervisor observations\n\nIndependent findings were withheld until all three workers completed and pushed. The supervisor then shared measured best candidates, recommending local refinement for gradient ascent, surrogate candidate enrichment for Bayesian optimization, and partial swarm initialization near promising points. Workers authored a revised implementation through local Ollama for the collaborative phase.\n\n'
    for r in history:
        text+=f"### {r['worker']} / {r['phase']}\n\nCommit: `{r['commit']}`. Parameters and worker observations:\n\n```json\n{json.dumps(r['details'],indent=2)}\n```\n\n"
    text+='## Evaluation efficiency and retained final performance\n\n'
    text+='| Method | Retained best | Total calls | Optimization seconds | First call >= 15 | First call >= 19 |\n|---|---:|---:|---:|---:|---:|\n'
    for name in sorted({r['worker'] for r in history}):
        trials=[r for r in history if r['worker']==name]
        values=[p['value'] for r in trials for p in r['trajectory']]
        first=lambda threshold: next((i+1 for i,v in enumerate(values) if v>=threshold), 'not reached')
        text+=f"| {name} | {max(values):.8f} | {len(values)} | {sum(r['runtime'] for r in trials):.3f} | {first(15)} | {first(19)} |\n"
    text+='\nFixed thresholds support evaluation-efficiency comparisons without conflating model-generation time with optimization time. Local model authoring timing and token counts are retained in worker development/repair metadata. Phase two restarts each revised algorithm with shared candidates and the same seed rather than continuing in-memory optimizer state.\n\n'
    text+='## Final conclusions\n\nThis is one seeded run per method, not a statistical comparison. Improvements in the second phase coincide with sharing candidates, an additional budget, and code revisions; without equal-budget independent continuation controls they cannot be attributed causally to collaboration. Similar final values may indicate convergence to local peaks, but the objective error alone does not prove a worker was trapped.\n\nEvaluation efficiency is shown by the full best-so-far curves. Runtime covers optimization and evaluator IPC, excluding local model authoring and Git publication. Imported candidate values never count as worker observations unless re-evaluated. The benchmark reference maximum is used only here for final error calculations.\n\nRecommended next experiments: multiple paired seeds, independent 300-evaluation controls, fixed-code collaboration ablations, and acquisition/gradient/swarm parameter sweeps.\n'
    (reports/'optimization_report.md').write_text(text)
    for phase in ('independent','collaborative'):
        (reports/(phase+'_comparison.md')).write_text('# '+phase.title()+' comparison\n\n'+header+'\n'.join(line for line,r in zip(table.splitlines()[2:],history) if r['phase']==phase)+'\n')
    (reports/'supervisor_decisions.md').write_text('# Supervisor decisions\n\n1. Use local Qwen authoring and three isolated execution processes.\n2. Enforce 150 evaluations per phase in a single-writer SQLite ledger.\n3. Complete the independent barrier before sharing measured candidates.\n4. Validate every recorded value independently before publication.\n5. Integrate only implementations that completed their full budgets.\n6. Treat collaboration effects as descriptive, pending control experiments.\n')
    plt.figure(figsize=(9,5))
    for name in sorted({r['worker'] for r in history}):
        rows=[r for r in history if r['worker']==name];values=[p['value'] for r in rows for p in r['trajectory']]
        plt.plot(np.arange(1,len(values)+1),np.maximum.accumulate(values),label=name)
    plt.axvline(150,color='gray',linestyle='--');plt.xlabel('Objective evaluations');plt.ylabel('Best value');plt.legend();plt.tight_layout();plt.savefig(plots/'convergence_comparison.png');plt.close()
    grid=np.linspace(-5,5,250);X,Y=np.meshgrid(grid,grid);Z=objective(X,Y)
    for trajectories,filename in [(False,'objective_contour.png'),(True,'optimization_trajectories.png')]:
        plt.figure(figsize=(8,7));plt.contourf(X,Y,Z,40,cmap='viridis');plt.colorbar(label='Objective')
        for name in sorted({r['worker'] for r in history}):
            rows=[r for r in history if r['worker']==name];bestrow=max(rows,key=lambda r:r['best_value'])
            if trajectories:
                points=[p for r in rows for p in r['trajectory']];plt.plot([p['x'] for p in points],[p['y'] for p in points],alpha=.25,lw=.5)
            plt.scatter(bestrow['best_x'],bestrow['best_y'],label=name,edgecolors='white',s=70)
        plt.xlabel('x');plt.ylabel('y');plt.legend();plt.tight_layout();plt.savefig(plots/filename);plt.close()
    names=sorted({r['worker'] for r in history});fig,axes=plt.subplots(1,3,figsize=(15,5))
    for ax,key,title in zip(axes,['best_value','runtime','error'],['Phase best value','Optimization runtime (s)','Error to reference maximum']):
        for i,phase in enumerate(('independent','collaborative')):
            values=[]
            for name in names:
                match=[r for r in history if r['worker']==name and r['phase']==phase]
                values.append((20-match[0]['best_value'] if key=='error' else match[0][key]) if match else np.nan)
            ax.bar(np.arange(len(names))+.35*i,values,width=.35,label=phase)
        ax.set_xticks(np.arange(len(names))+.175);ax.set_xticklabels(names,rotation=20);ax.set_title(title);ax.legend()
    fig.tight_layout();fig.savefig(plots/'algorithm_comparison.png');plt.close(fig)
