"""Real macOS sandbox integration checks; no benchmark evaluations."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy
from supervisor.agent_manager import profile, execute
from supervisor.coordinator import Ledger

@unittest.skipUnless(sys.platform=='darwin','macOS Seatbelt required')
class IsolationTests(unittest.TestCase):
    def test_private_files_network_and_writes_denied(self):
        runtime=Path.cwd()/'.runtime';runtime.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as temp:
            worker=Path(temp)/'worker';worker.mkdir()
            hidden=Path(temp)/'hidden.py';hidden.write_text('private fixture')
            policy=worker/'sandbox.sb';policy.write_text(profile(worker))
            cases=[("import numpy;print(numpy.__version__)",0),
                (f"open({str(hidden)!r}).read()",1),
                (f"open({str(worker/'bad.txt')!r},'w').write('bad')",1),
                ("import socket;socket.create_connection(('127.0.0.1',11434))",1)]
            prefix='import sys;sys.path.insert(0,'+repr(str(Path(numpy.__file__).parent.parent))+');'
            for code,expected in cases:
                proc=subprocess.run(['/usr/bin/sandbox-exec','-f',str(policy),sys.executable,'-I','-c',prefix+code],cwd=worker,text=True,capture_output=True)
                if 'sandbox_apply: Operation not permitted' in proc.stderr:
                    self.skipTest('Nested sandbox creation blocked by outer environment')
                self.assertEqual(proc.returncode,expected,proc.stderr)

    def test_restart_replays_without_extra_objective_calls(self):
        runtime=Path.cwd()/'.runtime';runtime.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runtime) as temp:
            worker=Path(temp)
            (worker/'algorithm.py').write_text('def optimize(evaluate,budget,seed,shared):\n for i in range(budget): evaluate(i/100,0)\n return {"parameters":{}}\n')
            calls=[]
            ledger=Ledger(worker/'ledger.sqlite',lambda x,y:calls.append((x,y)) or x+y)
            first=execute(worker,worker,ledger,'fixture','independent',[],timeout=30)
            second=execute(worker,worker,ledger,'fixture','independent',[],timeout=30)
            self.assertEqual(len(calls),150)
            self.assertEqual(first['best_value'],second['best_value'])
