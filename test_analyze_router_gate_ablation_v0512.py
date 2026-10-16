import unittest
from analyze_router_gate_ablation_v0512 import analyze
def r(gold,vm,accepted):
 return {"gold":gold,"candidate_vm":vm,"predicted":vm if accepted else "UNKNOWN",
         "contrast_score":1. if accepted else -1.,"guard_cutoff":0.,
         "text":gold+vm+str(accepted)}
class Tests(unittest.TestCase):
 def setUp(self):
  self.report={"version":"0.5.11","reference_replay_exact_match":True,
   "rows":[r("VM-A","VM-A",True),r("VM-B","VM-B",False),
           r("VM-C","VM-A",False),r("UNKNOWN","VM-B",True),
           r("UNKNOWN","VM-A",False)]}
 def test_counts(self):
  a=analyze(self.report)
  self.assertEqual(a["failure_counts"]["candidate_right_rejected"],1)
  self.assertEqual(a["failure_counts"]["candidate_wrong_rejected"],1)
  self.assertEqual(a["failure_counts"]["unknown_false_accepted"],1)
  self.assertEqual(a["router_only"]["unknown_false_accept"],1.)
 def test_oracle(self):
  a=analyze(self.report)
  self.assertEqual(a["oracle_upper_bound_not_deployable"]["unknown_false_accept"],0.)
  self.assertEqual(a["oracle_upper_bound_not_deployable"]["known_correct"],2)
 def test_replay_validation(self):
  self.report["rows"][0]["predicted"]="UNKNOWN"
  with self.assertRaises(ValueError):analyze(self.report)
 def test_version_guard(self):
  self.report["version"]="0.5.10"
  with self.assertRaises(ValueError):analyze(self.report)
if __name__=="__main__":unittest.main()
