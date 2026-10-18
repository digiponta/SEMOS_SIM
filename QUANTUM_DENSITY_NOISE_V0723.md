# SEMOS_SIM v0.7.23 — Density matrix, phase damping, amplitude damping

An **ideal quantum-mechanical open-system model** is implemented in pure Python and evaluated with synthetic Semantic candidate search. This is a **classical CPU simulation**, not quantum hardware and not evidence of quantum acceleration.

## Quantum state

`DensityRegister(qubits)` stores rho (2^q by 2^q), initially |0...0><0...0| or a pure-state outer product. For the noise-free circuit, the representation reproduces the v0.7.21 state-vector probabilities.

Ideal phase and diffusion evolve via U rho U†. Noise channels use the completely positive trace-preserving Kraus map rho' = sum_k E_k rho E_k†. For a local qubit with gamma in [0,1]:

Phase damping: E0 = diag(1,sqrt(1-gamma)), E1 = diag(0,sqrt(gamma)).

Amplitude damping: E0 = diag(1,sqrt(1-gamma)), E1 = [[0,sqrt(gamma)],[0,0]].

The noise channel runs independently on each qubit after every phase/diffusion round. Probability trace, Hermiticity, and nonnegative diagonal are checked in the runtime. **Full density-matrix eigenvalue PSD checking is not performed at runtime**; positivity follows mathematically for valid states evolved by the implemented Kraus/unitary operations. Pure-state purity Tr(rho²) and conditional probabilities for as-yet-unobserved candidates are exposed.

## Execute (PowerShell)
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile quantum_density_noise_v0723.py
python -m unittest -v test_quantum_density_noise_v0723.py
python quantum_density_noise_v0723.py --candidates 16 --trials 100 --seed 42 --rounds 1 --noise-levels 0,0.05,0.2,0.5,1.0 --output results/quantum_density_noise_v0723.json
$r=Get-Content results/quantum_density_noise_v0723.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table landscape,channel,noise,trials,one_step_hit,mean_purity
```

Exclusive output creation; use another name on reruns. Max register size is 4 qubits due to classical O(4^q) density matrix memory.

## Interpretation
Zero noise is the ideal baseline. Increasing gamma may reduce coherence/purity but does not guarantee monotonic success changes, since the utility-driven Semantic phase oracle may be inaccurate. `one_step_hit` is a newly proposed one-shot candidate metric with four pilot observations (not matched full-budget final success). Preserve the matched classical baseline from v0.7.22 for subsequent evaluation. Synthetic ring similarity is not actual Semantic Memory.

## Next
v0.7.24: demonstrate entanglement and coupled Semantic registers with Bell/controlled gates and partial trace tests. Then v0.7.25: integrate with real Semantic Memory/SPU request dispatch and matched conventional baselines.


## Hotfix: zero unseen mass under full amplitude damping

At `gamma=1`, independent amplitude-damping channels collapse the quantum state to the computational basis ground state `|0000>`. If this state was already observed during the pilot, then `sum_{i in unseen} P(i)=0`, so **conditional Born measurement on unseen states is mathematically undefined**. The original code raised `ArithmeticError("zero unseen mass")`.

The updated version implements a **clearly labeled, nonquantum fallback**: uniform random choice among unseen candidates when the quantum valid mass is <=1e-12. It exposes `used_classical_fallback`, `selection_mode`, `valid_mass`, `fallback_count`, `fallback_rate`, and `min_valid_mass` in JSON. This is not a claim that the noisy quantum state itself could have measured one of the excluded states. When interpreting success curves at extreme noise, inspect fallback rate: the algorithm can be entirely classical.

The hotfix adds three regression tests, for 21 total tests. Existing output paths are opened in exclusive mode, so use a new name when re-running, e.g. `results/quantum_density_noise_v0723_fixed.json`.
