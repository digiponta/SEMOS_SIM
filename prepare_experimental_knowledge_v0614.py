"""Create a separate, synthetic JSONL knowledge fixture for live LLM comparison.
This NEVER alters LLM_TRY's knowledge file.
"""
import argparse,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--output",default="data/experimental_semantic_knowledge_v0614.jsonl")
 a=p.parse_args()
 out=Path(a.output)
 if out.exists():p.error("Refusing overwrite")
 out.parent.mkdir(parents=True,exist_ok=True)
 record={"concept":"量子力学","assistant":"量子力学は原子や電子など微小な物理系の現象を記述する理論です。",
  "experiment":"SEMOS_SIM_v0.6.14","origin":"SYNTHETIC_KNOWLEDGE_FIXTURE",
  "verified":False}
 with out.open("x",encoding="utf-8") as f:
  f.write(json.dumps(record,ensure_ascii=False)+"\n")
 print("Experimental read-only lookup fixture saved:",out)
if __name__=="__main__":main()
