"""v0.7.8: matched-recognizer DAG and semantic dependency graph comparison.
Synthetic deterministic graph calculation; no real VMs or NLP inference.
"""
import argparse,json,random
from pathlib import Path
MODES=("TASK_DAG","RECOGNIZER_DAG","SEMANTIC_DAG")

def workload(concepts=20,repeats=3,seed=42):
    if concepts<2 or repeats<1:raise ValueError("invalid workload")
    rng=random.Random(seed)
    # A 3-stage DAG per concept with a repeated request for the same computation.
    nodes=[]
    for i in range(concepts):
        for stage in range(3):
            for repeat in range(repeats):
                nodes.append({"id":f"C{i}:S{stage}:R{repeat}",
                  "concept":f"C{i}","stage":stage,"repeat":repeat,
                  "surface":f"surface-{i}-{stage}-{repeat}",
                  "dependencies":[f"C{i}:S{stage-1}:R0"] if stage else [],
                  "compute":float(3+stage+(i%3))})
    # Independently include an upstream stage-0 concept cross-edge.
    for i in range(1,concepts):
        for n in nodes:
            if n["concept"]==f"C{i}" and n["stage"]==2:
                n["dependencies"].append(f"C{i-1}:S0:R0")
    return nodes

def run(nodes,mode,changed_concepts=(),recognizer_miss=0,
        recognizer_merge=0,semantic_overhead=0.1,recognition_cost=0.05,
        lookup_cost=0.02,sync_cost=0.05,network_latency=0.5,seed=42):
    if mode not in MODES:raise ValueError("invalid mode")
    if not 0<=recognizer_miss<=1 or not 0<=recognizer_merge<=1:raise ValueError("invalid recognition rate")
    if any(x<0 for x in (semantic_overhead,recognition_cost,lookup_cost,sync_cost,network_latency)):
        raise ValueError("invalid cost")
    rng=random.Random(seed+808)
    concept_set=sorted({n["concept"] for n in nodes})
    # Identity recognized once per request and SHARED between matched graph strategies.
    recognized={}
    for n in nodes:
        token=n["concept"]
        if rng.random()<recognizer_merge:
            choices=[x for x in concept_set if x!=token]
            if choices:token=rng.choice(choices)
        elif rng.random()<recognizer_miss:
            token="MISS:"+n["id"]
        recognized[n["id"]]=token
    return _execute(nodes,mode,recognized,set(changed_concepts),
                    semantic_overhead,recognition_cost,lookup_cost,sync_cost,network_latency)

def _execute(nodes,mode,recognized,changed,semantic_overhead,recognition_cost,
             lookup_cost,sync_cost,network_latency):
    ids=set();state={};cache={};clocks=[0.0]*3
    executed=reused=wrong=0; invalidated=set()
    component={"compute":0.0,"recognition":0.0,"lookup":0.0,
               "semantic_management":0.0,"sync":0.0,"network":0.0}
    # Two epochs, with cache results preserved across epochs and a concept update.
    for epoch in (0,1):
        state={};ids=set()
        for n in nodes:
            rid=n["id"]
            if rid in ids:raise ValueError("duplicate node id")
            ids.add(rid)
            if any(d not in state for d in n["dependencies"]):
                raise ValueError("not topologically sorted or dangling dependency")
            # Actual computation identity includes true dependency-result identity.
            upstream=tuple(state[d]["true_identity"] for d in n["dependencies"])
            true_identity=(n["concept"],n["stage"],upstream,
                           2 if epoch==1 and n["concept"] in changed else 1)
            if mode=="TASK_DAG":key=None
            else:
                upstream_key=tuple(state[d]["recognized_identity"] for d in n["dependencies"])
                key=(recognized[rid],n["stage"],upstream_key,
                     2 if epoch==1 and n["concept"] in changed else 1)
            recognize=recognition_cost if mode!="TASK_DAG" else 0.
            manager=semantic_overhead if mode=="SEMANTIC_DAG" else 0.
            lookup=lookup_cost if mode!="TASK_DAG" else 0.
            component["recognition"]+=recognize
            component["semantic_management"]+=manager
            component["lookup"]+=lookup
            ready=max((state[d]["end"] for d in n["dependencies"]),default=0.)
            if key is not None and key in cache:
                prior=cache[key]
                options=[]
                for vm in range(3):
                    transfer=network_latency if vm!=prior["vm"] else 0.
                    start=max(clocks[vm],ready,prior["end"])
                    options.append((start+recognize+manager+lookup+transfer,vm,transfer))
                end,vm,transfer=min(options);reused+=1;component["network"]+=transfer
                if prior["true_identity"]!=true_identity:wrong+=1
                if epoch==1 and prior["epoch"]==0:invalidated.add(rid) if prior["true_identity"]!=true_identity else None
            else:
                start,vm=min((max(clock,ready),i) for i,clock in enumerate(clocks))
                end=start+recognize+manager+lookup+n["compute"];executed+=1
                component["compute"]+=n["compute"]
                if key is not None:
                    end+=sync_cost;component["sync"]+=sync_cost
                    cache[key]={"vm":vm,"end":end,"true_identity":true_identity,"epoch":epoch}
            clocks[vm]=end
            state[rid]={"end":end,"true_identity":true_identity,
                        "recognized_identity":key if key is not None else (rid,epoch)}
    return {"mode":mode,"requests":len(nodes)*2,"executed":executed,
            "reused":reused,"wrong_reuse":wrong,"correctness_pass":wrong==0,
            "cross_epoch_invalid_reuse":len(invalidated),
            "aggregate_cost":round(sum(component.values()),6),
            "makespan":round(max(clocks),6),
            "cost_breakdown":{k:round(v,6) for k,v in component.items()}}

def compare(concepts=20,repeats=3,seed=42,changed=("C3","C9"),
            recognizer_miss=0.,recognizer_merge=0.,semantic_overhead=0.1):
    nodes=workload(concepts,repeats,seed)
    # Generate noisy tokens separately for each mode, but identically seeded.
    runs=[run(nodes,mode,changed,recognizer_miss,recognizer_merge,
              semantic_overhead=semantic_overhead,seed=seed) for mode in MODES]
    conventional,semantic=runs[1:]
    return {"version":"0.7.8","kind":"SYNTHETIC_MATCHED_DAG_SD_GRAPH",
            "parameters":{"concepts":concepts,"repeats":repeats,"seed":seed,
                          "changed_concepts":list(changed),
                          "recognizer_miss":recognizer_miss,
                          "recognizer_merge":recognizer_merge,
                          "semantic_overhead":semantic_overhead},
            "results":runs,
            "matched_comparison":{"same_reuse":conventional["reused"]==semantic["reused"],
              "same_wrong_reuse":conventional["wrong_reuse"]==semantic["wrong_reuse"],
              "spu_minus_dag_cost":round(semantic["aggregate_cost"]-conventional["aggregate_cost"],6),
              "spu_minus_dag_makespan":round(semantic["makespan"]-conventional["makespan"],6)},
            "limitations":[
             "Task baseline without caching; matched baseline has equivalent semantic-recognizer DAG keys",
             "No special scheduling improvement is modeled for SPU; this is a negative control",
             "Changes and provenance are synthetic, not externally verified semantic truth",
             "Three logical workers with shared centrally consistent cache, no real VMs",
             "Cross-epoch false reuse is represented by wrong_reuse metric",
             "No realistic topology/network contention or consensus failure"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--concepts",type=int,default=20)
    p.add_argument("--repeats",type=int,default=3)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--changed",default="C3,C9")
    p.add_argument("--recognizer-miss",type=float,default=0.)
    p.add_argument("--recognizer-merge",type=float,default=0.)
    p.add_argument("--semantic-overhead",type=float,default=0.1)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=compare(a.concepts,a.repeats,a.seed,
       tuple(x for x in a.changed.split(",") if x),
       a.recognizer_miss,a.recognizer_merge,a.semantic_overhead)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",path)
    for r in report["results"]:print(r["mode"],"executed",r["executed"],"reused",r["reused"],
          "wrong",r["wrong_reuse"],"cost",r["aggregate_cost"],"makespan",r["makespan"])
if __name__=="__main__":main()
