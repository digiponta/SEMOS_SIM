# SEMOS_SIM v0.7.1 — Semantic Processing Unit (SPU) simulator

## Research objective
Test whether using **Semantic data as a unit of execution** can reduce redundant work relative to task-oriented execution. This is the first synthetic building block for a fair baseline comparison in v0.7.2. No performance advantage is claimed yet.

## Assumptions
- An experimental oracle provides the canonical meaning of each request. No LLM or semantic similarity model infers equivalence.
- A SPU execution identity includes canonical meaning, context, version, operation, parameters **and upstream dependency/result signature**. This prevents unsafe reuse when a condition or operation changes.
- Scheduling is topological and deterministic, currently **single-process**. No actual parallelism, network or VM execution is performed.
- Outputs are synthetic hashes, not factual LLM answers. The simulation does not approve or promote knowledge.

## Run
```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m unittest -v test_semantic_processing_unit_v071.py
python semantic_processing_unit_v071.py --output results/spu_v071.json
Get-Content results/spu_v071.json -Encoding UTF8
```
If switching is blocked by local edits, save or stash them first. The report is create-only; use a new filename to rerun.

## Synthetic demonstration
Four requests: two canonically equal EVALUATE requests, one EVALUATE with a dependency, one EXPLAIN operation. Expected logical counts: requests 4, executed 3, reused 1, synthetic work cost 9.0 versus naive request costs 12.0. These **are fixture parameters, not empirical measurements**. Baseline modes and timing/cost sensitivity analysis are work for v0.7.2.

## Next
Add same-workload fair task/exact-cache/normalized-cache/SPU baselines, oracle error injection, and execution cost/semantic-resolution overhead accounting before scaling to multi-VM QHA simulation.
