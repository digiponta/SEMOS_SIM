"""v0.4.4: Compare single, centroid and multi-prototype semantic routing.

Prototype texts are predeclared, never derived from validation labels.
This is developmental comparison, NOT an independent final benchmark.
"""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
from benchmark_v040 import CAPS,load_csv,metrics

PROTOTYPES={
"VM-A":["量子力学 波動関数 粒子 量子もつれ","古典力学 運動法則 質点 振動 共振","線形代数 微分 積分 方程式 数学","電磁気学 電場 磁場 光学 回折","統計 確率 ベイズ推定 数理"],
"VM-B":["GPU CUDA グラフィックプロセッサ 並列処理","深層学習 ニューラルネットワーク 機械学習","LLM Transformer 言語モデル トークナイザ","Python ソフトウェア プログラミング デバッグ","データ処理 推論 分散学習 計算機"],
"VM-C":["文学 小説 物語 作品批評","日本語 文法 敬語 言語学","詩 俳句 短歌 韻律","創作 作文 文章 表現","翻訳 戯曲 古典文学 修辞"],
}

def make_representations(engine):
    import torch
    normalize=lambda v:torch.nn.functional.normalize(v,p=2,dim=0)
    singles={k:engine.vector(text) for k,text in CAPS.items()}
    vectors={k:[engine.vector(t) for t in texts] for k,texts in PROTOTYPES.items()}
    centroids={k:normalize(torch.stack(vecs).mean(dim=0)) for k,vecs in vectors.items()}
    return singles,vectors,centroids

def predict_scores(query, mode, representations):
    import torch
    singles,vectors,centroids=representations
    source={"single":singles,"centroid":centroids}.get(mode)
    if mode=="multi":
        scores={k:max(float(torch.dot(query,v).item()) for v in vecs) for k,vecs in vectors.items()}
    elif source is not None:
        scores={k:float(torch.dot(query,v).item()) for k,v in source.items()}
    else:
        raise ValueError(f"Invalid mode: {mode}")
    ranks=sorted(scores.items(),key=lambda x:(-x[1],x[0]))
    return ranks

def run(rows,engine):
    representations=make_representations(engine)
    results={}
    for mode in ("single","centroid","multi"):
        start=time.perf_counter()
        predictions=[];details=[]
        for row in rows:
            q=engine.vector(row["text"])
            rankings=predict_scores(q,mode,representations)
            (best,score),(second,second_score)=rankings[:2]
            predictions.append(best)
            details.append({"text":row["text"],"expected":row["label"],"predicted":best,
                            "cosine":score,"margin":score-second_score})
        measurement=metrics(rows,predictions,time.perf_counter()-start)
        results[mode]={"metrics":measurement,"details":details}
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--validation",default="data/validation_v043_dev100.csv")
    p.add_argument("--model",default="model/model-sem-internalized-v01575.pt")
    p.add_argument("--output",default="results/prototype_comparison_v044.json")
    args=p.parse_args()
    from llm_sem_adapter import LLMSemAdapter
    engine=LLMSemAdapter(model_path=args.model)
    rows=load_csv(args.validation)
    results=run(rows,engine)
    report={"version":"v0.4.4","kind":"development_comparison_no_unknown_gate",
            "prototypes":PROTOTYPES,
            "notes":["Prototype descriptions fixed before running this comparison",
                     "No unknown rejection in these three ranking-only variants",
                     "Final independent holdout not evaluated",
                     "Multi-prototype maximum cosine can increase unknown acceptance; recalibrate separately"],
            "results":results}
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for mode,item in results.items():
        m=item["metrics"]
        print(f"{mode:9s} known_accuracy={m['routing_accuracy_all_known']:.3f} "
              f"unknown_reject={m['unknown_reject_rate']:.3f} "
              f"latency_ms={m['latency_ms_per_request']:.3f}")
        for label in ("VM-A","VM-B","VM-C"):
            cm=m["confusion_matrix"][label]
            print(f"  {label}: {cm[label]}/25 correct")
    print(f"Saved: {out}")

if __name__=="__main__":main()
