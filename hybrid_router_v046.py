"""SEMOS_SIM v0.4.6 exploratory centroid/multi consensus routing.

No final holdout and no production scheduler changes.
Scores are embedded once per request; optional score gates are EXPLICIT
arguments, not learned from the current evaluation set.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from benchmark_v040 import load_csv,metrics
from compare_prototypes_v044 import make_representations,predict_scores

def decision(centroid,multi,mode="strict",threshold=0.0,margin=0.0,weight=.5):
    """Return label, reason. Ranked sequences: [(VM, cosine), ...]."""
    if mode not in ("strict","blend"):
        raise ValueError("mode must be strict or blend")
    if not 0<=weight<=1: raise ValueError("weight must be in [0,1]")
    c,m=centroid[0],multi[0]
    if mode=="strict":
        if c[0]!=m[0]: return "UNKNOWN","disagreement"
        if min(c[1],m[1])<threshold: return "UNKNOWN","low_similarity"
        if min(c[1]-centroid[1][1],m[1]-multi[1][1])<margin:
            return "UNKNOWN","low_margin"
        return c[0],"agreement"
    cs=dict(centroid);ms=dict(multi)
    fused=sorted(((weight*cs[k]+(1-weight)*ms[k],k) for k in cs),reverse=True)
    if fused[0][0]<threshold or fused[0][0]-fused[1][0]<margin:
        return "UNKNOWN","blend_gate"
    return fused[0][1],"blend"

def evaluate(rows,engine,mode="strict",threshold=0.0,margin=0.0,weight=.5):
    reps=make_representations(engine)
    start=time.perf_counter()
    output=[];details=[]
    for r in rows:
        vector=engine.vector(r["text"])
        c=predict_scores(vector,"centroid",reps)
        m=predict_scores(vector,"multi",reps)
        label,reason=decision(c,m,mode,threshold,margin,weight)
        output.append(label)
        details.append({"text":r["text"],"expected":r["label"],"predicted":label,
                        "reason":reason,"centroid_top":c[0][0],"multi_top":m[0][0],
                        "centroid_margin":c[0][1]-c[1][1],
                        "multi_margin":m[0][1]-m[1][1]})
    return {"metrics":metrics(rows,output,time.perf_counter()-start),"details":details}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",default="data/validation_v043_dev100.csv")
    p.add_argument("--model",default="model/model-sem-internalized-v01575.pt")
    p.add_argument("--mode",choices=("strict","blend","both"),default="both")
    p.add_argument("--threshold",type=float,default=0.0)
    p.add_argument("--margin",type=float,default=0.0)
    p.add_argument("--weight",type=float,default=.5)
    p.add_argument("--output",default="results/hybrid_consensus_v046.json")
    args=p.parse_args()
    from llm_sem_adapter import LLMSemAdapter
    rows=load_csv(args.validation)
    engine=LLMSemAdapter(model_path=args.model)
    selected=("strict","blend") if args.mode=="both" else (args.mode,)
    result={mode:evaluate(rows,engine,mode,args.threshold,args.margin,args.weight) for mode in selected}
    report={"version":"0.4.6","kind":"EXPLORATORY_DEVELOPMENT_ONLY",
            "settings":{"threshold":args.threshold,"margin":args.margin,"weight":args.weight},
            "notes":["No threshold selection against this dataset; default zero gates are not calibrated",
                     "Strict consensus rejects differing top VM candidates",
                     "Blend score is a weighted combination of per-VM centroid and multi cosine",
                     "Validation was previously used to inspect/rank component methods; not independent"],
            "methods":result}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for mode,item in result.items():
        met=item["metrics"]
        print(f"{mode}: known_accuracy={met['routing_accuracy_all_known']:.3f}, "
              f"coverage={met['known_coverage']:.3f}, "
              f"selective={met['selective_accuracy']}, "
              f"unknown_reject={met['unknown_reject_rate']:.3f}")
    print(f"Saved: {dest}")

if __name__=="__main__":main()
