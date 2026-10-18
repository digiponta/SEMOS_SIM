"""SEMOS_SIM v0.7.18: isolated phase/temperature comparison.
All search is classical. Fixed dev/holdout split and identical candidate oracle budgets.
"""
import argparse,cmath,json,math,random,statistics,time
from pathlib import Path
from semantic_weighted_interference_v0716 import workload,similarity
METHODS=("QI_COMPLEX","REAL_AMPLITUDE","REAL_KERNEL_SOFTMAX","KERNEL_UCB","RANDOM")
TEMPERATURES=(0.1,0.2,0.5,1.0)
KINDS=("smooth","shuffled","multimodal")

def weighted(items,logits,rng):
    hi=max(logits)
    weights=[math.exp(x-hi) for x in logits]
    threshold=rng.random()*sum(weights)
    for item,w in zip(items,weights):
        threshold-=w
        if threshold<=0:return item
    return items[-1]

def candidate_scores(n,observed,method,strength=1.0):
    if method not in METHODS or strength<0:raise ValueError("method/strength")
    remain=[i for i in range(n) if i not in observed]
    scores=[]
    for i in remain:
        if method=="RANDOM":scores.append(0.0);continue
        if not observed:scores.append(0.0);continue
        similarities=[similarity(i,j,n) for j in observed]
        total=sum(similarities)
        estimate=sum(w*v for w,v in zip(similarities,observed.values()))/total
        if method=="KERNEL_UCB":score=estimate+0.2/(1+total)
        elif method=="REAL_KERNEL_SOFTMAX":score=estimate+0.2/(1+total)
        elif method=="REAL_AMPLITUDE":
            amplitude=1+strength*sum(w*(2*v-1) for w,v in zip(similarities,observed.values()))
            score=math.log(max(amplitude*amplitude,1e-300))
        else:
            amplitude=1+strength*sum(w*cmath.exp(1j*math.pi*(1-v))
                           for w,v in zip(similarities,observed.values()))
            score=math.log(max(abs(amplitude)**2,1e-300))
        scores.append(score)
    return remain,scores

def search(values,method,budget,seed,temperature=0.2,strength=1.0):
    n=len(values)
    if method not in METHODS or not 1<=budget<=n or temperature<=0:
        raise ValueError("invalid search")
    rng=random.Random(seed);observed={}
    start=time.perf_counter_ns()
    for _ in range(budget):
        remain,scores=candidate_scores(n,observed,method,strength)
        if not observed or method=="RANDOM":idx=rng.choice(remain)
        elif method=="KERNEL_UCB":idx=max(zip(remain,scores),key=lambda x:(x[1],-x[0]))[0]
        else:idx=weighted(remain,[s/temperature for s in scores],rng)
        observed[idx]=values[idx]
    elapsed=(time.perf_counter_ns()-start)/1e6
    best=max(observed.values())
    return {"success":int(best==max(values)),"regret":max(values)-best,
            "calls":len(observed),"runtime_ms":elapsed}

def interval(differences,bootstrap=500,seed=991):
    rng=random.Random(seed)
    n=len(differences);means=[]
    for _ in range(bootstrap):
        means.append(sum(differences[rng.randrange(n)] for _ in range(n))/n)
    means.sort()
    return [means[int((bootstrap-1)*.025)],means[int((bootstrap-1)*.975)]]

def run_batch(kind,budget,trials,seed,method,temperature):
    return [search(workload(64,seed+t,kind),method,budget,seed+100000+t,temperature)
            for t in range(trials)]

def benchmark(dev_trials=40,holdout_trials=120,dev_seed=42,
              holdout_seed=30000,budgets=(8,12,24),bootstrap=500):
    if dev_trials<2 or holdout_trials<2 or bootstrap<100 or any(not 1<=b<=64 for b in budgets):
        raise ValueError("invalid benchmark")
    if not (dev_seed+dev_trials<=holdout_seed or holdout_seed+holdout_trials<=dev_seed):
        raise ValueError("overlapping dev and holdout")
    rows=[];contrasts=[]
    for kind in KINDS:
        for budget in budgets:
            tuned={}
            for method in METHODS:
                options=(TEMPERATURES if method in METHODS[:3] else (0.2,))
                candidates=[]
                for temp in options:
                    results=run_batch(kind,budget,dev_trials,dev_seed,method,temp)
                    # Decide once using dev only: lowest regret, then higher success.
                    candidates.append((statistics.fmean(r["regret"] for r in results),
                                      -statistics.fmean(r["success"] for r in results),temp))
                tuned[method]=min(candidates)[2]
            observations={}
            for method in METHODS:
                result=run_batch(kind,budget,holdout_trials,holdout_seed,method,tuned[method])
                observations[method]=result
                rows.append({"landscape":kind,"budget":budget,"method":method,
                     "selected_temperature":tuned[method],"dev_trials":dev_trials,
                     "holdout_trials":holdout_trials,
                     "holdout_success":statistics.fmean(x["success"] for x in result),
                     "holdout_mean_regret":statistics.fmean(x["regret"] for x in result),
                     "median_runtime_ms":statistics.median(x["runtime_ms"] for x in result),
                     "same_oracle_budget":all(x["calls"]==budget for x in result)})
            q=observations["QI_COMPLEX"]
            for baseline in ("REAL_AMPLITUDE","REAL_KERNEL_SOFTMAX","KERNEL_UCB","RANDOM"):
                other=observations[baseline]
                ds=[x["success"]-y["success"] for x,y in zip(q,other)]
                dr=[x["regret"]-y["regret"] for x,y in zip(q,other)]
                contrasts.append({"landscape":kind,"budget":budget,
                    "comparison":"QI_COMPLEX-minus-"+baseline,
                    "success_delta":statistics.fmean(ds),
                    "success_ci95":interval(ds,bootstrap,991+budget),
                    "regret_delta":statistics.fmean(dr),
                    "regret_ci95":interval(dr,bootstrap,1991+budget)})
    return {"version":"0.7.18","kind":"DEV_TUNED_HOLDOUT_COMPLEX_PHASE_ABLATION",
            "parameters":{"dev_trials":dev_trials,"holdout_trials":holdout_trials,
                "dev_seed":dev_seed,"holdout_seed":holdout_seed,
                "budgets":list(budgets),"temperatures":list(TEMPERATURES),"bootstrap":bootstrap},
            "results":rows,"contrasts":contrasts,
            "limitations":["All methods classical; no quantum speedup",
                "Ring kernel is not a real semantic embedding",
                "Phase and real-amplitude equations differ beyond removing imaginary component",
                "Matched oracle-call count, not matched CPU budget",
                "Fixed temperature grid tuned independently per method on dev-only seeds",
                "Multiple comparisons and synthetic holdout constrain generalization",
                "CPU timing reflects the local machine and measurement noise"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dev-trials",type=int,default=40)
    p.add_argument("--holdout-trials",type=int,default=120)
    p.add_argument("--dev-seed",type=int,default=42)
    p.add_argument("--holdout-seed",type=int,default=30000)
    p.add_argument("--budgets",default="8,12,24")
    p.add_argument("--bootstrap",type=int,default=500)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=benchmark(a.dev_trials,a.holdout_trials,a.dev_seed,a.holdout_seed,
                     tuple(int(x) for x in a.budgets.split(",")),a.bootstrap)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print("Wrote:",path)
    for c in result["contrasts"]:
        print(c["landscape"],"budget",c["budget"],c["comparison"],
              "success_delta",round(c["success_delta"],4),
              "95CI",tuple(round(x,4) for x in c["success_ci95"]))
if __name__=="__main__":main()
