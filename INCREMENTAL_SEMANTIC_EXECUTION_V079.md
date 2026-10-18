# SEMOS_SIM v0.7.9 — Incremental Semantic Execution

v0.7.9 models a DAG of 20 concepts × 3 processing stages. A source change propagates through the graph's descendant closure; only affected nodes are recomputed in epoch 2, and unaffected results are reused across logical workers.

The central methodological control is **fairness**: the conventional DAG_INCREMENTAL and SEMANTIC_INCREMENTAL modes are given exactly the same graph, recognized identities, change notifications, cache visibility and scheduler. SEMANTIC_INCREMENTAL adds a synthetic management cost. This is a **negative control**, not proof that semantic OS scheduling itself is faster.

## Windows reproduction
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_incremental_semantic_execution_v079.py
python incremental_semantic_execution_v079.py --concepts 20 --changed C3:S0,C9:S1 --output results/incremental_semantic_execution_v079.json
$r=Get-Content results/incremental_semantic_execution_v079.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,affected_nodes,recomputed_second_epoch,unnecessary_recomputation,missed_invalidations,executed,reused,aggregate_cost,makespan
$r.matched_comparison
```

Outputs are create-only; use a new filename when rerunning.

## Scientific interpretation
- TASK_FULL_REBUILD: recomputes the full graph in epoch 2; useful baseline but not a strong conventional incremental DAG.
- DAG_INCREMENTAL: identical change propagation and reuse policy to Semantic incremental.
- SEMANTIC_INCREMENTAL: same, plus per-request semantic management cost.
- True result identity and descendant closure are synthetic ground truth. The model does not implement actual NLP, learning, lineage inference or a distributed consistency protocol.
- Requires input nodes in topological order. Duplicate/dangling dependencies are rejected. No cycle resolution.
- VM-like resource clocks and remote transfer charges are synthetic; no real VMs or measured seconds.
- A subsequent phase should compare advanced dependency indexes, online graph updates, or implementation complexity and memory costs against a fully engineered conventional DAG engine without granting SPU an exclusive oracle.

## Research aim
Distinguish semantic equivalence/reuse benefits from an architectural improvement that ordinary graph schedulers cannot attain at comparable cost.
