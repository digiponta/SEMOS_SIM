import unittest
from benchmark_os_advantage_v050 import RoundRobin,dispatch,run
class Stub:
    def __init__(self,labels):self.labels=iter(labels)
    def predict(self,text):return next(self.labels)
class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{"text":"A","label":"VM-A"},{"text":"B","label":"VM-B"},
                   {"text":"C","label":"VM-C"},{"text":"U","label":"UNKNOWN"}]
    def test_round_robin(self):
        rr=RoundRobin()
        self.assertEqual([rr.predict("") for _ in range(4)],["VM-A","VM-B","VM-C","VM-A"])
    def test_perfect_routing_proxy(self):
        m=dispatch(self.rows,Stub(["VM-A","VM-B","VM-C","UNKNOWN"]))
        self.assertEqual(m["known_task_completion_proxy"],1.0)
        self.assertEqual(m["unknown_rejection_rate"],1.0)
        self.assertEqual(m["incorrect_known_dispatches"],0)
    def test_wrong_and_unknown(self):
        m=dispatch(self.rows,Stub(["VM-B","UNKNOWN","VM-C","VM-A"]))
        self.assertAlmostEqual(m["known_task_completion_proxy"],1/3)
        self.assertAlmostEqual(m["known_coverage"],2/3)
        self.assertEqual(m["unknown_false_dispatch_rate"],1.)
        self.assertEqual(m["incorrect_known_dispatches"],1)
    def test_baseline_without_model(self):
        result=run(self.rows,self.rows)
        self.assertEqual(set(result),{"round_robin","keyword","tfidf"})
if __name__=="__main__":unittest.main()
