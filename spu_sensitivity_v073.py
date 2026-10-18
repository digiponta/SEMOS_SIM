"""v0.7.3 controlled cost sensitivity and erroneous semantic merges.

Synthetic comparison; NOT a measured performance benchmark.
"""
import argparse, json, random
from pathlib import Path
from compare_task_spu_v072 import workload

def run_case(n=1000,duplicate_fraction=0.4,semantic_overhead=0.05,
             cache_overhead=0.01,normalization_coverage=0.5,
             false_merge_probability=0.0,seed=42):
    if n<1 or not 0<=duplicate_fraction<=1 or not 0<=normalization_coverage<=1 or not 0<=false_merge_probability<=1:
        raise ValueError("Invalid experiment parameters")
    if semantic_overhead<0 or cache_overhead<0:raise ValueError("Negative overhead")
    rows=workload(n,duplicate_fraction,seed)
    rng=random.Random(seed+1)
    # Normalized surface cache sees only its explicitly recognized fraction.
    # Synthetic canonical meaning oracle is isolated from lexical normalization.
    norm_map={};semantic_map={};first_by_key={}
    for row in rows:
        key=json.dumps(row["semantic"],ensure_ascii=False,sort_keys=True)
        first_by_key.setdefault(key,row["surface"])
    results=[]
    for mode in ("TASK","EXACT_CACHE","NORMALIZED_CACHE","SEMANTIC_SPU"):
        cache={};executed=0;reused=0;wrong_reuse=0;work_cost=0.0;overhead=0.0
        for i,row in enumerate(rows):
            true_key=json.dumps(row["semantic"],ensure_ascii=False,sort_keys=True)
            if mode=="TASK":lookup=None
            elif mode=="EXACT_CACHE":
                lookup=("surface",row["surface"]);overhead+=cache_overhead
            elif mode=="NORMALIZED_CACHE":
                recognized=rng.random()<normalization_coverage
                lookup=("normalized",true_key) if recognized else ("surface",row["surface"])
                overhead+=cache_overhead
            else:
                lookup=("semantic",true_key)
                # Simulated incorrect merger to an unrelated already-cached meaning.
                if cache and rng.random()<false_merge_probability:
                    foreign=[k for k,v in cache.items() if v!=true_key]
                    if foreign:lookup=rng.choice(foreign)
                overhead+=cache_overhead+semantic_overhead
            if lookup is not None and lookup in cache:
                reused+=1
                if cache[lookup]!=true_key:wrong_reuse+=1
            else:
                executed+=1;work_cost+=row["cost"]
                if lookup is not None:cache[lookup]=true_key
        total=work_cost+overhead
        results.append({"mode":mode,"executed":executed,"reused":reused,
                        "wrong_reuse":wrong_reuse,"execution_cost":round(work_cost,5),
                        "overhead_cost":round(overhead,5),"total_cost":round(total,5)})
    baseline=results[0]["total_cost"]
    return {"version":"0.7.3","kind":"SYNTHETIC_SPU_SENSITIVITY",
            "parameters":{"requests":n,"duplicate_fraction":duplicate_fraction,
              "semantic_overhead":semantic_overhead,"cache_overhead":cache_overhead,
              "normalization_coverage":normalization_coverage,
              "false_merge_probability":false_merge_probability,"seed":seed},
            "results":[dict(row,savings_fraction=round((baseline-row["total_cost"])/baseline,6),
                 correct_result_proxy=row["wrong_reuse"]==0) for row in results],
            "limitations":["Costs are synthetic work units, not elapsed time",
              "Canonical meanings supplied by fixture oracle",
              "Normalization coverage and error probability are artificial",
              "Wrong reuse indicates correctness risk; savings may be invalid",
              "No real VM, network, model, or parallel scheduling"]}

def sweep(n=1000,seed=42):
    cases=[]
    for dup in (0.0,0.2,0.4,0.6,0.8):
        for overhead in (0.0,0.05,0.2,0.5):
            for error in (0.0,0.01,0.05):
                cases.append(run_case(n,dup,overhead,false_merge_probability=error,seed=seed))
    return {"version":"0.7.3","kind":"SYNTHETIC_SPU_PARAMETER_SWEEP","cases":cases}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--requests",type=int,default=1000)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--sweep",action="store_true")
    p.add_argument("--output",required=True)
    p.add_argument("--duplicate-fraction",type=float,default=0.4)
    p.add_argument("--semantic-overhead",type=float,default=0.05)
    p.add_argument("--normalization-coverage",type=float,default=0.5)
    p.add_argument("--false-merge-probability",type=float,default=0.0)
    a=p.parse_args()
    report=sweep(a.requests,a.seed) if a.sweep else run_case(
        a.requests,a.duplicate_fraction,a.semantic_overhead,
        normalization_coverage=a.normalization_coverage,
        false_merge_probability=a.false_merge_probability,seed=a.seed)
    target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",target)
if __name__=="__main__":main()
