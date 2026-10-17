import tempfile
from pathlib import Path
import unittest
from supervisor.reviewed_algorithms import stage_reviewed

class ReviewedAlgorithmTests(unittest.TestCase):
    def test_idempotent_staging_and_historical_protection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);baseline=root/'workers'/'gradient';baseline.mkdir(parents=True)
            (baseline/'algorithm.py').write_text('reviewed implementation')
            target=root/'worker';target.mkdir()
            stage_reviewed(root,'gradient','independent',target)
            stage_reviewed(root,'gradient','independent',target)
            self.assertEqual((target/'algorithm.py').read_text(),'reviewed implementation')
            (target/'algorithm.py').write_text('historical implementation')
            with self.assertRaisesRegex(RuntimeError,'different implementation'):
                stage_reviewed(root,'gradient','independent',target)
            self.assertEqual((target/'algorithm.py').read_text(),'historical implementation')
