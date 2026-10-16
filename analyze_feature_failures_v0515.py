"""v0.5.15: descriptive feature separation of router and gate failure modes.
No tuning, thresholds, training, or holdout access.
"""
import argparse,json,statistics
from pathlib import Path
from collections import defaultdict

FEATURES=("fused_similarity","runner_up_margin","contrast_score","guard_margin","distance_to_known","distance_to_unknown")
def bucket(row):
    if row["gold"]=="UNKNOWN":
        return "unknown_false_accepted" if row["predicted"]!="UNKNOWN" else "unknown_correct_rejected"
    if row["candidate_vm"]!=row["gold"]:
        return "candidate_wrong_accepted" if row["predicted"]!="UNKNOWN" else "candidate_wrong_rejected"
    return "candidate_right_accepted" if row["predicted"]!="UNKNOWN" else "candidate_right_rejected"
def stats(rows):
    out={}
    for f in FEATURES:
        values=sorted(float(r[f]) for r in rows if r.get(f) is not None)
        if not values:out[f]=None;continue
        n=len(values)
        out[f]={"n":n,"mean":statistics.mean(values),"median":statistics.median(values),
                "min":values[0],"max":values[-1],
                "q25":values[(n-1)//4],"q75":values[(3*(n-1))//4]}
    return out
def analyze(doc):
    if doc.get("version")!="0.5.11" or not doc.get("reference_replay_exact_match"):
        raise ValueError("Verified v0.5.11 trace required")
    rows=doc["rows"]
    groups=defaultdict(list);vm=defaultdict(list)
    for r in rows:
        expected=r["candidate_vm"] if r["contrast_score"]>=r["guard_cutoff"] else "UNKNOWN"
        if expected!=r["predicted"]:raise ValueError("Replay mismatch")
        groups[bucket(r)].append(r)
        vm[r["gold"]].append(r)
    return {"version":"0.5.15","kind":"DESCRIPTIVE_FEATURE_FAILURE_ANALYSIS",
     "n":len(rows),
     "failure_modes":{name:{"count":len(g),"features":stats(g),
        "examples":[r["text"] for r in g]} for name,g in sorted(groups.items())},
     "by_gold_domain":{name:{"count":len(g),"features":stats(g),
        "failure_counts":dict(sorted(__import__("collections").Counter(bucket(r) for r in g).items()))}
         for name,g in sorted(vm.items())},
     "notes":["Descriptive distributions only: these are not generalization metrics",
              "Features are correlated; these summaries do not identify causal mechanisms",
              "Previously used development data; no threshold selection or independent holdout",
              "No QHA 2 Copies in 3 reliability or synchronization evaluation"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/nested_traces_v0511.json")
    p.add_argument("--output",default="results/feature_failure_analysis_v0515.json")
    a=p.parse_args()
    if "holdout" in Path(a.input).name.lower():p.error("Holdout forbidden")
    result=analyze(json.loads(Path(a.input).read_text(encoding="utf-8-sig")))
    dest=Path(a.output)
    if dest.exists():p.error("Refusing overwrite")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    for k,v in result["failure_modes"].items():
        print(k, v["count"],"score",v["features"]["fused_similarity"]["mean"])
    print("Saved:",dest)
if __name__=="__main__":main()
