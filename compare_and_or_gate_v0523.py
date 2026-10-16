"""v0.5.23 exploratory AND/OR gate comparison on frozen LLM_SEM scores.

No threshold fitting from evaluation examples. Do not use outcome to select
a model on this already exposed synthetic evaluation set.
"""
import argparse,bisect,json
from pathlib import Path
from evaluate_vm_calibration_v0522 import fit,load,measure,sha,validate_freeze
from compare_gate_variants_v056 import enrich

def evaluate_logic(eval_row,ecdf,quantile,margin,mode):
 candidate=eval_row["best_vm"]
 percentile=bisect.bisect_right(ecdf[candidate],eval_row["score"])/len(ecdf[candidate])
 e=percentile>=quantile
 m=eval_row["margin"]>=margin
 accepted=(e and m) if mode=="AND" else (e or m)
 cause=("both_pass" if e and m else "ecdf_only" if e else "margin_only" if m else "neither")
 return candidate if accepted else "UNKNOWN",{"request_id":eval_row["request_id"],"candidate":candidate,
  "score":eval_row["score"],"margin":eval_row["margin"],"ecdf":percentile,
  "ecdf_pass":e,"margin_pass":m,"cause":cause,"accepted":accepted}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--calibration",default="data/new_calibration.csv")
 p.add_argument("--evaluation",default="data/new_evaluation.csv")
 p.add_argument("--audit",default="results/calibration_split_audit_v0521.json")
 p.add_argument("--frozen",default="config/hybrid_gate_v053_frozen.json")
 p.add_argument("--output",default="results/and_or_gate_v0523.json")
 a=p.parse_args();out=Path(a.output)
 if out.exists():p.error("Refusing overwrite")
 aud=json.loads(Path(a.audit).read_text(encoding="utf-8-sig"))
 if aud.get("version")!="0.5.21" or not aud.get("automatic_pass"):p.error("v0.5.21 PASS audit required")
 if sha(a.calibration)!=aud["calibration"]["sha256"] or sha(a.evaluation)!=aud["evaluation"]["sha256"]:
  p.error("Calibration/evaluation SHA mismatch")
 frozen=json.loads(Path(a.frozen).read_text(encoding="utf-8-sig"))
 validate_freeze(frozen,sha(frozen["calibration_source"]))
 from llm_sem_adapter import LLMSemAdapter
 engine=LLMSemAdapter(model_path=frozen["model"])
 cal=load(a.calibration);ev=load(a.evaluation)
 cal_rep=enrich([{"text":r["text"],"label":r["gold"]} for r in cal],engine,frozen["weight"])
 ev_rep=enrich([{"text":r["text"],"label":r["gold"]} for r in ev],engine,frozen["weight"])
 ecdf=fit(cal_rep);q=.76;m=frozen["margin"]
 results={};traces={}
 for logic in ("AND","OR"):
  decisions=[evaluate_logic(dict(rep,request_id=row["request_id"]),ecdf,q,m,logic)
             for row,rep in zip(ev,ev_rep)]
  results[logic]=measure(ev,[pred for pred,trace in decisions])
  traces[logic]=[dict(trace,gold=row["gold"],predicted=pred)
                 for row,(pred,trace) in zip(ev,decisions)]
 global_dec=[r["best_vm"] if r["score"]>=frozen["threshold"] and r["margin"]>=m else "UNKNOWN" for r in ev_rep]
 results["global_frozen"]=measure(ev,global_dec)
 results["vector_only"]=measure(ev,[r["best_vm"] for r in ev_rep])
 cross={"known_correct_rescued":0,"known_wrong_newly_accepted":0,"unknown_newly_accepted":0}
 for row,at,ot in zip(ev,traces["AND"],traces["OR"]):
  if not at["accepted"] and ot["accepted"]:
   if row["gold"]=="UNKNOWN":cross["unknown_newly_accepted"]+=1
   elif ot["candidate"]==row["gold"]:cross["known_correct_rescued"]+=1
   else:cross["known_wrong_newly_accepted"]+=1
 payload={"version":"0.5.23","kind":"EXPLORATORY_FROZEN_GATE_AND_OR_COMPARISON",
   "calibration_sha256":sha(a.calibration),"evaluation_sha256":sha(a.evaluation),
   "audit_sha256":sha(a.audit),"frozen_sha256":sha(a.frozen),
   "fixed_rules":{"ecdf_threshold":q,"margin_threshold":m,
     "AND":"ecdf_pass and margin_pass","OR":"ecdf_pass or margin_pass"},
   "ecdf_candidate_counts":{k:len(v) for k,v in ecdf.items()},
   "results":results,"delta_and_to_or":cross,"traces":traces,
   "limitations":["These 40 evaluation samples have already been inspected at v0.5.22",
       "OR is an exploratory post hoc proposal and has no independent generalization claim",
       "Recovery Manager not implemented or tested",
       "No side-effecting execution performed; candidate routing is simulated"]}
 out.parent.mkdir(parents=True,exist_ok=True)
 out.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
 for k,v in results.items():
  print(k,{n:round(x["rate"],3) if x["rate"] is not None else None for n,x in v["metrics"].items()})
 print("OR minus AND:",cross,"Saved:",out)
if __name__=="__main__":main()
