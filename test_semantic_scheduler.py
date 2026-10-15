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

if __name__ == "__main__":
    unittest.main()
