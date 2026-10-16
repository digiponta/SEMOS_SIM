"""v0.5.29.5 retry reply intake and actionable diagnostics.

Never makes up VM output or execution timestamps. Uses user-supplied
answers plus mandatory execution metadata; CSV remains a declaration,
not cryptographic attestation. Does not execute any VM.
"""
import argparse,csv,json
from pathlib import Path
from validate_hitl_retry_v05294 import read_replies,inspect_reply

HEADER=("request_id","vm","question","answer","execution_id","executed_at","source")

def diagnose(packet_doc,replies):
    rows=[]
    for packet in packet_doc["packets"]:
        if packet.get("status")!="RETRY_HANDOFF_PENDING_VM_EXECUTION":
            continue
        rid=packet["request_id"]
        reply=replies.get(rid)
        if reply is None:
            reason="MISSING_REPLY_RECORD"
        elif reply.get("vm")!=packet.get("retry_vm"):
            reason="WRONG_VM"
        elif packet.get("question") and reply.get("question")!=packet["question"]:
            reason="QUESTION_MISMATCH"
        else:
            reason=inspect_reply(reply) or "READY_FOR_VALIDATION"
        rows.append({"request_id":rid,"expected_vm":packet.get("retry_vm"),"state":reason})
    return rows

def intake(record,request_id,vm,answer,execution_id,executed_at,source):
    if not str(answer).strip():raise ValueError("answer is empty; VM response required")
    if record["request_id"]!=request_id or record.get("retry_vm")!=vm or record.get("status")!="RETRY_HANDOFF_PENDING_VM_EXECUTION":
        raise ValueError("request_id / retry VM / pending state mismatch")
    candidate={"vm":vm,"question":record.get("question") or "","answer":answer.strip(),
               "execution_id":execution_id.strip(),"executed_at":executed_at.strip(),"source":source.strip()}
    failure=inspect_reply(candidate)
    if failure:raise ValueError(f"reply rejected: {failure}")
    return {"request_id":request_id,**candidate}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/hitl_retry_handoff_v05293.json")
    p.add_argument("--reply-file",default="data/hitl_retry_replies_v05294.csv")
    p.add_argument("--diagnose",action="store_true")
    p.add_argument("--intake",action="store_true")
    p.add_argument("--request-id")
    p.add_argument("--vm")
    p.add_argument("--answer")
    p.add_argument("--execution-id")
    p.add_argument("--executed-at")
    p.add_argument("--source")
    args=p.parse_args()
    doc=json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    packets=doc.get("packets",[])
    known={p["request_id"]:p for p in packets}
    path=Path(args.reply_file)
    replies=read_replies(path) if path.exists() else {}
    if args.diagnose and not args.intake:
        result=diagnose(doc,replies)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if any(x["state"]!="READY_FOR_VALIDATION" for x in result):
            print("未取得または検証保留の回答があります。VMの実際の回答と実行情報を登録してください。")
        return
    if not args.intake:p.error("Use --diagnose or --intake")
    required=(args.request_id,args.vm,args.answer,args.execution_id,args.executed_at,args.source)
    if any(x is None for x in required):p.error("Intake requires all six metadata and answer arguments")
    if args.request_id not in known:p.error("Unknown request_id")
    if args.request_id in replies and any(str(replies[args.request_id].get(k,"")).strip() for k in ("answer","execution_id","executed_at","source")):\n        p.error("Nonempty reply already exists: refusing overwrite")
    try:row=intake(known[args.request_id],*required)
    except ValueError as ex:p.error(str(ex))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8",newline="") as f:
        writer=csv.writer(f)
        if path.stat().st_size==0:writer.writerow(HEADER)
        writer.writerow([row[k] for k in HEADER])
    print("Saved external VM reply declaration for",args.request_id)
    print("Metadata is not authenticated; next run validate_hitl_retry_v05294.py")
if __name__=="__main__":main()
