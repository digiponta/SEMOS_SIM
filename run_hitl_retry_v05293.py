"""v0.5.29.3: safe replay of user-requested retry using explicitly supplied VM output.

Source: v0.5.29.1 reviewed packets, e.g. results/hitl_packets_reviewed_v05292.json.
RETRY never executes a VM. An externally provided answer from the selected,
previously unvisited VM produces a NEW pending-user-review packet. A further
user decision is processed only when explicitly supplied with a round-specific
CSV, and confirmation of the previous VM never confirms the replacement.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from simulate_vm_aware_recovery_v0525 import VMS

CHOICES={"APPROVE","REJECT","RETRY","DISCOVERY"}

def load_replies(path):
    if not path:return {}
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not {"request_id","vm","question","answer"}.issubset(reader.fieldnames or []):
            raise ValueError("reply CSV requires request_id,vm,question,answer")
        out={}
        for row in reader:
            rid=row["request_id"].strip()
            if not rid or rid in out:raise ValueError("duplicate or empty reply ID")
            out[rid]={k:row[k].strip() for k in ("vm","question","answer")}
        return out

def load_decisions(path):
    if not path:return {}
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not {"request_id","decision"}.issubset(reader.fieldnames or []):
            raise ValueError("decision CSV requires request_id,decision")
        out={}
        for row in reader:
            rid=row["request_id"].strip();choice=row["decision"].strip().upper()
            if not rid or rid in out or choice not in CHOICES:
                raise ValueError("invalid decision or duplicate ID")
            out[rid]=choice
        return out

def advance(packet,reply=None,decision=None):
    p=dict(packet)
    p["events"]=list(packet.get("events",[]))
    rid=p["request_id"]
    if p.get("status")!="RETRY_HANDOFF_PENDING_VM_EXECUTION":
        if reply or decision:raise ValueError(f"{rid}: no pending retry")
        return p
    target=p["retry_vm"];visited=list(p["visited_vms"])
    if target not in VMS or target in visited:
        raise ValueError(f"{rid}: invalid or previously visited target")
    if len(visited)>=len(VMS):raise ValueError(f"{rid}: retry budget exhausted")
    if reply is None:
        if decision:raise ValueError(f"{rid}: decision without retry VM reply")
        return p
    if reply["vm"]!=target:
        raise ValueError(f"{rid}: reply comes from unexpected VM")
    if not reply["question"] or not reply["answer"]:
        raise ValueError(f"{rid}: empty question or answer")
    if p.get("question") and reply["question"]!=p["question"]:
        raise ValueError(f"{rid}: question changed across retry")
    p["previous_answer"]=p.get("answer")
    p["vm"]=target;p["question"]=reply["question"];p["answer"]=reply["answer"]
    p["visited_vms"]=visited+[target];p["decision"]=decision
    p.pop("retry_vm",None)
    p["events"].extend([{"state":"EXTERNAL_VM_RESPONSE_RECORDED","vm":target},
                        {"state":"PROVISIONAL_RESULT","vm":target}])
    if decision is None:
        p["status"]="PENDING_USER_REVIEW"
        p["events"].append({"state":"USER_REVIEW_REQUIRED","vm":target})
    elif decision=="APPROVE":
        p["status"]="USER_CONFIRMED";p["events"].append({"state":"USER_CONFIRMED","vm":target})
    elif decision=="REJECT":
        p["status"]="USER_REJECTED";p["events"].append({"state":"USER_REJECTED","vm":target})
    elif decision=="DISCOVERY":
        p["status"]="DISCOVERY";p["events"].append({"state":"USER_REQUESTED_DISCOVERY"})
    else:
        nxt=next((vm for vm in VMS if vm not in p["visited_vms"]),None)
        if nxt:
            p["status"]="RETRY_HANDOFF_PENDING_VM_EXECUTION";p["retry_vm"]=nxt
            p["events"].append({"state":"RETRY_HANDOFF","vm":nxt})
        else:
            p["status"]="DISCOVERY";p["events"].append({"state":"EXHAUSTED_VM_SET"})
    return p

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="results/hitl_packets_reviewed_v05292.json")
    parser.add_argument("--reply-file")
    parser.add_argument("--decision-file")
    parser.add_argument("--output",default="results/hitl_retry_v05293.json")
    a=parser.parse_args();dest=Path(a.output)
    if dest.exists():parser.error("Refusing overwrite")
    raw=Path(a.input).read_bytes();data=json.loads(raw)
    if data.get("version") not in ("0.5.29.1","0.5.29.3"):parser.error("Expected reviewed packet input")
    packets=data.get("packets")
    if not isinstance(packets,list):parser.error("Missing packets")
    ids=[x["request_id"] for x in packets]
    if len(ids)!=len(set(ids)):parser.error("Duplicate request IDs")
    replies=load_replies(a.reply_file);decisions=load_decisions(a.decision_file)
    if (set(replies)|set(decisions))-set(ids):parser.error("Unknown request ID in CSV")
    if set(decisions)-set(replies):parser.error("Review requires a fresh reply for this round")
    try:updated=[advance(p,replies.get(p["request_id"]),decisions.get(p["request_id"])) for p in packets]
    except (ValueError,KeyError) as exc:parser.error(str(exc))
    states=sorted({p["status"] for p in updated})
    report={"version":"0.5.29.3","kind":"HITL_USER_RETRY_EXTERNAL_RESPONSE",
        "input_sha256":hashlib.sha256(raw).hexdigest(),
        "reply_sha256":hashlib.sha256(Path(a.reply_file).read_bytes()).hexdigest() if a.reply_file else None,
        "decision_sha256":hashlib.sha256(Path(a.decision_file).read_bytes()).hexdigest() if a.decision_file else None,
        "summary":{s:sum(p["status"]==s for p in updated) for s in states},
        "packets":updated,"limitations":[
        "Requires actual external VM reply via CSV; no VM execution performed",
        "No decision inferred or carried over to a replacement answer",
        "User confirmation is not proof of correctness",
        "Review CSV is a user-entered fixture, not authenticated user identity",
        "No side-effect execution or rollback"]}
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2))
    print("Saved:",dest)
if __name__=="__main__":main()
