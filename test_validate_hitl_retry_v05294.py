import unittest
from validate_hitl_retry_v05294 import inspect_reply,process
from hitl_retry_review_gui_v05294 import pending_rows

class V05294Tests(unittest.TestCase):
 def packet(self):
  return {"request_id":"R1","status":"RETRY_HANDOFF_PENDING_VM_EXECUTION",
          "vm":"VM-A","retry_vm":"VM-B","question":"量子力学とは何ですか","answer":"以前の回答です",
          "visited_vms":["VM-A"],"decision":"RETRY","events":[]}
 def reply(self):
  return {"vm":"VM-B","question":"量子力学とは何ですか",
          "answer":"量子現象の状態と観測を数学的に記述する理論です。",
          "execution_id":"vm-b-run-1","executed_at":"2026-10-17T10:00:00+09:00","source":"manual-captured-vm"}
 def test_placeholder_quarantined(self):
  r=self.reply();r["answer"]="ここにVM-Cの実際の回答を入力"
  p=process(self.packet(),r)
  self.assertEqual(p["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
  self.assertEqual(p["validation_error"],"PLACEHOLDER")
 def test_provenance_required(self):
  r=self.reply();r.pop("execution_id")
  self.assertEqual(inspect_reply(r),"MISSING_PROVENANCE_EXECUTION_ID")
 def test_fresh_review(self):
  p=process(self.packet(),self.reply())
  self.assertEqual(p["status"],"PENDING_USER_REVIEW")
  self.assertIsNone(p["decision"])
  self.assertFalse(p["provenance_verified"])
  self.assertEqual(len(pending_rows({"packets":[p]})),1)
 def test_wrong_vm_denied(self):
  r=self.reply();r["vm"]="VM-C"
  with self.assertRaises(ValueError):process(self.packet(),r)
 def test_timestamp_validation(self):
  r=self.reply();r["executed_at"]="yesterday"
  self.assertEqual(inspect_reply(r),"INVALID_TIMESTAMP")
 def test_no_implicit_approval(self):
  self.assertEqual(process(self.packet())["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
if __name__=="__main__":unittest.main()
