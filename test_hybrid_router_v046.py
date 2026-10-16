import unittest
from hybrid_router_v046 import decision
class HybridDecisionTests(unittest.TestCase):
    def setUp(self):
        self.c=[("VM-A",.8),("VM-B",.6),("VM-C",.4)]
        self.same=[("VM-A",.9),("VM-B",.5),("VM-C",.3)]
        self.diff=[("VM-B",.9),("VM-A",.7),("VM-C",.3)]
    def test_strict_agreement(self):
        self.assertEqual(decision(self.c,self.same),("VM-A","agreement"))
    def test_strict_disagreement(self):
        self.assertEqual(decision(self.c,self.diff),("UNKNOWN","disagreement"))
    def test_strict_absolute_gate(self):
        self.assertEqual(decision(self.c,self.same,threshold=.85)[1],"low_similarity")
    def test_strict_margin_gate(self):
        self.assertEqual(decision(self.c,self.same,margin=.3)[1],"low_margin")
    def test_blend(self):
        self.assertEqual(decision(self.c,self.diff,mode="blend",weight=.7)[0],"VM-A")
        self.assertEqual(decision(self.c,self.diff,mode="blend",weight=.3)[0],"VM-B")
    def test_blend_unknown(self):
        self.assertEqual(decision(self.c,self.same,mode="blend",threshold=.95)[0],"UNKNOWN")
    def test_arguments(self):
        with self.assertRaises(ValueError):decision(self.c,self.same,mode="unsupported")
        with self.assertRaises(ValueError):decision(self.c,self.same,weight=2.)
if __name__=="__main__":unittest.main()
