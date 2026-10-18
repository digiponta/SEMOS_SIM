import unittest
from distributed_statistics_v076 import describe,run_study,scenarios
class StatisticsV076(unittest.TestCase):
 def test_statistics(self):
  v=describe([1,2,3])
  self.assertEqual(v["mean"],2)
  self.assertEqual(v["sample_sd"],1)
 def test_one_sample_sd(self):
  self.assertEqual(describe([4])["sample_sd"],0)
 def test_empty_fails(self):
  with self.assertRaises(ValueError):describe([])
 def test_scenario_count(self):
  self.assertEqual(len(scenarios()),16)
 def test_runs_present(self):
  d=run_study(seed_count=2,requests=25)
  self.assertEqual(len(d["scenarios"]),16)
  self.assertTrue(all(len(s["runs"])==2 for s in d["scenarios"]))
 def test_repeatable(self):
  self.assertEqual(run_study(2,10,20),run_study(2,10,20))
 def test_metric_ranges(self):
  d=run_study(2,42,30)
  for sc in d["scenarios"]:
   self.assertGreaterEqual(sc["summary"]["positive_spu_vs_normalized_count"],0)
   self.assertLessEqual(sc["summary"]["positive_spu_vs_normalized_count"],2)
 def test_no_stale(self):
  d=run_study(2,42,25)
  self.assertTrue(all(x["summary"]["zero_stale_reuse_all"] for x in d["scenarios"]))
 def test_bad_count(self):
  with self.assertRaises(ValueError):run_study(1)
 def test_seed_diversity(self):
  d=run_study(3,42,20)
  self.assertEqual([r["seed"] for r in d["scenarios"][0]["runs"]],[42,43,44])
if __name__=="__main__":unittest.main()
