"""SEMOS_SIM v0.7.5 synthetic 3-worker fault/version/sync benchmark.
Same workload and worker count for TASK, normalized cache and Semantic SPU.
Canonical equivalence is supplied by oracle; not real VMs.
"""
import argparse, json, random
from pathlib import Path
VMS=("VM-A","VM-B","VM-C")
MODES=("TASK","NORMALIZED_CACHE","SEMANTIC_SPU")

def make_workload(count=120,duplicate_fraction=0.4,update_period=30,seed=42):
    if count<1 or not 0<=duplicate_fraction<=1 or update_period<1:raise ValueError("invalid workload")
    rng=random.Random(seed); unique=max(1,round(count*(1-duplicate_fraction))); out=[]
    for i in range(count):
        concept=i if i<unique else rng.randrange(unique)
        out.append({"id":f"R{i:05d}","surface":f"query-{i}-{concept}","canonical":f"concept-{concept}",
                    "version":1+i//update_period,"compute":float(4+concept%3)})
    return out

def simulate(rows,mode,failure_rate=0.1,network_latency=0.5,sync_cost=0.05,
             retry_cost=0.5,semantic_overhead=0.1,lookup_cost=0.02,
             normalized_coverage=0.5,seed=42):
    if mode not in MODES or not 0<=failure_rate<=1 or not 0<=normalized_coverage<=1:raise ValueError("bad mode/rate")
    if any(x<0 for x in (network_latency,sync_cost,retry_cost,semantic_overhead,lookup_cost)):raise ValueError("negative cost")
    fault_rng=random.Random(seed+900); norm_rng=random.Random(seed+1200)
    failures_by_id={r["id"] for r in rows if fault_rng.random()<failure_rate}
    clocks=dict.fromkeys(VMS,0.0); cache={}; records=[]
    executed=reused=failed=retries=transfers=stale=0
    cost={"compute":0.0,"network":0.0,"sync":0.0,"retry":0.0,"semantic":0.0,"lookup":0.0}
    for row in rows:
        if mode=="TASK":key=None
        elif mode=="NORMALIZED_CACHE":
            recognized=norm_rng.random()<normalized_coverage
            token=("normalized",row["canonical"]) if recognized else ("surface",row["surface"])
            key=(token,row["version"])
        else:key=(("semantic",row["canonical"]),row["version"])
        overhead=0.0 if mode=="TASK" else lookup_cost
        if mode!="TASK":cost["lookup"]+=lookup_cost
        if mode=="SEMANTIC_SPU":
            overhead+=semantic_overhead;cost["semantic"]+=semantic_overhead
        if key is not None and key in cache:
            origin,ready,canonical,version=cache[key]
            candidates=[]
            for vm in VMS:
                comm=network_latency if vm!=origin else 0.0
                start=max(clocks[vm],ready)
                candidates.append((start+overhead+comm,vm,comm))
            end,vm,comm=min(candidates);clocks[vm]=end;reused+=1
            if comm:transfers+=1;cost["network"]+=comm
            if canonical!=row["canonical"] or version!=row["version"]:stale+=1
            action="REUSED"
        else:
            start,vm=min((clocks[v],v) for v in VMS)
            end=start+overhead+row["compute"];cost["compute"]+=row["compute"];executed+=1
            if row["id"] in failures_by_id:
                failed+=1;retries+=1;clocks[vm]=end;cost["compute"]+=row["compute"];cost["retry"]+=retry_cost
                other=[v for v in VMS if v!=vm]
                start,vm=min((clocks[v],v) for v in other)
                end=start+retry_cost+row["compute"]
            if key is not None:
                end+=sync_cost;cost["sync"]+=sync_cost
                cache[key]=(vm,end,row["canonical"],row["version"])
            clocks[vm]=end;action="EXECUTED"
        records.append({"id":row["id"],"action":action,"vm":vm,"version":row["version"],"finish":round(end,5)})
    return {"mode":mode,"requests":len(rows),"executed":executed,"reused":reused,
            "failures":failed,"retries":retries,"remote_transfers":transfers,"stale_reuse":stale,
            "all_correct_proxy":stale==0,"makespan":round(max(clocks.values()),5),
            "aggregate_cost":round(sum(cost.values()),5),
            "cost_breakdown":{k:round(v,5) for k,v in cost.items()},
            "vm_busy_until":{k:round(v,5) for k,v in clocks.items()},"records":records}

def compare(count=120,duplicate_fraction=0.4,update_period=30,failure_rate=0.1,
            network_latency=0.5,sync_cost=0.05,retry_cost=0.5,semantic_overhead=0.1,
            lookup_cost=0.02,normalized_coverage=0.5,seed=42):
    rows=make_workload(count,duplicate_fraction,update_period,seed)
    runs=[simulate(rows,mode,failure_rate,network_latency,sync_cost,retry_cost,
                   semantic_overhead,lookup_cost,normalized_coverage,seed) for mode in MODES]
    baseline=runs[0]
    results=[{k:v for k,v in r.items() if k!="records"}|{
             "aggregate_savings_vs_task":round(1-r["aggregate_cost"]/baseline["aggregate_cost"],6),
             "makespan_savings_vs_task":round(1-r["makespan"]/baseline["makespan"],6)} for r in runs]
    return {"version":"0.7.5","kind":"SYNTHETIC_THREE_VM_RESILIENCE",
            "parameters":{"requests":count,"duplicate_fraction":duplicate_fraction,"update_period":update_period,
                          "failure_rate":failure_rate,"network_latency":network_latency,
                          "sync_cost":sync_cost,"retry_cost":retry_cost,"semantic_overhead":semantic_overhead,
                          "lookup_cost":lookup_cost,"normalized_coverage":normalized_coverage,"seed":seed},
            "results":results,"limitations":[
                "Logical three-worker model, not actual VM or network measurements",
                "Semantic equivalence is supplied by oracle",
                "Both caches use a perfectly consistent shared directory",
                "Version embedded in cache key; no stale replica lag modeled",
                "At most one simulated transient failure per request",
                "No actual network contention, correlated failures or semantic false merges",
                "Numbers are synthetic units, not measured milliseconds"]}

def main():
    p=argparse.ArgumentParser()
    for name,typ,default in [
        ("requests",int,120),("duplicate-fraction",float,0.4),("update-period",int,30),
        ("failure-rate",float,0.1),("network-latency",float,0.5),("sync-cost",float,0.05),
        ("retry-cost",float,0.5),("semantic-overhead",float,0.1),
        ("normalized-coverage",float,0.5),("seed",int,42)]:
        p.add_argument("--"+name,type=typ,default=default)
    p.add_argument("--output",required=True)
    a=vars(p.parse_args())
    report=compare(a["requests"],a["duplicate_fraction"],a["update_period"],
        a["failure_rate"],a["network_latency"],a["sync_cost"],a["retry_cost"],
        a["semantic_overhead"],normalized_coverage=a["normalized_coverage"],seed=a["seed"])
    dst=Path(a["output"]);dst.parent.mkdir(parents=True,exist_ok=True)
    with dst.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",dst)
if __name__=="__main__":main()
