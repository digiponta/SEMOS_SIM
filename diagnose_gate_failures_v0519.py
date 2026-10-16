"""v0.5.19 frozen gate failure attribution, diagnostic only.

The candidate router and thresholds are unchanged. Rows' gold and manual
semantic annotations are used only AFTER predictions for breakdowns.
"""
import argparse,csv,json
from pathlib import Path
from collections import Counter
from compare_gate_variants_v056 import enrich
from evaluate_frozen_holdout_v054 import sha,validate_freeze

DOMAINS=("VM-A","VM-B","VM-C","UNKNOWN")
def audit(rows,enriched,threshold,margin):
    result={}
    for gold in DOMAINS:
        subset=[(original,representation) for original,representation in zip(rows,enriched) if original["gold"]==gold]
        counts=Counter();samples=[]
        for original,rep in subset:
            candidate=rep["best_vm"]
            low_score=rep["score"]<threshold
            low_margin=rep["margin"]<margin
            rejected=low_score or low_margin
            right=candidate==gold if gold!="UNKNOWN" else False
            cause=("both" if low_score and low_margin else "similarity_only" if low_score else "margin_only" if low_margin else "accepted")
            counts[cause]+=1
            counts["candidate_correct" if right else "candidate_wrong_or_unknown"]+=1
            if right and rejected:counts["correct_candidate_rejected"]+=1
            if right and not rejected:counts["correct_candidate_accepted"]+=1
            if not rejected and gold=="UNKNOWN":counts["unknown_false_accepted"]+=1
            samples.append({"id":original["request_id"],"gold":gold,"candidate_vm":candidate,
                            "score":rep["score"],"margin":rep["margin"],
                            "score_gap":rep["score"]-threshold,
                            "margin_gap":rep["margin"]-margin,
                            "centroid_multi_agree":rep["centroid_top"]==rep["multi_top"],
                            "cause":cause,"candidate_correct":right})
        result[gold]={"n":len(subset),"counts":dict(sorted(counts.items())),"samples":samples}
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prospective",default="data/prospective_new_unseen.csv")
    p.add_argument("--manifest",default="results/prospective_manifest_v0517.json")
    p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
    p.add_argument("--comparison",default="results/prospective_comparison_v0518.json")
    p.add_argument("--output",default="results/gate_failure_attribution_v0519.json")
    a=p.parse_args()
    dest=Path(a.output)
    if dest.exists():p.error("Refusing overwrite")
    manifest=json.loads(Path(a.manifest).read_text(encoding="utf-8-sig"))
    if manifest.get("dataset_sha256")!=sha(a.prospective):p.error("Dataset differs from v0.5.17 manifest")
    reference=json.loads(Path(a.comparison).read_text(encoding="utf-8-sig"))
    if reference.get("dataset_sha256")!=sha(a.prospective):p.error("v0.5.18 dataset differs")
    frozen=json.loads(Path(a.frozen).read_text(encoding="utf-8-sig"))
    validate_freeze(frozen,sha(frozen["calibration_source"]))
    if reference.get("frozen_sha256")!=sha(a.frozen):p.error("Frozen configuration differs")
    with Path(a.prospective).open(encoding="utf-8-sig",newline="") as f:rows=list(csv.DictReader(f))
    from llm_sem_adapter import LLMSemAdapter
    engine=LLMSemAdapter(model_path=frozen["model"])
    enriched=enrich([{"text":row["text"],"label":row["gold"]} for row in rows],engine,frozen["weight"])
    predictions=[r["best_vm"] if r["score"]>=frozen["threshold"] and r["margin"]>=frozen["margin"] else "UNKNOWN" for r in enriched]
    prior=reference["results"]["llm_sem_frozen_vector_gate"]["predictions"]
    if [(r["request_id"],p) for r,p in zip(rows,predictions)]!=[(p["id"],p["predicted"]) for p in prior]:
        p.error("Frozen replay predictions differ from v0.5.18")
    groups=audit(rows,enriched,frozen["threshold"],frozen["margin"])
    out={"version":"0.5.19","kind":"FROZEN_GATE_FAILURE_ATTRIBUTION",
         "dataset_sha256":sha(a.prospective),"comparison_sha256":sha(a.comparison),
         "frozen_config_sha256":sha(a.frozen),"threshold":frozen["threshold"],
         "margin_threshold":frozen["margin"],"replay_matches_v0518":True,
         "by_gold_domain":groups,
         "limits":["Purely retrospective attribution on exposed synthetic 80-case set",
                   "Gold labels not used for inference; only post-hoc grouping",
                   "Failure causes are logical gate conditions, not evidence of causal mechanism",
                   "No retuning or independent validation",
                   "No QHA 2 Copies in 3 evaluation"]}
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    for domain,g in groups.items():print(domain,g["counts"])
    print("Saved:",dest)
if __name__=="__main__":main()
