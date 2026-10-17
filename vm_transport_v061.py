"""SEMOS_SIM v0.6.1: VM communication contract, mock-only by default.

Defines a provider-neutral request/response envelope and endpoint mapping.
Real HTTP transport is intentionally NOT implemented at this milestone.
"""
import argparse,json,re,hashlib
from pathlib import Path
from mock_vm_transport_v05297 import read_fixtures,fetch_mock
from validate_hitl_retry_v05294 import process

VMS=("VM-A","VM-B","VM-C")
class TransportError(Exception):pass

def validate_config(config):
    if not isinstance(config,dict) or config.get("version")!="0.6.1":raise ValueError("invalid config version")
    mapping=config.get("vms")
    if not isinstance(mapping,dict) or set(mapping)!=set(VMS):raise ValueError("VM mapping must contain VM-A/B/C")
    for vm,settings in mapping.items():
        if not isinstance(settings,dict) or settings.get("transport")!="mock":
            raise ValueError(f"{vm}: only mock transport is supported")
        timeout=settings.get("timeout_ms")
        if type(timeout) is not int or not 100<=timeout<=120000:
            raise ValueError(f"{vm}: invalid timeout_ms")
    return config

def envelope(packet):
    if packet.get("status")!="RETRY_HANDOFF_PENDING_VM_EXECUTION":raise ValueError("not pending VM execution")
    vm=packet.get("retry_vm");rid=packet.get("request_id");question=packet.get("question")
    if vm not in VMS or not isinstance(rid,str) or not rid or not isinstance(question,str) or not question.strip():
        raise ValueError("missing request ID, retry VM, or question")
    if vm in packet.get("visited_vms",[]):raise ValueError("retry VM already visited")
    return {"protocol":"semos.vm.v1","request_id":rid,"target_vm":vm,
        "question":question,"operation":"ANSWER_ONLY","side_effects_allowed":False}

def dispatch(packet,config,fixtures):
    if packet.get("status")!="RETRY_HANDOFF_PENDING_VM_EXECUTION":return dict(packet)
    request=envelope(packet)
    vm=request["target_vm"]
    if config["vms"][vm]["transport"]!="mock":raise ValueError("not an allowed transport")
    try:reply=fetch_mock(packet,fixtures)
    except (TimeoutError,ConnectionError) as exc:
        p=dict(packet);p["events"]=list(packet.get("events",[]))+[{
            "state":"VM_TRANSPORT_ERROR","vm":vm,"error":type(exc).__name__}]
        p["transport_error"]=type(exc).__name__
        return p
    if reply is None:return dict(packet)
    result=process(packet,reply)
    if result.get("status")=="PENDING_USER_REVIEW":
        result["transport"]="MOCK_ONLY"
        result["request_envelope"]=request
        result["response_envelope"]={"protocol":"semos.vm.v1","request_id":request["request_id"],
           "source_vm":vm,"execution_id":reply["execution_id"],"source":"mock-fixture"}
    return result

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--input",default="results/hitl_retry_handoff_v05293.json")
    a.add_argument("--config",default="config/vm_transport_v061.json")
    a.add_argument("--fixture-file",default="data/mock_vm_replies_v05297.csv")
    a.add_argument("--output",default="results/vm_transport_v061.json")
    args=a.parse_args();dst=Path(args.output)
    if dst.exists():a.error("Refusing overwrite")
    try:
        config=validate_config(json.loads(Path(args.config).read_text(encoding="utf-8-sig")))
        fixtures=read_fixtures(args.fixture_file)
        raw=Path(args.input).read_bytes();doc=json.loads(raw)
        packets=doc["packets"]
        ids=[p["request_id"] for p in packets]
        if len(ids)!=len(set(ids)):raise ValueError("duplicate request ID")
        if set(fixtures)-set(ids):raise ValueError("unknown fixture ID")
        result=[dispatch(p,config,fixtures) for p in packets]
    except (ValueError,KeyError,TypeError) as e:a.error(str(e))
    states=sorted({p["status"] for p in result})
    report={"version":"0.6.1","kind":"VM_TRANSPORT_CONTRACT_MOCK_ONLY",
      "input_sha256":hashlib.sha256(raw).hexdigest(),
      "summary":{s:sum(p["status"]==s for p in result) for s in states},
      "packets":result,"limitations":["Only mock transport is implemented; no real VM request",
        "No verified source attestation","No execution of side effects",
        "A valid mock response is still unapproved until explicit user review"]}
    dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2));print("Saved:",dst)
if __name__=="__main__":main()
