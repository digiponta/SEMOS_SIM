"""v0.7.16 — classical semantic-kernel interference matched-budget benchmark."""
import argparse,cmath,json,math,random,statistics
from pathlib import Path
METHODS=("RANDOM","GREEDY","KERNEL_UCB","QI_KERNEL_PHASE","QI_PHASE_ABLATION")
KINDS=("smooth","shuffled","multimodal")
def workload(n,seed,kind):
 if n<8 or kind not in KINDS:raise ValueError("workload")
 r=random.Random(seed)
 if kind=="smooth":
  p=r.randrange(n)
  return [.85*math.exp(-min(abs(i-p),n-abs(i-p))**2/25)+.15*r.random() for i in range(n)]
 if kind=="multimodal":
  peaks=r.sample(range(n),3)
  return [max(.8*math.exp(-min(abs(i-p),n-abs(i-p))**2/6) for p in peaks)+.2*r.random() for i in range(n)]
 return [r.random() for _ in range(n)]
def similarity(a,b,n,width=3):
 d=min(abs(a-b),n-abs(a-b))
 return math.exp(-d*d/(2*width*width))
def probability_after_update(n,seen,strength=1.,mode="QI_KERNEL_PHASE"):
 if strength<0:raise ValueError("strength")
 unseen=[i for i in range(n) if i not in seen]
 if not unseen:return []
 if mode=="QI_PHASE_ABLATION" or not seen:return [1/len(unseen)]*len(unseen)
 weights=[]
 for i in unseen:
  amp=1+strength*sum(similarity(i,j,n)*cmath.exp(1j*math.pi*(1-v)) for j,v in seen.items())
  weights.append(abs(amp)**2)
 total=sum(weights)
 return [x/total for x in weights]
def pick(weights,unseen,rng):
 t=rng.random()*sum(weights[i] for i in unseen)
 for i in unseen:
  t-=weights[i]
  if t<=0:return i
 return unseen[-1]
def search(values,method,budget,seed,strength=1.):
 n=len(values)
 if method not in METHODS or not 1<=budget<=n or strength<0:raise ValueError("search")
 rng=random.Random(seed);seen={};ops=0
 for _ in range(budget):
  unseen=[i for i in range(n) if i not in seen]
  if not seen or method=="RANDOM":i=rng.choice(unseen)
  elif method=="GREEDY":
   best=max(seen,key=lambda j:(seen[j],-j))
   options=[(best+d)%n for d in (-2,-1,1,2) if (best+d)%n not in seen]
   i=options[0] if options else rng.choice(unseen);ops+=4
  elif method=="KERNEL_UCB":
   def score(j):
    weights=[(similarity(j,k,n),v) for k,v in seen.items()]
    w=sum(x for x,_ in weights)
    return sum(x*v for x,v in weights)/w+.2/(1+w)
   i=max(unseen,key=lambda j:(score(j),-j))
   ops+=2*len(unseen)*len(seen)
  else:
   weights=[0.]*n
   if method=="QI_PHASE_ABLATION":
    for j in unseen:weights[j]=1.
    ops+=len(seen)
   else:
    for j,v in zip(unseen,probability_after_update(n,seen,strength)):weights[j]=v
    ops+=3*len(unseen)*len(seen)
   i=pick(weights,unseen,rng)
  seen[i]=values[i]
 return {"success":int(max(seen.values())==max(values)),
         "regret":max(values)-max(seen.values()),"best":max(seen.values()),
         "oracle_calls":len(seen),"operations_proxy":ops}
def benchmark(n=64,budgets=(8,12,24),trials=40,seed=42,strength=1.):
 budgets=tuple(budgets)
 if n<8 or trials<1 or not budgets or any(not 1<=b<=n for b in budgets):raise ValueError("benchmark")
 rows=[]
 for kind in KINDS:
  for budget in budgets:
   for method in METHODS:
    samples=[search(workload(n,seed+t,kind),method,budget,seed+10000+t,strength) for t in range(trials)]
    rows.append({"landscape":kind,"budget":budget,"method":method,"trials":trials,
     "success_at_budget":statistics.fmean(x["success"] for x in samples),
     "mean_regret":statistics.fmean(x["regret"] for x in samples),
     "mean_best":statistics.fmean(x["best"] for x in samples),
     "mean_operations_proxy":statistics.fmean(x["operations_proxy"] for x in samples),
     "equal_oracle_calls":all(x["oracle_calls"]==budget for x in samples)})
 ablation=[]
 for kind in KINDS:
  for budget in budgets:
   lookup={x["method"]:x for x in rows if x["landscape"]==kind and x["budget"]==budget}
   a,b=lookup["QI_KERNEL_PHASE"],lookup["QI_PHASE_ABLATION"]
   ablation.append({"landscape":kind,"budget":budget,
    "qi_minus_ablation_success":a["success_at_budget"]-b["success_at_budget"],
    "qi_minus_ablation_regret":a["mean_regret"]-b["mean_regret"],
    "qi_minus_kernel_ucb_success":a["success_at_budget"]-lookup["KERNEL_UCB"]["success_at_budget"]})
 return {"version":"0.7.16","kind":"SYNTHETIC_SEMANTIC_KERNEL_INTERFERENCE",
  "parameters":{"candidates":n,"budgets":list(budgets),"trials":trials,"seed":seed,"strength":strength},
  "results":rows,"ablations":ablation,
  "limitations":["Similarity is ring distance, not real semantic embedding",
   "All methods classical; quantum-inspired is complex amplitude heuristic",
   "Same oracle-call budgets, not equal CPU operations","No holdout or confidence intervals",
   "Kernel-UCB uses same similarity information as QI"]}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--candidates",type=int,default=64)
 p.add_argument("--budgets",default="8,12,24")
 p.add_argument("--trials",type=int,default=40)
 p.add_argument("--seed",type=int,default=42)
 p.add_argument("--strength",type=float,default=1.)
 p.add_argument("--output",required=True)
 a=p.parse_args()
 r=benchmark(a.candidates,[int(x) for x in a.budgets.split(",")],a.trials,a.seed,a.strength)
 path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("x",encoding="utf-8") as f:json.dump(r,f,indent=2,ensure_ascii=False)
 print("Wrote:",path)
 for x in r["ablations"]:
  print(x["landscape"],"budget",x["budget"],"QI-ablation",round(x["qi_minus_ablation_success"],4),
        "QI-kernel-UCB",round(x["qi_minus_kernel_ucb_success"],4))
if __name__=="__main__":main()
