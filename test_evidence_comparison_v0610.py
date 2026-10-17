import unittest
from prepare_vm_transport_fixture_v062 import make_fixture
from vm_http_transport_v063 import dispatch_live

class EvidenceComparisonTests(unittest.TestCase):
 def config(self):
  return {"version":"0.6.3","vms":{v:{"transport":"http-loopback","url":"http://127.0.0.1:8765/answer","timeout_ms":30000} for v in ("VM-A","VM-B","VM-C")}}
 def call(self,state,relation):
  p=make_fixture()["packets"][0]
  def fetch(req,settings):
   return {"protocol":"semos.vm.v1","request_id":req["request_id"],"source_vm":req["target_vm"],
    "question":req["question"],"answer":"量子力学は微視的な現象を記述する理論です。",
    "execution_id":"v0610-001","executed_at":"2026-10-17T13:00:00+09:00",
    "semantic_assessment":{"state":state,"verified":False,"full_unknown_gate_applied":False},
    "evidence_comparison":{"generated":{"answer":"量子力学は微視的な現象を記述する理論です。","origin":"LLM_TRY_CHECKPOINT"},
     "retrieved":{"answer":None,"origin":"LLM_TRY_LOCAL_SEMANTIC_KNOWLEDGE","present":False},
     "relation":relation,"verified":False,"requires_human_review":True}}
  return p,dispatch_live(p,self.config(),True,fetch)
 def test_unverified_keeps_comparison(self):
  _,out=self.call("UNVERIFIED","NO_RETRIEVAL")
  self.assertEqual(out["status"],"PENDING_USER_REVIEW")
  self.assertEqual(out["evidence_comparison"]["relation"],"NO_RETRIEVAL")
 def test_unknown_keeps_comparison_but_rejects(self):
  p,out=self.call("UNKNOWN","NO_RETRIEVAL")
  self.assertEqual(out["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
  self.assertEqual(out["answer"],p["answer"])
  self.assertEqual(out["evidence_comparison"]["relation"],"NO_RETRIEVAL")
 def test_known_still_needs_user_review(self):
  _,out=self.call("KNOWN","EXACT_MATCH")
  self.assertEqual(out["status"],"PENDING_USER_REVIEW")
 def test_invalid_relation_rejected(self):
  with self.assertRaises(ValueError):self.call("UNVERIFIED","TRUSTED")
if __name__=="__main__":unittest.main()
