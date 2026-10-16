"""SEMOS_SIM v0.5.11: reproducible per-request nested-gate trace.

Replays v0.5.9 with identical seeds and folds. All score traces are outer
out-of-fold; calibration never sees the corresponding held-out topic.
Does not retune or evaluate any holdout dataset.
"""
import argparse,json,random,math
from pathlib import Path
from benchmark_v040 import load_csv
from compare_gate_variants_v056 import enrich
from evaluate_frozen_holdout_v054 import sha,validate_freeze
from evaluate_paired_grouped_v058 import load_groups
from evaluate_separated_gate_v057 import fit,feature,dist
from evaluate_nested_topic_gate_v059 import choose_guard,contrast

def trace_nested(rows,groups,folds=5,inner=3,budget=.05,seed=59):
    if len(rows)!=len(groups):raise ValueError("Rows/groups mismatch")
    unique=sorted(set(groups))
    if len(unique)<folds:raise ValueError("Insufficient topics")
    random.Random(seed).shuffle(unique)
    assignment={g:i%folds for i,g in enumerate(unique)}
    result=[None]*len(rows);settings=[]
    for k in range(folds):
        training=[i for i,g in enumerate(groups) if assignment[g]!=k]
        testing=[i for i,g in enumerate(groups) if assignment[g]==k]
        train_rows=[rows[i] for i in training]
        guard=choose_guard(train_rows,[groups[i] for i in training],inner,budget,seed+k)
        centroid=fit(train_rows)
        cutoff=guard["cutoff"]
        for i in testing:
            row=rows[i];vm=row["best_vm"];fv=feature(row)
            known_distance=dist(fv,centroid[vm+":known"])
            unknown_distance=dist(fv,centroid[vm+":unknown"])
            score=unknown_distance-known_distance
            passed=score>=cutoff
            result[i]={"text":row["text"],"gold":row["label"],
                       "topic_group":groups[i],"outer_fold":k,
                       "candidate_vm":vm,"fused_similarity":row["score"],
                       "runner_up_margin":row["margin"],
                       "centroid_multi_agree":row["centroid_top"]==row["multi_top"],
                       "distance_to_known":known_distance,
                       "distance_to_unknown":unknown_distance,
                       "contrast_score":score,"guard_cutoff":cutoff,
                       "guard_margin":score-cutoff if math.isfinite(cutoff) else None,
                       "predicted":vm if passed else "UNKNOWN",
                       "reason":"ACCEPT" if passed else "REJECT_CONTRAST",
                       "candidate_correct":vm==row["label"]}
        settings.append({"fold":k,"guard":guard,"train_n":len(training),"test_n":len(testing)})
    return result,settings

def validate_replay(trace,prior):
    original=prior["diagnostics"]
    if len(original)!=len(trace):raise ValueError("Row count mismatch")
    wrong=[i for i,(a,b) in enumerate(zip(trace,original))
           if any((a[k]!=b[{"gold":"gold","text":"text","predicted":"predicted","topic_group":"topic_group"}[k]])
                  for k in ("gold","text","predicted","topic_group"))]
    if wrong:raise ValueError("Replay differs from v0.5.9 at indices "+str(wrong[:10]))
    return True

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--development",default="data/validation_v043_dev100.csv")
    p.add_argument("--groups",default="data/development_topic_groups.csv")
    p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
    p.add_argument("--reference",default="results/nested_topic_gate_v059.json")
    p.add_argument("--output",default="results/nested_traces_v0511.json")
    args=p.parse_args()
    for path in (args.development,args.groups,args.reference):
        if "holdout" in Path(path).name.lower():p.error("Holdout forbidden")
    prior=json.loads(Path(args.reference).read_text(encoding="utf-8-sig"))
    config=json.loads(Path(args.frozen).read_text(encoding="utf-8-sig"))
    validate_freeze(config,sha(config["calibration_source"]))
    if prior["development_sha256"]!=sha(args.development) or prior["groups_sha256"]!=sha(args.groups):
        p.error("Input dataset/group hash mismatch with v0.5.9 report")
    from llm_sem_adapter import LLMSemAdapter
    raw=load_csv(args.development)
    groups,mode=load_groups(raw,args.groups)
    if mode!="CURATED_TOPIC_GROUPS_UNVERIFIED":p.error("Topic groups required")
    enriched=enrich(raw,LLMSemAdapter(model_path=config["model"]),config["weight"])
    rows,folds=trace_nested(enriched,groups,budget=prior["budget"])
    validate_replay(rows,prior)
    summary={"version":"0.5.11","kind":"REPLAY_ONLY_OOF_GUARD_TRACE",
             "reference_replay_exact_match":True,"source_sha256":sha(args.reference),
             "frozen_sha256":sha(args.frozen),"rows":rows,"fold_settings":folds,
             "limitations":["Retrospective trace of reused 100-case development benchmark",
                            "No parameter update or new performance claim",
                            "Fused score and contrast score have different scales",
                            "No 2 Copies in 3 synchronization or VM availability test"]}
    dest=Path(args.output)
    if dest.exists():p.error("Output exists")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print("REPLAY CHECK: PASS",len(rows),"rows")
    print("Known rejected:",sum(r["gold"]!="UNKNOWN" and r["predicted"]=="UNKNOWN" for r in rows))
    print("Unknown accepted:",sum(r["gold"]=="UNKNOWN" and r["predicted"]!="UNKNOWN" for r in rows))
    print("Saved:",dest)
if __name__=="__main__":main()
