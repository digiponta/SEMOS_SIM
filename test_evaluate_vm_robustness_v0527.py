import unittest
from evaluate_vm_robustness_v0527 import run,aggregate,coin
class RobustnessTests(unittest.TestCase):
 def setUp(self):
  self.rows=[{"request_id":"A","gold":"VM-A","accepted":False,"candidate":"VM-B"},
             {"request_id":"U","gold":"UNKNOWN","accepted":False,"candidate":"VM-C"}]
  self.approvals={"A":True,"U":True}
 def test_reproducible(self):
  self.assertEqual(run(self.rows,self.approvals,.1,.1,527,1,3),
                   run(self.rows,self.approvals,.1,.1,527,1,3))
 def test_ideal(self):
  result=run(self.rows,self.approvals,0,0,527,0,3)
  self.assertEqual(result["known_correct"],1)
  self.assertEqual(result["unknown_discovery"],1)
 def test_all_false_accept(self):
  result=run(self.rows,self.approvals,1,0,527,0,3)
  self.assertEqual(result["unknown_false_commit"],1)
 def test_all_false_reject(self):
  result=run(self.rows,self.approvals,0,1,527,0,3)
  self.assertEqual(result["known_discovery"],1)
 def test_aggregate(self):
  self.assertEqual(aggregate([{"x":1},{"x":3}])["x"]["mean"],2)
 def test_coin_range(self):
  self.assertTrue(0<=coin(1,1,"A","VM-A","FA")<1)
if __name__=="__main__":unittest.main()
