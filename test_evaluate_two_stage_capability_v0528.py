import unittest
from evaluate_two_stage_capability_v0528 import evaluate,stage_status
class TwoStageTests(unittest.TestCase):
 def setUp(self):
  self.traces=[{"request_id":"K","gold":"VM-A","accepted":False,"candidate":"VM-B"},
               {"request_id":"U","gold":"UNKNOWN","accepted":False,"candidate":"VM-B"}]
  self.approvals={"K":True,"U":True}
 def test_ideal(self):
  for mode in ("single","independent","mixed","shared"):
   s=evaluate(self.traces,self.approvals,0,0,mode,528,0,3)
   self.assertEqual(s["known_correct"],1)
   self.assertEqual(s["unknown_discovery"],1)
 def test_reproducible(self):
  a=evaluate(self.traces,self.approvals,.10,.10,"mixed",528,3,3)
  b=evaluate(self.traces,self.approvals,.10,.10,"mixed",528,3,3)
  self.assertEqual(a,b)
 def test_perfect_correlation_same_as_single(self):
  for n in range(15):
   single=evaluate(self.traces,self.approvals,.2,.2,"single",528,n,3)
   shared=evaluate(self.traces,self.approvals,.2,.2,"shared",528,n,3)
   for key in ("known_correct","unknown_discovery","known_wrong_commit"):
    self.assertEqual(single[key],shared[key])
 def test_second_stage_rejection(self):
  self.assertEqual(stage_status(False,1,0.5),"ACCEPTED")
  self.assertEqual(stage_status(True,1,0.5),"NOT_SUPPORTED")
 def test_bad_mode(self):
  with self.assertRaises(ValueError):evaluate(self.traces,self.approvals,0,0,"garbage",528,0,3)
if __name__=="__main__":unittest.main()
