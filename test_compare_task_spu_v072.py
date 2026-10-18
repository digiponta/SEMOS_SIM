import unittest
from compare_task_spu_v072 import run,simulate,workload

class ComparisonV072(unittest.TestCase):
 def test_determinism(self):
  self.assertEqual(workload(100,0.3,21),workload(100,0.3,21))
 def test_zero_duplicates(self):
  r=run(40,0)
  self.assertEqual(r["results"][2]["reused"],0)
 def test_duplicate_savings(self):
  r=run(100,0.5)
  self.assertEqual(r["results"][2]["executed"],50)
  self.assertEqual(r["results"][2]["reused"],50)
 def test_exact_cache_unique_surface(self):
  r=run(100,0.5)
  self.assertEqual(r["results"][1]["reused"],0)
 def test_no_fake_speedup_high_overhead(self):
  r=run(100,0.5,semantic_overhead=1.0)
  self.assertLess(r["results"][2]["savings_vs_task_fraction"],0)
 def test_single_unit(self):
  r=run(1,1)
  self.assertEqual(r["results"][2]["executed"],1)
 def test_invalid_fraction(self):
  with self.assertRaises(ValueError):workload(10,1.1)
 def test_invalid_cost(self):
  with self.assertRaises(ValueError):simulate([], "SEMANTIC_SPU",semantic_overhead=-1)
 def test_same_workload(self):
  r=run(200,0.3)
  self.assertEqual([x["requests"] for x in r["results"]],[200]*3)
 def test_reproducible_metrics(self):
  self.assertEqual(run(100,0.4,17),run(100,0.4,17))
if __name__=="__main__":unittest.main()
