"""SEMOS_SIM v0.7.21: pilot count, kNN/centroid, confidence fallback.
All pilots are paid oracle calls; all search policies reuse the same pilots.
Classifiers never see holdout labels when predicting or tuning routes.
"""
import argparse,json,math,random,statistics,time
from pathlib import Path
from pilot_profile_router_v0720 import PROFILES,METHODS,sample_pilot,features,continue_search
from semantic_weighted_interference_v0716 import workload
PILOTS=(2,4,6)
CLASSIFIERS=("CENTROID","KNN3")
def training(n,seed,trials,pilot):
    return [(p,features(sample_pilot(workload(n,seed+t,p),
        seed+100000+t,pilot),n)) for p in PROFILES for t in range(trials)]
def prediction(data,feature,kind):
    if kind not in CLASSIFIERS:raise ValueError("classifier")
    if kind=="CENTROID":
        points=[(p,tuple(statistics.fmean(f[j] for q,f in data if q==p)
                            for j in range(2))) for p in PROFILES]
    else:points=data
    ranked=sorted(((sum((a-b)**2 for a,b in zip(feature,f)),p) for p,f in points),
                  key=lambda x:(x[0],PROFILES.index(x[1])))
    if kind=="CENTROID":
        best=ranked[0][1]
        margin=(math.sqrt(ranked[1][0])-math.sqrt(ranked[0][0]))
    else:
        nearest=ranked[:min(3,len(ranked))]
        best=min(PROFILES,key=lambda p:(-sum(x[1]==p for x in nearest),PROFILES.index(p)))
        ordered=sorted([sum(x[1]==p for x in nearest) for p in PROFILES],reverse=True)
        margin=(ordered[0]-ordered[1])/len(nearest)
    return best,margin
def route_table(data,n,dev_seed,dev_trials,pilot,kind,budgets):
    buckets={(p,b,m):[] for p in PROFILES for b in budgets for m in METHODS}
    for p in PROFILES:
        for t in range(dev_trials):
            v=workload(n,dev_seed+t,p)
            observed=sample_pilot(v,dev_seed+100000+t,pilot)
            pred,_=prediction(data,features(observed,n),kind)
            for b in budgets:
                for m in METHODS:
                    r=continue_search(v,m,b,dev_seed+200000+t,observed)
                    buckets[(pred,b,m)].append(r["regret"])
    routes={}
    for p in PROFILES:
        for b in budgets:
            candidates=[m for m in METHODS if buckets[(p,b,m)]]
            routes[(p,b)]=min(candidates,key=lambda m:(statistics.fmean(buckets[(p,b,m)]),METHODS.index(m))) if candidates else "KERNEL_UCB"
    return routes
def benchmark(n=64,budgets=(8,12,24),pilots=PILOTS,train_trials=60,
              dev_trials=40,holdout_trials=120,train_seed=1000,
              dev_seed=10000,holdout_seed=60000,confidence=.05):
    budgets=tuple(budgets);pilots=tuple(pilots)
    if n<8 or min(train_trials,dev_trials,holdout_trials)<2 or not budgets or not pilots or confidence<0:
        raise ValueError("settings")
    if any(p<2 or p>min(budgets) for p in pilots) or max(budgets)>n:raise ValueError("pilot budget")
    windows=[(train_seed,train_trials),(dev_seed,dev_trials),(holdout_seed,holdout_trials)]
    if any(max(a,c)<min(a+b,c+d) for i,(a,b) in enumerate(windows) for c,d in windows[i+1:]):
        raise ValueError("overlapping seeds")
    rows=[];matrices=[]
    for pilot in pilots:
        data=training(n,train_seed,train_trials,pilot)
        for kind in CLASSIFIERS:
            routes=route_table(data,n,dev_seed,dev_trials,pilot,kind,budgets)
            confusion={p:{q:0 for q in PROFILES} for p in PROFILES}
            for profile in PROFILES:
                # identical observations for each budget, to ensure within-pilot paired comparison
                for b in budgets:
                    observed_runs={k:[] for k in ("ADAPTIVE","CONFIDENCE_FALLBACK","FIXED_UCB","FIXED_QI")}
                    elapsed={k:[] for k in observed_runs}
                    rejected=0
                    for t in range(holdout_trials):
                        v=workload(n,holdout_seed+t,profile)
                        start=time.perf_counter_ns()
                        obs=sample_pilot(v,holdout_seed+100000+t,pilot)
                        predicted,margin=prediction(data,features(obs,n),kind)
                        classification_ms=(time.perf_counter_ns()-start)/1e6
                        if b==budgets[0]:confusion[profile][predicted]+=1
                        fallback=(margin<confidence)
                        rejected+=fallback
                        policies={"ADAPTIVE":routes[(predicted,b)],
                                  "CONFIDENCE_FALLBACK":"KERNEL_UCB" if fallback else routes[(predicted,b)],
                                  "FIXED_UCB":"KERNEL_UCB","FIXED_QI":"QI_PHASE_ON"}
                        for name,method in policies.items():
                            start=time.perf_counter_ns()
                            result=continue_search(v,method,b,holdout_seed+200000+t,obs)
                            runtime=(time.perf_counter_ns()-start)/1e6
                            # fixed policies do not pay classification, only same pilot gathering.
                            actual_time=runtime+(classification_ms if name in ("ADAPTIVE","CONFIDENCE_FALLBACK") else 0)
                            observed_runs[name].append(result);elapsed[name].append(actual_time)
                    for name,rr in observed_runs.items():
                        rows.append({"pilot":pilot,"classifier":kind,"profile":profile,"budget":b,"policy":name,
                            "success":statistics.fmean(x["success"] for x in rr),
                            "mean_regret":statistics.fmean(x["regret"] for x in rr),
                            "median_runtime_ms":statistics.median(elapsed[name]),
                            "classifier_fallback_rate":rejected/holdout_trials if name=="CONFIDENCE_FALLBACK" else 0,
                            "equal_oracle_calls":all(x["calls"]==b for x in rr)})
            matrices.append({"pilot":pilot,"classifier":kind,"confusion":confusion,
                "accuracy":sum(confusion[p][p] for p in PROFILES)/(holdout_trials*len(PROFILES)),
                "routes":[{"predicted":p,"budget":b,"method":routes[(p,b)]} for p in PROFILES for b in budgets]})
    return {"version":"0.7.21","kind":"PILOT_CLASSIFIER_SENSITIVITY",
        "parameters":{"candidates":n,"pilots":list(pilots),"budgets":list(budgets),
         "train_trials":train_trials,"dev_trials":dev_trials,"holdout_trials":holdout_trials,
         "train_seed":train_seed,"dev_seed":dev_seed,"holdout_seed":holdout_seed,
         "confidence_threshold":confidence},"classifiers":matrices,"results":rows,
        "limitations":["Ring utilities and similarity are synthetic, not Semantic Memory embeddings",
         "Classifier features use paid pilot utilities, counted within each oracle budget",
         "Classifier confidence is an uncalibrated margin; abstention is heuristic",
         "Fixed policies skip classification runtime while reusing the same paid pilots",
         "No paired confidence intervals or equal wall-clock stopping rule",
         "All techniques execute classically; no quantum speedup"]}
def main():
    a=argparse.ArgumentParser()
    a.add_argument("--candidates",type=int,default=64)
    a.add_argument("--budgets",default="8,12,24")
    a.add_argument("--pilots",default="2,4,6")
    for flag,default in [("train-trials",60),("dev-trials",40),("holdout-trials",120),
                          ("train-seed",1000),("dev-seed",10000),("holdout-seed",60000)]:
        a.add_argument("--"+flag,type=int,default=default)
    a.add_argument("--confidence",type=float,default=.05)
    a.add_argument("--output",required=True)
    x=a.parse_args()
    r=benchmark(x.candidates,tuple(map(int,x.budgets.split(","))),
                tuple(map(int,x.pilots.split(","))),x.train_trials,x.dev_trials,
                x.holdout_trials,x.train_seed,x.dev_seed,x.holdout_seed,x.confidence)
    path=Path(x.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf8") as f:json.dump(r,f,indent=2,ensure_ascii=False)
    print("Wrote:",path)
    for v in r["classifiers"]:print(v["pilot"],v["classifier"],"accuracy",round(v["accuracy"],4))
if __name__=="__main__":main()
