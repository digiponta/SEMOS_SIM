"""SEMOS_SIM v0.7.15: quantum-inspired phase/diffusion ablation.
Classical simulation, matched oracle calls, deterministic synthetic landscapes.
No claim of physical quantum speedup.
"""
import argparse, cmath, json, math, random, statistics, time
from pathlib import Path
METHODS=("RANDOM","GREEDY","QI_PHASE_ONLY","QI_DIFFUSION_ONLY","QI_PHASE_DIFFUSION")
LANDSCAPES=("smooth","shuffled","multimodal")

def landscape(n,seed,kind):
    if n<8 or kind not in LANDSCAPES: raise ValueError("landscape parameters")
    rng=random.Random(seed)
    if kind=="smooth":
        p=rng.randrange(n)
        vals=[.85*math.exp(-min(abs(i-p),n-abs(i-p))**2/25)+.15*rng.random() for i in range(n)]
    elif kind=="multimodal":
        peaks=rng.sample(range(n),3)
        vals=[max(.8*math.exp(-min(abs(i-p),n-abs(i-p))**2/6)
                  for p in peaks)+.2*rng.random() for i in range(n)]
    else:
        vals=[rng.random() for _ in range(n)]
    if kind=="shuffled":
        # iid random independent utility is the negative control for structure
        pass
    return vals

def pick(weights,rng,eligible):
    total=sum(weights[i] for i in eligible)
    if total<=0: return rng.choice(eligible)
    threshold=rng.random()*total
    for i in eligible:
        threshold-=weights[i]
        if threshold<=0: return i
    return eligible[-1]

def run(values,method,budget,seed,phase_scale=math.pi):
    n=len(values)
    if method not in METHODS or not 1<=budget<=n or phase_scale<0:
        raise ValueError("run parameters")
    rng=random.Random(seed)
    amp=[complex(1/math.sqrt(n)) for _ in range(n)]
    seen={};ops=0;trajectory=[]
    for _ in range(budget):
        left=[i for i in range(n) if i not in seen]
        if not seen or method=="RANDOM":
            idx=rng.choice(left)
        elif method=="GREEDY":
            best=max(seen,key=lambda i:(seen[i],-i))
            neighbors=[(best+d)%n for d in (-2,-1,1,2)]
            available=[i for i in neighbors if i not in seen]
            idx=available[0] if available else rng.choice(left)
            ops+=4
        else:
            if method in ("QI_PHASE_ONLY","QI_PHASE_DIFFUSION"):
                for i,v in seen.items():
                    amp[i]*=cmath.exp(1j*phase_scale*(1-v))
                ops+=len(seen)
            if method in ("QI_DIFFUSION_ONLY","QI_PHASE_DIFFUSION"):
                mean=sum(amp)/n
                amp=[2*mean-a for a in amp]
                ops+=3*n
            idx=pick([abs(z)**2 for z in amp],rng,left)
            ops+=n
        seen[idx]=values[idx]
        trajectory.append(max(seen.values()))
    optimal=max(values)
    return {"best":max(seen.values()),"regret":optimal-max(seen.values()),
            "success":int(max(seen.values())==optimal),
            "oracle_calls":len(seen),"operations_proxy":ops,"curve":trajectory}

def benchmark(n=64,budgets=(4,8,12,24),trials=40,seed=42,phase_scale=math.pi):
    budgets=tuple(budgets)
    if trials<1 or not budgets or any(b<1 or b>n for b in budgets):
        raise ValueError("benchmark parameters")
    rows=[]
    for kind in LANDSCAPES:
        for budget in budgets:
            samples={name:[] for name in METHODS}
            for trial in range(trials):
                values=landscape(n,seed+trial,kind)
                for name in METHODS:
                    samples[name].append(run(values,name,budget,seed+10000+trial,phase_scale))
            for name in METHODS:
                rs=samples[name]
                rows.append({"landscape":kind,"budget":budget,"method":name,
                             "trials":trials,"success_at_budget":sum(r["success"] for r in rs)/trials,
                             "mean_regret":statistics.fmean(r["regret"] for r in rs),
                             "mean_best":statistics.fmean(r["best"] for r in rs),
                             "mean_operations_proxy":statistics.fmean(r["operations_proxy"] for r in rs),
                             "equal_oracle_calls":all(r["oracle_calls"]==budget for r in rs)})
    ablations=[]
    for kind in LANDSCAPES:
        for budget in budgets:
            lookup={r["method"]:r for r in rows if r["landscape"]==kind and r["budget"]==budget}
            a=lookup["QI_PHASE_DIFFUSION"];b=lookup["QI_PHASE_ONLY"]
            ablations.append({"landscape":kind,"budget":budget,
                 "interference_success_delta":a["success_at_budget"]-b["success_at_budget"],
                 "interference_regret_delta":a["mean_regret"]-b["mean_regret"],
                 "interference_extra_operations":a["mean_operations_proxy"]-b["mean_operations_proxy"]})
    return {"version":"0.7.15","kind":"SYNTHETIC_QI_ABLATION_SWEEP",
            "parameters":{"candidates":n,"budgets":list(budgets),"trials":trials,"seed":seed,
                          "phase_scale":phase_scale},"results":rows,"ablations":ablations,
            "limitations":["All algorithms run classically; no physical quantum computation",
               "Matching candidate evaluation budgets, not matching CPU time",
               "Synthetic oracle utilities, not Semantic Memory",
               "Candidate phase uses only observed utility; no hidden-optimum oracle",
               "Operation proxy is not wall clock time",
               "Smooth and multimodal tasks encode neighborhood structure; shuffled task is iid",
               "Phase-only and diffusion-only preserve uniform magnitude in this setup"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",type=int,default=64)
    p.add_argument("--budgets",default="4,8,12,24")
    p.add_argument("--trials",type=int,default=40)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--phase-scale",type=float,default=math.pi)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=benchmark(a.candidates,[int(x) for x in a.budgets.split(",")],
                     a.trials,a.seed,a.phase_scale)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:
        json.dump(report,f,indent=2,ensure_ascii=False)
    print("Wrote:",out)
    for r in report["ablations"]:
        print(r["landscape"],"budget",r["budget"],"interference_success_delta",
              round(r["interference_success_delta"],4),"regret_delta",
              round(r["interference_regret_delta"],4))
if __name__=="__main__":main()
