import unittest
from semantic_weighted_interference_v0716 import METHODS,KINDS,workload,similarity,probability_after_update,search,benchmark
class V0716Tests(unittest.TestCase):
 def test_workloads(self):
  for k in KINDS:self.assertEqual(len(workload(16,2,k)),16)
 def test_similarity_identity(self):self.assertEqual(similarity(0,0,16),1)
 def test_similarity_symmetric(self):self.assertEqual(similarity(2,0,16),similarity(0,2,16))
 def test_probability_sum(self):self.assertAlmostEqual(sum(probability_after_update(16,{2:.8})),1)
 def test_probability_length(self):self.assertEqual(len(probability_after_update(16,{2:.8})),15)
 def test_probability_nonuniform(self):
  p=probability_after_update(16,{2:.8})
  self.assertGreater(max(p)-min(p),1e-5)
 def test_ablation_uniform(self):
  p=probability_after_update(16,{2:.8},mode="QI_PHASE_ABLATION")
  self.assertEqual(max(p),min(p))
 def test_zero_strength_uniform(self):
  p=probability_after_update(16,{2:.8},0)
  self.assertEqual(max(p),min(p))
 def test_methods_equal_calls(self):
  for m in METHODS:self.assertEqual(search(workload(16,2,"smooth"),m,8,2)["oracle_calls"],8)
 def test_full_budget(self):
  for m in METHODS:self.assertEqual(search(workload(16,2,"smooth"),m,16,2)["success"],1)
 def test_determinism(self):self.assertEqual(benchmark(16,(4,8),3),benchmark(16,(4,8),3))
 def test_result_rows(self):self.assertEqual(len(benchmark(16,(4,8),3)["results"]),30)
 def test_ablations(self):self.assertEqual(len(benchmark(16,(4,8),3)["ablations"]),6)
 def test_match_budget(self):self.assertTrue(all(x["equal_oracle_calls"] for x in benchmark(16,(4,),3)["results"]))
 def test_bad_method(self):
  with self.assertRaises(ValueError):search(workload(16,2,"smooth"),"bad",4,2)
 def test_bad_strength(self):
  with self.assertRaises(ValueError):probability_after_update(16,{2:.8},-1)
if __name__=="__main__":unittest.main()
