"""v0.6.12: produce deterministic, synthetic evidence-comparison test cases.

Fixtures are not actual retrieval, model generations, or VM responses.
All example text is synthetic and unverified.
"""
import argparse,json
from pathlib import Path

QUESTION="量子力学とは何ですか"
GENERATED="量子力学は微視的な現象を記述する理論です。"
RETRIEVED="量子力学は微小な物理系を記述する理論です。"

def packet(case):
    valid={"EXACT_MATCH","DIFFERENT","NO_RETRIEVAL","UNKNOWN"}
    if case not in valid:raise ValueError("unsupported case")
    present=case in ("EXACT_MATCH","DIFFERENT")
    retrieved=GENERATED if case=="EXACT_MATCH" else RETRIEVED if present else None
    state="UNKNOWN" if case=="UNKNOWN" else "KNOWN" if case=="EXACT_MATCH" else "UNVERIFIED"
    status="RETRY_HANDOFF_PENDING_VM_EXECUTION" if case=="UNKNOWN" else "PENDING_USER_REVIEW"
    return {"request_id":"SYNTH-"+case,"vm":"VM-C","question":QUESTION,
      "answer":GENERATED,"status":status,"decision":None,
      "visited_vms":["VM-A","VM-C"],
      "provenance":{"execution_id":"synthetic-"+case,"executed_at":"2026-10-17T00:00:00+09:00",
        "source":"SYNTHETIC_TEST_ONLY"},
      "provenance_verified":False,
      "semantic_assessment":{"state":state,"verified":False,"full_unknown_gate_applied":False},
      "evidence_comparison":{
        "generated":{"answer":GENERATED,"origin":"SYNTHETIC_GENERATED_TEXT"},
        "retrieved":{"answer":retrieved,"concept":"量子力学" if present else None,
          "origin":"SYNTHETIC_LOCAL_KNOWLEDGE","present":present,
          "source_authenticated":False},
        "relation":case if case!="UNKNOWN" else "NO_RETRIEVAL",
        "verified":False,"requires_human_review":True},
      "events":[{"state":"SYNTHETIC_COMPARISON_CASE","case":case}],
      "validation_error":"UNKNOWN_SEMANTIC" if case=="UNKNOWN" else None}

def make_fixtures():
    rows=[packet(c) for c in ("EXACT_MATCH","DIFFERENT","NO_RETRIEVAL","UNKNOWN")]
    return {"version":"0.6.12","kind":"SYNTHETIC_EVIDENCE_COMPARISON_FIXTURE",
      "packets":rows,"summary":{c:1 for c in ("EXACT_MATCH","DIFFERENT","NO_RETRIEVAL","UNKNOWN")},
      "limitations":["These are fully synthetic examples, not actual LLM or knowledge retrieval",
         "No source authentication, user approval, VM execution or knowledge promotion"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="results/synthetic_evidence_comparison_v0612.json")
    a=p.parse_args()
    path=Path(a.output)
    if path.exists():p.error("Refusing overwrite")
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:
        json.dump(make_fixtures(),f,ensure_ascii=False,indent=2)
    print("Synthetic comparison fixtures saved:",path)
if __name__=="__main__":main()
