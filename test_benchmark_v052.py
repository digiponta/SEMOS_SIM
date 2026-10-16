import csv,tempfile,unittest
from pathlib import Path
from audit_holdout_v052 import audit_holdout
from measure_routing_latency_v052 import measure
class Checks(unittest.TestCase):
    def test_audit_exact_and_near(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);a=p/"holdout.csv";b=p/"reference.csv"
            for path,rows in [(a,[("量子 力学","VM-A"),("未知の料理相談","UNKNOWN")]),
                              (b,[("量子力学","VM-A")])]:
                with path.open("w",encoding="utf-8",newline="") as out:
                    w=csv.writer(out);w.writerow(["text","label"]);w.writerows(rows)
            report=audit_holdout(a,[b])
            self.assertFalse(report["pass_automatic_checks"])
            self.assertEqual(report["exact_overlap_count"],1)
    def test_audit_missing_source(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"a.csv"
            f.write_text("text,label\n未登録の課題,UNKNOWN\n",encoding="utf-8")
            report=audit_holdout(f,[Path(d)/"missing.csv"])
            self.assertFalse(report["pass_automatic_checks"])
    def test_repeated_measurement(self):
        class Router:
            def predict(self,text):return "VM-A"
        results=measure({"stub":Router},[{"text":"x","label":"VM-A"}],repeats=3,warmup=1)
        self.assertEqual(results["stub"]["sample_count"],3)
        self.assertEqual(len(results["stub"]["per_run_means_ms"]),3)
    def test_repetition_guard(self):
        with self.assertRaises(ValueError):measure({},[],repeats=1)
if __name__=="__main__":unittest.main()
