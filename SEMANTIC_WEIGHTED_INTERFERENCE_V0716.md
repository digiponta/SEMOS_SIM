# SEMOS_SIM v0.7.16 — Semantic-weighted interference (synthetic)

## Goal
Verify that kernel-weighted complex-amplitude updates can transfer an observed candidate's utility toward **unobserved nearby candidates**, unlike the non-informative uniform diffusion of v0.7.15. Kernel is synthetic ring distance, not embeddings.

Methods: RANDOM, GREEDY, KERNEL_UCB (classical kernel regression with exploration bonus), QI_KERNEL_PHASE (classical coherent complex-amplitude heuristic), QI_PHASE_ABLATION (uniform no-information transfer). All candidates' true utilities are hidden until evaluation. All use identical oracle-call budgets. KERNEL_UCB and QI receive identical similarity information, but CPU operations are not equal.

## Run
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile semantic_weighted_interference_v0716.py
python -m unittest -v test_semantic_weighted_interference_v0716.py
python semantic_weighted_interference_v0716.py --candidates 64 --budgets 8,12,24 --trials 40 --seed 42 --strength 1.0 --output results/semantic_weighted_interference_v0716.json
$r=Get-Content results/semantic_weighted_interference_v0716.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table landscape,budget,method,success_at_budget,mean_regret,mean_operations_proxy
$r.ablations | Format-Table landscape,budget,qi_minus_ablation_success,qi_minus_kernel_ucb_success
```

Use a new output filename for reruns (exclusive create).

## Limits
Quantum-inspired denotes an **entirely classical** complex-amplitude heuristic, not physical interference, a unitary evolution, or quantum acceleration. Ring similarity is synthetic. Shuffled utility is a negative control. No Semantic Memory, LLM, calibrated uncertainty intervals, or matched CPU time. Differences with matched nonsemantic kernel methods are essential; improvement over a uniform ablation alone does not demonstrate a QHA-specific advantage.
