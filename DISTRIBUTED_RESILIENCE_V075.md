# SEMOS_SIM v0.7.5 — Synthetic Three-VM Resilience

## Objective
Compare task dispatch, a conventional normalized cache, and Semantic SPU under the **same** deterministic transient-failure schedule, resource count, workload, version updates and transfer/synchronization cost model. Reports separate makespan and aggregate simulated costs. No claim of real virtualization performance or fault tolerance.

## Design limitations
- Three logical workers only; no hypervisors, real networking or data replication.
- Both cache strategies use an identical centrally shared, strongly consistent result directory.
- Cache keys contain the canonical semantic identity (oracle-supplied), operation fixed to EVALUATE, and explicit version. Different versions cannot reuse cached answers.
- One transient failure can occur for each executed request. Lost compute is charged; retry goes to another logical VM.
- Cache hits are not retried, and failures are independent request-index events; failure counts can differ when reuse changes the executed subset. No permanent worker outages.
- Sync latency is charged at each cache publication. No stale-replica visibility, correctness errors, network contention or correlated VM failures are simulated.
- The chosen normalization-coverage parameter is synthetic, not evaluated from natural-language input.
- v0.7.4 modeled dependency-sensitive keys; v0.7.5 isolates **failures and version changes without a DAG**.

## Reproduce in PowerShell
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_distributed_resilience_v075.py
python distributed_resilience_v075.py --requests 120 --duplicate-fraction 0.4 --update-period 30 --failure-rate 0.1 --network-latency 0.5 --sync-cost 0.05 --retry-cost 0.5 --semantic-overhead 0.1 --normalized-coverage 0.5 --output results/distributed_resilience_v075.json
$r=Get-Content results/distributed_resilience_v075.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,executed,reused,failures,retries,remote_transfers,stale_reuse,makespan,aggregate_cost,aggregate_savings_vs_task,makespan_savings_vs_task
```

The report is create-only; choose a different output file if rerunning.

## Next
v0.7.6: multi-seed statistics; independent controls over VM failures, normalization quality, update frequency, network latency; matched ablations and uncertainty intervals. A later version should implement real replica-lag, fault-duration, DAG and distributed-consistency testing.
