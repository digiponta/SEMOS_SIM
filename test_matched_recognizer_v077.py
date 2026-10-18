import unittest
from matched_recognizer_v077 import compare,recognized_workload,study,simulate
class MatchedRecognizerV077Tests(unittest.TestCase):
 def test_equal_reuse(self):
  r=compare()
  self.assertTrue(r["matched_comparison"]["reuse_count_equal"])
 def test_equal_wrong_reuse(self):
  r=compare(false_merge_rate=0.5)
  self.assertTrue(r["matched_comparison"]["wrong_reuse_count_equal"])
 def test_spu_additional_overhead(self):
  r=compare()
  self.assertGreater(r["matched_comparison"]["spu_cost_difference"],0)
 def test_no_error_correct(self):
  r=compare()
  self.assertTrue(r["matched_comparison"]["both_correct"])
 def test_merge_error_detected(self):
  r=compare(false_merge_rate=1,update_period=120)
  self.assertGreater(r["results"][3]["wrong_reuse"],0)
 def test_full_miss(self):
  r=compare(false_miss_rate=1)
  self.assertEqual(r["results"][3]["reused"],0)
 def test_version_isolation(self):
  r=compare(update_period=1)
  self.assertEqual(r["results"][3]["reused"],0)
 def test_deterministic(self):
  self.assertEqual(compare(seed=7),compare(seed=7))
 def test_study_cases(self):
  s=study(seeds=2,count=30)
  self.assertEqual(len(s["cases"]),5)
  self.assertTrue(all(c["identical_reuse_all"] for c in s["cases"]))
 def test_bad_rate(self):
  with self.assertRaises(ValueError):recognized_workload(false_merge_rate=2)
 def test_cost_components(self):
  r=compare()
  for v in r["results"]:
   self.assertAlmostEqual(v["aggregate_cost"],sum(v["cost_breakdown"].values()))
if __name__=="__main__":unittest.main()
