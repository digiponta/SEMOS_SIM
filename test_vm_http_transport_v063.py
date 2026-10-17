import unittest
from vm_http_transport_v063 import verify_endpoint,verify_live_config,validate_response,dispatch_live
from prepare_vm_transport_fixture_v062 import make_fixture

class HTTPTransportTests(unittest.TestCase):
 def config(self):
  return {"version":"0.6.3","vms":{v:{"transport":"http-loopback","url":"http://127.0.0.1:8765/answer","timeout_ms":1000} for v in ("VM-A","VM-B","VM-C")}}
 def request(self):return make_fixture()["packets"][0]
 def response(self,req):
  return {"protocol":"semos.vm.v1","request_id":req["request_id"],"source_vm":req["target_vm"],
          "question":req["question"],"answer":"量子状態と観測を記述する理論です。",
          "execution_id":"local-run-001","executed_at":"2026-10-17T12:00:00+09:00"}
 def test_loopback(self):self.assertEqual(verify_endpoint("http://127.0.0.1:8765/answer"),"http://127.0.0.1:8765/answer")
 def test_remote_forbidden(self):
  with self.assertRaises(ValueError):verify_endpoint("http://example.com:80/answer")
 def test_redirect_target_forbidden(self):
  with self.assertRaises(ValueError):verify_endpoint("http://localhost:1234/redirect")
 def test_credentials_forbidden(self):
  with self.assertRaises(ValueError):verify_endpoint("http://user:secret@localhost:1234/answer")
 def test_live_opt_in_required(self):
  with self.assertRaises(ValueError):dispatch_live(self.request(),self.config())
 def test_valid_response(self):
  p=dispatch_live(self.request(),self.config(),True,lambda request,settings:self.response(request))
  self.assertEqual(p["status"],"PENDING_USER_REVIEW")
  self.assertEqual(p["transport"],"HTTP_LOOPBACK_UNVERIFIED")
 def test_mismatch(self):
  def fake(request,settings):
   d=self.response(request);d["request_id"]="wrong";return d
  with self.assertRaises(ValueError):dispatch_live(self.request(),self.config(),True,fake)
 def test_failed_connection(self):
  def offline(request,settings):raise ConnectionError("offline")
  p=dispatch_live(self.request(),self.config(),True,offline)
  self.assertEqual(p["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
 def test_bad_config(self):
  c=self.config();c["vms"]["VM-B"]["url"]="http://192.168.1.10:8000/answer"
  with self.assertRaises(ValueError):verify_live_config(c)
if __name__=="__main__":unittest.main()
