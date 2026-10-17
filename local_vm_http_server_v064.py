"""SEMOS_SIM v0.6.4 local HTTP test server. SYNTHETIC replies ONLY.

The server runs only on 127.0.0.1. It does NOT run an LLM or VM.
Provides /answer (POST) matching the v0.6.3 request contract.
"""
import argparse,json
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

VM_NAMES=("VM-A","VM-B","VM-C")
SYNTHETIC_ANSWER="量子力学は微視的な現象を数学的に記述する物理理論です。"

def answer_request(request,vm):
    if not isinstance(request,dict) or request.get("protocol")!="semos.vm.v1":
        raise ValueError("invalid protocol")
    if request.get("operation")!="ANSWER_ONLY" or request.get("side_effects_allowed") is not False:
        raise ValueError("operation not allowed")
    if request.get("target_vm")!=vm:raise ValueError("wrong VM target")
    rid=request.get("request_id");q=request.get("question")
    if not isinstance(rid,str) or not rid or not isinstance(q,str) or not q.strip():
        raise ValueError("request ID and question required")
    return {"protocol":"semos.vm.v1","request_id":rid,"source_vm":vm,
        "question":q,"answer":SYNTHETIC_ANSWER,
        "execution_id":"synthetic-http-"+rid,
        "executed_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "response_kind":"SYNTHETIC_TEST_ONLY"}

def make_handler(vm):
    class Handler(BaseHTTPRequestHandler):
        def respond(self,status,obj):
            raw=json.dumps(obj,ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers();self.wfile.write(raw)
        def do_POST(self):
            if self.path!="/answer":self.respond(404,{"error":"not found"});return
            try:
                size=int(self.headers.get("Content-Length","0"))
                if size<=0 or size>65536:raise ValueError("invalid body size")
                request=json.loads(self.rfile.read(size).decode("utf-8"))
                self.respond(200,answer_request(request,vm))
            except (ValueError,UnicodeDecodeError,json.JSONDecodeError) as exc:
                self.respond(400,{"error":str(exc)})
        def do_GET(self):
            self.respond(405,{"error":"POST /answer only"})
        def log_message(self,format,*args):
            print("%s - %s"%(self.address_string(),format%args))
    return Handler

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--vm",choices=VM_NAMES,default="VM-C")
    p.add_argument("--port",type=int,default=8765)
    args=p.parse_args()
    if not 1024<=args.port<=65535:p.error("Port must be 1024..65535")
    server=ThreadingHTTPServer(("127.0.0.1",args.port),make_handler(args.vm))
    print(f"SYNTHETIC local {args.vm} server at http://127.0.0.1:{args.port}/answer",flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=="__main__":main()
