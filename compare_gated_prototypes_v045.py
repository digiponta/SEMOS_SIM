"""v0.4.5 gate comparison on development validation only.

Computes vectors once per request for the three representations. Calibrates
separate cosine/margin gates; reports risk-coverage tradeoff. Not final test.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from benchmark_v040 import load_csv
from compare_prototypes_v044 import make_representations,predict_scores
from calibrate_gate_v042 import sweep,score_rows

def evaluate(rows, engine, false_accept=.05):
    reps=make_representations(engine)
    import torch
    vectors=[engine.vector(r["text"]) for r in rows]
    output={}
    for mode in ("single","centroid","multi"):
        scores=[]
        for row,q in zip(rows,vectors):
            ranking=predict_scores(q,mode,reps)
            (name,best),(_,second)=ranking[:2]
            scores.append({"text":row["text"],"label":row["label"],
                           "best_vm":name,"score":best,"margin":best-second})
        best,grid=sweep(scores,false_accept)
        current=score_rows(scores,.80,.10)
        # Risk is incorrect accepted known / all accepted known.
        frontier=[]
        for point in sorted(grid,key=lambda p:(p["known_coverage"],p["unknown_false_accept_rate"])):
            if point["unknown_false_accept_rate"]<=false_accept:
                frontier.append({"threshold":point["threshold"],"margin":point["margin"],
                                 "coverage":point["known_coverage"],
                                 "risk":None if point["selective_accuracy"] is None else 1-point["selective_accuracy"],
                                 "unknown_false_accept_rate":point["unknown_false_accept_rate"]})
        output[mode]={"current_gate":current,"calibrated":best,
                      "eligible_operating_points":frontier,"raw_scores":scores}
    return output

def main():
    p=argparse.ArgumentParser(description="v0.4.5 prototype gate comparison")
    p.add_argument("--validation",default="data/validation_v043_dev100.csv")
    p.add_argument("--model",default="model/model-sem-internalized-v01575.pt")
    p.add_argument("--max-unknown-false-accept",type=float,default=.05)
    p.add_argument("--output",default="results/gated_prototypes_v045.json")
    args=p.parse_args()
    if not 0<=args.max_unknown_false_accept<=1:
        p.error("Invalid false-accept budget")
    if Path(args.validation).name=="dev_test_v040.csv":
        p.error("Do not tune gates on the old development test fixture")
    from llm_sem_adapter import LLMSemAdapter
    rows=load_csv(args.validation)
    if not any(r["label"]=="UNKNOWN" for r in rows) or not any(r["label"]!="UNKNOWN" for r in rows):
        p.error("Need known and UNKNOWN samples")
    engine=LLMSemAdapter(model_path=args.model)
    result=evaluate(rows,engine,args.max_unknown_false_accept)
    report={"version":"0.4.5","kind":"DEVELOPMENT_VALIDATION_NOT_FINAL",
            "validation":args.validation,"sample_count":len(rows),
            "unknown_false_accept_budget":args.max_unknown_false_accept,
            "notes":["Separate thresholds tuned on SAME validation set; optimistic development metrics",
                     "Not a valid independent held-out generalization estimate",
                     "Unknown false accepts and misrouted known requests are different errors",
                     "Existing production semantic_scheduler.py is not modified"],
            "methods":result}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for mode,entry in result.items():
        item=entry["calibrated"]
        print(f"{mode}:")
        if item is None: print("  no feasible operating point");continue
        print(f"  threshold={item['threshold']:.2f} margin={item['margin']:.2f}")
        print(f"  known_accuracy={item['known_accuracy']:.3f} "
              f"coverage={item['known_coverage']:.3f} "
              f"selective_accuracy={item['selective_accuracy']} "
              f"unknown_reject={item['unknown_reject_rate']:.3f}")
    print(f"Saved: {path}")

if __name__=="__main__": main()
