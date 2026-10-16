"""v0.5.16: exploratory threshold-independent discrimination diagnostics.

Computes pairwise ROC AUC on precomputed OOF trace features, no refitting
and no independent holdout claims. AUC targets are provisional engineering goals.
"""
import argparse,json,math
from pathlib import Path

FEATURES={"fused_similarity":"higher","runner_up_margin":"higher",
          "contrast_score":"higher","guard_margin":"higher",
          "distance_to_known":"lower","distance_to_unknown":"higher"}
TARGET_AUC=0.90

def auc(values,labels):
    if len(values)!=len(labels):raise ValueError("length mismatch")
    pos=[v for v,y in zip(values,labels) if y]
    neg=[v for v,y in zip(values,labels) if not y]
    if not pos or not neg:return None
    wins=sum((p>n)+0.5*(p==n) for p in pos for n in neg)
    return wins/(len(pos)*len(neg))

def evaluate(rows,positive,negative):
    a=[r for r in rows if positive(r)]
    b=[r for r in rows if negative(r)]
    result={"positive_n":len(a),"negative_n":len(b),"features":{}}
    for f,direction in FEATURES.items():
        if any(r.get(f) is None for r in a+b):
            result["features"][f]={"auc":None,"target":TARGET_AUC,"status":"MISSING_FEATURE"}
            continue
        sign=1 if direction=="higher" else -1
        score=[sign*float(r[f]) for r in a+b]
        val=auc(score,[True]*len(a)+[False]*len(b))
        result["features"][f]={"auc":val,"target":TARGET_AUC,
          "gap_pp":100*(val-TARGET_AUC) if val is not None else None,
          "point_target_met":val>=TARGET_AUC if val is not None else None,
          "direction":direction}
    return result

def analyze(doc):
    if doc.get("version")!="0.5.11" or not doc.get("reference_replay_exact_match"):
        raise ValueError("Verified v0.5.11 replay trace required")
    rows=doc["rows"]
    for r in rows:
        if r["predicted"]!=(r["candidate_vm"] if r["contrast_score"]>=r["guard_cutoff"] else "UNKNOWN"):
            raise ValueError("Trace replay invariant violated")
    correct=lambda r:r["gold"]!="UNKNOWN" and r["candidate_vm"]==r["gold"]
    wrong=lambda r:r["gold"]!="UNKNOWN" and r["candidate_vm"]!=r["gold"]
    unknown=lambda r:r["gold"]=="UNKNOWN"
    rejected=lambda r:r["predicted"]=="UNKNOWN"
    comparisons={
       "known_candidate_correct_vs_wrong":evaluate(rows,correct,wrong),
       "known_candidate_correct_vs_unknown":evaluate(rows,correct,unknown),
       "known_right_rejected_vs_unknown":evaluate(rows,lambda r:correct(r) and rejected(r),unknown),
       "known_right_accepted_vs_rejected":evaluate(rows,lambda r:correct(r) and not rejected(r),lambda r:correct(r) and rejected(r))}
    return {"version":"0.5.16","kind":"EXPLORATORY_PAIRWISE_ROC_AUC",
      "n":len(rows),"target_kind":"PROVISIONAL_ENGINEERING_GOAL",
      "comparisons":comparisons,
      "limitations":["AUC measures ranking, not a deployed threshold or calibration",
        "One or both classes can be very small; no confidence intervals provided",
        "Post-hoc groups include gate outcomes, so Contrast-based comparisons with accept/reject are partly tautological",
        "Development examples have been reused across earlier studies",
        "The 400-case candidate holdout and QHA 2 Copies in 3 were not tested"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/nested_traces_v0511.json")
    p.add_argument("--output",default="results/feature_auc_v0516.json")
    a=p.parse_args()
    if "holdout" in Path(a.input).name.lower():p.error("Holdout prohibited")
    result=analyze(json.loads(Path(a.input).read_text(encoding="utf-8-sig")))
    dest=Path(a.output)
    if dest.exists():p.error("Refusing overwrite")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    for name,comparison in result["comparisons"].items():
        print(name,"positive=",comparison["positive_n"],"negative=",comparison["negative_n"])
        for feature,data in comparison["features"].items():
            print(" ",feature,"AUC=",data["auc"],"provisional_target=",data["target"])
    print("Saved:",dest)
if __name__=="__main__":main()
