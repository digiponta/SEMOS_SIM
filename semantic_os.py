"""Semantic OS control-plane simulator v0.1. All VM instances are Python-only dummies."""
from __future__ import annotations
import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Protocol

@dataclass
class Fact:
    subject: str
    predicate: str
    object: str
    truth: str = "UNVERIFIED"
    source: str = "user"

    @property
    def key(self) -> str:
        return f"{self.subject}|{self.predicate}|{self.object}"

@dataclass
class Decision:
    intent: str
    subject: str
    score: float
    explanation: str

class SemanticEngine(Protocol):
    def interpret(self, text: str, facts: list[Fact]) -> Decision: ...

class MockSemanticEngine:
    """Deterministic placeholder, NOT an actual LLM_SEM model."""
    def interpret(self, text: str, facts: list[Fact]) -> Decision:
        t = text.strip()
        commands = {"/sleep": "sleep", "/sync": "sync",
                    "/status": "status", "/memory": "memory"}
        for prefix, intent in (("/teach ", "teach"), ("/approve ", "approve")):
            if t.startswith(prefix):
                return Decision(intent, "", 1.0, "Explicit command")
        if t in commands:
            return Decision(commands[t], "", 1.0, "Explicit command")
        normalized = re.sub(r"[？?。\s]+$", "", t)
        normalized = re.sub(r"(とは|について教えて|を説明して|について)$", "", normalized)
        for subject in sorted({f.subject for f in facts}, key=len, reverse=True):
            if subject and subject in normalized:
                return Decision("query", subject, 0.95, "Exact subject match")
        return Decision("unknown", normalized, 0.0, "No matching knowledge")

@dataclass
class Process:
    pid: int
    request: str
    intent: str
    state: str
    vm: str
    result: str = ""

@dataclass
class DummyVM:
    name: str
    online: bool = True
    memory: dict[str, Fact] = field(default_factory=dict)
    internalized_keys: set[str] = field(default_factory=set)

class SemanticOS:
    def __init__(self, engine: SemanticEngine | None = None, scheduler=None):
        self.engine = engine or MockSemanticEngine()
        self.scheduler = scheduler
        self.vms = [DummyVM("VM-A"), DummyVM("VM-B"), DummyVM("VM-C")]
        self.canonical: dict[str, Fact] = {}
        self.pending: dict[str, Fact] = {}
        self.processes: list[Process] = []
        self.pid = 0
        self.next_vm = 0
        self.audit: list[dict] = []

    def _run(self, request: str, intent: str, operation) -> Process:
        # Dummy VM scheduling only: no hypervisor, container, or subprocess.
        if self.scheduler is not None:
            route = self.scheduler.route(request, self.vms)
            if route.selected is None:
                self.pid += 1
                proc = Process(self.pid, request, intent, "HELD", "-", "UNKNOWN_GATE: low-confidence semantic route")
                self.processes.append(proc)
                self.audit.append(asdict(proc))
                return proc
            vm = next(vm for vm in self.vms if vm.name == route.selected)
        else:
            vm = self.vms[self.next_vm % len(self.vms)]
            self.next_vm += 1
        self.pid += 1
        proc = Process(self.pid, request, intent, "RUNNING", vm.name)
        self.processes.append(proc)
        try:
            if not vm.online:
                raise RuntimeError(f"{vm.name} offline")
            proc.result = str(operation())
            proc.state = "DONE"
        except Exception as exc:
            proc.state = "FAILED"
            proc.result = str(exc)
        self.audit.append(asdict(proc))
        return proc

    def submit(self, request: str) -> Process:
        decision = self.engine.interpret(request, list(self.canonical.values()))

        def execute():
            if decision.intent == "teach":
                fields = [x.strip() for x in request[len("/teach "):].split("|")]
                if len(fields) not in (3, 4) or not all(fields[:3]):
                    raise ValueError("Usage: /teach SUBJECT | PREDICATE | OBJECT [| SOURCE]")
                fact = Fact(*fields[:3], source=fields[3] if len(fields) == 4 else "user")
                self.pending[fact.key] = fact
                return f"PENDING {fact.key}"
            if decision.intent == "approve":
                key = request[len("/approve "):].strip()
                if key not in self.pending:
                    raise ValueError(f"No such pending fact: {key}")
                fact = self.pending.pop(key)
                fact.truth = "UNVERIFIED"
                self.canonical[key] = fact
                return f"APPROVED {key} (UNVERIFIED)"
            if decision.intent == "query":
                matches = [f for f in self.canonical.values() if f.subject == decision.subject]
                return " / ".join(f"{f.subject} {f.predicate} {f.object} [{f.truth}; {f.source}]" for f in matches)
            if decision.intent == "sync":
                return json.dumps(self.sync(), ensure_ascii=False)
            if decision.intent == "sleep":
                return json.dumps(self.sleep(), ensure_ascii=False)
            if decision.intent == "status":
                return json.dumps(self.status(), ensure_ascii=False)
            if decision.intent == "memory":
                return json.dumps([asdict(f) for f in self.canonical.values()], ensure_ascii=False)
            return f"UNKNOWN: {decision.subject} (review needed)"

        return self._run(request, decision.intent, execute)

    def sync(self) -> dict:
        """Simulation of two-online-VM eligibility, NOT distributed consensus."""
        online = [vm for vm in self.vms if vm.online]
        if len(online) < 2:
            return {"ok": False, "reason": "2 of 3 dummy VMs required"}
        for vm in online:
            vm.memory = dict(self.canonical)
        return {"ok": True, "replicas_updated": [vm.name for vm in online], "facts": len(self.canonical)}

    def sleep(self) -> dict:
        """Simulation marker ONLY; never updates LLM model weights."""
        sync_result = self.sync()
        if not sync_result["ok"]:
            return sync_result
        for vm in self.vms:
            if vm.online:
                vm.internalized_keys.update(vm.memory)
        return {"ok": True, "mode": "SIMULATED_NO_WEIGHT_UPDATES",
                "markers": {vm.name: len(vm.internalized_keys) for vm in self.vms}}

    def status(self) -> dict:
        return {"processes": len(self.processes), "canonical": len(self.canonical),
                "pending": len(self.pending),
                "vms": {vm.name: {"online": vm.online, "memory": len(vm.memory),
                                    "simulated_internalized": len(vm.internalized_keys)}
                        for vm in self.vms}}

    def save(self, path: str | Path) -> None:
        state = {"canonical": [asdict(f) for f in self.canonical.values()],
                 "pending": [asdict(f) for f in self.pending.values()],
                 "audit": self.audit}
        Path(path).write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, path: str | Path) -> None:
        state = json.loads(Path(path).read_text(encoding="utf-8"))
        self.canonical = {f.key: f for f in (Fact(**x) for x in state["canonical"])}
        self.pending = {f.key: f for f in (Fact(**x) for x in state["pending"])}
        self.audit = state.get("audit", [])

def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic OS Simulator v0.1")
    parser.add_argument("--state", default="semantic_os_state.json")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--scheduler", choices=["round-robin", "semantic"], default="round-robin")
    parser.add_argument("--engine", choices=["mock", "llm-sem"], default="mock")
    parser.add_argument("--llm-sem-root", default=None)
    parser.add_argument("--llm-sem-model", default=None, help="Checkpoint path relative to sibling LLM_SEM")
    args = parser.parse_args()
    engine = None
    if args.engine == "llm-sem":
        from llm_sem_adapter import LLMSemAdapter
        engine = LLMSemAdapter(root=args.llm_sem_root, model_path=args.llm_sem_model)
        print(f"LLM_SEM connected: {engine.root} | model={'loaded' if engine.model is not None else 'not loaded'}")
    scheduler = None
    if args.scheduler == "semantic":
        if engine is None or getattr(engine, "model", None) is None:
            parser.error("--scheduler semantic requires --engine llm-sem --llm-sem-model MODEL")
        from semantic_scheduler import SemanticScheduler
        scheduler = SemanticScheduler(engine)
    osys = SemanticOS(engine=engine, scheduler=scheduler)
    state_path = Path(args.state)
    if state_path.exists():
        osys.load(state_path)
    if args.demo:
        commands = ["/teach 量子センサー | は | 量子現象を利用するセンサー",
                    "/approve 量子センサー|は|量子現象を利用するセンサー",
                    "量子センサーとは", "/sync", "/sleep", "/status"]
        for command in commands:
            result = osys.submit(command)
            print(f"> {command}\n[{result.vm}/{result.state}] {result.result}")
        return
    print(f"Semantic OS Simulator v0.3 — dummy VMs | engine={args.engine} | model={'loaded' if getattr(osys.engine, 'model', None) is not None else 'not loaded'}")
    print("Commands: /teach S | P | O, /approve S|P|O, /sync, /sleep, /memory, /status, /ndc TEXT, /vector TEXT, /similarity A | B, /route TEXT, /exit")
    try:
        while True:
            request = input("SemanticOS> ").strip()
            if request.startswith("/route "):
                if osys.scheduler is None:
                    print("ERROR: Route diagnostics require --scheduler semantic")
                else:
                    try:
                        print(json.dumps(osys.scheduler.route(request[7:].strip(), osys.vms).as_dict(),
                                         ensure_ascii=False))
                    except Exception as exc:
                        print(f"ERROR: {exc}")
                continue
            if request.startswith("/vector "):
                if not hasattr(osys.engine, "vector"):
                    print("ERROR: Vector requires --engine llm-sem --llm-sem-model MODEL")
                else:
                    try:
                        v = osys.engine.vector(request[8:].strip())
                        print(json.dumps({"dimension": int(v.numel()),
                                          "norm": float(v.norm().item()),
                                          "first8": v[:8].detach().cpu().tolist(),
                                          "source": "LLM_SEM checkpoint; mean pooling"},
                                         ensure_ascii=False))
                    except Exception as exc:
                        print(f"ERROR: {exc}")
                continue
            if request.startswith("/similarity "):
                if not hasattr(osys.engine, "vector"):
                    print("ERROR: Similarity requires --engine llm-sem --llm-sem-model MODEL")
                else:
                    try:
                        terms = [t.strip() for t in request[len("/similarity "):].split("|")]
                        if len(terms) != 2 or not all(terms):
                            raise ValueError("Usage: /similarity TEXT_A | TEXT_B")
                        import torch
                        a, b = (osys.engine.vector(t) for t in terms)
                        print(json.dumps({"cosine": float(torch.dot(a, b).item()),
                                          "texts": terms,
                                          "note": "Raw, uncalibrated model cosine"},
                                         ensure_ascii=False))
                    except Exception as exc:
                        print(f"ERROR: {exc}")
                continue
            if request.startswith("/ndc "):
                if not hasattr(osys.engine, "classify"):
                    print("NDC classification requires --engine llm-sem")
                else:
                    print(json.dumps(osys.engine.classify(request[5:]), ensure_ascii=False))
                continue
            if request == "/exit":
                break
            if request:
                result = osys.submit(request)
                print(f"[{result.pid} {result.vm} {result.state}] {result.result}")
                osys.save(state_path)
    except (EOFError, KeyboardInterrupt):
        print("\nExit")
    finally:
        osys.save(state_path)

if __name__ == "__main__":
    main()
