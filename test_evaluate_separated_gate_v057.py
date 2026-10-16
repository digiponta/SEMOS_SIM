import unittest
from evaluate_separated_gate_v057 import fit,predict_one,evaluate_grouped_oof
def row(text,vm,label,score,margin,agree=True):
 return {"text":text,"best_vm":vm,"label":label,"score":score,"margin":margin,
         "centroid_top":vm,"multi_top":vm if agree else "VM-C" if vm!="VM-C" else "VM-A"}
class GateTests(unittest.TestCase):
 def setUp(self):
  self.rows=[]
  for i in range(12):
   vm=("VM-A","VM-B","VM-C")[i%3]
   self.rows.append(row("known"+str(i),vm,vm,.86,.15))
   self.rows.append(row("unknown"+str(i),vm,"UNKNOWN",.55,.01,False))
 def test_fit_and_predict(self):
  centers=fit(self.rows)
  self.assertEqual(predict_one(row("new","VM-A","VM-A",.86,.15),centers),"VM-A")
  self.assertEqual(predict_one(row("newu","VM-A","UNKNOWN",.55,.01,False),centers),"UNKNOWN")
 def test_oof(self):
  metrics,preds=evaluate_grouped_oof(self.rows,folds=3)
  self.assertEqual(len(preds),24)
  self.assertEqual(metrics["known_n"],12)
  self.assertEqual(metrics["unknown_n"],12)
 def test_guard(self):
  with self.assertRaises(ValueError):evaluate_grouped_oof(self.rows,folds=1)
if __name__=="__main__":unittest.main()
