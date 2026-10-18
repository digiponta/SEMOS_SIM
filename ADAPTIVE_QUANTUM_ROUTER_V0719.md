# SEMOS_SIM v0.7.19 — Pre-execution Adaptive Quantum-inspired Router

## Research question

Can a pre-execution choice of search algorithm improve held-out success and regret relative to the best fixed search algorithm, while explicitly accounting for routing overhead? Does **changing only the complex phase** affect performance?

This is a **synthetic, classical** experiment. QI_PHASE_ON and QI_PHASE_OFF share an identical complex-amplitude update and sampling policy; only phase angle differs: pi*(1-observed_utility) versus zero. Neither is physical quantum interference.

## Methods and controls

- KERNEL_UCB: classical similarity-based deterministic exploration
- QI_PHASE_ON: complex amplitude with observed-utility-dependent phase
- QI_PHASE_OFF: exactly matched zero phase (negative control)
- RANDOM: random distinct candidates
- ADAPTIVE_ALL: the development-set lowest-regret algorithm for each externally supplied, **pre-known** profile and budget
- ADAPTIVE_CLASSICAL: similarly tuned kernel/rand router; receives the same profile information and is charged the same routing overhead
- BEST_FIXED_DEV: single best globally scored algorithm on development set (no routing overhead)
- FIXED_UCB / FIXED_QI / PHASE_OFF: untuned fixed policy controls

There is **no hidden per-instance oracle** involved in selecting the route: the profile (smooth/shuffled/multimodal) is exposed as an input before any utility evaluation. This is an idealized, highly privileged assumption; it is NOT a working profile classifier. For real QHA workloads, profile inference must be implemented and charged. The configured `--router-cost` is an assumed synthetic cost, **not** elapsed time. Compare regret/success separately from routing overhead; do not add arbitrary units to wall-clock times.

Dev (seed 42) and holdout (seed 40000) are disjoint. Equal candidate evaluation budgets, not equal CPU time. Paired bootstrap percentile intervals are exploratory and unadjusted for multiple testing.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile adaptive_quantum_router_v0719.py
python -m unittest -v test_adaptive_quantum_router_v0719.py
python adaptive_quantum_router_v0719.py --candidates 64 --budgets 8,12,24 --dev-trials 40 --holdout-trials 120 --dev-seed 42 --holdout-seed 40000 --bootstrap 500 --router-cost 0.05 --output results/adaptive_quantum_router_v0719.json
$r=Get-Content results/adaptive_quantum_router_v0719.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.routes | Format-Table profile,budget,adaptive_all,adaptive_classical
$r.results | Format-Table profile,budget,policy,selected_method,success,mean_regret,routing_cost_per_request
$r.contrasts | Format-Table profile,budget,comparison,success_delta,success_ci95,regret_delta,regret_ci95
```

Outputs use exclusive create; choose new path when repeating.

## Limits & next experiment

Results are conditional on supplied profile labels and chosen dev scoring metric. They cannot prove a universal quantum-inspired or QHA advantage. In particular, pre-known distribution labels could give an adaptive router an unrealistic advantage over a single fixed method. The fair profile-aware classical router is therefore essential. Real CPU-time-matched routing, profile misclassification, genuine Semantic Memory embeddings, and multiplicity-adjusted confirmatory benchmarks remain future tasks.
