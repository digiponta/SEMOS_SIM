"""SEMOS_SIM v0.7.23 — ideal/noisy density-matrix quantum simulator.
No quantum hardware. Exact Kraus channels, small Hilbert spaces (<= 4 qubits).
"""
import argparse, cmath, json, math, random
from pathlib import Path
from quantum_state_semantic_v0721 import QuantumRegister, semantic_phase_angles
from semantic_weighted_interference_v0716 import similarity, workload

def matmul(a,b):
 n=len(a)
 return [[sum(a[i][k]*b[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
def dagger(a):
 return [[a[j][i].conjugate() for j in range(len(a))] for i in range(len(a))]
class DensityRegister:
 def __init__(self,qubits):
  if not 1<=qubits<=4:raise ValueError("qubits 1..4")
  self.qubits=qubits;self.n=1<<qubits
  self.rho=[[complex(i==0 and j==0) for j in range(self.n)] for i in range(self.n)]
 def set_state(self,amplitudes):
  if len(amplitudes)!=self.n or abs(sum(abs(x)**2 for x in amplitudes)-1)>1e-9:
   raise ValueError("normalized amplitudes required")
  self.rho=[[a*b.conjugate() for b in amplitudes] for a in amplitudes]
 def trace(self):return sum(self.rho[i][i] for i in range(self.n))
 def purity(self):return sum((self.rho[i][j]*self.rho[j][i]).real for i in range(self.n) for j in range(self.n))
 def probabilities(self):return [max(0.,self.rho[i][i].real) for i in range(self.n)]
 def validate(self,tol=1e-8):
  if abs(self.trace()-1)>tol:raise ArithmeticError("trace")
  if any(abs(self.rho[i][j]-self.rho[j][i].conjugate())>tol for i in range(self.n) for j in range(self.n)):
   raise ArithmeticError("Hermiticity")
  if any(self.rho[i][i].real < -tol for i in range(self.n)):raise ArithmeticError("negative diagonal")
  # PSD is guaranteed by initialization and exact Kraus/unitary maps; full eigenvalue check in tests.
 def unitary(self,u):
  if len(u)!=self.n or any(len(row)!=self.n for row in u):raise ValueError("unitary dimensions")
  self.rho=matmul(matmul(u,self.rho),dagger(u));self.validate()
 def apply_kraus(self,operators):
  out=[[0j for _ in range(self.n)] for _ in range(self.n)]
  for k in operators:
   contribution=matmul(matmul(k,self.rho),dagger(k))
   for i in range(self.n):
    for j in range(self.n):out[i][j]+=contribution[i][j]
  self.rho=out;self.validate()
 def channel(self,wire,kind,gamma):
  if kind not in ("phase_damping","amplitude_damping") or not 0<=wire<self.qubits or not 0<=gamma<=1:
   raise ValueError("channel settings")
  if kind=="phase_damping":
   local=[[[1.,0.],[0.,math.sqrt(1-gamma)]],[[0.,0.],[0.,math.sqrt(gamma)]]]
  else:
   local=[[[1.,0.],[0.,math.sqrt(1-gamma)]],[[0.,math.sqrt(gamma)],[0.,0.]]]
  full=[]
  mask=1<<wire
  for k in local:
   operator=[[0j for _ in range(self.n)] for _ in range(self.n)]
   for source in range(self.n):
    bit=1 if source&mask else 0
    for destbit in (0,1):
     destination=(source&~mask)|(destbit*mask)
     operator[destination][source]=complex(k[destbit][bit])
   full.append(operator)
  self.apply_kraus(full)
 def phase(self,angles):
  if len(angles)!=self.n:raise ValueError("phase dimensions")
  ph=[cmath.exp(1j*a) for a in angles]
  self.rho=[[self.rho[i][j]*ph[i]*ph[j].conjugate() for j in range(self.n)] for i in range(self.n)]
  self.validate()
 def diffuse(self):
  n=self.n
  u=[[2/n-(1 if i==j else 0) for j in range(n)] for i in range(n)]
  self.unitary(u)

def semantic_noisy_probabilities(n,observed,noise=0.,channel="phase_damping",rounds=1):
 if not 2<=n<=16 or not 0<=noise<=1 or rounds<0:raise ValueError("semantic noisy parameters")
 q=QuantumRegister(max(1,(n-1).bit_length()));q.superpose()
 d=DensityRegister(q.qubits);d.set_state(q.state)
 angles=semantic_phase_angles(n,observed,lambda i,j:similarity(i,j,n))
 angles.extend([0.]*(d.n-n))
 for _ in range(rounds):
  d.phase(angles);d.diffuse()
  for w in range(d.qubits):d.channel(w,channel,noise)
 valid=[i for i in range(n) if i not in observed]
 if not valid:raise ValueError("no unobserved candidates")
 raw=d.probabilities();mass=sum(raw[i] for i in valid)
 if mass<=1e-12:raise ArithmeticError("zero unseen mass")
 return {"conditional_probabilities":{str(i):raw[i]/mass for i in valid},
         "trace":d.trace().real,"purity":d.purity(),"valid_mass":mass}

def benchmark(candidates=16,trials=100,seed=42,rounds=1,noise_levels=(0.,.05,.2,.5,1.)):
 levels=tuple(noise_levels)
 if trials<1 or not levels or any(not 0<=x<=1 for x in levels):raise ValueError("benchmark")
 result=[]
 for kind in ("smooth","shuffled","multimodal"):
  for channel in ("phase_damping","amplitude_damping"):
   for noise in levels:
    success=0;purities=[]
    for t in range(trials):
     v=workload(candidates,seed+t,kind)
     pilot=random.Random(seed+100000+t).sample(range(candidates),min(4,candidates-1))
     observed={i:v[i] for i in pilot}
     x=semantic_noisy_probabilities(candidates,observed,noise,channel,rounds)
     rng=random.Random(seed+200000+t)
     z=rng.random();selected=int(list(x["conditional_probabilities"])[-1])
     for key,p in x["conditional_probabilities"].items():
      z-=p
      if z<=0:selected=int(key);break
     success+=int(v[selected]==max(v))
     purities.append(x["purity"])
    result.append({"landscape":kind,"channel":channel,"noise":noise,
                   "trials":trials,"one_step_hit":success/trials,
                   "mean_purity":sum(purities)/trials})
 return {"version":"0.7.23","kind":"DENSITY_MATRIX_NOISE_STUDY",
         "parameters":{"candidates":candidates,"trials":trials,"seed":seed,"rounds":rounds,"noise_levels":list(levels)},
         "results":result,"limitations":["Classical ideal-density-matrix simulation, not physical quantum hardware",
           "Small registers only (<=4 qubits), no claimed quantum speedup",
           "Each one-step hit is not final 5-call success; reference v0.7.22 for matched baseline",
           "Channel noise is applied independently to every wire after each phase/diffusion round",
           "Synthetic ring similarity; no production Semantic Memory"]}
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--candidates",type=int,default=16)
 p.add_argument("--trials",type=int,default=100)
 p.add_argument("--seed",type=int,default=42)
 p.add_argument("--rounds",type=int,default=1)
 p.add_argument("--noise-levels",default="0,0.05,0.2,0.5,1.0")
 p.add_argument("--output",required=True)
 a=p.parse_args()
 r=benchmark(a.candidates,a.trials,a.seed,a.rounds,tuple(float(x) for x in a.noise_levels.split(",")))
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
 with out.open("x",encoding="utf-8") as f:json.dump(r,f,ensure_ascii=False,indent=2)
 print("Wrote:",out)
 for x in r["results"]:print(x["landscape"],x["channel"],x["noise"],"hit",x["one_step_hit"],"purity",round(x["mean_purity"],6))
if __name__=="__main__":main()
