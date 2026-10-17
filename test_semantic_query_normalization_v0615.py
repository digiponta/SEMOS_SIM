import json,tempfile,unittest
from pathlib import Path
from llm_try_backend_v066 import normalize_definition_query,experimental_lookup

class MiniMod:
 @staticmethod
 def semantic_knowledge_lookup(question,knowledge_path):
  if question!="量子力学とは":return None
  for line in Path(knowledge_path).read_text(encoding="utf-8").splitlines():
   row=json.loads(line)
   if row.get("concept")=="量子力学":return row["concept"],row["assistant"]
  return None

class NormalizationV0615(unittest.TestCase):
 def test_expected(self):
  self.assertEqual(normalize_definition_query("量子力学とは何ですか"),"量子力学とは")
 def test_question_mark(self):
  self.assertEqual(normalize_definition_query("量子力学とは何ですか？"),"量子力学とは")
 def test_unrelated_unchanged(self):
  self.assertIsNone(normalize_definition_query("今日はどうですか"))
 def test_no_substring_matching(self):
  self.assertIsNone(normalize_definition_query("量子力学の説明"))
 def test_live_lookup_contract(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"experiment.jsonl"
   p.write_text(json.dumps({"concept":"量子力学","assistant":"実験用知識回答"},ensure_ascii=False)+"\n",encoding="utf-8")
   hit,meta=experimental_lookup("量子力学とは何ですか",p,MiniMod)
   self.assertEqual(hit,("量子力学","実験用知識回答"))
   self.assertEqual(meta["query_normalized_to"],"量子力学とは")
   self.assertTrue(meta["retrieval_matched"])
   self.assertTrue(meta["read_only"])
if __name__=="__main__":unittest.main()
