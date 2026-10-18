import unittest
from distributed_mvcc_convergence_v0713 import dominant,dedup,heads,resolve,experiment,compare
class ConvergenceTests(unittest.TestCase):
 def test_dominance(self):self.assertTrue(dominant((1,1,0),(1,0,0)))
 def test_not_dominant(self):self.assertFalse(dominant((1,0,0),(0,1,0)))
 def test_duplicate(self):
  a={"clock":(1,0,0),"value":"alpha"}
  self.assertEqual(len(dedup([a,a])),1)
 def test_unique_heads(self):
  a={"clock":(1,0,0),"value":"alpha"};b={"clock":(0,1,0),"value":"beta"}
  self.assertEqual(len(heads([a,a,b,b])),2)
 def test_covered_head(self):
  a={"clock":(1,0,0),"value":"alpha"};b={"clock":(1,1,0),"value":"joined"}
  self.assertEqual(len(heads([a,b])),1)
 def test_multi(self):
  self.assertEqual(resolve([{"clock":(1,0,0),"value":"a"},{"clock":(0,1,0),"value":"b"}],"multi_value"),("a","b"))
 def test_merge(self):
  self.assertEqual(resolve([{"clock":(1,0,0),"value":"a"},{"clock":(0,1,0),"value":"b"}],"merge"),"MERGE:a,b")
 def test_converged(self):
  for p in ("multi_value","deterministic","merge"):self.assertTrue(experiment(policy=p)["converged"])
 def test_head_count(self):self.assertEqual(experiment()["final_unique_head_counts"],[2,2,2])
 def test_matched(self):
  r=compare()
  self.assertTrue(all(r["matched"][k] for k in ("same_convergence","same_heads","same_final_values")))
 def test_extra_cost(self):self.assertGreater(compare()["matched"]["semantic_extra_cost"],0)
 def test_zero_cost(self):self.assertEqual(compare(semantic_cost=0)["matched"]["semantic_extra_cost"],0)
 def test_delay(self):self.assertTrue(experiment(delay=4)["converged"])
 def test_invalid(self):
  with self.assertRaises(ValueError):experiment(delay=-1)
 def test_repeat(self):self.assertEqual(compare(),compare())
 def test_invalid_policy(self):
  with self.assertRaises(ValueError):resolve([],"unknown")
if __name__=="__main__":unittest.main()
