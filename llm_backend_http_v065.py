"""SEMOS_SIM v0.6.5: optional subprocess LLM backend for loopback HTTP VM.

No VM, LLM_TRY or LLM_SEM integration is asserted. Backend must implement
JSON-on-stdin / JSON-on-stdout protocol; no shell=True. Only explicitly
configured absolute executable and script files can run.
"""
import argparse,json,subprocess,sys,os
from pathlib import Path
from http.server import ThreadingHTTPServer
from local_vm_http_server_v064 import make_handler,answer_request

def invoke_backend(request,command,timeout_seconds=15):
    if not isinstance(command,list) or len(command)<2 or any(not isinstance(x,str) or not x for x in command):
        raise ValueError("command must be nonempty argv list")
    if not all(Path(x).is_absolute() for x in command[:2]):
        raise ValueError("executable and script paths must be absolute")
    if not Path(command[0]).is_file() or not Path(command[1]).is_file():
        raise ValueError("backend executable/script missing")
    if not isinstance(timeout_seconds,(int,float)) or not 1<=timeout_seconds<=60:
        raise ValueError("invalid backend timeout")
    encoded=json.dumps(request,ensure_ascii=False).encode("utf-8")
    if len(encoded)>65536:raise ValueError("request too large")
    try:
        completed=subprocess.run(command,input=encoded,stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,timeout=timeout_seconds,check=False,shell=False)
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError("LLM backend timeout") from exc
    if completed.returncode!=0:raise RuntimeError("backend returned nonzero exit code")
    if len(completed.stdout)>65536:raise ValueError("backend response too large")
    try:obj=json.loads(completed.stdout.decode("utf-8"))
    except (ValueError,UnicodeDecodeError) as exc:raise ValueError("invalid backend JSON") from exc
    return obj

def backend_response(request,vm,argv,timeout):
    # First validate request and avoid side effects using v0.6.4 contract.
    answer_request(request,vm)
    reply=invoke_backend(request,argv,timeout)
    if not isinstance(reply,dict) or reply.get("protocol")!="semos.vm.v1":
        raise ValueError("backend protocol mismatch")
    for k,v in (("request_id",request["request_id"]),("source_vm",vm),("question",request["question"])):
        if reply.get(k)!=v:raise ValueError("backend correlation mismatch: "+k)
    if not isinstance(reply.get("answer"),str) or not reply["answer"].strip():
        raise ValueError("empty backend answer")
    if not isinstance(reply.get("execution_id"),str) or not reply["execution_id"]:
        raise ValueError("execution_id required")
    if not isinstance(reply.get("executed_at"),str) or not reply["executed_at"]:
        raise ValueError("executed_at required")
    reply["response_kind"]="EXTERNAL_SUBPROCESS_UNVERIFIED"
    return reply

def handler_factory(vm,argv,timeout):
    base=make_handler(vm)
    class Handler(base):
        def do_POST(self):
            if self.path!="/answer":
                self.respond(404,{"error":"not found"});return
            try:
                size=int(self.headers.get("Content-Length","0"))
                if size<1 or size>65536:raise ValueError("invalid body size")
                obj=json.loads(self.rfile.read(size).decode("utf-8"))
                result=backend_response(obj,vm,argv,timeout)
                self.respond(200,result)
            except TimeoutError:self.respond(504,{"error":"backend timeout"})
            except (ValueError,UnicodeDecodeError,json.JSONDecodeError) as exc:
                self.respond(400,{"error":str(exc)})
            except RuntimeError:self.respond(502,{"error":"backend execution failed"})
    return Handler

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--vm",choices=("VM-A","VM-B","VM-C"),default="VM-C")
    p.add_argument("--port",type=int,default=8765)
    p.add_argument("--python",required=True,help="absolute Python executable")
    p.add_argument("--backend-script",required=True,help="absolute path to backend adapter")
    p.add_argument("--timeout",type=float,default=15)
    a=p.parse_args()
    if not 1024<=a.port<=65535:p.error("invalid port")
    argv=[str(Path(a.python).resolve()),str(Path(a.backend_script).resolve())]
    if not all(Path(x).is_file() for x in argv):p.error("Missing executable or backend script")
    server=ThreadingHTTPServer(("127.0.0.1",a.port),handler_factory(a.vm,argv,a.timeout))
    print(f"UNVERIFIED external subprocess adapter for {a.vm} on loopback:{a.port}",flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=="__main__":main()
