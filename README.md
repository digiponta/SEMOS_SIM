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

## v0.5.5 — Post-evaluation error decomposition, not parameter tuning

```powershell
git pull origin main
python -m unittest -v test_diagnose_hybrid_holdout_v055.py
python diagnose_hybrid_holdout_v055.py --holdout data/independent_holdout.csv --frozen config/hybrid_gate_v053_frozen.json --previous results/holdout_benchmark_v054.json --output results/holdout_diagnosis_v055.json
```

Diagnoses VM-A/B/C/UNKNOWN individually, gated versus ungated Hybrid, low-score versus low-margin rejections, and Centroid/Multi candidate disagreement. Requires the prior v0.5.4 evaluation, matching frozen settings and holdout SHA256, and refuses to overwrite. This is a **post-holdout diagnostic**: keep the same settings and preserve the 400-case results as an evaluation record. Changing thresholds, model or prototypes in response to these results requires a fresh untouched benchmark to assess any claimed improvement.

## v0.5.6 — Exploratory VM-aware / consensus gate variants

This iteration compares **hypotheses on development samples only**, without modifying the frozen v0.5.3 gate or reusing the 400-case holdout for calibration.

```powershell
git pull origin main
python -m unittest -v test_compare_gate_variants_v056.py
python compare_gate_variants_v056.py --development data/validation_v043_dev100.csv --frozen config/hybrid_gate_v053_frozen.json --output results/gate_variants_development_v056.json
```

Variants: reference global 0.76/0.06, three VM-specific cosine threshold offsets per VM (-.08, -.04, +.04), consensus requirement, and three global offsets. These are exploratory sensitivity tests, **not** a statistically valid fitted per-VM calibrator or learned Contrastive Unknown Gate. Report keeps raw known coverage, known routing accuracy and unknown false accept. No modification to frozen configuration or Semantic Scheduler. A newly authored untouched evaluation set is necessary for confirmation.

## v0.5.7 — Experimental separated VM-confidence/Unknown gate

```powershell
git pull origin main
python -m unittest -v test_evaluate_separated_gate_v057.py
python evaluate_separated_gate_v057.py --development data/validation_v043_dev100.csv --frozen config/hybrid_gate_v053_frozen.json --output results/separated_unknown_gate_v057.json
```

Candidate: score/margin/centroid–multi agreement features, fitted per nominated VM to known/UNKNOWN class centroids, then contrasted by scaled feature distance. A development-only out-of-fold evaluation is reported beside the existing (in-sample) frozen-gate baseline; the two are not a fair independent comparison. Grouped split blocks **exactly normalized identical requests only**, not paraphrases, and cannot remove previous model selection bias. No 400-item final candidate evaluation input is used, no model weights trained, and the v0.5.3 configuration remains frozen. This is an exploratory open-set classifier rather than a probabilistically calibrated confidence model.

## v0.5.8 — Paired grouped development validation and uncertainty

```powershell
git pull origin main
python -m unittest -v test_evaluate_paired_grouped_v058.py
python evaluate_paired_grouped_v058.py --development data/validation_v043_dev100.csv --frozen config/hybrid_gate_v053_frozen.json --output results/paired_grouped_gate_v058.json
```

Optional, **preferred**: provide a manually curated `text,group_id` CSV with an entry for every development request, grouping questions of the same topic and paraphrases under the same `group_id`. Add `--groups data/development_topic_groups.csv`. Without this, the fallback groups only exact normalized text; output is explicitly labeled `EXACT_TEXT_ONLY`, **not** topic-disjoint validation.

v0.5.8 produces side-by-side predictions on identical held-out folds for frozen Global and fitted Separated Gate. The Global parameters were nonetheless selected earlier using all development examples, so **paired folds do not repair pre-existing selection bias**. Unknown false-accept Wilson intervals are descriptive and assume independent observations; correlated prompts undermine that assumption. Previously evaluated synthetic 400-case holdout is not used. No runtime or frozen gate changes.

## v0.5.9 — Nested topic-group development evaluation

```powershell
git pull origin main
python -m unittest -v test_evaluate_nested_topic_gate_v059.py
python evaluate_nested_topic_gate_v059.py --development data/validation_v043_dev100.csv --groups data/development_topic_groups.csv --frozen config/hybrid_gate_v053_frozen.json --output results/nested_topic_gate_v059.json
```

Outer 5-fold topic-group CV reserves whole topics, while inner 3-fold group CV selects a contrast-distance rejection threshold using only outer-train examples. Candidate scores are VM-aware, comparing distance to known and unknown feature centroids. Reports unknown false acceptance with descriptive Wilson 95% interval and reports whether each inner estimate satisfies the empirical 5% budget. **No claim of 5% statistical upper bound is made** with tiny UNKNOWN samples. Frozen v0.5.3 and previously evaluated candidate 400 samples remain unchanged. Reference is development-fitted, therefore not a fair untouched benchmark. A new, independent benchmark remains necessary.

## v0.5.10 — Post-nested-CV error analysis

```powershell
git pull origin main
python -m unittest -v test_diagnose_nested_topic_v0510.py
python diagnose_nested_topic_v0510.py --input results/nested_topic_gate_v059.json --output results/nested_diagnosis_v0510.json
```

Aggregates the v0.5.9 JSON only: by-class confusion, topic-group accuracy and rejects, 5-fold cutoff spread, each UNKNOWN false accept, and known demands held as UNKNOWN. Pure diagnosis; no change to model, weights, guard or the earlier 400 synthetic examples. v0.5.9 JSON does not include each example's raw contrast score, so score distributions and calibration reliability cannot be audited from this artifact; that requires a separate, independently validated instrumentation run.

## v0.5.11 — Per-query replayable router decision trace

```powershell
git pull origin main
python -m unittest -v test_trace_nested_gate_v0511.py
python trace_nested_gate_v0511.py --reference results/nested_topic_gate_v059.json --output results/nested_traces_v0511.json
```

Exactly replays v0.5.9 topic-fold and inner threshold-selection seeds. Records each held-out query's selected candidate VM, fused semantic score, runner-up similarity margin, centroid/multi agreement, known/unknown feature distances, contrast score, guard cutoff, final predicted destination and reason. Requires **exact comparison** of every final prediction and topic with the v0.5.9 source JSON; mismatch raises an exception. This is instrumentation for analysis only, not new independent evidence, and does not modify QHA's 2 Copies in 3 or LLM_SEM model.

## v0.5.12 — Router/Unknown Gate ablation (diagnostic only)

```powershell
git pull origin main
python -m unittest -v test_analyze_router_gate_ablation_v0512.py
python analyze_router_gate_ablation_v0512.py --input results/nested_traces_v0511.json --output results/router_gate_ablation_v0512.json
```

Separates candidate VM classification accuracy (router-only) from the observed final safety gate. The router-only condition intentionally routes every UNKNOWN request, and an additional gold-label-based oracle measures a theoretical upper-bound decomposition **only**: neither is deployable. Input is verified v0.5.11 trace; no embedding recomputation, changes to frozen settings, guard tuning, final holdout access, or 2 Copies in 3 replication exercise.

## v0.5.14 — Exploratory selective-rescue sensitivity

```powershell
git pull origin main
python -m unittest -v test_evaluate_selective_rescue_v0514.py
python evaluate_selective_rescue_v0514.py --input results/nested_traces_v0511.json --output results/selective_rescue_v0514.json
```

Tests five illustrative, predeclared candidate rules against the **already-exposed** v0.5.11 diagnostic trace, plus a no-rescue baseline. It reports known routing accuracy, known coverage, selective accuracy, unknown rejection and the added correct/wrong/UNKNOWN accepts. The sweep is diagnostic: it does **not** select a winning threshold, modify the deployed gate or provide an independent result. Compare against **provisional** engineering goals (known accuracy >=70%, coverage >=80%, unknown rejection >=95%) without treating them as guaranteed statistical expectations. The QHA LLM_SEM **2 Copies in 3** synchronization mechanism remains outside this simulator evaluation.

## v0.5.15 — Router vs Gate failure-feature diagnosis

```powershell
git pull origin main
python -m unittest -v test_analyze_feature_failures_v0515.py
python analyze_feature_failures_v0515.py --input results/nested_traces_v0511.json --output results/feature_failure_analysis_v0515.json
```

Summarizes similarity, margin, contrast and known/unknown distances for correct routing, candidate VM errors, false gate rejects, and UNKNOWN errors, including VM-specific aggregates. **Exploratory descriptive analysis only**: no target optimization, learning, independent holdout or 2 Copies in 3 testing. The v0.5.13 target goals remain provisional and are not new measured outcomes.

## v0.5.16 — Exploratory feature AUC comparisons

```powershell
git pull origin main
python -m unittest -v test_evaluate_feature_auc_v0516.py
python evaluate_feature_auc_v0516.py --input results/nested_traces_v0511.json --output results/feature_auc_v0516.json
```

Compares fused similarity, runner-up margin, contrast score, guard margin and feature distances using pairwise ROC AUC. Contrasts correctly/incorrectly classified known requests, known versus UNKNOWN, and correctly nominated known requests that were rejected versus UNKNOWN. Illustrative AUC target = 0.90, an **unvalidated engineering target**, not a statistical expected value. Comparisons involving accepted/rejected labels are partly determined by the gate score itself; do not treat such AUC as independent performance. No new samples, tuning, 400-case candidate holdout, or QHA 2 Copies in 3 test.

## v0.5.17 — Prospective structured-semantic evaluation preparation

This stage defines a CSV schema for a **new, independently authored** dataset: `request_id,text,gold,subject,predicate,object,intent,topic_group,source_id`. `gold` is one of `VM-A`, `VM-B`, `VM-C`, `UNKNOWN`. `subject/predicate/object/intent` are manually specified structured labels, not outputs of a trained parser. Ensure provenance (`source_id`), disjoint topics, and data freeze before evaluating competing semantic representations; the tool cannot itself certify independence.

```powershell
python -m unittest -v test_prepare_prospective_eval_v0517.py
python prepare_prospective_eval_v0517.py --prospective data/prospective_new_unseen.csv --output results/prospective_manifest_v0517.json
```

The prospective CSV **is not included**: create one without consulting previously used development or exposed candidate holdout cases. The validator checks required columns, class labels, exact normalized text duplicates/overlap with v0.5.11 development trace, and SHA-256 hashes; it does **not** run an ML benchmark, prove paraphrase or topic independence, change the frozen router, or evaluate QHA's 2 Copies in 3. Previously reported AUC and accuracy remain exploratory.

## v0.5.18 — Frozen synthetic prospective routing comparison

```powershell
git pull origin main
python -m unittest -v test_evaluate_prospective_v0518.py
python evaluate_prospective_v0518.py --prospective data/prospective_new_unseen.csv --manifest results/prospective_manifest_v0517.json --output results/prospective_comparison_v0518.json
```

Runs Keyword, TF-IDF trained on the old development training set, frozen LLM_SEM semantic-vector candidate router, and its frozen similarity gate on the SHA-256-checked 80-case synthetic set. **All predictors read only the request text**: the manually authored Subject/Predicate/Object/Intent fields and gold labels are reserved for descriptive annotation and scoring. A true Structured Semantic Router requires a separate automatic text-to-SPOI parser, and is **not** evaluated here; feeding gold-side SPOI into a router would leak information. Goals are provisional; samples were newly authored for this project but do not constitute external independent validation. No retuning and no QHA 2 Copies in 3 test.

## v0.5.19 — Frozen Gate Failure Attribution

```powershell
git pull origin main
python -m unittest -v test_diagnose_gate_failures_v0519.py
python diagnose_gate_failures_v0519.py --manifest results/prospective_manifest_v0517_run2.json --comparison results/prospective_comparison_v0518.json --output results/gate_failure_attribution_v0519.json
```

Replays v0.5.18 **exactly** under frozen LLM_SEM checkpoint and config. For each gold VM, distinguishes gate rejection caused by low fused similarity, low runner-up margin, or both; records margins relative to frozen thresholds, centroid/multi-prototype agreement, and candidate correctness. Gold labels are used only for post-hoc audit, never in routing. This is analysis of already exposed synthetic data, not a new independent score or a tuned Gate. QHA 2 Copies in 3 remains out of scope.

## v0.5.20 — VM-specific Similarity Diagnostic (retrospective)

```powershell
git pull origin main
python -m unittest -v test_diagnose_vm_similarity_v0520.py
python diagnose_vm_similarity_v0520.py --input results/gate_failure_attribution_v0519.json --output results/vm_similarity_diagnostic_v0520.json
```

Reports fused-score distributions for correct VM candidates versus UNKNOWN and other-domain requests whose top candidate is that same VM, and conditional pairwise AUC. Shows **hypothetical** similarity-threshold changes (-0.10, -0.05, 0, +0.05), holding the margin fixed; counts candidate rescues and UNKNOWN/wrong-route risks. These are sensitivity examples, **not calibrated recommendations**; conditional AUC suffers selection bias, because all examples are filtered to top-1 candidate VM. Data already exposed. Frozen inference unchanged and no 2 Copies in 3 testing.

## v0.5.21 — Preregistered VM calibration data separation

The v0.5.20 result showed score-scale variation across VM candidates; the exposed 80 synthetic cases must **not** be used to fit or select a new Gate. v0.5.21 specifies a candidate (VM-wise empirical CDF of fused similarity using **new training-only calibration data**, then a fixed 0.76 percentile rule with unchanged raw margin .06), and audits calibration/evaluation source, topic and exact-text separation. This is a protocol proposal, **not an implemented or validated calibrated gate**.

```powershell
git pull origin main
python -m unittest -v test_prepare_vm_calibration_v0521.py
python prepare_vm_calibration_v0521.py --calibration data/new_calibration.csv --evaluation data/new_evaluation.csv --block data/validation_v043_dev100.csv --block data/independent_holdout.csv --block data/prospective_new_unseen.csv --output results/calibration_split_audit_v0521.json
```

`new_calibration.csv` and `new_evaluation.csv` are **not supplied**: they require new independently sourced and topic/source-disjoint records with columns `request_id,text,gold,topic_group,source_id`. Automatic PASS does not prove semantic independence. Do not inspect evaluation labels or iterate on evaluation failures while developing candidates; final reference comparison uses frozen global gate and vector-only controls, Wilson 95% intervals, and held-out metrics. No results or 2 Copies in 3 validation are claimed.

## v0.5.22 — VM ECDF calibrated gate: frozen split evaluation

```powershell
git pull origin main
python -m unittest -v test_evaluate_vm_calibration_v0522.py
python evaluate_vm_calibration_v0522.py --calibration data/new_calibration.csv --evaluation data/new_evaluation.csv --audit results/calibration_split_audit_v0521.json --output results/vm_calibrated_gate_v0522.json
```

Uses v0.5.21 **passed audit and byte-exact SHA-256 files**. Scores calibration requests first using the frozen LLM_SEM checkpoint and existing 70% centroid / 30% multi-prototype mixture. Builds an empirical score CDF separately for each top-1 candidate VM, then applies the preregistered 0.76 percentile criterion with unchanged raw runner-up margin 0.06. Evaluation labels and Subject/Predicate/Object/Intent annotations are NEVER used in inference. Compares unchanged Vector Only and Global Gate. Reports per-VM confusion and 95% Wilson confidence intervals. This is a synthetic split demonstration, not independent real-world validation; ECDF percentiles are not calibrated correctness probabilities and small samples can make quantiles unstable. Do not tune methods after observing the evaluation file. QHA synchronization is not evaluated.

## v0.5.23 — AND versus OR Gate (diagnostic; not deployed)

Run after local `git pull origin main`:

```powershell
python -m unittest -v test_compare_and_or_gate_v0523.py
python compare_and_or_gate_v0523.py --calibration data/new_calibration.csv --evaluation data/new_evaluation.csv --audit results/calibration_split_audit_v0521.json --output results/and_or_gate_v0523.json
```

Replays frozen LLM_SEM checkpoint to measure AND (ECDF percentile >= 0.76 **and** margin >= 0.06) vs OR (ECDF percentile >= 0.76 **or** margin >= 0.06) on the same pre-existing synthetic calibration/evaluation split. Preserves baseline thresholds and model weights; reports score/margin/ECDF diagnostics, correct-route rescues, wrong-route accepts, and UNKNOWN false accepts. OR is exploratory **after evaluation set was inspected**, so metrics are not independent confirmation. Recovery is a future proposal **not implemented**: validate provisional reversible execution, rollback and retry if needed; irreversible side effects require explicit safeguards.

## v0.5.24 — OR Gate optimistic execution / recovery (oracle simulation)

```powershell
git pull origin main
python -m unittest -v test_simulate_recovery_v0524.py
python simulate_recovery_v0524.py --input results/and_or_gate_v0523.json --output results/recovery_oracle_simulation_v0524.json
```

An **in-memory-only state-machine experiment** reads v0.5.23 OR traces: Gate reject goes straight to Discovery; accepted requests enter provisional VM simulation; an **oracle that reads evaluation gold** validates route, then a simulated commit or rollback, and optionally a deterministic different VM for retry. The alternate is **not** the measured top-2 candidate (not available in input). No VM is invoked, no actual snapshots, isolation, semantic result validation, rollback or side effect is performed. These metrics are an **optimistic oracle upper bound**, not real recovery performance; don't compare as production performance or use exposed 40 cases to tune parameters. Future real validator must be gold-free and may require user confirmation for irreversible operations.

## v0.5.25 — VM-Aware Recovery Protocol simulation

```powershell
git pull origin main
python -m unittest -v test_simulate_vm_aware_recovery_v0525.py
python simulate_vm_aware_recovery_v0525.py --input results/and_or_gate_v0523.json --output results/vm_aware_recovery_v0525.json
python simulate_vm_aware_recovery_v0525.py --input results/and_or_gate_v0523.json --false-accept 0.10 --false-reject 0.10 --output results/vm_aware_recovery_faulty_v0525.json
```

Simulates OR Gate provisional VM dispatch, VM self-report `ACCEPTED` or `NOT_SUPPORTED`, automatic retry, and eventual Discovery. Deterministic synthetic responder uses evaluation **gold** to emulate configurable capability-check false positives/negatives; the dispatcher itself receives only the reply. Default zero errors is an idealized oracle, **not measured VM behavior**. Retries use alphabetical remaining VMs, since the v0.5.23 artifact lacks top-2 scores; actual semantic top-2 routing remains future work. No real VM execution, commit, rollback, external effects, semantic verification or 2 Copies in 3 is tested. Results are retrospective and synthetic.

## v0.5.26 — User-authorized round-robin VM capability probe

Gate-rejected requests remain rejected unless explicitly authorized by `--approval-file` (CSV `request_id,approved` with `true` or `false`); absent entries are denied. An authorized rejected request starts a rotating VM-A/B/C sequence and stops on first `ACCEPTED`, else Discovery. Nonrejected requests retain v0.5.25 behavior. Consent is an **offline supplied fixture**, not interactive UI consent. Never interpret it as authorization for side effects.

```powershell
git pull origin main
python -m unittest -v test_simulate_user_rr_v0526.py
# Prepare approval fixture manually, e.g. request_id,approved followed by EVALA002,true
python simulate_user_rr_v0526.py --input results/and_or_gate_v0523.json --approval-file data/user_rr_approvals.csv --output results/user_authorized_rr_v0526.json
```

**Limitations:** Synthetic VM responder still reads gold labels. Simulates no actual VM or effects. Default zero-error behavior is an idealized upper bound. Fault simulation: `--false-accept 0.10 --false-reject 0.10` with a *different* output path. RR probe start changes per **approved Gate rejection**, not per request. Already-exposed examples are exploratory only.

## v0.5.27 — VM capability error robustness

```powershell
git pull origin main
python -m unittest -v test_evaluate_vm_robustness_v0527.py
python evaluate_vm_robustness_v0527.py --input results/and_or_gate_v0523.json --approval-file data/user_rr_approvals.csv --output results/vm_capability_robustness_v0527.json
```

Ten predeclared false-accept / false-reject scenarios at 0/5/10/20% (single-axis and paired), 200 paired deterministic pseudo-random replicates each. Reports mean/min/max of outcomes and probe counts. **This is a sensitivity model with synthetic gold-aware responders** and previously inspected test cases, not independently validated real-VM error rates or evidence for deployment. Same explicit approval CSV from v0.5.26; absent approval means deny.

## v0.5.28 — Two-stage capability validation, error-dependence sweep

```powershell
git pull origin main
python -m unittest -v test_evaluate_two_stage_capability_v0528.py
python evaluate_two_stage_capability_v0528.py --input results/and_or_gate_v0523.json --approval-file data/user_rr_approvals.csv --output results/two_stage_capability_v0528.json
```

Compares first-stage-only acceptance to requiring both stage checks. Second stage is called only after first-stage acceptance; a rejection continues VM probing. Simulates independent, perfectly shared, or 50%-mixture paired random errors, plus single-stage baseline on identical cases and explicit approvals. Reports known correctness, false commits, UNKNOWN discovery, and second-stage check counts over 200 seeded replicates. **Gold-aware error injection is synthetic**, shared errors are an assumed correlation model, and no real VM capability checking or commit is performed. New independent cases and actual capability response traces are needed for production evidence.

## v0.5.29 — Human-in-the-Loop response review (initial simulation)

VM `SIMULATED_COMPLETED` is converted to `PROVISIONAL_RESULT` rather than presumed correct. Missing user review leaves `PENDING_USER_REVIEW` (fail-closed); explicit `APPROVE`, `REJECT`, `RETRY`, or `DISCOVERY` decisions determine the next state. Discovery routes do not request answer approval. `RETRY_REQUESTED` is a handoff marker, not an executed retry. No real VM answer text or live user UI is available, and user confirmation is distinct from factual correctness.

```powershell
git pull origin main
python -m unittest -v test_simulate_hitl_review_v0529.py
python simulate_hitl_review_v0529.py --input results/user_authorized_rr_v0526.json --output results/hitl_review_v0529.json
# Optional explicit user feedback: CSV request_id,decision (APPROVE/REJECT/RETRY/DISCOVERY)
python simulate_hitl_review_v0529.py --input results/user_authorized_rr_v0526.json --review-file data/hitl_reviews_v0529.csv --output results/hitl_review_with_decisions_v0529.json
```

This is only the first v0.5.29 protocol milestone. Real response payload validation, user feedback UI, durable authorization, automated rerouting and contract checking remain future work.

## v0.5.29.1 — HITL answer packets and no-repeat retry handoff

```powershell
git pull origin main
python -m unittest -v test_prepare_hitl_packets_v05291.py
python prepare_hitl_packets_v05291.py --input results/user_authorized_rr_v0526.json --output results/hitl_packets_v05291.json
# Optional: manually supplied answer payload CSV: request_id,question,answer
# Optional: review CSV: request_id,decision (APPROVE/REJECT/RETRY/DISCOVERY)
python prepare_hitl_packets_v05291.py --input results/user_authorized_rr_v0526.json --payload-file data/hitl_answers_v05291.csv --review-file data/hitl_reviews_v05291.csv --output results/hitl_packets_reviewed_v05291.json
```

Missing question/answer => `AWAITING_ANSWER_PAYLOAD`, and an explicit review decision in that state is rejected. Supplied answers appear as `PENDING_USER_REVIEW` until a genuine decision is given. `RETRY` selects a **not-yet-contacted VM** based on source routing events, with no VM execution and no synthesized replacement answer. If all VMs were previously contacted, it transitions to Discovery. This is a protocol simulation only, not a UI and not real VM responses. Do not treat CSV fixtures as genuine human evaluations unless they are supplied by the human.

## v0.5.29.2 — Local HITL answer review GUI

A local Tkinter GUI displays **explicitly supplied** question and VM answer content, and asks the user to choose APPROVE, REJECT, RETRY, or DISCOVERY. Decisions require a confirmation click and are saved atomically to CSV. A request without a nonempty question and answer is **not reviewable**. Rejected/unknown/Discovery routes are excluded. RETRY is recorded as a request only; no new VM is executed. No real VM answer source or user authenticity mechanism is present.

```powershell
git pull origin main
python -m unittest -v test_hitl_review_gui_v05292.py
# Create data/hitl_answers_v05292.csv with header: request_id,question,answer
# Use real responses only; the simulator does not generate them.
python hitl_review_gui_v05292.py --input results/user_authorized_rr_v0526.json --payload-file data/hitl_answers_v05292.csv --review-file data/hitl_gui_decisions_v05292.csv
python prepare_hitl_packets_v05291.py --input results/user_authorized_rr_v0526.json --payload-file data/hitl_answers_v05292.csv --review-file data/hitl_gui_decisions_v05292.csv --output results/hitl_packets_reviewed_v05292.json
```

Tkinter must be available in the local Python installation. If no payload data exists, the GUI cannot show answers. Review decisions do not validate factual truth. For irreversible actions, obtaining review decisions alone does not execute or authorize side effects.

## v0.5.29.3 — User-directed retry and renewed response approval

This incremental simulation processes a `RETRY_HANDOFF_PENDING_VM_EXECUTION` from v0.5.29.1. It **does not call VMs**: a separate reply CSV provides the newly returned actual VM answer. It validates the expected *unvisited* VM, preserves the question, records the previous answer, and always requires a new decision for the new answer. Repeating RETRY uses another unvisited VM (if available); otherwise the state becomes DISCOVERY. Each run outputs a new JSON file and will not overwrite an existing file.

```powershell
git pull origin main
python -m unittest -v test_run_hitl_retry_v05293.py
# Prepare a prior packet with an actual RETRY decision using v0.5.29.1, then:
python run_hitl_retry_v05293.py --input results/hitl_packets_retry_v05291.json --output results/hitl_retry_waiting_v05293.json
# External reply CSV: request_id,vm,question,answer
# E.g. if the packet's retry_vm is VM-B, the row's vm MUST be VM-B.
python run_hitl_retry_v05293.py --input results/hitl_packets_retry_v05291.json --reply-file data/hitl_retry_replies_v05293.csv --output results/hitl_retry_review_v05293.json
# Optional explicit next-round review CSV: request_id,decision
python run_hitl_retry_v05293.py --input results/hitl_packets_retry_v05291.json --reply-file data/hitl_retry_replies_v05293.csv --decision-file data/hitl_retry_decisions_v05293.csv --output results/hitl_retry_decided_v05293.json
```

Before this, create a genuine RETRY decision using the v0.5.29.2 GUI or another human-controlled CSV. The v0.5.29.2 GUI itself is not yet wired to display replacement answers from v0.5.29.3; this remains follow-up work. Simulation outputs are not evidence of real VM dispatch, which is external to this project milestone.

## v0.5.29.4 — Retry reply provenance gate and review GUI

Adds `validate_hitl_retry_v05294.py` to reject placeholders, empty/short replies, missing declared provenance (`execution_id`, `executed_at`, `source`), wrong VM, or changed questions. Validation failure keeps the request in `RETRY_HANDOFF_PENDING_VM_EXECUTION`; it does not approve or reroute it. Source metadata is **self-declared, not authenticated**. Valid replacement answers become `PENDING_USER_REVIEW` with prior review cleared. A new Tkinter GUI `hitl_retry_review_gui_v05294.py` displays replacement answers and self-declared provenance and saves a new round's explicit decisions.

```powershell
git pull origin main
python -m unittest -v test_validate_hitl_retry_v05294.py
# Header: request_id,vm,question,answer,execution_id,executed_at,source
# Supply a real answer, and its claimed metadata, not placeholder example text.
python validate_hitl_retry_v05294.py --input results/hitl_retry_handoff_v05293.json --reply-file data/hitl_retry_replies_v05294.csv --output results/hitl_retry_validated_v05294.json
python hitl_retry_review_gui_v05294.py --input results/hitl_retry_validated_v05294.json --output data/hitl_retry_review_v05294.csv
```

Review CSV is a human decision record for the replacement answer; `APPROVE` is never inferred. The GUI does not itself advance the state to USER_CONFIRMED; that is a future integration. No actual VM invocation, cryptographic provenance, semantic validation of answer truth, transaction rollback, or irreversible action is present.

## v0.5.29.5 — VM retry reply intake diagnostics

`intake_hitl_retry_v05295.py` diagnoses whether a retry reply is missing, is a blank template row, has the wrong VM/question, or lacks required metadata. It can register an **actual externally obtained VM reply** and overwrite *only* an empty template row for the same request. No VM invocation or fabricated response. Metadata remains unverified self-declaration.

```powershell
git pull origin main
python -m unittest -v test_intake_hitl_retry_v05295.py
python intake_hitl_retry_v05295.py --input results/hitl_retry_handoff_v05293.json --reply-file data/hitl_retry_replies_v05294.csv --diagnose
# After VM-C has ACTUALLY produced an answer, input the real information:
python intake_hitl_retry_v05295.py --input results/hitl_retry_handoff_v05293.json --reply-file data/hitl_retry_replies_v05294.csv --intake --request-id EVALA001 --vm VM-C --answer 'ACTUAL_VM_C_ANSWER' --execution-id ACTUAL_RUN_ID --executed-at '2026-10-17T12:00:00+09:00' --source ACTUAL_SOURCE
python validate_hitl_retry_v05294.py --input results/hitl_retry_handoff_v05293.json --reply-file data/hitl_retry_replies_v05294.csv --output results/hitl_retry_validated_v05295.json
python hitl_retry_review_gui_v05294.py --input results/hitl_retry_validated_v05295.json --output data/hitl_retry_review_v05295.csv
```

The capitalized placeholders above are **explanatory only, not valid test data**. The validator tests syntactic provenance and simple placeholder patterns, not factual truth. Use actual VM output and timestamp, and do not claim live VM integration.

## v0.5.29.6 — Explicit GUI decision state finalization

`finalize_hitl_retry_v05296.py` converts the independent GUI decision CSV from v0.5.29.4 into auditable transitions: `APPROVE -> USER_CONFIRMED`, `REJECT -> USER_REJECTED`, `DISCOVERY -> DISCOVERY`, and `RETRY -> RETRY_HANDOFF_PENDING_VM_EXECUTION` for an unvisited VM, otherwise `DISCOVERY`. Decisions are accepted **only** for `PENDING_USER_REVIEW` packets containing a reply and declared provenance. Missing answers and repeated approvals fail closed. This does not execute VMs or authenticate a decision's identity.

```powershell
# Update and test
git pull origin main
python -m unittest -v test_finalize_hitl_retry_v05296.py
# Only after an actual external VM reply has passed v0.5.29.4 and been reviewed in GUI:
python finalize_hitl_retry_v05296.py --input results/hitl_retry_validated_v05294.json --decision-file data/hitl_retry_review_v05294.csv --output results/hitl_retry_finalized_v05296.json
```

The current EVALA001 blank VM-C template cannot be finalized: it must first contain the actual external response and validated provenance; running GUI against pending-execution packets intentionally reports no reviewable items.

## v0.5.29.7 — Isolated mock VM transport

Mock-only transport is implemented in `mock_vm_transport_v05297.py`. It consumes pending retry packets and an explicitly synthetic fixture file `data/mock_vm_replies_v05297.csv`, validates VM/request/question correlation, simulates timeout and connection failures, and (for a valid fixture) produces an unapproved `PENDING_USER_REVIEW` response carrying `transport: MOCK_ONLY`. **No real VM was invoked**, and the embedded synthetic answer must never be represented as a real VM answer. Valid mock replies remain subject to user review; test success does not demonstrate real integration.

```powershell
git fetch origin
git restore --source=origin/main -- mock_vm_transport_v05297.py test_mock_vm_transport_v05297.py data/mock_vm_replies_v05297.csv
python -m unittest -v test_mock_vm_transport_v05297.py
python mock_vm_transport_v05297.py --input results/hitl_retry_handoff_v05293.json --fixture-file data/mock_vm_replies_v05297.csv --output results/hitl_mock_transport_v05297.json
```

Next: an actual VM transport adapter with explicit endpoint authorization, timeouts, response-to-request correlation, and provenance verification. Existing offline test paths stay isolated from the real adapter.

## v0.6.2 — Reproducible standalone mock fixture

`prepare_vm_transport_fixture_v062.py` creates a one-request **synthetic** retry handoff locally. This avoids reliance on deleted/stashed historical `results/hitl_retry_handoff_v05293.json` files when validating v0.6.1. It is not a restoration of historical user approvals, nor a real VM execution.

```powershell
git fetch origin
git switch v0.6.0
git pull --ff-only origin v0.6.0
python -m unittest -v test_prepare_vm_transport_fixture_v062.py
python prepare_vm_transport_fixture_v062.py --output results/synthetic_retry_handoff_v062.json
python vm_transport_v061.py --input results/synthetic_retry_handoff_v062.json --config config/vm_transport_v061.json --fixture-file data/mock_vm_replies_v05297.csv --output results/vm_transport_synthetic_v062.json
```

Expected output status count for this minimal fixture: `PENDING_USER_REVIEW: 1` and `transport: MOCK_ONLY`. Use a new output path if the previous report already exists. The existing 40-record historical dataset is not recreated, because its approvals and trace contents must not be fabricated.

## v0.6.3 — Explicitly enabled loopback HTTP transport (experimental)

`vm_http_transport_v063.py` adds a separate HTTP adapter; mock transport stays unchanged. By default the HTTP adapter refuses any network call unless `--allow-live` is passed. Configuration (`config/vm_http_transport_v063.json`) permits only `http://127.0.0.1:PORT/answer` or equivalent localhost loopback addresses and bounded timeouts. Redirects and proxy use are disabled; request ID, question, protocol, and claimed source VM must match. Transport failures leave the retry pending. Successful replies remain `PENDING_USER_REVIEW` with `HTTP_LOOPBACK_UNVERIFIED`; claimed VM identity is **not authenticated**. The example config does not mean a listening VM exists.

```powershell
git fetch origin
git switch v0.6.0
git pull --ff-only origin v0.6.0
python -m unittest -v test_vm_http_transport_v063.py
# This call requires a real, user-controlled local /answer endpoint; do NOT use until one is running.
python vm_http_transport_v063.py --input results/synthetic_retry_handoff_v062.json --config config/vm_http_transport_v063.json --output results/http_transport_v063.json --allow-live
```

Request JSON protocol: `semos.vm.v1`, fields `request_id`, `target_vm`, `question`, `operation=ANSWER_ONLY`, `side_effects_allowed=false`. Response JSON fields: `protocol`, `request_id`, `source_vm`, `question`, `answer`, `execution_id`, `executed_at`. This milestone supplies the client adapter **only**, not an HTTP VM server, authenticated origin, TLS, or side-effect authorization.

## v0.6.4 — Synthetic loopback HTTP server and end-to-end test

`local_vm_http_server_v064.py` provides a local **synthetic HTTP test server**, not a VM or LLM. Requests to `POST /answer` must use `semos.vm.v1`, `ANSWER_ONLY` and `side_effects_allowed=false`. Replies contain fixed synthetic content, tagged `SYNTHETIC_TEST_ONLY`. `test_local_vm_http_server_v064.py` tests a real HTTP loopback round-trip with the v0.6.3 client. The client records `HTTP_LOOPBACK_UNVERIFIED` and still requires user review.

```powershell
git fetch origin
git switch v0.6.0
git pull --ff-only origin v0.6.0
python -m unittest -v test_local_vm_http_server_v064.py test_vm_http_transport_v063.py
python prepare_vm_transport_fixture_v062.py --output results/synthetic_retry_handoff_v064.json
# Terminal 1: server (stop with Ctrl+C)
python local_vm_http_server_v064.py --vm VM-C --port 8765
# Terminal 2: opt-in client after server is running
python vm_http_transport_v063.py --input results/synthetic_retry_handoff_v064.json --config config/vm_http_transport_v063.json --output results/http_transport_v064.json --allow-live
```

No actual VM, inference engine, authenticated identity, production network, or true answer correctness is involved. Use a distinct output path if the file exists.

## v0.6.5 — Subprocess backend bridge (experimental)

`llm_backend_http_v065.py` connects the loopback HTTP server to a separately launched Python backend through a JSON stdin/stdout contract. It validates protocol, request ID, VM name, nonempty answer and mandatory execution metadata; enforces an execution timeout; uses `subprocess.run(..., shell=False)`; and remains answer-only. A successful reply carries `response_kind=EXTERNAL_SUBPROCESS_UNVERIFIED`. No model inference, provenance attestation, or permission for side effects is implied. The supplied `synthetic_llm_backend_v065.py` produces **only a synthetic answer**, not a trained LLM. No LLM_TRY or LLM_SEM runtime has been integrated yet.

```powershell
git fetch origin
git switch v0.6.0
git pull --ff-only origin v0.6.0
python -m unittest -v test_llm_backend_http_v065.py
# Terminal 1: synthetic subprocess-backed loopback server
python llm_backend_http_v065.py --vm VM-C --port 8765 --python (python -c 'import sys; print(sys.executable)') --backend-script (Resolve-Path .\\synthetic_llm_backend_v065.py).Path
# Terminal 2: only after server starts
python prepare_vm_transport_fixture_v062.py --output results/synthetic_retry_handoff_v065.json
python vm_http_transport_v063.py --input results/synthetic_retry_handoff_v065.json --config config/vm_http_transport_v063.json --output results/http_transport_v065.json --allow-live
```

A real model backend would need an adapter implementing the same input/output contract. Before connecting one, check the actual inference invocation and model dependencies in LLM_TRY/LLM_SEM. This implementation does not claim VM authenticity; v0.6.3 classifies it as `HTTP_LOOPBACK_UNVERIFIED`.

## v0.6.6 — LLM_TRY checkpoint raw-generation adapter (experimental)

`llm_try_backend_v066.py` reuses the real `LLM_TRY/chat.py` model-loading and `generate_reply` functions, loading a user-provided tokenizer and model checkpoint; this is **not** a synthetic answer. It is a **raw generation bridge**, not the entire LLM_TRY chat runtime. Specifically, the chat runtime's Unknown Gate, Semantic Memory routing, NDC, evidence provenance and trust policy **are not invoked**. It sets `unknown_gate_applied=false`, and the final answer remains human-review-required. Until a verified guard is integrated, DO NOT treat raw generation as trusted semantic knowledge.

`llm_backend_http_v065.py` now accepts repeatable `--backend-arg` for backend command-line parameters. The subprocess interface and safe loopback transport remain as before. It never authorizes actions.

```powershell
git fetch origin
git restore --source=origin/v0.6.0 -- llm_try_backend_v066.py test_llm_try_backend_v066.py llm_backend_http_v065.py
python -m unittest -v test_llm_try_backend_v066.py test_llm_backend_http_v065.py
# Provide REAL existing paths for these three variables:
$repo = "C:\Users\inoma\git\misc\LLM_TRY"
$checkpoint = "$repo\model\model-llm-try-nagato-chat-v94.pt"
$tokenizer = "$repo\model\tokenizer-v0.7-bpe.json"
Test-Path $checkpoint
Test-Path $tokenizer
# Only run if both paths exist, and with an appropriate LLM_TRY checkout.
python llm_backend_http_v065.py --vm VM-C --port 8765 --timeout 30 `
  --python (python -c 'import sys; print(sys.executable)') `
  --backend-script (Resolve-Path .\llm_try_backend_v066.py).Path `
  --backend-arg=--repo --backend-arg="$repo" `
  --backend-arg=--checkpoint --backend-arg="$checkpoint" `
  --backend-arg=--tokenizer --backend-arg="$tokenizer"
# In another PowerShell window once the server starts:
python vm_http_transport_v063.py --input results/synthetic_retry_handoff_v062.json `
  --config config/vm_http_transport_v063.json `
  --output results/http_llm_try_v066.json --allow-live
```

The previous checkpoint path is an example only; select the checkpoint actually installed. This may require PyTorch/CUDA and the exact Python packages expected by the current LLM_TRY checkout. At present no local model run has been performed or claimed.

## v0.6.7 — Rejected LLM answer diagnostics

When the v0.5.29.4 validator rejects a **received and correlated** HTTP reply (e.g. `TOO_SHORT`, `MISSING_TEXT`, `PLACEHOLDER`), `vm_http_transport_v063.py` now saves `rejected_reply_diagnostic` with the actual rejected `answer`, Unicode character count, validation error, claimed source VM and execution metadata. The old `packet.answer` is deliberately preserved, the retry remains pending, and rejected text is not eligible for HITL approval or semantic knowledge promotion. This is diagnostic evidence from an **unverified** loopback endpoint, not attested VM provenance. Request correlation errors still fail without admitting a reply.

```powershell
git fetch origin
git restore --source=origin/v0.6.0 -- vm_http_transport_v063.py test_rejected_reply_diagnostic_v067.py
python -m unittest -v test_rejected_reply_diagnostic_v067.py test_vm_http_transport_v063.py
# Use an unused output path while a backend server is listening:
python vm_http_transport_v063.py --input results/synthetic_retry_handoff_v062.json --config config/vm_http_transport_v063.json --output results/http_llm_try_v067.json --allow-live
# PowerShell:
$r = Get-Content results/http_llm_try_v067.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.packets[0].rejected_reply_diagnostic | Format-List *
```

Rejected answers can contain sensitive data; restrict diagnostic access and retention. The validator threshold remains eight Unicode characters; this feature does not repair poor generations or integrate the full LLM_TRY Unknown Gate.

## v0.6.8 — Native LLM_TRY chat prompt and generation diagnostics

The checkpoint adapter now calls `LLM_TRY.chat.build_prompt([], question, 0)` before `generate_reply` rather than passing a bare question. This uses the real `USER_PREFIX` / `AI_PREFIX` conversation framing with zero history, but **does not** call the complete LLM_TRY semantic router, Unknown Gate, or memory retrieval pipeline. The adapter attaches `generation_diagnostic` (generated token/character counts, model confidence statistics, prompt mode) and `vm_http_transport_v063.py` preserves the diagnostic on accepted or rejected replies. Diagnostic values are unverified information from the backend, not proof of model correctness.

```powershell
git fetch origin
git restore --source=origin/v0.6.0 -- llm_try_backend_v066.py vm_http_transport_v063.py test_llm_generation_diagnostic_v068.py
python -m unittest -v test_llm_generation_diagnostic_v068.py test_rejected_reply_diagnostic_v067.py test_llm_try_backend_v066.py
# Restart the VM-C HTTP backend server to pick up the updated Python adapter.
# Then submit using an unused output name.
python vm_http_transport_v063.py --input results/synthetic_retry_handoff_v062.json --config config/vm_http_transport_v063.json --output results/http_llm_try_v068.json --allow-live
$r = Get-Content results/http_llm_try_v068.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.summary
$r.packets[0].rejected_reply_diagnostic | Format-List *
$r.packets[0].generation_diagnostic | Format-List *
```

Be aware that model inference through the HTTP bridge is an external subprocess and the source still has no authenticated VM identity. The eight-character safety gate remains unchanged.

## v0.6.9 — Conservative lexical knowledge assessment (experimental)

`llm_try_backend_v066.py` calls the existing LLM_TRY `pre_generation_unknown_concept()` and `semantic_knowledge_lookup()` after raw generation to attach `semantic_assessment`:
- `UNKNOWN`: conservative lexical concept pre-gate rejects the concept with no semantic retrieval hit.
- `KNOWN`: the model output exactly matches an existing local canonical knowledge answer; this is **not** external truth verification.
- `UNVERIFIED`: all remaining responses; generative confidence does not imply known facts.
All assessments include `full_unknown_gate_applied=false` and `verified=false`. **This does not integrate the full LLM_TRY Unknown Gate or Semantic Memory lifecycle.** It is an initial routing contract, not factual validation.

The HTTP transport now rejects `UNKNOWN` before user-review promotion, preserving the original answer and adding `UNKNOWN_SEMANTIC` with rejected-reply diagnostics. `KNOWN` and `UNVERIFIED` still require explicit HITL review. Older synthetic backends without `semantic_assessment` retain existing behavior.

```powershell
git fetch origin
git restore --source=origin/v0.6.0 -- llm_try_backend_v066.py vm_http_transport_v063.py test_semantic_assessment_v069.py
python -m unittest -v test_semantic_assessment_v069.py test_llm_generation_diagnostic_v068.py test_rejected_reply_diagnostic_v067.py test_llm_try_backend_v066.py
# Restart the HTTP server, then run with a NEW output filename.
python vm_http_transport_v063.py --input results/synthetic_retry_handoff_v062.json --config config/vm_http_transport_v063.json --output results/http_llm_try_v069.json --allow-live
$r=Get-Content results/http_llm_try_v069.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.summary
$r.packets[0].semantic_assessment | Format-List *
```

## v0.6.10 — Generated vs retrieved evidence comparison

`llm_try_backend_v066.py` records `evidence_comparison` with separate `generated` and `retrieved` answer fields, plus `relation` (`EXACT_MATCH`, `DIFFERENT`, `NO_RETRIEVAL`). The retrieved field comes solely from LLM_TRY's existing local `semantic_knowledge_lookup` when available; it is **not independently fact-checked or authenticated**. A model-generated response is never reclassified as retrieved. The HTTP adapter preserves this comparison both for normal HITL review and UNKNOWN rejection. No automatic approval or Semantic Memory write is introduced.

```powershell
git fetch origin
git restore --source=origin/v0.6.0 -- llm_try_backend_v066.py vm_http_transport_v063.py test_evidence_comparison_v0610.py
python -m unittest -v test_evidence_comparison_v0610.py test_semantic_assessment_v069.py test_llm_generation_diagnostic_v068.py
# Restart the VM-C HTTP server to load the updated adapter, then use an unused output path:
python vm_http_transport_v063.py --input results/synthetic_retry_handoff_v062.json --config config/vm_http_transport_v063.json --output results/http_llm_try_v0610.json --allow-live
$r=Get-Content results/http_llm_try_v0610.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.summary
$r.packets[0].evidence_comparison | Format-List *
```

The `KNOWN` state from v0.6.9 reflects a local exact-text match only, not verified truth. The complete LLM_TRY Unknown Gate and external Discovery remain outside this limited adapter.

## v0.6.11 — HITL evidence-comparison UI (selection draft)

`hitl_evidence_comparison_gui_v0611.py` renders the question, LLM-generated answer, local Semantic Knowledge answer and comparison relation separately in Tkinter. It offers GENERATED / RETRIEVED / REJECT_BOTH / HOLD. Selecting a missing retrieved answer is forbidden. A recorded selection is written as an independent `HITL_EVIDENCE_COMPARISON_DRAFT` JSON with `approved=false` and `promoted=false`; it is deliberately **not** a v0.5.29.x approval CSV, and does not change the original packet, trigger a VM, or update Semantic Memory. A new output filename is required for each saved selection.

```powershell
git fetch origin
git restore --source=origin/v0.6.0 -- hitl_evidence_comparison_gui_v0611.py test_hitl_evidence_comparison_v0611.py
python -m unittest -v test_hitl_evidence_comparison_v0611.py
python hitl_evidence_comparison_gui_v0611.py --input results/http_llm_try_v0610.json --output results/hitl_evidence_selection_v0611.json
# after choosing in GUI:
$r = Get-Content results/hitl_evidence_selection_v0611.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.selections | Format-List *
```

**Important:** this milestone captures a human comparison preference only. Final authorization must remain an independent explicit operation; neither an exact match nor a selected answer implies fact verification.

## v0.6.12 — Deterministic semantic evidence comparison fixtures

`prepare_evidence_comparison_v0612.py` produces four clearly marked **synthetic** scenarios: EXACT_MATCH, DIFFERENT, NO_RETRIEVAL and UNKNOWN. They are deliberately not actual model outputs, VM responses, or live semantic memory retrievals. UNKNOWN remains `RETRY_HANDOFF_PENDING_VM_EXECUTION` and is excluded from HITL review. The other three states are reviewable, but selecting either answer does not approve or promote it.

```powershell
git fetch origin
git restore --source=origin/v0.6.0 -- prepare_evidence_comparison_v0612.py test_evidence_comparison_cases_v0612.py
python -m unittest -v test_evidence_comparison_cases_v0612.py test_hitl_evidence_comparison_v0611.py
python prepare_evidence_comparison_v0612.py --output results/synthetic_evidence_comparison_v0612.json
python hitl_evidence_comparison_gui_v0611.py --input results/synthetic_evidence_comparison_v0612.json --output results/evidence_choice_v0612.json
```

The GUI saves one selection per invocation; re-launch using a new output path for another case. The complete LLM_TRY Unknown Gate and a live retrieved-vs-generated disagreement remain future work.

## v0.6.13 — HITL comparison selection audit trail

The HITL comparison GUI now records an optional free-text **reason**, UTC `recorded_at` timestamp, evidence relation and selected answer source alongside the already non-authorizing choice. A generated/retrieved selection, REJECT_BOTH or HOLD still produces a draft-only JSON; `approved=false`, `promoted=false`, `provenance_verified=false`. There is no VM execution, final approval, or Semantic Memory write. This extends the review audit trail but is **not** cryptographically authenticated or tamper-evident. The four cases in v0.6.12 are synthetic; the actual live retrieval-vs-generation divergence experiment remains pending.

```powershell
git fetch origin
git restore --source=origin/v0.6.0 -- hitl_evidence_comparison_gui_v0611.py test_hitl_comparison_audit_v0613.py
python -m unittest -v test_hitl_comparison_audit_v0613.py test_hitl_evidence_comparison_v0611.py test_evidence_comparison_cases_v0612.py
python hitl_evidence_comparison_gui_v0611.py --input results/synthetic_evidence_comparison_v0612.json --output results/evidence_choice_v0613.json
$r=Get-Content results/evidence_choice_v0613.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.selections | Format-List *
```

## v0.6.14 — Real LLM generation vs isolated experimental knowledge lookup

The existing LLM_TRY adapter can now accept `--knowledge-file` to use a **separate read-only experimental JSONL knowledge file** instead of the repository's normal semantic knowledge source. It calls the real LLM_TRY `semantic_knowledge_lookup(question, knowledge_path=...)` and records the experimental file path and SHA-256 as unverified provenance. The new generator `prepare_experimental_knowledge_v0614.py` writes a synthetic local fixture for the concept 量子力学, with a deliberately distinct answer. Only LLM generation and the lookup operation are real in this experiment; the lookup content itself is synthetic and not verified knowledge.

```powershell
git fetch origin
git restore --source=origin/v0.6.0 -- llm_try_backend_v066.py prepare_experimental_knowledge_v0614.py test_experimental_knowledge_v0614.py
python -m unittest -v test_experimental_knowledge_v0614.py test_hitl_comparison_audit_v0613.py
python prepare_experimental_knowledge_v0614.py --output data/experimental_semantic_knowledge_v0614.jsonl
# Set this BEFORE starting the server:
$knowledgePath=(Resolve-Path .\data\experimental_semantic_knowledge_v0614.jsonl).Path
# Existing $arguments is the configured server argv array from v0.6.6.
$arguments += @("--backend-arg=--knowledge-file","--backend-arg=$knowledgePath")
python .\llm_backend_http_v065.py @arguments
# From a SECOND terminal:
python vm_http_transport_v063.py --input results/synthetic_retry_handoff_v062.json --config config/vm_http_transport_v063.json --output results/http_llm_try_v0614.json --allow-live
$r=Get-Content results/http_llm_try_v0614.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.summary
$r.packets[0].evidence_comparison | Format-List *
# If pending, launch HITL comparison GUI (use a new output path):
python hitl_evidence_comparison_gui_v0611.py --input results/http_llm_try_v0614.json --output results/evidence_choice_v0614.json
```

Restart the server after changing adapter files; if `$arguments` already has the knowledge flags, do not append them twice. An `EXACT_MATCH` is theoretically possible despite the distinct fixture, so the experiment measures the actual relation instead of asserting a difference. Neither selection nor matching authorizes knowledge promotion. Full LLM_TRY Unknown Gate remains unintegrated.
