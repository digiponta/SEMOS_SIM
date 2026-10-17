import unittest,sys
from pathlib import Path
from llm_backend_http_v065 import invoke_backend,backend_response
class BackendTests(unittest.TestCase):
 def req(self):return {"protocol":"semos.vm.v1","request_id":"R1","target_vm":"VM-C","question":"量子力学とは何ですか","operation":"ANSWER_ONLY","side_effects_allowed":False}
 def argv(self):return [str(Path(sys.executable).resolve()),str(Path("synthetic_llm_backend_v065.py").resolve())]
 def test_stub_invocation(self):
  r=invoke_backend(self.req(),self.argv())
  self.assertEqual(r["request_id"],"R1")
 def test_wrapped_response(self):
  self.assertEqual(backend_response(self.req(),"VM-C",self.argv(),5)["response_kind"],"EXTERNAL_SUBPROCESS_UNVERIFIED")
 def test_wrong_target(self):
  with self.assertRaises(ValueError):backend_response(self.req(),"VM-A",self.argv(),5)
 def test_no_side_effect(self):
  q=self.req();q["side_effects_allowed"]=True
  with self.assertRaises(ValueError):backend_response(q,"VM-C",self.argv(),5)
 def test_missing_backend(self):
  with self.assertRaises(ValueError):invoke_backend(self.req(),[str(Path(sys.executable).resolve()),str(Path("missing_backend.py").resolve())])
if __name__=="__main__":unittest.main()
