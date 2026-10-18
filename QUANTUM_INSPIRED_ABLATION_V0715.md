# SEMOS_SIM v0.7.15 — Quantum-Inspired Phase/Diffusion Ablation

This matched-budget synthetic benchmark extends v0.7.14 with 3 landscape structures (smooth ring, iid shuffled, multimodal), 4 budgets (4, 8, 12, 24), 40 trials per setting, and 5 search methods: RANDOM, GREEDY, QI_PHASE_ONLY, QI_DIFFUSION_ONLY, QI_PHASE_DIFFUSION.

**Scientific validity:** this is conventional CPU simulation of complex amplitudes, NOT a quantum computer, quantum interference in physical matter, quantum speedup, or proof of QHA superiority. There is no semantic memory or real language model in this pilot. Every method observes utilities only after choosing candidates; candidate evaluation calls are held equal, but CPU arithmetic is not. The "operations_proxy" is bookkeeping, not timing.

Particular cautions: phase-only and diffusion-only applied to a uniform starting amplitude do not change sampling magnitudes. The phase+diffusion combination can change probabilities but may not improve the outcome. RNG sampling primitives differ between RANDOM and weighted samplers, so do not interpret a single paired sample as statistically paired noise, and evaluate many trials/seeds. Smooth rings favor proximity exploration; iid shuffled is a structural negative control.

## PowerShell

```powershell
cd C:\Users\inoma\git\misc\SEMOS_SIM
git fetch origin
git switch v0.7.0
git pull --ff-only origin v0.7.0
python -m py_compile quantum_inspired_ablation_v0715.py
python -m unittest -v test_quantum_inspired_ablation_v0715.py
python quantum_inspired_ablation_v0715.py --candidates 64 --budgets 4,8,12,24 --trials 40 --seed 42 --output results/quantum_inspired_ablation_v0715.json
$r=Get-Content results/quantum_inspired_ablation_v0715.json -Raw -Encoding UTF8 | ConvertFrom-Json
$r.results | Format-Table landscape,budget,method,success_at_budget,mean_regret,mean_operations_proxy
$r.ablations | Format-Table landscape,budget,interference_success_delta,interference_regret_delta,interference_extra_operations
```

Outputs use exclusive-create mode; choose another filename on rerun.

## Next steps
Compare multiple independent seed blocks with intervals, explicitly match real CPU time rather than just evaluation calls, fix algorithmic search biases, then test actual semantic candidates and semantic correctness. A zero/negative finding is useful and must remain reported.
