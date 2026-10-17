"""Run: python3 -m supervisor.orchestrator --objective /private/path/objective.py"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import time
from .agent_manager import author, execute
from .coordinator import Ledger, guidance
from .git_manager import git, publish

WORKERS={'bayesian':('bayesian','agent/bayesian-optimization'), 'gradient':('gradient','agent/gradient-optimization'), 'particle_swarm':('particle-swarm','agent/particle-swarm-optimization')}

def atomic(path,data):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data,indent=2));temporary.replace(path)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--objective',required=True);parser.add_argument('--worktrees',default='../multi-agent-worktrees');parser.add_argument('--algorithm-source',choices=('ollama','reviewed'),default='ollama');args=parser.parse_args()
    root=Path.cwd();worktrees=Path(args.worktrees).resolve();objective_path=Path(args.objective).resolve()
    if git(root,'branch','--show-current')!='main': raise RuntimeError('Supervisor must run on main')
    if objective_path.is_relative_to(root) or objective_path.is_relative_to(worktrees): raise RuntimeError('Hidden objective must be outside repositories')
    if not any(objective_path.is_relative_to(Path(base)) for base in ('/Users','/private/tmp','/private/var/folders')): raise RuntimeError('Objective must reside under a sandbox-protected private directory')
    for name,(folder,branch) in WORKERS.items():
        if git(worktrees/folder,'branch','--show-current')!=branch: raise RuntimeError('Incorrect worktree')
        if not git(root,'ls-remote','origin','refs/heads/'+branch): raise RuntimeError('Worker branch not published')
    spec=importlib.util.spec_from_file_location('private_objective',objective_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    ledger=Ledger(root/'experiments'/'experiments.sqlite',module.black_box_function)
    history=[]
    for phase in ('independent','collaborative'):
        shared=[] if phase=='independent' else guidance([r for r in history if r['phase']=='independent'])
        jobs=[]
        # Serialize model authoring to bound unified-memory use; experiment processes run in parallel.
        for worker,(folder,branch) in WORKERS.items():
            wt=worktrees/folder;directory=wt/'workers'/worker/phase;directory.mkdir(parents=True,exist_ok=True)
            if args.algorithm_source=='reviewed':
                from .reviewed_algorithms import stage_reviewed
                stage_reviewed(root,worker,phase,directory)
            result_path=directory/'result.json'
            if result_path.exists():
                result=json.loads(result_path.read_text());publish(wt,branch,['workers/'+worker+'/'+phase],phase+' '+worker+' results');result['commit']=git(wt,'log','-1','--format=%H','--','workers/'+worker+'/'+phase+'/result.json');history.append(result);continue
            algorithm=directory/'algorithm.py'
            if not algorithm.exists():
                previous=(wt/'workers'/worker/'independent'/'algorithm.py').read_text() if phase=='collaborative' else None
                print('Authoring',worker,phase,flush=True)
                answer,metadata=author(worker,phase,previous,shared)
                algorithm.write_text(answer['code']);atomic(directory/'development.json',{'rationale':answer['rationale'],'ollama':metadata,'phase':phase,'guidance':shared})
            # Test protocol/budget against a disposable synthetic fixture, never the benchmark.
            if not (directory/'preflight.json').exists():
                for attempt in range(4):
                    try:
                        fixture=Ledger(':memory:',lambda x,y: -(x*x+y*y))
                        execute(wt,directory,fixture,worker,phase,shared,timeout=240)
                        atomic(directory/'preflight.json',{'passed':True,'fixture':'synthetic quadratic; not benchmark data','attempts':attempt+1})
                        break
                    except Exception as exc:
                        atomic(directory/f'preflight_failure_{attempt}.json',{'error':str(exc)})
                        if args.algorithm_source=='reviewed' or attempt==3: raise
                        shutil.copy2(algorithm,directory/f'preflight_failed_{attempt}.py')
                        print('Repairing preflight',worker,phase,str(exc)[-250:],flush=True)
                        answer,metadata=author(worker,phase,algorithm.read_text(),shared,str(exc))
                        algorithm.write_text(answer['code'])
                        atomic(directory/f'repair_{attempt}.json',{'rationale':answer['rationale'],'ollama':metadata})
            jobs.append((worker,wt,directory,branch))
        def run(job):
            worker,wt,directory,branch=job
            print('Running',worker,phase,flush=True)
            try:
                result=execute(wt,directory,ledger,worker,phase,shared)
            except Exception as exc:
                atomic(directory/'failure.json',{'error':str(exc),'phase':phase})
                # Never silently restart a spent budget with a different algorithm.
                if args.algorithm_source=='reviewed' or ledger.rows(worker,phase): raise
                answer,metadata=author(worker,phase,(directory/'algorithm.py').read_text(),shared,str(exc))
                (directory/'algorithm.py').write_text(answer['code'])
                atomic(directory/'repair.json',{'rationale':answer['rationale'],'ollama':metadata})
                result=execute(wt,directory,ledger,worker,phase,shared)
            atomic(directory/'result.json',result)
            result['commit']=publish(wt,branch,['workers/'+worker+'/'+phase],phase+' '+worker+' implementation and measured results')
            print('Published',worker,phase,result['best_value'],result['commit'],flush=True)
            return result
        with ThreadPoolExecutor(max_workers=3) as pool:
            history.extend(list(pool.map(run,jobs)))
        atomic(root/'experiments'/'experiment_history.json',history)
        git(root,'fetch','origin')
        from .report_generator import generate
        generate(root,history,module.black_box_function)
        publish(root,'main',['supervisor','experiments','reports','visualizations','tests','requirements.txt','README.md','.gitignore'],phase+' optimization review and consolidated results')
    # Select only code/results successfully executed under the controlled interface.
    for worker,(folder,branch) in WORKERS.items():
        source=worktrees/folder/'workers'/worker
        target=root/'workers'/worker;target.mkdir(parents=True,exist_ok=True)
        for phase in ('independent','collaborative'):
            destination=target/phase;destination.mkdir(exist_ok=True)
            for name in ('algorithm.py','result.json','development.json'):
                shutil.copy2(source/phase/name,destination/name)
    from .validation import validate_selection
    validate_selection(root,history)
    generate(root,history,module.black_box_function)
    subprocess.run(['python3','-m','unittest','discover','-s','tests','-v'],check=True)
    publish(root,'main',['workers','reports','visualizations','experiments'], 'Final multi-agent optimization results and report')
    print('COMPLETE',flush=True)

if __name__=='__main__': main()
