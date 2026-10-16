import unittest
from compare_gate_variants_v056 import analyze,predict_variant
class GateVariantTests(unittest.TestCase):
 def setUp(self):
  self.rows=[
   {"label":"VM-A","best_vm":"VM-A","score":.72,"margin":.1,"centroid_top":"VM-A","multi_top":"VM-A"},
   {"label":"VM-B","best_vm":"VM-B","score":.88,"margin":.15,"centroid_top":"VM-B","multi_top":"VM-A"},
   {"label":"UNKNOWN","best_vm":"VM-A","score":.65,"margin":.03,"centroid_top":"VM-A","multi_top":"VM-B"}]
 def test_reference(self):
  baseline,variants=analyze(self.rows)
  self.assertEqual(baseline["known_accuracy"],.5)
  self.assertEqual(baseline["unknown_reject"],1.)
  self.assertEqual(len(variants),14)
 def test_class_specific(self):
  pred=predict_variant(self.rows,{"VM-A":.7,"VM-B":.76,"VM-C":.76},.06)
  self.assertEqual(pred,["VM-A","VM-B","UNKNOWN"])
 def test_consensus(self):
  self.assertEqual(predict_variant(self.rows,.7,.06,True),["VM-A","UNKNOWN","UNKNOWN"])
 def test_missing_unknown(self):
  with self.assertRaises(ValueError):analyze(self.rows[:2])
if __name__=="__main__":unittest.main()
