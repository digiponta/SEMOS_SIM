import unittest
from finalize_hitl_retry_v05296 import apply_decision,apply_all

class FinalizeTests(unittest.TestCase):
 def pending(self,visited=None):
  v=visited or ["VM-A","VM-C"]
  return {"request_id":"EVALA001","status":"PENDING_USER_REVIEW",
    "vm":v[-1],"question":"量子力学とは何ですか",
    "answer":"量子の状態や測定を説明する理論です。",
    "provenance":{"execution_id":"run-001","executed_at":"2026-10-17T12:00:00+09:00","source":"supplied"},
    "provenance_verified":False,"visited_vms":v,"decision":None,"events":[]}
 def test_approve(self):
  r=apply_decision(self.pending(),"APPROVE")
  self.assertEqual(r["status"],"USER_CONFIRMED")
  self.assertFalse(r["provenance_verified"])
 def test_reject(self):
  self.assertEqual(apply_decision(self.pending(),"REJECT")["status"],"USER_REJECTED")
 def test_discovery(self):
  self.assertEqual(apply_decision(self.pending(),"DISCOVERY")["status"],"DISCOVERY")
 def test_retry_unvisited(self):
  r=apply_decision(self.pending(),"RETRY")
  self.assertEqual(r["retry_vm"],"VM-B")
  self.assertEqual(r["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
 def test_retry_exhaustion(self):
  r=apply_decision(self.pending(["VM-B","VM-A","VM-C"]),"RETRY")
  self.assertEqual(r["status"],"DISCOVERY")
  self.assertNotIn("retry_vm",r)
 def test_no_reply_cannot_approve(self):
  p=self.pending();p["answer"]=""
  with self.assertRaises(ValueError):apply_decision(p,"APPROVE")
 def test_not_pending(self):
  p=self.pending();p["status"]="RETRY_HANDOFF_PENDING_VM_EXECUTION"
  with self.assertRaises(ValueError):apply_decision(p,"APPROVE")
 def test_no_decision_preserved(self):
  self.assertEqual(apply_decision(self.pending(),None),self.pending())
 def test_duplicate_review_forbidden(self):
  p=self.pending();p["decision"]="APPROVE"
  with self.assertRaises(ValueError):apply_decision(p,"APPROVE")
 def test_unknown_id_forbidden(self):
  with self.assertRaises(ValueError):apply_all({"version":"0.5.29.4","packets":[self.pending()]},{"OTHER":"APPROVE"})
 def test_valid_all(self):
  p=self.pending()
  doc={"version":"0.5.29.4","packets":[p,{"request_id":"R2","status":"DISCOVERY"}]}
  rows=apply_all(doc,{"EVALA001":"APPROVE"})
  self.assertEqual([x["status"] for x in rows],["USER_CONFIRMED","DISCOVERY"])
if __name__=="__main__":unittest.main()
