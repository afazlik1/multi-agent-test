import unittest
from supervisor.privacy import sanitize_diagnostic, sanitize_record

class PrivacyTests(unittest.TestCase):
    def test_redacts_local_paths_in_tracebacks(self):
        text='File "/Users/example-user/Private Projects/worker/algorithm.py", line 4\nFile "/home/example-user/.local/module.py", line 2\nValueError: invalid budget'
        cleaned=sanitize_diagnostic(text)
        self.assertNotIn('example-user',cleaned)
        self.assertNotIn('Private Projects',cleaned)
        self.assertIn('ValueError: invalid budget',cleaned)
        self.assertEqual(cleaned.count('<local-path>'),2)

    def test_recursively_redacts_diagnostics_without_altering_metrics(self):
        original={'error':{'messages':['File "/Users/example-user/worker.py"']},'value':19.5,'evaluations':150}
        clean=sanitize_record(original)
        self.assertNotIn('example-user',str(clean))
        self.assertEqual(clean['value'],19.5)
        self.assertEqual(clean['evaluations'],150)
        self.assertIn('example-user',str(original))
