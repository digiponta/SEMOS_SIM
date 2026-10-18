# SEMOS_SIM v0.7.14 — Quantum-inspired Candidate Search (matched comparison)

## Objective

Measure whether a **classically simulated complex-amplitude / interference search** has any benefit relative to conventional Greedy, Beam, Random and a no-interference ablation. This is a methodological pilot of QHA quantum-inspired processing, **not** evidence of physical quantum mechanics, quantum computing, quantum speedup or a production Semantic OS.

The benchmark uses 64 synthetic ring-arranged candidates and 30 seeded smooth utility landscapes. Each strategy may consult the exact same utility oracle only after selecting a candidate; all have exactly 12 distinct utility evaluations per trial. All methods use the same seed schedule. There is no oracle information leakage from the hidden optimum during proposal generation.

Algorithms:
- GREEDY — prefer immediate untested neighbors of current highest-scoring evaluated candidate.
- BEAM — explore immediate neighbors of the top four evaluated candidates.
- RANDOM — uniform untested candidates.
- QI_INTERFERENCE — complex phase update based only on observed utility followed by diffusion across the entire simulated amplitude vector; proposals sampled from squared magnitudes.
- QI_NO_INTERFERENCE — identical phase update **without diffusion** (negative ablation), so untouched magnitudes remain uniform.

Metrics: Success@budget, mean regret, mean best utility, per-evaluation best-utility curve, and a rough operation-count proxy. Equal oracle-call budget DOES NOT imply equal arithmetic work: QI diffusion costs O(N) per iteration.

## Run

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile quantum_inspired_search_v0714.py
python -m unittest -v test_quantum_inspired_search_v0714.py
python quantum_inspired_search_v0714.py --candidates 64 --budget 12 --trials 30 --seed 42 --output results/quantum_inspired_search_v0714.json
$r=Get-Content results/quantum_inspired_search_v0714.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table method,success_at_budget,mean_regret,mean_best,mean_operations_proxy,all_oracle_calls_equal
$r.interference_ablation
```

Results use exclusive create: give a new filename when rerunning.

## Interpretation & next work

We must report a negative result when interference does not improve Success@K, or when gain disappears after accounting for operation costs. Models here have zero relation to real quantum physical phenomena. The ring landscape favors local neighborhood search and should be counterbalanced with shuffled/uncorrelated, multimodal and adversarial workloads.

Next: systematic budget sweeps, held-out seeds, paired uncertainty intervals, classical optimization of equal computational cost, non-redundant phase and diffusion ablations, then semantic candidate processing and 3VM QHA integration.
