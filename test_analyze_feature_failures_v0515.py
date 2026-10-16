import unittest
from analyze_feature_failures_v0515 import analyze,bucket,stats
class FeatureTests(unittest.TestCase):
 def row(self,gold,vm,pred,contrast):
  return {"text":gold+vm+pred,"gold":gold,"candidate_vm":vm,"predicted":pred,
   "contrast_score":contrast,"guard_cutoff":0,"guard_margin":contrast,
   "fused_similarity":.75,"runner_up_margin":.12,
   "distance_to_known":.3,"distance_to_unknown":.8}
 def test_buckets(self):
  self.assertEqual(bucket(self.row("VM-A","VM-A","UNKNOWN",-1)),"candidate_right_rejected")
  self.assertEqual(bucket(self.row("UNKNOWN","VM-C","UNKNOWN",-1)),"unknown_correct_rejected")
 def test_analysis(self):
  rows=[self.row("VM-A","VM-A","UNKNOWN",-1),self.row("UNKNOWN","VM-B","VM-B",1)]
  x=analyze({"version":"0.5.11","reference_replay_exact_match":True,"rows":rows})
  self.assertEqual(x["n"],2)
  self.assertEqual(x["failure_modes"]["candidate_right_rejected"]["count"],1)
 def test_replay_guard(self):
  r=self.row("VM-A","VM-A","VM-A",-1)
  with self.assertRaises(ValueError):
   analyze({"version":"0.5.11","reference_replay_exact_match":True,"rows":[r]})
if __name__=="__main__":unittest.main()
