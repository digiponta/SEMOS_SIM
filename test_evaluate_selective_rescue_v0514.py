import unittest
from evaluate_selective_rescue_v0514 import evaluate,analyze

def sample(gold,vm,score,margin,contrast,cutoff,agree=True):
    accepted=contrast>=cutoff
    return {"text":f"{gold}:{vm}:{score}:{margin}","gold":gold,"candidate_vm":vm,
            "predicted":vm if accepted else "UNKNOWN","contrast_score":contrast,
            "guard_cutoff":cutoff,"guard_margin":contrast-cutoff,
            "fused_similarity":score,"runner_up_margin":margin,
            "centroid_multi_agree":agree}

class RescueTests(unittest.TestCase):
    def setUp(self):
        self.rows=[
            sample("VM-A","VM-A",.86,.17,.9,1.),
            sample("VM-B","VM-A",.81,.12,.7,1.),
            sample("UNKNOWN","VM-B",.82,.13,.5,1.),
            sample("UNKNOWN","VM-C",.41,.02,-2,1.),
            sample("VM-C","VM-C",.9,.2,2,1.)]
    def test_safe_baseline(self):
        x=evaluate(self.rows,lambda r:False)
        self.assertEqual(x["additional_correct_known"],0)
        self.assertEqual(x["unknown_false_accept_count"],0)
    def test_rescue_accounting(self):
        x=evaluate(self.rows,lambda r:r["fused_similarity"]>=.8)
        self.assertEqual(x["additional_correct_known"],1)
        self.assertEqual(x["additional_wrong_known"],1)
        self.assertEqual(x["additional_unknown_false_accept"],1)
    def test_invalid_trace(self):
        self.rows[0]["predicted"]="VM-A"
        with self.assertRaises(ValueError):evaluate(self.rows,lambda r:False)
    def test_predeclared_probes(self):
        a=analyze({"version":"0.5.11","reference_replay_exact_match":True,"rows":self.rows})
        self.assertIn("none",a["probes"])
        self.assertIn("consensus_strict",a["probes"])

if __name__=="__main__":unittest.main()
