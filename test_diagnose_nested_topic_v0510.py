import unittest
from diagnose_nested_topic_v0510 import analyze,bucket
class DiagnosisTests(unittest.TestCase):
 def report(self):
  details=[]
  for i in range(25):
   for label in ("VM-A","VM-B","VM-C","UNKNOWN"):
    predicted=label
    if i==0 and label=="UNKNOWN":predicted="VM-B"
    if i==1 and label=="VM-A":predicted="UNKNOWN"
    details.append({"text":label+str(i),"gold":label,"predicted":predicted,"topic_group":label})
  return {"version":"0.5.9","kind":"EXPLORATORY_NESTED_TOPIC_GROUP_CV",
   "development_sha256":"a","groups_sha256":"b",
   "diagnostics":details,"candidate_nested_oof":{"known_accuracy":74/75,"unknown_false_accept_count":1},
   "outer_folds":[{"fold":k,"train_n":80,"test_n":20,"guard":{"cutoff":k/10,
    "inner_unknown_n":20,"inner_unknown_false_accept":0,
    "inner_unknown_wilson95_upper":.16,"upper_bound_under_budget":False}}
    for k in range(5)]}
 def test_counts(self):
  result=analyze(self.report())
  self.assertEqual(result["global"]["n"],100)
  self.assertEqual(result["global"]["by_class"]["VM-A"]["held"],1)
  self.assertEqual(len(result["unknown_false_accept_cases"]),1)
  self.assertEqual(len(result["known_rejected_cases"]),1)
 def test_cutoff(self):
  self.assertAlmostEqual(analyze(self.report())["cutoff_summary"]["mean"],.2)
 def test_wrong_version(self):
  r=self.report();r["version"]="0.5.8"
  with self.assertRaises(ValueError):analyze(r)
 def test_metric_mismatch(self):
  r=self.report();r["candidate_nested_oof"]["known_accuracy"]=.3
  with self.assertRaises(ValueError):analyze(r)
if __name__=="__main__":unittest.main()
