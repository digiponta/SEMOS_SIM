"""Synthetic stdin/stdout protocol stub; NOT an LLM."""
import json,sys
from datetime import datetime,timezone
q=json.loads(sys.stdin.buffer.read().decode("utf-8"))
print(json.dumps({"protocol":"semos.vm.v1","request_id":q["request_id"],"source_vm":q["target_vm"],
"question":q["question"],"answer":"量子力学は微視的な物理現象を記述する理論です。",
"execution_id":"synthetic-backend-"+q["request_id"],
"executed_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
"model_kind":"SYNTHETIC_STUB"},ensure_ascii=False))
