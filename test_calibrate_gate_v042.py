import unittest
from calibrate_gate_v042 import score_rows,sweep,apply_gate

ROWS=[
 {"text":"physics","label":"VM-A","best_vm":"VM-A","score":.73,"margin":.16},
 {"text":"gpu","label":"VM-B","best_vm":"VM-B","score":.84,"margin":.25},
 {"text":"literature","label":"VM-C","best_vm":"VM-B","score":.76,"margin":.04},
 {"text":"unknown","label":"UNKNOWN","best_vm":"VM-C","score":.54,"margin":.20},
]
class CalibrationTests(unittest.TestCase):
    def test_gating(self):
        self.assertEqual(apply_gate(ROWS[0],.8,.1),"UNKNOWN")
        self.assertEqual(apply_gate(ROWS[0],.7,.1),"VM-A")
    def test_known_and_unknown_independent_metrics(self):
        r=score_rows(ROWS,.7,.1)
        self.assertAlmostEqual(r["known_coverage"],2/3)
        self.assertAlmostEqual(r["known_accuracy"],2/3)
        self.assertEqual(r["unknown_reject_rate"],1)
        self.assertEqual(r["misroute_rate"],0)
    def test_sweep_unknown_constraint(self):
        best,_=sweep(ROWS,0)
        self.assertIsNotNone(best)
        self.assertEqual(best["unknown_false_accept_rate"],0)
        self.assertGreaterEqual(best["known_accuracy"],2/3)
    def test_requires_unknown_cases(self):
        with self.assertRaises(ValueError):
            sweep(ROWS[:2])
if __name__=="__main__":
    unittest.main()
