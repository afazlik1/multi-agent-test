"""Single-writer, durable objective accounting and phase barrier."""
import json
import math
import sqlite3
import threading
import time

class Ledger:
    def __init__(self, path, objective):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS evaluations (worker TEXT, phase TEXT, n INTEGER, x REAL, y REAL, value REAL, elapsed REAL, PRIMARY KEY(worker,phase,n))')
        self.db.commit()
        self.lock = threading.Lock()
        self.objective = objective

    def rows(self, worker, phase):
        with self.lock:
            return self.db.execute('SELECT n,x,y,value,elapsed FROM evaluations WHERE worker=? AND phase=? ORDER BY n', (worker, phase)).fetchall()

    def evaluate(self, worker, phase, x, y, elapsed):
        x, y = float(x), float(y)
        if not all(math.isfinite(v) and -5 <= v <= 5 for v in (x,y)):
            raise ValueError('Coordinates must be finite and in [-5,5]')
        with self.lock:
            n = self.db.execute('SELECT count(*) FROM evaluations WHERE worker=? AND phase=?', (worker,phase)).fetchone()[0]
            if n >= 150:
                raise ValueError('Phase budget exhausted')
            value = float(self.objective(x,y))
            if not math.isfinite(value):
                raise ValueError('Nonfinite objective')
            self.db.execute('INSERT INTO evaluations VALUES (?,?,?,?,?,?,?)', (worker,phase,n+1,x,y,value,elapsed))
            self.db.commit()
            return value

def guidance(results):
    best = sorted(results, key=lambda r:r['best_value'], reverse=True)
    return [{'x':r['best_x'], 'y':r['best_y'], 'value':r['best_value'], 'source':r['worker']} for r in best]
