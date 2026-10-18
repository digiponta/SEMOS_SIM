# SEMOS_SIM v0.7.18 — Phase and Temperature Isolation

v0.7.17 introduced temperature=0.2 and changed selection probabilities relative to v0.7.16. This benchmark explicitly isolates **temperature tuning** and compares complex phase updates with non-complex kernel strategies. All models are ordinary classical algorithms; it does not demonstrate a physical quantum advantage.

## Design
- Three synthetic utility landscapes (smooth, shuffled, multimodal), candidates=64.
- Same 8/12/24 candidate utility-oracle calls per method.
- **Dev**: 40 landscape seeds starting at 42. Each probabilistic method independently tunes temperature over 0.1, 0.2, 0.5, 1.0 using lowest mean dev regret, with dev success as tiebreak.
- **Holdout**: 120 fresh seeds starting at 30000; temperatures locked beforehand.
- Methods: QI_COMPLEX (complex-phase amplitude), REAL_AMPLITUDE (real signed amplitude), REAL_KERNEL_SOFTMAX (ordinary kernel expected utility plus exploration), KERNEL_UCB (deterministic), RANDOM.
- 95% paired bootstrap intervals for QI success/regret differences, median CPU wall-clock diagnostic timing.
- The comparison to REAL_AMPLITUDE is informative, **not a pure phase deletion**: real-vs-complex update formulas and their nonlinearities both differ. A clean unitary/phase-only causal intervention remains for future work.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile quantum_phase_isolation_v0718.py
python -m unittest -v test_quantum_phase_isolation_v0718.py
python quantum_phase_isolation_v0718.py --dev-trials 40 --holdout-trials 120 --dev-seed 42 --holdout-seed 30000 --budgets 8,12,24 --bootstrap 500 --output results/quantum_phase_isolation_v0718.json
$r=Get-Content results/quantum_phase_isolation_v0718.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table landscape,budget,method,selected_temperature,holdout_success,holdout_mean_regret,median_runtime_ms
$r.contrasts | Format-Table landscape,budget,comparison,success_delta,success_ci95,regret_delta,regret_ci95
```

A quick smoke run can use --dev-trials 5 --holdout-trials 10 --budgets 8 --bootstrap 100 and a separate output path. Output is create-only.

## Scientific limitations
This is a synthetic ring similarity, not LLM_SEM, real semantic embeddings or production QHA workloads. Models have equal oracle-call budgets, not equal CPU budgets. Multiple comparisons are exploratory; positive single-cell results require replication and correction. Real and complex amplitude transformations may differ in additional nonlinear ways. Future work should use an exactly matched phase-off operator, tune hyperparameters with a computational-cost constraint, and use genuinely semantic held-out datasets.
