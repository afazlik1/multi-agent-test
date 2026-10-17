"""Selective integration and objective-free replay of reviewed worker code."""
import hashlib
import json
from .agent_manager import execute
from .coordinator import Ledger

def prepare_source(worker, code):
    if worker=='particle_swarm':
        for index in ('i','idx'):
            for axis in (0,1):
                code=code.replace(f'float(X[{index}, {axis}])',f'float(pbest[{index}, {axis}])')
        code=code.replace("'source': 'independent'", "'source': 'collaborative' if shared else 'independent'")
    if worker=='gradient':
        code=code.replace('fxp = eval_point(x + h, y)', 'xp, xm = min(5.0, x + h), max(-5.0, x - h)\n        yp, ym = min(5.0, y + h), max(-5.0, y - h)\n        fxp = eval_point(xp, y)')
        code=code.replace('fxm = eval_point(x - h, y)','fxm = eval_point(xm, y)').replace('fyp = eval_point(x, y + h)','fyp = eval_point(x, yp)').replace('fym = eval_point(x, y - h)','fym = eval_point(x, ym)')
        code=code.replace('gx = (fxp - fxm) / (2 * h)','dx = 2 * h if -5 <= x - h and x + h <= 5 else xp - xm\n        dy = 2 * h if -5 <= y - h and y + h <= 5 else yp - ym\n        gx = (fxp - fxm) / dx').replace('gy = (fyp - fym) / (2 * h)','gy = (fyp - fym) / dy')
    return code

def validate_selection(root, history):
    for result in history:
        worker=result['worker'];phase=result['phase'];directory=root/'workers'/worker/phase
        algorithm=directory/'algorithm.py'
        algorithm.write_text(prepare_source(worker,algorithm.read_text()))
        ledger=Ledger(':memory:',lambda x,y: (_ for _ in ()).throw(RuntimeError('Review cannot request new objective values')))
        for p in result['trajectory']:
            ledger.db.execute('INSERT INTO evaluations VALUES (?,?,?,?,?,?,?)',(worker,phase,p['evaluation'],p['x'],p['y'],p['value'],p['elapsed']))
        ledger.db.commit()
        reviewed=execute(directory,directory,ledger,worker,phase,result['supervisor_instructions'])
        points={(p['x'],p['y']):p['value'] for p in result['trajectory']+result['supervisor_instructions']}
        for p in reviewed['details'].get('observations',[]):
            if (p['x'],p['y']) not in points or abs(points[(p['x'],p['y'])]-p['value'])>1e-9:
                raise RuntimeError('Worker auxiliary summary failed validation')
        result['details']=reviewed['details']
        result['selected_source_sha256']=hashlib.sha256(algorithm.read_bytes()).hexdigest()
        result['supervisor_review']='Selected code passed exact full-trajectory replay without new objective calls. Main adds reviewed swarm-summary and gradient-boundary fixes where applicable; original worker reports remain in their branch commits.'
        (directory/'result.json').write_text(json.dumps(result,indent=2))
        for filename in ('runner.py','sandbox.sb'):(directory/filename).unlink(missing_ok=True)
