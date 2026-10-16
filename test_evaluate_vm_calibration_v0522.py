import unittest
from evaluate_vm_calibration_v0522 import fit,calibrated_predict,wilson,measure
class CalibrationTests(unittest.TestCase):
 def test_ecdf(self):
  e=[{"best_vm":vm,"score":score} for vm in ("VM-A","VM-B","VM-C") for score in (.2,.8)]
  fit_map=fit(e)
  self.assertEqual(calibrated_predict({"best_vm":"VM-A","score":.8,"margin":.1},fit_map),"VM-A")
  self.assertEqual(calibrated_predict({"best_vm":"VM-A","score":.2,"margin":.1},fit_map),"UNKNOWN")
 def test_guard(self):
  with self.assertRaises(ValueError):fit([{"best_vm":"VM-B","score":.8}])
 def test_wilson(self):
  self.assertTrue(wilson(10,10)[0]<1)
 def test_measures(self):
  result=measure([{"request_id":"a","gold":"VM-A"},{"request_id":"b","gold":"UNKNOWN"}],["VM-A","UNKNOWN"])
  self.assertEqual(result["metrics"]["known_accuracy"]["successes"],1)
if __name__=="__main__":unittest.main()
