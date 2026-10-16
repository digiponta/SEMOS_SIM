"""v0.5.18: frozen prospective routing comparison, text-only controls.

WARNING: dataset is developer-authored synthetic examples and already visible;
this is exploratory, not independent third-party validation. Manual SPOI
annotations are GOLD-SIDE METADATA ONLY; none is available to predictors.
"""
import argparse,csv,json
from pathlib import Path
from benchmark_v040 import KeywordRouter,TFIDFRouter,load_csv
from compare_gate_variants_v056 import enrich,eval_predictions,predict_variant
from evaluate_frozen_holdout_v054 import sha,validate_freeze
from prepare_prospective_eval_v0517 import inspect

GOALS={"known_accuracy":.70,"known_coverage":.80,"selective_accuracy":.90,"unknown_reject":.95,"unknown_false_accept":.05}
def summarize(records,predictions):
    rows=[{"label":r["gold"]} for r in records]
    base=eval_predictions(rows,predictions)
    base["predictions"]= [{"id":r["request_id"],"gold":r["gold"],"predicted":p} for r,p in zip(records,predictions)]
    base["targets"]={k:{"value":v,"direction":"max" if k=="unknown_false_accept" else "min",
                             "point_estimate_met":base[k]<=v if k=="unknown_false_accept" else base[k]>=v}
                      for k,v in GOALS.items()}
    return base
def evaluate(records,training,engine,config):
    plain=[{"text":r["text"],"label":r["gold"]} for r in records]
    enriched=enrich(plain,engine,config["weight"])
    predictions={
      "keyword_text_only":[KeywordRouter().predict(r["text"]) for r in records],
      "tfidf_dev_train_text_only":[TFIDFRouter(training).predict(r["text"]) for r in records],
      "llm_sem_frozen_vector":[r["best_vm"] for r in enriched],
      "llm_sem_frozen_vector_gate":predict_variant(enriched,config["threshold"],config["margin"])
    }
    return {name:summarize(records,preds) for name,preds in predictions.items()}
def read_records(path):
    with open(path,encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prospective",default="data/prospective_new_unseen.csv")
    p.add_argument("--manifest",default="results/prospective_manifest_v0517.json")
    p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
    p.add_argument("--train",default="data/dev_train_v040.csv")
    p.add_argument("--output",default="results/prospective_comparison_v0518.json")
    a=p.parse_args()
    output=Path(a.output)
    if output.exists():p.error("Refusing to overwrite results")
    manifest=json.loads(Path(a.manifest).read_text(encoding="utf-8-sig"))
    if manifest.get("version")!="0.5.17" or not manifest.get("audit",{}).get("valid_structure"):
        p.error("Valid v0.5.17 manifest required")
    if sha(a.prospective)!=manifest["dataset_sha256"]:
        p.error("Prospective dataset changed since manifest")
    frozen=json.loads(Path(a.frozen).read_text(encoding="utf-8-sig"))
    validate_freeze(frozen,sha(frozen["calibration_source"]))
    rows=read_records(a.prospective)
    if not inspect(a.prospective)["valid_structure"]:p.error("Invalid prospective rows")
    training=load_csv(a.train)
    from llm_sem_adapter import LLMSemAdapter
    engine=LLMSemAdapter(model_path=frozen["model"])
    result=evaluate(rows,training,engine,frozen)
    out={"version":"0.5.18","kind":"SYNTHETIC_PROSPECTIVE_TEXT_ONLY_CONTROLS",
         "dataset_sha256":sha(a.prospective),"manifest_sha256":sha(a.manifest),
         "frozen_sha256":sha(a.frozen),"training_sha256":sha(a.train),
         "annotation_policy":"SPOI and gold labels not used by predictors",
         "results":result,
         "limitations":["Structured SPOI prediction NOT evaluated: human-authored SPOI annotations would leak semantic interpretation",
                        "Each baseline consumes the raw request text only",
                        "Synthetic user/assistant-authored examples, not certified independent",
                        "Do not modify the benchmark or tune methods after seeing results",
                        "Fused LLM_SEM vector uses original frozen similarity scoring",
                        "No QHA 2 Copies in 3 behavior tested"]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")
    for name,data in result.items():
        print(name,"known",data["known_accuracy"],"coverage",data["known_coverage"],"unknown_reject",data["unknown_reject"])
    print("Saved:",output)
if __name__=="__main__":main()
