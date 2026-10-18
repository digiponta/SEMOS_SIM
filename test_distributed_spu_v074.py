import unittest
from distributed_spu_v074 import make_workload,simulate,compare,MODES

class DistributedV074Tests(unittest.TestCase):
 def test_modes(self):
  self.assertEqual([x["mode"] for x in compare()["results"]],list(MODES))
 def test_total_accounting(self):
  for result in compare()["results"]:
   self.assertEqual(result["executed"]+result["reused"],result["requests"])
 def test_determinism(self):
  self.assertEqual(compare(seed=21),compare(seed=21))
 def test_zero_dependencies(self):
  r=compare(dependency_fraction=0)
  self.assertGreater(r["results"][-1]["reused"],0)
 def test_full_dependencies_limit_reuse(self):
  r=compare(dependency_fraction=1)
  self.assertEqual(r["results"][-1]["reused"],0)
 def test_no_duplicate_semantics(self):
  r=compare(duplicate_fraction=0,dependency_fraction=0)
  self.assertEqual(r["results"][-1]["reused"],0)
 def test_cost_identity(self):
  for x in compare()["results"]:
   total=x["execution_work"]+x["transfer_cost"]+x["semantic_cost"]+x["lookup_cost"]
   self.assertAlmostEqual(x["aggregate_cost"],total)
 def test_remote_transfer_present(self):
  rows=make_workload(200,0.7,0,7)
  r=simulate(rows,"SEMANTIC_SPU",network_latency=0.5,seed=7)
  self.assertGreater(r["transfers"],0)
 def test_dependency_missing_rejected(self):
  rows=make_workload(4)
  rows[1]["dependencies"]=("missing",)
  with self.assertRaises(ValueError):simulate(rows,"TASK")
 def test_bad_parameter(self):
  with self.assertRaises(ValueError):compare(dependency_fraction=1.1)
if __name__=="__main__":unittest.main()
