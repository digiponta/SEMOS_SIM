import unittest
from distributed_mvcc_v0712 import compare,simulate,dominates,concurrent,maximal,choose_latest
class MVCCTests(unittest.TestCase):
 def test_dominance(self):self.assertTrue(dominates((2,1,0),(1,1,0)))
 def test_concurrent(self):self.assertTrue(concurrent((1,0,0),(0,1,0)))
 def test_equal_not_concurrent(self):self.assertFalse(concurrent((1,0,0),(1,0,0)))
 def test_maximal(self):
  v=[{"clock":(0,0,0),"value":"z","writer":-1},{"clock":(1,0,0),"value":"a","writer":0}]
  self.assertEqual(len(maximal(v)),1)
 def test_tie_break(self):
  v=[{"clock":(1,0,0),"value":"a","writer":0},{"clock":(0,1,0),"value":"b","writer":1}]
  self.assertEqual(choose_latest(v)["value"],"a")
 def test_two_modes(self):self.assertEqual(len(compare()["results"]),2)
 def test_matched_conflicts(self):self.assertTrue(compare()["matched"]["same_conflict_detection"])
 def test_matched_stale(self):self.assertTrue(compare()["matched"]["same_stale_observations"])
 def test_extra_cost(self):self.assertGreater(compare()["matched"]["semantic_extra_cost"],0)
 def test_zero_semantic_cost(self):self.assertEqual(compare(semantic_cost=0)["matched"]["semantic_extra_cost"],0)
 def test_peer_conflict(self):self.assertGreater(simulate()["conflict_reads"],0)
 def test_stale(self):self.assertGreater(simulate(notification_delay=3)["stale_local_reads"],0)
 def test_deterministic(self):self.assertEqual(compare(),compare())
 def test_negative_delay(self):
  with self.assertRaises(ValueError):simulate(notification_delay=-1)
 def test_negative_cost(self):
  with self.assertRaises(ValueError):simulate(validation_cost=-1)
 def test_cost_breakdown(self):
  for row in compare()["results"]:
   self.assertAlmostEqual(row["aggregate_cost"],sum(row["cost_breakdown"].values()))
if __name__=="__main__":unittest.main()
