"""v0.5.29.6: apply explicit GUI review decisions to validated retry packets.

No VM execution. No implicit approval. Only PENDING_USER_REVIEW can be
finalized. A repeated decision is rejected; full VM exhaustion => DISCOVERY.
"""
import argparse,hashlib,json
from pathlib import Path
from run_hitl_retry_v05293 import load_decisions
from simulate_vm_aware_recovery_v0525 import VMS

def apply_decision(packet,decision):
    p=dict(packet)
    if decision is None:return p
    rid=p["request_id"]
    if p.get("status")!="PENDING_USER_REVIEW":
        raise ValueError(f"{rid}: decision requires PENDING_USER_REVIEW")
    if not p.get("question") or not p.get("answer") or not p.get("provenance"):
        raise ValueError(f"{rid}: reply text and provenance required")
    if p.get("validation_error"):raise ValueError(f"{rid}: validation failed")
    if p.get("decision") is not None:raise ValueError(f"{rid}: prior decision exists")
    visited=list(p.get("visited_vms",[]))
    if not visited or len(visited)!=len(set(visited)) or p.get("vm")!=visited[-1]:
        raise ValueError(f"{rid}: invalid VM history")
    if any(v not in VMS for v in visited):raise ValueError(f"{rid}: unknown VM")
    p["events"]=list(p.get("events",[]))
    p["decision"]=decision
    p["events"].append({"state":"USER_DECISION_RECORDED","vm":p["vm"],"decision":decision})
    if decision=="APPROVE":
        p["status"]="USER_CONFIRMED"
    elif decision=="REJECT":
        p["status"]="USER_REJECTED"
    elif decision=="DISCOVERY":
        p["status"]="DISCOVERY"
    elif decision=="RETRY":
        target=next((vm for vm in VMS if vm not in visited),None)
        if target:
            p["status"]="RETRY_HANDOFF_PENDING_VM_EXECUTION"
            p["retry_vm"]=target
            p["events"].append({"state":"RETRY_HANDOFF","vm":target})
        else:
            p["status"]="DISCOVERY"
            p["events"].append({"state":"EXHAUSTED_VM_SET"})
    else:raise ValueError(f"{rid}: invalid decision")
    p["events"].append({"state":p["status"],"vm":p.get("retry_vm",p["vm"])})
    return p

def apply_all(doc,decisions):
    packets=doc.get("packets")
    if doc.get("version")!="0.5.29.4" or not isinstance(packets,list):
        raise ValueError("Expected v0.5.29.4 packets")
    ids=[p["request_id"] for p in packets]
    if len(ids)!=len(set(ids)):raise ValueError("Duplicate request IDs")
    if set(decisions)-set(ids):raise ValueError("Unknown decision request ID")
    return [apply_decision(p,decisions.get(p["request_id"])) for p in packets]

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/hitl_retry_validated_v05294.json")
    p.add_argument("--decision-file",required=True)
    p.add_argument("--output",default="results/hitl_retry_finalized_v05296.json")
    a=p.parse_args();dest=Path(a.output)
    if dest.exists():p.error("Refusing overwrite")
    raw=Path(a.input).read_bytes()
    try:
        doc=json.loads(raw);decisions=load_decisions(a.decision_file)
        if not decisions:raise ValueError("Decision file is empty; no update")
        packets=apply_all(doc,decisions)
    except (ValueError,KeyError,TypeError) as ex:p.error(str(ex))
    states=sorted({x["status"] for x in packets})
    report={"version":"0.5.29.6","kind":"HITL_EXPLICIT_USER_DECISION_FINALIZATION",
      "input_sha256":hashlib.sha256(raw).hexdigest(),
      "decision_sha256":hashlib.sha256(Path(a.decision_file).read_bytes()).hexdigest(),
      "summary":{s:sum(x["status"]==s for x in packets) for s in states},
      "packets":packets,"limitations":[
        "CSV decisions are not identity-authenticated",
        "Declared VM provenance is not independently verified",
        "USER_CONFIRMED means a recorded human decision, not factual truth",
        "No VM invocation, action execution, rollback, or cryptographic attestation"]}
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2))
    print("Saved:",dest)
if __name__=="__main__":main()
