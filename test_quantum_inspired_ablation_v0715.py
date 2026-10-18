import unittest
from quantum_inspired_ablation_v0715 import METHODS,LANDSCAPES,landscape,run,benchmark
class AblationTests(unittest.TestCase):
 def test_landscapes(self):
  for k in LANDSCAPES:self.assertEqual(len(landscape(32,2,k)),32)
 def test_reproducible_landscape(self):self.assertEqual(landscape(32,2,"smooth"),landscape(32,2,"smooth"))
 def test_distinct_landscapes(self):self.assertNotEqual(landscape(32,2,"smooth"),landscape(32,2,"shuffled"))
 def test_methods(self):
  for m in METHODS:self.assertEqual(run(landscape(32,2,"smooth"),m,8,2)["oracle_calls"],8)
 def test_complete_budget(self):
  for m in METHODS:self.assertEqual(run(landscape(16,2,"shuffled"),m,16,2)["success"],1)
 def test_regret(self):
  for m in METHODS:self.assertGreaterEqual(run(landscape(32,2,"smooth"),m,8,2)["regret"],0)
 def test_curve(self):self.assertEqual(len(run(landscape(32,2,"smooth"),"QI_PHASE_DIFFUSION",8,2)["curve"]),8)
 def test_phase_only_matches_random(self):
  vals=landscape(32,2,"shuffled")
  a=run(vals,"QI_PHASE_ONLY",8,2)
  b=run(vals,"RANDOM",8,2)
  self.assertEqual(a["best"],b["best"])
 def test_diffusion_only_matches_random(self):
  vals=landscape(32,2,"shuffled")
  self.assertEqual(run(vals,"QI_DIFFUSION_ONLY",8,2)["best"],run(vals,"RANDOM",8,2)["best"])
 def test_rows(self):self.assertEqual(len(benchmark(16,(4,8),3)["results"]),30)
 def test_ablations(self):self.assertEqual(len(benchmark(16,(4,8),3)["ablations"]),6)
 def test_equal_calls(self):self.assertTrue(all(r["equal_oracle_calls"] for r in benchmark(16,(4,8),3)["results"]))
 def test_deterministic(self):self.assertEqual(benchmark(16,(4,8),3),benchmark(16,(4,8),3))
 def test_bad_trials(self):
  with self.assertRaises(ValueError):benchmark(16,(4,),0)
 def test_bad_budget(self):
  with self.assertRaises(ValueError):benchmark(16,(32,),3)
 def test_bad_method(self):
  with self.assertRaises(ValueError):run(landscape(16,2,"smooth"),"bad",4,2)
if __name__=="__main__":unittest.main()
