"""v0.5.4: one-shot evaluation of frozen Semantic Hybrid settings.

This is an independently *reserved* candidate holdout, not a certified
independent benchmark. The script never modifies the frozen parameters.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from benchmark_v040 import load_csv
from benchmark_os_advantage_v050 import run

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate_freeze(frozen,source_bytes_sha):
    if frozen.get("status")!="FROZEN_DEVELOPMENT_SELECTED_NOT_FINAL_VALIDATED":
        raise ValueError("Invalid frozen status")
    for key in ("threshold","margin","weight"):
        if not isinstance(frozen.get(key),(int,float)) or not 0<=frozen[key]<=1:
            raise ValueError(f"Invalid frozen {key}")
    if frozen.get("calibration_sha256")!=source_bytes_sha:
        raise ValueError("Frozen calibration SHA256 mismatch")
    if not frozen.get("model"):raise ValueError("Missing frozen model")
    return True

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--holdout",default="data/independent_holdout.csv")
    p.add_argument("--train",default="data/dev_train_v040.csv")
    p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
    p.add_argument("--audit",default="results/holdout_audit_v052.json")
    p.add_argument("--output",default="results/holdout_benchmark_v054.json")
    args=p.parse_args()
    frozen=json.loads(Path(args.frozen).read_text(encoding="utf-8-sig"))
    validation=frozen.get("calibration_source")
    if not validation or not Path(validation).is_file():
        p.error("Calibration source missing; cannot verify freeze")
    validate_freeze(frozen,sha(validation))
    if Path(args.holdout).resolve()==Path(validation).resolve():
        p.error("Cannot evaluate calibration data as holdout")
    audit=json.loads(Path(args.audit).read_text(encoding="utf-8-sig"))
    if not audit.get("pass_automatic_checks") or audit.get("kind")!="HOLDOUT_CANDIDATE_AUDIT_NOT_CERTIFICATION":
        p.error("Holdout audit did not pass")
    if Path(audit.get("holdout_path","")).resolve()!=Path(args.holdout).resolve():
        p.error("Holdout path differs from audit input")
    rows=load_csv(args.holdout)
    if len(rows)!=audit.get("n"):p.error("Holdout size differs from audit")
    counts={k:sum(r["label"]==k for r in rows) for k in ("VM-A","VM-B","VM-C","UNKNOWN")}
    if counts!=audit.get("label_counts"):p.error("Holdout label counts differ from audit")
    if Path(args.output).exists():p.error("Output already exists; refusing to overwrite holdout evaluation")
    results=run(rows,load_csv(args.train),model=frozen["model"],weight=frozen["weight"],
                threshold=frozen["threshold"],margin=frozen["margin"])
    payload={"version":"0.5.4","kind":"FIRST_PASS_CANDIDATE_HOLDOUT_FROZEN_CONFIG",
             "holdout":args.holdout,"holdout_sha256":sha(args.holdout),
             "frozen_config":args.frozen,"frozen_config_sha256":sha(args.frozen),
             "audit":args.audit,"limitations":[
                 "Development-aware synthetic holdout: manual review still required",
                 "Frozen parameters must not be retuned using these results",
                 "A passing overlap audit does not certify semantic independence",
                 "Routing correctness is a proxy, not OS task execution",
                 "Turnaround simulated; wall-clock routing measured only once"],
             "results":results}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    for k,m in results.items():
        print(f"{k:16} known={m['known_task_completion_proxy']:.3f} "
              f"coverage={m['known_coverage']:.3f} unknown_reject={m['unknown_rejection_rate']:.3f}")
    print("Saved:",out)
if __name__=="__main__":main()
