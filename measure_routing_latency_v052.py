"""v0.5.2 repeated, warmed, order-rotated routing-only latency.

No OS/task execution or independent holdout claim. Reconstructs routers for
each timed repetition; excludes construction time, records it separately.
"""
import argparse,json,random,statistics,time,platform
from pathlib import Path
from benchmark_v040 import load_csv,KeywordRouter,TFIDFRouter
from benchmark_os_advantage_v050 import RoundRobin,HybridAdapter

def percentile(values,p):
    data=sorted(values)
    return data[max(0,min(len(data)-1,int((len(data)-1)*p)))]

def measure(routers,rows,repeats=10,warmup=2,seed=52):
    if repeats<2 or warmup<0:raise ValueError("repeats>=2 and warmup>=0")
    times={name:[] for name in routers}
    pass_means={name:[] for name in routers}
    names=list(routers)
    for cycle in range(warmup+repeats):
        order=names[:]
        random.Random(seed+cycle).shuffle(order)
        for name in order:
            router=routers[name]()
            measured=[]
            for row in rows:
                before=time.perf_counter_ns()
                router.predict(row["text"])
                measured.append((time.perf_counter_ns()-before)/1e6)
            if cycle>=warmup:
                times[name].extend(measured)
                pass_means[name].append(statistics.mean(measured))
    return {name:{"sample_count":len(values),"repetition_count":repeats,
                  "mean_ms":statistics.mean(values),"median_ms":statistics.median(values),
                  "p95_ms":percentile(values,.95),
                  "per_run_means_ms":pass_means[name],
                  "per_run_mean_stddev_ms":statistics.stdev(pass_means[name])}
            for name,values in times.items()}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",default="data/dev_train_v040.csv")
    p.add_argument("--requests",default="data/validation_v043_dev100.csv")
    p.add_argument("--model",default=None)
    p.add_argument("--repeats",type=int,default=10)
    p.add_argument("--warmup",type=int,default=2)
    p.add_argument("--seed",type=int,default=52)
    p.add_argument("--output",default="results/repeated_latency_v052.json")
    args=p.parse_args()
    if args.repeats<2 or args.warmup<0:p.error("repeats >= 2 and warmup >= 0 required")
    train,rows=load_csv(args.train),load_csv(args.requests)
    routers={"round_robin":RoundRobin,"keyword":KeywordRouter,
             "tfidf":lambda:TFIDFRouter(train)}
    if args.model:
        from llm_sem_adapter import LLMSemAdapter
        # The model is loaded once; per-request inferencing is clocked.
        engine=LLMSemAdapter(model_path=args.model)
        routers["semantic_hybrid"]=lambda:HybridAdapter(engine,weight=.7)
    results=measure(routers,rows,args.repeats,args.warmup,args.seed)
    report={"version":"0.5.2","kind":"REPEATED_ROUTING_LATENCY_DEVELOPMENT",
            "environment":{"python":platform.python_version(),"system":platform.platform()},
            "parameters":{"train":args.train,"requests":args.requests,"model":args.model,
                          "repeats":args.repeats,"warmup":args.warmup,"seed":args.seed},
            "limitations":["Model loading and router construction excluded from routing timings",
                           "Each cycle reconstructs routers (round robin resets); within-cycle request order unchanged",
                           "CPU/GPU asynchronous work must be synchronized for strict GPU latency measurement",
                           "Individual requests in a run are correlated: per-run means are reported separately",
                           "Validation samples are previously used development fixtures",
                           "No task execution or real OS runtime comparison"],"results":results}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for name,m in results.items():print(f"{name:16s} mean={m['mean_ms']:.5f}ms p95={m['p95_ms']:.5f}ms stddev_of_run_means={m['per_run_mean_stddev_ms']:.5f}ms")
    print("Saved:",out)
if __name__=="__main__":main()
