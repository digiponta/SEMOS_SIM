import unittest
from evaluate_nested_topic_gate_v059 import choose_guard,nested_evaluate,contrast

def sample(i,known):
    vm=("VM-A","VM-B","VM-C")[i%3]
    return {"text":str(i)+str(known),"label":vm if known else "UNKNOWN",
            "best_vm":vm,"score":.88 if known else .43,
            "margin":.14 if known else .015,
            "centroid_top":vm,"multi_top":vm if known else "VM-C" if vm!="VM-C" else "VM-A"}

class NestedGateTests(unittest.TestCase):
    def setUp(self):
        self.rows=[sample(i,known) for i in range(15) for known in (True,False)]
        self.groups=[str(i//2) for i in range(len(self.rows))]
    def test_guard(self):
        c=choose_guard(self.rows,self.groups,folds=3)
        self.assertIn("cutoff",c)
        self.assertLessEqual(c["inner_unknown_false_accept"],.05)
        self.assertEqual(c["inner_unknown_n"],15)
    def test_outer(self):
        m,p,folds=nested_evaluate(self.rows,self.groups,outer_folds=3,inner_folds=2)
        self.assertEqual(len(p),len(self.rows))
        self.assertEqual(sum(f["test_n"] for f in folds),len(self.rows))
        self.assertEqual(m["unknown_n"],15)
    def test_guard_requires_unknown(self):
        with self.assertRaises(ValueError):
            choose_guard(self.rows[::2],self.groups[::2],folds=3)
    def test_unequal(self):
        with self.assertRaises(ValueError):
            nested_evaluate(self.rows,["x"],outer_folds=3)
if __name__=="__main__":unittest.main()
