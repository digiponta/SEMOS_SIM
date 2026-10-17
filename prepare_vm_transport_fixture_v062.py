"""v0.6.2: generate a self-contained SYNTHETIC retry handoff fixture.

This is not recovery of user records and does not infer approvals.
The fixture drives v0.6.1 mock transport without prior results/ or stash.
"""
import argparse,json
from pathlib import Path

def make_fixture():
    packet={
      "request_id":"EVALA001","vm":"VM-A",
      "question":"量子力学とは何ですか",
      "answer":"量子力学は微視的な物理現象を記述する理論です。",
      "decision":"RETRY","visited_vms":["VM-B","VM-A"],
      "retry_vm":"VM-C","status":"RETRY_HANDOFF_PENDING_VM_EXECUTION",
      "events":[{"state":"SYNTHETIC_TEST_FIXTURE"},
                {"state":"RETRY_HANDOFF","vm":"VM-C"}]}
    return {"version":"0.5.29.3","kind":"SYNTHETIC_HITL_RETRY_HANDOFF_FIXTURE",
       "summary":{"RETRY_HANDOFF_PENDING_VM_EXECUTION":1},
       "packets":[packet],
       "limitations":["Synthetic state fixture; not user or VM activity",
                      "No user authorization or VM action is created",
                      "Do not use this as evidence of actual external VM execution"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output",default="results/synthetic_retry_handoff_v062.json")
    a=p.parse_args();dst=Path(a.output)
    if dst.exists():p.error("Refusing overwrite")
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(make_fixture(),ensure_ascii=False,indent=2),encoding="utf-8")
    print("Synthetic mock-only test fixture saved:",dst)
if __name__=="__main__":main()
