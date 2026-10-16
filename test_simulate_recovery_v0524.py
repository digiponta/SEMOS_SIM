import unittest
from simulate_recovery_v0524 import simulate,summarize
class RecoveryTests(unittest.TestCase):
 def row(self,gold,candidate,accepted=True):
  return {"request_id":"X","gold":gold,"candidate":candidate,"predicted":candidate if accepted else "UNKNOWN","accepted":accepted}
 def test_correct(self):
  x=simulate(self.row("VM-A","VM-A"))
  self.assertEqual(x["final"],"VM-A")
  self.assertFalse(any(e["state"]=="SIMULATED_ROLLBACK" for e in x["events"]))
 def test_retry(self):
  x=simulate(self.row("VM-B","VM-A"))
  self.assertEqual(x["final"],"VM-B")
  self.assertEqual(sum(e["state"]=="SIMULATED_ROLLBACK" for e in x["events"]),1)
 def test_unknown(self):
  x=simulate(self.row("UNKNOWN","VM-B"))
  self.assertEqual(x["final"],"DISCOVERY")
 def test_gate_reject(self):
  x=simulate(self.row("VM-B","VM-A",False))
  self.assertEqual(x["final"],"DISCOVERY")
  self.assertFalse(x["oracle_knowledge_used"])
 def test_one_attempt(self):
  self.assertEqual(simulate(self.row("VM-B","VM-A"),1)["final"],"DISCOVERY")
if __name__=="__main__":unittest.main()
