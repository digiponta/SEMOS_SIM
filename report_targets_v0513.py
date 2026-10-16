"""v0.5.13: target-aware report from frozen v0.5.12 diagnostic.

Goals are provisional engineering targets, not statistical expectations.
Never tunes routing thresholds or accesses the independent holdout.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from math import sqrt

GOALS={
 "router_accuracy":(90.0,"min"),
 "known_accuracy":(70.0,"min"),
 "known_coverage":(80.0,"min"),
 "selective_accuracy":(90.0,"min"),
 "unknown_reject":(95.0,"min"),
 "unknown_false_accept":(5.0,"max")}
def wilson(success,n,z=1.96):
 if n<=0:return None
 p=success/n;d=1+z*z/n;c=(p+z*z/(2*n))/d
 h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return [100*(c-h),100*(c+h)]
def report(data):
 if data.get("version")!="0.5.12" or data.get("kind")!="POST_HOC_ROUTER_GATE_ABLATION":
  raise ValueError("v0.5.12 diagnostic JSON required")
 if not data.get("trace_verified"):raise ValueError("Unverified trace")
 router=data["router_only"]; gate=data["full_gate"]
 known_n=round(router["known_correct"]/router["known_accuracy"])
 unknown_n=round(gate["unknown_false_accept_count"]/gate["unknown_false_accept"]) if gate["unknown_false_accept"] else data["n"]-known_n
 if known_n+unknown_n!=data["n"]:raise ValueError("Inconsistent denominators")
 actual={"router_accuracy":100*router["known_accuracy"],
 "known_accuracy":100*gate["known_accuracy"],
 "known_coverage":100*gate["known_coverage"],
 "selective_accuracy":100*gate["selective_accuracy"],
 "unknown_reject":100*gate["unknown_reject"],
 "unknown_false_accept":100*gate["unknown_false_accept"]}
 intervals={
 "router_accuracy":wilson(router["known_correct"],known_n),
 "known_accuracy":wilson(gate["known_correct"],known_n),
 "known_coverage":wilson(gate["known_accepted"],known_n),
 "selective_accuracy":wilson(gate["known_correct"],gate["known_accepted"]),
 "unknown_reject":wilson(unknown_n-gate["unknown_false_accept_count"],unknown_n),
 "unknown_false_accept":wilson(gate["unknown_false_accept_count"],unknown_n)}
 metrics=[]
 for key,(goal,direction) in GOALS.items():
  value=actual[key]
  gap=value-goal if direction=="min" else goal-value
  metrics.append({"metric":key,"actual_percent":round(value,3),
   "target_percent":goal,"target_kind":"PROVISIONAL_ENGINEERING_GOAL",
   "direction":direction,"gap_in_favorable_direction_pp":round(gap,3),
   "point_estimate_meets_target":gap>=-1e-8,
   "wilson95_percent":intervals[key]})
 return {"version":"0.5.13","kind":"TARGET_AWARE_DIAGNOSTIC_REPORT",
         "source":"v0.5.12_exploratory_development_ablation",
         "n_total":data["n"],"n_known":known_n,"n_unknown":unknown_n,
         "metrics":metrics,
         "limitations":["Targets are provisional design goals, not expected values from a probability model",
                        "A point-estimate goal pass does not imply the Wilson 95% confidence bound passes",
                        "Small development sample; previously used for design decisions",
                        "Router-only is not deployable (all unknown cases routed)",
                        "No retuning, new benchmark, or 2 Copies in 3 evaluation"]}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--input",default="results/router_gate_ablation_v0512.json")
 p.add_argument("--output",default="results/target_report_v0513.json")
 a=p.parse_args()
 if "holdout" in Path(a.input).name.lower():p.error("Holdout prohibited")
 src=json.loads(Path(a.input).read_text(encoding="utf-8-sig"))
 out=Path(a.output)
 if out.exists():p.error("Refusing overwrite")
 result=report(src);out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
 for r in result["metrics"]:
  print(f'{r["metric"]:22} actual={r["actual_percent"]:6.2f}% target={r["target_percent"]:5.1f}% gap={r["gap_in_favorable_direction_pp"]:+6.2f}pp 95%CI={r["wilson95_percent"]}')
 print("Saved:",out)
if __name__=="__main__":main()
