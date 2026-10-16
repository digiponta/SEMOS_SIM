"""SEMOS_SIM v0.5.2: audit an externally curated unseen holdout.

Does NOT manufacture any final evaluation data. Exact and approximate textual
overlap checks cannot establish true independence; manual review is mandatory.
"""
from __future__ import annotations
import argparse,json,unicodedata
from pathlib import Path
from benchmark_v040 import load_csv
from audit_dataset_v043 import normalize,similarity

DEFAULT_REFERENCES=["data/dev_train_v040.csv","data/dev_test_v040.csv",
                    "data/validation_v043_dev100.csv","data/my_validation.csv"]

def audit_holdout(holdout, reference_paths, near_threshold=.8):
    target=load_csv(holdout)
    refs=[]
    for path in reference_paths:
        if Path(path).exists():
            refs.extend((path,r) for r in load_csv(path))
    exact=[];near=[];seen={}
    for i,row in enumerate(target):
        key=normalize(row["text"])
        if key in seen:
            exact.append({"holdout_index":i+1,"other":"holdout","other_index":seen[key]})
        seen[key]=i+1
        for source,ref in refs:
            similarity_value=similarity(row["text"],ref["text"])
            if key==normalize(ref["text"]):
                exact.append({"holdout_index":i+1,"other":source,"text":row["text"]})
            elif similarity_value>=near_threshold:
                near.append({"holdout_index":i+1,"other":source,
                             "similarity":round(similarity_value,4),
                             "text":row["text"],"reference_text":ref["text"]})
    from collections import Counter
    counts=dict(Counter(r["label"] for r in target))
    return {"kind":"HOLDOUT_CANDIDATE_AUDIT_NOT_CERTIFICATION",
            "holdout_path":str(holdout),"n":len(target),"label_counts":counts,
            "reference_files_checked":[p for p in reference_paths if Path(p).exists()],
            "missing_reference_files":[p for p in reference_paths if not Path(p).exists()],
            "exact_overlap_count":len(exact),"near_overlap_candidate_count":len(near),
            "exact_examples":exact[:50],"near_examples":near[:50],
            "pass_automatic_checks":not exact and not near and not any(
                not Path(p).exists() for p in reference_paths),
            "manual_review_required":True,
            "limitations":["No automatic text comparison can prove semantic/paraphrase independence",
                           "Previously used datasets not listed here must be added via --reference",
                           "Do not inspect final holdout labels to tune prototypes, weights or gates"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--holdout",required=True)
    p.add_argument("--reference",action="append",default=[],
                   help="Additional development CSV; may be specified repeatedly")
    p.add_argument("--near-threshold",type=float,default=.8)
    p.add_argument("--output",default="results/holdout_audit_v052.json")
    args=p.parse_args()
    if not 0<=args.near_threshold<=1:p.error("near-threshold must be in [0,1]")
    report=audit_holdout(args.holdout,DEFAULT_REFERENCES+args.reference,args.near_threshold)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if not k.endswith("_examples")},ensure_ascii=False,indent=2))
    print("Saved:",path)
    if not report["pass_automatic_checks"]:raise SystemExit(1)
if __name__=="__main__":main()
