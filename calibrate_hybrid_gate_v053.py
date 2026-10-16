"""v0.5.3 development-only calibration of blended centroid/multi router.

Never read a final holdout in this script. Freeze selected settings in JSON
before evaluating any unused candidate evaluation sample.
"""
import argparse,hashlib,json
from pathlib import Path
from benchmark_v040 import load_csv
from calibrate_gate_v042 import sweep
from compare_prototypes_v044 import make_representations,predict_scores

FORBIDDEN={"independent_holdout.csv","final_holdout.csv"}
def fused_score_rows(rows,engine,weight=.7):
    if not 0<=weight<=1:raise ValueError("weight must be in [0,1]")
    reps=make_representations(engine);output=[]
    for r in rows:
        vec=engine.vector(r["text"])
        c=dict(predict_scores(vec,"centroid",reps))
        m=dict(predict_scores(vec,"multi",reps))
        ranked=sorted(((key,weight*c[key]+(1-weight)*m[key]) for key in c),
                      key=lambda item:(-item[1],item[0]))
        output.append({"text":r["text"],"label":r["label"],
                       "best_vm":ranked[0][0],"score":ranked[0][1],
                       "margin":ranked[0][1]-ranked[1][1]})
    return output

def calibrate(rows,engine,weight=.7,max_false_accept=.05):
    scores=fused_score_rows(rows,engine,weight)
    best,candidates=sweep(scores,max_false_accept)
    return best,len(candidates)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",default="data/validation_v043_dev100.csv")
    p.add_argument("--model",default="model/model-sem-internalized-v01575.pt")
    p.add_argument("--weight",type=float,default=.7)
    p.add_argument("--max-unknown-false-accept",type=float,default=.05)
    p.add_argument("--output",default="results/hybrid_gate_calibration_v053.json")
    p.add_argument("--freeze",default="config/hybrid_gate_v053_frozen.json")
    args=p.parse_args()
    if Path(args.validation).name.lower() in FORBIDDEN or "holdout" in Path(args.validation).name.lower():
        p.error("Final holdout data is forbidden for calibration")
    if not 0<=args.weight<=1 or not 0<=args.max_unknown_false_accept<=1:
        p.error("weight and maximum false-accept must be in [0,1]")
    from llm_sem_adapter import LLMSemAdapter
    engine=LLMSemAdapter(model_path=args.model)
    rows=load_csv(args.validation)
    best,n=calibrate(rows,engine,args.weight,args.max_unknown_false_accept)
    validation_hash=hashlib.sha256(Path(args.validation).read_bytes()).hexdigest()
    report={"version":"0.5.3","kind":"DEVELOPMENT_GATE_CALIBRATION",
            "validation":args.validation,"validation_sha256":validation_hash,
            "model":args.model,"weight":args.weight,
            "max_unknown_false_accept":args.max_unknown_false_accept,
            "search_candidates":n,"best":best,
            "limitations":["Previously reused development data; optimistic selection performance",
                           "Only weight=0.7 is considered; fixed before threshold sweep",
                           "No final holdout was read",
                           "Freeze parameters before any evaluation on candidate final data"]}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if best is None:
        print("No feasible operating point; frozen configuration not written")
        raise SystemExit(2)
    frozen={"version":"0.5.3","status":"FROZEN_DEVELOPMENT_SELECTED_NOT_FINAL_VALIDATED",
            "model":args.model,"weight":args.weight,
            "threshold":best["threshold"],"margin":best["margin"],
            "calibration_source":args.validation,"calibration_sha256":validation_hash,
            "unknown_false_accept_budget":args.max_unknown_false_accept}
    destination=Path(args.freeze)
    if destination.exists():
        existing=json.loads(destination.read_text(encoding="utf-8"))
        if existing!=frozen:
            raise SystemExit("Frozen settings already exist and differ: refusing overwrite")
    else:
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(frozen,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Frozen:",destination)
if __name__=="__main__":main()
