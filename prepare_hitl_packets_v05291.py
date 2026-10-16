"""v0.5.29.1 HITL review packets and fail-closed retry handoff.

Review packets must come from explicitly supplied question/answer CSV; no
synthetic text is invented. Retry selects an unvisited VM for a new provisional
attempt, never pretends that a VM executed or that an answer was produced.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from simulate_vm_aware_recovery_v0525 import VMS
from simulate_hitl_review_v0529 import load_reviews

def read_payload(path):
    if not path:return {}
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not {"request_id","question","answer"}.issubset(reader.fieldnames or []):
            raise ValueError("payload CSV requires request_id,question,answer")
        out={}
        for row in reader:
            rid=row["request_id"].strip()
            if not rid or rid in out:raise ValueError("duplicate/empty request_id")
            out[rid]={"question":row["question"],"answer":row["answer"]}
        return out

def visited(record):
    result=[]
    for e in record.get("events",[]):
        if e.get("state") in ("DISPATCH","CAPABILITY_PROBE") and e.get("vm") in VMS:
            if e["vm"] not in result:result.append(e["vm"])
    if record["final"] in VMS and record["final"] not in result:
        result.append(record["final"])
    return result

def review(record,decision=None,payload=None):
    rid=record["request_id"];current=record["final"]
    if decision not in (None,"APPROVE","RETRY","DISCOVERY","REJECT"):raise ValueError("Invalid review")
    packet={"request_id":rid,"vm":current,"question":(payload or {}).get("question"),
      "answer":(payload or {}).get("answer"),"decision":decision,
      "visited_vms":visited(record),"events":[{"state":"ROUTING_RESULT","vm":current}]}
    if current=="DISCOVERY":
        if decision:raise ValueError("Review decision on Discovery request")
        packet["status"]="DISCOVERY";return packet
    packet["events"].append({"state":"PROVISIONAL_RESULT","vm":current})
    # If response text has not been supplied, review cannot be approved.
    if not payload or not str(payload.get("answer","")).strip() or not str(payload.get("question","")).strip():
        if decision:raise ValueError("Decision requires real question and answer payload")
        packet["status"]="AWAITING_ANSWER_PAYLOAD";return packet
    if decision is None:
        packet["status"]="PENDING_USER_REVIEW";return packet
    if decision=="APPROVE":
        packet["status"]="USER_CONFIRMED"
    elif decision=="REJECT":
        packet["status"]="USER_REJECTED"
    elif decision=="DISCOVERY":
        packet["status"]="DISCOVERY"
    else:
        next_vm=next((vm for vm in VMS if vm not in packet["visited_vms"]),None)
        if next_vm:
            packet["status"]="RETRY_HANDOFF_PENDING_VM_EXECUTION"
            packet["retry_vm"]=next_vm
            packet["events"].append({"state":"RETRY_HANDOFF","vm":next_vm})
        else:
            packet["status"]="DISCOVERY"
            packet["events"].append({"state":"EXHAUSTED_VM_SET"})
    return packet

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/user_authorized_rr_v0526.json")
    p.add_argument("--payload-file",default=None)
    p.add_argument("--review-file",default=None)
    p.add_argument("--output",default="results/hitl_packets_v05291.json")
    a=p.parse_args();out=Path(a.output)
    if out.exists():p.error("Refusing overwrite")
    raw=Path(a.input).read_bytes();doc=json.loads(raw)
    if doc.get("version")!="0.5.26":p.error("Expected v0.5.26 source")
    payloads=read_payload(a.payload_file);decisions=load_reviews(a.review_file)
    records=doc["records"];ids=[x["request_id"] for x in records]
    if len(set(ids))!=len(ids) or (set(payloads)|set(decisions))-set(ids):
        p.error("Duplicate records or unexpected request ID")
    try:
        packets=[review(x,decisions.get(x["request_id"]),payloads.get(x["request_id"])) for x in records]
    except ValueError as exc:p.error(str(exc))
    states=sorted(set(x["status"] for x in packets))
    report={"version":"0.5.29.1","kind":"HITL_REVIEW_PACKET_AND_RETRY_HANDOFF",
      "input_sha256":hashlib.sha256(raw).hexdigest(),
      "payload_sha256":hashlib.sha256(Path(a.payload_file).read_bytes()).hexdigest() if a.payload_file else None,
      "review_sha256":hashlib.sha256(Path(a.review_file).read_bytes()).hexdigest() if a.review_file else None,
      "summary":{s:sum(p["status"]==s for p in packets) for s in states},
      "packets":packets,
      "limitations":["v0.5.26 source is a simulated route, not actual VM-generated answers",
        "Questions and answers only from external explicit CSV, never invented by simulation",
        "RETRY is a handoff only; next VM is not run and no replacement answer produced",
        "Next VM uses unvisited fixed VM order, not semantic scores",
        "USER_CONFIRMED is subjective review, not proof of factual correctness",
        "No actual user UI or execution-side-effect authorization"]}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2));print("Saved:",out)
if __name__=="__main__":main()
