import unittest
from analyze_os_advantage_v051 import compare,exact_mcnemar_p,quantile
class StatisticalEvaluationTests(unittest.TestCase):
    def record(self,text,gold,choice):
        return {"text":text,"gold":gold,"selected":choice}
    def fixture(self):
        labels=["VM-A","VM-B","VM-C","UNKNOWN","UNKNOWN"]
        a=["VM-A","VM-A","VM-C","VM-C","UNKNOWN"]
        b=["VM-A","VM-B","VM-A","UNKNOWN","UNKNOWN"]
        return {"kind":"DEVELOPMENT_SIMULATION_NOT_OS_BENCHMARK",
                "results":{"tfidf":{"details":[self.record(str(i),g,s) for i,(g,s) in enumerate(zip(labels,a))]},
                           "semantic_hybrid":{"details":[self.record(str(i),g,s) for i,(g,s) in enumerate(zip(labels,b))]}}}
    def test_mcnemar(self):
        self.assertEqual(exact_mcnemar_p(0,0),1.0)
        self.assertEqual(exact_mcnemar_p(5,0),0.0625)
        self.assertEqual(exact_mcnemar_p(2,2),1.0)
    def test_bootstrap_is_deterministic(self):
        data=self.fixture()
        first=compare(data,iterations=200,seed=7)
        second=compare(data,iterations=200,seed=7)
        self.assertEqual(first,second)
        self.assertAlmostEqual(first["known_correct_routing"]["reference_rate"],2/3)
        self.assertAlmostEqual(first["known_correct_routing"]["candidate_rate"],2/3)
        self.assertEqual(first["unknown_rejection"]["reference_rate"],.5)
        self.assertEqual(first["unknown_rejection"]["candidate_rate"],1.)
    def test_unpaired_rejected(self):
        data=self.fixture()
        data["results"]["semantic_hybrid"]["details"][1]["text"]="different"
        with self.assertRaisesRegex(ValueError,"Unpaired"):compare(data,iterations=100)
    def test_minimum_samples(self):
        with self.assertRaises(ValueError):compare(self.fixture(),iterations=5)
    def test_quantile(self):
        self.assertEqual(quantile([1,2,3,4,5],.5),3)
if __name__=="__main__":unittest.main()
