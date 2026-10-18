"""SEMOS_SIM 0.7.19: pre-execution adaptive routing, strict phase ablation.
Synthetic classical benchmark. The supplied task profile is assumed available before search.
"""
import argparse, json, math, cmath, random, statistics
from pathlib import Path
from semantic_weighted_interference_v0716 import workload, similarity

METHODS=("KERNEL_UCB","QI_PHASE_ON","QI_PHASE_OFF","RANDOM")
PROFILES=("smooth","shuffled","multimodal")
TEMPERATURE=.1

def search(values,method,budget,seed):
    n=len(values)
    if method not in METHODS or not 1<=budget<=n:raise ValueError("search parameters")
    rng=random.Random(seed); seen={}
    for _ in range(budget):
        remaining=[i for i in range(n) if i not in seen]
        if not seen or method=="RANDOM":
            chosen=rng.choice(remaining)
        elif method=="KERNEL_UCB":
            def score(i):
                weights=[similarity(i,j,n) for j in seen]
                s=sum(weights)
                return sum(w*v for w,v in zip(weights,seen.values()))/s+.2/(1+s)
            chosen=max(remaining,key=lambda i:(score(i),-i))
        else:
            scores=[]
            for i in remaining:
                if method=="QI_PHASE_ON":
                    a=1+sum(similarity(i,j,n)*cmath.exp(1j*math.pi*(1-v)) for j,v in seen.items())
                else:
                    # EXACT phase-off ablation: same amplitude update, phi=0.
                    a=1+sum(similarity(i,j,n)*cmath.exp(0j) for j,v in seen.items())
                scores.append(math.log(max(1e-300,abs(a)**2))/TEMPERATURE)
            top=max(scores)
            weights=[math.exp(s-top) for s in scores]
            draw=rng.random()*sum(weights)
            chosen=remaining[-1]
            for i,w in zip(remaining,weights):
                draw-=w
                if draw<=0:chosen=i;break
        seen[chosen]=values[chosen]
    best=max(seen.values())
    return {"success":int(best==max(values)),"regret":max(values)-best,"calls":len(seen)}

def build_dev(n,budgets,dev_trials,seed):
    # Task-profile is an externally supplied label before the search.
    # No peek at holdout utilities or post-hoc per-instance selection.
    data={}
    for profile in PROFILES:
        for budget in budgets:
            for method in METHODS:
                rs=[search(workload(n,seed+t,profile),method,budget,seed+100000+t) for t in range(dev_trials)]
                data[(profile,budget,method)]=statistics.fmean(x["regret"] for x in rs)
    return data

def choose_routes(dev,budgets):
    routes={}
    for p in PROFILES:
        for b in budgets:
            routes[(p,b)]=min(METHODS,key=lambda m:(dev[(p,b,m)],METHODS.index(m)))
    fixed=min(METHODS,key=lambda m:(statistics.fmean(dev[(p,b,m)] for p in PROFILES for b in budgets),METHODS.index(m)))
    # Profile-aware classical-only control has the same metadata and routing overhead.
    classical=("KERNEL_UCB","RANDOM")
    control={(p,b):min(classical,key=lambda m:(dev[(p,b,m)],classical.index(m)))
             for p in PROFILES for b in budgets}
    return routes,fixed,control

def bootstrap_ci(diffs,repetitions=500,seed=9):
    r=random.Random(seed);n=len(diffs);means=[]
    for _ in range(repetitions):
        means.append(sum(diffs[r.randrange(n)] for _ in range(n))/n)
    means.sort()
    return [means[int(.025*(repetitions-1))],means[int(.975*(repetitions-1))]]

def benchmark(n=64,budgets=(8,12,24),dev_trials=40,holdout_trials=120,
              dev_seed=42,holdout_seed=40000,bootstrap=500,router_cost=.05):
    budgets=tuple(budgets)
    if n<8 or dev_trials<2 or holdout_trials<2 or bootstrap<100 or router_cost<0 or not budgets or any(b<1 or b>n for b in budgets):raise ValueError("benchmark parameters")
    if not (dev_seed+dev_trials<=holdout_seed or holdout_seed+holdout_trials<=dev_seed):raise ValueError("overlapping split")
    dev=build_dev(n,budgets,dev_trials,dev_seed)
    routes,fixed,control=choose_routes(dev,budgets)
    rows=[];contrasts=[]
    for profile in PROFILES:
        for budget in budgets:
            methods={"ADAPTIVE_ALL":routes[(profile,budget)],"ADAPTIVE_CLASSICAL":control[(profile,budget)],
                     "BEST_FIXED_DEV":fixed,"FIXED_UCB":"KERNEL_UCB",
                     "FIXED_QI":"QI_PHASE_ON","PHASE_OFF":"QI_PHASE_OFF"}
            values=[workload(n,holdout_seed+t,profile) for t in range(holdout_trials)]
            observations={}
            for label,method in methods.items():
                obs=[search(v,method,budget,holdout_seed+100000+t) for t,v in enumerate(values)]
                observations[label]=obs
                cost=router_cost if label.startswith("ADAPTIVE") else 0.
                rows.append({"profile":profile,"budget":budget,"policy":label,"selected_method":method,
                             "success":statistics.fmean(x["success"] for x in obs),
                             "mean_regret":statistics.fmean(x["regret"] for x in obs),
                             "routing_cost_per_request":cost,
                             "total_router_cost":cost*holdout_trials,
                             "equal_oracle_calls":all(x["calls"]==budget for x in obs)})
            for competitor in ("ADAPTIVE_CLASSICAL","BEST_FIXED_DEV","FIXED_UCB","FIXED_QI"):
                left=observations["ADAPTIVE_ALL"];right=observations[competitor]
                ds=[a["success"]-b["success"] for a,b in zip(left,right)]
                dr=[a["regret"]-b["regret"] for a,b in zip(left,right)]
                contrasts.append({"profile":profile,"budget":budget,"comparison":"ADAPTIVE_ALL-minus-"+competitor,
                                  "success_delta":statistics.fmean(ds),"success_ci95":bootstrap_ci(ds,bootstrap,seed=budget+9),
                                  "regret_delta":statistics.fmean(dr),"regret_ci95":bootstrap_ci(dr,bootstrap,seed=budget+19)})
            a=observations["FIXED_QI"];b=observations["PHASE_OFF"]
            ds=[x["success"]-y["success"] for x,y in zip(a,b)]
            dr=[x["regret"]-y["regret"] for x,y in zip(a,b)]
            contrasts.append({"profile":profile,"budget":budget,"comparison":"PHASE_ON-minus-PHASE_OFF",
                              "success_delta":statistics.fmean(ds),"success_ci95":bootstrap_ci(ds,bootstrap,seed=budget+29),
                              "regret_delta":statistics.fmean(dr),"regret_ci95":bootstrap_ci(dr,bootstrap,seed=budget+39)})
    return {"version":"0.7.19","kind":"PRE_EXECUTION_ROUTER_PHASE_ABLATION",
            "parameters":{"candidates":n,"budgets":list(budgets),"dev_trials":dev_trials,"holdout_trials":holdout_trials,
                          "dev_seed":dev_seed,"holdout_seed":holdout_seed,"bootstrap":bootstrap,"router_cost":router_cost},
            "fixed_dev_method":fixed,
            "routes":[{"profile":p,"budget":b,"adaptive_all":routes[(p,b)],
                      "adaptive_classical":control[(p,b)]} for p in PROFILES for b in budgets],
            "results":rows,"contrasts":contrasts,
            "limitations":["Synthetic profile labels are explicitly provided before search; a real profile classifier has not been implemented",
             "Routing cost is an assumed synthetic charge, not measured wall-clock overhead",
             "Routing selects dev-optimal methods by regret; comparisons include unadjusted multiple contrasts",
             "No equal-CPU-time evaluation; identical utility oracle calls only",
             "Classical complex amplitude heuristic; no physical quantum effect or speedup",
             "Ring similarity is not semantic embedding; no production QHA execution",
             "Exactly matched phase-off ablation freezes phase to zero but still uses a nonunitary update"]}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--candidates",type=int,default=64)
    ap.add_argument("--budgets",default="8,12,24")
    ap.add_argument("--dev-trials",type=int,default=40)
    ap.add_argument("--holdout-trials",type=int,default=120)
    ap.add_argument("--dev-seed",type=int,default=42)
    ap.add_argument("--holdout-seed",type=int,default=40000)
    ap.add_argument("--bootstrap",type=int,default=500)
    ap.add_argument("--router-cost",type=float,default=.05)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    r=benchmark(a.candidates,tuple(int(x) for x in a.budgets.split(",")),a.dev_trials,
                a.holdout_trials,a.dev_seed,a.holdout_seed,a.bootstrap,a.router_cost)
    f=Path(a.output);f.parent.mkdir(parents=True,exist_ok=True)
    with f.open("x",encoding="utf-8") as out:json.dump(r,out,ensure_ascii=False,indent=2)
    print("Wrote:",f,"fixed_dev_method:",r["fixed_dev_method"])
    for x in r["routes"]:print(x["profile"],x["budget"],"adaptive",x["adaptive_all"],"classical",x["adaptive_classical"])
if __name__=="__main__":main()
