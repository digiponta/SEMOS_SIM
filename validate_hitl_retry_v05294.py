"""v0.5.29.4: provenance-aware retry reply validation and review export.

Provenance is user-provided metadata, NOT independently authenticated.
Placeholder/empty replies fail closed, and no user decision is inferred.
"""
import argparse,csv,hashlib,json,re
from pathlib import Path
from run_hitl_retry_v05293 import advance

PLACEHOLDERS=("ここに","実際の回答を入力","TODO","TBD","PLACEHOLDER","SAMPLE ANSWER","DUMMY ANSWER")
def inspect_reply(reply):
    answer=str(reply.get("answer","")).strip()
    question=str(reply.get("question","")).strip()
    if not question or not answer:return "MISSING_TEXT"
    if any(s.casefold() in answer.casefold() for s in PLACEHOLDERS):return "PLACEHOLDER"
    if len(answer)<8:return "TOO_SHORT"
    for key in ("execution_id","executed_at","source"):
        if not str(reply.get(key,"")).strip():return "MISSING_PROVENANCE_"+key.upper()
    if not re.fullmatch(r"[^\s,]{3,128}",reply["execution_id"]):return "INVALID_EXECUTION_ID"
    if not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:Z|[+-]\d\d:\d\d)",reply["executed_at"]):
        return "INVALID_TIMESTAMP"
    return None

def read_replies(path):
    if not path:return {}
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        fields=("request_id","vm","question","answer","execution_id","executed_at","source")
        if not set(fields).issubset(reader.fieldnames or []):raise ValueError("Required CSV: "+",".join(fields))
        out={}
        for row in reader:
            rid=row["request_id"].strip()
            if not rid or rid in out:raise ValueError("duplicate/empty request_id")
            out[rid]={k:row[k].strip() for k in fields if k!="request_id"}
    return out

def process(packet,reply=None):
    if reply is None:return advance(packet)
    # Strictly require an outstanding retry; no silent remapping.
    if packet.get("status")!="RETRY_HANDOFF_PENDING_VM_EXECUTION":
        raise ValueError("No pending retry for "+packet["request_id"])
    if reply.get("vm")!=packet.get("retry_vm"):
        raise ValueError("Wrong VM for "+packet["request_id"])
    error=inspect_reply(reply)
    if error:
        p=dict(packet);p["events"]=list(packet.get("events",[]))+[{"state":"REPLY_VALIDATION_FAILED","reason":error}]
        p["validation_error"]=error
        # Keep retry open, never promote a suspect reply to user review.
        return p
    result=advance(packet,reply)
    result["provenance"]={k:reply[k] for k in ("execution_id","executed_at","source")}
    result["provenance_verified"]=False
    result["events"].append({"state":"PROVENANCE_DECLARED","execution_id":reply["execution_id"]})
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/hitl_retry_handoff_v05293.json")
    p.add_argument("--reply-file",required=True)
    p.add_argument("--output",default="results/hitl_retry_validated_v05294.json")
    a=p.parse_args();dest=Path(a.output)
    if dest.exists():p.error("Refusing overwrite")
    raw=Path(a.input).read_bytes()
    doc=json.loads(raw)
    if doc.get("version") not in ("0.5.29.1","0.5.29.3","0.5.29.4"):p.error("Unsupported input version")
    records=doc["packets"];ids=[r["request_id"] for r in records]
    if len(set(ids))!=len(ids):p.error("Duplicate packet request ID")
    replies=read_replies(a.reply_file)
    if set(replies)-set(ids):p.error("Unknown reply request ID")
    try:rows=[process(r,replies.get(r["request_id"])) for r in records]
    except (ValueError,KeyError) as ex:p.error(str(ex))
    states=sorted({r["status"] for r in rows})
    summary={s:sum(r["status"]==s for r in rows) for s in states}
    summary["validation_failed"]=sum(bool(r.get("validation_error")) for r in rows)
    report={"version":"0.5.29.4","kind":"HITL_RETRY_PROVENANCE_REVIEW",
      "input_sha256":hashlib.sha256(raw).hexdigest(),
      "reply_sha256":hashlib.sha256(Path(a.reply_file).read_bytes()).hexdigest(),
      "summary":summary,"packets":rows,
      "limitations":["Metadata is declared by CSV supplier, not cryptographically verified",
        "Placeholder detection is heuristic, not proof of correctness",
        "No real VM invocation, authenticated identity, or transaction execution",
        "Retry reply cannot be implicitly approved"]}
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("Saved:",dest)
if __name__=="__main__":main()
