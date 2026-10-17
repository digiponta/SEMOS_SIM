import unittest
from vm_transport_v061 import validate_config,envelope,dispatch

class TransportContractTests(unittest.TestCase):
 def config(self):
  return {"version":"0.6.1","vms":{v:{"transport":"mock","timeout_ms":5000} for v in ("VM-A","VM-B","VM-C")}}
 def packet(self):
  return {"request_id":"EVALA001","status":"RETRY_HANDOFF_PENDING_VM_EXECUTION","vm":"VM-A","retry_vm":"VM-C","question":"量子力学とは何ですか","answer":"前の答え","visited_vms":["VM-B","VM-A"],"events":[]}
 def fixture(self):
  return {"request_id":"EVALA001","vm":"VM-C","question":"量子力学とは何ですか","answer":"微視的な物理現象を記述する理論です。","execution_id":"mock-run","executed_at":"2026-10-17T12:00:00+09:00","simulate":""}
 def test_config(self):self.assertEqual(validate_config(self.config())["version"],"0.6.1")
 def test_disallow_http(self):
  c=self.config();c["vms"]["VM-A"]["transport"]="http"
  with self.assertRaises(ValueError):validate_config(c)
 def test_timeout_bounds(self):
  c=self.config();c["vms"]["VM-A"]["timeout_ms"]=0
  with self.assertRaises(ValueError):validate_config(c)
 def test_envelope(self):
  e=envelope(self.packet());self.assertEqual(e["target_vm"],"VM-C");self.assertFalse(e["side_effects_allowed"])
 def test_no_revisit(self):
  p=self.packet();p["visited_vms"].append("VM-C")
  with self.assertRaises(ValueError):envelope(p)
 def test_mock_reply_remains_unapproved(self):
  p=dispatch(self.packet(),self.config(),{"EVALA001":self.fixture()})
  self.assertEqual(p["status"],"PENDING_USER_REVIEW")
  self.assertEqual(p["transport"],"MOCK_ONLY")
  self.assertEqual(p["response_envelope"]["request_id"],"EVALA001")
 def test_timeout_maintains_handoff(self):
  f=self.fixture();f["simulate"]="timeout"
  p=dispatch(self.packet(),self.config(),{"EVALA001":f})
  self.assertEqual(p["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
 def test_mismatch_rejected(self):
  f=self.fixture();f["vm"]="VM-A"
  with self.assertRaises(ValueError):dispatch(self.packet(),self.config(),{"EVALA001":f})
if __name__=="__main__":unittest.main()
