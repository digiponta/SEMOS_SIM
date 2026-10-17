import unittest
from hitl_evidence_comparison_gui_v0611 import choice_record,make_report
from prepare_evidence_comparison_v0612 import packet
class AuditV0613(unittest.TestCase):
 def test_reason_saved(self):
  d=choice_record(packet("DIFFERENT"),"RETRIEVED","検索結果の説明が明確")
  self.assertEqual(d["reason"],"検索結果の説明が明確")
  self.assertTrue(d["recorded_at"].endswith("+00:00"))
  self.assertFalse(d["approved"])
 def test_relation(self):
  d=choice_record(packet("EXACT_MATCH"),"GENERATED","同じ内容")
  self.assertEqual(d["evidence_relation"],"EXACT_MATCH")
 def test_reason_length(self):
  with self.assertRaises(ValueError):choice_record(packet("DIFFERENT"),"HOLD","x"*2001)
 def test_report(self):
  p=packet("DIFFERENT")
  report=make_report(b"synthetic",[p],{p["request_id"]:"REJECT_BOTH"},{p["request_id"]:"相違がある"})
  self.assertEqual(report["selections"][0]["reason"],"相違がある")
  self.assertFalse(report["selections"][0]["promoted"])
 def test_unknown_still_blocked(self):
  with self.assertRaises(ValueError):choice_record(packet("UNKNOWN"),"GENERATED","不明")
if __name__=="__main__":unittest.main()
