# SEMOS_SIM — Semantic OS Simulator v0.1

Python prototype of the **Semantic OS control plane** for future use with [LLM_SEM](https://github.com/digiponta/LLM_SEM).

**Important:** All three VMs are **dummy Python objects**, not actual virtual machines. The current semantic engine is a **mock**, not LLM_SEM neural inference. The `/sleep` command only records simulated internalization markers; it **does not train model weights**.

## Requirements

- Python 3.13 (also compatible with modern Python 3.10+)
- No external Python packages
- No Hyper-V, VMware, Docker, or virtualization requirement

## Quick start (PowerShell)

```powershell
git clone https://github.com/digiponta/SEMOS_SIM.git
cd SEMOS_SIM
python semantic_os.py --demo
python -m unittest -v test_semantic_os.py
python semantic_os.py
```

## Interactive example

```text
/teach 量子センサー | は | 量子現象を利用するセンサー
/approve 量子センサー|は|量子現象を利用するセンサー
量子センサーとは
/sync
/sleep
/status
/memory
/exit
```

`/teach` places knowledge in pending memory; `/approve` promotes it to canonical memory with an **UNVERIFIED** label. `/sync` copies canonical facts to online dummy VM replicas when at least two of three are online. `/sleep` simulates consolidation without touching LLM weights.

## Architecture

```text
User / Agent
  |
Semantic OS Kernel (intent routing, process table, unknown gate)
  |
SemanticEngine protocol
  +-- MockSemanticEngine (implemented in v0.1)
  +-- LLM_SEM adapter (planned)
  |
Canonical / Pending Semantic Memory
  |
Dummy VM Manager (Python objects; no virtualization)
  +-- VM-A
  +-- VM-B
  +-- VM-C
  |
Simulated /sync and /sleep, audit records
```

## Future work

- Connect actual LLM_SEM semantic vectors and NDC routing via the `SemanticEngine` adapter.
- Use semantic scoring to schedule requests.
- Add VM-failure, network-partition, versioning and reconciliation experiments.
- Implement separately validated, opt-in LLM_SEM `/sleep` weight updates with rollback.

**Research boundary:** The two-of-three online check is not Raft or distributed consensus; there is no real GPU model execution, isolation, VM networking, or truth verification.

## Files

- `semantic_os.py`: simulator and interactive CLI
- `test_semantic_os.py`: five unit tests
- `README.md`: this documentation

## LLM_SEM sibling integration (experimental)

From SEMOS_SIM with a sibling `..\\LLM_SEM` checkout:

```powershell
python semantic_os.py --engine llm-sem
# Interactive command: /ndc 量子力学
# To enable REAL checkpoint hidden-state vectors (requires torch and model files):
python semantic_os.py --engine llm-sem --llm-sem-model model/model-sem-internalized-v01575.pt
python -m unittest -v test_llm_sem_adapter.py
```

The optional adapter loads LLM_SEM's real `ndc.py` keyword classification; with an explicit checkpoint it also uses `LanguageModel.semantic_vector(pooling="mean")` for experimental cosine retrieval. The threshold is not calibrated. This is **not** the stable NDC neural router or an actual `/sleep` training integration. Checkpoint files may be absent locally. No LLM_SEM files are edited.

## v0.3 experimental Semantic Scheduler

The optional scheduler computes normalized mean-pooled checkpoint vectors for the incoming request and three dummy-VM capability descriptions in `semantic_scheduler.py`. It selects the best online dummy VM only if the uncalibrated cosine is >= 0.85 and the gap to second place is >= 0.04. Otherwise it falls back to round-robin among online VMs. All slash commands also fall back. These thresholds are **illustrative, not validated**.

```powershell
git pull origin main
python -m unittest -v test_semantic_scheduler.py test_llm_sem_adapter.py test_semantic_os.py
python semantic_os.py --engine llm-sem --llm-sem-model model/model-sem-internalized-v01575.pt --scheduler semantic
```

Interactive diagnosis:

```text
/route 量子力学
/route CUDAによるGPU計算
/route 日本文学
/route 未知の話題
/exit
```

The `/route` command reports selected dummy VM, method, raw cosine scores, and ranking. It does **not** execute an operation or train model weights. Because semantic vectors are raw model representations, assess scores before relying on them. Semantic routing of ordinary requests only affects which dummy VM is annotated as executing the operation; it does not provide a VM workload executor.

