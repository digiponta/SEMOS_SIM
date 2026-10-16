import tempfile
import unittest
from pathlib import Path
from benchmark_v040 import KeywordRouter,TFIDFRouter,load_csv,metrics

class BenchmarkTests(unittest.TestCase):
    def test_keyword(self):
        self.assertEqual(KeywordRouter().predict("量子力学"),"VM-A")
        self.assertEqual(KeywordRouter().predict("CUDA"),"VM-B")
        self.assertEqual(KeywordRouter().predict("文学"),"VM-C")
        self.assertEqual(KeywordRouter().predict("未登録項目"),"UNKNOWN")
    def test_metrics(self):
        rows=[{"text":"a","label":"VM-A"},{"text":"b","label":"UNKNOWN"}]
        result=metrics(rows,["VM-A","UNKNOWN"],0.002)
        self.assertEqual(result["known_coverage"],1.0)
        self.assertEqual(result["unknown_reject_rate"],1.0)
        self.assertEqual(result["unknown_reject_precision"],1.0)
        self.assertEqual(result["confusion_matrix"]["VM-A"]["VM-A"],1)
    def test_tfidf(self):
        examples=[{"text":"物理 粒子","label":"VM-A"},{"text":"GPU CUDA","label":"VM-B"},
                  {"text":"文学 作文","label":"VM-C"}]
        model=TFIDFRouter(examples)
        self.assertIn(model.predict("CUDA GPU"),("VM-B","UNKNOWN"))
    def test_cp932_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"japanese.csv"
            path.write_bytes("text,label\n量子力学,VM-A\n".encode("cp932"))
            rows=load_csv(path)
            self.assertEqual(rows[0]["text"],"量子力学")
            self.assertEqual(rows[0]["label"],"VM-A")

    def test_utf8_bom_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"japanese.csv"
            path.write_text("text,label\n物理,VM-A\n",encoding="utf-8-sig")
            rows=load_csv(path)
            self.assertEqual(rows[0]["text"],"物理")

    def test_csv_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"x.csv"
            path.write_text("text,label\nhello,NOPE\n",encoding="utf-8")
            with self.assertRaises(ValueError):
                load_csv(path)

if __name__=="__main__":
    unittest.main()
