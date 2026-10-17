"""v0.6.7 tests: preserve rejected answer separately, fail closed."""
import unittest
from prepare_vm_transport_fixture_v062 import make_fixture
from vm_http_transport_v063 import dispatch_live

class RejectedReplyDiagnosticTests(unittest.TestCase):
    def packet(self):
        return make_fixture()["packets"][0]
    def config(self):
        return {"version":"0.6.3","vms":{v:{"transport":"http-loopback","url":"http://127.0.0.1:8765/answer","timeout_ms":30000} for v in ("VM-A","VM-B","VM-C")}}
    def reply(self,request,answer):
        return {"protocol":"semos.vm.v1","request_id":request["request_id"],
            "source_vm":request["target_vm"],"question":request["question"],
            "answer":answer,"execution_id":"test-execution-01",
            "executed_at":"2026-10-17T13:00:00+09:00"}
    def run_reply(self,answer):
        p=self.packet()
        original=p["answer"]
        out=dispatch_live(p,self.config(),True,
            lambda request,settings:self.reply(request,answer))
        return original,out
    def test_short_reply_separately_preserved(self):
        original,out=self.run_reply("はい。")
        self.assertEqual(out["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
        self.assertEqual(out["answer"],original)
        d=out["rejected_reply_diagnostic"]
        self.assertEqual(d["answer"],"はい。")
        self.assertEqual(d["character_count"],3)
        self.assertEqual(d["validation_error"],"TOO_SHORT")
        self.assertFalse(d["trusted"])
        self.assertFalse(d["eligible_for_hitl"])
    def test_empty_reply(self):
        original,out=self.run_reply("")
        self.assertEqual(out["answer"],original)
        self.assertEqual(out["rejected_reply_diagnostic"]["validation_error"],"MISSING_TEXT")
        self.assertEqual(out["rejected_reply_diagnostic"]["character_count"],0)
    def test_placeholder(self):
        original,out=self.run_reply("TODO: 回答待ちです。")
        self.assertEqual(out["answer"],original)
        self.assertEqual(out["rejected_reply_diagnostic"]["validation_error"],"PLACEHOLDER")
    def test_valid_reply_has_no_rejected_diagnostic(self):
        _,out=self.run_reply("量子力学は微視的な現象を記述する理論です。")
        self.assertEqual(out["status"],"PENDING_USER_REVIEW")
        self.assertNotIn("rejected_reply_diagnostic",out)
    def test_mismatch_fails_without_diagnostic(self):
        def wrong(request,settings):
            r=self.reply(request,"短い。")
            r["request_id"]="wrong"
            return r
        with self.assertRaises(ValueError):
            dispatch_live(self.packet(),self.config(),True,wrong)
if __name__=="__main__":
    unittest.main()
