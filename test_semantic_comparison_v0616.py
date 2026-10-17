import unittest
from semantic_comparison_v0616 import compare_answers,SEMANTIC_LABELS
class SemanticComparisonV0616Tests(unittest.TestCase):
 def test_exact(self):
  r=compare_answers("量子力学です。","量子力学です。")
  self.assertEqual(r["semantic_label"],"EXACT_MATCH")
  self.assertEqual(r["character_bigram_jaccard"],1)
 def test_different_not_asserted_contradictory(self):
  r=compare_answers("重ね合わせが重要。","量子状態を扱います。")
  self.assertEqual(r["semantic_label"],"UNDETERMINED")
  self.assertGreaterEqual(r["character_bigram_jaccard"],0)
 def test_no_retrieval(self):
  self.assertEqual(compare_answers("説明",None)["reason"],"NO_RETRIEVAL")
 def test_empty_retrieved(self):
  self.assertEqual(compare_answers("説明","")["semantic_label"],"UNDETERMINED")
 def test_no_automatic_semantic_guess(self):
  for x in ("SEMANTICALLY_EQUIVALENT","COMPLEMENTARY","CONTRADICTORY"):
   self.assertIn(x,SEMANTIC_LABELS)
   self.assertNotEqual(compare_answers("量子力学は理論です。","量子力学は物理の理論です。")["semantic_label"],x)
 def test_bad_type(self):
  with self.assertRaises(TypeError):compare_answers("a",123)
if __name__=="__main__":unittest.main()
