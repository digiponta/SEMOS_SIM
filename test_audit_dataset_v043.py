import tempfile,unittest
from pathlib import Path
from audit_dataset_v043 import audit,normalized,jaccard,bigrams

class DatasetAuditTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalized("ＡＩ とは"),normalized("AIとは"))
    def test_similarity(self):
        self.assertEqual(jaccard(bigrams("量子力学"),bigrams("量子力学")),1.0)
    def test_development_dataset(self):
        path=Path(__file__).resolve().parent/"data/validation_v043_dev100.csv"
        if not path.exists(): self.skipTest("Dataset unavailable")
        result=audit(path)
        self.assertEqual(result["total"],100)
        self.assertTrue(result["balanced_25_each"])
        self.assertFalse(result["exact_duplicates"])
    def test_cross_split_detection(self):
        with tempfile.TemporaryDirectory() as d:
            val=Path(d)/"val.csv"
            ref=Path(d)/"ref.csv"
            val.write_text("text,label\n量子力学,VM-A\n",encoding="utf-8")
            ref.write_text("text,label\n量子 力学,VM-B\n",encoding="utf-8")
            result=audit(val,[ref])
            self.assertEqual(len(result["exact_duplicates"]),1)
            self.assertFalse(result["pass_basic_checks"])
if __name__=="__main__":unittest.main()
