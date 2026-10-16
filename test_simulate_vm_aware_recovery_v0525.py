import unittest
from simulate_vm_aware_recovery_v0525 import dispatch,response,summarize
class VMRecoveryTests(unittest.TestCase):
 def trace(self,gold="VM-B",first="VM-A",accepted=True):
  return {"request_id":"case-1","gold":gold,"candidate":first,"accepted":accepted}
 def test_retry(self):
  x=dispatch(self.trace())
  self.assertEqual(x["final"],"VM-B")
  self.assertEqual(x["retry_count"],1)
 def test_not_supported_unknown(self):
  self.assertEqual(dispatch(self.trace("UNKNOWN"))["final"],"DISCOVERY")
 def test_rejected(self):
  self.assertEqual(dispatch(self.trace(accepted=False))["final"],"DISCOVERY")
  self.assertEqual(dispatch(self.trace(accepted=False))["retry_count"],0)
  self.assertEqual(summarize([dispatch(self.trace(accepted=False))],[self.trace(accepted=False)])["retry_requests"],0)
 def test_injected_false_response(self):
  def bad(vm,gold,request_id):return "ACCEPTED"
  self.assertEqual(dispatch(self.trace(),bad)["final"],"VM-A")
 def test_invalid(self):
  with self.assertRaises(ValueError):dispatch(self.trace(),max_attempts=4)
if __name__=="__main__":unittest.main()
