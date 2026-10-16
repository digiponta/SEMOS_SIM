import unittest
from compare_prototypes_v044 import predict_scores,PROTOTYPES
class Vector:
    def __init__(self,n): self.n=n
class CompareTests(unittest.TestCase):
    def test_fixed_prototype_count(self):
        self.assertEqual({k:len(v) for k,v in PROTOTYPES.items()},
                         {"VM-A":5,"VM-B":5,"VM-C":5})
    def test_rankings(self):
        import torch
        a=torch.tensor([1.,0.,0.]);b=torch.tensor([0.,1.,0.]);c=torch.tensor([0.,0.,1.])
        reps=({"VM-A":a,"VM-B":b,"VM-C":c},
              {"VM-A":[a],"VM-B":[b],"VM-C":[c]},
              {"VM-A":a,"VM-B":b,"VM-C":c})
        for mode in ("single","centroid","multi"):
            self.assertEqual(predict_scores(b,mode,reps)[0][0],"VM-B")
    def test_invalid_mode(self):
        import torch
        v=torch.tensor([1.,0.])
        with self.assertRaises(ValueError):
            predict_scores(v,"bad",({"VM-A":v},{},{"VM-A":v}))
if __name__=="__main__":unittest.main()
