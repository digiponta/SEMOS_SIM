# SEMOS_SIM v0.7.10 — Dynamic Graph Updates (matched negative control)

## Scope
Add, remove and update directed dependency edges and source content between two executions. Model truth is a deterministic digest of node content plus dependency outputs. Only nodes with changed digests must be recomputed; unaffected outputs may be safely reused.

Compared strategies:
- FULL_REBUILD: no reuse; recompute all.
- DAG_DYNAMIC: conventional graph scheduler with perfect change notifications, output hashes and incremental reuse.
- SEMANTIC_DYNAMIC: exactly same scheduling and information plus a per-request semantic management cost.

This is a **negative control**, not a demonstration of architectural superiority for Semantic OS. The conventional DAG receives the same information and capabilities, so expecting SEMANTIC_DYNAMIC to beat it would be methodologically unsound.

## PowerShell
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_dynamic_semantic_graph_v0710.py
python dynamic_semantic_graph_v0710.py --concepts 12 --output results/dynamic_semantic_graph_v0710.json
$r=Get-Content results/dynamic_semantic_graph_v0710.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,affected,recomputed,unnecessary_recompute,missed_invalidation,reused,aggregate_cost,makespan,correct
$r.matched
```

Output files use exclusive create; use a fresh filename to rerun.

## Current limits
- Dynamic events are applied **between** two execution epochs (not mid-computation).
- A single shared consistency domain with complete graph knowledge.
- Three logical worker clocks but no real VMs, distributed memory, failures, message reordering, or network contention.
- Output hashes are synthetic ground truth, not validated LLM semantic correctness.
- SPU does not currently have a distinct dynamic scheduler; only extra management cost is modeled.
- Future work: mutations during execution, replica-local cache, version vectors, dependency conflict resolution, fault recovery, and truly matched real implementation costs.
