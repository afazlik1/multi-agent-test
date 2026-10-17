"""Branch-scoped Git publication; no arbitrary model-supplied commands."""
import subprocess

def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()

def publish(path, branch, files, message):
    if git(path, 'branch', '--show-current') != branch:
        raise RuntimeError('Worker branch mismatch')
    git(path, 'add', '--', *files)
    if git(path, 'diff', '--cached', '--name-only'):
        git(path, 'commit', '-m', message)
    sha = git(path, 'rev-parse', 'HEAD')
    git(path, 'push', 'origin', 'HEAD:refs/heads/' + branch)
    remote = git(path, 'ls-remote', 'origin', 'refs/heads/' + branch).split()[0]
    if remote != sha:
        raise RuntimeError('Remote SHA verification failed')
    return sha
