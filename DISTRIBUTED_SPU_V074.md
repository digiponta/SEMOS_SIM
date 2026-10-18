# SEMOS_SIM v0.7.4 — Three-VM semantic processing simulation

This phase extends the *synthetic* comparison of semantic data as distributed execution units. It models three workers (VM-A/B/C), dependency-aware readiness, a shared result directory, and VM-to-VM result transfer cost. It does **not** create real VMs or perform real networking.

## Fairness
All modes receive identical requests, processing costs, dependency DAG and three workers. Both NORMALIZED_CACHE and SEMANTIC_SPU have access to the same shared completed-result directory. NORMALIZED_CACHE receives a configurable normalization-coverage oracle; SEMANTIC_SPU receives a canonical-meaning oracle. This is a sensitivity model, **not a demonstration of algorithmic superiority over a real normalized cache**.

In all modes dependency provenance is part of the reuse key. Cross-DAG reuse is conservatively refused. Results are assumed pure and immutable; side effects, stale replicas, faults and incorrect semantic equivalence are not modeled.

## Run on Windows
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_distributed_spu_v074.py
python distributed_spu_v074.py --requests 120 --duplicate-fraction 0.4 --dependency-fraction 0.2 --network-latency 0.5 --semantic-overhead 0.1 --normalization-coverage 0.5 --output results/distributed_spu_v074.json
$r=Get-Content results/distributed_spu_v074.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,executed,reused,transfers,makespan,aggregate_cost,aggregate_cost_saving_vs_task,makespan_saving_vs_task
```

File output uses exclusive create; choose another output filename to rerun.

## Interpretation
- **makespan**: completion time of all requests in synthetic scheduling time units (not elapsed wall-clock seconds).
- **aggregate_cost**: summed execution, communication, lookup, and semantic overhead.
- **transfers**: simulated inter-worker cache-result transfers.
- A reduction in makespan is distinct from aggregate work reduction.
- Asynchronous admission, concurrent scheduling of ready requests, network contention, failures, persistence, learned semantic equivalence, and correctness are **future work**. Current scheduling makes an ordered admission decision for each request, even though VM timelines overlap.

## Next
v0.7.5: shared-result consistency, VM failure/retry and sync cost; v0.7.6: matched baselines, multiple seeds, ablations and statistical intervals.
