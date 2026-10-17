# Multi-agent optimization report

## Executive summary

Best measured result: gradient (collaborative), f=20.00000000 at (1.70000002, -2.30000004). All reported evaluations were independently recalculated by the supervisor.

## Algorithm comparison

| Algorithm | Phase | Best x | Best y | Best value | Evaluations | Runtime (s) | Error to 20 |
|---|---|---:|---:|---:|---:|---:|---:|
| bayesian | independent | 2.65033351 | -0.54785744 | 16.01073362 | 150 | 1.066 | 3.98926638 |
| gradient | independent | 2.65401264 | -0.55369070 | 16.02016881 | 150 | 0.272 | 3.97983119 |
| particle_swarm | independent | 1.75161722 | -2.37826711 | 18.28855195 | 150 | 0.273 | 1.71144805 |
| bayesian | collaborative | 1.70005127 | -2.31835612 | 19.93319883 | 150 | 0.691 | 0.06680117 |
| gradient | collaborative | 1.70000002 | -2.30000004 | 20.00000000 | 150 | 0.274 | 0.00000000 |
| particle_swarm | collaborative | 1.77508668 | -2.27486463 | 18.76871058 | 150 | 0.274 | 1.23128942 |

## Independent vs. collaborative results

- bayesian: independent 16.01073362; collaboration phase 19.93319883; retained-best improvement 3.92246521. Total 300 evaluations.
- gradient: independent 16.02016881; collaboration phase 20.00000000; retained-best improvement 3.97983119. Total 300 evaluations.
- particle_swarm: independent 18.28855195; collaboration phase 18.76871058; retained-best improvement 0.48015863. Total 300 evaluations.

## Supervisor observations

Independent findings were withheld until all three workers completed and pushed. The supervisor then shared measured best candidates, recommending local refinement for gradient ascent, surrogate candidate enrichment for Bayesian optimization, and partial swarm initialization near promising points. Workers authored a revised implementation through local Ollama for the collaborative phase.

### bayesian / independent

Commit: `ab2a918da854437373c892bb84b0e082b64bdbb6`. Parameters and worker observations:

```json
{
  "algorithm_parameters": {
    "min_init": 5,
    "length_scale": 1.0,
    "signal_var": 1.0,
    "noise_var": 1e-06,
    "beta": 2.0,
    "n_candidates": 2000
  },
  "worker_notes": {
    "parameters": {
      "x": 2.650333507415592,
      "y": -0.5478574357449784
    },
    "observations": "150 worker summary entries; authoritative points are in the evaluator trajectory",
    "proposed_improvements": []
  }
}
```

### gradient / independent

Commit: `242efc03ad2b758ee506d3a6754fbcdd367634e4`. Parameters and worker observations:

```json
{
  "algorithm_parameters": {
    "h": 0.01,
    "step": 0.1
  },
  "worker_notes": {
    "parameters": {
      "x": 2.6540126406725064,
      "y": -0.5536906999850462
    },
    "observations": "150 worker summary entries; authoritative points are in the evaluator trajectory",
    "proposed_improvements": []
  }
}
```

### particle_swarm / independent

Commit: `aa84eefa31ba5078e84e3612bf8b957030518c06`. Parameters and worker observations:

```json
{
  "algorithm_parameters": {
    "n_particles": 10,
    "w": 0.9,
    "c1": 1.5,
    "c2": 1.5
  },
  "worker_notes": {
    "parameters": {
      "n_particles": 10,
      "w": 0.9,
      "c1": 1.5,
      "c2": 1.5,
      "budget": 150,
      "seed": 42
    },
    "observations": "10 worker summary entries; authoritative points are in the evaluator trajectory",
    "proposed_improvements": [
      {
        "x": 1.751617220710806,
        "y": -2.3782671087103484,
        "value": 18.2885519478321
      },
      {
        "x": 1.6125478351202145,
        "y": -2.19265312685318,
        "value": 16.372276172968085
      },
      {
        "x": 1.569107479987347,
        "y": -2.1767512261754147,
        "value": 14.160453020873259
      }
    ]
  }
}
```

### bayesian / collaborative

Commit: `e5926f8521d9a1cf4d62ac1310f900db5d5d9cc0`. Parameters and worker observations:

```json
{
  "algorithm_parameters": {
    "n_init": 5,
    "length_scale": 1.0,
    "signal_var": 1.0,
    "noise_var": 1e-06,
    "beta": 2.0,
    "n_candidates": 2000
  },
  "worker_notes": {
    "parameters": {
      "x": 1.7000512721899985,
      "y": -2.3183561222847446
    },
    "observations": "153 worker summary entries; authoritative points are in the evaluator trajectory",
    "proposed_improvements": []
  }
}
```

### gradient / collaborative

Commit: `30e6d59803424782b5b08c3d3e7c0301a848f4ef`. Parameters and worker observations:

```json
{
  "algorithm_parameters": {
    "h": 0.01,
    "step": 0.1
  },
  "worker_notes": {
    "parameters": {
      "x": 1.7000000219116012,
      "y": -2.300000041318224
    },
    "observations": "150 worker summary entries; authoritative points are in the evaluator trajectory",
    "proposed_improvements": []
  }
}
```

### particle_swarm / collaborative

Commit: `92cf30eb1d1df2074a9190722913aab39ba2cb0d`. Parameters and worker observations:

```json
{
  "algorithm_parameters": {
    "n_particles": 10,
    "w": 0.9,
    "c1": 1.5,
    "c2": 1.5
  },
  "worker_notes": {
    "parameters": {
      "n_particles": 10,
      "w": 0.9,
      "c1": 1.5,
      "c2": 1.5,
      "budget": 150,
      "seed": 42
    },
    "observations": "10 worker summary entries; authoritative points are in the evaluator trajectory",
    "proposed_improvements": [
      {
        "x": 1.7750866774902319,
        "y": -2.2748646310976604,
        "value": 18.768710577752124
      },
      {
        "x": 0.8671790763870466,
        "y": -1.7295121847149513,
        "value": 17.01591098860983
      },
      {
        "x": 2.1605394231742188,
        "y": -3.617747127878139,
        "value": 16.991149260368484
      }
    ]
  }
}
```

## Evaluation efficiency and retained final performance

| Method | Retained best | Total calls | Optimization seconds | First call >= 15 | First call >= 19 |
|---|---:|---:|---:|---:|---:|
| bayesian | 19.93319883 | 300 | 1.757 | 23 | 156 |
| gradient | 20.00000000 | 300 | 0.546 | 11 | 161 |
| particle_swarm | 18.76871058 | 300 | 0.547 | 30 | not reached |

Fixed thresholds support evaluation-efficiency comparisons without conflating model-generation time with optimization time. Local model authoring timing and token counts are retained in worker development/repair metadata. Phase two restarts each revised algorithm with shared candidates and the same seed rather than continuing in-memory optimizer state.

## Method-specific findings

Bayesian optimization used a Matern 3/2 Gaussian process and UCB acquisition; its independent search concentrated near a peak also reached by gradient ascent. Sharing the swarm candidate moved both methods into a better basin. Gradient ascent refined that candidate with central differences and backtracking. The swarm discovered the strongest independent candidate, but its high inertia (0.9) and limited remaining generations produced less precise final refinement. Recommended improvements are output normalization and adaptive kernel scales for Bayesian optimization, boundary-safe finite differences and a bounded per-start budget for gradient ascent, and declining inertia plus smaller local velocities for the swarm.

The supervisor corrected auxiliary swarm summary coordinates to match personal-best values in selected main implementations, and bounded gradient difference probes. Exact replay tests verify all six measured trajectories remain unchanged and spend no new benchmark calls. Original worker development and reports remain in their branches.

## Final conclusions

This is one seeded run per method, not a statistical comparison. Improvements in the second phase coincide with sharing candidates, an additional budget, and code revisions; without equal-budget independent continuation controls they cannot be attributed causally to collaboration. Similar final values may indicate convergence to local peaks, but the objective error alone does not prove a worker was trapped.

Evaluation efficiency is shown by the full best-so-far curves. Runtime covers optimization and evaluator IPC, excluding local model authoring and Git publication. Imported candidate values never count as worker observations unless re-evaluated. The benchmark reference maximum is used only here for final error calculations.

Recommended next experiments: multiple paired seeds, independent 300-evaluation controls, fixed-code collaboration ablations, and acquisition/gradient/swarm parameter sweeps.
