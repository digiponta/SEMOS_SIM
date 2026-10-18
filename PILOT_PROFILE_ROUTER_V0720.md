# SEMOS_SIM v0.7.20 — Pilot-based Profile Classifier and Adaptive Router

## What changed
Unlike v0.7.19, true synthetic landscape labels are not handed to the Router. Every policy begins with the **same random pilot candidate observations**, and all pilot utility-oracle calls are deducted from the total search budget. A two-feature nearest-centroid classifier estimates the profile from these observations, using disjoint training seeds. Development trials learn a lookup of which method performs best for each **predicted** profile and budget; final Holdout trials then evaluate those routes without re-tuning.

Compared policies: ADAPTIVE_ALL (QI, UCB, random, phase-off eligible); ADAPTIVE_CLASSICAL (UCB, random eligible); FIXED_UCB; FIXED_QI. All reuse pilot observations, and all are charged the same pilot plus classifier wall-clock time, including fixed policies, for a matched workflow. The latter is conservative to fixed policies; a deployment fixed-policy baseline would skip classifier time, so these timings MUST NOT be taken as a real runtime advantage. Timing varies with CPU, Python version, and background load.

Classification feature extraction uses pairwise absolute utility differences at nearby versus distant ring positions. Ring distance is an artificial proxy for Semantic similarity, not an actual semantic embedding. Predicted profile is not a real task-understanding classifier. **This version uses observed utilities to classify** and therefore needs pilot oracle calls; it does not classify exclusively from request metadata.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile pilot_profile_router_v0720.py
python -m unittest -v test_pilot_profile_router_v0720.py
python pilot_profile_router_v0720.py --candidates 64 --budgets 8,12,24 --pilot 4 --train-trials 60 --dev-trials 40 --holdout-trials 120 --train-seed 1000 --dev-seed 10000 --holdout-seed 50000 --output results/pilot_profile_router_v0720.json
$r=Get-Content results/pilot_profile_router_v0720.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.confusion | Format-List
$r.routes | Format-Table predicted_profile,budget,adaptive_all,adaptive_classical
$r.results | Format-Table profile,budget,policy,success,mean_regret,median_total_ms
```

Output uses exclusive-create mode; choose a different filename on reruns.

## Scientific limitations
The four pilot evaluations consume a large fraction of budget 8. No confidence intervals are computed in this version. Synthetic class labels and utility functions are generated from known distributions; classifier performance depends on pilot sampling and ring prior. The methods are classical, and no quantum advantage is claimed. The measured total time includes pilot selection and classifier time for ALL policies, which deliberately matches the instrumented workflow but is NOT the fastest fixed-policy implementation.

## Next
Quantify misclassification and route confusion, vary pilot count (2,4,6), add a no-classifier fixed baseline, calculate paired bootstrap differences with independent holdout blocks, and test real Semantic Memory candidate data.
