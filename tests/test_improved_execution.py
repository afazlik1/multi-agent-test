"""Run reviewed implementations through the real restricted evaluation interface."""
import tempfile
from pathlib import Path
import sys
import unittest
from supervisor.agent_manager import execute
from supervisor.coordinator import Ledger
from supervisor.reviewed_algorithms import stage_reviewed

@unittest.skipUnless(sys.platform=='darwin','macOS sandbox required')
class ImprovedExecutionTests(unittest.TestCase):
    def test_independent_and_shared_runs_obey_interface(self):
        root=Path.cwd();runtime=root/'.runtime';runtime.mkdir(exist_ok=True)
        objective=lambda x,y: -(0.2*x*x+3*y*y)
        shared=[{'x':0.5,'y':-0.5,'value':objective(0.5,-0.5),'source':'fixture'}]
        for worker in ('bayesian','gradient','particle_swarm'):
            for phase,points in (('independent',[]),('collaborative',shared)):
                with self.subTest(worker=worker,phase=phase):
                    with tempfile.TemporaryDirectory(dir=runtime) as temp:
                        directory=Path(temp);stage_reviewed(root,worker,phase,directory)
                        ledger=Ledger(':memory:',objective)
                        result=execute(directory,directory,ledger,worker,phase,points)
                        self.assertEqual(result['evaluations'],150)
                        observations=result['details']['observations']
                        self.assertEqual(len(observations),150)
                        for point in observations:
                            self.assertAlmostEqual(point['value'],objective(point['x'],point['y']),places=9)
