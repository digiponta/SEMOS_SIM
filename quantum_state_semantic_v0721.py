"""SEMOS_SIM v0.7.21: ideal quantum state-vector simulator + semantic candidate adapter.

Educational, noiseless CLASSICAL state-vector simulation (not quantum hardware).
Basis states encode candidates. No access to unobserved candidate utility.
"""
import argparse,cmath,json,math,random
from pathlib import Path

class QuantumRegister:
    def __init__(self,qubits):
        if not 1<=qubits<=12:raise ValueError("qubits must be in [1,12]")
        self.qubits=qubits;self.n=1<<qubits
        self.state=[0j]*self.n;self.state[0]=1+0j
    def norm(self):return sum(abs(z)**2 for z in self.state)
    def _check(self):
        if not math.isclose(self.norm(),1.,rel_tol=1e-9,abs_tol=1e-9):
            raise ArithmeticError("quantum state norm changed")
    def hadamard(self,wire):
        if not 0<=wire<self.qubits:raise ValueError("wire")
        shift=1<<wire;scale=1/math.sqrt(2)
        for i in range(self.n):
            if i&shift:continue
            j=i|shift;a=self.state[i];b=self.state[j]
            self.state[i]=(a+b)*scale;self.state[j]=(a-b)*scale
        self._check()
    def superpose(self):
        for w in range(self.qubits):self.hadamard(w)
    def phase_oracle(self,angles):
        if len(angles)!=self.n:raise ValueError("angles must match basis")
        self.state=[a*cmath.exp(1j*phi) for a,phi in zip(self.state,angles)]
        self._check()
    def diffuse(self):
        # Grover D=2|s><s|-I (unitary reflection over uniform |s>).
        mean=sum(self.state)/self.n
        self.state=[2*mean-a for a in self.state]
        self._check()
    def probabilities(self):return [abs(a)**2 for a in self.state]
    def measure(self,seed=None):
        rng=random.Random(seed);t=rng.random()
        for i,p in enumerate(self.probabilities()):
            t-=p
            if t<=0:return i
        return self.n-1
    def snapshot(self):
        return [{"basis":i,"real":z.real,"imag":z.imag,"probability":abs(z)**2}
                for i,z in enumerate(self.state)]

def semantic_phase_angles(candidate_count,observed,similarity,strength=math.pi):
    """Build phase angles using only observed utilities and candidate similarity.

    Invalid/padded basis states never become valid search candidates.
    similarity(i,j) supplied by caller, e.g. observed Semantic Memory similarity.
    """
    if candidate_count<2 or strength<0:raise ValueError("candidate_count/strength")
    for j,v in observed.items():
        if not isinstance(j,int) or not 0<=j<candidate_count or not 0<=v<=1:
            raise ValueError("observed entries must be index->normalized utility")
    angles=[0.]*candidate_count
    for i in range(candidate_count):
        if i in observed:continue
        if observed:
            weights=[max(0.,float(similarity(i,j))) for j in observed]
            s=sum(weights)
            score=sum(w*v for w,v in zip(weights,observed.values()))/s if s>0 else .5
            angles[i]=strength*(2*score-1)
    return angles

def quantum_semantic_search(candidate_count,observed,similarity,rounds=1,seed=42):
    """Return next unexplored candidate via unitary steps and Born-rule measurement.

    Rejection-sampling on already observed/padded states conditions the measurement
    onto valid candidate outcomes. No hidden utility lookup is performed.
    """
    if candidate_count<2 or rounds<0:raise ValueError("candidate_count/rounds")
    qubits=max(1,(candidate_count-1).bit_length())
    if qubits>12:raise ValueError("too many candidates")
    register=QuantumRegister(qubits);register.superpose()
    valid=[i for i in range(candidate_count) if i not in observed]
    if not valid:raise ValueError("no remaining candidates")
    angles=semantic_phase_angles(candidate_count,observed,similarity)
    angles.extend([0.]*(register.n-candidate_count))
    for _ in range(rounds):
        register.phase_oracle(angles)
        register.diffuse()
    p=register.probabilities()
    remaining_mass=sum(p[i] for i in valid)
    # Conditioning equivalent to repeated measurement until a valid unseen outcome.
    if remaining_mass<=1e-14:raise ArithmeticError("no probability mass on valid states")
    rng=random.Random(seed);t=rng.random()*remaining_mass;choice=valid[-1]
    for i in valid:
        t-=p[i]
        if t<=0:choice=i;break
    return {"version":"0.7.21","candidate":choice,"qubits":qubits,
            "rounds":rounds,"norm":register.norm(),"valid_probability_mass":remaining_mass,
            "conditional_probabilities":{str(i):p[i]/remaining_mass for i in valid},
            "observed_count":len(observed),"physics":"ideal_unitary_statevector_classical_simulation"}

def benchmark(n=16,rounds=1,trials=100,seed=42):
    from semantic_weighted_interference_v0716 import workload,similarity
    if n<2 or n>4096 or rounds<0 or trials<1:raise ValueError("benchmark")
    rows=[]
    for landscape in ("smooth","shuffled","multimodal"):
        successes=0
        for t in range(trials):
            v=workload(n,seed+t,landscape)
            initial=random.Random(seed+100000+t).sample(range(n),min(4,n-1))
            observed={i:v[i] for i in initial}
            result=quantum_semantic_search(n,observed,
                lambda i,j:similarity(i,j,n),rounds,seed+200000+t)
            picked=result["candidate"]
            successes+=int(v[picked]==max(v))
        rows.append({"landscape":landscape,"trials":trials,
                     "one_step_optimum_hit":successes/trials})
    return {"version":"0.7.21","kind":"IDEAL_STATEVECTOR_SEMANTIC_QI",
            "parameters":{"candidates":n,"rounds":rounds,"trials":trials,"seed":seed},
            "results":rows,
            "limitations":["Classical simulation of ideal quantum amplitudes; no quantum computer",
               "Unobserved utilities not provided to phase oracle",
               "Candidate graph kernel used only through observed utility",
               "Does not demonstrate quantum speedup",
               "Single-next-candidate test, not matched full-budget search",
               "Zero-phase plus diffusion alone leaves uniform amplitude unchanged"]}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",type=int,default=16)
    p.add_argument("--rounds",type=int,default=1)
    p.add_argument("--trials",type=int,default=100)
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--output",required=True)
    a=p.parse_args();r=benchmark(a.candidates,a.rounds,a.trials,a.seed)
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(r,f,ensure_ascii=False,indent=2)
    print("Wrote:",path)
    for row in r["results"]:print(row)
if __name__=="__main__":main()
