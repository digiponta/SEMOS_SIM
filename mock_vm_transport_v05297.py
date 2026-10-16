"""SEMOS_SIM v0.5.29.7 — mock VM reply transport for HITL retries.

Only mock transport is implemented. No production VM is contacted. An
explicitly provided fixture is matched to a pending request and its retry VM.
A successful mock reply remains identified as MOCK in the output; it must not
be treated as authenticated real-world VM evidence.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from datetime import datetime, timezone
from validate_hitl_retry_v05294 import process

def fetch_mock(packet,fixtures):
    rid=packet["request_id"]
    if packet.get("status")!="RETRY_HANDOFF_PENDING_VM_EXECUTION":
        return None
    item=fixtures.get(rid)
    if item is None:return None
    if item.get("simulate")=="timeout":
        raise TimeoutError(f"{rid}: simulated timeout")
    if item.get("simulate")=="connection_error":
        raise ConnectionError(f"{rid}: simulated connection failure")
    if item.get("request_id")!=rid or item.get("vm")!=packet.get("retry_vm"):
        raise ValueError(f"{rid}: response/request VM mismatch")
    if packet.get("question") and item.get("question")!=packet["question"]:
        raise ValueError(f"{rid}: question mismatch")
    answer=item.get("answer","")
    if not answer:raise ValueError(f"{rid}: empty mock answer")
    return {"vm":item["vm"],"question":item["question"],"answer":answer,
        "execution_id":item["execution_id"],"executed_at":item["executed_at"],
        "source":"mock-fixture"}

def read_fixtures(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        rows=csv.DictReader(f)
        required={"request_id","vm","question","answer","execution_id","executed_at","simulate"}
        if not required.issubset(rows.fieldnames or []):
            raise ValueError("Fixture CSV missing columns: "+",".join(sorted(required)))
        data={}
        for raw in rows:
            row={k:(v or "").strip() for k,v in raw.items()}
            rid=row["request_id"]
            if not rid or rid in data:raise ValueError("duplicate/blank fixture ID")
            data[rid]=row
        return data

def route(packet,fixtures):
    p=dict(packet)
    if p.get("status")!="RETRY_HANDOFF_PENDING_VM_EXECUTION":return p
    try:reply=fetch_mock(p,fixtures)
    except (TimeoutError,ConnectionError) as exc:
        p["transport_error"]=type(exc).__name__
        p["events"]=list(p.get("events",[]))+[{
            "state":"MOCK_TRANSPORT_FAILURE","kind":type(exc).__name__}]
        return p
    if reply is None:return p
    result=process(p,reply)
    if result.get("status")=="PENDING_USER_REVIEW":
        result["transport"]="MOCK_ONLY"
        result["events"].append({"state":"MOCK_REPLY_VALIDATED","vm":reply["vm"]})
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",default="results/hitl_retry_handoff_v05293.json")
    parser.add_argument("--fixture-file",required=True)
    parser.add_argument("--output",default="results/hitl_mock_transport_v05297.json")
    args=parser.parse_args()
    dest=Path(args.output)
    if dest.exists():parser.error("Refusing overwrite")
    raw=Path(args.input).read_bytes()
    data=json.loads(raw);packets=data.get("packets")
    if not isinstance(packets,list):parser.error("Missing packets")
    ids=[x["request_id"] for x in packets]
    if len(ids)!=len(set(ids)):parser.error("Duplicate IDs")
    try:
        fixtures=read_fixtures(args.fixture_file)
        if set(fixtures)-set(ids):raise ValueError("Unknown fixture ID")
        results=[route(item,fixtures) for item in packets]
    except (ValueError,KeyError) as exc:parser.error(str(exc))
    states=sorted({x["status"] for x in results})
    report={"version":"0.5.29.7","kind":"HITL_MOCK_VM_TRANSPORT",
        "input_sha256":hashlib.sha256(raw).hexdigest(),
        "fixture_sha256":hashlib.sha256(Path(args.fixture_file).read_bytes()).hexdigest(),
        "summary":{s:sum(x["status"]==s for x in results) for s in states},
        "packets":results,"limitations":[
           "Mock fixtures only; no real VM communication",
           "Mock response has no verified origin and is not real VM output",
           "No user decision inferred; finalization requires explicit review",
           "No side effects or rollback"]}
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2))
    print("Saved:",dest)
if __name__=="__main__":main()
