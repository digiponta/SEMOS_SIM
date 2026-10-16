import tempfile,unittest
from pathlib import Path
from simulate_hitl_review_v0529 import process,load_reviews,summarize
class HITLTests(unittest.TestCase):
 def record(self,final="VM-A"):
  return {"request_id":"R1","final":final}
 def test_missing_decision_pending(self):
  self.assertEqual(process(self.record())["status"],"PENDING_USER_REVIEW")
 def test_confirm_requires_explicit(self):
  self.assertEqual(process(self.record(),"APPROVE")["status"],"USER_CONFIRMED")
 def test_retry_handoff_only(self):
  self.assertEqual(process(self.record(),"RETRY")["status"],"RETRY_REQUESTED")
 def test_discovery_does_not_prompt(self):
  self.assertEqual(process(self.record("DISCOVERY"))["status"],"DISCOVERY")
  with self.assertRaises(ValueError):process(self.record("DISCOVERY"),"APPROVE")
 def test_denial(self):
  self.assertEqual(process(self.record(),"REJECT")["status"],"USER_REJECTED")
 def test_review_csv(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"reviews.csv"
   p.write_text("request_id,decision\nR1,approve\n",encoding="utf8")
   self.assertEqual(load_reviews(p),{"R1":"APPROVE"})
 def test_summary(self):
  self.assertEqual(summarize([process(self.record())])["USER_CONFIRMED"],0)
if __name__=="__main__":unittest.main()
