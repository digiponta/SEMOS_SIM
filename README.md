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


## v0.3.1 provisional Unknown Gate

In response to the first real-checkpoint four-probe run, default thresholds were provisionally changed to cosine >= 0.80 and first-to-second margin >= 0.10. Low-confidence non-command requests now enter process state `HELD` with `selected=null`; they are **not** sent to an unrelated dummy VM. Slash commands retain deterministic round-robin.

**Caution:** These four observed examples are insufficient to calibrate a meaningful Unknown Gate. This is a safety-oriented prototype behavior, not established classification accuracy. Evaluate larger independent held-out known and unknown datasets before setting stable thresholds. The command `/route TEXT` reports the proposed destination or hold and does not execute a process.

## v0.4 First-stage quantitative evaluation

`benchmark_v040.py` measures routing accuracy over known cases (with holds counted as misses), known coverage, selective accuracy, unknown reject rate and precision, latency, and a four-way confusion matrix. Supported comparisons: keyword rules, character n-gram TF-IDF, LLM_SEM checkpoint vectors (no gate), and LLM_SEM vectors with the current SEMOS_SIM Unknown Gate.

```powershell
python -m unittest -v test_benchmark_v040.py
python benchmark_v040.py --train data/dev_train_v040.csv --test data/dev_test_v040.csv --model model/model-sem-internalized-v01575.pt
```

Results go to `results/benchmark_v040.json`. You can run without `--model` for the two CPU baselines.

**Important:** Both bundled CSV files are small, hand-authored **development fixtures**, not a scientifically independent holdout. Do not report their scores as generalization results. For an independent experiment, prepare separate frozen training/validation/test CSV files with columns `text,label` and labels `VM-A`, `VM-B`, `VM-C`, `UNKNOWN`. Target approximately 100 final test cases per label; sample before viewing model predictions, avoid paraphrase duplicates across splits, document dataset provenance, and calibrate thresholds only using the validation set. The runner currently checks only exact overlap and does **not** tune thresholds. The LLM_SEM vector baselines use the same fixed capability profiles, rather than a separately trained embedding model.


## v0.4.2 Validation-only calibration

The v0.4.1 diagnostic identifies widespread false rejection at cosine 0.80. **Do not change the deployed gate based on those same 12 cases.** Instead, author a separate validation CSV with columns `text,label` and labels `VM-A`, `VM-B`, `VM-C`, `UNKNOWN`, keeping it distinct from the final benchmark.

```powershell
python -m unittest -v test_calibrate_gate_v042.py
python calibrate_gate_v042.py --validation data/my_validation.csv --model model/model-sem-internalized-v01575.pt
```

This reports a threshold/margin grid search constrained by unknown false-accept rate (default <= 5%), with known accuracy, coverage, misroute rate and reject rate. It does **not** automatically alter `semantic_scheduler.py`, does not guarantee generalization, and rejects use of the bundled `dev_test_v040.csv` fixture by filename. Freeze chosen values before a truly independent final holdout and measure sensitivity across more examples. Note the small-sample uncertainty if validation has few unknowns.

## v0.4.3 — Development validation expansion

Added `data/validation_v043_dev100.csv`: 100 manually authored prompts, 25 per class (VM-A / VM-B / VM-C / UNKNOWN). These examples are **development-only**; they have not been independently labeled or frozen as a final benchmark. Some phrasing resembles the known capability profiles. Scores derived from this file are calibration/development results, not generalization claims.

Dataset validation and full benchmark:

```powershell
git pull origin main
python -m unittest -v test_audit_dataset_v043.py test_benchmark_v040.py test_calibrate_gate_v042.py
python audit_dataset_v043.py --validation data/validation_v043_dev100.csv
python benchmark_v040.py --train data/dev_train_v040.csv --test data/validation_v043_dev100.csv --model model/model-sem-internalized-v01575.pt --output results/development_benchmark_v043.json
python calibrate_gate_v042.py --validation data/validation_v043_dev100.csv --model model/model-sem-internalized-v01575.pt --output results/development_calibration_v043.json
```

Audit checks class balance, exact normalized duplicates and candidate near overlaps against `data/dev_train_v040.csv` and `data/dev_test_v040.csv`. Similarity is only character-bigram Jaccard, so semantic paraphrases and incorrect category labels need manual inspection. **Do not tune on `dev_test_v040.csv`**. The calibration sweep must be used to fix gate thresholds *before* an independently prepared final 400-case holdout.

Important methodological limit: running the benchmark on the same validation dataset used for threshold calibration gives developmental scores only. Those values must never be presented as an independent final test. Dataset creation is not the same as measuring model accuracy. The existing `semantic_scheduler.py` gate remains unchanged pending validation and independent testing.

## v0.4.4 — Fixed Multi-Prototype study

Compare three ranking-only variants using the **same LLM_SEM checkpoint and validation CSV**:

- **single:** one existing capability text per dummy VM
- **centroid:** normalized mean of five predeclared capability prototype vectors per VM
- **multi:** maximum cosine across five prototypes per VM

The predeclared prototypes are in `compare_prototypes_v044.py`. They are not trained or selected from the labels in `validation_v043_dev100.csv`, although their domains are informed by the project design. Comparisons exclude the Unknown Gate; accordingly, Unknown Reject Rate is always zero for these variants. Do not compare these results to gated routing as though they have equivalent rejection policies.

```powershell
git pull origin main
python -m unittest -v test_compare_prototypes_v044.py
python compare_prototypes_v044.py --validation data/validation_v043_dev100.csv --model model/model-sem-internalized-v01575.pt
```

Inspect `results/prototype_comparison_v044.json` for predictions, margin, latency, and per-VM confusion. Use a **separate** validation/holdout protocol to calibrate Unknown Gate for each method, then evaluate a fully unseen final dataset. This comparison is developmental and cannot establish independent generalization.

## v0.4.5 — Per-method calibrated Unknown Gate (development only)

This experiment applies the same threshold/margin grid and false-accept budget independently to Single, Centroid, and Multi-Prototype. It outputs known routing accuracy, coverage, selective accuracy, unknown rejection, per-method threshold choices, and eligible Risk–Coverage operating points.

```powershell
git pull origin main
python -m unittest -v test_compare_gated_prototypes_v045.py
python compare_gated_prototypes_v045.py --validation data/validation_v043_dev100.csv --model model/model-sem-internalized-v01575.pt
```

Output: `results/gated_prototypes_v045.json`. Thresholds selected on this same development dataset are **optimistically biased**. Do not use these scores to claim final performance or publish superiority. Keep `semantic_scheduler.py` unchanged until thresholds are frozen and evaluated against a separately curated final holdout. The 25 unknown validation cases make a 5% false-accept limit coarse (one false accept = 4%). The 448 candidate combinations are multiple-comparison selection and increase validation overfitting risk.

## v0.4.6 — Hybrid Consensus routing (development experiment)

`hybrid_router_v046.py` compares two candidate combinations from the same checkpoint and fixed prototypes: **strict consensus** (accept only if centroid and multi top-VM labels agree), and **blend** (weighted combination of each method's three cosine scores; weight defaults to 0.5). Optional `--threshold` and `--margin` are explicit, NOT automatically tuned. Default zero thresholds are exploratory, not calibrated Unknown Gates.

```powershell
git pull origin main
python -m unittest -v test_hybrid_router_v046.py
python hybrid_router_v046.py --validation data/validation_v043_dev100.csv --model model/model-sem-internalized-v01575.pt
```

Outputs per-method known accuracy, coverage, selective accuracy, Unknown reject rate, and rejection reasons to `results/hybrid_consensus_v046.json`. A disagreement is treated as UNKNOWN/HELD for strict mode, but does not imply a genuinely out-of-domain input. Prior use of these same 100 labels means any model selection based on them is exploratory; create an untouched validation split to choose gates, freeze a candidate, and only then evaluate the independently curated final holdout. No changes are made to production `semantic_scheduler.py`.

## v0.5.0 — Quantitative control-plane comparison (NOT actual OS superiority)

Compare deterministic Round Robin, Keyword, TF-IDF and optional actual LLM_SEM Hybrid routing under identical labeled request and dummy VM dispatch conditions. Fixed virtual arrival spacing (1 ms) and VM service durations (VM-A:8, VM-B:12, VM-C:10 ms) are **synthetic**; only Python wall-clock routing time is measured. `known_task_completion_proxy` means choosing the labeled VM, **not** executing the user task. No real Hyper-V/VMware, OS scheduler, resource measurements, knowledge synchronization, recovery, or IPC are evaluated here.

```powershell
git pull origin main
python -m unittest -v test_benchmark_os_advantage_v050.py
python benchmark_os_advantage_v050.py --model model/model-sem-internalized-v01575.pt
```

Output: `results/os_advantage_v050.json`, containing metrics and individual routing decisions. Run without `--model` to test just the three classic baselines. Default Hybrid weight=0.7 comes from prior development exploration and its zero gate rejects no out-of-domain inputs. Therefore this benchmark is **development-only**, not an independent scientific claim. Evaluate unknown rejection and correct-routing separately. Final comparisons must freeze all parameters/prototypes, curate genuinely unseen independent requests, rotate method order and repeat timed trials with warmup, and disclose model loading + hardware + overhead; separate actual OS experiments will be required to support genuine OS superiority.

## v0.5.1 — Paired statistical analysis of routing outcomes

This tool evaluates **paired, request-matched** v0.5.0 predictions in an existing JSON; it does not rerun model inference, fabricate a final holdout, or treat synthetic turnaround as wall-clock execution.

```powershell
git pull origin main
python -m unittest -v test_analyze_os_advantage_v051.py
python analyze_os_advantage_v051.py --input results/os_advantage_v050.json --output results/os_advantage_stats_v051.json
```

Default comparison: TF-IDF vs Semantic Hybrid. The output includes known correct-routing rate difference, unknown rejection difference, paired percentile bootstrap 95% intervals (5000 deterministic resamples) and exploratory exact two-sided McNemar tests. If using other methods, specify `--reference round_robin` or `--candidate keyword`.

**Interpretation boundary:** All these requests were used in previous development iterations and weight/prototype selection. Bootstrap intervals cannot remove this bias, and exploratory p-values must not be treated as confirmatory evidence. For a definitive claim, freeze the algorithms/thresholds and benchmark freshly curated, unseen and independently reviewed test requests. Repeated/warmed wall-clock latency measurements are a separate future experiment; the existing JSON contains only one measured run per method. The previous simulated queue benchmark is not real OS scheduling.

## v0.5.2 — Candidate holdout audit and repeated routing latency

This release adds two independent **evaluation infrastructure** scripts, not new proof of OS superiority.

```powershell
git pull origin main
python -m unittest -v test_benchmark_v052.py
python measure_routing_latency_v052.py --model model/model-sem-internalized-v01575.pt --repeats 10 --warmup 2 --output results/repeated_latency_v052.json
```

For **externally authored** candidate holdout CSV (CSV columns: `text,label`; do not recycle development prompts):

```powershell
python audit_holdout_v052.py --holdout data/independent_holdout.csv --output results/holdout_audit_v052.json
```

The candidate holdout is **not included**; prepare it separately. The auditor checks canonicalized exact overlap and character bigram near-overlap with all available development CSVs. Missing default reference files are reported as failures. Human review of paraphrases and labels is mandatory. **Do not use holdout to optimize gates, blend weights, or prototypes.** The timing script randomizes method order across repetitions with warmup and records per-run variability but still excludes model initialization, does not synchronize GPU asynchronous operations explicitly, and is not an OS benchmark.

## v0.5.3 — Freeze calibrated Hybrid Unknown Gate (development-only)

```powershell
git pull origin main
python -m unittest -v test_calibrate_hybrid_gate_v053.py
python calibrate_hybrid_gate_v053.py --validation data/validation_v043_dev100.csv --model model/model-sem-internalized-v01575.pt --weight 0.7 --max-unknown-false-accept 0.05
```

Outputs:
- `results/hybrid_gate_calibration_v053.json`: constrained grid search and observed development-only score.
- `config/hybrid_gate_v053_frozen.json`: selected threshold, margin, weight, model and development SHA256. Existing different frozen settings are **not overwritten**. If there is no feasible candidate satisfying the budget, no configuration is written.

Holdout-named CSVs are rejected as calibration inputs. The previously constructed 400-example candidate holdout must **not** be used to choose thresholds, prototypes, or weights. Calibration uses the already explored 100 development records, so metrics are optimistic. Inspect calibration and validate the freeze before a single holdout scoring pass. Current production Semantic Scheduler is unchanged.

## v0.5.4 — First-pass candidate holdout evaluation with frozen gate

Only after manual candidate-holdout review and v0.5.3 calibration, run once:

```powershell
git pull origin main
python -m unittest -v test_evaluate_frozen_holdout_v054.py
python evaluate_frozen_holdout_v054.py --holdout data/independent_holdout.csv --frozen config/hybrid_gate_v053_frozen.json --audit results/holdout_audit_v052.json --output results/holdout_benchmark_v054.json
```

The command verifies the calibration CSV SHA256, freeze format, matching holdout audit path/size/label counts, and refuses to overwrite existing results. It uses the previously frozen weight=0.7, cosine threshold=0.76 and margin=0.06 **as read from the JSON**, not command-line tuning inputs. Reports baseline Round Robin, Keyword, TF-IDF and frozen Semantic Hybrid. It **does not** claim scientific independence: the 400 prompts were synthetic and developed in the same research context, and the overlap audit cannot prove semantic independence. Do not tune against this evaluation output. Routing latency is single-run wall clock; turnaround is simulated and cannot demonstrate OS superiority.
