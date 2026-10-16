"""SEMOS_SIM v0.5.8 — paired, grouped development comparison.

Groups MUST be supplied explicitly for topic-disjoint evaluation. An exact
text fallback is not called topic-disjoint. Does not read final holdout.
"""
from __future__ import annotations
import argparse,csv,json,math,random
from collections import Counter
from pathlib import Path
from benchmark_v040 import load_csv
from compare_gate_variants_v056 import enrich,eval_predictions,predict_variant
from evaluate_separated_gate_v057 import fit,predict_one
from evaluate_frozen_holdout_v054 import validate_freeze,sha

def wilson(success,n,z=1.959963984540054):
    if n<1: return None
    p=success/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0,center-half),min(1,center+half)]

def load_groups(rows,csv_path=None):
    if csv_path is None:
        from audit_dataset_v043 import normalized
        return [normalized(r["text"]) for r in rows],"EXACT_TEXT_ONLY"
    with open(csv_path,encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not {"text","group_id"}<=set(reader.fieldnames or []):
            raise ValueError("Group CSV requires text and group_id columns")
        mapping={}
        for item in reader:
            text=item["text"];group=item["group_id"].strip()
            if not text or not group or text in mapping:
                raise ValueError("Empty or duplicate text/group_id")
            mapping[text]=group
    if set(mapping)!={r["text"] for r in rows} or len(rows)!=len(mapping):
        raise ValueError("Group mapping must cover each unique development request once")
    return [mapping[r["text"]] for r in rows],"CURATED_TOPIC_GROUPS_UNVERIFIED"

def paired_evaluate(rows,groups,folds=5,seed=58,threshold=.76,margin=.06):
    if len(rows)!=len(groups):raise ValueError("Missing groups")
    unique=list(set(groups))
    if folds<2 or len(unique)<folds:raise ValueError("Insufficient groups for folds")
    order=sorted(unique);random.Random(seed).shuffle(order)
    assignments={g:i%folds for i,g in enumerate(order)}
    cand=[None]*len(rows);ref=[None]*len(rows);fold_meta=[]
    for k in range(folds):
        held=[i for i,g in enumerate(groups) if assignments[g]==k]
        train=[r for i,r in enumerate(rows) if assignments[groups[i]]!=k]
        if not held or not train:raise ValueError("Empty fold")
        model=fit(train)
        subset=[rows[i] for i in held]
        ref_fold=predict_variant(subset,threshold,margin)
        for i,p in zip(held,ref_fold):
            ref[i]=p;cand[i]=predict_one(rows[i],model)
        fold_meta.append({"fold":k,"n_test":len(held),"n_train":len(train),
                          "held_group_count":len({groups[i] for i in held})})
    if any(x is None for x in cand+ref):raise AssertionError("Missing predictions")
    known=[i for i,r in enumerate(rows) if r["label"]!="UNKNOWN"]
    unknown=[i for i,r in enumerate(rows) if r["label"]=="UNKNOWN"]
    def stats(pred):
        m=eval_predictions(rows,pred)
        wrong=sum(pred[i]!="UNKNOWN" for i in unknown)
        m["unknown_false_accept_count"]=wrong
        m["unknown_false_accept_wilson95"]=wilson(wrong,len(unknown))
        m["known_correct_count"]=sum(pred[i]==rows[i]["label"] for i in known)
        return m
    diffs=[int(cand[i]==rows[i]["label"])-int(ref[i]==rows[i]["label"]) for i in known]
    result={"reference":stats(ref),"candidate":stats(cand),
            "paired_known_candidate_only_correct":sum(d==1 for d in diffs),
            "paired_known_reference_only_correct":sum(d==-1 for d in diffs),
            "folds":fold_meta}
    return result,ref,cand

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--development",default="data/validation_v043_dev100.csv")
    p.add_argument("--groups",help="Curated CSV: text,group_id. Strongly recommended.")
    p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
    p.add_argument("--folds",type=int,default=5)
    p.add_argument("--seed",type=int,default=58)
    p.add_argument("--output",default="results/paired_grouped_gate_v058.json")
    a=p.parse_args()
    if "holdout" in Path(a.development).name.lower():p.error("Cannot use holdout for model evaluation/tuning")
    frozen=json.loads(Path(a.frozen).read_text(encoding="utf-8-sig"))
    validate_freeze(frozen,sha(frozen["calibration_source"]))
    from llm_sem_adapter import LLMSemAdapter
    data=load_csv(a.development)
    groups,mode=load_groups(data,a.groups)
    rows=enrich(data,LLMSemAdapter(model_path=frozen["model"]),frozen["weight"])
    comparison,ref,candidate=paired_evaluate(rows,groups,a.folds,a.seed,frozen["threshold"],frozen["margin"])
    result={"version":"0.5.8","kind":"EXPLORATORY_PAIRED_GROUP_CV",
            "development_sha256":sha(a.development),"frozen_sha256":sha(a.frozen),
            "groups_mode":mode,"groups_file_sha256":sha(a.groups) if a.groups else None,
            "unique_groups":len(set(groups)),"seed":a.seed,"comparison":comparison,
            "diagnostics":[{"text":r["text"],"label":r["label"],"group_id":groups[i],
                            "reference":ref[i],"candidate":candidate[i]}
                           for i,r in enumerate(rows)],
            "limitations":["Both predictions use identical held-out fold indices; reference thresholds were selected previously on this entire development dataset",
                           "Prior prototype/algorithm selection also used development data, so neither result is a fresh independent benchmark",
                           "Curated group mappings are not proof of semantic independence",
                           "Wilson 95% intervals assume independent Bernoulli trials; correlated prompts may invalidate coverage",
                           "400-case holdout is not read; do not tune against it",
                           "No real operating-system execution benchmark"]}
    out=Path(a.output)
    if out.exists():p.error("Output already exists: refusing overwrite")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Group mode:",mode,"unique:",result["unique_groups"])
    for name in ("reference","candidate"):print(name,comparison[name])
    print("Saved:",out)
if __name__=="__main__":main()
