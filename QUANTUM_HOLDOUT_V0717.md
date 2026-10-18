# SEMOS_SIM v0.7.17 — Independent Holdout, Bootstrap CIs, Softmax Kernel

Compares QI_KERNEL_PHASE against deterministic KERNEL_UCB, stochastic SOFTMAX_KERNEL, and RANDOM on independent synthetic workload seeds starting at 10000 (different from v0.7.16's 42). All search methods receive identical ring-kernel information and candidate evaluation budgets. Reports mean Success@Budget, mean regret, median CPU wall-clock diagnostic time, and paired bootstrap percentile 95% confidence intervals on per-trial differences. Fixed temperature 0.2 and QI strength 1.0.

**Cautions:** v0.7.16 parameters are not separately optimized on training-only data. Holdout means a previously unused seed block, not real external data. The synthetic ring kernel is not an actual embedding or Semantic Memory. Equal oracle calls do not imply equal arithmetic operations; wall-clock measurements are hardware- and load-sensitive, not rigorous performance evidence. The QI heuristic is classical code, not physical quantum computation. Confidence intervals for 27 comparisons do not adjust for multiple testing; isolated positive comparisons require replication.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile quantum_holdout_v0717.py
python -m unittest -v test_quantum_holdout_v0717.py
python quantum_holdout_v0717.py --candidates 64 --budgets 8,12,24 --trials 120 --seed 10000 --strength 1.0 --temperature 0.2 --bootstrap 1000 --output results/quantum_holdout_v0717.json
$r=Get-Content results/quantum_holdout_v0717.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table landscape,budget,method,success_at_budget,mean_regret,median_runtime_ms
$r.contrasts | Format-Table landscape,budget,comparison,success_difference,success_95ci,regret_difference,regret_95ci
```

Output is exclusive create. Repeated tests may take longer due to real timing measurements.

## Next
Use predeclared single-primary-endpoint analysis with multiple-testing correction, additional independent seed blocks, equal wall-clock budgets, and real semantic candidate datasets. Preserve negative findings and matched classical baselines.
