import unittest
from semantic_dependency_graph_v078 import workload,run,compare
class SDGTests(unittest.TestCase):
 def test_workload(self):self.assertEqual(len(workload(4,2)),24)
 def test_modes(self):self.assertEqual(len(compare(concepts=4)["results"]),3)
 def test_matched_reuse(self):
  self.assertTrue(compare(concepts=6)["matched_comparison"]["same_reuse"])
 def test_matched_errors(self):
  self.assertTrue(compare(concepts=6,recognizer_merge=0.5)["matched_comparison"]["same_wrong_reuse"])
 def test_overhead(self):
  self.assertGreater(compare(concepts=6)["matched_comparison"]["spu_minus_dag_cost"],0)
 def test_no_false_merge(self):
  self.assertEqual(compare(concepts=6)["results"][2]["wrong_reuse"],0)
 def test_accounting(self):
  for r in compare(concepts=4)["results"]:
   self.assertEqual(r["executed"]+r["reused"],r["requests"])
 def test_changed_invalidation(self):
  a=compare(concepts=6,changed=())["results"][1]["reused"]
  b=compare(concepts=6,changed=("C3",))["results"][1]["reused"]
  self.assertLess(b,a)
 def test_determinism(self):self.assertEqual(compare(concepts=5,seed=8),compare(concepts=5,seed=8))
 def test_bad_input(self):
  with self.assertRaises(ValueError):workload(0)
 def test_bad_dependency(self):
  rows=workload(3)
  rows[0]["dependencies"]=["missing"]
  with self.assertRaises(ValueError):run(rows,"TASK_DAG")
if __name__=="__main__":unittest.main()
