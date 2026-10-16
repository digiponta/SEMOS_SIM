import unittest
from diagnose_hybrid_holdout_v055 import summarize
class DiagnosisTests(unittest.TestCase):
 def test_reason_and_counts(self):
  details=[
   {"gold":"VM-A","ungated":"VM-A","gated":"VM-A","reason":"accepted","consensus":True},
   {"gold":"VM-A","ungated":"VM-B","gated":"UNKNOWN","reason":"low_margin","consensus":False},
   {"gold":"UNKNOWN","ungated":"VM-A","gated":"UNKNOWN","reason":"low_similarity","consensus":True}]
  output=summarize(details)
  self.assertEqual(output["known_ungated_correct"],1)
  self.assertEqual(output["known_gated_correct"],1)
  self.assertEqual(output["known_gate_rejections"],1)
  self.assertEqual(output["unknown_gated_rejections"],1)
  self.assertEqual(output["by_class"]["VM-A"]["centroid_multi_disagreement"],1)
if __name__=="__main__":unittest.main()
