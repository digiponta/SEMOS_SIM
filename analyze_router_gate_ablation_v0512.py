"""SEMOS_SIM v0.5.12: offline ablation of router and unknown gate.
Reads only v0.5.11 replay trace; does not retrain or tune.
"""
import argparse,json
from pathlib import Path
from collections import Counter
LABELS=("VM-A","VM-B","VM-C")
def summarize(rows,key):
    known=[r for r in rows if r["gold"]!="UNKNOWN"]
    unknown=[r for r in rows if r["gold"]=="UNKNOWN"]
    pred=lambda r:r[key]
    correct=sum(pred(r)==r["gold"] for r in known)
    accepted=sum(pred(r)!="UNKNOWN" for r in known)
    false_accept=sum(pred(r)!="UNKNOWN" for r in unknown)
    return {"known_accuracy":correct/len(known),"known_correct":correct,
            "known_coverage":accepted/len(known),"known_accepted":accepted,
            "selective_accuracy":correct/accepted if accepted else None,
            "unknown_false_accept":false_accept/len(unknown),
            "unknown_false_accept_count":false_accept,
            "unknown_reject":1-false_accept/len(unknown)}
def analyze(trace):
    if trace.get("version")!="0.5.11" or not trace.get("reference_replay_exact_match"):
        raise ValueError("Verified v0.5.11 trace required")
    rows=trace["rows"]
    if not rows:raise ValueError("Empty trace")
    for r in rows:
        if r["candidate_vm"] not in LABELS or r["predicted"] not in LABELS+("UNKNOWN",):
            raise ValueError("Invalid routing destination")
        expected=r["candidate_vm"] if r["contrast_score"]>=r["guard_cutoff"] else "UNKNOWN"
        if expected!=r["predicted"]:raise ValueError("Trace is internally inconsistent")
    augmented=[dict(r,router_only=r["candidate_vm"]) for r in rows]
    failures={"candidate_wrong_accepted":[],"candidate_wrong_rejected":[],
              "candidate_right_rejected":[],"unknown_false_accepted":[]}
    per_vm={}
    for vm in LABELS:
        subset=[r for r in rows if r["gold"]==vm]
        right=sum(r["candidate_vm"]==vm for r in subset)
        right_held=sum(r["candidate_vm"]==vm and r["predicted"]=="UNKNOWN" for r in subset)
        wrong_held=sum(r["candidate_vm"]!=vm and r["predicted"]=="UNKNOWN" for r in subset)
        per_vm[vm]={"n":len(subset),"candidate_correct":right,
                    "candidate_accuracy":right/len(subset) if subset else None,
                    "candidate_right_rejected":right_held,
                    "candidate_wrong_rejected":wrong_held}
    for r in rows:
        if r["gold"]=="UNKNOWN":
            if r["predicted"]!="UNKNOWN":failures["unknown_false_accepted"].append(r["text"])
        elif r["candidate_vm"]!=r["gold"]:
            group="candidate_wrong_rejected" if r["predicted"]=="UNKNOWN" else "candidate_wrong_accepted"
            failures[group].append(r["text"])
        elif r["predicted"]=="UNKNOWN":
            failures["candidate_right_rejected"].append(r["text"])
    # Diagnostic oracle accepts a known correctly classified candidate and rejects
    # every UNKNOWN; not an executable model, only an upper-bound decomposition.
    oracle=[dict(r,oracle=r["candidate_vm"] if r["gold"]!="UNKNOWN" and r["candidate_vm"]==r["gold"] else "UNKNOWN") for r in rows]
    return {"version":"0.5.12","kind":"POST_HOC_ROUTER_GATE_ABLATION",
      "trace_verified":True,"n":len(rows),
      "router_only":summarize(augmented,"router_only"),
      "full_gate":summarize(rows,"predicted"),
      "oracle_upper_bound_not_deployable":summarize(oracle,"oracle"),
      "per_known_vm":per_vm,
      "failure_counts":{k:len(v) for k,v in failures.items()},
      "failure_texts":failures,
      "limitations":["Router-only always routes all UNKNOWN requests; this is a diagnostic ablation, not a deployable policy",
                     "Oracle uses ground-truth labels; it is not an executable model",
                     "All measurements reuse previously explored development data",
                     "No independent prospective benchmark or tuning performed",
                     "No LLM_SEM 2 Copies in 3 fault-tolerance test"]}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",default="results/nested_traces_v0511.json")
    p.add_argument("--output",default="results/router_gate_ablation_v0512.json")
    a=p.parse_args()
    if "holdout" in Path(a.input).name.lower():p.error("Holdout not permitted")
    report=analyze(json.loads(Path(a.input).read_text(encoding="utf-8-sig")))
    dest=Path(a.output)
    if dest.exists():p.error("Output already exists")
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    for key in ("router_only","full_gate","oracle_upper_bound_not_deployable"):print(key,report[key])
    print("Failures:",report["failure_counts"])
    print("Saved:",dest)
if __name__=="__main__":main()
