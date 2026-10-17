import tempfile
import unittest
from pathlib import Path
from supervisor.coordinator import Ledger, guidance
from supervisor.agent_manager import profile

class FrameworkTests(unittest.TestCase):
    def test_budget_bounds_and_persistence(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'ledger.sqlite';ledger=Ledger(path,lambda x,y:x+y)
            for x,y in [(float('nan'),0),(6,0),(0,float('inf'))]:
                with self.assertRaises(ValueError):ledger.evaluate('a','independent',x,y,0)
            for i in range(150):self.assertEqual(ledger.evaluate('a','independent',1,2,0),3)
            with self.assertRaises(ValueError):ledger.evaluate('a','independent',0,0,0)
            restored=Ledger(path,lambda x,y:x+y)
            self.assertEqual(len(restored.rows('a','independent')),150)
            self.assertEqual(restored.evaluate('a','collaborative',0,0,0),0)
            self.assertEqual(restored.evaluate('b','independent',0,0,0),0)
    def test_guidance_uses_measured_best(self):
        rows=[dict(worker='a',best_x=1,best_y=2,best_value=3),dict(worker='b',best_x=2,best_y=3,best_value=4)]
        self.assertEqual(guidance(rows)[0]['source'],'b')
    def test_profile_denies_by_default(self):
        policy=profile('/tmp/worker');self.assertIn('(deny file-write*)',policy);self.assertNotIn('allow network',policy)

if __name__=='__main__':unittest.main()
