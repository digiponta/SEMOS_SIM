import unittest
from trace_nested_gate_v0511 import trace_nested,validate_replay
def make(i,known):
 vm=("VM-A","VM-B","VM-C")[i%3]
 return {"text":f"{i}_{known}","label":vm if known else "UNKNOWN",
  "best_vm":vm,"score":.85 if known else .44,"margin":.15 if known else .01,
  "centroid_top":vm,"multi_top":vm if known else ("VM-B" if vm!="VM-B" else "VM-A")}
class TraceTests(unittest.TestCase):
 def setUp(self):
  self.rows=[make(i,known) for i in range(15) for known in (True,False)]
  self.groups=[str(i//2) for i in range(30)]
 def test_trace(self):
  rows,folds=trace_nested(self.rows,self.groups,folds=3,inner=2)
  self.assertEqual(len(rows),30)
  self.assertTrue(all("contrast_score" in r for r in rows))
  self.assertTrue(all(r["candidate_vm"] in ("VM-A","VM-B","VM-C") for r in rows))
 def test_replay(self):
  rows,_=trace_nested(self.rows,self.groups,folds=3,inner=2)
  prior={"diagnostics":[{k:r[k] for k in ("text","gold","topic_group","predicted")} for r in rows]}
  self.assertTrue(validate_replay(rows,prior))
  prior["diagnostics"][0]["predicted"]="INVALID"
  with self.assertRaises(ValueError):validate_replay(rows,prior)
 def test_length_guard(self):
  with self.assertRaises(ValueError):trace_nested(self.rows,["one"],folds=3)
if __name__=="__main__":unittest.main()
