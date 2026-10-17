import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
sys.path.insert(0,'/Users/reza/Library/Python/3.9/lib/python/site-packages')
from algorithm import optimize
def evaluate(x,y):
 print(json.dumps({"evaluate":[float(x),float(y)]}),flush=True)
 response=json.loads(sys.stdin.readline())
 if "error" in response: raise RuntimeError(response["error"])
 return response["value"]
config=json.loads(sys.stdin.readline())
result=optimize(evaluate,config["budget"],config["seed"],config["shared"])
print(json.dumps({"result":result}),flush=True)
