# SEMOS_SIM v0.7.8 — Matched Task DAG vs Semantic Dependency Graph

## Experimental question
Can a semantic dependency graph (SDG) reduce recomputation following semantic changes *beyond* what an equally capable, conventional DAG execution runtime with the same recognition keys can do?

**Important:** v0.7.8 is a matched **negative control**. The conventional RECOGNIZER_DAG has identical input semantic recognition, version keys, dependency-result identities, shared caches, three logical workers, and scheduling policy to SEMANTIC_DAG. SEMANTIC_DAG adds management overhead only. Consequently, this experiment is not designed to show SPU superiority; it tests equivalence, invalidation correctness, and whether earlier reuse improvements can be replicated without an OS architectural novelty.

## Workload
For each concept C0..C(N-1): stage S0 -> S1 -> S2, with repeated requests per stage. S2 also depends on the previous concept's S0 output. Execute the same graph twice. Between epochs 0 and 1, specified concepts change their version. Descendant keys carry upstream dependency-result identity, so changed ancestors invalidate dependent results in matched caching strategies.

All result identities are synthetic. Wrong reuse is defined by cached true-identity mismatches, not factual truth checks.

## Commands (PowerShell)
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_semantic_dependency_graph_v078.py
python semantic_dependency_graph_v078.py --concepts 20 --repeats 3 --changed C3,C9 --output results/semantic_dependency_graph_v078.json
$r=Get-Content results/semantic_dependency_graph_v078.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table mode,executed,reused,wrong_reuse,aggregate_cost,makespan
$r.matched_comparison
```
An output path is exclusive-create; use a new filename to rerun.

## Research interpretation
- TASK_DAG: dependency-correct execution, no cache.
- RECOGNIZER_DAG: same semantic oracle (with optional error injection), version-aware dependency-sensitive reuse.
- SEMANTIC_DAG: identical reuse capabilities plus an explicit synthetic per-request semantic management cost.
- A changed concept must cause only relevant version-linked descendant identities to change; unaffected concepts can reuse.
- If this matched experiment yields equivalent reuse but higher SPU cost, no semantic OS architectural advantage has yet been established.
- The next experiment must introduce an operationally distinct SPU feature, accompanied by an equally engineered baseline and correctness constraints, to isolate architectural value.

## Limitations
One Python process, three virtual worker clocks, centrally consistent shared results, no real VMs, real NLP, true distributed synchronization, per-VM local caches, concurrent submissions, system clocks, durable storage, or faults.
