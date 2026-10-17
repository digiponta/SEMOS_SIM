"""v0.6.6: LLM_TRY raw-generation subprocess adapter.

Reads one semos.vm.v1 request on stdin, responds with one JSON object
on stdout. Uses LLM_TRY/chat.py's genuine model/tokenizer/generate_reply.
Raw generation ONLY: DOES NOT replicate LLM_TRY's full Unknown Gate, NDC,
Semantic Memory, or interactive dispatch policy. Human approval required.
"""
import argparse,importlib.util,json,sys,uuid,hashlib
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

def experimental_lookup(question,knowledge_file,mod):
    if not knowledge_file:
        return None,None
    path=Path(knowledge_file).resolve(strict=True)
    if not path.is_file():raise ValueError("Experimental knowledge path is not a file")
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    hit=mod.semantic_knowledge_lookup(question,knowledge_path=path)
    return hit,{"path":str(path),"sha256":digest,"read_only":True,
                "experimental":True,"authenticated":False}

def generate(obj,repo,checkpoint,tokenizer,max_tokens=96,knowledge_file=None):
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
        prompt,_selected_history=mod.build_prompt([],req["question"],0)
        response=mod.generate_reply(model,tokenizer_obj,prompt,
                    max_new_tokens=max_tokens,temperature=0.0,top_k=1,
                    repetition_penalty=1.0)
        # v0.6.9: use LLM_TRY's conservative lexical concept gate and
        # canonical semantic lookup, but do not claim full runtime evaluation.
        lexical_unknown,concept=mod.pre_generation_unknown_concept(req["question"])
        knowledge_hit,experiment_meta=experimental_lookup(req["question"],knowledge_file,mod)
        if knowledge_file is None:
            knowledge_hit=mod.semantic_knowledge_lookup(req["question"])
        semantic_state="UNVERIFIED"
        semantic_reason="raw_model_generation_not_fact_verified"
        if knowledge_hit and knowledge_hit[1].strip()==response.text.strip():
            semantic_state="KNOWN"
            semantic_reason="exact_match_to_local_semantic_knowledge"
        elif lexical_unknown and not knowledge_hit:
            semantic_state="UNKNOWN"
            semantic_reason="llm_try_pre_generation_unknown_concept"
        answer=response.text.strip()
        retrieved_answer=knowledge_hit[1].strip() if knowledge_hit else None
        evidence_comparison={
            "generated":{"answer":answer,"origin":"LLM_TRY_CHECKPOINT"},
            "retrieved":{"answer":retrieved_answer,"origin":"LLM_TRY_LOCAL_SEMANTIC_KNOWLEDGE",
                "concept":knowledge_hit[0] if knowledge_hit else None,
                "present":bool(knowledge_hit),"source_authenticated":False,
                "experimental_file":experiment_meta},
            "relation":"EXACT_MATCH" if retrieved_answer is not None and answer==retrieved_answer
                else "DIFFERENT" if retrieved_answer is not None else "NO_RETRIEVAL",
            "verified":False,"requires_human_review":True}
    finally:
        sys.path[:]=old_path
    if not answer:raise ValueError("Empty LLM generation; refused")
    return {"protocol":"semos.vm.v1","request_id":req["request_id"],
        "source_vm":req["target_vm"],"question":req["question"],"answer":answer,
        "execution_id":"llmtry-"+uuid.uuid4().hex,
        "executed_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "response_kind":"LLM_TRY_RAW_GENERATION_UNVERIFIED",
        "model_checkpoint":str(ckpt),"tokenizer":str(tok),
        "unknown_gate_applied":False,"human_approval_required":True,
        "evidence_comparison":evidence_comparison,
        "semantic_assessment":{"state":semantic_state,"reason":semantic_reason,
            "concept":concept,"knowledge_record_present":bool(knowledge_hit),
            "full_unknown_gate_applied":False,"verified":False},
        "generation_diagnostic":{"prompt_mode":"llm_try_build_prompt_empty_history",
            "prompt_character_count":len(prompt),"generated_character_count":len(answer),
            "generated_token_count":response.token_count,
            "mean_confidence":response.mean_confidence,
            "min_confidence":response.min_confidence,
            "mean_top2_margin":response.mean_top2_margin}}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",required=True);p.add_argument("--checkpoint",required=True)
    p.add_argument("--tokenizer",required=True);p.add_argument("--max-tokens",type=int,default=96)
    p.add_argument("--knowledge-file",default=None,help="read-only experimental JSONL knowledge")
    a=p.parse_args()
    if not 1<=a.max_tokens<=256:p.error("max-tokens out of bounds")
    try:
        raw=sys.stdin.buffer.read(65537)
        if len(raw)>65536:raise ValueError("Input too large")
        req=json.loads(raw.decode("utf-8"))
        out=generate(req,a.repo,a.checkpoint,a.tokenizer,a.max_tokens,a.knowledge_file)
        sys.stdout.buffer.write((json.dumps(out,ensure_ascii=False)+"\n").encode("utf-8"))
    except Exception as exc:
        print(f"LLM_TRY adapter failed: {type(exc).__name__}: {exc}",file=sys.stderr)
        raise SystemExit(1)
if __name__=="__main__":main()
