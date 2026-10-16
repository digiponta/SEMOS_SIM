import unittest
from evaluate_prospective_v0518 import summarize
class ProspectiveTests(unittest.TestCase):
 def test_metrics(self):
  rows=[{"request_id":"a","gold":"VM-A"},{"request_id":"b","gold":"UNKNOWN"}]
  result=summarize(rows,["VM-A","UNKNOWN"])
  self.assertEqual(result["known_accuracy"],1)
  self.assertEqual(result["unknown_reject"],1)
  self.assertEqual(result["predictions"][0]["id"],"a")
 def test_false_accept(self):
  rows=[{"request_id":"a","gold":"VM-B"},{"request_id":"b","gold":"UNKNOWN"}]
  result=summarize(rows,["VM-A","VM-C"])
  self.assertEqual(result["unknown_false_accept"],1)
  self.assertFalse(result["targets"]["unknown_false_accept"]["point_estimate_met"])
if __name__=="__main__":unittest.main()
