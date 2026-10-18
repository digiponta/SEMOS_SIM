import unittest
from quantum_holdout_v0717 import trial,paired_interval,benchmark,METHODS
from semantic_weighted_interference_v0716 import workload
class HoldoutTests(unittest.TestCase):
 def test_methods(self):
  for m in METHODS:self.assertEqual(trial(workload(16,9,"smooth"),m,4,7)["calls"],4)
 def test_success_binary(self):
  for m in METHODS:self.assertIn(trial(workload(16,9,"smooth"),m,4,7)["success"],(0,1))
 def test_regret_nonnegative(self):self.assertGreaterEqual(trial(workload(16,9,"smooth"),"QI_KERNEL_PHASE",4,7)["regret"],0)
 def test_full_budget(self):
  for m in METHODS:self.assertEqual(trial(workload(16,9,"smooth"),m,16,7)["success"],1)
 def test_ci_zero(self):self.assertEqual(paired_interval([0]*10,100),[0,0])
 def test_ci_order(self):
  a,b=paired_interval([-1,0,1]*10,100);self.assertLessEqual(a,b)
 def test_rows(self):self.assertEqual(len(benchmark(16,(4,),3,bootstrap=100)["results"]),12)
 def test_contrasts(self):self.assertEqual(len(benchmark(16,(4,),3,bootstrap=100)["contrasts"]),9)
 def test_calls(self):self.assertTrue(all(r["all_equal_calls"] for r in benchmark(16,(4,),3,bootstrap=100)["results"]))
 def test_diffs(self):
  r=benchmark(16,(4,),3,bootstrap=100)
  self.assertTrue(all(len(c["success_95ci"])==2 for c in r["contrasts"]))
 def test_invalid_budget(self):
  with self.assertRaises(ValueError):trial(workload(16,9,"smooth"),"RANDOM",17,7)
 def test_invalid_temp(self):
  with self.assertRaises(ValueError):trial(workload(16,9,"smooth"),"SOFTMAX_KERNEL",4,7,temperature=0)
 def test_bad_trials(self):
  with self.assertRaises(ValueError):benchmark(16,(4,),1,bootstrap=100)
 def test_bad_bootstrap(self):
  with self.assertRaises(ValueError):benchmark(16,(4,),3,bootstrap=50)
 def test_holdout_seed(self):self.assertEqual(benchmark(16,(4,),3,seed=300,bootstrap=100)["parameters"]["holdout_seed_start"],300)
 def test_runtime(self):self.assertGreaterEqual(trial(workload(16,9,"smooth"),"QI_KERNEL_PHASE",4,7)["milliseconds"],0)
if __name__=="__main__":unittest.main()
