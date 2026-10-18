"""SEMOS_SIM v0.7.6: reproducible multi-seed resilience sensitivity study.

Uses the unchanged v0.7.5 synthetic three-worker simulator.
This is NOT real VM performance, a confidence guarantee, or a causal
estimate from measured deployments.
"""
import argparse
import json
import math
import statistics
from pathlib import Path

from distributed_resilience_v075 import compare

METRICS=("aggregate_cost","makespan","reused","stale_reuse")
MODES=("TASK","NORMALIZED_CACHE","SEMANTIC_SPU")


def describe(values):
    n=len(values)
    if not n:
        raise ValueError("empty sample")
    mean=statistics.mean(values)
    sd=statistics.stdev(values) if n>1 else 0.0
    # Descriptive 1.96*SE interval, not a formal small-sample/t-based CI.
    margin=1.96*sd/math.sqrt(n)
    return {"n":n,"mean":round(mean,6),"sample_sd":round(sd,6),
            "min":round(min(values),6),"max":round(max(values),6),
            "normal_approx_95_interval":[round(mean-margin,6),round(mean+margin,6)]}


def scenario(name,overrides):
    return {"name":name,"overrides":overrides}


def scenarios():
    out=[scenario("REFERENCE",{})]
    for rate in (0.0,0.1,0.3):
        out.append(scenario("FAILURE_"+str(rate),{"failure_rate":rate}))
    for value in (0.0,0.05,0.5):
        out.append(scenario("SYNC_"+str(value),{"sync_cost":value}))
    for value in (0.0,0.1,0.5):
        out.append(scenario("SEMANTIC_OVERHEAD_"+str(value),{"semantic_overhead":value}))
    for period in (10,30,120):
        out.append(scenario("UPDATE_PERIOD_"+str(period),{"update_period":period}))
    for coverage in (0.0,0.5,1.0):
        out.append(scenario("NORMALIZATION_"+str(coverage),{"normalized_coverage":coverage}))
    return out


def run_study(seed_count=20,seed_start=42,requests=120):
    if seed_count<2 or requests<1:
        raise ValueError("seed_count must be >=2, requests >=1")
    defaults={"count":requests,"duplicate_fraction":0.4,"update_period":30,
              "failure_rate":0.1,"network_latency":0.5,"sync_cost":0.05,
              "retry_cost":0.5,"semantic_overhead":0.1,"lookup_cost":0.02,
              "normalized_coverage":0.5}
    reports=[]
    for sc in scenarios():
        runs=[]
        for seed in range(seed_start,seed_start+seed_count):
            c=compare(**(defaults|sc["overrides"]),seed=seed)
            by_mode={r["mode"]:r for r in c["results"]}
            task=by_mode["TASK"]
            norm=by_mode["NORMALIZED_CACHE"]
            sem=by_mode["SEMANTIC_SPU"]
            runs.append({
                "seed":seed,
                "by_mode":{mode:{m:by_mode[mode][m] for m in METRICS} for mode in MODES},
                "spu_vs_task_cost_saving":1-sem["aggregate_cost"]/task["aggregate_cost"],
                "spu_vs_normalized_cost_saving":1-sem["aggregate_cost"]/norm["aggregate_cost"],
                "spu_vs_task_makespan_saving":1-sem["makespan"]/task["makespan"],
                "spu_vs_normalized_makespan_saving":1-sem["makespan"]/norm["makespan"],
                "normalization_vs_task_cost_saving":1-norm["aggregate_cost"]/task["aggregate_cost"]
            })
        fields=("spu_vs_task_cost_saving","spu_vs_normalized_cost_saving",
                "spu_vs_task_makespan_saving","spu_vs_normalized_makespan_saving",
                "normalization_vs_task_cost_saving")
        summary={f:describe([r[f] for r in runs]) for f in fields}
        summary["positive_spu_vs_normalized_count"]=sum(
            x["spu_vs_normalized_cost_saving"]>0 for x in runs)
        summary["zero_stale_reuse_all"]=all(
            x["by_mode"][mode]["stale_reuse"]==0
            for x in runs for mode in MODES)
        reports.append({"scenario":sc["name"],"overrides":sc["overrides"],
                        "summary":summary,"runs":runs})
    return {
        "version":"0.7.6","kind":"SYNTHETIC_MULTI_SEED_ABLATION",
        "baseline_parameters":defaults,"seed_start":seed_start,"seed_count":seed_count,
        "scenarios":reports,
        "limitations":[
            "Synthetic, oracle-supplied canonical identity and 3 logical workers only",
            "All results use identical v0.7.5 implementation; no real VMs or timing",
            "Scenarios are one-factor-at-a-time relative to REFERENCE, not full factorial",
            "The normal-approximation 95% interval is descriptive, not a rigorous CI",
            "Seed repeats do not establish production generalization",
            "No actual replica lag, correlated failures, NLP error or data races",
            "Update-period version gate changes how many requests can be reused",
            "Semantic-overhead=0 is a cost ablation, not SPU-disable ablation"]}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed-count",type=int,default=20)
    p.add_argument("--seed-start",type=int,default=42)
    p.add_argument("--requests",type=int,default=120)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    data=run_study(a.seed_count,a.seed_start,a.requests)
    dest=Path(a.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("x",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    print("Wrote:",dest)
    print("Scenarios:",len(data["scenarios"]),
          "Runs:",len(data["scenarios"])*data["seed_count"])
    for sc in data["scenarios"]:
        r=sc["summary"]["spu_vs_normalized_cost_saving"]
        print(f'{sc["scenario"]:<30} mean={r["mean"]:+.4f} '
              f'sd={r["sample_sd"]:.4f} '
              f'positive={sc["summary"]["positive_spu_vs_normalized_count"]}/{a.seed_count}')


if __name__=="__main__":
    main()
