"""v0.6.6: LLM_TRY raw-generation subprocess adapter.

Reads one semos.vm.v1 request on stdin, responds with one JSON object
on stdout. Uses LLM_TRY/chat.py's genuine model/tokenizer/generate_reply.
Raw generation ONLY: DOES NOT replicate LLM_TRY's full Unknown Gate, NDC,
Semantic Memory, or interactive dispatch policy. Human approval required.
"""
import argparse,importlib.util,json,sys,uuid
from datetime import datetime,timezone
from pathlib import Path

def read_request(obj):
    if not isinstance(obj,dict) or obj.get("protocol")!="semos.vm.v1":
        raise ValueError("Invalid protocol")
    if obj.get("operation")!="ANSWER_ONLY" or obj.get("side_effects_allowed") is not False:
        raise ValueError("Only answer-only requests allowed")
    for k in ("request_id","target_vm","question"):
        if not isinstance(obj.get(k),str) or not obj[k].strip():raise ValueError("Missing "+k)
    if obj["target_vm"] not in ("VM-A","VM-B","VM-C"):raise ValueError("Invalid VM")
    return obj

def resolve_model_paths(repo,checkpoint,tokenizer):
    root=Path(repo).resolve()
    if not (root/"chat.py").is_file():raise FileNotFoundError("LLM_TRY chat.py missing")
    ckpt=Path(checkpoint).resolve();tok=Path(tokenizer).resolve()
    if not ckpt.is_file() or not tok.is_file():raise FileNotFoundError("Model or tokenizer missing")
    return root,ckpt,tok

def generate(obj,repo,checkpoint,tokenizer,max_tokens=96):
    req=read_request(obj)
    root,ckpt,tok=resolve_model_paths(repo,checkpoint,tokenizer)
    # Prevent chat.py import-time stdout from corrupting JSON protocol.
    old_path=list(sys.path)
    try:
        sys.path.insert(0,str(root))
        spec=importlib.util.spec_from_file_location("semos_llm_try_chat",root/"chat.py")
        mod=importlib.util.module_from_spec(spec)
        sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
        device=mod.torch.device("cuda" if mod.torch.cuda.is_available() else "cpu")
        tokenizer_obj=mod.Tokenizer.load(str(tok))
        model,_=mod.LanguageModel.load_checkpoint(str(ckpt),device=device)
        if model.vocab_size!=tokenizer_obj.vocab_size:raise ValueError("Vocabulary mismatch")
        response=mod.generate_reply(model,tokenizer_obj,req["question"],
                    max_new_tokens=max_tokens,temperature=0.0,top_k=1,
                    repetition_penalty=1.0)
        answer=response.text.strip()
    finally:
        sys.path[:]=old_path
    if not answer:raise ValueError("Empty LLM generation; refused")
    return {"protocol":"semos.vm.v1","request_id":req["request_id"],
        "source_vm":req["target_vm"],"question":req["question"],"answer":answer,
        "execution_id":"llmtry-"+uuid.uuid4().hex,
        "executed_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "response_kind":"LLM_TRY_RAW_GENERATION_UNVERIFIED",
        "model_checkpoint":str(ckpt),"tokenizer":str(tok),
        "unknown_gate_applied":False,"human_approval_required":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",required=True);p.add_argument("--checkpoint",required=True)
    p.add_argument("--tokenizer",required=True);p.add_argument("--max-tokens",type=int,default=96)
    a=p.parse_args()
    if not 1<=a.max_tokens<=256:p.error("max-tokens out of bounds")
    try:
        raw=sys.stdin.buffer.read(65537)
        if len(raw)>65536:raise ValueError("Input too large")
        req=json.loads(raw.decode("utf-8"))
        out=generate(req,a.repo,a.checkpoint,a.tokenizer,a.max_tokens)
        sys.stdout.buffer.write((json.dumps(out,ensure_ascii=False)+"\n").encode("utf-8"))
    except Exception as exc:
        print(f"LLM_TRY adapter failed: {type(exc).__name__}: {exc}",file=sys.stderr)
        raise SystemExit(1)
if __name__=="__main__":main()
