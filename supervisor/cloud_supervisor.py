"""Optional supported CLI bridge; never enabled automatically."""
import subprocess

def request_review(summary, cwd, enabled=False):
    if not enabled:
        raise RuntimeError('Cloud invocation is disabled; explicitly enable after reviewing account costs')
    return subprocess.run(['codex','exec','--json','--sandbox','read-only','-C',str(cwd), '-'],input=summary,text=True,capture_output=True,check=True).stdout
