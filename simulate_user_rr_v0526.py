"""v0.5.26 user-authorized round-robin capability probes (simulation).

No user approvals are fabricated: an explicit --approval-file CSV supplies
request_id,approved (true/false). With no record, denied by default.
VM self-check is synthetic and reads gold; it is not a real capability VM.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from simulate_vm_aware_recovery_v0525 import VMS,response,dispatch

def approvals_read(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if not {"request_id","approved"}.issubset(reader.fieldnames or []):
            raise ValueError("approval file needs request_id,approved")
        result={}
        for row in reader:
            key=row["request_id"].strip(); val=row["approved"].strip().lower()
            if not key or key in result or val not in ("true","false"):
                raise ValueError("invalid or duplicate approval")
            result[key]=(val=="true")
    return result

def simulate(trace,approved,rr_start,responder,max_attempts=3):
    if trace["accepted"]:
        result=dispatch(trace,responder,max_attempts)
        result["authorization"]="OR_GATE_ACCEPTED"
        return result
    rid=trace["request_id"]
    if not approved:
        return {"request_id":rid,"initial":"UNKNOWN","final":"DISCOVERY",
                "events":[{"state":"USER_PROBE_NOT_AUTHORIZED"},{"state":"DISCOVERY"}],
                "retry_count":0,"authorization":"DENIED_OR_UNSPECIFIED"}
    events=[{"state":"USER_PROBE_AUTHORIZED"}]
    order=[VMS[(rr_start+i)%len(VMS)] for i in range(len(VMS))]
    final="DISCOVERY"
    for i,vm in enumerate(order[:max_attempts],1):
        events.append({"state":"CAPABILITY_PROBE","vm":vm,"attempt":i})
        reply=responder(vm,trace["gold"],rid)
        events.append({"state":"VM_RESPONSE","vm":vm,"status":reply})
        if reply=="ACCEPTED":
            final=vm
            events.append({"state":"SIMULATED_COMPLETED","vm":vm})
            break
        if reply!="NOT_SUPPORTED":raise ValueError("invalid VM reply")
    if final=="DISCOVERY":events.append({"state":"DISCOVERY"})
    return {"request_id":rid,"initial":"UNKNOWN","final":final,
            "events":events,"retry_count":sum(e["state"]=="CAPABILITY_PROBE" for e in events)-1,
            "authorization":"EXPLICIT_APPROVAL"}

def metrics(records,traces):
    gold={r["request_id"]:r["gold"] for r in traces}
    known=[r for r in records if gold[r["request_id"]]!="UNKNOWN"]
    unknown=[r for r in records if gold[r["request_id"]]=="UNKNOWN"]
    returned=[r for r in records if r["authorization"]=="EXPLICIT_APPROVAL"]
    return {"known_correct":sum(r["final"]==gold[r["request_id"]] for r in known),
      "known_total":len(known),"known_discovery":sum(r["final"]=="DISCOVERY" for r in known),
      "known_wrong_commit":sum(r["final"] in VMS and r["final"]!=gold[r["request_id"]] for r in known),
      "unknown_discovery":sum(r["final"]=="DISCOVERY" for r in unknown),
      "unknown_total":len(unknown),
      "unknown_false_commit":sum(r["final"] in VMS for r in unknown),
      "authorized_probe_requests":len(returned),
      "unauthorized_gate_rejections":sum(r["authorization"]=="DENIED_OR_UNSPECIFIED" for r in records),
      "probe_attempts":sum(sum(e["state"]=="CAPABILITY_PROBE" for e in r["events"]) for r in records),
      "retry_requests":sum(r["retry_count"]>0 for r in records)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/and_or_gate_v0523.json")
    p.add_argument("--approval-file",required=True)
    p.add_argument("--output",default="results/user_authorized_rr_v0526.json")
    p.add_argument("--false-accept",type=float,default=0)
    p.add_argument("--false-reject",type=float,default=0)
    p.add_argument("--max-attempts",type=int,choices=(1,2,3),default=3)
    a=p.parse_args()
    if not 0<=a.false_accept<=1 or not 0<=a.false_reject<=1:p.error("false accept/reject must be 0..1")
    out=Path(a.output)
    if out.exists():p.error("Refusing overwrite")
    raw=Path(a.input).read_bytes();doc=json.loads(raw)
    if doc.get("version")!="0.5.23":p.error("v0.5.23 input required")
    traces=doc["traces"]["OR"]
    allow=approvals_read(a.approval_file)
    ids=[r["request_id"] for r in traces]
    if len(ids)!=len(set(ids)) or set(allow)-set(ids):p.error("Duplicate trace or unknown approval ID")
    def responder(vm,gold,request_id):
        return response(vm,gold,request_id,a.false_accept,a.false_reject)
    cursor=0;records=[]
    for row in traces:
        if not row["accepted"] and allow.get(row["request_id"],False):
            # Rotate start ONLY on authorized probe requests, not all traffic.
            start=cursor%len(VMS);cursor+=1
        else:start=0
        records.append(simulate(row,allow.get(row["request_id"],False),start,responder,a.max_attempts))
    obj={"version":"0.5.26","kind":"USER_AUTHORIZED_ROUND_ROBIN_SIMULATION",
         "input_sha256":hashlib.sha256(raw).hexdigest(),
         "approval_sha256":hashlib.sha256(Path(a.approval_file).read_bytes()).hexdigest(),
         "parameters":{"max_attempts":a.max_attempts,"false_accept":a.false_accept,
                       "false_reject":a.false_reject,
                       "missing_approval_policy":"DENY",
                       "rr_rotation":"per explicitly authorized gate rejection"},
         "summary":metrics(records,traces),"records":records,
         "limitations":["Explicit approval file is an offline test artifact, not UI consent",
                        "VM capability responses are synthetic gold-aware oracles",
                        "Wrong accepts are not actually rolled back",
                        "No real VM execution, side effects, rank-based retry or QHA 2 Copies in 3 test",
                        "Previously observed synthetic examples; not independent validation"]}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(obj["summary"],ensure_ascii=False,indent=2));print("Saved:",out)
if __name__=="__main__":main()
