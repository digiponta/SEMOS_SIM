"""v0.7.12 three-replica vector-clock and MVCC synthetic simulator.
No central truth oracle is queried by read/write logic. Not real VMs.
"""
import argparse,json
from pathlib import Path
MODES=("DAG_MVCC","SEMANTIC_MVCC")
def dominates(a,b):
    return all(x>=y for x,y in zip(a,b)) and any(x>y for x,y in zip(a,b))
def concurrent(a,b):
    return a!=b and not dominates(a,b) and not dominates(b,a)
def maximal(versions):
    return [v for v in versions if not any(dominates(w["clock"],v["clock"]) for w in versions)]
def choose_latest(versions):
    # Deterministic tie-break only; not semantic truth or consensus.
    return max(versions,key=lambda v:(sum(v["clock"]),v["clock"],v["writer"]))
def simulate(mode="DAG_MVCC",notification_delay=2,validation_cost=.2,
             transmission_cost=.3,semantic_cost=.1):
    if mode not in MODES or notification_delay<0 or min(validation_cost,transmission_cost,semantic_cost)<0:
        raise ValueError("invalid input")
    local=[[{"clock":(0,0,0),"value":"initial","writer":-1}] for _ in range(3)]
    counters=[0,0,0];pending=[];costs={"validation":0.,"transmission":0.,"semantic":0.}
    events=[]
    stats={"writes":0,"reads":0,"delivered":0,"conflict_reads":0,
           "resolved_conflicts":0,"stale_local_reads":0}
    schedule=[(0,"read",2,""),(1,"write",0,"alpha"),(1,"write",1,"beta"),
              (2,"read",2,""),(3,"sync",2,""),(3,"read",2,""),
              (4,"sync",0,""),(4,"sync",1,""),(5,"read",0,""),
              (6,"sync",2,""),(6,"read",2,"")]
    def integrate(target,version):
        if version not in local[target]:local[target].append(version)
    for tick,operation,vm,value in schedule:
        due=[p for p in pending if p[0]<=tick]
        pending=[p for p in pending if p[0]>tick]
        for _,target,version in due:
            integrate(target,version);stats["delivered"]+=1
            events.append({"tick":tick,"type":"DELIVER","vm":target,"clock":version["clock"]})
        if operation=="write":
            counters[vm]+=1
            observed=tuple(max(x["clock"][i] for x in local[vm]) for i in range(3))
            clock=list(observed);clock[vm]=max(clock[vm],counters[vm])
            version={"clock":tuple(clock),"value":value,"writer":vm}
            integrate(vm,version)
            for target in range(3):
                if target!=vm:
                    pending.append((tick+notification_delay,target,version))
                    costs["transmission"]+=transmission_cost
            stats["writes"]+=1
            events.append({"tick":tick,"type":"WRITE","vm":vm,"clock":version["clock"]})
        elif operation=="sync":
            for peer in range(3):
                if peer!=vm:
                    costs["validation"]+=validation_cost
                    costs["transmission"]+=transmission_cost
                    for version in list(local[peer]):integrate(vm,version)
            events.append({"tick":tick,"type":"SYNC","vm":vm})
        else:
            visible=maximal(local[vm])
            conflict=len(visible)>1;winner=choose_latest(visible)
            stats["reads"]+=1;stats["conflict_reads"]+=int(conflict)
            # A post-hoc evaluator metric, not an oracle consulted on the read path.
            all_heads=maximal([v for replica in local for v in replica])
            stale=any(v not in local[vm] for v in all_heads)
            stats["stale_local_reads"]+=int(stale)
            if mode=="SEMANTIC_MVCC":costs["semantic"]+=semantic_cost
            events.append({"tick":tick,"type":"READ","vm":vm,"clock":winner["clock"],
                           "value":winner["value"],"conflict":conflict,"stale_local":stale})
    heads=maximal([v for replica in local for v in replica])
    return {"mode":mode,**stats,"unresolved_heads":len(heads),
            "selected_value":choose_latest(heads)["value"],
            "aggregate_cost":round(sum(costs.values()),6),
            "cost_breakdown":{k:round(v,6) for k,v in costs.items()},"events":events}
def compare(notification_delay=2,validation_cost=.2,transmission_cost=.3,semantic_cost=.1):
    results=[simulate(m,notification_delay,validation_cost,transmission_cost,semantic_cost) for m in MODES]
    a,b=results
    return {"version":"0.7.12","kind":"SYNTHETIC_PEER_MVCC_CONTROL",
            "parameters":{"notification_delay":notification_delay,"validation_cost":validation_cost,
                          "transmission_cost":transmission_cost,"semantic_cost":semantic_cost},
            "results":results,
            "matched":{"same_conflict_detection":a["conflict_reads"]==b["conflict_reads"],
                       "same_stale_observations":a["stale_local_reads"]==b["stale_local_reads"],
                       "same_selected_value":a["selected_value"]==b["selected_value"],
                       "semantic_extra_cost":round(b["aggregate_cost"]-a["aggregate_cost"],6)},
            "limitations":["No central truth oracle queried by replica read/write logic",
               "Post-hoc evaluator compares all replica heads for stale-read metrics",
               "Vector clocks detect concurrency but do not establish semantic truth",
               "Chosen value is a deterministic policy, not resolved consensus",
               "Peer synchronization and message delivery simulated without real VMs",
               "No durable recovery, partition, or consensus protocol",
               "Both modes have identical MVCC behavior; SPU adds synthetic cost"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--notification-delay",type=int,default=2)
    p.add_argument("--validation-cost",type=float,default=.2)
    p.add_argument("--transmission-cost",type=float,default=.3)
    p.add_argument("--semantic-cost",type=float,default=.1)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=compare(a.notification_delay,a.validation_cost,a.transmission_cost,a.semantic_cost)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",path)
    for r in report["results"]:
        print(r["mode"],"reads",r["reads"],"conflict_reads",r["conflict_reads"],
              "stale_local_reads",r["stale_local_reads"],"heads",r["unresolved_heads"],
              "cost",r["aggregate_cost"])
if __name__=="__main__":main()
