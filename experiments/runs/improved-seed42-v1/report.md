# Improved algorithm benchmark

The reviewed implementations ran against the same hidden objective, bounds, seed 42, and 150 independent + 150 collaborative evaluations per method as the original experiment. The collaborative phase receives only the three best candidates from this new independent phase. No original-run candidates, known optimum, landscape, or source were given to the algorithms. The original experiment files are unchanged.

| Method | Original best | Improved best | Change | Improved x | Improved y | Calls |
|---|---:|---:|---:|---:|---:|---:|
| bayesian | 19.9331988297 | 18.7150740664 | -1.2181247633 | 1.25923639 | -3.18557119 | 300 |
| gradient | 20.0000000000 | 18.9840633749 | -1.0159366251 | 1.23263002 | -3.17674186 | 300 |
| particle_swarm | 18.7687105778 | 18.7150740664 | -0.0536365114 | 1.25923639 | -3.18557119 | 300 |

Final-value improvements: none. Regressions: bayesian, gradient, particle_swarm. Keep the original results as the demonstrated stronger final-value benchmark for methods that regressed.

## Independent phase

| Method | Original best | Improved best |
|---|---:|---:|
| bayesian | 16.0107336156 | 18.7150740664 |
| gradient | 16.0201688068 | 15.9088887143 |
| particle_swarm | 18.2885519478 | 16.8884058759 |

## Evaluation efficiency

| Method | Version | First call ≥19 | First call ≥19.99 | Optimization seconds |
|---|---|---:|---:|---:|
| bayesian | original | 156 | not reached | 1.7569 |
| bayesian | improved | not reached | not reached | 0.8128 |
| gradient | original | 161 | 175 | 0.5463 |
| gradient | improved | not reached | not reached | 0.5789 |
| particle_swarm | original | not reached | not reached | 0.5468 |
| particle_swarm | improved | not reached | not reached | 0.5777 |

## Interpretation

Positive changes indicate better final values; earlier threshold crossings indicate greater evaluation efficiency at that target. Runtime includes worker startup and evaluator communication, excludes model authoring and Git, and can vary with machine load. This is one seed and one original-vs-reviewed comparison, not evidence of statistical superiority. All three methods changed together, so a collaborative change can also reflect different candidates supplied by another method; per-change causal effects require ablations.

Reviewed source is fixed across phases: these runs test the code improvements, without Ollama rewriting or additional cloud model calls. Each worker re-evaluates or explicitly imports shared data according to its algorithm; reported best values come exclusively from its own evaluator ledger. Every logged point was independently revalidated by the supervisor.
