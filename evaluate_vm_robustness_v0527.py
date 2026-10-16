"""v0.5.27: VM capability error-rate robustness sweep, synthetic only.

Retrospective 40 already inspected examples. All VM self checks use ground
truth to simulate controlled error rates; do not interpret as real reliability.
A deterministic hash per (scenario, replicate, request, VM) allows paired
comparisons. No rerun of LLM_SEM required.
"""
import argparse,csv,hashlib,json
from pathlib import Path
from simulate_user_rr_v0526 import simulate,metrics,approvals_read
from simulate_vm_aware_recovery_v0525 import VMS

def coin(seed,replicate,request_id,vm,channel):
    b=f"{seed}|{replicate}|{request_id}|{vm}|{channel}".encode()
    return int.from_bytes(hashlib.sha256(b).digest()[:8],"big")/2**64

def run(traces,approvals,false_accept,false_reject,seed,replicate,max_attempts):
    cursor=0;records=[]
    def check(vm,gold,rid):
        proper=vm==gold
        if proper:
            return "NOT_SUPPORTED" if coin(seed,replicate,rid,vm,"FR")<false_reject else "ACCEPTED"
        return "ACCEPTED" if coin(seed,replicate,rid,vm,"FA")<false_accept else "NOT_SUPPORTED"
    for row in traces:
        authorized=(not row["accepted"] and approvals.get(row["request_id"],False))
        start=cursor%len(VMS) if authorized else 0
        if authorized:cursor+=1
        records.append(simulate(row,approvals.get(row["request_id"],False),start,check,max_attempts))
    return metrics(records,traces)

def aggregate(items):
    keys=items[0].keys()
    return {k:{"mean":sum(r[k] for r in items)/len(items),
               "min":min(r[k] for r in items),"max":max(r[k] for r in items)}
            for k in keys}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/and_or_gate_v0523.json")
    p.add_argument("--approval-file",required=True)
    p.add_argument("--output",default="results/vm_capability_robustness_v0527.json")
    p.add_argument("--replicates",type=int,default=200)
    p.add_argument("--seed",type=int,default=527)
    p.add_argument("--max-attempts",type=int,choices=(1,2,3),default=3)
    a=p.parse_args()
    if a.replicates<1 or a.replicates>10000:p.error("replicates must be 1..10000")
    dst=Path(a.output)
    if dst.exists():p.error("Refusing overwrite")
    raw=Path(a.input).read_bytes();data=json.loads(raw)
    if data.get("version")!="0.5.23":p.error("Need v0.5.23 traces")
    traces=data["traces"]["OR"]
    ids=[r["request_id"] for r in traces]
    if len(traces)!=40 or len(set(ids))!=len(ids):p.error("Expected 40 distinct cases")
    approved=approvals_read(a.approval_file)
    if set(approved)-set(ids):p.error("Unknown request_id in approval file")
    scenarios=[(0.,0.),(.05,0.),(.10,0.),(.20,0.),
               (0.,.05),(0.,.10),(0.,.20),
               (.05,.05),(.10,.10),(.20,.20)]
    results=[]
    for fa,fr in scenarios:
        samples=[run(traces,approved,fa,fr,a.seed,i,a.max_attempts) for i in range(a.replicates)]
        means=aggregate(samples)
        results.append({"false_accept":fa,"false_reject":fr,"replicates":a.replicates,
            "metrics":means,
            "known_accuracy_mean":means["known_correct"]["mean"]/30,
            "unknown_discovery_rate_mean":means["unknown_discovery"]["mean"]/10,
            "known_wrong_commit_rate_mean":means["known_wrong_commit"]["mean"]/30,
            "unknown_false_commit_rate_mean":means["unknown_false_commit"]["mean"]/10})
        print(f"FA={fa:.0%},FR={fr:.0%}: known={means['known_correct']['mean']:.2f}/30 "
          f"wrong_commit={means['known_wrong_commit']['mean']:.2f}/30 "
          f"unknown_discovery={means['unknown_discovery']['mean']:.2f}/10 "
          f"probes={means['probe_attempts']['mean']:.2f}")
    output={"version":"0.5.27","kind":"SYNTHETIC_VM_CAPABILITY_ROBUSTNESS_SWEEP",
        "input_sha256":hashlib.sha256(raw).hexdigest(),
        "approval_sha256":hashlib.sha256(Path(a.approval_file).read_bytes()).hexdigest(),
        "replicates":a.replicates,"seed":a.seed,"max_attempts":a.max_attempts,
        "scenarios":results,
        "limitations":["Known labels used by synthetic capability simulator, not a deployed VM check",
          "Independent deterministic pseudo-random response events; real VM error correlations unknown",
          "Same previously exposed 40 cases, no independent evaluation",
          "Retry order for Gate-accepted requests remains fixed VM order",
          "Explicit approval CSV is offline simulated authorization, not interactive user consent",
          "Probe/commit is simulated, no side effects, real rollback, or QHA redundancy evaluation"]}
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",dst)
if __name__=="__main__":main()
