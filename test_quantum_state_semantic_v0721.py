import unittest,math
from quantum_state_semantic_v0721 import QuantumRegister,semantic_phase_angles,quantum_semantic_search,benchmark
class QuantumStateTests(unittest.TestCase):
 def test_zero(self):
  q=QuantumRegister(2);self.assertEqual(q.probabilities(),[1.,0.,0.,0.])
 def test_hadamard(self):
  q=QuantumRegister(1);q.hadamard(0)
  self.assertAlmostEqual(q.probabilities()[0],.5)
  self.assertAlmostEqual(q.probabilities()[1],.5)
 def test_hadamard_twice_identity(self):
  q=QuantumRegister(2);q.hadamard(0);q.hadamard(0)
  self.assertAlmostEqual(q.probabilities()[0],1.)
 def test_uniform(self):
  q=QuantumRegister(3);q.superpose()
  self.assertTrue(all(abs(p-.125)<1e-10 for p in q.probabilities()))
 def test_phase_norm(self):
  q=QuantumRegister(2);q.superpose();q.phase_oracle([0,1,2,3])
  self.assertAlmostEqual(q.norm(),1.)
 def test_phase_modulus(self):
  q=QuantumRegister(2);q.superpose();old=q.probabilities()
  q.phase_oracle([0,1,2,3]);self.assertEqual(old,q.probabilities())
 def test_diffusion_norm(self):
  q=QuantumRegister(2);q.superpose();q.phase_oracle([math.pi,0,0,0]);q.diffuse()
  self.assertAlmostEqual(q.norm(),1.)
 def test_grover_marked(self):
  q=QuantumRegister(2);q.superpose();q.phase_oracle([math.pi,0,0,0]);q.diffuse()
  self.assertAlmostEqual(q.probabilities()[0],1.)
 def test_diffusion_twice_identity(self):
  q=QuantumRegister(2);q.superpose();q.phase_oracle([math.pi,0,0,0])
  old=q.state[:];q.diffuse();q.diffuse()
  self.assertTrue(all(abs(a-b)<1e-10 for a,b in zip(old,q.state)))
 def test_measure_valid(self):
  q=QuantumRegister(2);q.superpose()
  self.assertIn(q.measure(9),range(4))
 def test_no_hidden_utility(self):
  angles=semantic_phase_angles(4,{0:.8},lambda i,j:1.)
  self.assertEqual(len(angles),4)
 def test_zero_similarity(self):
  a=semantic_phase_angles(4,{0:.8},lambda i,j:0.)
  self.assertEqual(a[0],0.)
 def test_search_unseen(self):
  out=quantum_semantic_search(6,{0:.8,4:.2},lambda i,j:1.,1,1)
  self.assertNotIn(out["candidate"],(0,4))
  self.assertAlmostEqual(sum(out["conditional_probabilities"].values()),1.)
 def test_padded_basis(self):
  out=quantum_semantic_search(5,{0:.5},lambda i,j:1.,1,2)
  self.assertLess(out["candidate"],5)
 def test_reproducible(self):
  args=(6,{0:.8},lambda i,j:1.,1,42)
  self.assertEqual(quantum_semantic_search(*args)["candidate"],quantum_semantic_search(*args)["candidate"])
 def test_bad_rounds(self):
  with self.assertRaises(ValueError):quantum_semantic_search(4,{},lambda i,j:1.,-1)
 def test_all_observed(self):
  with self.assertRaises(ValueError):quantum_semantic_search(4,{i:.5 for i in range(4)},lambda i,j:1.)
 def test_bad_qubits(self):
  with self.assertRaises(ValueError):QuantumRegister(0)
 def test_small_benchmark(self):
  self.assertEqual(len(benchmark(8,1,2)["results"]),3)
if __name__=="__main__":unittest.main()
