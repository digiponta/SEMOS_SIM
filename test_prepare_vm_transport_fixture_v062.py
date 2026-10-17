import unittest
from prepare_vm_transport_fixture_v062 import make_fixture
from vm_transport_v061 import validate_config,dispatch

class V062Tests(unittest.TestCase):
 def config(self):
  return validate_config({"version":"0.6.1","vms":{k:{"transport":"mock","timeout_ms":5000} for k in ("VM-A","VM-B","VM-C")}})
 def reply(self):
  return {"request_id":"EVALA001","vm":"VM-C","question":"量子力学とは何ですか",
    "answer":"量子状態の変化と観測を記述する物理理論です。",
    "execution_id":"synthetic-mock-001","executed_at":"2026-10-17T12:00:00+09:00","simulate":""}
 def test_fixture_state(self):
  doc=make_fixture();self.assertEqual(doc["kind"],"SYNTHETIC_HITL_RETRY_HANDOFF_FIXTURE")
  self.assertEqual(len(doc["packets"]),1)
 def test_visited_history(self):
  p=make_fixture()["packets"][0]
  self.assertNotIn(p["retry_vm"],p["visited_vms"])
 def test_mock_integration(self):
  p=make_fixture()["packets"][0]
  out=dispatch(p,self.config(),{"EVALA001":self.reply()})
  self.assertEqual(out["status"],"PENDING_USER_REVIEW")
  self.assertEqual(out["transport"],"MOCK_ONLY")
  self.assertIsNone(out["decision"] if "decision" in out else None)
 def test_timeout_stays_pending(self):
  p=make_fixture()["packets"][0];f=self.reply();f["simulate"]="timeout"
  o=dispatch(p,self.config(),{"EVALA001":f})
  self.assertEqual(o["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
if __name__=="__main__":unittest.main()
