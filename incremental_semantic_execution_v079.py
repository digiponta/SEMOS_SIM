"""SEMOS_SIM v0.7.9 — matched incremental DAG change propagation.

All figures are synthetic. Both DAG engines get identical semantic identities,
edges and change notifications. No unique SPU scheduling advantage is presumed.
"""
import argparse
import json
import random
from pathlib import Path

MODES=("TASK_FULL_REBUILD","DAG_INCREMENTAL","SEMANTIC_INCREMENTAL")

def build_graph(concepts=20,seed=42):
    if concepts<2:raise ValueError("concepts must be >= 2")
    rng=random.Random(seed)
    nodes=[]
    for i in range(concepts):
        for stage in range(3):
            deps=([f"C{i}:S{stage-1}"] if stage else [])
            if stage==2 and i>0:deps.append(f"C{i-1}:S0")
            nodes.append({"id":f"C{i}:S{stage}","concept":f"C{i}",
                          "deps":deps,"compute":float(3+stage+(i%3)),
                          "recognition_token":f"C{i}"})
    return nodes

def descendants(nodes,changed):
    ids={n["id"] for n in nodes}
    if len(ids)!=len(nodes):raise ValueError("duplicate node id")
    children={name:set() for name in ids}
    for node in nodes:
        for dep in node["deps"]:
            if dep not in children:raise ValueError("unknown dependency")
            children[dep].add(node["id"])
    if not set(changed)<=ids:raise ValueError("unknown changed node")
    reached=set(changed);stack=list(changed)
    while stack:
        for child in children[stack.pop()]:
            if child not in reached:
                reached.add(child);stack.append(child)
    return reached

def simulate(nodes,mode,changed,semantic_overhead=0.1,
             recognition_cost=0.05,lookup_cost=0.02,sync_cost=0.05,
             remote_cost=0.5,seed=42):
    if mode not in MODES:raise ValueError("invalid mode")
    if any(x<0 for x in (semantic_overhead,recognition_cost,lookup_cost,sync_cost,remote_cost)):
        raise ValueError("negative overhead")
    affected=descendants(nodes,changed)
    id_set={n["id"] for n in nodes}
    if not id_set:raise ValueError("empty graph")
    clocks=[0.0]*3
    previous={}
    executed=0;reused=0;wrong=0;transfers=0
    work=0.0; overheads={"recognition":0.0,"lookup":0.0,
             "semantic_management":0.0,"publication":0.0,"network":0.0}
    second_recomputed=set()
    results={}
    for epoch in (0,1):
        results={}
        for node in nodes:
            nid=node["id"]
            if any(dep not in results for dep in node["deps"]):
                raise ValueError("topological order violated")
            current=(node["recognition_token"],node["id"],
                     tuple(results[d]["truth"] for d in node["deps"]),
                     epoch if nid in affected else 0)
            canonical_truth=(node["id"],tuple(results[d]["truth"] for d in node["deps"]),
                            epoch if nid in affected else 0)
            manager=semantic_overhead if mode=="SEMANTIC_INCREMENTAL" else 0.0
            recognition=recognition_cost if mode!="TASK_FULL_REBUILD" else 0.0
            lookup=lookup_cost if mode!="TASK_FULL_REBUILD" else 0.0
            overheads["recognition"]+=recognition
            overheads["lookup"]+=lookup
            overheads["semantic_management"]+=manager
            ready=max((results[d]["end"] for d in node["deps"]),default=0.0)
            can_reuse=(epoch==1 and mode!="TASK_FULL_REBUILD"
                       and nid not in affected and nid in previous)
            if can_reuse:
                prior=previous[nid]
                options=[]
                for vm in range(3):
                    transfer=remote_cost if prior["vm"]!=vm else 0.0
                    start=max(ready,clocks[vm],prior["end"])
                    options.append((start+recognition+lookup+manager+transfer,vm,transfer))
                end,vm,transfer=min(options)
                reused+=1
                overheads["network"]+=transfer
                if transfer:transfers+=1
                # Compare actual true computation signatures, never only the keys.
                if prior["truth"]!=canonical_truth:wrong+=1
            else:
                start,vm=min((max(clock,ready),i) for i,clock in enumerate(clocks))
                end=start+recognition+lookup+manager+node["compute"]
                if mode!="TASK_FULL_REBUILD":
                    end+=sync_cost;overheads["publication"]+=sync_cost
                executed+=1;work+=node["compute"]
                if epoch==1:second_recomputed.add(nid)
            clocks[vm]=end
            results[nid]={"truth":canonical_truth,"key":current,"vm":vm,"end":end}
        previous=results
    total=work+sum(overheads.values())
    return {"mode":mode,"requests":len(nodes)*2,"initial_nodes":len(nodes),
            "changed_nodes":len(changed),"affected_nodes":len(affected),
            "recomputed_second_epoch":len(second_recomputed),
            "unnecessary_recomputation":len(second_recomputed-affected),
            "missed_invalidations":len(affected-second_recomputed),
            "executed":executed,"reused":reused,"wrong_reuse":wrong,
            "correctness_pass":wrong==0 and not (affected-second_recomputed),
            "transfers":transfers,"aggregate_cost":round(total,6),
            "makespan":round(max(clocks),6),
            "cost_breakdown":{"compute":round(work,6),**{k:round(v,6) for k,v in overheads.items()}}}

def compare(concepts=20,seed=42,changed=("C3:S0","C9:S1"),
            semantic_overhead=0.1):
    nodes=build_graph(concepts,seed)
    affected=descendants(nodes,set(changed))
    runs=[simulate(nodes,m,set(changed),semantic_overhead=semantic_overhead,seed=seed)
          for m in MODES]
    a,b=runs[1:]
    return {"version":"0.7.9","kind":"SYNTHETIC_MATCHED_INCREMENTAL_DAG",
            "parameters":{"concepts":concepts,"seed":seed,"changed":list(changed),
                          "semantic_overhead":semantic_overhead},
            "affected_ids":sorted(affected),"results":runs,
            "matched_comparison":{"same_recompute":a["recomputed_second_epoch"]==b["recomputed_second_epoch"],
                 "same_accuracy":a["correctness_pass"]==b["correctness_pass"],
                 "semantic_minus_dag_cost":round(b["aggregate_cost"]-a["aggregate_cost"],6),
                 "semantic_minus_dag_makespan":round(b["makespan"]-a["makespan"],6)},
            "limitations":[
              "Both incremental DAG engines have the same graph, change notifications, identity and scheduling",
              "No SPU-exclusive benefit modeled; this is an architectural negative control",
              "All changed nodes are known exactly; no missed semantic change detection",
              "Central memory, 3 logical workers, no real VM or network measurements",
              "Change effects are synthetically defined by graph descendants",
              "VM migration represented only as cache retrieval and synthetic transfer cost"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--concepts",type=int,default=20)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--changed",default="C3:S0,C9:S1")
    p.add_argument("--semantic-overhead",type=float,default=0.1)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=compare(a.concepts,a.seed,tuple(filter(None,a.changed.split(","))),a.semantic_overhead)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",dest)
    print("Affected nodes:",len(report["affected_ids"]))
    for x in report["results"]:
        print(x["mode"],"epoch2 recomputed",x["recomputed_second_epoch"],
              "reuse",x["reused"],"wrong",x["wrong_reuse"],
              "cost",x["aggregate_cost"],"makespan",x["makespan"])
if __name__=="__main__":main()
