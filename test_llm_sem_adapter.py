import tempfile
import unittest
from pathlib import Path
from llm_sem_adapter import LLMSemAdapter

class AdapterSmokeTests(unittest.TestCase):
    def test_sibling_ndc(self):
        root = Path(__file__).resolve().parent.parent / "LLM_SEM"
        if not (root / "ndc.py").exists():
            self.skipTest("Sibling LLM_SEM repository not installed")
        adapter = LLMSemAdapter(root=root)
        result = adapter.classify("量子力学")
        self.assertEqual(result["code"], "420")
        self.assertEqual(result["state"], "CLASSIFIED")

    def test_model_is_explicit_opt_in(self):
        root = Path(__file__).resolve().parent.parent / "LLM_SEM"
        if not (root / "ndc.py").exists():
            self.skipTest("Sibling LLM_SEM repository not installed")
        adapter = LLMSemAdapter(root=root)
        with self.assertRaises(RuntimeError):
            adapter.vector("量子力学")

    def test_real_checkpoint_vector_when_available(self):
        root = Path(__file__).resolve().parent.parent / "LLM_SEM"
        checkpoint = root / "model/model-sem-internalized-v01575.pt"
        tokenizer = root / "model/tokenizer.json"
        if not checkpoint.is_file() or not tokenizer.is_file():
            self.skipTest("Real LLM_SEM checkpoint or tokenizer not available")
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch not installed")
        adapter = LLMSemAdapter(root=root, model_path=checkpoint, device="cpu")
        vector = adapter.vector("量子力学")
        self.assertEqual(vector.ndim, 1)
        self.assertEqual(vector.numel(), adapter.model.d_model)
        self.assertAlmostEqual(float(vector.norm().item()), 1.0, places=5)

if __name__ == "__main__":
    unittest.main()
