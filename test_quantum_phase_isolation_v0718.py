import unittest
from quantum_phase_isolation_v0718 import (METHODS,TEMPERATURES,candidate_scores,
                                            search,interval,benchmark)
from semantic_weighted_interference_v0716 import workload
class PhaseIsolationTests(unittest.TestCase):
 def test_methods(self):
  for m in METHODS:
   self.assertEqual(search(workload(16,7,"smooth"),m,6,8)["calls"],6)
 def test_scores(self):
  for m in METHODS:
   indexes,scores=candidate_scores(16,{0:.8},m)
   self.assertEqual(len(indexes),15)
   self.assertEqual(len(scores),15)
 def test_phase_nontrivial(self):
  a=candidate_scores(16,{0:.8},"QI_COMPLEX")[1]
  b=candidate_scores(16,{0:.8},"REAL_AMPLITUDE")[1]
  self.assertNotEqual(a,b)
 def test_full(self):
  for m in METHODS:self.assertEqual(search(workload(16,7,"smooth"),m,16,8)["success"],1)
 def test_interval_zero(self):self.assertEqual(interval([0]*8,100),[0,0])
 def test_interval_order(self):
  lo,hi=interval([-1,1]*10,100);self.assertLessEqual(lo,hi)
 def test_outputs(self):
  r=benchmark(3,4,42,30000,(4,),100)
  self.assertEqual(len(r["results"]),15)
  self.assertEqual(len(r["contrasts"]),12)
 def test_temperature_grid(self):
  r=benchmark(3,4,42,30000,(4,),100)
  self.assertTrue(all(x["selected_temperature"] in TEMPERATURES for x in r["results"]))
 def test_matched_budget(self):
  r=benchmark(3,4,42,30000,(4,),100)
  self.assertTrue(all(x["same_oracle_budget"] for x in r["results"]))
 def test_no_overlap(self):
  with self.assertRaises(ValueError):benchmark(4,4,42,44,(4,),100)
 def test_bad_bootstrap(self):
  with self.assertRaises(ValueError):benchmark(3,4,42,30000,(4,),50)
 def test_bad_budget(self):
  with self.assertRaises(ValueError):benchmark(3,4,42,30000,(80,),100)
 def test_bad_temp(self):
  with self.assertRaises(ValueError):search(workload(16,7,"smooth"),"QI_COMPLEX",4,8,0)
 def test_random_regret(self):self.assertGreaterEqual(search(workload(16,7,"smooth"),"RANDOM",4,8)["regret"],0)
 def test_strength_negative(self):
  with self.assertRaises(ValueError):candidate_scores(16,{0:.8},"QI_COMPLEX",-1)
 def test_holdout_seed(self):
  self.assertEqual(benchmark(3,4,42,30000,(4,),100)["parameters"]["holdout_seed"],30000)
if __name__=="__main__":unittest.main()
