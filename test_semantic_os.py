import tempfile
import unittest
from pathlib import Path
from semantic_os import SemanticOS

class SemanticOSTest(unittest.TestCase):
    def setUp(self):
        self.os = SemanticOS()

    def teach(self):
        self.assertEqual(self.os.submit("/teach 量子センサー | は | センサー").state, "DONE")
        self.assertEqual(self.os.submit("/approve 量子センサー|は|センサー").state, "DONE")

    def test_pending_approval_and_query(self):
        self.assertEqual(self.os.submit("未知とは").intent, "unknown")
        self.teach()
        self.assertIn("UNVERIFIED", self.os.submit("量子センサーとは").result)

    def test_sync_and_sleep(self):
        self.teach()
        self.assertTrue(self.os.sync()["ok"])
        self.assertEqual(self.os.sleep()["mode"], "SIMULATED_NO_WEIGHT_UPDATES")
        self.assertEqual(len(self.os.vms[0].internalized_keys), 1)

    def test_quorum_gate(self):
        self.os.vms[1].online = False
        self.os.vms[2].online = False
        self.assertFalse(self.os.sync()["ok"])
        self.assertFalse(self.os.sleep()["ok"])

    def test_dummy_vm_failure(self):
        self.os.vms[0].online = False
        self.assertEqual(self.os.submit("/status").state, "FAILED")

    def test_persistence(self):
        self.teach()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            self.os.save(path)
            other = SemanticOS()
            other.load(path)
            self.assertEqual(len(other.canonical), 1)

if __name__ == "__main__":
    unittest.main()
