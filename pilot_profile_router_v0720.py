"""SEMOS_SIM v0.7.20 — pilot-based profile classification and honest routing.
Only observed pilot utilities are used for classification. Pilot oracle calls count
towards budget; search continues from SAME observations without re-evaluation.
Classical simulation; no physical quantum claim.
"""
import argparse, cmath, json, math, random, statistics, time
from pathlib import Path
from semantic_weighted_interference_v0716 import workload, similarity
PROFILES=("smooth","shuffled","multimodal")
METHODS=("KERNEL_UCB","QI_PHASE_ON","QI_PHASE_OFF","RANDOM")
def sample_pilot(values,seed,k):
    if not 1<=k<=len(values):raise ValueError("pilot")
    rng=random.Random(seed)
    idx=rng.sample(range(len(values)),k)
    return {i:values[i] for i in idx}
def features(observed,n):
    pairs=sorted(observed.items())
    if len(pairs)<2:return (0.,0.)
    near=[];far=[]
    for a,(i,vi) in enumerate(pairs):
        for j,vj in pairs[a+1:]:
            d=min(abs(i-j),n-abs(i-j))
            (near if d<=n/8 else far).append(abs(vi-vj))
    return (statistics.fmean(near) if near else .5,
            statistics.fmean(far) if far else .5)
def fit_classifier(n,train_seed,train_trials,pilot):
    samples=[]
    for profile in PROFILES:
        for t in range(train_trials):
            vals=workload(n,train_seed+t,profile)
            seen=sample_pilot(vals,train_seed+100000+t,pilot)
            samples.append((profile,features(seen,n)))
    return {p:tuple(statistics.fmean(x[1][j] for x in samples if x[0]==p)
                    for j in range(2)) for p in PROFILES}
def classify(centers,feat):
    return min(PROFILES,key=lambda p:(sum((a-b)**2 for a,b in zip(centers[p],feat)),
                                   PROFILES.index(p)))
def continue_search(values,method,budget,seed,observed):
    n=len(values)
    if method not in METHODS or not len(observed)<=budget<=n:raise ValueError("search")
    seen=dict(observed);rng=random.Random(seed)
    while len(seen)<budget:
        remain=[i for i in range(n) if i not in seen]
        if method=="RANDOM":chosen=rng.choice(remain)
        elif method=="KERNEL_UCB":
            def score(i):
                weights=[similarity(i,j,n) for j in seen]
                s=sum(weights)
                return sum(w*v for w,v in zip(weights,seen.values()))/s+.2/(1+s)
            chosen=max(remain,key=lambda i:(score(i),-i))
        else:
            probs=[]
            for i in remain:
                if method=="QI_PHASE_ON":
                    z=1+sum(similarity(i,j,n)*cmath.exp(1j*math.pi*(1-v)) for j,v in seen.items())
                else:z=1+sum(similarity(i,j,n) for j in seen)
                probs.append(math.log(max(1e-300,abs(z)**2))/.1)
            high=max(probs);w=[math.exp(x-high) for x in probs]
            threshold=rng.random()*sum(w);chosen=remain[-1]
            for j,p in zip(remain,w):
                threshold-=p
                if threshold<=0:chosen=j;break
        seen[chosen]=values[chosen]
    best=max(seen.values())
    return {"success":int(best==max(values)),"regret":max(values)-best,"calls":len(seen)}
def benchmark(n=64,budgets=(8,12,24),pilot=4,train_trials=60,dev_trials=40,
              holdout_trials=120,train_seed=1000,dev_seed=10000,holdout_seed=50000):
    budgets=tuple(budgets)
    if n<8 or train_trials<2 or dev_trials<2 or holdout_trials<2 or not 2<=pilot<=min(budgets) or max(budgets)>n:
        raise ValueError("params")
    windows=[(train_seed,train_trials),(dev_seed,dev_trials),(holdout_seed,holdout_trials)]
    for i,(s,k) in enumerate(windows):
        for j,(t,l) in enumerate(windows):
            if i<j and max(s,t)<min(s+k,t+l):raise ValueError("overlapping splits")
    centers=fit_classifier(n,train_seed,train_trials,pilot)
    # Dev: route keyed by PREDICTED class, not true profile.
    routes={};classical={}
    for budget in budgets:
        accum={(p,m):[] for p in PROFILES for m in METHODS}
        for real in PROFILES:
            for t in range(dev_trials):
                v=workload(n,dev_seed+t,real)
                pilot_obs=sample_pilot(v,dev_seed+100000+t,pilot)
                predicted=classify(centers,features(pilot_obs,n))
                for m in METHODS:
                    r=continue_search(v,m,budget,dev_seed+200000+t,pilot_obs)
                    accum[(predicted,m)].append(r["regret"])
        for p in PROFILES:
            def criterion(m):
                vals=accum[(p,m)]
                # If class absent, use conservative UCB.
                return statistics.fmean(vals) if vals else float("inf")
            eligible=METHODS if any(accum[(p,m)] for m in METHODS) else ("KERNEL_UCB",)
            routes[(p,budget)]=min(eligible,key=lambda m:(criterion(m),METHODS.index(m)))
            ordinary=("KERNEL_UCB","RANDOM")
            classical[(p,budget)]=min(ordinary,key=lambda m:(criterion(m),METHODS.index(m)))
    rows=[];confusion={p:{q:0 for q in PROFILES} for p in PROFILES}
    for profile in PROFILES:
        for budget in budgets:
            observations={name:[] for name in ("ADAPTIVE_ALL","ADAPTIVE_CLASSICAL","FIXED_UCB","FIXED_QI")}
            total_times={name:[] for name in observations}
            for t in range(holdout_trials):
                v=workload(n,holdout_seed+t,profile)
                start=time.perf_counter_ns()
                pilot_obs=sample_pilot(v,holdout_seed+100000+t,pilot)
                predicted=classify(centers,features(pilot_obs,n))
                inference_ms=(time.perf_counter_ns()-start)/1e6
                if budget==budgets[0]:confusion[profile][predicted]+=1
                methods={"ADAPTIVE_ALL":routes[(predicted,budget)],
                         "ADAPTIVE_CLASSICAL":classical[(predicted,budget)],
                         "FIXED_UCB":"KERNEL_UCB","FIXED_QI":"QI_PHASE_ON"}
                for policy,m in methods.items():
                    s=time.perf_counter_ns()
                    result=continue_search(v,m,budget,holdout_seed+200000+t,pilot_obs)
                    total_times[policy].append(inference_ms+(time.perf_counter_ns()-s)/1e6)
                    observations[policy].append(result)
            for policy,rr in observations.items():
                rows.append({"profile":profile,"budget":budget,"policy":policy,
                             "success":statistics.fmean(x["success"] for x in rr),
                             "mean_regret":statistics.fmean(x["regret"] for x in rr),
                             "median_total_ms":statistics.median(total_times[policy]),
                             "equal_total_oracle_calls":all(x["calls"]==budget for x in rr)})
    return {"version":"0.7.20","kind":"PILOT_OBSERVATION_PROFILE_ROUTER",
      "parameters":{"candidates":n,"budgets":list(budgets),"pilot_calls":pilot,
                    "train_trials":train_trials,"dev_trials":dev_trials,"holdout_trials":holdout_trials,
                    "train_seed":train_seed,"dev_seed":dev_seed,"holdout_seed":holdout_seed},
      "centroids":centers,
      "routes":[{"predicted_profile":p,"budget":b,"adaptive_all":routes[(p,b)],
                 "adaptive_classical":classical[(p,b)]} for p in PROFILES for b in budgets],
      "confusion":confusion,"results":rows,
      "limitations":["Classification requires real pilot oracle calls, counted inside budget",
                     "All code classical, no physical quantum computing",
                     "Synthetic ring similarity; no real semantic embeddings or LLM",
                     "Classification relies on observed rewards, not pre-request metadata",
                     "CPU wall clock is workload/hardware dependent",
                     "No confidence intervals or equal-clock-time policy comparison in this milestone",
                     "All policies share the same pilot observations and inference charge"]}
def main():
    p=argparse.ArgumentParser()
    for name,default in (("candidates",64),("pilot",4),("train-trials",60),
                          ("dev-trials",40),("holdout-trials",120),("train-seed",1000),
                          ("dev-seed",10000),("holdout-seed",50000)):
        p.add_argument("--"+name,type=int,default=default)
    p.add_argument("--budgets",default="8,12,24")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    r=benchmark(a.candidates,tuple(map(int,a.budgets.split(","))),a.pilot,
                a.train_trials,a.dev_trials,a.holdout_trials,
                a.train_seed,a.dev_seed,a.holdout_seed)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print("Wrote:",out)
    print("confusion:",r["confusion"])
if __name__=="__main__":main()
