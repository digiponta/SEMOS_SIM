import csv,tempfile,unittest
from pathlib import Path
from evaluate_paired_grouped_v058 import wilson,load_groups,paired_evaluate

def item(text,label,vm,score):
 return {"text":text,"label":label,"best_vm":vm,"score":score,"margin":.1,
         "centroid_top":vm,"multi_top":vm}
class PairedGroupTests(unittest.TestCase):
 def test_wilson(self):
  lo,hi=wilson(0,25)
  self.assertEqual(lo,0)
  self.assertGreater(hi,.05)
  self.assertLess(hi,.2)
 def test_explicit_groups(self):
  rows=[item("abc","VM-A","VM-A",.8),item("xyz","UNKNOWN","VM-A",.5)]
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"groups.csv"
   with p.open("w",encoding="utf-8",newline="") as f:
    w=csv.writer(f);w.writerow(("text","group_id"));w.writerows((("abc","topic1"),("xyz","topic2")))
   groups,mode=load_groups(rows,p)
   self.assertEqual(groups,["topic1","topic2"])
   self.assertEqual(mode,"CURATED_TOPIC_GROUPS_UNVERIFIED")
 def test_missing_group(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/"groups.csv";p.write_text("text,group_id\nabc,topic1\n",encoding="utf-8")
   with self.assertRaises(ValueError):load_groups([item("xyz","VM-A","VM-A",.8)],p)
 def test_same_fold_indices(self):
  rows=[]
  for i in range(9):
   vm=("VM-A","VM-B","VM-C")[i%3]
   rows.append(item("known"+str(i),vm,vm,.85))
   rows.append(item("unknown"+str(i),"UNKNOWN",vm,.5))
  groups=[str(i//2) for i in range(18)]
  report,ref,cand=paired_evaluate(rows,groups,folds=3)
  self.assertEqual(len(ref),18)
  self.assertEqual(len(cand),18)
  self.assertEqual(report["reference"]["unknown_false_accept_count"],0)
  self.assertEqual(report["candidate"]["known_n"],9)
 def test_insufficient_groups(self):
  with self.assertRaises(ValueError):
   paired_evaluate([item("a","VM-A","VM-A",.8)],["same"],folds=2)
if __name__=="__main__":unittest.main()
