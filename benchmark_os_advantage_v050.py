"""v0.5.0 Semantic OS control-plane advantage benchmark.

This is NOT an operating-system benchmark: VMs are simulated dispatch targets.
Uses preexisting development requests, never reports final holdout performance.
Task success = routing to labeled-capable VM; processing time is synthetic.
"""
from __future__ import annotations
import argparse,csv,json,statistics,time
from collections import Counter
from pathlib import Path
from benchmark_v040 import load_csv,KeywordRouter,TFIDFRouter

VMS=("VM-A","VM-B","VM-C")
SIMULATED_SERVICE_MS={"VM-A":8.0,"VM-B":12.0,"VM-C":10.0}
# Per-VM execution time is fixed per benchmark scenario, not measured OS work.

class RoundRobin:
    def __init__(self):self.index=0
    def predict(self,text):
        result=VMS[self.index%len(VMS)];self.index+=1;return result

class HybridAdapter:
    def __init__(self,engine,weight=.7,threshold=0.,margin=0.):
        from compare_prototypes_v044 import make_representations
        self.reps=make_representations(engine)
        self.engine=engine;self.weight=weight
        self.threshold=threshold;self.margin=margin
    def predict(self,text):
        from compare_prototypes_v044 import predict_scores
        from hybrid_router_v046 import decision
        q=self.engine.vector(text)
        c=predict_scores(q,"centroid",self.reps)
        m=predict_scores(q,"multi",self.reps)
        return decision(c,m,"blend",self.threshold,self.margin,self.weight)[0]

def dispatch(rows,router,service_ms=None):
    """Simulated serial per-VM queue; routing is clocked separately."""
    service_ms=service_ms or SIMULATED_SERVICE_MS
    free={vm:0. for vm in VMS}
    clock=0.; results=[];route_time=[]
    for row in rows:
        t0=time.perf_counter()
        selected=router.predict(row["text"])
        route_time.append((time.perf_counter()-t0)*1000)
        arrival=clock
        clock+=1.0  # synthetic interarrival: 1ms
        known=row["label"]!="UNKNOWN"
        correct=known and selected==row["label"]
        if selected in VMS:
            begin=max(arrival,free[selected])
            finish=begin+service_ms[selected]
            free[selected]=finish
            turnaround=finish-arrival
        else:
            turnaround=0.0
        results.append({"text":row["text"],"gold":row["label"],"selected":selected,
                        "correct_route":correct,"turnaround_simulated_ms":turnaround})
    known=[r for r in results if r["gold"]!="UNKNOWN"]
    unknown=[r for r in results if r["gold"]=="UNKNOWN"]
    accepted=[r for r in known if r["selected"]!="UNKNOWN"]
    dispatched=[r for r in results if r["selected"]!="UNKNOWN"]
    correct=sum(r["correct_route"] for r in known)
    def ratio(n,d):return n/d if d else None
    return {"n":len(rows),"known_n":len(known),"unknown_n":len(unknown),
            "known_task_completion_proxy":ratio(correct,len(known)),
            "known_coverage":ratio(len(accepted),len(known)),
            "accepted_known_precision":ratio(correct,len(accepted)),
            "unknown_rejection_rate":ratio(sum(r["selected"]=="UNKNOWN" for r in unknown),len(unknown)),
            "unknown_false_dispatch_rate":ratio(sum(r["selected"]!="UNKNOWN" for r in unknown),len(unknown)),
            "incorrect_known_dispatches":sum(r["selected"] not in (r["gold"],"UNKNOWN") for r in known),
            "mean_routing_wall_ms":statistics.mean(route_time),
            "p95_routing_wall_ms":sorted(route_time)[max(0,int(.95*len(route_time))-1)],
            "mean_simulated_turnaround_ms_dispatched":ratio(sum(r["turnaround_simulated_ms"] for r in dispatched),len(dispatched)),
            "simulated_queue_free_at_ms":free,
            "dispatch_counts":dict(Counter(r["selected"] for r in results)),
            "details":results}

def run(rows,train,model=None,weight=.7,threshold=0.,margin=0.):
    routers={"round_robin":RoundRobin(),"keyword":KeywordRouter(),
             "tfidf":TFIDFRouter(train)}
    if model:
        from llm_sem_adapter import LLMSemAdapter
        routers["semantic_hybrid"]=HybridAdapter(LLMSemAdapter(model_path=model),
                                                  weight,threshold,margin)
    return {name:dispatch(rows,router) for name,router in routers.items()}

def main():
    p=argparse.ArgumentParser(description="v0.5 Semantic OS control-plane benchmark")
    p.add_argument("--train",default="data/dev_train_v040.csv")
    p.add_argument("--requests",default="data/validation_v043_dev100.csv")
    p.add_argument("--model",default=None,help="Enable real LLM_SEM vector dispatch")
    p.add_argument("--weight",type=float,default=.7)
    p.add_argument("--threshold",type=float,default=0.)
    p.add_argument("--margin",type=float,default=0.)
    p.add_argument("--output",default="results/os_advantage_v050.json")
    args=p.parse_args()
    if not 0<=args.weight<=1:p.error("weight must be between 0 and 1")
    train,rows=load_csv(args.train),load_csv(args.requests)
    results=run(rows,train,args.model,args.weight,args.threshold,args.margin)
    report={"version":"0.5.0","kind":"DEVELOPMENT_SIMULATION_NOT_OS_BENCHMARK",
            "setup":{"train":args.train,"requests":args.requests,"model":args.model,
                     "weight":args.weight,"threshold":args.threshold,"margin":args.margin,
                     "arrival_interval_simulated_ms":1.0,
                     "service_time_simulated_ms":SIMULATED_SERVICE_MS},
            "interpretation":["Completion is a correct-routing proxy, not actual task execution",
                              "VMs are Python labels and independent simulated queues",
                              "Routing wall-clock is measured; service and turnaround are synthetic",
                              "Router setup/checkpoint load are excluded from per-request routing latency",
                              "Latency varies with machine/warmup/order and is not directly comparable to an OS",
                              "Validation requests used in prior model/prototype exploration; NOT an independent holdout",
                              "No meaningful real resource utilization, failover, knowledge reuse or semantic IPC measured"],
            "results":results}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    for name,r in results.items():
        print(f"{name:16} completion_proxy={r['known_task_completion_proxy']:.3f} "
              f"coverage={r['known_coverage']:.3f} unknown_reject={r['unknown_rejection_rate']:.3f} "
              f"routing_wall_ms={r['mean_routing_wall_ms']:.4f}")
    print(f"Saved: {path}")
if __name__=="__main__":main()
