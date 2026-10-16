"""SEMOS_SIM v0.4 independent-routing benchmark.

The included fixtures are synthetic developmental examples, NOT independent
scientific validation. Supply a separately authored, frozen CSV for final tests.
"""
from __future__ import annotations
import argparse,csv,json,math,re,time
from collections import Counter,defaultdict
from pathlib import Path

LABELS=("VM-A","VM-B","VM-C","UNKNOWN")
CAPS={"VM-A":"量子力学 物理学 数学 科学 計算",
      "VM-B":"GPU CUDA AI LLM プログラミング 情報工学",
      "VM-C":"文学 言語 日本語 文章 芸術"}

def tokens(s):
    """Unicode character ngrams; usable for Japanese without external modules."""
    s=re.sub(r"\s+","",s.lower())
    return [s[i:i+n] for n in (1,2,3) for i in range(max(0,len(s)-n+1))]

class KeywordRouter:
    def __init__(self):
        self.rules={
            "VM-A":["量子","物理","数学","力学","微分","積分","電磁","確率"],
            "VM-B":["gpu","cuda","python","llm","ai","機械学習","人工知能","プログラム"],
            "VM-C":["文学","俳句","小説","言語","日本語","芸術","詩","作文"]}
    def predict(self,text):
        t=text.lower(); scores={k:sum(w in t for w in words) for k,words in self.rules.items()}
        ranking=sorted(scores,key=lambda k:scores[k],reverse=True)
        return ranking[0] if scores[ranking[0]]>0 and scores[ranking[0]]>scores[ranking[1]] else "UNKNOWN"

class TFIDFRouter:
    def __init__(self,examples):
        self.profiles={k:" ".join([CAPS[k]]+[x["text"] for x in examples if x["label"]==k])
                       for k in CAPS}
        docs=[Counter(tokens(s)) for s in self.profiles.values()]
        df=Counter(t for d in docs for t in d)
        self.idf={t:math.log((len(docs)+1)/(n+1))+1 for t,n in df.items()}
        self.profiles={k:self._vector(s) for k,s in self.profiles.items()}
    def _vector(self,text):
        d=Counter(tokens(text))
        vec={t:v*self.idf.get(t,math.log(4)+1) for t,v in d.items()}
        norm=math.sqrt(sum(x*x for x in vec.values())) or 1
        return {t:v/norm for t,v in vec.items()}
    def predict(self,text):
        q=self._vector(text)
        scores=sorted(((sum(v*self.profiles[k].get(t,0) for t,v in q.items()),k)
                       for k in CAPS),reverse=True)
        return scores[0][1] if scores[0][0]>0 and scores[0][0]-scores[1][0]>=0.02 else "UNKNOWN"

class VectorRouter:
    def __init__(self,engine,reject=True,threshold=.80,margin=.10):
        import torch
        self.torch=torch
        self.engine=engine;self.reject=reject
        self.threshold=threshold;self.margin=margin
        self.caps={k:engine.vector(v) for k,v in CAPS.items()}
    def predict(self,text):
        q=self.engine.vector(text)
        scores=sorted(((float(self.torch.dot(q,v).item()),k) for k,v in self.caps.items()),reverse=True)
        if self.reject and (scores[0][0]<self.threshold or scores[0][0]-scores[1][0]<self.margin):
            return "UNKNOWN"
        return scores[0][1]

def load_csv(path):
    with open(path,encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if not rows or not all("text" in r and "label" in r for r in rows):
        raise ValueError("CSV must contain nonempty text,label rows")
    for i,r in enumerate(rows,2):
        if not r["text"].strip() or r["label"] not in LABELS:
            raise ValueError(f"Invalid row {i}: {r}")
    return rows

def metrics(rows, predictions, elapsed):
    n=len(rows); known=[i for i,r in enumerate(rows) if r["label"]!="UNKNOWN"]
    unknown=[i for i,r in enumerate(rows) if r["label"]=="UNKNOWN"]
    held=[i for i,p in enumerate(predictions) if p=="UNKNOWN"]
    accepted=[i for i in known if predictions[i]!="UNKNOWN"]
    correct=sum(predictions[i]==rows[i]["label"] for i in known)
    routed_correct=sum(predictions[i]==rows[i]["label"] for i in accepted)
    matrix={gold:{pred:0 for pred in LABELS} for gold in LABELS}
    for row,pred in zip(rows,predictions):
        matrix[row["label"]][pred]+=1
    ratio=lambda num,den: num/den if den else None
    return {"n":n,"known_n":len(known),"unknown_n":len(unknown),
            "routing_accuracy_all_known":ratio(correct,len(known)),
            "known_coverage":ratio(len(accepted),len(known)),
            "selective_accuracy":ratio(routed_correct,len(accepted)),
            "unknown_reject_rate":ratio(sum(predictions[i]=="UNKNOWN" for i in unknown),len(unknown)),
            "unknown_reject_precision":ratio(sum(rows[i]["label"]=="UNKNOWN" for i in held),len(held)),
            "latency_ms_per_request":elapsed*1000/n,
            "confusion_matrix":matrix}

def evaluate(name,router,rows):
    start=time.perf_counter()
    predictions=[router.predict(r["text"]) for r in rows]
    return {"method":name,**metrics(rows,predictions,time.perf_counter()-start)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--train",required=True,help="CSV: text,label")
    p.add_argument("--test",required=True,help="Independent held-out CSV: text,label")
    p.add_argument("--output",default="results/benchmark_v040.json")
    p.add_argument("--model",default=None,help="LLM_SEM checkpoint relative to sibling repo")
    p.add_argument("--tokenizer",default=None)
    args=p.parse_args()
    train,test=load_csv(args.train),load_csv(args.test)
    # Exact text overlap is a fundamental guard, not a sufficient independence test.
    traintexts={re.sub(r"\s+","",r["text"]).lower() for r in train}
    overlap=[r["text"] for r in test if re.sub(r"\s+","",r["text"]).lower() in traintexts]
    if overlap:
        p.error(f"Data leakage: {len(overlap)} exact train/test overlaps")
    runs=[evaluate("keyword",KeywordRouter(),test),
          evaluate("tfidf",TFIDFRouter(train),test)]
    if args.model:
        from llm_sem_adapter import LLMSemAdapter
        engine=LLMSemAdapter(model_path=args.model,tokenizer_path=args.tokenizer)
        runs.append(evaluate("llm_sem_vector_no_gate",VectorRouter(engine,reject=False),test))
        runs.append(evaluate("semos_sim_gate",VectorRouter(engine,reject=True),test))
    output={"version":"0.4.0","dataset":{"train":len(train),"test":len(test),
            "train_labels":dict(Counter(r["label"] for r in train)),
            "test_labels":dict(Counter(r["label"] for r in test))},
            "limitations":["Only exact text overlap checked; paraphrase leakage needs human review",
                           "Thresholds are provisional and must be tuned on separate validation data",
                           "No claims of independence for bundled synthetic fixtures"],
            "results":runs}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
