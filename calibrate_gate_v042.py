"""SEMOS_SIM v0.4.2 validation-only threshold sweep.

Use a separately authored validation CSV; NEVER tune thresholds on final test.
The command only writes diagnostics and does not change production thresholds.
"""
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path
from benchmark_v040 import load_csv,CAPS,LABELS

def apply_gate(row,threshold,margin):
    return row["best_vm"] if row["score"] >= threshold and row["margin"] >= margin else "UNKNOWN"

def score_rows(rows,threshold,margin):
    pred=[apply_gate(row,threshold,margin) for row in rows]
    known=[(r,p) for r,p in zip(rows,pred) if r["label"]!="UNKNOWN"]
    unknown=[(r,p) for r,p in zip(rows,pred) if r["label"]=="UNKNOWN"]
    routed=[(r,p) for r,p in known if p!="UNKNOWN"]
    ratio=lambda a,b:(a/b if b else None)
    return {
        "known_accuracy":ratio(sum(p==r["label"] for r,p in known),len(known)),
        "known_coverage":ratio(len(routed),len(known)),
        "selective_accuracy":ratio(sum(p==r["label"] for r,p in routed),len(routed)),
        "misroute_rate":ratio(sum(p!=r["label"] for r,p in routed),len(known)),
        "unknown_reject_rate":ratio(sum(p=="UNKNOWN" for r,p in unknown),len(unknown)),
        "unknown_false_accept_rate":ratio(sum(p!="UNKNOWN" for r,p in unknown),len(unknown)),
        "counts":{"known":len(known),"unknown":len(unknown),
                  "accepted_known":len(routed),"held_known":len(known)-len(routed)}
    }

def sweep(rows,max_unknown_false_accept=0.05):
    if not any(r["label"]=="UNKNOWN" for r in rows) or not any(r["label"]!="UNKNOWN" for r in rows):
        raise ValueError("Validation requires both known and UNKNOWN examples")
    candidates=[]
    for t_int in range(40,96,2):
        for m_int in range(0,31,2):
            t=t_int/100;m=m_int/100
            result=score_rows(rows,t,m)
            candidates.append({"threshold":t,"margin":m,**result})
    eligible=[r for r in candidates if r["unknown_false_accept_rate"]<=max_unknown_false_accept]
    if not eligible:
        return None,candidates
    # Maximize correctly routed known requests under a constrained unknown false-accept budget.
    # Stable tie breaks prefer higher selective accuracy, then stricter threshold.
    best=max(eligible,key=lambda x:(x["known_accuracy"],x["selective_accuracy"] or 0,
                                   x["unknown_reject_rate"],x["threshold"],x["margin"]))
    return best,candidates

def compute_scores(data,model):
    import torch
    from llm_sem_adapter import LLMSemAdapter
    engine=LLMSemAdapter(model_path=model)
    caps={k:engine.vector(t) for k,t in CAPS.items()}
    results=[]
    for row in data:
        q=engine.vector(row["text"])
        ranks=sorted(((float(torch.dot(q,v).item()),k) for k,v in caps.items()),reverse=True)
        results.append({"text":row["text"],"label":row["label"],
                        "best_vm":ranks[0][1],"score":ranks[0][0],
                        "margin":ranks[0][0]-ranks[1][0]})
    return results

def main():
    p=argparse.ArgumentParser(description="Validation-only Semantic OS gate calibration")
    p.add_argument("--validation",required=True,help="Labeled validation CSV, not final held-out test")
    p.add_argument("--model",default="model/model-sem-internalized-v01575.pt")
    p.add_argument("--output",default="results/calibration_v042.json")
    p.add_argument("--max-unknown-false-accept",type=float,default=.05)
    args=p.parse_args()
    if not 0<=args.max_unknown_false_accept<=1:
        p.error("false-accept constraint must be between 0 and 1")
    # Avoid accidental tuning on the bundled demonstration test fixtures.
    if Path(args.validation).name in {"dev_test_v040.csv"}:
        p.error("Do not calibrate thresholds using dev_test_v040.csv; create a separate validation split")
    data=load_csv(args.validation)
    scores=compute_scores(data,args.model)
    best,all_candidates=sweep(scores,args.max_unknown_false_accept)
    report={"version":"0.4.2","source":str(args.validation),
            "evaluation_kind":"development_validation_not_final_test",
            "n":len(scores),"max_unknown_false_accept":args.max_unknown_false_accept,
            "best":best,"selected_from":len(all_candidates),
            "note":"Exploratory calibrated operating point; freeze before independent final holdout.",
            "raw_scores":scores}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="raw_scores"},indent=2,ensure_ascii=False))
    print(f"Saved: {output}")

if __name__=="__main__":
    main()
