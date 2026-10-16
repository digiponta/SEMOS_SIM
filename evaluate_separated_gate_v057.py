"""v0.5.7: decouple candidate-VM confidence and open-set UNKNOWN decision.

Experimental only. Out-of-fold development evaluation grouped by exact text
normalization; no use of the previously evaluated 400-example holdout.
"""
from __future__ import annotations
import argparse,json,math,hashlib,random
from pathlib import Path
from benchmark_v040 import load_csv
from compare_gate_variants_v056 import enrich,eval_predictions,predict_variant

VMS=("VM-A","VM-B","VM-C")

def feature(row):
    return (float(row["score"]),float(row["margin"]),
            float(row["centroid_top"]==row["multi_top"]))

def fit(rows):
    """Shrinkage empirical feature centroids, per nominated VM and known/unknown.
    Never use labels while predicting; training labels are necessary for fitting.
    """
    centers={}
    for vm in VMS:
        for kind in ("known","unknown"):
            subset=[feature(r) for r in rows if r["best_vm"]==vm
                    and ((r["label"]!="UNKNOWN")==(kind=="known"))]
            # Generic fallback prevents a tiny bucket from causing invalid output.
            if not subset:
                subset=[feature(r) for r in rows if
                        ((r["label"]!="UNKNOWN")==(kind=="known"))]
            if not subset:
                raise ValueError("Both known and unknown needed in calibration")
            centers[f"{vm}:{kind}"]=[sum(v[i] for v in subset)/len(subset) for i in range(3)]
    return centers

def dist(a,b):
    # Conservative scaling avoids consensus (binary feature) dominating cosine.
    return sum(((x-y)/scale)**2 for x,y,scale in zip(a,b,(.15,.12,1.5)))

def predict_one(row,centers):
    vm=row["best_vm"];q=feature(row)
    known_dist=dist(q,centers[f"{vm}:known"])
    unknown_dist=dist(q,centers[f"{vm}:unknown"])
    return vm if known_dist<=unknown_dist else "UNKNOWN"

def evaluate_grouped_oof(rows,folds=5,seed=57):
    if folds<2 or len(rows)<folds:raise ValueError("At least 2 folds required")
    # Pair paraphrases by shared topically identical quoted term or prefix,
    # avoiding random-row leakage when the dataset has grouped prompts.
    # This grouping is heuristic and does not guarantee semantic independence.
    from audit_dataset_v043 import normalized
    groups={}
    for i,row in enumerate(rows):
        key=normalized(row["text"])
        groups.setdefault(key,[]).append(i)
    order=list(groups)
    random.Random(seed).shuffle(order)
    partitions=[[] for _ in range(folds)]
    for i,key in enumerate(order):partitions[i%folds].extend(groups[key])
    predictions=[None]*len(rows)
    for hold in partitions:
        train=[r for i,r in enumerate(rows) if i not in set(hold)]
        model=fit(train)
        for i in hold:predictions[i]=predict_one(rows[i],model)
    if any(x is None for x in predictions):raise AssertionError("Missing out-of-fold prediction")
    return eval_predictions(rows,predictions),predictions

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--development",default="data/validation_v043_dev100.csv")
    p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
    p.add_argument("--output",default="results/separated_unknown_gate_v057.json")
    p.add_argument("--folds",type=int,default=5)
    args=p.parse_args()
    if "holdout" in Path(args.development).name.lower():
        p.error("Do not train/evaluate on holdout")
    from evaluate_frozen_holdout_v054 import validate_freeze,sha
    frozen=json.loads(Path(args.frozen).read_text(encoding="utf-8-sig"))
    validate_freeze(frozen,sha(frozen["calibration_source"]))
    from llm_sem_adapter import LLMSemAdapter
    rows=enrich(load_csv(args.development),
                LLMSemAdapter(model_path=frozen["model"]),frozen["weight"])
    candidate,pred=evaluate_grouped_oof(rows,args.folds)
    reference=eval_predictions(rows,predict_variant(rows,frozen["threshold"],frozen["margin"]))
    result={"version":"0.5.7","kind":"EXPLORATORY_DEVELOPMENT_OPEN_SET_OOF",
            "development_sha256":sha(args.development),
            "frozen_sha256":sha(args.frozen),
            "folds":args.folds,"reference_frozen_on_development":reference,
            "candidate_oof":candidate,
            "diagnostic_predictions":[{"text":r["text"],"gold":r["label"],"prediction":v}
                                       for r,v in zip(rows,pred)],
            "limitations":["New contrastive centroid is an experimental lightweight model, not independent calibrated probability",
                           "Group splitting uses normalized exact text only; paraphrase/topic families may span folds",
                           "Source has been reused in previous development experiments",
                           "Reference evaluated on its own calibration data; not a fair independent comparison",
                           "No 400-item holdout used and no v0.5.3 freeze changed",
                           "No production Scheduler integration"]}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("REFERENCE:",reference)
    print("CANDIDATE OOF:",candidate)
    print("Saved:",dest)
if __name__=="__main__":main()
