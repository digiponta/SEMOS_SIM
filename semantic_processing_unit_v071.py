"""SEMOS_SIM v0.7.1: deterministic Semantic Processing Unit simulation.

This is a synthetic, single-process logical simulation, not a distributed runtime.
Equivalence uses explicitly supplied canonical IDs (oracle), NOT vector similarity.
"""
from dataclasses import dataclass, field
from hashlib import sha256
import json

STATES=("PENDING","RUNNING","COMPLETED","FAILED")

def stable_key(value):
    return sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class SemanticUnit:
    semantic_id: str
    canonical_meaning: dict
    context: dict = field(default_factory=dict)
    version: int = 1
    def __post_init__(self):
        if not self.semantic_id or not isinstance(self.canonical_meaning,dict) or self.version<1:
            raise ValueError("Invalid Semantic Unit")

@dataclass(frozen=True)
class ProcessingRequest:
    request_id: str
    unit: SemanticUnit
    operation: str
    dependencies: tuple = ()
    parameters: dict = field(default_factory=dict)
    cost: float = 1.0
    def __post_init__(self):
        if not self.request_id or not self.operation or self.cost<0:
            raise ValueError("Invalid processing request")
    def execution_key(self):
        return stable_key({"meaning":self.unit.canonical_meaning,
                           "context":self.unit.context,"version":self.unit.version,
                           "operation":self.operation,"parameters":self.parameters})

class SPUSimulator:
    """Topological, deterministic simulation with explicitly trusted equivalence.

    Each request has its own execution record; equal keys may reuse a completed
    result only after its dependencies have completed. No wall-clock timing,
    network, GPU, truth assessment, or human approval is simulated.
    """
    def run(self,requests):
        by_id={r.request_id:r for r in requests}
        if len(by_id)!=len(requests):raise ValueError("Duplicate request_id")
        for r in requests:
            if len(r.dependencies)!=len(set(r.dependencies)):raise ValueError("Duplicate dependencies")
            if r.request_id in r.dependencies:raise ValueError("Self dependency")
            if any(d not in by_id for d in r.dependencies):raise ValueError("Missing dependency")
        records={};cache={};pending=set(by_id)
        executed=0;reused=0;work_cost=0.0
        while pending:
            ready=sorted(rid for rid in pending if all(d in records for d in by_id[rid].dependencies))
            if not ready:raise ValueError("Cyclic dependencies")
            for rid in ready:
                r=by_id[rid]
                # The dependency signature is essential to prevent reusing
                # an operation whose upstream inputs changed.
                upstream=[(d,records[d]["result_key"]) for d in sorted(r.dependencies)]
                cache_key=stable_key({"execution_key":r.execution_key(),"upstream":upstream})
                if cache_key in cache:
                    result_key=cache[cache_key];reused+=1;action="REUSED"
                else:
                    result_key=stable_key({"cache_key":cache_key,"result":"synthetic"})
                    cache[cache_key]=result_key
                    executed+=1;work_cost+=r.cost;action="EXECUTED"
                records[rid]={"state":"COMPLETED","action":action,
                              "semantic_id":r.unit.semantic_id,
                              "result_key":result_key,"execution_key":r.execution_key(),
                              "dependencies":list(r.dependencies)}
                pending.remove(rid)
        return {"version":"0.7.1","simulation":"SYNTHETIC_ORACLE_EQUIVALENCE",
                "requests":len(requests),"executed":executed,"reused":reused,
                "work_cost":work_cost,"records":records,
                "limitations":["Canonical meanings and equality are supplied by the fixture",
                               "No distributed execution, wall-clock benchmark or semantic recognition",
                               "No knowledge promotion or truth verification"]}

def sample_requests():
    a={"subject":"量子力学","predicate":"describes","object":"微視的物理現象"}
    b={"subject":"数学","predicate":"studies","object":"構造"}
    return [
       ProcessingRequest("R1",SemanticUnit("SEM-A",a),"EVALUATE",cost=3.0),
       ProcessingRequest("R2",SemanticUnit("SEM-A-PARAPHRASE",a),"EVALUATE",cost=3.0),
       ProcessingRequest("R3",SemanticUnit("SEM-B",b),"EVALUATE",("R1",),cost=2.0),
       ProcessingRequest("R4",SemanticUnit("SEM-A",a),"EXPLAIN",cost=4.0),
    ]

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--output",help="Create-only JSON report path")
    a=p.parse_args()
    report=SPUSimulator().run(sample_requests())
    data=json.dumps(report,ensure_ascii=False,indent=2)
    if a.output:
        from pathlib import Path
        path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("x",encoding="utf-8") as f:f.write(data+"\n")
    else:print(data)

if __name__=="__main__":main()
