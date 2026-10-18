import unittest
from pilot_classifier_sensitivity_v0721 import (PROFILES,CLASSIFIERS,training,prediction,
 route_table,benchmark)
class SensitivityTests(unittest.TestCase):
 def test_training_count(self):self.assertEqual(len(training(16,100,3,4)),9)
 def test_predict_kinds(self):
  data=training(16,100,3,4)
  for kind in CLASSIFIERS:
   p,c=prediction(data,(.2,.3),kind)
   self.assertIn(p,PROFILES)
   self.assertGreaterEqual(c,0)
 def test_routes(self):
  data=training(16,100,3,4)
  self.assertEqual(len(route_table(data,16,200,3,4,"CENTROID",(4,))),3)
 def test_rows(self):
  r=benchmark(16,(4,),(2,4),3,3,3,100,200,300)
  self.assertEqual(len(r["results"]),24*2)
 def test_matrices(self):
  r=benchmark(16,(4,),(2,4),3,3,3,100,200,300)
  self.assertEqual(len(r["classifiers"]),4)
 def test_confusion(self):
  r=benchmark(16,(4,),(2,),3,3,3,100,200,300)
  for item in r["classifiers"]:
   self.assertEqual(sum(sum(x.values()) for x in item["confusion"].values()),9)
 def test_budget(self):
  r=benchmark(16,(4,),(2,),3,3,3,100,200,300)
  self.assertTrue(all(x["equal_oracle_calls"] for x in r["results"]))
 def test_fallback(self):
  r=benchmark(16,(4,),(2,),3,3,3,100,200,300,confidence=100.)
  self.assertTrue(all(x["classifier_fallback_rate"]==1 for x in r["results"] if x["policy"]=="CONFIDENCE_FALLBACK"))
 def test_invalid_pilot(self):
  with self.assertRaises(ValueError):benchmark(16,(4,),(6,),3,3,3,100,200,300)
 def test_overlap(self):
  with self.assertRaises(ValueError):benchmark(16,(4,),(2,),3,3,3,100,101,300)
 def test_classifier_invalid(self):
  with self.assertRaises(ValueError):prediction(training(16,100,3,4),(.2,.3),"BAD")
 def test_accuracy_bounded(self):
  r=benchmark(16,(4,),(2,),3,3,3,100,200,300)
  self.assertTrue(all(0<=x["accuracy"]<=1 for x in r["classifiers"]))
if __name__=="__main__":unittest.main()
