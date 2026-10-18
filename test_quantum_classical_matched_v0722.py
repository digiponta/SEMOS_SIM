import unittest,math
from quantum_classical_matched_v0722 import choose,evaluate,METHODS
from semantic_weighted_interference_v0716 import workload
class MatchedTests(unittest.TestCase):
 def setUp(self):
  self.n=16;self.v=workload(16,42,"smooth");self.seen={0:self.v[0],3:self.v[3],5:self.v[5],7:self.v[7]}
 def test_methods(self):
  for m in METHODS:
   index,_=choose(self.n,self.seen,m,42,1)
   self.assertNotIn(index,self.seen)
 def test_reproducible(self):
  self.assertEqual(choose(self.n,self.seen,"QI_PHASE_DIFFUSION",42,1),
                   choose(self.n,self.seen,"QI_PHASE_DIFFUSION",42,1))
 def test_unitary_norm(self):
  for r in range(4):
   _,err=choose(self.n,self.seen,"QI_PHASE_DIFFUSION",42,r)
   self.assertLess(err,1e-9)
 def test_qi_phase_only(self):
  for r in range(4):
   index,_=choose(self.n,self.seen,"QI_PHASE_ONLY",42,r)
   self.assertNotIn(index,self.seen)
 def test_no_rounds(self):
  index,_=choose(self.n,self.seen,"QI_PHASE_DIFFUSION",42,0)
  self.assertNotIn(index,self.seen)
 def test_rows(self):
  r=evaluate(8,3,99,2,(0,1),100)
  self.assertEqual(len(r["results"]),3*(3+4))
 def test_comparisons(self):
  r=evaluate(8,3,99,2,(0,1),100)
  self.assertEqual(len(r["comparisons"]),3*2*4)
 def test_equal_calls(self):
  r=evaluate(8,3,99,2,(0,1),100)
  self.assertTrue(all(x["equal_oracle_calls"] for x in r["results"]))
 def test_pilot_same_across_methods(self):
  rows=evaluate(8,3,99,2,(0,1),100)["results"]
  for kind in ("smooth","shuffled","multimodal"):
   vals=[x["pilot_optimum_rate"] for x in rows if x["landscape"]==kind]
   self.assertEqual(len(set(vals)),1)
 def test_deterministic_quality(self):
  a=evaluate(8,3,99,2,(0,1),100)
  b=evaluate(8,3,99,2,(0,1),100)
  self.assertEqual([(r["final_success"],r["mean_final_regret"]) for r in a["results"]],
                   [(r["final_success"],r["mean_final_regret"]) for r in b["results"]])
 def test_invalid_pilot(self):
  with self.assertRaises(ValueError):evaluate(8,3,99,8,(0,1),100)
 def test_invalid_round(self):
  with self.assertRaises(ValueError):choose(16,self.seen,"QI_PHASE_DIFFUSION",42,-1)
 def test_invalid_temp(self):
  with self.assertRaises(ValueError):choose(16,self.seen,"KERNEL_SOFTMAX",42,0,0)
 def test_bad_method(self):
  with self.assertRaises(ValueError):choose(16,self.seen,"bad",42)
 def test_rows_norm(self):
  self.assertTrue(all(x["max_norm_error"]<1e-9 for x in evaluate(8,3,99,2,(0,1),100)["results"]))
 def test_qi_same_zero_round(self):
  a=choose(16,self.seen,"QI_PHASE_ONLY",42,0)[0]
  b=choose(16,self.seen,"QI_PHASE_DIFFUSION",42,0)[0]
  self.assertEqual(a,b)
if __name__=="__main__":unittest.main()
