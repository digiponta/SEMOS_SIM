"""SEMOS_SIM v0.7.13: deduplicated MVCC heads and convergence controls.
All nodes are logical replicas; this is not a distributed consensus algorithm.
"""
import argparse,json
from pathlib import Path
MODES=("DAG_MVCC_RESOLVE","SEMANTIC_MVCC_RESOLVE")
POLICIES=("multi_value","deterministic","merge")
def dominant(a,b):
 return all(x>=y for x,y in zip(a,b)) and a!=b
def dedup(items):
 return {tuple(x["clock"]):x for x in items}
def heads(items):
 unique=list(dedup(items).values())
 return sorted((x for x in unique if not any(dominant(y["clock"],x["clock"]) for y in unique)),key=lambda x:x["clock"])
def resolve(items,policy):
 h=heads(items)
 if policy=="multi_value":return tuple(sorted(x["value"] for x in h))
 if policy=="deterministic":return max(h,key=lambda x:(x["clock"],x["value"]))["value"]
 if policy=="merge":return "MERGE:"+",".join(sorted(x["value"] for x in h))
 raise ValueError("unknown policy")
def experiment(mode="DAG_MVCC_RESOLVE",policy="multi_value",delay=2,semantic_cost=.1,
               message_cost=.3,merge_cost=.5):
 if mode not in MODES or policy not in POLICIES or min(delay,semantic_cost,message_cost,merge_cost)<0:
  raise ValueError("invalid parameter")
 initial={"clock":(0,0,0),"value":"initial"}
 alpha={"clock":(1,0,0),"value":"alpha"}
 beta={"clock":(0,1,0),"value":"beta"}
 replicas=[[initial,alpha],[initial,beta],[initial]]
 packets=[(1+delay,2,alpha),(1+delay,2,beta),
          (1+delay,0,beta),(1+delay,1,alpha)]
 reads=[];messages=4;cost=messages*message_cost
 for tick in (2,3,4,5):
  arrived=[p for p in packets if p[0]<=tick]
  packets=[p for p in packets if p[0]>tick]
  for _,vm,v in arrived:replicas[vm].append(v)
  for vm in range(3):
   h=heads(replicas[vm])
   reads.append({"tick":tick,"vm":vm,"head_count":len(h),
                 "result":resolve(replicas[vm],policy)})
   if mode=="SEMANTIC_MVCC_RESOLVE":cost+=semantic_cost
   if policy=="merge" and len(h)>1:cost+=merge_cost
 # Explicit anti-entropy exchanges all unique versions. There is no central truth lookup.
 for sender in range(3):
  for receiver in range(3):
   if sender!=receiver:
    replicas[receiver].extend(list(dedup(replicas[sender]).values()))
    cost+=message_cost;messages+=1
 final_heads=[heads(replica) for replica in replicas]
 decisions=[resolve(replica,policy) for replica in replicas]
 # Dedup corrects v0.7.12 repeated replication entries being counted as heads.
 return {"mode":mode,"policy":policy,"read_count":len(reads),
         "initial_unique_conflict_heads":2,
         "final_unique_head_counts":[len(x) for x in final_heads],
         "final_values":decisions,
         "converged":all(x==decisions[0] for x in decisions),
         "unresolved_concurrent_heads":len(final_heads[0]) if len(final_heads[0])>1 else 0,
         "messages":messages,"aggregate_cost":round(cost,6),"reads":reads}
def compare(policy="multi_value",delay=2,semantic_cost=.1,message_cost=.3):
 a,b=[experiment(m,policy,delay,semantic_cost,message_cost) for m in MODES]
 return {"version":"0.7.13","kind":"SYNTHETIC_MVCC_CONVERGENCE",
         "parameters":{"policy":policy,"delay":delay,"semantic_cost":semantic_cost,"message_cost":message_cost},
         "results":[a,b],
         "matched":{"same_convergence":a["converged"]==b["converged"],
                    "same_heads":a["final_unique_head_counts"]==b["final_unique_head_counts"],
                    "same_final_values":a["final_values"]==b["final_values"],
                    "semantic_extra_cost":round(b["aggregate_cost"]-a["aggregate_cost"],6)},
         "limitations":["Logical replicas only, no network partitions, durability, or crashes",
                        "Concurrent clocks known in the initial scenario; no semantic correctness oracle",
                        "Deterministic/merge output is a presentation policy, not a committed causal successor",
                        "Anti-entropy runs on a fixed schedule and counts each peer exchange as one message",
                        "Matching comparison gives DAG and Semantic modes identical conflict semantics"]}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--policy",choices=POLICIES,default="multi_value")
 p.add_argument("--delay",type=int,default=2)
 p.add_argument("--semantic-cost",type=float,default=.1)
 p.add_argument("--message-cost",type=float,default=.3)
 p.add_argument("--output",required=True)
 a=p.parse_args()
 r=compare(a.policy,a.delay,a.semantic_cost,a.message_cost)
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open("x",encoding="utf-8") as f:json.dump(r,f,ensure_ascii=False,indent=2)
 print("Wrote:",out)
 for x in r["results"]:
  print(x["mode"],"heads",x["final_unique_head_counts"],"converged",x["converged"],
        "conflicting_heads",x["unresolved_concurrent_heads"],"cost",x["aggregate_cost"])
if __name__=="__main__":main()
