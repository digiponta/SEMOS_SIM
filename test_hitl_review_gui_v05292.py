import csv,tempfile,unittest
from pathlib import Path
from hitl_review_gui_v05292 import reviewable,save_decisions
from simulate_hitl_review_v0529 import load_reviews
class GUIPacketTests(unittest.TestCase):
 def setUp(self):
  self.records=[{"request_id":"A","final":"VM-A"},{"request_id":"B","final":"VM-B"},{"request_id":"U","final":"DISCOVERY"}]
 def test_only_real_answer_is_reviewable(self):
  payloads={"A":{"question":"実際の質問","answer":"回答"},
            "B":{"question":"質問","answer":""},"U":{"question":"質問","answer":"回答"}}
  self.assertEqual([r["request_id"] for r in reviewable(self.records,payloads)],["A"])
 def test_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"choices.csv"
   save_decisions(p,{"A":"RETRY","B":"APPROVE"})
   self.assertEqual(load_reviews(p),{"A":"RETRY","B":"APPROVE"})
 def test_invalid_decision(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):save_decisions(Path(d)/"choices.csv",{"A":"MAYBE"})
if __name__=="__main__":unittest.main()
