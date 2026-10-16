"""v0.5.20 retrospective candidate-score separation and threshold sensitivity.

No tuning, no deployable thresholds: examines already exposed v0.5.19
measurements. Gold is solely for post-hoc reporting.
"""
import argparse,json,statistics
from pathlib import Path

VMS=("VM-A","VM-B","VM-C")
def describe(v):
 if not v:return None
 v=sorted(v);n=len(v)
 return {"n":n,"mean":statistics.mean(v),"median":statistics.median(v),
   "min":v[0],"max":v[-1],"q25":v[(n-1)//4],"q75":v[3*(n-1)//4]}
def roc_auc(positive,negative):
 if not positive or not negative:return None
 return sum((x>y)+0.5*(x==y) for x in positive for y in negative)/(len(positive)*len(negative))
def analyze(doc):
 if doc.get("version")!="0.5.19" or not doc.get("replay_matches_v0518"):
  raise ValueError("Verified v0.5.19 frozen replay required")
 groups=doc["by_gold_domain"];threshold=doc["threshold"];margin=doc["margin_threshold"]
 rows=[s for g in groups.values() for s in g["samples"]]
 if len(rows)!=80:raise ValueError("Expected frozen synthetic 80-case diagnostic")
 unknown=[x for x in rows if x["gold"]=="UNKNOWN"]
 output={}
 for vm in VMS:
  own=[x for x in rows if x["gold"]==vm and x["candidate_vm"]==vm]
  foreign=[x for x in rows if x["gold"]!=vm and x["candidate_vm"]==vm]
  unknown_candidates=[x for x in unknown if x["candidate_vm"]==vm]
  # Diagnose score if the gate's similarity threshold were shifted by
  # predefined illustrative deltas, with its margin requirement unchanged.
  shifts=[]
  for delta in (-.10,-.05,0,.05):
   th=threshold+delta
   passed=lambda x:x["score"]>=th and x["margin"]>=margin
   shifts.append({"hypothetical_delta":delta,"threshold":th,
      "known_right_accepted":sum(map(passed,own)),
      "known_right_total":len(own),
      "unknown_false_accepted":sum(map(passed,unknown_candidates)),
      "unknown_candidate_total":len(unknown_candidates),
      "other_known_wrong_accepted":sum(passed(x) for x in foreign if x["gold"]!="UNKNOWN")})
  output[vm]={"correct_candidate_similarity":describe([x["score"] for x in own]),
              "foreign_candidate_similarity":describe([x["score"] for x in foreign]),
              "unknown_candidate_similarity":describe([x["score"] for x in unknown_candidates]),
              "correct_vs_unknown_candidate_auc":roc_auc([x["score"] for x in own],[x["score"] for x in unknown_candidates]),
              "diagnostic_counterfactual_shifts":shifts}
 return {"version":"0.5.20","kind":"RETROSPECTIVE_VM_SCORE_CALIBRATION_DIAGNOSTIC",
         "dataset_sha256":doc["dataset_sha256"],
         "baseline_similarity_threshold":threshold,"baseline_margin_threshold":margin,
         "vm_diagnostics":output,
         "notes":["Scoring uses only top-1 candidate; cannot estimate class-specific scores for non-top VM",
          "AUC conditioned on candidate selection creates selection bias",
          "Threshold shifts are hypothetical retrospective examples, not proposed settings",
          "Do not choose parameters on previously evaluated data",
          "This does not test 2 Copies in 3 or QHA availability"]}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--input",default="results/gate_failure_attribution_v0519.json")
 p.add_argument("--output",default="results/vm_similarity_diagnostic_v0520.json")
 a=p.parse_args();out=Path(a.output)
 if out.exists():p.error("Refusing overwrite")
 result=analyze(json.loads(Path(a.input).read_text(encoding="utf-8-sig")))
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
 for vm,v in result["vm_diagnostics"].items():
  print(vm,"known mean=",v["correct_candidate_similarity"]["mean"] if v["correct_candidate_similarity"] else None,
         "unknown mean=",v["unknown_candidate_similarity"]["mean"] if v["unknown_candidate_similarity"] else None,
         "AUC=",v["correct_vs_unknown_candidate_auc"])
 print("Saved:",out)
if __name__=="__main__":main()
