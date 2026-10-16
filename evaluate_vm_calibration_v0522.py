"""v0.5.22: predeclared ECDF VM gate, calibrated on calibration split ONLY."""
import argparse,bisect,csv,json,math
from pathlib import Path
from collections import defaultdict
from compare_gate_variants_v056 import enrich
from evaluate_frozen_holdout_v054 import sha,validate_freeze

VMS=("VM-A","VM-B","VM-C")
def wilson(k,n,z=1.959963984540054):
 if not n:return None
 p=k/n; den=1+z*z/n; center=(p+z*z/(2*n))/den
 half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
 return [max(0,center-half),min(1,center+half)]
def fit(enriched):
 by=defaultdict(list)
 for row in enriched:by[row["best_vm"]].append(row["score"])
 if any(not by[vm] for vm in VMS):raise ValueError("Calibration split has no candidate scores for some VM")
 return {vm:sorted(by[vm]) for vm in VMS}
def calibrated_predict(row,ecdf,quantile=.76,margin=.06):
 # Pure train-side ECDF; no gold-side metadata.
 q=bisect.bisect_right(ecdf[row["best_vm"]],row["score"])/len(ecdf[row["best_vm"]])
 return row["best_vm"] if q>=quantile and row["margin"]>=margin else "UNKNOWN"
def measure(rows,preds):
 known=[(r,p) for r,p in zip(rows,preds) if r["gold"]!="UNKNOWN"]
 unknown=[(r,p) for r,p in zip(rows,preds) if r["gold"]=="UNKNOWN"]
 accepted=[(r,p) for r,p in known if p!="UNKNOWN"]
 definitions={
  "known_accuracy":(sum(r["gold"]==p for r,p in known),len(known)),
  "known_coverage":(len(accepted),len(known)),
  "selective_accuracy":(sum(r["gold"]==p for r,p in accepted),len(accepted)),
  "unknown_reject":(sum(p=="UNKNOWN" for r,p in unknown),len(unknown)),
  "unknown_false_accept":(sum(p!="UNKNOWN" for r,p in unknown),len(unknown))}
 summary={metric:{"successes":k,"n":n,"rate":k/n if n else None,"wilson95":wilson(k,n)}
          for metric,(k,n) in definitions.items()}
 confusion={g:{p:sum(r["gold"]==g and pred==p for r,pred in zip(rows,preds))
               for p in (*VMS,"UNKNOWN")} for g in (*VMS,"UNKNOWN")}
 return {"metrics":summary,"confusion":confusion,
         "predictions":[{"request_id":r["request_id"],"gold":r["gold"],"predicted":p}
                        for r,p in zip(rows,preds)]}
def load(path):
 with Path(path).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--calibration",default="data/new_calibration.csv")
 p.add_argument("--evaluation",default="data/new_evaluation.csv")
 p.add_argument("--audit",default="results/calibration_split_audit_v0521.json")
 p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
 p.add_argument("--output",default="results/vm_calibrated_gate_v0522.json")
 a=p.parse_args();out=Path(a.output)
 if out.exists():p.error("Refusing overwrite")
 audit=json.loads(Path(a.audit).read_text(encoding="utf-8-sig"))
 if audit.get("version")!="0.5.21" or not audit.get("automatic_pass"):p.error("Passed v0.5.21 audit required")
 if sha(a.calibration)!=audit["calibration"]["sha256"] or sha(a.evaluation)!=audit["evaluation"]["sha256"]:
  p.error("Dataset hash mismatch with v0.5.21 audit")
 frozen=json.loads(Path(a.frozen).read_text(encoding="utf-8-sig"))
 validate_freeze(frozen,sha(frozen["calibration_source"]))
 from llm_sem_adapter import LLMSemAdapter
 engine=LLMSemAdapter(model_path=frozen["model"])
 cal=load(a.calibration);ev=load(a.evaluation)
 # The enrichment helper consults only text; gold is passed solely as inert row metadata.
 cal_rep=enrich([{"text":r["text"],"label":r["gold"]} for r in cal],engine,frozen["weight"])
 ev_rep=enrich([{"text":r["text"],"label":r["gold"]} for r in ev],engine,frozen["weight"])
 ecdf=fit(cal_rep)
 vector=[r["best_vm"] for r in ev_rep]
 global_gate=[r["best_vm"] if r["score"]>=frozen["threshold"] and r["margin"]>=frozen["margin"] else "UNKNOWN" for r in ev_rep]
 vm_gate=[calibrated_predict(r,ecdf,.76,frozen["margin"]) for r in ev_rep]
 results={name:measure(ev,preds) for name,preds in [
  ("vector_only",vector),("frozen_global_gate",global_gate),("vm_ecdf_gate",vm_gate)]}
 payload={"version":"0.5.22","kind":"SYNTHETIC_SPLIT_VM_ECDF_GATE_COMPARISON",
  "calibration_sha256":sha(a.calibration),"evaluation_sha256":sha(a.evaluation),
  "audit_sha256":sha(a.audit),"frozen_sha256":sha(a.frozen),
  "ecdf_candidate_counts":{k:len(v) for k,v in ecdf.items()},
  "protocol":{"ecdf_score_quantile":.76,"margin":frozen["margin"],
   "gold_used_in_inference":False,"source":"v0.5.21 preregistered"},
  "results":results,
  "limitations":["Calibration and evaluation are disjoint but both developer-authored synthetic datasets",
  "Only 10 UNKNOWN evaluation examples; Wilson uncertainty is substantial",
  "ECDF equalizes percentiles, not calibrated probabilities",
  "No post-result optimization or claim of external generalization",
  "No Structured Router or QHA 2 Copies in 3 evaluation"]}
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
 for name,result in results.items():
  print(name,[(k,round(v["rate"],4) if v["rate"] is not None else None) for k,v in result["metrics"].items()])
 print("Saved:",out)
if __name__=="__main__":main()
