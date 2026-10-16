import unittest
from mock_vm_transport_v05297 import fetch_mock,route

class MockVmTransportTests(unittest.TestCase):
 def packet(self):
  return {"request_id":"EVALA001","vm":"VM-A","retry_vm":"VM-C",
   "question":"量子力学とは何ですか","answer":"以前の仮回答です。",
   "status":"RETRY_HANDOFF_PENDING_VM_EXECUTION",
   "visited_vms":["VM-B","VM-A"],"decision":"RETRY","events":[]}
 def fixture(self,simulate=""):
  return {"request_id":"EVALA001","vm":"VM-C",
   "question":"量子力学とは何ですか","answer":"量子状態の変化と観測を記述する物理理論です。",
   "execution_id":"mock-run-1","executed_at":"2026-10-17T12:00:00+09:00",
   "simulate":simulate}
 def test_mock_response_review(self):
  r=route(self.packet(),{"EVALA001":self.fixture()})
  self.assertEqual(r["status"],"PENDING_USER_REVIEW")
  self.assertEqual(r["transport"],"MOCK_ONLY")
  self.assertIsNone(r["decision"])
  self.assertFalse(r["provenance_verified"])
 def test_missing_fixture_stays_pending(self):
  self.assertEqual(route(self.packet(),{})["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
 def test_timeout_stays_pending(self):
  p=route(self.packet(),{"EVALA001":self.fixture("timeout")})
  self.assertEqual(p["transport_error"],"TimeoutError")
  self.assertEqual(p["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
 def test_connection_failure(self):
  p=route(self.packet(),{"EVALA001":self.fixture("connection_error")})
  self.assertEqual(p["transport_error"],"ConnectionError")
 def test_wrong_vm(self):
  x=self.fixture();x["vm"]="VM-B"
  with self.assertRaises(ValueError):route(self.packet(),{"EVALA001":x})
 def test_wrong_question(self):
  x=self.fixture();x["question"]="違う質問"
  with self.assertRaises(ValueError):route(self.packet(),{"EVALA001":x})
 def test_completed_status_not_replayed(self):
  p=self.packet();p["status"]="USER_CONFIRMED"
  self.assertEqual(route(p,{"EVALA001":self.fixture()}),p)
 def test_placeholder_not_reviewable(self):
  x=self.fixture();x["answer"]="ここにVM-Cの実際の回答を入力"
  p=route(self.packet(),{"EVALA001":x})
  self.assertEqual(p["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
  self.assertEqual(p["validation_error"],"PLACEHOLDER")
if __name__=="__main__":unittest.main()
