import json,tempfile,unittest
from pathlib import Path
from llm_try_backend_v066 import experimental_lookup
class FakeMod:
 @staticmethod
 def semantic_knowledge_lookup(question,knowledge_path):
  rows=[json.loads(x) for x in Path(knowledge_path).read_text(encoding="utf-8").splitlines()]
  return next(((x["concept"],x["assistant"]) for x in rows if x["concept"]=="量子力学" and "量子力学" in question),None)
class TestExperimentalKnowledgeV0614(unittest.TestCase):
 def test_lookup(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"fixture.jsonl"
   p.write_text(json.dumps({"concept":"量子力学","assistant":"検索からの回答"},ensure_ascii=False),encoding="utf-8")
   hit,meta=experimental_lookup("量子力学とは",p,FakeMod)
   self.assertEqual(hit,("量子力学","検索からの回答"))
   self.assertTrue(meta["read_only"])
   self.assertEqual(len(meta["sha256"]),64)
 def test_no_file(self):
  self.assertEqual(experimental_lookup("量子力学とは",None,FakeMod),(None,None))
 def test_missing_file(self):
  with self.assertRaises(FileNotFoundError):experimental_lookup("量子力学とは","Z:/no-such-file.jsonl",FakeMod)
if __name__=="__main__":unittest.main()
