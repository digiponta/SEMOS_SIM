"""SEMOS_SIM v0.6.3: opt-in local HTTP VM adapter.

By default: NO network request. Only explicitly configured loopback HTTP
endpoints are accepted. The remote process is not authenticated as a VM.
Only ANSWER_ONLY requests are permitted. No redirect following.
"""
import argparse,hashlib,json,socket,urllib.parse,urllib.request,urllib.error,ipaddress
from pathlib import Path
from validate_hitl_retry_v05294 import process
from vm_transport_v061 import envelope

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None

def verify_endpoint(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme!="http" or not u.hostname or u.username or u.password or u.query or u.fragment:
        raise ValueError("Only http loopback URLs without credentials/query/fragment")
    if u.hostname not in ("localhost","127.0.0.1","::1"):
        raise ValueError("Only explicit loopback endpoints allowed")
    try:
        if not (1<=u.port<=65535):raise ValueError("Invalid port")
    except TypeError:raise ValueError("Port required")
    if u.path!="/answer":raise ValueError("Endpoint path must be /answer")
    return url

def verify_live_config(config):
    if config.get("version")!="0.6.3":raise ValueError("Expected v0.6.3 config")
    vms=config.get("vms")
    if not isinstance(vms,dict) or set(vms)!={"VM-A","VM-B","VM-C"}:
        raise ValueError("Expected VM-A/B/C mappings")
    for name,entry in vms.items():
        if entry.get("transport")!="http-loopback":raise ValueError("Only http-loopback configured")
        verify_endpoint(entry.get("url",""))
        timeout=entry.get("timeout_ms")
        if type(timeout)!=int or not 100<=timeout<=30000:raise ValueError("Invalid timeout_ms")
    return config

def validate_response(body,request,vm):
    if not isinstance(body,dict):raise ValueError("VM reply must be JSON object")
    if body.get("protocol")!="semos.vm.v1":raise ValueError("Protocol mismatch")
    if body.get("request_id")!=request["request_id"]:raise ValueError("Request ID mismatch")
    if body.get("source_vm")!=vm:raise ValueError("VM identity claim mismatch")
    if body.get("question")!=request["question"]:raise ValueError("Question mismatch")
    return {"vm":vm,"question":body["question"],"answer":body.get("answer",""),
            "generation_diagnostic":body.get("generation_diagnostic"),
            "execution_id":body.get("execution_id",""),
            "executed_at":body.get("executed_at",""),
            "source":"unverified-http-loopback"}

def fetch_http(request,settings):
    endpoint=verify_endpoint(settings["url"])
    body=json.dumps(request,ensure_ascii=False).encode("utf-8")
    if len(body)>65536:raise ValueError("Request too large")
    req=urllib.request.Request(endpoint,data=body,method="POST",
            headers={"Content-Type":"application/json; charset=utf-8","Accept":"application/json"})
    opener=urllib.request.build_opener(NoRedirect,urllib.request.ProxyHandler({}))
    try:
        with opener.open(req,timeout=settings["timeout_ms"]/1000) as resp:
            if resp.status!=200:raise ValueError("Unexpected HTTP status")
            if "application/json" not in resp.headers.get("Content-Type",""):
                raise ValueError("Expected application/json")
            payload=resp.read(65537)
            if len(payload)>65536:raise ValueError("Response too large")
    except (urllib.error.URLError,TimeoutError,ConnectionError,OSError) as exc:
        raise ConnectionError(type(exc).__name__) from exc
    return json.loads(payload.decode("utf-8"))

def dispatch_live(packet,config,allow_live=False,fetcher=fetch_http):
    if packet.get("status")!="RETRY_HANDOFF_PENDING_VM_EXECUTION":return dict(packet)
    if not allow_live:raise ValueError("Live transport requires --allow-live")
    verify_live_config(config)
    req=envelope(packet);vm=req["target_vm"]
    try:
        body=fetcher(req,config["vms"][vm])
        reply=validate_response(body,req,vm)
    except (ConnectionError,TimeoutError) as exc:
        p=dict(packet);p["events"]=list(packet.get("events",[]))+[{"state":"VM_TRANSPORT_ERROR","vm":vm,"error":type(exc).__name__}]
        p["transport_error"]=type(exc).__name__
        return p
    result=process(packet,reply)
    if result.get("validation_error"):
        # Keep prior packet.answer unchanged: the rejected text is diagnostic only.
        # Never promote rejected content to HITL approval or semantic memory.
        answer=reply.get("answer","")
        result["rejected_reply_diagnostic"]={
            "answer":answer,
            "character_count":len(answer),
            "validation_error":result["validation_error"],
            "source":reply.get("source",""),
            "source_vm":vm,
            "execution_id":reply.get("execution_id",""),
            "executed_at":reply.get("executed_at",""),
            "trusted":False,
            "eligible_for_hitl":False,
            "generation_diagnostic":reply.get("generation_diagnostic"),
        }
    if result["status"]=="PENDING_USER_REVIEW":
        result["transport"]="HTTP_LOOPBACK_UNVERIFIED"
        if reply.get("generation_diagnostic") is not None:
            result["generation_diagnostic"]=reply["generation_diagnostic"]
        result["request_envelope"]=req
        result["response_envelope"]={"protocol":"semos.vm.v1","request_id":req["request_id"],"source_vm":vm,"source":"unverified-http-loopback"}
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True);p.add_argument("--config",required=True)
    p.add_argument("--output",required=True);p.add_argument("--allow-live",action="store_true")
    a=p.parse_args()
    if not a.allow_live:p.error("Refusing network access without --allow-live")
    output=Path(a.output)
    if output.exists():p.error("Refusing overwrite")
    try:
        config=verify_live_config(json.loads(Path(a.config).read_text(encoding="utf-8-sig")))
        raw=Path(a.input).read_bytes();doc=json.loads(raw);packets=doc["packets"]
        ids=[x["request_id"] for x in packets]
        if len(set(ids))!=len(ids):raise ValueError("Duplicate request IDs")
        rows=[dispatch_live(x,config,allow_live=True) for x in packets]
    except (ValueError,KeyError,TypeError) as exc:p.error(str(exc))
    states=sorted(set(x["status"] for x in rows))
    report={"version":"0.6.3","kind":"OPT_IN_LOOPBACK_HTTP_VM_TRANSPORT",
      "input_sha256":hashlib.sha256(raw).hexdigest(),
      "summary":{s:sum(x["status"]==s for x in rows) for s in states},
      "packets":rows,"limitations":[
         "Loopback HTTP response is not authenticated or cryptographically attested",
         "All answers require explicit human review; no automatic authorization",
         "No remote VM implementation or side effect execution is supplied"]}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2))
if __name__=="__main__":main()
