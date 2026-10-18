"""SEMOS_SIM v0.7.17: held-out, paired bootstrap, classical softmax control.

Independent landscape seeds, common initial candidate, same oracle-call budget.
Runtime is wall-clock diagnostic, not hardware-neutral reproducible evidence.
"""
import argparse,json,math,random,statistics,time
from pathlib import Path
from semantic_weighted_interference_v0716 import workload,similarity,search as legacy_search
METHODS=("RANDOM","KERNEL_UCB","SOFTMAX_KERNEL","QI_KERNEL_PHASE")
KINDS=("smooth","shuffled","multimodal")

def weighted_choice(items,weights,rng):
    total=sum(weights)
    if total<=0:return rng.choice(items)
    draw=rng.random()*total
    for item,w in zip(items,weights):
        draw-=w
        if draw<=0:return item
    return items[-1]

def trial(values,method,budget,seed,strength=1.0,temperature=.2):
    n=len(values)
    if method not in METHODS or not (1<=budget<=n) or temperature<=0 or strength<0:
        raise ValueError("trial parameters")
    rng=random.Random(seed); seen={}
    started=time.perf_counter_ns()
    while len(seen)<budget:
        remaining=[i for i in range(n) if i not in seen]
        if not seen:
            index=rng.randrange(n)
        elif method=="RANDOM":
            index=rng.choice(remaining)
        elif method=="KERNEL_UCB":
            def score(i):
                w=[similarity(i,j,n) for j in seen]
                s=sum(w)
                return sum(x*v for x,v in zip(w,seen.values()))/s + .2/(1+s)
            index=max(remaining,key=lambda i:(score(i),-i))
        else:
            scores=[]
            for i in remaining:
                if method=="SOFTMAX_KERNEL":
                    weights=[similarity(i,j,n) for j in seen]
                    s=sum(weights)
                    value=sum(w*v for w,v in zip(weights,seen.values()))/s + .2/(1+s)
                    scores.append(value)
                else:
                    real=1.0;imag=0.0
                    for j,v in seen.items():
                        k=strength*similarity(i,j,n)
                        phi=math.pi*(1-v)
                        real+=k*math.cos(phi);imag+=k*math.sin(phi)
                    scores.append(math.log(max(1e-300,real*real+imag*imag)))
            z=max(scores)
            weights=[math.exp((x-z)/temperature) for x in scores]
            index=weighted_choice(remaining,weights,rng)
        seen[index]=values[index]
    duration=(time.perf_counter_ns()-started)/1e6
    best=max(seen.values())
    return {"success":int(best==max(values)),"regret":max(values)-best,
            "best":best,"calls":len(seen),"milliseconds":duration}

def paired_interval(differences,replications=1500,seed=123):
    if not differences:raise ValueError("empty differences")
    rng=random.Random(seed);n=len(differences)
    draws=[]
    for _ in range(replications):
        draws.append(statistics.fmean(differences[rng.randrange(n)] for _ in range(n)))
    draws.sort()
    return [draws[int(.025*(replications-1))],draws[int(.975*(replications-1))]]

def benchmark(n=64,budgets=(8,12,24),trials=120,seed=10000,
              strength=1.,temperature=.2,bootstrap=1000):
    if n<8 or trials<2 or bootstrap<100 or any(not 1<=b<=n for b in budgets):
        raise ValueError("benchmark settings")
    rows=[];contrasts=[]
    for kind in KINDS:
        for budget in budgets:
            values=[workload(n,seed+t,kind) for t in range(trials)]
            obs={m:[trial(v,m,budget,seed+100000+t,strength,temperature)
                    for t,v in enumerate(values)] for m in METHODS}
            for m,ss in obs.items():
                rows.append({"landscape":kind,"budget":budget,"method":m,
                    "trials":trials,"success_at_budget":statistics.fmean(x["success"] for x in ss),
                    "mean_regret":statistics.fmean(x["regret"] for x in ss),
                    "median_runtime_ms":statistics.median(x["milliseconds"] for x in ss),
                    "all_equal_calls":all(x["calls"]==budget for x in ss)})
            for other in ("KERNEL_UCB","SOFTMAX_KERNEL","RANDOM"):
                q=obs["QI_KERNEL_PHASE"];baseline=obs[other]
                sd=[x["success"]-y["success"] for x,y in zip(q,baseline)]
                rd=[x["regret"]-y["regret"] for x,y in zip(q,baseline)]
                contrasts.append({"landscape":kind,"budget":budget,"comparison":"QI-minus-"+other,
                    "success_difference":statistics.fmean(sd),
                    "success_95ci":paired_interval(sd,bootstrap,seed+budget),
                    "regret_difference":statistics.fmean(rd),
                    "regret_95ci":paired_interval(rd,bootstrap,seed+budget+1)})
    return {"version":"0.7.17","kind":"HELDOUT_MATCHED_SEMANTIC_KERNEL_SEARCH",
        "parameters":{"candidates":n,"budgets":list(budgets),"trials":trials,
                      "holdout_seed_start":seed,"strength":strength,
                      "softmax_temperature":temperature,"bootstrap":bootstrap},
        "results":rows,"contrasts":contrasts,
        "limitations":["No trained hyperparameters here; held-out seed block independent of v0.7.16",
          "Ring kernel is synthetic, not a semantic embedding",
          "All algorithms execute on CPU and use same oracle calls, not equal compute budget",
          "Wall clock timings are diagnostics, affected by Python runtime and system load",
          "Bootstrap intervals quantify variability over synthetic seeded trials, not external generalization",
          "Methods have same kernel but different deterministic/stochastic policy",
          "No physical quantum calculation or quantum advantage claim"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",type=int,default=64)
    p.add_argument("--budgets",default="8,12,24")
    p.add_argument("--trials",type=int,default=120)
    p.add_argument("--seed",type=int,default=10000)
    p.add_argument("--strength",type=float,default=1.)
    p.add_argument("--temperature",type=float,default=.2)
    p.add_argument("--bootstrap",type=int,default=1000)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    result=benchmark(a.candidates,tuple(int(x) for x in a.budgets.split(",")),
                     a.trials,a.seed,a.strength,a.temperature,a.bootstrap)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print("Wrote:",path)
    for c in result["contrasts"]:
        print(c["landscape"],"budget",c["budget"],c["comparison"],
              "success_delta",round(c["success_difference"],4),
              "95CI",tuple(round(v,4) for v in c["success_95ci"]))
if __name__=="__main__":main()
