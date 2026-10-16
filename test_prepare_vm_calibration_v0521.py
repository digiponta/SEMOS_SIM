import csv,tempfile,unittest
from pathlib import Path
from prepare_vm_calibration_v0521 import audit
class CalibrationAuditTests(unittest.TestCase):
 def make(self,path,text,source,topic):
  with path.open("w",encoding="utf-8",newline="") as f:
   w=csv.DictWriter(f,fieldnames=["request_id","text","gold","topic_group","source_id"]);w.writeheader()
   w.writerow({"request_id":"1","text":text,"gold":"VM-A","topic_group":topic,"source_id":source})
 def test_disjoint(self):
  with tempfile.TemporaryDirectory() as d:
   a,b,c=[Path(d)/name for name in ("a.csv","b.csv","old.csv")]
   self.make(a,"physics alpha","src-a","topic-a");self.make(b,"language beta","src-b","topic-b")
   self.make(c,"old topic","src-c","topic-c")
   self.assertTrue(audit(a,b,[c])["automatic_pass"])
 def test_topic_overlap(self):
  with tempfile.TemporaryDirectory() as d:
   a,b,c=[Path(d)/name for name in ("a.csv","b.csv","old.csv")]
   self.make(a,"physics alpha","src-a","same");self.make(b,"language beta","src-b","same")
   self.make(c,"old topic","src-c","topic-c")
   self.assertFalse(audit(a,b,[c])["automatic_pass"])
if __name__=="__main__":unittest.main()
