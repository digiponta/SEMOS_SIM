"""v0.5.9: nested topic-group CV for a safety-constrained open-set gate.

The 400-example candidate holdout is never read. Outer held-out topics are not
used to calibrate guard thresholds. Results remain exploratory because this
development dataset has already informed model and architecture choices.
"""
from __future__ import annotations
import argparse,json,math,random
from pathlib import Path
from compare_gate_variants_v056 import enrich,eval_predictions,predict_variant
from evaluate_separated_gate_v057 import fit,feature,dist,VMS
from evaluate_paired_grouped_v058 import load_groups,wilson
from evaluate_frozen_holdout_v054 import sha,validate_freeze
from benchmark_v040 import load_csv

def contrast(row,centers):
    vm=row["best_vm"];f=feature(row)
    return dist(f,centers[f"{vm}:unknown"])-dist(f,centers[f"{vm}:known"])

def choose_guard(rows,groups,folds=3,budget=.05,seed=12):
    """Inner OOF contrast score calibration; threshold determined from INNER data."""
    unique=sorted(set(groups));random.Random(seed).shuffle(unique)
    if len(unique)<folds or folds<2:raise ValueError("Insufficient inner groups")
    assignments={g:i%folds for i,g in enumerate(unique)}
    margins=[None]*len(rows)
    for k in range(folds):
        held=[i for i,g in enumerate(groups) if assignments[g]==k]
        train=[r for i,r in enumerate(rows) if assignments[groups[i]]!=k]
        if not train or not held:raise ValueError("Empty inner fold")
        center=fit(train)
        for i in held:margins[i]=contrast(rows[i],center)
    # Conservative finite-sample empirical upper confidence constraint.
    # If few UNKNOWN examples, a 5% 95%-Wilson upper limit is generally unattainable.
    unknown=[m for m,r in zip(margins,rows) if r["label"]=="UNKNOWN"]
    if not unknown:raise ValueError("No unknown samples for guard selection")
    candidates=[float("inf")]+sorted(set(margins),reverse=True)+[float("-inf")]
    viable=[]
    for cutoff in candidates:
        fp=sum(m>=cutoff for m in unknown)
        rate=fp/len(unknown)
        upper=wilson(fp,len(unknown))[1]
        if rate<=budget:
            known_correct=sum(r["best_vm"]==r["label"] and m>=cutoff for r,m in zip(rows,margins) if r["label"]!="UNKNOWN")
            viable.append((known_correct,-rate,cutoff,upper))
    # Optimize known accuracy subject to empirical budget; Wilson limit is diagnostic,
    # not used as constraint because only 25 UNKNOWN samples in the whole dev set.
    winner=max(viable,key=lambda x:(x[0],x[1],-x[2]))
    return {"cutoff":winner[2],"inner_known_correct":winner[0],
            "inner_unknown_false_accept":-winner[1],
            "inner_unknown_wilson95_upper":winner[3],
            "upper_bound_under_budget":winner[3]<=budget,
            "inner_unknown_n":len(unknown)}

def nested_evaluate(rows,groups,outer_folds=5,inner_folds=3,budget=.05,seed=59):
    if len(groups)!=len(rows):raise ValueError("Missing groups")
    unique=sorted(set(groups))
    if len(unique)<outer_folds or outer_folds<2:raise ValueError("Too few outer groups")
    random.Random(seed).shuffle(unique)
    assignment={g:i%outer_folds for i,g in enumerate(unique)}
    predictions=[None]*len(rows);metadata=[]
    for k in range(outer_folds):
        tr=[i for i,g in enumerate(groups) if assignment[g]!=k]
        te=[i for i,g in enumerate(groups) if assignment[g]==k]
        inner_rows=[rows[i] for i in tr];inner_groups=[groups[i] for i in tr]
        guard=choose_guard(inner_rows,inner_groups,inner_folds,budget,seed+k)
        center=fit(inner_rows)
        for i in te:
            predictions[i]=rows[i]["best_vm"] if contrast(rows[i],center)>=guard["cutoff"] else "UNKNOWN"
        metadata.append({"fold":k,"train_n":len(tr),"test_n":len(te),"guard":guard})
    if any(x is None for x in predictions):raise AssertionError("Incomplete outer predictions")
    metrics=eval_predictions(rows,predictions)
    n=sum(r["label"]=="UNKNOWN" for r in rows)
    fp=sum(p!="UNKNOWN" and r["label"]=="UNKNOWN" for r,p in zip(rows,predictions))
    metrics["unknown_false_accept_count"]=fp
    metrics["unknown_false_accept_wilson95"]=wilson(fp,n)
    return metrics,predictions,metadata

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--development",default="data/validation_v043_dev100.csv")
    ap.add_argument("--groups",default="data/development_topic_groups.csv")
    ap.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
    ap.add_argument("--output",default="results/nested_topic_gate_v059.json")
    ap.add_argument("--outer-folds",type=int,default=5)
    ap.add_argument("--inner-folds",type=int,default=3)
    ap.add_argument("--budget",type=float,default=.05)
    a=ap.parse_args()
    if "holdout" in Path(a.development).name.lower():ap.error("Holdout not permitted")
    if not 0<=a.budget<=1:ap.error("budget must be between 0 and 1")
    config=json.loads(Path(a.frozen).read_text(encoding="utf-8-sig"))
    validate_freeze(config,sha(config["calibration_source"]))
    from llm_sem_adapter import LLMSemAdapter
    base=load_csv(a.development)
    groups,mode=load_groups(base,a.groups)
    if mode!="CURATED_TOPIC_GROUPS_UNVERIFIED":ap.error("Explicit topic groups required")
    rows=enrich(base,LLMSemAdapter(model_path=config["model"]),config["weight"])
    result,preds,foldmeta=nested_evaluate(rows,groups,a.outer_folds,a.inner_folds,a.budget)
    reference=eval_predictions(rows,predict_variant(rows,config["threshold"],config["margin"]))
    report={"version":"0.5.9","kind":"EXPLORATORY_NESTED_TOPIC_GROUP_CV",
            "development_sha256":sha(a.development),"groups_sha256":sha(a.groups),
            "frozen_sha256":sha(a.frozen),"budget":a.budget,
            "candidate_nested_oof":result,"reference_in_sample_development":reference,
            "outer_folds":foldmeta,
            "diagnostics":[{"text":r["text"],"gold":r["label"],"predicted":p,
                            "topic_group":groups[i]} for i,(r,p) in enumerate(zip(rows,preds))],
            "limitations":["Empirical <=5% false accept budget on inner OOF is not a statistical guarantee",
                           "Wilson upper bound is descriptive and often greater than 5% for small unknown N",
                           "Development examples have already informed prior model/threshold selection",
                           "Reference is in-sample and cannot be interpreted as a fair head-to-head",
                           "Topic grouping is curated, not verified independent",
                           "Outer held-out topics do not participate in threshold calibration",
                           "400-example candidate holdout is not accessed"]}
    out=Path(a.output)
    if out.exists():ap.error("Output exists; refusing overwrite")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding="utf-8")
    print("NESTED:",result)
    print("Saved:",out)
if __name__=="__main__":main()
