import unittest
from prepare_vm_transport_fixture_v062 import make_fixture
from vm_http_transport_v063 import dispatch_live
from llm_try_backend_v066 import read_request

class DiagnosticsV068(unittest.TestCase):
 def config(self):
  return {"version":"0.6.3","vms":{v:{"transport":"http-loopback","url":"http://127.0.0.1:8765/answer","timeout_ms":30000} for v in ("VM-A","VM-B","VM-C")}}
 def backend(self,answer):
  def fetch(req,settings):
   return {"protocol":"semos.vm.v1","request_id":req["request_id"],
    "source_vm":req["target_vm"],"question":req["question"],"answer":answer,
    "execution_id":"v068-test-01","executed_at":"2026-10-17T13:00:00+09:00",
    "generation_diagnostic":{"prompt_mode":"llm_try_build_prompt_empty_history",
     "generated_character_count":len(answer),"generated_token_count":1}}
  return fetch
 def test_rejected_diagnostics(self):
  p=make_fixture()["packets"][0]
  res=dispatch_live(p,self.config(),True,self.backend("。"))
  self.assertEqual(res["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
  self.assertEqual(res["answer"],p["answer"])
  d=res["rejected_reply_diagnostic"]
  self.assertEqual(d["answer"],"。")
  self.assertEqual(d["generation_diagnostic"]["generated_token_count"],1)
 def test_accepted_diagnostics(self):
  p=make_fixture()["packets"][0]
  res=dispatch_live(p,self.config(),True,self.backend("量子力学は微視的な現象を記述します。"))
  self.assertEqual(res["status"],"PENDING_USER_REVIEW")
  self.assertIn("generation_diagnostic",res)
 def test_request_contract(self):
  with self.assertRaises(ValueError):read_request({"protocol":"other"})
if __name__=="__main__":unittest.main()
