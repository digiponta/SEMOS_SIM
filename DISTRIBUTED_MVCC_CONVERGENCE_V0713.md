# SEMOS_SIM v0.7.13 — MVCC Head Deduplication, Conflict Policies, Convergence

This fixes the v0.7.12 **duplicate head-counting issue** in a new standalone simulator. Each causal version is deduplicated by vector clock. In the supplied three-replica scenario, two genuinely concurrent write versions remain, not six distinct conflicts.

Policies: multi_value (retain both), deterministic (choose a winner for presentation), merge (present a combined value). The latter two do not create a causally new version or guarantee semantic truth; all 3 replicas still retain 2 unresolved causal heads. Fixed peer-to-peer anti-entropy exchanges make replicas converge in this synthetic no-failure schedule.

DAG_MVCC_RESOLVE and SEMANTIC_MVCC_RESOLVE have matching algorithms and received messages. The semantic route pays per-read management overhead. Not a claim of SPU performance superiority.

## PowerShell
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile distributed_mvcc_convergence_v0713.py
python -m unittest -v test_distributed_mvcc_convergence_v0713.py
python distributed_mvcc_convergence_v0713.py --policy multi_value --delay 2 --output results/distributed_mvcc_convergence_v0713.json
```

Rerun with new output filenames for --policy deterministic or merge; outputs are create-only.

## Limits and next experiments
No real VM, durable version write, message failure, partition, consensus or actual semantic merge logic. The fixed peer exchange itself causes convergence of *visible decisions*; it does not resolve the two concurrent branches causally. Next build true merge commits that dominate both parents, then partitions, restoration and stable convergence criteria with comparable conventional implementations.
