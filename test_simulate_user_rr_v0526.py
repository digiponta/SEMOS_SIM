import tempfile,unittest
from pathlib import Path
from simulate_user_rr_v0526 import simulate,approvals_read
def responder(vm,gold,rid):
 return "ACCEPTED" if vm==gold else "NOT_SUPPORTED"
class UserRRTests(unittest.TestCase):
 def t(self,gold="VM-C",accepted=False):
  return {"request_id":"R1","gold":gold,"accepted":accepted,"candidate":"VM-A"}
 def test_denied_is_no_probe(self):
  x=simulate(self.t(),False,0,responder)
  self.assertEqual(x["final"],"DISCOVERY")
  self.assertFalse(any(e["state"]=="CAPABILITY_PROBE" for e in x["events"]))
 def test_authorized_rotated_probe(self):
  x=simulate(self.t(),True,1,responder)
  self.assertEqual(x["final"],"VM-C")
  self.assertEqual([e["vm"] for e in x["events"] if e["state"]=="CAPABILITY_PROBE"],["VM-B","VM-C"])
 def test_unknown(self):
  self.assertEqual(simulate(self.t("UNKNOWN"),True,2,responder)["final"],"DISCOVERY")
 def test_accepted_no_approval_needed(self):
  x=simulate(self.t("VM-A",True),False,0,responder)
  self.assertEqual(x["final"],"VM-A")
 def test_approval_validation(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"approvals.csv"
   p.write_text("request_id,approved\nR1,true\nR2,false\n",encoding="utf8")
   self.assertEqual(approvals_read(p),{"R1":True,"R2":False})
if __name__=="__main__":unittest.main()
