import unittest
from quantum_inspired_search_v0714 import METHODS,landscape,search,compare,choose_weighted
import random
class QuantumInspiredTests(unittest.TestCase):
 def test_landscape_len(self):self.assertEqual(len(landscape(32,4)),32)
 def test_landscape_bounds(self):self.assertTrue(all(0<=x<=1 for x in landscape(32,4)))
 def test_landscape_reproduce(self):self.assertEqual(landscape(32,4),landscape(32,4))
 def test_landscape_bad(self):
  with self.assertRaises(ValueError):landscape(3,4)
 def test_every_method(self):
  for m in METHODS:self.assertEqual(search(landscape(32,4),m,8,4)["oracle_calls"],8)
 def test_success_range(self):
  for m in METHODS:self.assertIn(search(landscape(32,4),m,8,4)["success"],(0,1))
 def test_regret_nonnegative(self):
  for m in METHODS:self.assertGreaterEqual(search(landscape(32,4),m,8,4)["regret"],-1e-12)
 def test_full_budget_success(self):
  for m in METHODS:self.assertEqual(search(landscape(32,4),m,32,4)["success"],1)
 def test_deterministic(self):self.assertEqual(compare(32,8,5),compare(32,8,5))
 def test_equal_budget(self):self.assertTrue(all(x["all_oracle_calls_equal"] for x in compare(32,8,5)["results"]))
 def test_ablation_present(self):self.assertIn("qi_minus_no_interference_success",compare(32,8,5)["interference_ablation"])
 def test_bad_budget(self):
  with self.assertRaises(ValueError):search(landscape(32,4),"GREEDY",33)
 def test_bad_trials(self):
  with self.assertRaises(ValueError):compare(32,8,0)
 def test_weighted_fallback(self):self.assertIn(choose_weighted([0,0],random.Random(2)),(0,1))
 def test_unknown_method(self):
  with self.assertRaises(ValueError):search(landscape(32,4),"INVALID",5)
 def test_curve_length(self):self.assertTrue(all(len(x["mean_success_curve"])==8 for x in compare(32,8,5)["results"]))
if __name__=="__main__":unittest.main()
