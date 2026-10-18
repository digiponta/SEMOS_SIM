import unittest
from semantic_processing_unit_v071 import SemanticUnit,ProcessingRequest,SPUSimulator,sample_requests

class SPUSimulatorV071Tests(unittest.TestCase):
 def unit(self,meaning=None,context=None,version=1):
  return SemanticUnit("S",meaning or {"concept":"X"},context or {},version)
 def test_fixture(self):
  result=SPUSimulator().run(sample_requests())
  self.assertEqual((result["requests"],result["executed"],result["reused"]),(4,3,1))
  self.assertEqual(result["work_cost"],9.0)
 def test_canonical_equivalence(self):
  a=ProcessingRequest("a",self.unit(),"EVALUATE")
  b=ProcessingRequest("b",SemanticUnit("another",{"concept":"X"}),"EVALUATE")
  self.assertEqual(SPUSimulator().run([a,b])["reused"],1)
 def test_operation_blocks_reuse(self):
  a=ProcessingRequest("a",self.unit(),"EVALUATE")
  b=ProcessingRequest("b",self.unit(),"EXPLAIN")
  self.assertEqual(SPUSimulator().run([a,b])["reused"],0)
 def test_context_blocks_reuse(self):
  a=ProcessingRequest("a",self.unit(),"EVALUATE")
  b=ProcessingRequest("b",self.unit(context={"scope":"different"}),"EVALUATE")
  self.assertEqual(SPUSimulator().run([a,b])["reused"],0)
 def test_version_blocks_reuse(self):
  a=ProcessingRequest("a",self.unit(),"EVALUATE")
  b=ProcessingRequest("b",self.unit(version=2),"EVALUATE")
  self.assertEqual(SPUSimulator().run([a,b])["reused"],0)
 def test_parameter_blocks_reuse(self):
  a=ProcessingRequest("a",self.unit(),"EVALUATE",parameters={"precision":1})
  b=ProcessingRequest("b",self.unit(),"EVALUATE",parameters={"precision":2})
  self.assertEqual(SPUSimulator().run([a,b])["reused"],0)
 def test_dependencies_block_reuse(self):
  a=ProcessingRequest("a",self.unit(),"EVALUATE")
  b=ProcessingRequest("b",self.unit(),"EVALUATE",("a",))
  self.assertEqual(SPUSimulator().run([a,b])["reused"],0)
 def test_cycle_rejected(self):
  a=ProcessingRequest("a",self.unit(),"EVALUATE",("b",))
  b=ProcessingRequest("b",self.unit(),"EVALUATE",("a",))
  with self.assertRaises(ValueError):SPUSimulator().run([a,b])
 def test_missing_dependency_rejected(self):
  with self.assertRaises(ValueError):SPUSimulator().run([ProcessingRequest("a",self.unit(),"EVALUATE",("unknown",))])
 def test_duplicate_id_rejected(self):
  p=ProcessingRequest("a",self.unit(),"EVALUATE")
  with self.assertRaises(ValueError):SPUSimulator().run([p,p])
 def test_empty(self):
  r=SPUSimulator().run([])
  self.assertEqual((r["executed"],r["reused"]),(0,0))
if __name__=="__main__":unittest.main()
