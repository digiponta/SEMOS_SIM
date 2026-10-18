# SEMOS_SIM v0.7.6 — Multi-seed synthetic resilience analysis

## Purpose
Estimate whether SPU cost and makespan advantages in v0.7.5 persist across synthetic workload seeds and how they respond to controlled changes in transient failure rate, synchronization cost, semantic overhead, update frequency, and normalized-cache coverage.

## Reproduce (PowerShell)
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_distributed_statistics_v076.py
python distributed_statistics_v076.py --seed-count 20 --seed-start 42 --requests 120 --output results/distributed_statistics_v076.json
$r=Get-Content results/distributed_statistics_v076.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.scenarios | ForEach-Object {
  [pscustomobject]@{
    scenario = $_.scenario
    mean_spu_vs_normalized = $_.summary.spu_vs_normalized_cost_saving.mean
    sd = $_.summary.spu_vs_normalized_cost_saving.sample_sd
    positive_runs = $_.summary.positive_spu_vs_normalized_count
  }
} | Format-Table
```

## Experiments
16 scenarios: one reference and five independent three-level factors = 320 runs using 20 seeds per scenario. Configurations are **one-factor-at-a-time**, not a full factorial experiment; changing one parameter does not imply other factors have no interactions.

Metrics: paired relative cost savings and makespan savings for SPU vs TASK and SPU vs NORMALIZED_CACHE, and NORMALIZED_CACHE vs TASK. Each summary includes mean, sample standard deviation, min/max, and a *descriptive* 1.96*SE interval. These intervals do not have guaranteed 95% coverage with 20 samples, correlated seeds or non-normal distributions.

## Scientific limits
- Synthetic workload/virtual-worker scheduling and oracle semantic identity; no actual VM failure or elapsed-time profiling.
- Central strongly consistent directory: version mismatch prevented by cache key. Does **not** validate replica consistency.
- Normalization coverage is an oracle acceptance probability, not actual NLP matching performance.
- Semantic-overhead=0 is a **cost ablation only**; SPU still performs reuse. It is not equivalent to removing semantic reasoning.
- No confidence claims about real-world Semantic OS superiority.
- Real benchmarking, uncertainty quantification with independent holdouts, failure-duration modeling and matched real normalized caching remain future work.
