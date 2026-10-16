"""v0.4.1 per-request diagnostic (exploratory, no threshold optimization)."""
from __future__ import annotations
import argparse,csv,json,statistics
from pathlib import Path
from benchmark_v040 import CAPS, load_csv
from llm_sem_adapter import LLMSemAdapter

def diagnostic(rows,engine,threshold=.80,margin=.10):
    import torch
    capabilities={label:engine.vector(text) for label,text in CAPS.items()}
    detail=[]
    for row in rows:
        q=engine.vector(row["text"])
        scores=sorted(((float(torch.dot(q,v).item()),name)
                       for name,v in capabilities.items()),reverse=True)
        top,second=scores[:2]
        gap=top[0]-second[0]
        selected=top[1] if top[0]>=threshold and gap>=margin else "UNKNOWN"
        detail.append({"text":row["text"],"expected":row["label"],
                       "top_vm":top[1],"top_score":top[0],"margin":gap,
                       "assigned":selected,"correct":selected==row["label"],
                       "scores":{name:score for score,name in scores},
                       "hold_reason":("similarity_and_margin" if top[0]<threshold and gap<margin else
                                      "similarity" if top[0]<threshold else
                                      "margin" if gap<margin else "none")})
    return detail

def main():
    p=argparse.ArgumentParser(description="SEMOS_SIM v0.4.1 request-level diagnostics")
    p.add_argument("--data",default="data/dev_test_v040.csv")
    p.add_argument("--model",default="model/model-sem-internalized-v01575.pt")
    p.add_argument("--output",default="results/diagnostic_v041.json")
    args=p.parse_args()
    rows=load_csv(args.data)
    adapter=LLMSemAdapter(model_path=args.model)
    details=diagnostic(rows,adapter)
    held=[r for r in details if r["assigned"]=="UNKNOWN"]
    report={"note":"Development diagnostics only; do not tune final thresholds on the test set.",
            "thresholds":{"similarity":.80,"margin":.10},
            "counts":{"total":len(details),"held":len(held),
                      "false_rejects":sum(r["expected"]!="UNKNOWN" for r in held)},
            "examples":details}
    output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Request | Expected | Top VM | Score | Margin | Final | Reason")
    for r in details:
        print(f"{r['text']} | {r['expected']} | {r['top_vm']} | {r['top_score']:.4f} | {r['margin']:.4f} | {r['assigned']} | {r['hold_reason']}")
    print(f"Saved: {output}")

if __name__=="__main__":
    main()
