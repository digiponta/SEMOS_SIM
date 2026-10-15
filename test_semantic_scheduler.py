import unittest
from types import SimpleNamespace
from semantic_scheduler import SemanticScheduler

class Vector:
    def __init__(self, name):
        self.name = name

class FakeTorch:
    pass

class DummyEngine:
    model = object()
    def vector(self, text):
        return Vector(text)

class SchedulerTests(unittest.TestCase):
    def test_requires_real_model(self):
        with self.assertRaises(ValueError):
            SemanticScheduler(SimpleNamespace(model=None))

    def test_explicit_command_fallback_and_offline(self):
        scheduler = SemanticScheduler(DummyEngine())
        vms = [SimpleNamespace(name=name, online=(name != "VM-A"))
               for name in ("VM-A", "VM-B", "VM-C")]
        r = scheduler.route("/status", vms)
        self.assertEqual(r.selected, "VM-B")
        self.assertEqual(r.method, "round_robin_fallback")
        self.assertEqual(r.rankings, [])

    def test_no_online(self):
        scheduler = SemanticScheduler(DummyEngine())
        with self.assertRaises(RuntimeError):
            scheduler.route("/status", [SimpleNamespace(name="VM-A", online=False)])

    def test_known_routes_and_unknown_hold(self):
        try:
            import torch
        except ImportError:
            self.skipTest("PyTorch unavailable")
        class Engine:
            model = object()
            def vector(self, text):
                index = 0 if text.startswith("量子力学") or text.startswith("量子") else (
                    1 if "CUDA" in text or "GPU" in text else (
                    2 if "文学" in text else 3))
                vectors = [
                    [1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0],
                    [0.57735, 0.57735, 0.57735],
                ]
                return torch.tensor(vectors[index])
        scheduler = SemanticScheduler(Engine())
        vms = [SimpleNamespace(name=n, online=True) for n in ("VM-A", "VM-B", "VM-C")]
        self.assertEqual(scheduler.route("量子力学", vms).selected, "VM-A")
        self.assertEqual(scheduler.route("CUDA", vms).selected, "VM-B")
        self.assertEqual(scheduler.route("日本文学", vms).selected, "VM-C")
        held = scheduler.route("未登録", vms)
        self.assertIsNone(held.selected)
        self.assertEqual(held.method, "unknown_hold")

if __name__ == "__main__":
    unittest.main()
