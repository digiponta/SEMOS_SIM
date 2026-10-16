"""v0.5.24: non-side-effecting OR Gate + Recovery state-machine simulation.

IMPORTANT: simulated validation uses gold ONLY as an oracle for an
upper-bound recovery experiment. It is NOT a deployable semantic validator.
No real VMs, snapshots, rollback, or side effects are executed.
"""
import argparse,hashlib,json
from pathlib import Path

VMS=("VM-A","VM-B","VM-C")

def simulate(row, max_attempts=2):
    gold=row["gold"]
    initial=row["predicted"]
    candidate=row["candidate"]
    events=[]
    if not row["accepted"]:
        return {"request_id":row["request_id"],"gold":gold,"initial":initial,
                "final":"DISCOVERY","events":[{"state":"GATE_REJECT","vm":candidate},
                {"state":"DISCOVERY"}],"oracle_knowledge_used":False}
    if initial not in VMS:
        raise ValueError("Accepted input must nominate VM")
    # All operations stay in memory: no VM invocation, external I/O or commits.
    # Only a deterministic alternate route is simulated. No real runner-up
    # score is provided by v0.5.23 traces, so do not describe it as top-2.
    attempts=[candidate]+[v for v in VMS if v!=candidate]
    attempts=attempts[:max_attempts]
    for index,vm in enumerate(attempts):
        events.append({"state":"PROVISIONAL","vm":vm,"attempt":index+1})
        valid=(vm==gold)  # explicit omniscient oracle, not actual semantic checking
        events.append({"state":"ORACLE_VALIDATION","vm":vm,"ok":valid})
        if valid:
            events.append({"state":"SIMULATED_COMMIT","vm":vm})
            return {"request_id":row["request_id"],"gold":gold,"initial":initial,
                    "final":vm,"events":events,"oracle_knowledge_used":True}
        events.append({"state":"SIMULATED_ROLLBACK","vm":vm})
    events.append({"state":"DISCOVERY"})
    return {"request_id":row["request_id"],"gold":gold,"initial":initial,
            "final":"DISCOVERY","events":events,"oracle_knowledge_used":True}

def summarize(rows):
    known=[r for r in rows if r["gold"]!="UNKNOWN"]
    unknown=[r for r in rows if r["gold"]=="UNKNOWN"]
    return {"known_correct_final":sum(r["final"]==r["gold"] for r in known),
      "known_total":len(known),"unknown_discovery":sum(r["final"]=="DISCOVERY" for r in unknown),
      "unknown_total":len(unknown),
      "rollback_events":sum(sum(e["state"]=="SIMULATED_ROLLBACK" for e in r["events"]) for r in rows),
      "retry_events":sum(sum(e["state"]=="PROVISIONAL" for e in r["events"])>1 for r in rows),
      "provisional_accepted":sum(r["initial"]!="UNKNOWN" for r in rows),
      "final_discovery":sum(r["final"]=="DISCOVERY" for r in rows)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/and_or_gate_v0523.json")
    p.add_argument("--output",default="results/recovery_oracle_simulation_v0524.json")
    p.add_argument("--max-attempts",type=int,choices=(1,2,3),default=2)
    a=p.parse_args()
    out=Path(a.output)
    if out.exists():p.error("Refusing to overwrite output")
    raw=Path(a.input).read_bytes()
    doc=json.loads(raw)
    if doc.get("version")!="0.5.23" or doc.get("kind")!="EXPLORATORY_FROZEN_GATE_AND_OR_COMPARISON":
        p.error("v0.5.23 full trace required")
    trials=doc["traces"]["OR"]
    if len(trials)!=40 or len(set(x["request_id"] for x in trials))!=40:
        p.error("Expected 40 unique v0.5.23 OR traces")
    records=[simulate(row,a.max_attempts) for row in trials]
    result={"version":"0.5.24","kind":"ORACLE_UPPER_BOUND_RECOVERY_SIMULATION",
            "input_sha256":hashlib.sha256(raw).hexdigest(),
            "input_calibration_sha256":doc["calibration_sha256"],
            "input_evaluation_sha256":doc["evaluation_sha256"],
            "max_attempts":a.max_attempts,"summary":summarize(records),
            "records":records,
            "limitations":["Oracle validator reads gold labels: this is NOT realistic recovery accuracy",
            "The second VM is a fixed-order alternate, not the semantic runner-up",
            "All rollbacks and commits are simulated; no real VM or side-effect rollback",
            "Gate rejects are routed to discovery without attempted VM recovery",
            "Previously observed 40 synthetic examples: exploratory only",
            "UNKNOWN discovery is not equivalent to successful understanding",
            "No QHA 2 Copies in 3 resiliency test"]}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result["summary"],ensure_ascii=False,indent=2))
    print("Saved:",out)
if __name__=="__main__":main()
