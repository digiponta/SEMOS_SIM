"""Optional real LLM_SEM adapter. Loads sibling repository, never modifies it."""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
from semantic_os import Decision, MockSemanticEngine

def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

class LLMSemAdapter:
    """Actual LLM_SEM NDC classification and optional checkpoint semantic vectors.

    Classification is keyword-based ndc.py, not learned NDC inference.
    Vector similarity uses raw model semantic_vector, not calibrated for routing.
    """
    def __init__(self, root=None, *, model_path=None, tokenizer_path=None,
                 device="auto", similarity_threshold=0.90):
        self.root = Path(root or Path(__file__).resolve().parent.parent / "LLM_SEM").resolve()
        for name in ("ndc.py", "model.py", "tokenizer.py"):
            if not (self.root / name).is_file():
                raise FileNotFoundError(f"Missing LLM_SEM file: {self.root / name}")
        self.ndc = _load_module("semos_external_ndc", self.root / "ndc.py")
        self.fallback = MockSemanticEngine()
        self.model = None
        self.tokenizer = None
        self.torch = None
        self.device = None
        self.similarity_threshold = similarity_threshold
        if model_path is not None:
            import torch
            self.torch = torch
            self.device = torch.device("cuda" if device == "auto" and torch.cuda.is_available()
                                       else "cpu" if device == "auto" else device)
            model_module = _load_module("semos_external_model", self.root / "model.py")
            tokenizer_module = _load_module("semos_external_tokenizer", self.root / "tokenizer.py")
            def resolve(path):
                p = Path(path)
                return p if p.is_absolute() else self.root / p
            tp = resolve(tokenizer_path or "model/tokenizer.json")
            mp = resolve(model_path)
            if not tp.is_file() or not mp.is_file():
                raise FileNotFoundError(f"Missing checkpoint/tokenizer: {mp}, {tp}")
            self.tokenizer = tokenizer_module.Tokenizer.load(str(tp))
            self.model, self.checkpoint = model_module.LanguageModel.load_checkpoint(
                str(mp), device=self.device)
            if self.model.vocab_size != self.tokenizer.vocab_size:
                raise ValueError("Tokenizer/model vocabulary mismatch")
            self.model.eval()

    def classify(self, text):
        return self.ndc.classify(text).as_dict()

    def vector(self, text):
        if self.model is None:
            raise RuntimeError("Model checkpoint not loaded; supply --llm-sem-model")
        ids = self.tokenizer.encode(text, add_bos=True)
        ids = ids[-self.model.context_length:]
        inputs = self.torch.tensor([ids], dtype=self.torch.long, device=self.device)
        with self.torch.no_grad():
            v = self.model.encode_semantic(inputs, pooling="mean")[0]
            v = self.torch.nn.functional.normalize(v, p=2, dim=0)
        return v

    def interpret(self, text, facts):
        decision = self.fallback.interpret(text, facts)
        if decision.intent != "unknown" or not facts or self.model is None:
            return decision
        # Semantic similarity is exploratory; no automatic fact promotion.
        query = self.vector(decision.subject)
        subjects = sorted({f.subject for f in facts})
        scores = [(float(self.torch.dot(query, self.vector(subject)).item()), subject)
                  for subject in subjects]
        score, subject = max(scores)
        if score < self.similarity_threshold:
            return Decision("unknown", decision.subject, score, "LLM_SEM uncalibrated cosine below threshold")
        return Decision("query", subject, score, "LLM_SEM pooled hidden-state cosine (experimental)")
