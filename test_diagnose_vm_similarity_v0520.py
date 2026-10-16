import unittest
from diagnose_vm_similarity_v0520 import roc_auc,describe,analyze
class DiagnosticTest(unittest.TestCase):
 def test_auc(self):
  self.assertEqual(roc_auc([.8,.9],[.1,.2]),1)
  self.assertIsNone(roc_auc([], [.1]))
 def test_stats(self):
  self.assertEqual(describe([.1,.3])["mean"],.2)
 def test_invalid(self):
  with self.assertRaises(ValueError):analyze({"version":"0.5.18"})
if __name__=="__main__":unittest.main()
