"""Install reviewed baselines without overwriting an existing experiment."""
import hashlib
import json


def stage_reviewed(root, worker, phase, directory):
    baseline=root/'workers'/worker/'algorithm.py'
    code=baseline.read_text()
    destination=directory/'algorithm.py'
    if destination.exists() and destination.read_text()!=code:
        raise RuntimeError('Existing experiment uses a different implementation. Preserve its ledger and results; use fresh experiment worktrees and tracking for a new reviewed run.')
    if not destination.exists():
        destination.write_text(code)
        (directory/'development.json').write_text(json.dumps({
            'source':'supervisor-reviewed', 'phase':phase,
            'baseline':str(baseline.relative_to(root)),
            'source_sha256':hashlib.sha256(code.encode()).hexdigest(),
            'rationale':'Adaptive Bayesian scales, bounded gradient restarts, or declining swarm inertia.'
        },indent=2))
