import unittest
from prepare_vm_transport_fixture_v062 import make_fixture
from vm_http_transport_v063 import dispatch_live

class SemanticGateV069(unittest.TestCase):
 def config(self):
  return {"version":"0.6.3","vms":{v:{"transport":"http-loopback","url":"http://127.0.0.1:8765/answer","timeout_ms":30000} for v in ("VM-A","VM-B","VM-C")}}
 def dispatch(self,state,answer="量子力学は微視的な現象を記述する理論です。"):
  p=make_fixture()["packets"][0]
  def fetch(req,settings):
   return {"protocol":"semos.vm.v1","request_id":req["request_id"],"source_vm":req["target_vm"],
           "question":req["question"],"answer":answer,"execution_id":"semantic-v069-01",
           "executed_at":"2026-10-17T13:00:00+09:00",
           "semantic_assessment":{"state":state,"reason":"test","verified":False,
           "full_unknown_gate_applied":False}}
  return p,dispatch_live(p,self.config(),True,fetch)
 def test_unknown_remains_retry_pending(self):
  original,out=self.dispatch("UNKNOWN")
  self.assertEqual(out["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
  self.assertEqual(out["answer"],original["answer"])
  self.assertEqual(out["validation_error"],"UNKNOWN_SEMANTIC")
  self.assertEqual(out["rejected_reply_diagnostic"]["eligible_for_hitl"],False)
 def test_unverified_requires_review(self):
  p,out=self.dispatch("UNVERIFIED")
  self.assertEqual(out["status"],"PENDING_USER_REVIEW")
  self.assertFalse(out["semantic_assessment"]["verified"])
 def test_known_still_requires_review(self):
  p,out=self.dispatch("KNOWN")
  self.assertEqual(out["status"],"PENDING_USER_REVIEW")
 def test_unknown_diagnostic_never_overwrites_source(self):
  p,out=self.dispatch("UNKNOWN","短い。")
  self.assertEqual(out["answer"],p["answer"])
  self.assertEqual(out["rejected_reply_diagnostic"]["answer"],"短い。")
 def test_invalid_state_fails_closed(self):
  with self.assertRaises(ValueError):self.dispatch("TRUSTED")
if __name__=="__main__":unittest.main()
