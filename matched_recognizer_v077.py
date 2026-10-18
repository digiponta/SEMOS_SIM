"""SEMOS_SIM v0.7.7: equal-recognizer cache vs SPU control.

All strategies consume THE SAME precomputed, fallible semantic recognition tokens.
No model inference, real VMs, network activity, or wall-clock measurements.
"""
import argparse,json,random,statistics
from pathlib import Path
from distributed_resilience_v075 import make_workload

MODES=("TASK","EXACT_CACHE","RECOGNIZER_CACHE","SEMANTIC_SPU")

def recognized_workload(count=120, duplicate_fraction=0.4, update_period=30,
                        false_merge_rate=0.0, false_miss_rate=0.0, seed=42):
    if not 0<=false_merge_rate<=1 or not 0<=false_miss_rate<=1:
        raise ValueError("rates must be between 0 and 1")
    rows=make_workload(count,duplicate_fraction,update_period,seed)
    rng=random.Random(seed+771)
    canonical=[r["canonical"] for r in rows]
    for i,row in enumerate(rows):
        token=row["canonical"]
        # An actual incorrect merge targets a different canonical concept.
        if rng.random()<false_merge_rate:
            other=sorted(set(canonical)-{row["canonical"]})
            if other:token=rng.choice(other)
        elif rng.random()<false_miss_rate:
            token=f"unrecognized:{row['id']}"
        row["recognized"]=token
    return rows

def simulate(rows, mode, semantic_overhead=0.1, cache_overhead=0.02,
             common_recognition_cost=0.05, sync_cost=0.05,
             network_latency=0.5):
    if mode not in MODES:raise ValueError("unknown mode")
    if any(v<0 for v in (semantic_overhead,cache_overhead,
                         common_recognition_cost,sync_cost,network_latency)):
        raise ValueError("negative cost")
    clocks=[0.0]*3
    cache={}
    costs={"compute":0.0,"recognition":0.0,"semantic_management":0.0,
           "lookup":0.0,"sync":0.0,"network":0.0}
    executed=reused=wrong_reuse=0
    for row in rows:
        # All modes except TASK include same exact recognition cost.
        recognizer=common_recognition_cost if mode in ("RECOGNIZER_CACHE","SEMANTIC_SPU") else 0.0
        manager=semantic_overhead if mode=="SEMANTIC_SPU" else 0.0
        lookup=cache_overhead if mode!="TASK" else 0.0
        costs["recognition"]+=recognizer
        costs["semantic_management"]+=manager
        costs["lookup"]+=lookup
        if mode=="TASK":key=None
        elif mode=="EXACT_CACHE":key=("surface",row["surface"],row["version"])
        else:key=("recognized",row["recognized"],row["version"])
        overhead=recognizer+manager+lookup
        if key is not None and key in cache:
            origin,finish,actual=cache[key]
            candidates=[]
            for vm in range(3):
                transport=network_latency if origin!=vm else 0.0
                start=max(clocks[vm],finish)
                candidates.append((start+overhead+transport,vm,transport))
            end,vm,transport=min(candidates)
            costs["network"]+=transport
            reused+=1
            if actual!=row["canonical"]:wrong_reuse+=1
        else:
            start,vm=min((t,j) for j,t in enumerate(clocks))
            end=start+overhead+row["compute"];executed+=1
            costs["compute"]+=row["compute"]
            if key is not None:
                end+=sync_cost;costs["sync"]+=sync_cost
                cache[key]=(vm,end,row["canonical"])
        clocks[vm]=end
    return {"mode":mode,"requests":len(rows),"executed":executed,
            "reused":reused,"wrong_reuse":wrong_reuse,
            "correct_reuse":reused-wrong_reuse,
            "correctness_pass":wrong_reuse==0,
            "makespan":round(max(clocks),6),
            "aggregate_cost":round(sum(costs.values()),6),
            "cost_breakdown":{k:round(v,6) for k,v in costs.items()}}

def compare(count=120,duplicate_fraction=0.4,update_period=30,
            false_merge_rate=0.0,false_miss_rate=0.0,seed=42,
            semantic_overhead=0.1,common_recognition_cost=0.05):
    rows=recognized_workload(count,duplicate_fraction,update_period,
                             false_merge_rate,false_miss_rate,seed)
    runs=[simulate(rows,m,semantic_overhead=semantic_overhead,
                   common_recognition_cost=common_recognition_cost) for m in MODES]
    conventional=runs[2]; semantic=runs[3]
    return {"version":"0.7.7","kind":"SYNTHETIC_EQUAL_RECOGNIZER_CONTROL",
            "parameters":{"count":count,"duplicate_fraction":duplicate_fraction,
              "update_period":update_period,"false_merge_rate":false_merge_rate,
              "false_miss_rate":false_miss_rate,"seed":seed,
              "semantic_overhead":semantic_overhead,
              "common_recognition_cost":common_recognition_cost},
            "results":runs,
            "matched_comparison":{
              "spu_cost_difference":round(semantic["aggregate_cost"]-conventional["aggregate_cost"],6),
              "spu_makespan_difference":round(semantic["makespan"]-conventional["makespan"],6),
              "reuse_count_equal":semantic["reused"]==conventional["reused"],
              "wrong_reuse_count_equal":semantic["wrong_reuse"]==conventional["wrong_reuse"],
              "both_correct":semantic["correctness_pass"] and conventional["correctness_pass"]},
            "limitations":[
              "The same noisy recognition tokens feed BOTH matched caching modes",
              "Semantic SPU is represented by incremental management overhead only",
              "No scheduling benefit unique to SPU is modeled, so no structural superiority can be inferred",
              "Wrong reuse counts are a proxy, not a verification of generated answer truth",
              "Synthetically assigned identities, no real VM, retrieval, network, or NLP evaluation",
              "No independent holdout or correlated replica failures"]}

def study(seeds=20,count=120,seed_start=42):
    if seeds<1:raise ValueError("seeds must be positive")
    cases=[]
    for merge,miss in ((0,0),(0.01,0),(0.05,0),(0,0.2),(0.01,0.2)):
        runs=[compare(count=count,false_merge_rate=merge,false_miss_rate=miss,
                      seed=seed_start+i) for i in range(seeds)]
        cases.append({"false_merge_rate":merge,"false_miss_rate":miss,
                      "wrong_reuse_rate_positive_runs":sum(r["results"][3]["wrong_reuse"]>0 for r in runs),
                      "mean_cache_wrong_reuse":round(statistics.mean(r["results"][2]["wrong_reuse"] for r in runs),6),
                      "mean_spu_wrong_reuse":round(statistics.mean(r["results"][3]["wrong_reuse"] for r in runs),6),
                      "mean_spu_minus_cache_cost":round(statistics.mean(r["matched_comparison"]["spu_cost_difference"] for r in runs),6),
                      "identical_reuse_all":all(r["matched_comparison"]["reuse_count_equal"] for r in runs),
                      "identical_wrong_reuse_all":all(r["matched_comparison"]["wrong_reuse_count_equal"] for r in runs)})
    return {"version":"0.7.7","kind":"SYNTHETIC_RECOGNITION_ERROR_STUDY",
            "seed_count":seeds,"seed_start":seed_start,"cases":cases}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--requests",type=int,default=120)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--false-merge-rate",type=float,default=0)
    p.add_argument("--false-miss-rate",type=float,default=0)
    p.add_argument("--semantic-overhead",type=float,default=0.1)
    p.add_argument("--common-recognition-cost",type=float,default=0.05)
    p.add_argument("--study",action="store_true")
    p.add_argument("--seeds",type=int,default=20)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=(study(a.seeds,a.requests,a.seed) if a.study else
            compare(count=a.requests,seed=a.seed,
                    false_merge_rate=a.false_merge_rate,
                    false_miss_rate=a.false_miss_rate,
                    semantic_overhead=a.semantic_overhead,
                    common_recognition_cost=a.common_recognition_cost))
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",dest)
    if a.study:
        for case in report["cases"]:print(case)
    else:
        for r in report["results"]:
            print(r["mode"],"reused=",r["reused"],"wrong=",r["wrong_reuse"],
                  "cost=",r["aggregate_cost"],"makespan=",r["makespan"])
if __name__=="__main__":main()
