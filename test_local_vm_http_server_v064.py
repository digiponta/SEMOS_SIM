import json,threading,unittest,urllib.request
from http.server import ThreadingHTTPServer
from local_vm_http_server_v064 import answer_request,make_handler
from vm_http_transport_v063 import dispatch_live
from prepare_vm_transport_fixture_v062 import make_fixture

class LocalServerTests(unittest.TestCase):
 def config(self,port):
  return {"version":"0.6.3","vms":{vm:{"transport":"http-loopback","url":f"http://127.0.0.1:{port}/answer","timeout_ms":1500} for vm in ("VM-A","VM-B","VM-C")}}
 def test_synthetic_label(self):
  a=answer_request({"protocol":"semos.vm.v1","request_id":"R1","target_vm":"VM-C","question":"質問","operation":"ANSWER_ONLY","side_effects_allowed":False},"VM-C")
  self.assertEqual(a["response_kind"],"SYNTHETIC_TEST_ONLY")
 def test_wrong_target(self):
  q={"protocol":"semos.vm.v1","request_id":"R1","target_vm":"VM-A","question":"質問","operation":"ANSWER_ONLY","side_effects_allowed":False}
  with self.assertRaises(ValueError):answer_request(q,"VM-C")
 def test_side_effects_forbidden(self):
  q={"protocol":"semos.vm.v1","request_id":"R1","target_vm":"VM-C","question":"質問","operation":"ANSWER_ONLY","side_effects_allowed":True}
  with self.assertRaises(ValueError):answer_request(q,"VM-C")
 def test_real_loopback_roundtrip(self):
  server=ThreadingHTTPServer(("127.0.0.1",0),make_handler("VM-C"))
  runner=threading.Thread(target=server.serve_forever,daemon=True);runner.start()
  try:
   result=dispatch_live(make_fixture()["packets"][0],self.config(server.server_address[1]),True)
   self.assertEqual(result["status"],"PENDING_USER_REVIEW")
   self.assertEqual(result["transport"],"HTTP_LOOPBACK_UNVERIFIED")
   self.assertIsNone(result["decision"])
  finally:
   server.shutdown();server.server_close();runner.join(timeout=3)
if __name__=="__main__":unittest.main()
