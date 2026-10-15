"""Experimental semantic scheduler for dummy VM capabilities.

Cosine similarities are uncalibrated; fallback is conservative round-robin.
No actual VM, hypervisor, or privileged execution is involved.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict

CAPABILITIES = {
    "VM-A": "量子力学 物理学 数学 科学 計算",
    "VM-B": "GPU CUDA AI LLM プログラミング 情報工学",
    "VM-C": "文学 言語 日本語 文章 芸術",
}

@dataclass
class Route:
    selected: str
    method: str
    score: float | None
    margin: float | None
    rankings: list[dict]

    def as_dict(self):
        return asdict(self)

class SemanticScheduler:
    def __init__(self, engine, *, min_similarity=0.85, min_margin=0.04):
        if getattr(engine, "model", None) is None:
            raise ValueError("Semantic scheduler requires real LLM_SEM checkpoint")
        self.engine = engine
        self.min_similarity = min_similarity
        self.min_margin = min_margin
        self.cap_vectors = {name: engine.vector(text) for name, text in CAPABILITIES.items()}
        self.last_route = None
        self.round_robin_index = 0

    def route(self, request, vms):
        online = [vm for vm in vms if vm.online]
        if not online:
            raise RuntimeError("No online dummy VMs")
        scores = []
        # Explicit kernel commands use deterministic fallback, not semantic routing.
        if not request.lstrip().startswith("/"):
            import torch
            q = self.engine.vector(request)
            scores = sorted(
                [{"vm": vm.name, "cosine": float(torch.dot(q, self.cap_vectors[vm.name]).item())}
                 for vm in online],
                key=lambda item: item["cosine"], reverse=True
            )
        best = scores[0]["cosine"] if scores else None
        margin = best - scores[1]["cosine"] if len(scores) > 1 else None
        confident = (best is not None and best >= self.min_similarity
                     and (margin is None or margin >= self.min_margin))
        if confident:
            selected = scores[0]["vm"]
            method = "semantic"
        else:
            selected = online[self.round_robin_index % len(online)].name
            self.round_robin_index += 1
            method = "round_robin_fallback"
        self.last_route = Route(selected, method, best, margin, scores)
        return self.last_route

