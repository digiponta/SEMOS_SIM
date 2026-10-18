# SEMOS_SIM v0.7.3 — SPU cost and correctness sensitivity

This phase advances quantitative research of Semantic data as an OS processing unit. It is a **synthetic cost model**, not empirical OS performance. It compares the same workload under TASK, EXACT_CACHE, NORMALIZED_CACHE and SEMANTIC_SPU. NORMALIZED_CACHE has configurable recognition coverage; SPU is provided canonical equivalence by an oracle, and can be perturbed with artificial false merges. All modes report execution count, reuse, overhead, total cost, and wrong reuse. Wrong reuse must not be counted as a quality-preserving performance improvement.

## Reproduce (PowerShell)
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_compare_task_spu_v072.py test_spu_sensitivity_v073.py
python spu_sensitivity_v073.py --requests 1000 --duplicate-fraction 0.4 --semantic-overhead 0.05 --normalization-coverage 0.5 --output results/spu_sensitivity_v073.json
$r=Get-Content results/spu_sensitivity_v073.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,executed,reused,wrong_reuse,total_cost,savings_fraction
python spu_sensitivity_v073.py --requests 1000 --sweep --output results/spu_sweep_v073.json
```

The `--sweep` runs 60 synthetic configurations: 5 duplicate fractions × 4 semantic overheads × 3 false-merge probabilities. Result files are create-only.

## Scientific boundaries
- Normalization coverage is assigned probabilistically, *not* evaluated from real natural-language queries. The existing exact-cache fixture deliberately uses unique surface IDs.
- The synthetic wrong-reuse measure tracks a specific false-merge mechanism, not every possible semantic misclassification. Cost reductions accompanied by wrong reuse are not valid net improvements.
- Equality oracle and cache accounting do not include network transfers, CPU profiling, distributed VM faults, truth verification or independent semantic model inference.
- v0.7.4 should model dependency scheduling and distributed VM transfer overhead under fair baseline controls.
