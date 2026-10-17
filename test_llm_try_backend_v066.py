import json, tempfile, unittest
from pathlib import Path
from llm_try_backend_v066 import read_request,resolve_model_paths

class LLMTRYBackendTests(unittest.TestCase):
 def req(self):
  return {"protocol":"semos.vm.v1","request_id":"R1","target_vm":"VM-C","question":"量子力学とは",
  "operation":"ANSWER_ONLY","side_effects_allowed":False}
 def test_valid_request(self):self.assertEqual(read_request(self.req())["request_id"],"R1")
 def test_side_effect_rejected(self):
  q=self.req();q["side_effects_allowed"]=True
  with self.assertRaises(ValueError):read_request(q)
 def test_invalid_vm_rejected(self):
  q=self.req();q["target_vm"]="VM-D"
  with self.assertRaises(ValueError):read_request(q)
 def test_invalid_protocol_rejected(self):
  q=self.req();q["protocol"]="unknown"
  with self.assertRaises(ValueError):read_request(q)
 def test_missing_checkpoint(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/"chat.py").write_text("pass",encoding="utf-8")
   with self.assertRaises(FileNotFoundError):resolve_model_paths(root,root/"not.pt",root/"not.json")
if __name__=="__main__":unittest.main()
