# SEMOS_SIM v0.7.22 — Matched Quantum/Classical One-Step Search

The v0.7.21 output was **one-step optimal candidate hit rate only**, not comparable to a multi-step algorithm. This milestone uses identical 4 initial observed candidates, identical initial utilities, and **one additional unseen candidate oracle evaluation** for every classical and state-vector simulated quantum strategy. Both newly discovered optimum and final best including the pilot observations are reported.

Methods: RANDOM, KERNEL_UCB, KERNEL_SOFTMAX (temperature .2), QI_PHASE_ONLY and QI_PHASE_DIFFUSION. QI methods sweep 0,1,2,3 oracle/diffusion rounds. A zero-round run is a uniform Born-distribution control. QI_PHASE_ONLY uses unitary phase operations; phase changes alone do not change Born probabilities, so unless conditioned phase information is coupled through a mixing operation, its selection stays uniform. QI_PHASE_DIFFUSION adds the unitary Grover reflection to permit measurement-distribution change. All run on ordinary classical CPUs.

## Run (PowerShell)

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile quantum_classical_matched_v0722.py
python -m unittest -v test_quantum_classical_matched_v0722.py
python quantum_classical_matched_v0722.py --candidates 16 --trials 200 --seed 10000 --pilot 4 --rounds 0,1,2,3 --bootstrap 500 --output results/quantum_classical_matched_v0722.json
$r=Get-Content results/quantum_classical_matched_v0722.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table landscape,method,rounds,pilot_optimum_rate,new_optimum_rate,final_success,mean_final_regret,median_selection_ms
$r.comparisons | Format-Table landscape,rounds,comparison,success_delta,success_ci95,regret_delta,regret_ci95
```

Writes output using exclusive creation; use a new filename if rerunning.

## Interpretation and limits

Success includes pilot successes, so inspect `new_optimum_rate` to measure the incremental search benefit. Same oracle calls does not imply equal computation time. The classical similarity kernel is synthetic ring distance, not a real Semantic Memory embedding. No physical quantum computation or speedup is claimed. Round sweep is exploratory, without multiple comparison correction. Selection-time timing excludes initial pilot evaluation, which is identical across strategies; compare both selection time and quality.

## Proposed next phases

v0.7.23: density-matrix/noise and decoherence sensitivity. v0.7.24: entanglement/correlation demonstrations with separate semantic registers. v0.7.25: Semantic Memory/SPU request interface and realistic workloads. In each phase preserve matched oracle and classical baselines.
