import unittest
from intake_hitl_retry_v05295 import diagnose,intake
class IntakeTests(unittest.TestCase):
 def record(self):return {"request_id":"EVALA001","status":"RETRY_HANDOFF_PENDING_VM_EXECUTION","retry_vm":"VM-C","question":"量子力学とは何ですか"}
 def test_blank_template_detected(self):
  reply={"vm":"VM-C","question":"量子力学とは何ですか","answer":"","execution_id":"","executed_at":"","source":""}
  d=diagnose({"packets":[self.record()]},{"EVALA001":reply})
  self.assertEqual(d[0]["state"],"MISSING_TEXT")
 def test_missing_record(self):
  self.assertEqual(diagnose({"packets":[self.record()]},{})[0]["state"],"MISSING_REPLY_RECORD")
 def test_valid(self):
  row=intake(self.record(),"EVALA001","VM-C","量子状態を数学的に記述する理論です","vm-c-0001","2026-10-17T12:00:00+09:00","captured_vm_output")
  self.assertEqual(row["vm"],"VM-C")
 def test_no_placeholder(self):
  with self.assertRaises(ValueError):intake(self.record(),"EVALA001","VM-C","ここにVM-Cの実際の回答を入力","vm-c-0001","2026-10-17T12:00:00+09:00","captured_vm_output")
 def test_wrong_vm(self):
  with self.assertRaises(ValueError):intake(self.record(),"EVALA001","VM-A","回答文章を登録します","run-001","2026-10-17T12:00:00+09:00","captured_vm_output")
if __name__=="__main__":unittest.main()
