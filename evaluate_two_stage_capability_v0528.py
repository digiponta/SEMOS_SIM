"""v0.5.28 two-stage capability validation sensitivity experiment.

IMPORTANT: synthetic responder uses evaluation gold; correlation is modeled
through deterministic shared vs independent Bernoulli draws, not observed
real-world VM error dependence. No external effects or real VM checks.
"""
import argparse,hashlib,json
from pathlib import Path
from evaluate_vm_robustness_v0527 import coin,aggregate
from simulate_user_rr_v0526 import approvals_read,simulate,metrics
from simulate_vm_aware_recovery_v0525 import VMS

def stage_status(correct,rate,u):
    error=u<rate
    return "ACCEPTED" if (correct != error) else "NOT_SUPPORTED"

def evaluate(traces,approvals,fa,fr,mode,seed,replicate,max_attempts):
    if mode not in ("single","independent","shared","mixed"):raise ValueError("bad mode")
    counts={"stage1_accepted":0,"stage2_checked":0,"stage2_rejected":0,
            "stage2_false_accepted":0,"stage2_true_rejected":0}
    def responder(vm,gold,rid):
        correct=vm==gold
        rate=fr if correct else fa
        u1=coin(seed,replicate,rid,vm,"stage1")
        s1=stage_status(correct,rate,u1)
        if s1!="ACCEPTED":return "NOT_SUPPORTED"
        counts["stage1_accepted"]+=1
        if mode=="single":return "ACCEPTED"
        counts["stage2_checked"]+=1
        common=(mode=="shared" or (mode=="mixed" and coin(seed,replicate,rid,vm,"dependence")<.5))
        u2=u1 if common else coin(seed,replicate,rid,vm,"stage2")
        s2=stage_status(correct,rate,u2)
        if s2=="NOT_SUPPORTED":
            counts["stage2_rejected"]+=1
            if correct:counts["stage2_true_rejected"]+=1
        elif not correct:counts["stage2_false_accepted"]+=1
        return s2
    rr=0;records=[]
    for t in traces:
        authorized=(not t["accepted"] and approvals.get(t["request_id"],False))
        offset=rr%len(VMS) if authorized else 0
        if authorized:rr+=1
        records.append(simulate(t,approvals.get(t["request_id"],False),offset,responder,max_attempts))
    return dict(metrics(records,traces),**counts)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/and_or_gate_v0523.json")
    p.add_argument("--approval-file",required=True)
    p.add_argument("--output",default="results/two_stage_capability_v0528.json")
    p.add_argument("--replicates",type=int,default=200)
    p.add_argument("--seed",type=int,default=528)
    p.add_argument("--max-attempts",type=int,choices=(1,2,3),default=3)
    a=p.parse_args()
    if not 1<=a.replicates<=10000:p.error("replicates range 1..10000")
    dst=Path(a.output)
    if dst.exists():p.error("Refusing overwrite")
    raw=Path(a.input).read_bytes()
    d=json.loads(raw)
    if d.get("version")!="0.5.23":p.error("Require v0.5.23 trace")
    traces=d["traces"]["OR"]
    ids=[t["request_id"] for t in traces]
    if len(traces)!=40 or len(set(ids))!=40:p.error("Require 40 unique traces")
    approvals=approvals_read(a.approval_file)
    if set(approvals)-set(ids):p.error("Unknown approval ID")
    results=[]
    for fa,fr in ((0.,0.),(.05,.05),(.10,.10),(.20,.20),(.10,0.),(0.,.10)):
        for mode in ("single","independent","mixed","shared"):
            raw_metrics=[evaluate(traces,approvals,fa,fr,mode,a.seed,n,a.max_attempts)
                         for n in range(a.replicates)]
            agg=aggregate(raw_metrics)
            entry={"fa":fa,"fr":fr,"mode":mode,
                   "known_accuracy":agg["known_correct"]["mean"]/30,
                   "known_wrong_commit_rate":agg["known_wrong_commit"]["mean"]/30,
                   "unknown_discovery_rate":agg["unknown_discovery"]["mean"]/10,
                   "unknown_false_commit_rate":agg["unknown_false_commit"]["mean"]/10,
                   "averages":{k:v["mean"] for k,v in agg.items()}}
            results.append(entry)
            print(f"FA={fa:.0%} FR={fr:.0%} {mode:11s} known={entry['known_accuracy']:.3f}"
                  f" unknown_reject={entry['unknown_discovery_rate']:.3f}"
                  f" wrong_known={entry['known_wrong_commit_rate']:.3f}"
                  f" stage2_checks={agg['stage2_checked']['mean']:.2f}")
    output={"version":"0.5.28","kind":"SYNTHETIC_TWO_STAGE_CAPABILITY_VALIDATION",
     "input_sha256":hashlib.sha256(raw).hexdigest(),
     "approval_sha256":hashlib.sha256(Path(a.approval_file).read_bytes()).hexdigest(),
     "replicates":a.replicates,"seed":a.seed,"max_attempts":a.max_attempts,
     "correlation_models":{"single":"first stage only",
       "independent":"stage 2 independently sampled",
       "mixed":"50% shared stage 1 draw per VM/check, otherwise independent stage 2",
       "shared":"identical draw across stages (perfect event correlation)"},
     "scenarios":results,
     "limitations":["Synthetic responder uses gold (oracle) to emulate capability errors",
       "Correlation configurations are hypothetical not measured from VMs",
       "This is repeated simulation on previously observed synthetic examples",
       "Both stages use the same per-stage FA/FR rates; the rate of errors after both stages depends on correlation",
       "Second-stage failure returns NOT_SUPPORTED and may cause loss of valid requests",
       "No real VM activity, transaction semantics or side effects",
       "No live interactive approval or real LLM_SEM runner-up ranking"]}
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Saved:",dst)
if __name__=="__main__":main()
