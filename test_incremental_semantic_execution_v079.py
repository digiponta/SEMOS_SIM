import unittest
from incremental_semantic_execution_v079 import build_graph,descendants,compare,simulate
class IncrementalV079Tests(unittest.TestCase):
 def test_graph(self):self.assertEqual(len(build_graph(5)),15)
 def test_impact(self):
  nodes=build_graph(4)
  self.assertEqual(descendants(nodes,{"C1:S0"}),
    {"C1:S0","C1:S1","C1:S2","C2:S2"})
 def test_no_change(self):
  report=compare(5,changed=())
  self.assertEqual(report["results"][1]["recomputed_second_epoch"],0)
 def test_changed_recompute(self):
  r=compare(5,changed=("C1:S0",))
  self.assertEqual(r["results"][1]["recomputed_second_epoch"],4)
 def test_equal_incremental(self):
  self.assertTrue(compare(5,changed=("C1:S0",))["matched_comparison"]["same_recompute"])
 def test_correctness(self):
  self.assertTrue(all(x["correctness_pass"] for x in compare(5,changed=("C1:S0",))["results"]))
 def test_cost(self):
  self.assertGreater(compare(5,changed=("C1:S0",))["matched_comparison"]["semantic_minus_dag_cost"],0)
 def test_accounting(self):
  for x in compare(5,changed=("C1:S0",))["results"]:
   self.assertEqual(x["executed"]+x["reused"],x["requests"])
 def test_avoidable_recompute(self):
  r=compare(5,changed=("C1:S0",))
  self.assertGreater(r["results"][0]["unnecessary_recomputation"],0)
  self.assertEqual(r["results"][1]["unnecessary_recomputation"],0)
 def test_deterministic(self):self.assertEqual(compare(5,seed=7,changed=("C1:S0",)),compare(5,seed=7,changed=("C1:S0",)))
 def test_invalid_changed(self):
  with self.assertRaises(ValueError):compare(5,changed=("BAD",))
 def test_bad_order(self):
  nodes=build_graph(5)
  with self.assertRaises(ValueError):simulate(list(reversed(nodes)),"TASK_FULL_REBUILD",set())
if __name__=="__main__":unittest.main()
