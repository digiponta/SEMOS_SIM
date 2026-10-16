import unittest
from run_hitl_retry_v05293 import advance
class RetryTests(unittest.TestCase):
 def pkt(self,visited=("VM-A",),target="VM-B"):
  return {"request_id":"X","vm":"VM-A","question":"Q","answer":"old","decision":"RETRY",
          "status":"RETRY_HANDOFF_PENDING_VM_EXECUTION","retry_vm":target,
          "visited_vms":list(visited),"events":[]}
 def reply(self,vm="VM-B"):return {"vm":vm,"question":"Q","answer":"new"}
 def test_no_reply_stays_pending(self):
  self.assertEqual(advance(self.pkt())["status"],"RETRY_HANDOFF_PENDING_VM_EXECUTION")
 def test_new_reply_requires_new_review(self):
  p=advance(self.pkt(),self.reply())
  self.assertEqual(p["status"],"PENDING_USER_REVIEW")
  self.assertEqual(p["previous_answer"],"old")
  self.assertIsNone(p["decision"])
 def test_confirm_new_reply(self):
  self.assertEqual(advance(self.pkt(),self.reply(),"APPROVE")["status"],"USER_CONFIRMED")
 def test_next_retry_avoids_old_and_new(self):
  p=advance(self.pkt(),self.reply(),"RETRY")
  self.assertEqual(p["retry_vm"],"VM-C")
 def test_last_retry_discovery(self):
  p=advance(self.pkt(("VM-A","VM-C"),"VM-B"),self.reply(),"RETRY")
  self.assertEqual(p["status"],"DISCOVERY")
 def test_wrong_vm_rejected(self):
  with self.assertRaises(ValueError):advance(self.pkt(),self.reply("VM-C"))
 def test_changed_question_rejected(self):
  x=self.reply();x["question"]="DIFFERENT"
  with self.assertRaises(ValueError):advance(self.pkt(),x)
 def test_decision_without_response_rejected(self):
  with self.assertRaises(ValueError):advance(self.pkt(),decision="APPROVE")
if __name__=="__main__":unittest.main()
