import unittest
from unittest.mock import patch
from calibrate_hybrid_gate_v053 import calibrate,fused_score_rows

class Engine:
    def vector(self,text):
        return text

class TestHybridCalibration(unittest.TestCase):
    def setUp(self):
        self.rows=[{"text":"a","label":"VM-A"},
                   {"text":"b","label":"VM-B"},
                   {"text":"u","label":"UNKNOWN"}]
    def fake_scores(self,query,mode,reps):
        score={"a":(.9,.4,.2),"b":(.3,.85,.2),"u":(.31,.3,.29)}[query]
        return sorted(zip(("VM-A","VM-B","VM-C"),score),key=lambda x:-x[1])
    def test_score_fusion(self):
        with patch("calibrate_hybrid_gate_v053.make_representations",return_value=()),patch("calibrate_hybrid_gate_v053.predict_scores",side_effect=self.fake_scores):
            scored=fused_score_rows(self.rows,Engine(),.7)
        self.assertEqual([x["best_vm"] for x in scored],["VM-A","VM-B","VM-A"])
        self.assertAlmostEqual(scored[0]["margin"],.5)
    def test_sweep_feasible(self):
        with patch("calibrate_hybrid_gate_v053.make_representations",return_value=()),patch("calibrate_hybrid_gate_v053.predict_scores",side_effect=self.fake_scores):
            best,count=calibrate(self.rows,Engine())
        self.assertIsNotNone(best)
        self.assertLessEqual(best["unknown_false_accept_rate"],.05)
        self.assertGreater(count,0)
    def test_invalid_weight(self):
        with self.assertRaises(ValueError):
            fused_score_rows(self.rows,Engine(),1.2)
if __name__=="__main__":unittest.main()
