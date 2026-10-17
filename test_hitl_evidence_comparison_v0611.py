import json,unittest
from hitl_evidence_comparison_gui_v0611 import pending_rows,choice_record,make_report

def packet(retrieved=None):
    return {"request_id":"EVALA001","status":"PENDING_USER_REVIEW","question":"量子力学とは",
     "provenance":{"source":"unverified-http-loopback"},
     "semantic_assessment":{"state":"UNVERIFIED"},
     "evidence_comparison":{"generated":{"answer":"生成回答"},
       "retrieved":{"answer":retrieved,"present":retrieved is not None},
       "relation":"DIFFERENT" if retrieved else "NO_RETRIEVAL"}}
class TestHITLEvidenceGUI(unittest.TestCase):
 def test_pending_only(self):
  p=packet();q=dict(p,status="RETRY_HANDOFF_PENDING_VM_EXECUTION")
  self.assertEqual(pending_rows({"packets":[p,q]}),[p])
 def test_generated_selection_not_approval(self):
  r=choice_record(packet(),"GENERATED")
  self.assertFalse(r["approved"]);self.assertFalse(r["promoted"])
 def test_no_retrieval_cannot_select(self):
  with self.assertRaises(ValueError):choice_record(packet(),"RETRIEVED")
 def test_retrieved_selection(self):
  r=choice_record(packet("検索回答"),"RETRIEVED")
  self.assertEqual(r["selection"],"RETRIEVED")
 def test_reject_both(self):
  self.assertEqual(choice_record(packet(),"REJECT_BOTH")["selection"],"REJECT_BOTH")
 def test_hold(self):
  self.assertEqual(choice_record(packet(),"HOLD")["selection"],"HOLD")
 def test_invalid_choice(self):
  with self.assertRaises(ValueError):choice_record(packet(),"APPROVE")
 def test_duplicate_ids(self):
  with self.assertRaises(ValueError):make_report(b"{}",[packet(),packet()],{})
 def test_report_safe(self):
  report=make_report(b"{}",[packet()],{"EVALA001":"GENERATED"})
  self.assertEqual(report["kind"],"HITL_EVIDENCE_COMPARISON_DRAFT")
  self.assertFalse(report["selections"][0]["approved"])
if __name__=="__main__":unittest.main()
