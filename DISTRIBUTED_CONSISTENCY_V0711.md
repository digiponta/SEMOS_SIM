# SEMOS_SIM v0.7.11 — Synthetic Three-VM Replica Consistency

Each of three logical VMs owns a local cached output for a small dependency graph A→B,C→D. Two same-tick writes to A are serialized deterministically; change notifications propagate with configurable delay. Before any READ is returned, a central reference truth checks the local result. An obsolete local result is counted, repaired, then recomputed; no incorrect value is returned. Both DAG_REPLICA and SEMANTIC_REPLICA have identical information and repairs. Semantic management adds explicit cost only.

## Run (PowerShell)
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile distributed_consistency_v0711.py
python -m unittest -v test_distributed_consistency_v0711.py
python distributed_consistency_v0711.py --notification-delay 2 --management-cost 0.1 --output results/distributed_consistency_v0711.json
$r=Get-Content results/distributed_consistency_v0711.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,reads,stale_detected,repairs,conflicts,wrong_results_returned,cost
$r.matched
```

Output is create-only.

## Critical limitations
- A **logical** replication experiment in one process. No actual VMs, sockets, asynchronous wall time, consensus or network partitions.
- The central version/truth oracle prevents wrong results; real distributed replica caches cannot generally obtain this guarantee at zero network cost. This model DOES NOT demonstrate a safe real distributed cache.
- Conflicting writes are serialized by fixed event order; the model is not a distributed concurrency control protocol.
- Only one static graph and fixed event sequence; no random multi-seed claims.
- Both alternatives share the same oracle, invalidation and repair policies; Semantic costs add overhead. This is another architectural negative control.
- Next: implement distributed version validation cost, asynchronous change delivery, per-replica state with MVCC and conflict resolution and matched conventional baselines.
