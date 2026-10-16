"""SEMOS_SIM v0.5.1: paired uncertainty analysis for v0.5.0 outputs.

Analyzes frozen predictions in an existing benchmark JSON; no model inference.
Bootstrap intervals quantify sampling variability only, not selection/leakage bias.
"""
from __future__ import annotations
import argparse,json,math,random
from pathlib import Path

def quantile(values,p):
    if not values:raise ValueError("empty samples")
    ordered=sorted(values)
    position=(len(ordered)-1)*p
    lo=math.floor(position);hi=math.ceil(position)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(position-lo)

def exact_mcnemar_p(discordant_a,discordant_b):
    """Two-sided exact binomial test for paired discordant correct/incorrect outcomes."""
    n=discordant_a+discordant_b
    if not n:return 1.0
    k=min(discordant_a,discordant_b)
    return min(1.0,2.0*sum(math.comb(n,i) for i in range(k+1))/2**n)

def interval(samples,confidence=.95):
    alpha=(1-confidence)/2
    return [quantile(samples,alpha),quantile(samples,1-alpha)]

def compare(report,reference="tfidf",candidate="semantic_hybrid",
            iterations=5000,seed=5101):
    if iterations<100:raise ValueError("iterations must be at least 100")
    results=report.get("results",{})
    if reference not in results or candidate not in results:
        raise ValueError("Both methods must be present in results")
    baseline=results[reference]["details"]; proposed=results[candidate]["details"]
    if len(baseline)!=len(proposed) or not baseline:
        raise ValueError("Unpaired or empty requests")
    for i,(a,b) in enumerate(zip(baseline,proposed)):
        if a["text"]!=b["text"] or a["gold"]!=b["gold"]:
            raise ValueError(f"Unpaired request at index {i}")
    known=[(a,b) for a,b in zip(baseline,proposed) if a["gold"]!="UNKNOWN"]
    unknown=[(a,b) for a,b in zip(baseline,proposed) if a["gold"]=="UNKNOWN"]
    if not known or not unknown:raise ValueError("Both known and UNKNOWN classes required")
    correct=lambda r:int(r["selected"]==r["gold"])
    reject=lambda r:int(r["selected"]=="UNKNOWN")
    def paired_stats(pairs,fn):
        n=len(pairs)
        a=sum(fn(x) for x,_ in pairs)/n
        b=sum(fn(y) for _,y in pairs)/n
        rng=random.Random(seed)
        sampled=[]
        for _ in range(iterations):
            draw=[pairs[rng.randrange(n)] for _ in range(n)]
            sampled.append(sum(fn(y)-fn(x) for x,y in draw)/n)
        pos=sum(fn(y)==1 and fn(x)==0 for x,y in pairs)
        neg=sum(fn(y)==0 and fn(x)==1 for x,y in pairs)
        return {"reference_rate":a,"candidate_rate":b,"difference_candidate_minus_reference":b-a,
                "difference_95pct_bootstrap_ci":interval(sampled),
                "discordant_candidate_only_correct":pos,
                "discordant_reference_only_correct":neg,
                "mcnemar_exact_two_sided_p":exact_mcnemar_p(pos,neg),
                "sample_size":n}
    return {
        "version":"0.5.1",
        "analysis_kind":"DEVELOPMENT_PAIRED_BOOTSTRAP_NOT_INDEPENDENT_HOLDOUT",
        "source_kind":report.get("kind"),
        "reference":reference,"candidate":candidate,
        "bootstrap_iterations":iterations,"seed":seed,
        "known_correct_routing":paired_stats(known,correct),
        "unknown_rejection":paired_stats(unknown,reject),
        "caveats":[
            "Predictions are from previously used development validation samples, NOT independent testing",
            "95% percentile bootstrap intervals reflect request resampling only; do not adjust for model/threshold selection or domain shift",
            "McNemar p-values are exploratory, not confirmatory after repeated development comparisons",
            "The source does not contain repeated timed trials; no valid latency confidence intervals can be estimated",
            "Correct VM dispatch is a task-completion proxy; no actual task execution or OS advantage established"
        ]
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/os_advantage_v050.json")
    p.add_argument("--reference",default="tfidf")
    p.add_argument("--candidate",default="semantic_hybrid")
    p.add_argument("--iterations",type=int,default=5000)
    p.add_argument("--seed",type=int,default=5101)
    p.add_argument("--output",default="results/os_advantage_stats_v051.json")
    args=p.parse_args()
    report=json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    result=compare(report,args.reference,args.candidate,args.iterations,args.seed)
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    for name in ("known_correct_routing","unknown_rejection"):
        stat=result[name]
        print(f"{name}: baseline={stat['reference_rate']:.3f}, "
              f"candidate={stat['candidate_rate']:.3f}, "
              f"delta={stat['difference_candidate_minus_reference']:+.3f}, "
              f"bootstrap_95%={stat['difference_95pct_bootstrap_ci']}, "
              f"McNemar_exact_p={stat['mcnemar_exact_two_sided_p']:.4g}")
    print(f"Saved: {dest}")

if __name__=="__main__":main()
