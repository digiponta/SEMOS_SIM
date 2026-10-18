# SEMOS_SIM v0.7.21 — Ideal Quantum State Vector and Semantic Adapter

This version introduces an **ideal gate-level quantum-mechanics simulation**, implemented entirely on a classical CPU. This is materially different from a generic complex-weight heuristic: it explicitly maintains a normalized state vector, implements unitary single-qubit Hadamard gates, a diagonal phase oracle, unitary Grover mean-inversion diffusion, Born-rule measurement, and checks probability conservation.

## Mathematical model

- Register: `n` qubits, `2^n` basis states, `|psi> = sum_i alpha_i |i>` with `sum_i |alpha_i|^2 = 1`.
- Hadamard: `H = [[1,1],[1,-1]] / sqrt(2)`. Apply H on every wire to prepare uniform superposition.
- Phase oracle: `U_phi|i> = exp(j phi_i)|i>`. `phi_i` is computed from known observed utility and supplied candidate similarity only. Unknown utility values are never looked up.
- Diffusion: `D = 2|s><s| - I`. Unitary reflection; phase oracle and diffusion together can produce interference.
- Measurement: sample `p_i = |alpha_i|^2`; condition on valid unseen candidate states (avoids observed indices and padded basis states).

**Important qualification:** the observed-data Semantic phase oracle is not an oracle that marks a true unknown optimum. Consequently there is no guarantee of Grover's optimality or asymptotic quantum search speedup. This is a classical state-vector emulator, not a quantum machine. Using estimated utility in phases is a modeling choice; it is not a physically validated QHA architecture.

A known 2-qubit Grover sanity test marks state `|00>` using a pi phase and checks it gets probability nearly 1 after one diffusion step. This verifies elementary interference behavior independently from the Semantic use case.

## Code

- `quantum_state_semantic_v0721.py` — `QuantumRegister`, phase construction, semantic adapter, synthetic benchmark.
- `test_quantum_state_semantic_v0721.py` — 19 checks for unitary norm, Hadamard, phase-modulus preservation, Grover sanity, padding and measurement.

## Windows PowerShell

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile quantum_state_semantic_v0721.py
python -m unittest -v test_quantum_state_semantic_v0721.py
python quantum_state_semantic_v0721.py --candidates 16 --rounds 1 --trials 100 --seed 42 --output results/quantum_state_semantic_v0721.json
$r=Get-Content results/quantum_state_semantic_v0721.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table landscape,trials,one_step_optimum_hit
```

Exclusive output creation requires a different filename on subsequent runs.

## Next investigations

Measure against a classical kernel-search baseline using identical observed pilot evaluations, matched full evaluation budgets, and equal CPU time. Quantify whether phase encoding and diffusion improve probability assigned to *held-out* high-value states. Study noisy/decohering channels with density matrices, explicit entanglement for multi-register semantic relationships, and QHA dispatch integration. None are implemented yet.
