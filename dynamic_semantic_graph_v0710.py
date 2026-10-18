"""SEMOS_SIM v0.7.10: dynamic dependency changes, matched DAG control.
Synthetic deterministic computation and logical VM clocks, not an OS benchmark.
"""
import argparse
import hashlib
import json
from pathlib import Path

MODES=("FULL_REBUILD","DAG_DYNAMIC","SEMANTIC_DYNAMIC")

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:20]

def graph(concepts=12):
    if concepts<3:raise ValueError("concepts >=3 required")
    nodes={}
    for i in range(concepts):
        for stage in range(3):
            name=f"C{i}:S{stage}"
            deps=([f"C{i}:S{stage-1}"] if stage else [])
            if stage==2 and i>0:deps.append(f"C{i-1}:S0")
            nodes[name]={"deps":deps,"content":f"source:{i}:{stage}",
                         "compute":float(3+stage+i%3)}
    return nodes

def ordered(nodes):
    remaining=set(nodes);result=[]
    for n in nodes:
        for dep in nodes[n]["deps"]:
            if dep not in nodes:raise ValueError("dangling edge")
    while remaining:
        ready=sorted(n for n in remaining if all(d in result for d in nodes[n]["deps"]))
        if not ready:raise ValueError("cycle")
        result.extend(ready);remaining.difference_update(ready)
    return result

def mutate(nodes,events):
    new={n:{**v,"deps":list(v["deps"])} for n,v in nodes.items()}
    for event in events:
        node=event["node"]
        if node not in new:raise ValueError("unknown node")
        action=event["action"]
        if action=="content":
            new[node]["content"]=event["value"]
        elif action in ("add_edge","remove_edge"):
            dep=event["dependency"]
            if dep not in new:raise ValueError("unknown dependency")
            deps=new[node]["deps"]
            if action=="add_edge":
                if dep in deps:raise ValueError("edge already exists")
                deps.append(dep)
            else:
                if dep not in deps:raise ValueError("edge not found")
                deps.remove(dep)
        else:raise ValueError("unknown event")
    ordered(new)
    return new

def oracle_outputs(nodes):
    outputs={}
    for n in ordered(nodes):
        x=nodes[n]
        outputs[n]=digest([n,x["content"],[(d,outputs[d]) for d in sorted(x["deps"])]])
    return outputs

def simulate(original,events,mode,semantic_overhead=.1,lookup_cost=.02,
             publish_cost=.05,transfer_cost=.5):
    if mode not in MODES:raise ValueError("bad mode")
    if min(semantic_overhead,lookup_cost,publish_cost,transfer_cost)<0:
        raise ValueError("negative cost")
    revised=mutate(original,events)
    before=oracle_outputs(original);after=oracle_outputs(revised)
    affected={n for n in after if after[n]!=before[n]}
    clocks=[0.0]*3;old_cache={};records=[];costs={"compute":0.0,
             "lookup":0.0,"semantic":0.0,"publication":0.0,"transfer":0.0}
    for epoch,nodes,expected in ((0,original,before),(1,revised,after)):
        finished={}
        for n in ordered(nodes):
            deps=nodes[n]["deps"]
            ready=max((finished[d]["end"] for d in deps),default=0.0)
            overhead=0.0 if mode=="FULL_REBUILD" else lookup_cost
            manager=semantic_overhead if mode=="SEMANTIC_DYNAMIC" else 0.0
            costs["lookup"]+=overhead;costs["semantic"]+=manager
            # Source versions and dependency values validated against oracle outputs.
            reuse=(epoch==1 and mode!="FULL_REBUILD" and n in old_cache
                   and old_cache[n]["truth"]==expected[n])
            if reuse:
                cached=old_cache[n]
                candidates=[]
                for vm in range(3):
                    transfer=transfer_cost if cached["vm"]!=vm else 0.0
                    start=max(clocks[vm],ready,cached["end"])
                    candidates.append((start+overhead+manager+transfer,vm,transfer))
                end,vm,remote=min(candidates)
                costs["transfer"]+=remote
            else:
                start,vm=min((max(ready,t),i) for i,t in enumerate(clocks))
                end=start+overhead+manager+nodes[n]["compute"]
                costs["compute"]+=nodes[n]["compute"]
                if mode!="FULL_REBUILD":
                    end+=publish_cost;costs["publication"]+=publish_cost
            clocks[vm]=end
            finished[n]={"truth":expected[n],"vm":vm,"end":end}
            records.append({"epoch":epoch,"id":n,"action":"REUSE" if reuse else "EXECUTE",
                            "vm":vm,"truth":expected[n]})
        old_cache=finished
    second=[x for x in records if x["epoch"]==1]
    recomputed={x["id"] for x in second if x["action"]=="EXECUTE"}
    return {"mode":mode,"events":len(events),"affected":len(affected),
            "affected_ids":sorted(affected),"recomputed":len(recomputed),
            "unnecessary_recompute":len(recomputed-affected),
            "missed_invalidation":len(affected-recomputed),
            "reused":sum(x["action"]=="REUSE" for x in records),
            "correct":all(x["truth"]==(before if x["epoch"]==0 else after)[x["id"]] for x in records)
                      and not (affected-recomputed),
            "aggregate_cost":round(sum(costs.values()),6),
            "makespan":round(max(clocks),6),
            "cost_breakdown":{k:round(v,6) for k,v in costs.items()}}

def compare(concepts=12,semantic_overhead=.1):
    nodes=graph(concepts)
    events=[{"action":"content","node":"C3:S0","value":"modified"},
            {"action":"add_edge","node":"C7:S2","dependency":"C2:S0"},
            {"action":"remove_edge","node":"C6:S2","dependency":"C5:S0"}]
    results=[simulate(nodes,events,m,semantic_overhead) for m in MODES]
    a,b=results[1:]
    return {"version":"0.7.10","kind":"SYNTHETIC_DYNAMIC_DAG_NEGATIVE_CONTROL",
            "events":events,"results":results,
            "matched":{"same_affected":a["affected_ids"]==b["affected_ids"],
                       "same_recompute":a["recomputed"]==b["recomputed"],
                       "both_correct":a["correct"] and b["correct"],
                       "semantic_extra_cost":round(b["aggregate_cost"]-a["aggregate_cost"],6)},
            "limitations":["Central perfect knowledge of graph, semantic content and dependency outputs",
                           "Both incremental engines receive identical change information",
                           "No unique scheduling capability attributed to SPU",
                           "Three logical VM clocks; no real network or failures",
                           "Correctness is a deterministic content-hash proxy, not semantic truth"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--concepts",type=int,default=12)
    p.add_argument("--semantic-overhead",type=float,default=.1)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=compare(a.concepts,a.semantic_overhead)
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:json.dump(report,f,indent=2,ensure_ascii=False)
    print("Wrote:",dest)
    for r in report["results"]:
        print(r["mode"],"affected",r["affected"],"recomputed",r["recomputed"],
              "reuse",r["reused"],"cost",r["aggregate_cost"],"correct",r["correct"])
if __name__=="__main__":main()
