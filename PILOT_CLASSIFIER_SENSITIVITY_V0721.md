# SEMOS_SIM v0.7.21 — Pilot Classifier Sensitivity

This follow-up to v0.7.20 compares pilot sizes **2, 4, 6**, two lightweight classifiers **CENTROID vs KNN3**, and an uncertainty-based fallback to KERNEL_UCB. Each pilot observation is a **paid oracle call** included in total 8/12/24 evaluation budgets. Split seeds do not overlap (train 1000, dev 10000, holdout 60000). Predicted class—not true class—is used to choose a route, tuned on development trials only.

Four policies share each initial pilot:
- ADAPTIVE: method selected from predictions and development regret.
- CONFIDENCE_FALLBACK: uncertain prediction routes to UCB, otherwise ADAPTIVE.
- FIXED_UCB and FIXED_QI: fixed methods without classifier overhead, but with the same pilot evaluations.

Classification score is a raw nearest-centroid distance gap or a kNN majority-vote margin, **not a calibrated probability**. Threshold 0.05 is heuristic. No oracle calls are made secretly for classification; all observed values originate in pilots. Wall-clock timings are provisional diagnostic measurements. The classifier and both search methods are entirely classical and the ring similarity is only a synthetic stand-in for meaning.

## Run in PowerShell

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile pilot_classifier_sensitivity_v0721.py
python -m unittest -v test_pilot_classifier_sensitivity_v0721.py
python pilot_classifier_sensitivity_v0721.py --candidates 64 --budgets 8,12,24 --pilots 2,4,6 --train-trials 60 --dev-trials 40 --holdout-trials 120 --train-seed 1000 --dev-seed 10000 --holdout-seed 60000 --confidence 0.05 --output results/pilot_classifier_sensitivity_v0721.json
$r=Get-Content results/pilot_classifier_sensitivity_v0721.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.classifiers | Format-Table pilot,classifier,accuracy
$r.results | Format-Table pilot,classifier,profile,budget,policy,success,mean_regret,median_runtime_ms,classifier_fallback_rate
```

The output path uses exclusive create. For quicker diagnostics set --budgets 8 --holdout-trials 10 --train-trials 8 --dev-trials 8 and choose a distinct output filename.

**Interpretation:** Selecting a classifier based on holdout accuracy would leak test data; keep holdout for evaluation only. A higher classification accuracy does not guarantee better search. The most important comparison is adaptive vs fixed UCB and adaptive vs confidence-fallback at identical pilot counts. Future work: calibrated abstention, paired CIs, equal-clock-time budgets, and real Semantic Memory candidate embeddings.
