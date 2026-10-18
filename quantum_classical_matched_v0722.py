"""SEMOS_SIM v0.7.22 — matched one-step quantum-vs-classical benchmarks.
Uses v0.7.21 QuantumRegister and semantic phase construction, no hidden utility oracle.
"""
import argparse,json,math,random,statistics,time
from pathlib import Path
from quantum_state_semantic_v0721 import QuantumRegister,semantic_phase_angles
from semantic_weighted_interference_v0716 import workload,similarity

METHODS=("RANDOM","KERNEL_UCB","KERNEL_SOFTMAX","QI_PHASE_ONLY","QI_PHASE_DIFFUSION")
ROUNDS=(0,1,2,3)
KINDS=("smooth","shuffled","multimodal")

def choose(n,observed,method,seed,rounds=1,temperature=.2):
    if method not in METHODS or not 0<=rounds<=20 or temperature<=0 or not observed or len(observed)>=n:
        raise ValueError("choose settings")
    unseen=[i for i in range(n) if i not in observed];rng=random.Random(seed)
    if method=="RANDOM":return unseen[rng.randrange(len(unseen))],0.
    if method in ("KERNEL_UCB","KERNEL_SOFTMAX"):
        scores=[]
        for i in unseen:
            ww=[similarity(i,j,n) for j in observed];s=sum(ww)
            scores.append(sum(w*v for w,v in zip(ww,observed.values()))/s+.2/(1+s))
        if method=="KERNEL_UCB":
            return unseen[max(range(len(unseen)),key=lambda k:(scores[k],-unseen[k]))],0.
        hi=max(scores);weights=[math.exp((x-hi)/temperature) for x in scores]
    else:
        q=QuantumRegister(max(1,(n-1).bit_length()));q.superpose()
        angles=semantic_phase_angles(n,observed,lambda i,j:similarity(i,j,n))
        angles.extend([0.]*(q.n-n))
        for _ in range(rounds):
            q.phase_oracle(angles)
            if method=="QI_PHASE_DIFFUSION":q.diffuse()
        probabilities=q.probabilities()
        weights=[probabilities[i] for i in unseen]
        norm_error=abs(q.norm()-1.)
        if sum(weights)<=1e-14:raise ArithmeticError("zero unseen mass")
        result=weighted(unseen,weights,rng)
        return result,norm_error
    return weighted(unseen,weights,rng),0.

def weighted(items,weights,rng):
    draw=rng.random()*sum(weights)
    for item,w in zip(items,weights):
        draw-=w
        if draw<=0:return item
    return items[-1]

def evaluate(n=16,trials=200,seed=10000,pilot=4,rounds=ROUNDS,bootstrap=500):
    rounds=tuple(rounds)
    if not 8<=n<=4096 or not 1<=pilot<n or trials<2 or bootstrap<100 or not rounds or any(r<0 or r>20 for r in rounds):
        raise ValueError("evaluate settings")
    rows=[];comparisons=[]
    configurations=[(m,r) for m in METHODS for r in (rounds if m.startswith("QI_") else (0,))]
    for kind in KINDS:
        observations={key:[] for key in configurations}
        for t in range(trials):
            values=workload(n,seed+t,kind)
            initial=random.Random(seed+100000+t).sample(range(n),pilot)
            seen={i:values[i] for i in initial}
            baseline_best=max(seen.values());optimal=max(values)
            for method,r in configurations:
                start=time.perf_counter_ns()
                chosen,error=choose(n,seen,method,seed+200000+t,r)
                runtime_ms=(time.perf_counter_ns()-start)/1e6
                best=max(baseline_best,values[chosen])
                observations[(method,r)].append({
                    "pilot_optimum_hit":int(baseline_best==optimal),
                    "new_optimum_hit":int(values[chosen]==optimal and baseline_best<optimal),
                    "final_success":int(best==optimal),
                    "final_regret":optimal-best,
                    "selected":chosen,"norm_error":error,"runtime_ms":runtime_ms,
                    "oracle_calls":pilot+1})
        for (method,r),rr in observations.items():
            rows.append({"landscape":kind,"method":method,"rounds":r,"trials":trials,"pilot_calls":pilot,
                         "total_calls":pilot+1,"pilot_optimum_rate":statistics.fmean(x["pilot_optimum_hit"] for x in rr),
                         "new_optimum_rate":statistics.fmean(x["new_optimum_hit"] for x in rr),
                         "final_success":statistics.fmean(x["final_success"] for x in rr),
                         "mean_final_regret":statistics.fmean(x["final_regret"] for x in rr),
                         "median_selection_ms":statistics.median(x["runtime_ms"] for x in rr),
                         "max_norm_error":max(x["norm_error"] for x in rr),
                         "equal_oracle_calls":all(x["oracle_calls"]==pilot+1 for x in rr)})
        for r in rounds:
            q=observations[("QI_PHASE_DIFFUSION",r)]
            for baseline in (("QI_PHASE_ONLY",r),("RANDOM",0),("KERNEL_UCB",0),("KERNEL_SOFTMAX",0)):
                other=observations[baseline]
                sd=[x["final_success"]-y["final_success"] for x,y in zip(q,other)]
                rd=[x["final_regret"]-y["final_regret"] for x,y in zip(q,other)]
                comparisons.append({"landscape":kind,"rounds":r,
                    "comparison":"QI_PHASE_DIFFUSION-minus-"+baseline[0],
                    "success_delta":statistics.fmean(sd),
                    "success_ci95":ci(sd,bootstrap,seed+r),
                    "regret_delta":statistics.fmean(rd),
                    "regret_ci95":ci(rd,bootstrap,seed+r+11)})
    return {"version":"0.7.22","kind":"MATCHED_QUANTUM_CLASSICAL_ONE_STEP",
            "parameters":{"candidates":n,"trials":trials,"seed":seed,"pilot":pilot,
                          "total_candidate_oracle_calls":pilot+1,"rounds":list(rounds),"bootstrap":bootstrap},
            "results":rows,"comparisons":comparisons,
            "limitations":["Ideal noiseless quantum state-vector simulation runs on classical CPU",
                "One next-candidate choice after identical pilot; NOT full multi-step search",
                "All algorithms get exactly the same observed utilities and evaluation budget",
                "No hidden optimum passed to any algorithm",
                "CPU duration is for next-candidate selection only; no matched CPU-time cap",
                "Synthetic ring kernel; not real Semantic Memory",
                "Probability improvement is not proof of quantum computational advantage",
                "Comparisons and round choices are exploratory; multiple testing not corrected"]}
def ci(values,reps,seed):
    rng=random.Random(seed);n=len(values);draws=[]
    for _ in range(reps):
        draws.append(sum(values[rng.randrange(n)] for _ in range(n))/n)
    draws.sort()
    return [draws[int((reps-1)*.025)],draws[int((reps-1)*.975)]]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",type=int,default=16)
    p.add_argument("--trials",type=int,default=200)
    p.add_argument("--seed",type=int,default=10000)
    p.add_argument("--pilot",type=int,default=4)
    p.add_argument("--rounds",default="0,1,2,3")
    p.add_argument("--bootstrap",type=int,default=500)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    report=evaluate(a.candidates,a.trials,a.seed,a.pilot,
                    [int(x) for x in a.rounds.split(",")],a.bootstrap)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("x",encoding="utf-8") as f:json.dump(report,f,ensure_ascii=False,indent=2)
    print("Wrote:",out)
    for x in report["results"]:
        print(x["landscape"],x["method"],"r=",x["rounds"],
              "new_hit=",round(x["new_optimum_rate"],4),"final_success=",round(x["final_success"],4))
if __name__=="__main__":main()
