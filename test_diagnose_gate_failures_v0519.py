import unittest
from diagnose_gate_failures_v0519 import audit
class DiagnosticsTests(unittest.TestCase):
 def test_exclusive_causes(self):
  rows=[{"request_id":str(i),"gold":"VM-C"} for i in range(4)]
  enriched=[{"best_vm":"VM-C","score":s,"margin":m,"centroid_top":"VM-C","multi_top":"VM-C"}
   for s,m in [(0.8,.1),(.6,.1),(.8,.01),(.6,.01)]]
  g=audit(rows,enriched,.76,.06)["VM-C"]
  self.assertEqual([g["counts"][x] for x in ("accepted","similarity_only","margin_only","both")],[1,1,1,1])
  self.assertEqual(g["counts"]["correct_candidate_rejected"],3)
if __name__=="__main__":unittest.main()
