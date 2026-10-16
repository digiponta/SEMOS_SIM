import unittest
from compare_gated_prototypes_v045 import evaluate
class TestGatedPrototypes(unittest.TestCase):
    def test_three_modes_with_fake_embedding(self):
        import torch
        class Engine:
            def vector(self,text):
                if "量子" in text or "物理" in text or "数学" in text:return torch.tensor([1.,0.,0.])
                if "CUDA" in text or "GPU" in text or "プログラミング" in text:return torch.tensor([0.,1.,0.])
                if "文学" in text or "日本語" in text:return torch.tensor([0.,0.,1.])
                return torch.nn.functional.normalize(torch.tensor([1.,1.,1.]),dim=0)
        rows=[{"text":"量子力学","label":"VM-A"},{"text":"GPU","label":"VM-B"},
              {"text":"日本語","label":"VM-C"},{"text":"不明","label":"UNKNOWN"}]
        result=evaluate(rows,Engine(),0.25)
        self.assertEqual(set(result),{"single","centroid","multi"})
        for value in result.values():
            self.assertEqual(len(value["raw_scores"]),4)
            self.assertGreater(len(value["eligible_operating_points"]),0)
if __name__=="__main__": unittest.main()
