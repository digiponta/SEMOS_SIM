"""v0.5.21: predeclared VM-calibration protocol and disjoint-data audit.

No fitting to previously scored 80-case synthetic evaluation set.
Calibration requires a NEW source distinct from development, candidate
holdout, and exposed prospective data. This program audits, not trains.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from collections import Counter

LABELS={"VM-A","VM-B","VM-C","UNKNOWN"}
REQUIRED={"request_id","text","gold","topic_group","source_id"}
BANNED=("validation_v043_dev100.csv","independent_holdout.csv","prospective_new_unseen.csv")
def sha(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def norm(s):
 return "".join(s.casefold().split())
def load(path):
 with Path(path).open(encoding="utf-8-sig",newline="") as f:
  rd=csv.DictReader(f)
  if not rd.fieldnames or not REQUIRED.issubset(rd.fieldnames):
   raise ValueError("Missing required columns: "+", ".join(sorted(REQUIRED)))
  rows=list(rd)
 if not rows:raise ValueError("Empty CSV")
 ids=set();texts=set()
 for i,r in enumerate(rows,2):
  if any(not r[k].strip() for k in REQUIRED):raise ValueError("Empty field at row "+str(i))
  if r["gold"] not in LABELS:raise ValueError("Unknown label at row "+str(i))
  if r["request_id"] in ids or norm(r["text"]) in texts:raise ValueError("Duplicate request/text at row "+str(i))
  ids.add(r["request_id"]);texts.add(norm(r["text"]))
 return rows
def audit(calibration,evaluation,blocked):
 c=load(calibration);e=load(evaluation)
 ct={norm(r["text"]) for r in c}
 et={norm(r["text"]) for r in e}
 cs={r["source_id"] for r in c};es={r["source_id"] for r in e}
 cg={r["topic_group"] for r in c};eg={r["topic_group"] for r in e}
 overlaps={}
 for path in blocked:
  with Path(path).open(encoding="utf-8-sig",newline="") as f:
   rd=csv.DictReader(f)
   if "text" not in (rd.fieldnames or []):raise ValueError("Blocked file lacks text: "+path)
   old={norm(r["text"]) for r in rd}
  overlaps[path]={"calibration":len(old&ct),"evaluation":len(old&et)}
 flags={"text_overlap_calibration_eval":len(ct&et),
        "topic_overlap_calibration_eval":len(cg&eg),
        "source_overlap_calibration_eval":len(cs&es),
        "blocked_text_overlaps":overlaps}
 return {"version":"0.5.21","kind":"PREDECLARED_VM_CALIBRATION_DATA_SPLIT_AUDIT",
         "calibration":{"rows":len(c),"sha256":sha(calibration),"labels":dict(Counter(r["gold"] for r in c))},
         "evaluation":{"rows":len(e),"sha256":sha(evaluation),"labels":dict(Counter(r["gold"] for r in e))},
         "separation_checks":flags,
         "automatic_pass":not any([flags["text_overlap_calibration_eval"],
            flags["topic_overlap_calibration_eval"],flags["source_overlap_calibration_eval"],
            any(sum(v.values()) for v in overlaps.values())]),
         "frozen_candidate_protocol":{
           "reference":"global_gate_v053_no_retraining",
           "candidate":"vm_score_ecdf_calibration_train_only",
           "candidate_description":"For each top-1 VM, transform raw fused score to empirical CDF from calibration partition only; apply globally declared 0.76 score percentile and unchanged 0.06 raw margin; never use gold at inference.",
           "calibration_partition":"VM candidate score distributions; UNKNOWN included in candidate distribution",
           "predeclared_target_metrics":{"known_accuracy":0.70,"known_coverage":0.80,
              "selective_accuracy":0.90,"unknown_reject":0.95,"unknown_false_accept_max":0.05},
           "reporting":"Wilson 95% intervals and per-VM confusion counts on untouched evaluation set",
           "mandatory_controls":["Global frozen baseline","Vector only; no gate","VM calibrated gate (candidate)"]},
         "limitations":["Audit cannot establish semantic paraphrase or model pretraining independence",
                       "A topic/source split is necessary but not sufficient",
                       "Candidate protocol is a hypothesis not validated performance",
                       "No calibration fitting or evaluation is performed here",
                       "Not a QHA 2 Copies in 3 test"]}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--calibration",required=True)
 p.add_argument("--evaluation",required=True)
 p.add_argument("--block",action="append",default=[])
 p.add_argument("--output",default="results/calibration_split_audit_v0521.json")
 a=p.parse_args()
 if Path(a.calibration).resolve()==Path(a.evaluation).resolve():p.error("Same calibration/evaluation file")
 for path in [a.calibration,a.evaluation]:
  if Path(path).name in BANNED:p.error("Previously exposed dataset prohibited: "+path)
 for required in BANNED:
  if not any(Path(s).name==required for s in a.block):
   p.error("Provide --block for "+required)
 out=Path(a.output)
 if out.exists():p.error("Refusing overwrite")
 result=audit(a.calibration,a.evaluation,a.block)
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
 print("Pass:",result["automatic_pass"],"checks:",result["separation_checks"])
 print("Saved:",out)
if __name__=="__main__":main()
