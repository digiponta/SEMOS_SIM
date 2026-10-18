"""v0.7.11 deterministic replica-consistency simulation, not real VMs."""
import argparse,json
from pathlib import Path
MODES=("DAG_REPLICA","SEMANTIC_REPLICA")
def workload():
    return {"A":(),"B":("A",),"C":("A",),"D":("B","C")}
def truth(graph,versions):
    out={}
    for n in graph:out[n]=(n,versions[n],tuple(out[d] for d in graph[n]))
    return out
def _depends(graph,node,ancestor):
    return ancestor in graph[node] or any(_depends(graph,d,ancestor) for d in graph[node])
def run(mode="DAG_REPLICA",notification_delay=2,management_cost=.1,repair_cost=.5):
    if mode not in MODES:raise ValueError("mode")
    if min(notification_delay,management_cost,repair_cost)<0:raise ValueError("cost/delay")
    graph=workload();versions=dict.fromkeys(graph,1)
    replicas=[{}, {}, {}];pending=[];trace=[]
    cost=0.;stale=repairs=conflicts=reads=0
    events=[(0,"read",0,"D"),(0,"read",1,"D"),(0,"read",2,"D"),
            (1,"write",0,"A"),(1,"write",1,"A"),
            (2,"read",2,"D"),(3,"read",0,"D"),(4,"read",1,"D"),
            (5,"read",2,"D"),(6,"read",0,"D")]
    for tick,kind,vm,node in events:
        due=[x for x in pending if x[0]<=tick]
        pending=[x for x in pending if x[0]>tick]
        for _,target,changed,version in due:
            for item in graph:
                if item==changed or _depends(graph,item,changed):replicas[target].pop(item,None)
            trace.append({"tick":tick,"type":"INVALIDATE","vm":target,"node":changed,"version":version})
        if kind=="write":
            if vm==1:conflicts+=1 # second concurrent writer serialized after VM 0
            versions[node]+=1
            for target in range(3):
                if target==vm:
                    for item in graph:
                        if item==node or _depends(graph,item,node):replicas[target].pop(item,None)
                else:pending.append((tick+notification_delay,target,node,versions[node]))
            cost+=1
            trace.append({"tick":tick,"type":"WRITE","vm":vm,"node":node,"version":versions[node]})
        else:
            expected=truth(graph,versions)[node]
            actual=replicas[vm].get(node);reads+=1
            if actual is not None and actual!=expected:
                stale+=1;repairs+=1;cost+=repair_cost
                replicas[vm].pop(node,None);actual=None
            if actual is None:
                replicas[vm][node]=expected;cost+=4;action="COMPUTE"
            else:cost+=.1;action="REUSE"
            if mode=="SEMANTIC_REPLICA":cost+=management_cost
            trace.append({"tick":tick,"type":"READ","vm":vm,"action":action,
                          "result_correct":replicas[vm][node]==expected})
    return {"mode":mode,"reads":reads,"stale_detected":stale,"repairs":repairs,
            "conflicts":conflicts,
            "wrong_results_returned":sum(x["type"]=="READ" and not x["result_correct"] for x in trace),
            "cost":round(cost,6),"events":trace}
def compare(notification_delay=2,management_cost=.1):
    results=[run(m,notification_delay,management_cost) for m in MODES]
    a,b=results
    return {"version":"0.7.11","kind":"SYNTHETIC_REPLICA_CONSISTENCY",
            "notification_delay":notification_delay,"management_cost":management_cost,
            "results":results,
            "matched":{"same_stale_detection":a["stale_detected"]==b["stale_detected"],
                       "same_conflicts":a["conflicts"]==b["conflicts"],
                       "semantic_extra_cost":round(b["cost"]-a["cost"],6)},
            "limitations":["Three logical workers, no real network or VM",
             "Perfect central truth used for validation on read (oracle)",
             "Concurrent writes serialized deterministically, not consensus",
             "Conventional and semantic modes have identical validation ability",
             "No crashes, network partitions or actual Semantic Memory replication"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--notification-delay",type=int,default=2)
    p.add_argument("--management-cost",type=float,default=.1)
    p.add_argument("--output",required=True)
    a=p.parse_args();report=compare(a.notification_delay,a.management_cost)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",path)
    for r in report["results"]:
        print(r["mode"],"stale",r["stale_detected"],"repairs",r["repairs"],
              "conflicts",r["conflicts"],"wrong_returned",r["wrong_results_returned"],"cost",r["cost"])
if __name__=="__main__":main()
