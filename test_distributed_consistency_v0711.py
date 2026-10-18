import unittest
from distributed_consistency_v0711 import workload,truth,run,compare,_depends
class ReplicaTests(unittest.TestCase):
 def test_graph(self):self.assertEqual(len(workload()),4)
 def test_dependency(self):self.assertTrue(_depends(workload(),"D","A"))
 def test_no_reverse_dependency(self):self.assertFalse(_depends(workload(),"A","D"))
 def test_truth(self):
  self.assertNotEqual(truth(workload(),{"A":1,"B":1,"C":1,"D":1})["D"],
                      truth(workload(),{"A":2,"B":1,"C":1,"D":1})["D"])
 def test_mode_pair(self):self.assertEqual(len(compare()["results"]),2)
 def test_same_stale(self):self.assertTrue(compare()["matched"]["same_stale_detection"])
 def test_same_conflict(self):self.assertTrue(compare()["matched"]["same_conflicts"])
 def test_extra_cost(self):self.assertGreater(compare()["matched"]["semantic_extra_cost"],0)
 def test_correct_return(self):
  self.assertTrue(all(r["wrong_results_returned"]==0 for r in compare()["results"]))
 def test_delayed_notification(self):self.assertGreater(run(notification_delay=3)["stale_detected"],0)
 def test_reproducible(self):self.assertEqual(compare(),compare())
 def test_bad_delay(self):
  with self.assertRaises(ValueError):run(notification_delay=-1)
 def test_no_management_cost(self):self.assertEqual(compare(management_cost=0)["matched"]["semantic_extra_cost"],0)
 def test_conflict(self):self.assertEqual(run()["conflicts"],1)
if __name__=="__main__":unittest.main()
