import unittest
from evaluate_feature_auc_v0516 import auc,analyze
class AUCTest(unittest.TestCase):
 def test_perfect(self):
  self.assertEqual(auc([3,4,1,2],[True,True,False,False]),1)
 def test_ties(self):
  self.assertEqual(auc([2,2],[True,False]),.5)
 def test_empty(self):
  self.assertIsNone(auc([1],[True]))
 def test_version(self):
  with self.assertRaises(ValueError):analyze({"version":"0.5.15"})
if __name__=="__main__":unittest.main()
