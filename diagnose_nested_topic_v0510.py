"""SEMOS_SIM v0.5.10: post-evaluation audit of v0.5.9 nested CV.

No fitting, predictions, or thresholds change. Input is only the v0.5.9 JSON.
"""
import argparse,collections,json,math,statistics
from pathlib import Path

LABELS=("VM-A","VM-B","VM-C","UNKNOWN")

def ratio(n,d):
    return n/d if d else None

def bucket(items):
    cm={gold:{pred:0 for pred in LABELS} for gold in LABELS}
    for row in items:
        cm[row["gold"]][row["predicted"]]+=1
    by_class={}
    for gold in LABELS:
        matched=[x for x in items if x["gold"]==gold]
        correct=sum(x["predicted"]==gold for x in matched)
        rejected=sum(x["predicted"]=="UNKNOWN" for x in matched)
        by_class[gold]={"n":len(matched),"correct":correct,"accuracy_or_reject_rate":ratio(correct,len(matched)),
                        "held":rejected if gold!="UNKNOWN" else None,
                        "misrouted_to_vm":sum(x["predicted"] not in (gold,"UNKNOWN") for x in matched)}
    return {"n":len(items),"by_class":by_class,"confusion":cm}

def analyze(report):
    if report.get("version")!="0.5.9" or report.get("kind")!="EXPLORATORY_NESTED_TOPIC_GROUP_CV":
        raise ValueError("Requires a v0.5.9 nested-topic report")
    details=report["diagnostics"]
    if len(details)!=100:raise ValueError("Unexpected development row count")
    for d in details:
        if d["gold"] not in LABELS or d["predicted"] not in LABELS or not d.get("topic_group"):
            raise ValueError("Invalid diagnostic row")
    summary=bucket(details)
    topic={}
    for group in sorted({x["topic_group"] for x in details}):
        sample=[x for x in details if x["topic_group"]==group]
        topic[group]=bucket(sample)
    cutoffs=[float(f["guard"]["cutoff"]) for f in report["outer_folds"]]
    folds=[{"fold":f["fold"],"train_n":f["train_n"],"test_n":f["test_n"],
            "cutoff":float(f["guard"]["cutoff"]),
            "inner_unknown_n":f["guard"]["inner_unknown_n"],
            "inner_unknown_false_accept":f["guard"]["inner_unknown_false_accept"],
            "inner_unknown_wilson95_upper":f["guard"]["inner_unknown_wilson95_upper"],
            "upper_bound_under_budget":f["guard"]["upper_bound_under_budget"]}
           for f in report["outer_folds"]]
    unknown_false=[{"text":x["text"],"predicted":x["predicted"],"topic_group":x["topic_group"]}
                   for x in details if x["gold"]=="UNKNOWN" and x["predicted"]!="UNKNOWN"]
    known_held=[{"text":x["text"],"gold":x["gold"],"topic_group":x["topic_group"]}
                for x in details if x["gold"]!="UNKNOWN" and x["predicted"]=="UNKNOWN"]
    observed=sum(x["predicted"]==x["gold"] for x in details if x["gold"]!="UNKNOWN")
    if observed!=report["candidate_nested_oof"]["known_accuracy"]*75 and abs(observed-report["candidate_nested_oof"]["known_accuracy"]*75)>1e-7:
        raise ValueError("Metric mismatch with source report")
    if len(unknown_false)!=report["candidate_nested_oof"]["unknown_false_accept_count"]:
        raise ValueError("Unknown-count mismatch")
    return {"version":"0.5.10","kind":"POST_NESTED_CV_DIAGNOSTICS_NO_RETUNING",
            "source_version":report["version"],"development_sha256":report["development_sha256"],
            "groups_sha256":report["groups_sha256"],"global":summary,"topic_groups":topic,
            "fold_diagnostics":folds,
            "cutoff_summary":{"minimum":min(cutoffs),"maximum":max(cutoffs),
                              "mean":statistics.mean(cutoffs),"stdev":statistics.stdev(cutoffs)},
            "unknown_false_accept_cases":unknown_false,
            "known_rejected_cases":known_held,
            "limitations":["Only post-hoc diagnostics of previously evaluated development data",
                           "Threshold standard deviation is descriptive across 5 training folds, not independent estimates",
                           "Original report lacks raw per-row contrast features; no score overlap or calibration curve can be inferred",
                           "Topic assignments are curated, not independent certification",
                           "No model update, calibration, or previously evaluated 400-case reuse"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/nested_topic_gate_v059.json")
    p.add_argument("--output",default="results/nested_diagnosis_v0510.json")
    a=p.parse_args()
    if "holdout" in a.input.lower():p.error("Holdout inputs forbidden")
    data=json.loads(Path(a.input).read_text(encoding="utf-8-sig"))
    result=analyze(data)
    out=Path(a.output)
    if out.exists():p.error("Output exists, refusing overwrite")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("By class:")
    for label,stats in result["global"]["by_class"].items():print(" ",label,stats)
    print("Cutoff:",result["cutoff_summary"])
    print("Unknown false accepts:",len(result["unknown_false_accept_cases"]))
    print("Known held:",len(result["known_rejected_cases"]))
    print("Saved:",out)
if __name__=="__main__":main()
