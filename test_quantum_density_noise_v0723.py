import unittest, math
from quantum_density_noise_v0723 import DensityRegister,semantic_noisy_probabilities,benchmark
from quantum_state_semantic_v0721 import QuantumRegister
class DensityNoiseTests(unittest.TestCase):
 def test_initial(self):
  d=DensityRegister(1);self.assertAlmostEqual(d.trace().real,1);self.assertAlmostEqual(d.purity(),1)
 def test_hadamard_pure(self):
  q=QuantumRegister(2);q.superpose();d=DensityRegister(2);d.set_state(q.state)
  self.assertAlmostEqual(d.purity(),1)
 def test_diagonal(self):
  d=DensityRegister(1);d.channel(0,"amplitude_damping",.5);self.assertAlmostEqual(d.trace().real,1)
 def test_phase_damping_preserves_population(self):
  q=QuantumRegister(1);q.superpose();d=DensityRegister(1);d.set_state(q.state)
  prior=d.probabilities();d.channel(0,"phase_damping",.7)
  self.assertTrue(all(abs(a-b)<1e-10 for a,b in zip(prior,d.probabilities())))
 def test_phase_damping_reduces_purity(self):
  q=QuantumRegister(1);q.superpose();d=DensityRegister(1);d.set_state(q.state);d.channel(0,"phase_damping",1)
  self.assertAlmostEqual(d.purity(),.5)
 def test_amplitude_damping_excited(self):
  d=DensityRegister(1);d.set_state([0j,1+0j]);d.channel(0,"amplitude_damping",1)
  self.assertAlmostEqual(d.probabilities()[0],1)
 def test_no_noise_purity(self):
  q=QuantumRegister(2);q.superpose();d=DensityRegister(2);d.set_state(q.state);d.channel(0,"phase_damping",0)
  self.assertAlmostEqual(d.purity(),1)
 def test_diffusion_unitary(self):
  q=QuantumRegister(2);q.superpose();d=DensityRegister(2);d.set_state(q.state)
  d.phase([math.pi,0,0,0]);d.diffuse()
  self.assertAlmostEqual(d.probabilities()[0],1)
 def test_trace_after_noise(self):
  x=semantic_noisy_probabilities(8,{0:.8,3:.2},.4,"amplitude_damping")
  self.assertAlmostEqual(x["trace"],1)
 def test_distribution(self):
  x=semantic_noisy_probabilities(8,{0:.8,3:.2},.4)
  self.assertAlmostEqual(sum(x["conditional_probabilities"].values()),1)
 def test_ideal_matches(self):
  a=semantic_noisy_probabilities(8,{0:.8,3:.2},0.,rounds=1)
  b=semantic_noisy_probabilities(8,{0:.8,3:.2},0.,rounds=1)
  self.assertEqual(a["conditional_probabilities"],b["conditional_probabilities"])
 def test_noise_decreases_purity(self):
  a=semantic_noisy_probabilities(8,{0:.8,3:.2},0.)
  b=semantic_noisy_probabilities(8,{0:.8,3:.2},.5)
  self.assertLessEqual(b["purity"],a["purity"]+1e-9)
 def test_invalid_noise(self):
  with self.assertRaises(ValueError):semantic_noisy_probabilities(8,{0:.8},1.1)
 def test_invalid_channel(self):
  with self.assertRaises(ValueError):DensityRegister(1).channel(0,"unknown",.1)
 def test_invalid_register(self):
  with self.assertRaises(ValueError):DensityRegister(5)
 def test_bad_amplitudes(self):
  with self.assertRaises(ValueError):DensityRegister(1).set_state([1+0j,1+0j])
 def test_benchmark_rows(self):
  self.assertEqual(len(benchmark(8,2,42,1,(0,.2))["results"]),12)
 def test_benchmark_purity(self):
  self.assertTrue(all(0<=r["mean_purity"]<=1.000001 for r in benchmark(8,2,42,1,(0,.2))["results"]))
 def test_full_amplitude_damping_observed_ground_fallback(self):
  x=semantic_noisy_probabilities(16,{0:.8,3:.2},1.,"amplitude_damping")
  self.assertTrue(x["used_classical_fallback"])
  self.assertEqual(x["selection_mode"],"uniform_classical_fallback")
  self.assertAlmostEqual(x["valid_mass"],0.)
  self.assertAlmostEqual(sum(x["conditional_probabilities"].values()),1.)
  self.assertNotIn("0",x["conditional_probabilities"])
 def test_full_amplitude_damping_unobserved_ground(self):
  x=semantic_noisy_probabilities(16,{1:.8,3:.2},1.,"amplitude_damping")
  self.assertFalse(x["used_classical_fallback"])
  self.assertAlmostEqual(x["conditional_probabilities"]["0"],1.)
 def test_fallback_count_benchmark(self):
  rows=benchmark(16,4,42,1,(1.,))["results"]
  amplified=[x for x in rows if x["channel"]=="amplitude_damping"]
  self.assertTrue(all("fallback_count" in x for x in amplified))
  self.assertTrue(all(0<=x["fallback_rate"]<=1 for x in amplified))
if __name__=="__main__":unittest.main()
