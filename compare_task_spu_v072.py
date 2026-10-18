"""v0.7.2: fair, synthetic task-vs-SPU execution-cost comparison.

Canonical meaning is fixture-provided (oracle), not inferred by a model.
All modes receive the same requests, costs and dependency graph.
"""
import argparse,json,random
from pathlib import Path
from semantic_processing_unit_v071 import SemanticUnit,ProcessingRequest,SPUSimulator

def workload(n=1000,duplicate_fraction=0.4,seed=42):
    if n<1 or not 0<=duplicate_fraction<=1:raise ValueError("Invalid workload")
    rng=random.Random(seed)
    originals=max(1,round(n*(1-duplicate_fraction)))
    rows=[]
    for i in range(n):
        c=i if i<originals else rng.randrange(originals)
        semantic={"concept":f"SEM-{c}","predicate":"EVALUATE","value":c}
        # Distinct surfaces for semantically identical instances.
        surface=f"request-{i}-concept-{c}"
        rows.append({"request_id":f"R{i:06d}","surface":surface,
                     "semantic":semantic,"cost":1.0})
    rng.shuffle(rows)
    return rows

def simulate(rows,mode,semantic_overhead=0.05,cache_overhead=0.01):
    if mode not in ("TASK","EXACT_CACHE","SEMANTIC_SPU"):raise ValueError("Invalid mode")
    if semantic_overhead<0 or cache_overhead<0:raise ValueError("Negative overhead")
    cache=set();exec_count=0;reused=0;task_cost=0.0;index_cost=0.0
    for row in rows:
        if mode=="TASK":
            key=None
        elif mode=="EXACT_CACHE":
            key=row["surface"]
            index_cost+=cache_overhead
        else:
            key=json.dumps(row["semantic"],sort_keys=True,ensure_ascii=False)
            index_cost+=semantic_overhead+cache_overhead
        if key is not None and key in cache:
            reused+=1
        else:
            exec_count+=1;task_cost+=row["cost"]
            if key is not None:cache.add(key)
    return {"mode":mode,"requests":len(rows),"executed":exec_count,
            "reused":reused,"reuse_rate":round(reused/len(rows),6) if rows else 0,
            "execution_cost":round(task_cost,6),
            "index_and_semantic_cost":round(index_cost,6),
            "total_cost":round(task_cost+index_cost,6)}

def run(n=1000,duplicate_fraction=0.4,seed=42,semantic_overhead=0.05,cache_overhead=0.01):
    rows=workload(n,duplicate_fraction,seed)
    modes=[simulate(rows,m,semantic_overhead,cache_overhead) for m in ("TASK","EXACT_CACHE","SEMANTIC_SPU")]
    baseline=modes[0]["total_cost"]
    return {"version":"0.7.2","kind":"SYNTHETIC_COMPARATIVE_COST_EXPERIMENT",
            "parameters":{"requests":n,"duplicate_fraction_requested":duplicate_fraction,
                          "seed":seed,"semantic_overhead_per_request":semantic_overhead,
                          "cache_overhead_per_request":cache_overhead},
            "results":[dict(x,savings_vs_task_fraction=round((baseline-x["total_cost"])/baseline,6)) for x in modes],
            "limitations":["Synthetic cost units, not real CPU/time measurements",
                           "Oracle-supplied semantic IDs: no false merges or semantic model errors",
                           "Surface IDs deliberately unique; no exact-cache hits in this fixture",
                           "No real VM scheduling, parallel execution or network effects",
                           "SPU algorithm from v0.7.1 is conceptual; this isolates cost accounting"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--requests",type=int,default=1000)
    p.add_argument("--duplicate-fraction",type=float,default=0.4)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--semantic-overhead",type=float,default=0.05)
    p.add_argument("--cache-overhead",type=float,default=0.01)
    p.add_argument("--output",default=None)
    a=p.parse_args()
    report=run(a.requests,a.duplicate_fraction,a.seed,a.semantic_overhead,a.cache_overhead)
    data=json.dumps(report,indent=2,ensure_ascii=False)
    if a.output:
        target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("x",encoding="utf-8") as f:f.write(data+"\n")
        print("Wrote:",target)
    else:print(data)
if __name__=="__main__":main()
