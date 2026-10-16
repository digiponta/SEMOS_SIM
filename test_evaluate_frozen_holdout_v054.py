import unittest
from evaluate_frozen_holdout_v054 import validate_freeze

class FrozenEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.frozen={"status":"FROZEN_DEVELOPMENT_SELECTED_NOT_FINAL_VALIDATED",
                     "threshold":.76,"margin":.06,"weight":.7,
                     "calibration_sha256":"abc","model":"model/example.pt"}
    def test_valid(self):
        self.assertTrue(validate_freeze(self.frozen,"abc"))
    def test_source_mismatch(self):
        with self.assertRaisesRegex(ValueError,"SHA256"):
            validate_freeze(self.frozen,"wrong")
    def test_status(self):
        self.frozen["status"]="draft"
        with self.assertRaisesRegex(ValueError,"status"):
            validate_freeze(self.frozen,"abc")
    def test_invalid_range(self):
        self.frozen["weight"]=1.5
        with self.assertRaisesRegex(ValueError,"weight"):
            validate_freeze(self.frozen,"abc")
    def test_model_required(self):
        self.frozen["model"]=""
        with self.assertRaisesRegex(ValueError,"model"):
            validate_freeze(self.frozen,"abc")

if __name__=="__main__":unittest.main()
