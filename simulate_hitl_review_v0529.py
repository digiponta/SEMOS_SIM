"""v0.5.29 Human-in-the-Loop response review state machine (simulation).

Consumes v0.5.26 VM routing records, NOT real VM answers.
A VM 'SIMULATED_COMPLETED' is only a PROVISIONAL_RESULT.
User approval must be supplied explicitly in a review CSV; missing => PENDING,
not implicit acceptance. Human choices are not inferred from gold labels.
"""
import argparse,csv,hashlib,json
from pathlib import Path

DECISIONS={"APPROVE","RETRY","DISCOVERY","REJECT"}
def load_reviews(path):
    if not path:return {}
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not {"request_id","decision"}.issubset(reader.fieldnames or []):
            raise ValueError("review CSV requires request_id,decision")
        out={}
        for row in reader:
            rid=row["request_id"].strip()
            decision=row["decision"].strip().upper()
            if not rid or rid in out or decision not in DECISIONS:
                raise ValueError("duplicate or invalid review decision")
            out[rid]=decision
        return out

def process(record,decision=None):
    rid=record["request_id"];final=record["final"]
    if decision is not None and decision not in DECISIONS:raise ValueError("invalid decision")
    base={"request_id":rid,"candidate":final,"review_decision":decision,
          "events":[{"state":"ROUTING_RESULT","route":final}]}
    if final=="DISCOVERY":
        if decision is not None:raise ValueError("cannot approve review for discovery route")
        base["status"]="DISCOVERY";base["events"].append({"state":"DISCOVERY"})
    else:
        base["events"].append({"state":"PROVISIONAL_RESULT","vm":final})
        if decision is None:
            base["status"]="PENDING_USER_REVIEW"
            base["events"].append({"state":"USER_REVIEW_REQUIRED"})
        elif decision=="APPROVE":
            base["status"]="USER_CONFIRMED"
            base["events"].append({"state":"USER_CONFIRMED","vm":final})
        elif decision=="RETRY":
            base["status"]="RETRY_REQUESTED"
            base["events"].append({"state":"RETRY_REQUESTED"})
        elif decision=="DISCOVERY":
            base["status"]="DISCOVERY"
            base["events"].append({"state":"USER_REQUESTED_DISCOVERY"})
        else:
            base["status"]="USER_REJECTED"
            base["events"].append({"state":"USER_REJECTED"})
    return base

def summarize(rows):
    states=("DISCOVERY","PENDING_USER_REVIEW","USER_CONFIRMED","RETRY_REQUESTED","USER_REJECTED")
    return {s:sum(x["status"]==s for x in rows) for s in states}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/user_authorized_rr_v0526.json")
    p.add_argument("--review-file",default=None)
    p.add_argument("--output",default="results/hitl_review_v0529.json")
    a=p.parse_args();dest=Path(a.output)
    if dest.exists():p.error("Refusing overwrite")
    raw=Path(a.input).read_bytes();d=json.loads(raw)
    if d.get("version")!="0.5.26" or d.get("kind")!="USER_AUTHORIZED_ROUND_ROBIN_SIMULATION":
        p.error("Expected v0.5.26 user-authorized RR output")
    records=d["records"];ids=[x["request_id"] for x in records]
    if len(set(ids))!=len(ids):p.error("duplicate request IDs")
    decisions=load_reviews(a.review_file)
    if set(decisions)-set(ids):p.error("review contains unknown request ID")
    try:results=[process(x,decisions.get(x["request_id"])) for x in records]
    except ValueError as exc:p.error(str(exc))
    output={"version":"0.5.29","kind":"HUMAN_IN_THE_LOOP_REVIEW_STATE_SIMULATION",
        "source_sha256":hashlib.sha256(raw).hexdigest(),
        "review_sha256":hashlib.sha256(Path(a.review_file).read_bytes()).hexdigest() if a.review_file else None,
        "summary":summarize(results),"records":results,
        "limitations":["No actual VM output content is available from v0.5.26 routing simulation",
          "Human decisions must be explicitly supplied; never inferred from ground truth",
          "APPROVE records user confirmation, not objective factual correctness",
          "RETRY_REQUESTED is a handoff state; v0.5.29 does not execute another VM",
          "No real UI, transactions, side effects, or real VM integration"]}
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output["summary"],ensure_ascii=False,indent=2));print("Saved:",dest)
if __name__=="__main__":main()
