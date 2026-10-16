"""v0.5.25 VM-aware recovery protocol, simulation only.

The VM capability responder is a synthetic oracle with configurable false
accept / false reject rates. It does NOT implement real VM understanding.
Real ranked runner-up scores are unavailable in v0.5.23 output. Retrying
remaining VMs is therefore marked fallback enumeration, not semantic ranking.
"""
import argparse,hashlib,json
from pathlib import Path
VMS=("VM-A","VM-B","VM-C")

def response(vm,gold,request_id,false_accept=0.0,false_reject=0.0):
    # Deterministic coin for repeatable simulations; gold is accessed only by
    # synthetic responder, never by dispatcher.
    digest=hashlib.sha256((request_id+"|"+vm).encode()).digest()
    u=int.from_bytes(digest[:8],"big")/2**64
    capable=(vm==gold)
    claimed = (u>=false_reject) if capable else (u<false_accept)
    return "ACCEPTED" if claimed else "NOT_SUPPORTED"

def dispatch(trace,responder=response,max_attempts=3):
    if max_attempts not in (1,2,3):raise ValueError("attempt budget 1..3")
    if not trace["accepted"]:
        return {"request_id":trace["request_id"],"initial":"UNKNOWN",
          "final":"DISCOVERY","events":[{"state":"GATE_REJECT"},{"state":"DISCOVERY"}]}
    first=trace["candidate"]
    if first not in VMS:raise ValueError("Invalid candidate")
    # Neither per-VM score vectors nor top-2 ordering exist in v0.5.23.
    # Explicitly designate alphabetical fallback ordering.
    candidates=[first]+[v for v in VMS if v!=first]
    events=[];final="DISCOVERY"
    for index,vm in enumerate(candidates[:max_attempts],1):
        events.append({"state":"DISPATCH","vm":vm,"attempt":index})
        status=responder(vm,trace["gold"],trace["request_id"])
        events.append({"state":"VM_RESPONSE","vm":vm,"status":status})
        if status=="ACCEPTED":
            events.append({"state":"SIMULATED_COMPLETED","vm":vm})
            final=vm
            break
        if status!="NOT_SUPPORTED":raise ValueError("unsupported VM response")
    if final=="DISCOVERY":events.append({"state":"DISCOVERY"})
    return {"request_id":trace["request_id"],"initial":first,
            "final":final,"events":events,
            "retry_count":sum(x["state"]=="DISPATCH" for x in events)-1}

def summarize(records,traces):
    lookup={r["request_id"]:r for r in traces}
    known=[r for r in records if lookup[r["request_id"]]["gold"]!="UNKNOWN"]
    unknown=[r for r in records if lookup[r["request_id"]]["gold"]=="UNKNOWN"]
    statuses=[(r,lookup[r["request_id"]]["gold"]) for r in records]
    return {"known_correct":sum(r["final"]==g for r,g in statuses if g!="UNKNOWN"),
      "known_total":len(known),"known_wrong_commit":sum(r["final"] in VMS and r["final"]!=g for r,g in statuses if g!="UNKNOWN"),
      "known_discovery":sum(r["final"]=="DISCOVERY" for r in known),
      "unknown_discovery":sum(r["final"]=="DISCOVERY" for r in unknown),
      "unknown_total":len(unknown),
      "unknown_false_commit":sum(r["final"] in VMS for r in unknown),
      "retry_requests":sum(r["retry_count"]>0 for r in records),
      "dispatch_attempts":sum(sum(e["state"]=="DISPATCH" for e in r["events"]) for r in records)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/and_or_gate_v0523.json")
    p.add_argument("--output",default="results/vm_aware_recovery_v0525.json")
    p.add_argument("--false-accept",type=float,default=0.0)
    p.add_argument("--false-reject",type=float,default=0.0)
    p.add_argument("--max-attempts",type=int,choices=(1,2,3),default=3)
    a=p.parse_args()
    if not 0<=a.false_accept<=1 or not 0<=a.false_reject<=1:p.error("error rates must be 0..1")
    o=Path(a.output)
    if o.exists():p.error("Refusing overwrite")
    raw=Path(a.input).read_bytes();doc=json.loads(raw)
    if doc.get("version")!="0.5.23":p.error("v0.5.23 input required")
    traces=doc["traces"]["OR"]
    if len(traces)!=40:p.error("expected 40 trace cases")
    def vm_responder(vm,gold,request_id):
        return response(vm,gold,request_id,a.false_accept,a.false_reject)
    records=[dispatch(t,vm_responder,a.max_attempts) for t in traces]
    out={"version":"0.5.25","kind":"SYNTHETIC_VM_SELF_REJECTION_SIMULATION",
      "input_sha256":hashlib.sha256(raw).hexdigest(),
      "input_calibration_sha256":doc["calibration_sha256"],
      "input_evaluation_sha256":doc["evaluation_sha256"],
      "config":{"false_accept":a.false_accept,"false_reject":a.false_reject,
                "max_attempts":a.max_attempts,
                "retry_order":"candidate_first_then_fixed_VM_order"},
      "summary":summarize(records,traces),"records":records,
      "limitations":["Synthetic VM checks have privileged access to gold label; they are not deployable validators",
        "Zero error rates represent idealized self-rejection only",
        "No actual runner-up scores available; retry is fixed-order enumeration, NOT real LLM_SEM ranking",
        "No VM executions, actual rollbacks, state restoration or irreversible side effects",
        "Discovery is a routing destination, not proof of successful task handling",
        "Previously inspected synthetic cases; no independent benchmark",
        "QHA 2 Copies in 3 not evaluated"]}
    o.parent.mkdir(parents=True,exist_ok=True)
    o.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(out["summary"],ensure_ascii=False,indent=2));print("Saved:",o)
if __name__=="__main__":main()
