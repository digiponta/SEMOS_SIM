import unittest
from distributed_resilience_v075 import compare,simulate,MODES
class ResilienceV075Tests(unittest.TestCase):
 def test_modes(self):
  self.assertEqual([r["mode"] for r in compare()["results"]],list(MODES))
 def test_repeatable(self):
  self.assertEqual(compare(seed=7),compare(seed=7))
 def test_accounting(self):
  for r in compare()["results"]:
   self.assertEqual(r["executed"]+r["reused"],r["requests"])
   self.assertAlmostEqual(r["aggregate_cost"],sum(r["cost_breakdown"].values()))
 def test_equal_failures_when_no_reuse(self):
  r=compare(duplicate_fraction=0,failure_rate=0.4)
  self.assertEqual(len({x["failures"] for x in r["results"]}),1)
 def test_full_failure(self):
  r=compare(duplicate_fraction=0,failure_rate=1)["results"][0]
  self.assertEqual(r["retries"],120)
 def test_version_invalidation(self):
  rows=[{"id":"a","surface":"one","canonical":"X","version":1,"compute":4.0},
        {"id":"b","surface":"two","canonical":"X","version":2,"compute":4.0}]
  self.assertEqual(simulate(rows,"SEMANTIC_SPU",failure_rate=0)["reused"],0)
 def test_reuse(self):
  r=compare(update_period=1000,failure_rate=0)["results"][-1]
  self.assertGreater(r["reused"],0)
 def test_stale_reuse_zero(self):
  self.assertEqual([x["stale_reuse"] for x in compare(update_period=1)["results"]],[0,0,0])
 def test_no_negative_transfer(self):
  self.assertGreaterEqual(compare()["results"][-1]["cost_breakdown"]["network"],0)
 def test_invalid_rates(self):
  with self.assertRaises(ValueError):compare(failure_rate=1.1)
  with self.assertRaises(ValueError):compare(sync_cost=-1)
if __name__=="__main__":unittest.main()
