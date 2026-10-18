import unittest
from pilot_profile_router_v0720 import (PROFILES,METHODS,sample_pilot,features,
 fit_classifier,classify,continue_search,benchmark)
from semantic_weighted_interference_v0716 import workload
class PilotRouterTests(unittest.TestCase):
 def test_sample_count(self):self.assertEqual(len(sample_pilot(workload(16,2,"smooth"),3,4)),4)
 def test_sample_unique(self):self.assertEqual(len(set(sample_pilot(workload(16,2,"smooth"),3,4))),4)
 def test_features(self):self.assertEqual(len(features({0:1.,2:0.,4:1.},16)),2)
 def test_centroids(self):self.assertEqual(len(fit_classifier(16,10,3,4)),3)
 def test_classify(self):
  centers=fit_classifier(16,10,3,4)
  self.assertIn(classify(centers,(.2,.4)),PROFILES)
 def test_continue(self):
  v=workload(16,2,"smooth");obs=sample_pilot(v,3,4)
  for m in METHODS:self.assertEqual(continue_search(v,m,8,7,obs)["calls"],8)
 def test_complete(self):
  v=workload(16,2,"smooth");obs=sample_pilot(v,3,4)
  for m in METHODS:self.assertEqual(continue_search(v,m,16,7,obs)["success"],1)
 def test_no_extra_calls(self):
  r=benchmark(16,(4,8),4,3,3,4,100,200,300)
  self.assertTrue(all(x["equal_total_oracle_calls"] for x in r["results"]))
 def test_rows(self):self.assertEqual(len(benchmark(16,(4,),4,3,3,4,100,200,300)["results"]),12)
 def test_confusion(self):
  r=benchmark(16,(4,),4,3,3,4,100,200,300)
  self.assertTrue(all(sum(r["confusion"][p].values())==4 for p in PROFILES))
 def test_routes(self):self.assertEqual(len(benchmark(16,(4,),4,3,3,4,100,200,300)["routes"]),3)
 def test_timing(self):self.assertTrue(all(x["median_total_ms"]>=0 for x in benchmark(16,(4,),4,3,3,4,100,200,300)["results"]))
 def test_overlapping_seed(self):
  with self.assertRaises(ValueError):benchmark(16,(4,),4,3,3,4,100,102,300)
 def test_pilot_too_large(self):
  with self.assertRaises(ValueError):benchmark(16,(4,),5,3,3,4,100,200,300)
 def test_invalid_method(self):
  with self.assertRaises(ValueError):continue_search(workload(16,2,"smooth"),"bad",8,7,{0:.5})
 def test_deterministic_centers(self):self.assertEqual(fit_classifier(16,10,3,4),fit_classifier(16,10,3,4))
if __name__=="__main__":unittest.main()
