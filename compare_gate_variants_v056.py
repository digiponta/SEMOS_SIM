"""SEMOS_SIM v0.5.6: development-only VM-aware gate candidates.

Reference v0.5.3 global gate is immutable. This script does not access
the 400-item holdout. Candidate variants are exploratory, not validated.
"""
import argparse, hashlib, json
from pathlib import Path
from benchmark_v040 import load_csv
from calibrate_hybrid_gate_v053 import fused_score_rows
from calibrate_gate_v042 import score_rows

def eval_predictions(rows,pred):
    known=[(r,p) for r,p in zip(rows,pred) if r["label"]!="UNKNOWN"]
    unknown=[(r,p) for r,p in zip(rows,pred) if r["label"]=="UNKNOWN"]
    ratio=lambda a,b:a/b if b else None
    accepted=[(r,p) for r,p in known if p!="UNKNOWN"]
    return {"known_accuracy":ratio(sum(r["label"]==p for r,p in known),len(known)),
            "known_coverage":ratio(len(accepted),len(known)),
            "selective_accuracy":ratio(sum(r["label"]==p for r,p in accepted),len(accepted)),
            "unknown_reject":ratio(sum(p=="UNKNOWN" for r,p in unknown),len(unknown)),
            "unknown_false_accept":ratio(sum(p!="UNKNOWN" for r,p in unknown),len(unknown)),
            "known_n":len(known),"unknown_n":len(unknown)}

def predict_variant(rows,thresholds,margin,consensus=False):
    output=[]
    for r in rows:
        vm=r["best_vm"]
        th=thresholds[vm] if isinstance(thresholds,dict) else thresholds
        accept=r["score"]>=th and r["margin"]>=margin
        if consensus:accept=accept and r["centroid_top"]==r["multi_top"]
        output.append(vm if accept else "UNKNOWN")
    return output

def enrich(rows,engine,weight):
    from compare_prototypes_v044 import make_representations,predict_scores
    representations=make_representations(engine)
    enriched=[]
    for original in rows:
        q=engine.vector(original["text"])
        c=predict_scores(q,"centroid",representations)
        m=predict_scores(q,"multi",representations)
        cs=dict(c);ms=dict(m)
        fused=sorted(((vm,weight*cs[vm]+(1-weight)*ms[vm]) for vm in cs),
                     key=lambda x:(-x[1],x[0]))
        enriched.append({"text":original["text"],"label":original["label"],
                         "best_vm":fused[0][0],"score":fused[0][1],
                         "margin":fused[0][1]-fused[1][1],
                         "centroid_top":c[0][0],"multi_top":m[0][0]})
    return enriched

def analyze(rows,base_threshold=.76,base_margin=.06,max_false_accept=.05):
    if not any(r["label"]=="UNKNOWN" for r in rows) or not any(r["label"]!="UNKNOWN" for r in rows):
        raise ValueError("Both known and unknown are required")
    baseline=eval_predictions(rows,predict_variant(rows,base_threshold,base_margin))
    variants={"frozen_global":(base_threshold,base_margin,False)}
    # Exploratory VM-specific offsets only; no conditional gate based on gold label.
    for vm in ("VM-A","VM-B","VM-C"):
        for delta in (-.08,-.04,.04):
            t={"VM-A":base_threshold,"VM-B":base_threshold,"VM-C":base_threshold}
            t[vm]=round(max(0,min(1,base_threshold+delta)),4)
            variants[f"{vm}_{delta:+.2f}"]=(t,base_margin,False)
    variants["consensus_global"]=(base_threshold,base_margin,True)
    for delta in (-.08,-.04,.04):
        variants[f"global_{delta:+.2f}"]=(round(max(0,min(1,base_threshold+delta)),4),base_margin,False)
    results=[]
    for name,(thresholds,margin,consensus) in variants.items():
        metrics=eval_predictions(rows,predict_variant(rows,thresholds,margin,consensus))
        results.append({"name":name,"thresholds":thresholds,"margin":margin,
                        "consensus":consensus,**metrics,
                        "within_false_accept_budget":metrics["unknown_false_accept"]<=max_false_accept})
    return baseline,results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--development",default="data/validation_v043_dev100.csv")
    p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
    p.add_argument("--output",default="results/gate_variants_development_v056.json")
    args=p.parse_args()
    if "holdout" in Path(args.development).name.lower():p.error("Holdout must not be used for exploratory comparison")
    from evaluate_frozen_holdout_v054 import validate_freeze,sha
    frozen=json.loads(Path(args.frozen).read_text(encoding="utf-8-sig"))
    validate_freeze(frozen,sha(frozen["calibration_source"]))
    from llm_sem_adapter import LLMSemAdapter
    rows=load_csv(args.development)
    enriched=enrich(rows,LLMSemAdapter(model_path=frozen["model"]),frozen["weight"])
    baseline,variants=analyze(enriched,frozen["threshold"],frozen["margin"],
                              frozen["unknown_false_accept_budget"])
    report={"version":"0.5.6","kind":"EXPLORATORY_DEVELOPMENT_ABLATION_NOT_HOLDOUT",
            "source":args.development,"source_sha256":sha(args.development),
            "frozen_sha256":sha(args.frozen),
            "reference_frozen_global":baseline,"variants":variants,
            "limits":["Only reused development data; comparative values have selection bias",
                      "VM-specific offsets are illustrative hypotheses, not independent calibration",
                      "Consensus checks prototype disagreement; no trained contrastive unknown model",
                      "Do not select or deploy a winning setting based on already evaluated 400-case holdout",
                      "No actual OS scheduling or task execution"]}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for v in variants:print(v["name"],"known=",v["known_accuracy"],"unknown_reject=",v["unknown_reject"],"budget=",v["within_false_accept_budget"])
    print("Saved:",out)
if __name__=="__main__":main()
