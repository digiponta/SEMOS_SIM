import unittest
from adaptive_quantum_router_v0719 import (METHODS,PROFILES,search,choose_routes,bootstrap_ci,
                                            build_dev,benchmark)
from semantic_weighted_interference_v0716 import workload
class RouterTests(unittest.TestCase):
 def test_search_methods(self):
  for m in METHODS:self.assertEqual(search(workload(16,3,"smooth"),m,4,7)["calls"],4)
 def test_success(self):
  for m in METHODS:self.assertIn(search(workload(16,3,"smooth"),m,4,7)["success"],(0,1))
 def test_full_budget(self):
  for m in METHODS:self.assertEqual(search(workload(16,3,"smooth"),m,16,7)["success"],1)
 def test_phase_intervention_not_identical(self):
  v=workload(16,3,"multimodal")
  results=[search(v,m,8,s) for s in range(8) for m in ("QI_PHASE_ON","QI_PHASE_OFF")]
  self.assertEqual(len(results),16)
 def test_deterministic(self):
  self.assertEqual(search(workload(16,3,"smooth"),"QI_PHASE_ON",4,7),
                   search(workload(16,3,"smooth"),"QI_PHASE_ON",4,7))
 def test_bootstrap_zero(self):self.assertEqual(bootstrap_ci([0]*5,100),[0.,0.])
 def test_route_key(self):
  d=build_dev(16,(4,),3,42)
  r,f,c=choose_routes(d,(4,))
  self.assertIn(("smooth",4),r)
  self.assertIn(f,METHODS)
  self.assertIn(c[("smooth",4)],("KERNEL_UCB","RANDOM"))
 def test_row_count(self):
  x=benchmark(16,(4,),3,4,42,40000,100)
  self.assertEqual(len(x["results"]),18)
 def test_contrast_count(self):
  x=benchmark(16,(4,),3,4,42,40000,100)
  self.assertEqual(len(x["contrasts"]),15)
 def test_matched_calls(self):
  x=benchmark(16,(4,),3,4,42,40000,100)
  self.assertTrue(all(y["equal_oracle_calls"] for y in x["results"]))
 def test_router_cost_control(self):
  x=benchmark(16,(4,),3,4,42,40000,100,router_cost=.2)
  self.assertEqual(next(v["routing_cost_per_request"] for v in x["results"] if v["policy"]=="ADAPTIVE_CLASSICAL"),.2)
 def test_phase_off_in_contrasts(self):
  x=benchmark(16,(4,),3,4,42,40000,100)
  self.assertTrue(any(c["comparison"]=="PHASE_ON-minus-PHASE_OFF" for c in x["contrasts"]))
 def test_bad_budget(self):
  with self.assertRaises(ValueError):benchmark(16,(20,),3,4,42,40000,100)
 def test_overlap(self):
  with self.assertRaises(ValueError):benchmark(16,(4,),3,4,42,43,100)
 def test_bad_method(self):
  with self.assertRaises(ValueError):search(workload(16,3,"smooth"),"INVALID",4,7)
 def test_invalid_cost(self):
  with self.assertRaises(ValueError):benchmark(16,(4,),3,4,42,40000,100,router_cost=-1)
if __name__=="__main__":unittest.main()
