import unittest
from spu_sensitivity_v073 import run_case,sweep
class SensitivityV073(unittest.TestCase):
 def test_modes(self):
  r=run_case(100)
  self.assertEqual([x["mode"] for x in r["results"]],["TASK","EXACT_CACHE","NORMALIZED_CACHE","SEMANTIC_SPU"])
 def test_oracle_savings(self):
  r=run_case(100,0.4,0.05,normalization_coverage=0)
  self.assertEqual(r["results"][-1]["executed"],60)
  self.assertEqual(r["results"][-1]["wrong_reuse"],0)
 def test_no_duplicates(self):
  self.assertEqual(run_case(100,0)["results"][-1]["reused"],0)
 def test_overhead_can_reverse_advantage(self):
  r=run_case(100,0.4,1.0)
  self.assertGreater(r["results"][-1]["total_cost"],100)
 def test_false_merge_tracked(self):
  r=run_case(300,0.4,0.05,false_merge_probability=1.0)
  self.assertGreater(r["results"][-1]["wrong_reuse"],0)
  self.assertFalse(r["results"][-1]["correct_result_proxy"])
 def test_no_false_merge(self):
  r=run_case(300,0.4,0.05,false_merge_probability=0)
  self.assertEqual(r["results"][-1]["wrong_reuse"],0)
 def test_reproducible(self):
  self.assertEqual(run_case(100,0.3,seed=7),run_case(100,0.3,seed=7))
 def test_bad_probability(self):
  with self.assertRaises(ValueError):run_case(100,false_merge_probability=1.2)
 def test_sweep_cases(self):
  self.assertEqual(len(sweep(20)["cases"]),60)
if __name__=="__main__":unittest.main()
