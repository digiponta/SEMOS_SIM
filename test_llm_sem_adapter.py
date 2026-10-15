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

if __name__ == "__main__":
    unittest.main()
