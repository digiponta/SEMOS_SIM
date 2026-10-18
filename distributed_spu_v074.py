"""SEMOS_SIM v0.7.4: deterministic three-VM discrete-event cost model.

Not a real VM/runtime measurement. Canonical equivalence is fixture-provided.
Both caching modes use the SAME globally accessible result directory.
"""
import argparse
import json
import random
from pathlib import Path

VM_NAMES=("VM-A","VM-B","VM-C")
MODES=("TASK","NORMALIZED_CACHE","SEMANTIC_SPU")

def make_workload(count=120,duplicate_fraction=0.4,dependency_fraction=0.2,seed=42):
    if count<1 or not 0<=duplicate_fraction<=1 or not 0<=dependency_fraction<=1:
        raise ValueError("invalid workload parameters")
    rng=random.Random(seed)
    originals=max(1,round(count*(1-duplicate_fraction)))
    rows=[]
    for i in range(count):
        concept=i if i<originals else rng.randrange(originals)
        # Dependencies refer only to earlier entries (acyclic by construction).
        dep=(f"R{i-1:05d}",) if i>0 and rng.random()<dependency_fraction else ()
        rows.append({"id":f"R{i:05d}","surface":f"surface-{i}-{concept}",
                     "canonical":f"concept-{concept}","dependencies":dep,
                     "compute":4.0+(concept%3)})
    return rows

def simulate(rows,mode,network_latency=0.5,semantic_overhead=0.1,
             normalized_coverage=0.5,lookup_overhead=0.02,seed=42):
    if mode not in MODES:raise ValueError("unknown mode")
    if any(v<0 for v in (network_latency,semantic_overhead,lookup_overhead)):
        raise ValueError("negative cost")
    if not 0<=normalized_coverage<=1:raise ValueError("invalid coverage")
    rng=random.Random(seed)
    vm_free={vm:0.0 for vm in VM_NAMES}
    completed={};shared_cache={};records=[]
    executed=reused=transfers=0
    execution_work=transfer_cost=semantic_cost=lookup_cost=0.0
    ids=[x["id"] for x in rows]
    if len(set(ids))!=len(ids):raise ValueError("duplicate request id")
    for index,row in enumerate(rows):
        if any(d not in completed for d in row["dependencies"]):
            raise ValueError("dependencies must appear earlier")
        # Dependencies part of the *execution identity*: no unsafe
        # reuse across different upstream request graphs.
        dep_signature=tuple((d,completed[d]["identity"]) for d in row["dependencies"])
        identity=(row["canonical"],dep_signature)
        if mode=="TASK":key=None
        elif mode=="NORMALIZED_CACHE":
            # Fixed random seed, same normalization coverage each run.
            # No actual NLP normalization is performed.
            recognized=rng.random()<normalized_coverage
            key=("normalized",row["canonical"],dep_signature) if recognized else ("surface",row["surface"],dep_signature)
        else:key=("semantic",row["canonical"],dep_signature)

        ready=max([completed[d]["end"] for d in row["dependencies"]],default=0.0)
        lookup=(lookup_overhead if mode!="TASK" else 0.0)
        semantic=(semantic_overhead if mode=="SEMANTIC_SPU" else 0.0)
        lookup_cost+=lookup
        semantic_cost+=semantic
        if key is not None and key in shared_cache:
            origin=shared_cache[key]
            # Each VM is a potential requester; choose earliest completion
            # including cache visibility and simulated VM-to-VM transfer.
            options=[]
            for vm in VM_NAMES:
                is_remote=vm!=origin["vm"]
                communication=network_latency if is_remote else 0.0
                start=max(ready,vm_free[vm],origin["end"])
                options.append((start+lookup+semantic+communication,vm,start,communication))
            end,vm,start,comm=min(options)
            reused+=1
            if comm:transfers+=1;transfer_cost+=comm
            action="REUSED"
        else:
            options=[(max(ready,vm_free[vm])+lookup+semantic+row["compute"],vm,
                      max(ready,vm_free[vm])) for vm in VM_NAMES]
            end,vm,start=min(options)
            execution_work+=row["compute"];executed+=1
            action="EXECUTED";comm=0.0
            if key is not None:shared_cache[key]={"vm":vm,"end":end}
        vm_free[vm]=end
        rec={"id":row["id"],"vm":vm,"action":action,"start":round(start,5),
             "end":round(end,5),"identity":identity,"dependencies":list(row["dependencies"]),
             "transfer_cost":comm}
        records.append(rec);completed[row["id"]]=rec
    makespan=max(vm_free.values())
    return {"mode":mode,"requests":len(rows),"executed":executed,
            "reused":reused,"transfers":transfers,
            "makespan":round(makespan,5),
            "execution_work":round(execution_work,5),
            "transfer_cost":round(transfer_cost,5),
            "semantic_cost":round(semantic_cost,5),
            "lookup_cost":round(lookup_cost,5),
            "aggregate_cost":round(execution_work+transfer_cost+semantic_cost+lookup_cost,5),
            "vm_busy_until":{k:round(v,5) for k,v in vm_free.items()},
            "records":records}

def compare(count=120,duplicate_fraction=0.4,dependency_fraction=0.2,seed=42,
            network_latency=0.5,semantic_overhead=0.1,normalized_coverage=0.5):
    rows=make_workload(count,duplicate_fraction,dependency_fraction,seed)
    runs=[simulate(rows,mode,network_latency,semantic_overhead,
                   normalized_coverage,seed=seed) for mode in MODES]
    task_cost=runs[0]["aggregate_cost"];task_span=runs[0]["makespan"]
    metrics=[]
    for run in runs:
        metrics.append({k:v for k,v in run.items() if k!="records"}|{
            "aggregate_cost_saving_vs_task":round((task_cost-run["aggregate_cost"])/task_cost,6),
            "makespan_saving_vs_task":round((task_span-run["makespan"])/task_span,6)})
    return {"version":"0.7.4","kind":"SYNTHETIC_THREE_VM_COMPARISON",
            "parameters":{"requests":count,"duplicate_fraction":duplicate_fraction,
                          "dependency_fraction":dependency_fraction,"seed":seed,
                          "network_latency":network_latency,
                          "semantic_overhead":semantic_overhead,
                          "normalization_coverage":normalized_coverage},
            "results":metrics,"limitations":[
              "Three virtual workers are modeled in one process; no actual VMs or network",
              "Canonical semantic equivalence is supplied by synthetic fixture",
              "No errors, VM crashes, network contention or cross-request admission delay",
              "Both caching modes have the same shared result directory",
              "Dependency-sensitive keys intentionally limit reuse across different DAGs",
              "Times and costs are synthetic units, not measured seconds or joules"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--requests",type=int,default=120)
    p.add_argument("--duplicate-fraction",type=float,default=0.4)
    p.add_argument("--dependency-fraction",type=float,default=0.2)
    p.add_argument("--network-latency",type=float,default=0.5)
    p.add_argument("--semantic-overhead",type=float,default=0.1)
    p.add_argument("--normalization-coverage",type=float,default=0.5)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=compare(a.requests,a.duplicate_fraction,a.dependency_fraction,
                   a.seed,a.network_latency,a.semantic_overhead,a.normalization_coverage)
    dst=Path(a.output);dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",dst)
if __name__=="__main__":main()
