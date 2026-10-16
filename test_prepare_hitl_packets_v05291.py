import unittest
from prepare_hitl_packets_v05291 import review
class PacketTests(unittest.TestCase):
 def row(self,final="VM-A",visits=None):
  return {"request_id":"R1","final":final,"events":[{"state":"DISPATCH","vm":v} for v in (visits or [])]}
 def payload(self):return {"question":"question","answer":"answer"}
 def test_requires_real_payload(self):
  self.assertEqual(review(self.row())["status"],"AWAITING_ANSWER_PAYLOAD")
  with self.assertRaises(ValueError):review(self.row(),"APPROVE")
 def test_pending(self):
  self.assertEqual(review(self.row(),payload=self.payload())["status"],"PENDING_USER_REVIEW")
 def test_explicit_confirmation(self):
  self.assertEqual(review(self.row(),"APPROVE",self.payload())["status"],"USER_CONFIRMED")
 def test_retry_avoids_visited(self):
  p=review(self.row("VM-A",["VM-C","VM-A"]),"RETRY",self.payload())
  self.assertEqual(p["retry_vm"],"VM-B")
 def test_retry_exhausted(self):
  p=review(self.row("VM-C",["VM-A","VM-B","VM-C"]),"RETRY",self.payload())
  self.assertEqual(p["status"],"DISCOVERY")
 def test_discovery_no_decision(self):
  self.assertEqual(review(self.row("DISCOVERY"))["status"],"DISCOVERY")
  with self.assertRaises(ValueError):review(self.row("DISCOVERY"),"APPROVE",self.payload())
if __name__=="__main__":unittest.main()
