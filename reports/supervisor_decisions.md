# Supervisor decisions

1. Use local Qwen authoring and three isolated execution processes.
2. Enforce 150 evaluations per phase in a single-writer SQLite ledger.
3. Complete the independent barrier before sharing measured candidates.
4. Validate every recorded value independently before publication.
5. Integrate only implementations that completed their full budgets.
6. Treat collaboration effects as descriptive, pending control experiments.

7. Retain original failed Bayesian preflight source and diagnostics on its worker branch. Shared observations do not consume new-call budget.
8. Reject raw swarm summary coordinate/value mismatches; use evaluator trajectories for every comparison. Correct selected main summaries and bound gradient probes; verify all six trajectories by cached replay.
9. Gradient wins final value; Bayesian reaches value 19 first (evaluation 156 vs gradient 161). Gradient reaches 19.99 first at evaluation 175. Swarm wins the independent phase at 18.28855195. These are threshold-dependent efficiency rankings.
