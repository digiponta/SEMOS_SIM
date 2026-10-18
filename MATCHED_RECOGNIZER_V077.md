# SEMOS_SIM v0.7.7 — matched semantic-recognizer control

## Research question
Does Semantic data as the **OS processing unit** provide an improvement distinct from giving a conventional task cache the **same semantic recognizer**? v0.7.2–0.7.6 favored Semantic SPU with oracle identity against partial normalized recognition. That is not an apples-to-apples architectural comparison.

v0.7.7 gives conventional RECOGNIZER_CACHE and SEMANTIC_SPU the *identical precomputed, fallible recognition tokens*, input requests, version checks, three logical VM slots, transfer costs and published results. The SPU variant adds configurable semantic-management cost only. There is **no modeled scheduling capability unique to SPU** at this stage; the matched comparison should therefore not produce structural speedups. Treat this as a **negative control**.

## Execute in PowerShell
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_matched_recognizer_v077.py
python matched_recognizer_v077.py --requests 120 --false-merge-rate 0.0 --false-miss-rate 0.0 --output results/matched_recognizer_v077.json
$r=Get-Content results/matched_recognizer_v077.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,executed,reused,wrong_reuse,aggregate_cost,makespan
$r.matched_comparison
python matched_recognizer_v077.py --study --seeds 20 --requests 120 --output results/matched_recognizer_study_v077.json
```

All output files use exclusive creation; choose a new filename to rerun.

## Interpretation
- Wrong reuse compares cached ground-truth canonical identity with the current request; false merges can produce apparently favorable performance with invalid results.
- False misses prevent reuse. Version mismatch always prevents reuse.
- Both matching modes use the same recognition tokens and recognition overhead, so any cost difference reflects modeled SPU metadata overhead, *not* better recognizer coverage.
- The five experiment configurations vary false-merge and false-miss rates using 20 seeds; they are not real-world error rates or evaluation of an NLP model.
- No claim is made that the SPU architecture is superior. To evaluate OS-level benefits, the next stage must implement **a genuinely distinct architectural capability** (e.g. dependency-aware semantic result sharing across VM boundaries, safe invalidation, coordinated scheduling) available to the SPU and test against a conventional DAG/task runtime with comparable semantics and engineering effort.

## Limits
Three worker clocks simulated in one Python process; no real VMs, real time, concurrency contention, replica lag, cryptographic verification or truth validation.
