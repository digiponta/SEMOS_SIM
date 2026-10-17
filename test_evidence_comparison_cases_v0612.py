import unittest
from prepare_evidence_comparison_v0612 import make_fixtures
from hitl_evidence_comparison_gui_v0611 import pending_rows,choice_record,make_report

class EvidenceCasesV0612(unittest.TestCase):
 def setUp(self):
  self.doc=make_fixtures()
  self.by={x["request_id"].split("SYNTH-")[1]:x for x in self.doc["packets"]}
 def test_four_cases(self):self.assertEqual(len(self.doc["packets"]),4)
 def test_exact(self):
  p=self.by["EXACT_MATCH"];e=p["evidence_comparison"]
  self.assertEqual(e["generated"]["answer"],e["retrieved"]["answer"])
  self.assertEqual(choice_record(p,"RETRIEVED")["selection"],"RETRIEVED")
 def test_different(self):
  p=self.by["DIFFERENT"];e=p["evidence_comparison"]
  self.assertNotEqual(e["generated"]["answer"],e["retrieved"]["answer"])
  self.assertEqual(choice_record(p,"GENERATED")["selection"],"GENERATED")
 def test_no_retrieval(self):
  with self.assertRaises(ValueError):choice_record(self.by["NO_RETRIEVAL"],"RETRIEVED")
 def test_unknown_excluded(self):
  self.assertNotIn(self.by["UNKNOWN"],pending_rows(self.doc))
 def test_unknown_cannot_select(self):
  with self.assertRaises(ValueError):choice_record(self.by["UNKNOWN"],"GENERATED")
 def test_three_reviewable(self):self.assertEqual(len(pending_rows(self.doc)),3)
 def test_no_implicit_approval(self):
  p=self.by["DIFFERENT"]
  report=make_report(b"synthetic",[p],{p["request_id"]:"RETRIEVED"})
  self.assertFalse(report["selections"][0]["approved"])
  self.assertFalse(report["selections"][0]["promoted"])
if __name__=="__main__":unittest.main()
