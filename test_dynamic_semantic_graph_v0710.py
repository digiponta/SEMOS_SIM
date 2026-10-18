import unittest
from dynamic_semantic_graph_v0710 import graph,ordered,mutate,oracle_outputs,simulate,compare
class DynamicGraphTests(unittest.TestCase):
 def test_size(self):self.assertEqual(len(graph(5)),15)
 def test_order(self):self.assertEqual(len(ordered(graph(5))),15)
 def test_add_edge(self):
  n=mutate(graph(8),[{"action":"add_edge","node":"C7:S2","dependency":"C2:S0"}])
  self.assertIn("C2:S0",n["C7:S2"]["deps"])
 def test_remove_edge(self):
  n=mutate(graph(8),[{"action":"remove_edge","node":"C6:S2","dependency":"C5:S0"}])
  self.assertNotIn("C5:S0",n["C6:S2"]["deps"])
 def test_changed_truth(self):
  n=graph(8)
  m=mutate(n,[{"action":"content","node":"C3:S0","value":"updated"}])
  self.assertNotEqual(oracle_outputs(n)["C3:S2"],oracle_outputs(m)["C3:S2"])
 def test_recompute_matches(self):
  r=compare()
  self.assertTrue(r["matched"]["same_recompute"])
 def test_accuracy(self):
  r=compare()
  self.assertTrue(r["matched"]["both_correct"])
 def test_overhead(self):
  self.assertGreater(compare()["matched"]["semantic_extra_cost"],0)
 def test_incremental_saves(self):
  r=compare()["results"]
  self.assertLess(r[1]["recomputed"],r[0]["recomputed"])
 def test_no_invalidation_loss(self):
  for r in compare()["results"]:self.assertEqual(r["missed_invalidation"],0)
 def test_no_change_reuses_all(self):
  n=graph(4)
  r=simulate(n,[],"DAG_DYNAMIC")
  self.assertEqual(r["recomputed"],0)
 def test_cycle_rejected(self):
  with self.assertRaises(ValueError):
   mutate(graph(4),[{"action":"add_edge","node":"C0:S0","dependency":"C0:S2"}])
 def test_invalid_event(self):
  with self.assertRaises(ValueError):
   mutate(graph(4),[{"action":"delete","node":"C0:S0"}])
 def test_deterministic(self):self.assertEqual(compare(),compare())
if __name__=="__main__":unittest.main()
