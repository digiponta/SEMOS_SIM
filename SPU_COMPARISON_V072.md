# SEMOS_SIM v0.7.2 — Task vs Semantic Processing Unit comparative simulation

## Central hypothesis
Can canonical Semantic data as the scheduling/reuse unit reduce logical execution work **after** accounting for semantic indexing overhead? This experiment is a synthetic controlled *cost model*, not an empirical performance benchmark or validation of equivalence inference.

### Modes (same workload)
- TASK: each request executed separately.
- EXACT_CACHE: exact surface-string key; fixture gives each request a different surface, so all miss by design.
- SEMANTIC_SPU: canonical meaning (oracle supplied) is the reuse key; cache and semantic indexing costs are charged for **all** requests.

Dependency graph is empty in this phase. v0.7.1 tests dependency-aware execution separately. This v0.7.2 experiment intentionally isolates redundant-work savings, not distributed execution.

### Execute on Windows PowerShell
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_semantic_processing_unit_v071.py test_compare_task_spu_v072.py
python compare_task_spu_v072.py --requests 1000 --duplicate-fraction 0.4 --seed 42 --semantic-overhead 0.05 --cache-overhead 0.01 --output results/task_spu_comparison_v072.json
$r=Get-Content results/task_spu_comparison_v072.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,executed,reused,execution_cost,index_and_semantic_cost,total_cost,savings_vs_task_fraction
```

All output files are create-only. Use a new filename if rerunning.

### Test design / caveats
- Baseline must eventually include normalized conventional caches; the current EXACT_CACHE case represents **surface-exact only**.
- Semantic equivalence is a fixture oracle, so the simulation does not measure false-positive merges, false-negative misses, embedding, LLM or SPU metadata costs beyond chosen per-request numeric overheads.
- All time and cost numbers are user-chosen synthetic units; not milliseconds, GPU seconds or real energy usage.
- Performance can be worse for SPU when duplicate fraction is low or semantic overhead high. Evaluate a parameter sweep rather than reporting a single favorable point.
- No VM, concurrency, networking, checkpointing, consistency or consensus is implemented.
- Next: v0.7.3 build better-matched normalized caching baselines, overhead sweeps, erroneous equivalence detection and actual integration with v0.7.1 dependency execution.
