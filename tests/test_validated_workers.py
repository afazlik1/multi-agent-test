"""Replay measured trajectories; no new objective evaluations or hidden source."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from supervisor.agent_manager import execute
from supervisor.coordinator import Ledger

@unittest.skipUnless(sys.platform=='darwin','macOS sandbox required')
class ValidatedWorkerTests(unittest.TestCase):
    def test_selected_code_replays_all_measured_trajectories(self):
        root=Path.cwd();history=root/'experiments'/'experiment_history.json'
        if not history.exists(): self.skipTest('Experiments have not finished')
        runtime=root/'.runtime';runtime.mkdir(exist_ok=True)
        for result in json.loads(history.read_text()):
            with self.subTest(worker=result['worker'],phase=result['phase']):
                with tempfile.TemporaryDirectory(dir=runtime) as temp:
                    directory=Path(temp)
                    shutil.copy2(root/'workers'/result['worker']/result['phase']/'algorithm.py',directory/'algorithm.py')
                    def forbidden(x,y): raise AssertionError('Replay must not invoke objective')
                    ledger=Ledger(':memory:',forbidden)
                    for row in result['trajectory']:
                        ledger.db.execute('INSERT INTO evaluations VALUES (?,?,?,?,?,?,?)',(result['worker'],result['phase'],row['evaluation'],row['x'],row['y'],row['value'],row['elapsed']))
                    ledger.db.commit()
                    replay=execute(directory,directory,ledger,result['worker'],result['phase'],result['supervisor_instructions'])
                    self.assertEqual(replay['best_value'],result['best_value'])
                    points={(p['x'],p['y']):p['value'] for p in result['trajectory']+result['supervisor_instructions']}
                    for point in replay['details'].get('observations',[]):
                        self.assertIn((point['x'],point['y']),points)
                        self.assertAlmostEqual(points[(point['x'],point['y'])],point['value'],places=9)
