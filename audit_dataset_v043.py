"""SEMOS_SIM v0.4.3 dataset audit — overlap and metadata, not ground-truth validation."""
from __future__ import annotations
import argparse,json,re,unicodedata
from collections import Counter
from pathlib import Path
from benchmark_v040 import load_csv,LABELS

def normalized(text):
    return "".join(ch for ch in unicodedata.normalize("NFKC",text).casefold() if ch.isalnum())

def bigrams(text):
    t=normalized(text)
    return {t[i:i+2] for i in range(max(0,len(t)-1))}

def jaccard(a,b):
    return len(a & b)/len(a | b) if a | b else 1.

def audit(validation,reference_paths=(),near_threshold=.80):
    rows=load_csv(validation)
    refs=[(str(path),r) for path in reference_paths for r in load_csv(path)]
    examples=[("validation",r) for r in rows]+refs
    seen={};duplicates=[];near=[]
    for i,(origin,row) in enumerate(examples):
        key=normalized(row["text"])
        if key in seen:
            other_origin,other_row=seen[key]
            duplicates.append({"text":row["text"],"source":origin,"previous_source":other_origin,
                               "label":row["label"],"previous_label":other_row["label"]})
        else:
            seen[key]=(origin,row)
        for other_origin,other in examples[:i]:
            if origin!="validation" and other_origin!="validation":
                continue
            if key==normalized(other["text"]):
                continue
            similarity=jaccard(bigrams(row["text"]),bigrams(other["text"]))
            if similarity>=near_threshold:
                near.append({"text":row["text"],"other":other["text"],"score":round(similarity,4),
                             "labels":[row["label"],other["label"]]})
    counts=Counter(r["label"] for r in rows)
    return {"validation":str(validation),"total":len(rows),"labels":dict(counts),
            "balanced_25_each":all(counts[label]==25 for label in LABELS),
            "exact_duplicates":duplicates,"near_duplicate_candidates":near,
            "pass_basic_checks":all(counts[label]==25 for label in LABELS) and not duplicates,
            "limitations":["Near-overlap is only character-bigram Jaccard",
                           "Manual review required for paraphrases, semantic ambiguity, and label correctness",
                           "These prompts are development validation, not independent final test"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",default="data/validation_v043_dev100.csv")
    p.add_argument("--reference",nargs="*",default=["data/dev_train_v040.csv","data/dev_test_v040.csv"])
    p.add_argument("--output",default="results/audit_v043.json")
    p.add_argument("--near-threshold",type=float,default=.8)
    args=p.parse_args()
    report=audit(args.validation,args.reference,args.near_threshold)
    target=Path(args.output);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:v if not isinstance(v,list) else {"count":len(v),"examples":v[:5]}
                      for k,v in report.items()},ensure_ascii=False,indent=2))
    if not report["pass_basic_checks"]:
        raise SystemExit(1)

if __name__=="__main__":
    main()
