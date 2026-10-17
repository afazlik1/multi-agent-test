"""Read progress without invoking any model: python3 -m supervisor.status."""
import json
from pathlib import Path
import sqlite3

def main():
    path=Path('experiments/experiments.sqlite')
    if not path.exists():
        print(json.dumps({'status':'not_started'}));return
    db=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
    records=[]
    for worker,phase,count,value in db.execute('SELECT worker,phase,count(*),max(value) FROM evaluations GROUP BY worker,phase'):
        x,y=db.execute('SELECT x,y FROM evaluations WHERE worker=? AND phase=? ORDER BY value DESC LIMIT 1',(worker,phase)).fetchone()
        records.append(dict(worker=worker,phase=phase,evaluations=count,best_value=value,best_x=x,best_y=y))
    print(json.dumps({'results':records},indent=2))

if __name__=='__main__':main()
