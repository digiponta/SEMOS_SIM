"""SEMOS_SIM v0.7.14: fair-budget classical quantum-inspired search benchmark.

Quantum-inspired means simulated complex amplitudes; no quantum computer or speedup claim.
All methods see utilities only after a candidate evaluation. Equal oracle-call budgets.
"""
import argparse
import cmath
import json
import math
import random
from pathlib import Path

METHODS=("GREEDY","BEAM","RANDOM","QI_INTERFERENCE","QI_NO_INTERFERENCE")

def landscape(n,seed):
    if n<8:raise ValueError("n must be >= 8")
    rng=random.Random(seed)
    peak=rng.randrange(n)
    secondary=rng.randrange(n)
    values=[]
    for i in range(n):
        d=min(abs(i-peak),n-abs(i-peak))
        e=min(abs(i-secondary),n-abs(i-secondary))
        values.append(max(0.,min(1.,0.72*math.exp(-d*d/18)+
                       0.18*math.exp(-e*e/8)+0.1*rng.random())))
    return values

def choose_weighted(weights,rng):
    total=sum(weights)
    if total<=0:return rng.randrange(len(weights))
    t=rng.random()*total
    for i,w in enumerate(weights):
        t-=w
        if t<=0:return i
    return len(weights)-1

def search(values,method,budget=12,seed=0):
    n=len(values)
    if method not in METHODS:raise ValueError("unknown method")
    if budget<1 or budget>n:raise ValueError("budget must be in 1..n")
    rng=random.Random(seed)
    visited={}
    amplitudes=[complex(1/math.sqrt(n)) for _ in range(n)]
    path=[]
    operations=0
    for step in range(budget):
        remaining=[i for i in range(n) if i not in visited]
        if not visited:
            candidate=rng.randrange(n)
        elif method=="RANDOM":
            candidate=rng.choice(remaining)
        elif method in ("GREEDY","BEAM"):
            ranking=sorted(visited,key=lambda i:(-visited[i],i))
            sources=ranking[:1 if method=="GREEDY" else min(4,len(ranking))]
            proposed=[]
            for idx in sources:
                for offset in (-2,-1,1,2):
                    x=(idx+offset)%n
                    if x not in visited and x not in proposed:proposed.append(x)
            candidate=proposed[0] if proposed else rng.choice(remaining)
            operations+=len(sources)*4
        else:
            # All amplitude transformations use already observed utilities only.
            # Phase kick depends on measured utility; unmeasured positions are untouched.
            # Diffusion creates classical complex-amplitude interference (not quantum speedup).
            if method=="QI_INTERFERENCE":
                for idx,utility in visited.items():
                    amplitudes[idx]*=cmath.exp(1j*math.pi*(1-utility))
                mean=sum(amplitudes)/n
                amplitudes=[2*mean-x for x in amplitudes]
                operations+=3*n+len(visited)
            else:
                for idx,utility in visited.items():
                    amplitudes[idx]*=cmath.exp(1j*math.pi*(1-utility))
                operations+=len(visited)
            weights=[abs(amplitudes[i])**2 if i not in visited else 0.
                     for i in range(n)]
            candidate=choose_weighted(weights,rng)
            if candidate in visited:candidate=rng.choice(remaining)
        visited[candidate]=values[candidate]
        path.append(max(visited.values()))
    optimum=max(values)
    return {"method":method,"oracle_calls":len(visited),"best":max(visited.values()),
            "regret":optimum-max(visited.values()),
            "success":int(max(visited.values())>=optimum-1e-12),
            "search_operations_proxy":operations,"best_by_step":path}

def compare(n=64,budget=12,trials=30,seed=42):
    if trials<1:raise ValueError("trials >=1")
    samples={m:[] for m in METHODS}
    for t in range(trials):
        vals=landscape(n,seed+t)
        for m in METHODS:
            r=search(vals,m,budget,seed=seed+100000+t)
            samples[m].append(r)
    rows=[]
    for m,results in samples.items():
        rows.append({"method":m,"trials":trials,
                     "success_at_budget":sum(x["success"] for x in results)/trials,
                     "mean_regret":sum(x["regret"] for x in results)/trials,
                     "mean_best":sum(x["best"] for x in results)/trials,
                     "mean_operations_proxy":sum(x["search_operations_proxy"] for x in results)/trials,
                     "mean_success_curve":[sum(x["best_by_step"][i] for x in results)/trials
                                           for i in range(budget)],
                     "all_oracle_calls_equal":all(x["oracle_calls"]==budget for x in results)})
    return {"version":"0.7.14","kind":"SYNTHETIC_QUANTUM_INSPIRED_SEARCH",
            "parameters":{"candidates":n,"budget":budget,"trials":trials,"seed":seed},
            "results":rows,
            "interference_ablation":{"qi_minus_no_interference_success":
                 next(x["success_at_budget"] for x in rows if x["method"]=="QI_INTERFERENCE")-
                 next(x["success_at_budget"] for x in rows if x["method"]=="QI_NO_INTERFERENCE")},
            "limitations":["No physical quantum states, entanglement or quantum speedup",
               "Synthetic smooth utility landscape on a ring; no real Semantic Memory or NDC",
               "All methods have same utility oracle and evaluation budget, not equal CPU operations",
               "Diffusion transforms classical complex amplitudes and may not improve success",
               "QI_NO_INTERFERENCE uses phase kicks without amplitude mixing (uniform selection)",
               "Search-operation proxy is algorithmic bookkeeping, not measured runtime",
               "Score is revealed only after the chosen index is evaluated"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",type=int,default=64)
    p.add_argument("--budget",type=int,default=12)
    p.add_argument("--trials",type=int,default=30)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=compare(a.candidates,a.budget,a.trials,a.seed)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",path)
    for x in report["results"]:
        print(x["method"],"success",round(x["success_at_budget"],4),
              "regret",round(x["mean_regret"],4),"ops_proxy",round(x["mean_operations_proxy"],1))
if __name__=="__main__":main()
