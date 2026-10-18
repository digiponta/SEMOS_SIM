# SEMOS_SIM v0.7.12 — Peer-to-peer MVCC and Vector Clocks

This phase models three independent logical VM histories, vector clock versioning, deterministic concurrent writes, delayed update delivery, and peer-to-peer validation/synchronization with explicit synthetic costs.

**Crucial distinction:** Read/write logic does not consult a central truth oracle. A *post-hoc evaluator* can inspect all replicas to count locally stale reads; this detection is NOT available to the reading replica. Thus the simulation does not guarantee strong consistency or correctness of locally returned values.

Concurrent versions remain as multiple maximal vector-clock heads. `choose_latest` applies an explicit deterministic tie-break to display one value; it is **not** distributed consensus, causal conflict resolution, or semantic truth. No real VM, durable store or network runs in this version.

Conventional DAG_MVCC and SEMANTIC_MVCC have identical versioning, conflict observation and peer sync. The Semantic mode only adds per-READ overhead. This is a matched negative control.

## Windows commands

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile distributed_mvcc_v0712.py
python -m unittest -v test_distributed_mvcc_v0712.py
python distributed_mvcc_v0712.py --notification-delay 2 --validation-cost 0.2 --transmission-cost 0.3 --semantic-cost 0.1 --output results/distributed_mvcc_v0712.json
$r=Get-Content results/distributed_mvcc_v0712.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,reads,conflict_reads,stale_local_reads,unresolved_heads,aggregate_cost
$r.matched
```

Results are create-only; use another file name to rerun.

## Next
v0.7.13: robust resolution of concurrent versions, explicit repair paths and bounded staleness; future versions: partition/failure schedules and 3VM state synchronization, ideally with real network/VM measurements. Keep fully matched nonsemantic distributed baselines.
