import csv,tempfile,unittest
from pathlib import Path
from prepare_prospective_eval_v0517 import inspect,FIELDS
class ProspectiveTests(unittest.TestCase):
 def test_overlap(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"case.csv"
   with p.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
    w.writerow(dict(zip(FIELDS,("id1","known text","VM-A","x","y","z","explain","topic1","source1"))))
   result=inspect(p,["  KNOWN  text "])
   self.assertEqual(result["rows"],1)
   self.assertFalse(result["valid_structure"])
   self.assertEqual(result["prior_development_overlap_lines"],[2])
 def test_invalid_label(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/"case.csv"
   with p.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
    w.writerow(dict(zip(FIELDS,("id1","new text","OTHER","x","y","z","explain","topic","source"))))
   with self.assertRaises(ValueError):inspect(p)
if __name__=="__main__":unittest.main()
