"""SEMOS_SIM v0.5.14 — diagnostic selective-rescue sensitivity sweep.

Uses an already-exposed v0.5.11 out-of-fold trace. No threshold is trained,
promoted, or recommended for deployment. Ground truth is used for scoring
AFTER candidate decisions, not to form the decisions.
"""
import argparse,json,math
from pathlib import Path

# Predeclared probes; NOT selected from held-out outcomes.
PROBES={
 "none":lambda r:False,
 "consensus_strict":lambda r:r["centroid_multi_agree"] and r["fused_similarity"]>=.80 and r["runner_up_margin"]>=.10,
 "consensus_moderate":lambda r:r["centroid_multi_agree"] and r["fused_similarity"]>=.75 and r["runner_up_margin"]>=.08,
 "margin_strict":lambda r:r["runner_up_margin"]>=.15 and r["fused_similarity"]>=.80,
 "contrast_near_miss":lambda r:r["guard_margin"] is not None and r["guard_margin"]>=-.15 and r["centroid_multi_agree"],
 "consensus_near_miss":lambda r:r["guard_margin"] is not None and r["guard_margin"]>=-.50 and r["centroid_multi_agree"] and r["fused_similarity"]>=.75
}
def evaluate(rows,rule):
    if not rows:raise ValueError("empty rows")
    seen=set();records=[]
    for row in rows:
        for key in ("text","gold","candidate_vm","predicted","contrast_score","guard_cutoff","fused_similarity","runner_up_margin","centroid_multi_agree","guard_margin"):
            if key not in row:raise ValueError("Missing "+key)
        if row["text"] in seen:raise ValueError("Duplicate request text")
        seen.add(row["text"])
        expected=row["candidate_vm"] if row["contrast_score"]>=row["guard_cutoff"] else "UNKNOWN"
        if expected!=row["predicted"]:raise ValueError("Gate replay inconsistent")
        rescued=row["predicted"]=="UNKNOWN" and bool(rule(row))
        prediction=row["candidate_vm"] if rescued else row["predicted"]
        records.append((row,prediction,rescued))
    known=[(r,p,rec) for r,p,rec in records if r["gold"]!="UNKNOWN"]
    unknown=[(r,p,rec) for r,p,rec in records if r["gold"]=="UNKNOWN"]
    if not known or not unknown:raise ValueError("Both known and unknown examples are required")
    ncorrect=sum(r["gold"]==p for r,p,_ in known)
    naccept=sum(p!="UNKNOWN" for r,p,_ in known)
    nfalse=sum(p!="UNKNOWN" for r,p,_ in unknown)
    return {
      "known_accuracy":ncorrect/len(known),
      "known_coverage":naccept/len(known),
      "selective_accuracy":ncorrect/naccept if naccept else None,
      "unknown_reject":1-nfalse/len(unknown),
      "unknown_false_accept":nfalse/len(unknown),
      "known_correct_count":ncorrect,"known_accepted_count":naccept,
      "unknown_false_accept_count":nfalse,
      "additional_correct_known":sum(rec and r["gold"]==p for r,p,rec in known),
      "additional_wrong_known":sum(rec and r["gold"]!=p for r,p,rec in known),
      "additional_unknown_false_accept":sum(rec for _,_,rec in unknown),
      "rescued_texts":[{"text":r["text"],"gold":r["gold"],"candidate_vm":r["candidate_vm"]} for r,p,rec in records if rec]
    }
def analyze(trace):
    if trace.get("version")!="0.5.11" or not trace.get("reference_replay_exact_match"):
        raise ValueError("Verified v0.5.11 trace required")
    rows=trace["rows"]
    results={name:evaluate(rows,rule) for name,rule in PROBES.items()}
    baseline=results["none"]
    for name,result in results.items():
        result["delta_known_accuracy_pp"]=round(100*(result["known_accuracy"]-baseline["known_accuracy"]),3)
        result["delta_unknown_false_accept_pp"]=round(100*(result["unknown_false_accept"]-baseline["unknown_false_accept"]),3)
        result["delta_known_coverage_pp"]=round(100*(result["known_coverage"]-baseline["known_coverage"]),3)
    return {"version":"0.5.14","kind":"EXPLORATORY_SELECTIVE_RESCUE_SENSITIVITY",
     "input_verified":True,"n":len(rows),"probes":results,
     "guardrails":["Predeclared illustrative heuristic probes; no candidate selected as optimum",
                   "Do not tune these thresholds using this development set",
                   "All metrics are retrospective; performance is not independent evidence",
                   "No production rule, frozen gate change, or 2 Copies in 3 validation"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/nested_traces_v0511.json")
    p.add_argument("--output",default="results/selective_rescue_v0514.json")
    args=p.parse_args()
    if "holdout" in Path(args.input).name.lower():p.error("Holdout prohibited")
    trace=json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    result=analyze(trace);dest=Path(args.output)
    if dest.exists():p.error("Refusing overwrite")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    for name,row in result["probes"].items():
        print(f'{name:22} known={row["known_accuracy"]:.2%} coverage={row["known_coverage"]:.2%} unknown_FA={row["unknown_false_accept"]:.2%} rescued(correct/wrong/unknown)={row["additional_correct_known"]}/{row["additional_wrong_known"]}/{row["additional_unknown_false_accept"]}')
    print("Saved:",dest)
if __name__=="__main__":main()
