"""SEMOS_SIM v0.5.5 diagnostic only. Do not tune on holdout outputs."""
import argparse,collections,hashlib,json
from pathlib import Path
from benchmark_v040 import load_csv,LABELS
from compare_prototypes_v044 import make_representations,predict_scores
from hybrid_router_v046 import decision
from evaluate_frozen_holdout_v054 import validate_freeze,sha

def analyze_rows(rows,engine,config):
    reps=make_representations(engine)
    details=[]
    for row in rows:
        q=engine.vector(row["text"])
        c=predict_scores(q,"centroid",reps)
        m=predict_scores(q,"multi",reps)
        ungated, _=decision(c,m,mode="blend",weight=config["weight"])
        gated,reason=decision(c,m,mode="blend",weight=config["weight"],
                              threshold=config["threshold"],margin=config["margin"])
        cs=dict(c);ms=dict(m)
        ranks=sorted(((vm,config["weight"]*cs[vm]+(1-config["weight"])*ms[vm])
                      for vm in cs),key=lambda pair:(-pair[1],pair[0]))
        score=ranks[0][1];margin=ranks[0][1]-ranks[1][1]
        if gated=="UNKNOWN":
            reason=("low_similarity_and_margin" if score<config["threshold"] and margin<config["margin"]
                    else "low_similarity" if score<config["threshold"] else "low_margin")
        else:reason="accepted"
        details.append({"text":row["text"],"gold":row["label"],"ungated":ungated,
                        "gated":gated,"reason":reason,"centroid_top":c[0][0],
                        "multi_top":m[0][0],"consensus":c[0][0]==m[0][0],
                        "fused_score":score,"fused_margin":margin,
                        "ungated_correct":ungated==row["label"],"gated_correct":gated==row["label"]})
    return summarize(details)

def summarize(details):
    by_class={}
    for label in LABELS:
        group=[x for x in details if x["gold"]==label]
        if not group:continue
        n=len(group)
        by_class[label]={"n":n,
            "ungated_accuracy_or_rejection":sum(x["ungated"]==label for x in group)/n,
            "gated_accuracy_or_rejection":sum(x["gated"]==label for x in group)/n,
            "gated_held":sum(x["gated"]=="UNKNOWN" for x in group),
            "ungated_confusion":dict(collections.Counter(x["ungated"] for x in group)),
            "gated_confusion":dict(collections.Counter(x["gated"] for x in group)),
            "reasons":dict(collections.Counter(x["reason"] for x in group)),
            "centroid_multi_disagreement":sum(not x["consensus"] for x in group)}
    known=[x for x in details if x["gold"]!="UNKNOWN"]
    unknown=[x for x in details if x["gold"]=="UNKNOWN"]
    return {"version":"0.5.5","kind":"POST_HOLDOUT_DIAGNOSIS_NO_TUNING",
            "total":len(details),"by_class":by_class,
            "known_ungated_correct":sum(x["ungated"]==x["gold"] for x in known),
            "known_gated_correct":sum(x["gated"]==x["gold"] for x in known),
            "known_gate_rejections":sum(x["gated"]=="UNKNOWN" for x in known),
            "unknown_ungated_rejections":sum(x["ungated"]=="UNKNOWN" for x in unknown),
            "unknown_gated_rejections":sum(x["gated"]=="UNKNOWN" for x in unknown),
            "details":details,
            "limitations":["The candidate holdout was already evaluated in v0.5.4",
                           "Diagnostic comparisons may inform hypotheses, not tuning against this holdout",
                           "Improvements motivated by this report require a fresh untouched final evaluation",
                           "Neither label routing nor synthetic execution is a real operating-system benchmark"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--holdout",default="data/independent_holdout.csv")
    p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
    p.add_argument("--previous",default="results/holdout_benchmark_v054.json")
    p.add_argument("--output",default="results/holdout_diagnosis_v055.json")
    args=p.parse_args()
    previous=json.loads(Path(args.previous).read_text(encoding="utf-8-sig"))
    if previous.get("kind")!="FIRST_PASS_CANDIDATE_HOLDOUT_FROZEN_CONFIG":p.error("Invalid previous evaluation")
    if previous.get("holdout_sha256")!=sha(args.holdout):p.error("Holdout SHA256 mismatch")
    if previous.get("frozen_config_sha256")!=sha(args.frozen):p.error("Frozen config SHA256 mismatch")
    config=json.loads(Path(args.frozen).read_text(encoding="utf-8-sig"))
    validate_freeze(config,sha(config["calibration_source"]))
    from llm_sem_adapter import LLMSemAdapter
    engine=LLMSemAdapter(model_path=config["model"])
    report=analyze_rows(load_csv(args.holdout),engine,config)
    report["holdout_sha256"]=sha(args.holdout)
    report["frozen_sha256"]=sha(args.frozen)
    out=Path(args.output)
    if out.exists():p.error("Existing diagnostic output: refusing overwrite")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Known correct (ungated/gated):",report["known_ungated_correct"],report["known_gated_correct"])
    print("Unknown rejected (ungated/gated):",report["unknown_ungated_rejections"],report["unknown_gated_rejections"])
    for label,row in report["by_class"].items():
        print(label,row["gated_accuracy_or_rejection"],row["gated_held"],row["reasons"])
    print("Saved:",out)
if __name__=="__main__":main()
