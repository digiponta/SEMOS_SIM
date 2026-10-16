import unittest
from compare_and_or_gate_v0523 import evaluate_logic
class GateLogicTests(unittest.TestCase):
 def setUp(self):
  self.ecdf={"VM-A":[.2,.4,.6,.8]}
 def test_margin_only_or_rescues(self):
  row={"request_id":"a","best_vm":"VM-A","score":.4,"margin":.09}
  self.assertEqual(evaluate_logic(row,self.ecdf,.76,.06,"AND")[0],"UNKNOWN")
  self.assertEqual(evaluate_logic(row,self.ecdf,.76,.06,"OR")[0],"VM-A")
 def test_ecdf_only_or_rescues(self):
  row={"request_id":"a","best_vm":"VM-A","score":.8,"margin":.01}
  self.assertEqual(evaluate_logic(row,self.ecdf,.76,.06,"AND")[0],"UNKNOWN")
  self.assertEqual(evaluate_logic(row,self.ecdf,.76,.06,"OR")[0],"VM-A")
 def test_neither_rejects(self):
  row={"request_id":"a","best_vm":"VM-A","score":.1,"margin":.01}
  self.assertEqual(evaluate_logic(row,self.ecdf,.76,.06,"OR")[0],"UNKNOWN")
if __name__=="__main__":unittest.main()
