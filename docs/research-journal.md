# Research journal

## 2026-09-07 - Part 1: project foundation

Goal: establish a small, testable representation for future Newtonian N-body
research before implementing physical evolution.

Inspection: existing Git repository contained an untracked directory scaffold,
packaging metadata, README, and placeholder packages, with no executable tests.
No AGENTS.md instructions were found in the checked project/ancestor paths.

Implementation: retained the scaffold; added centralized SI G, copied/read-only
SystemState arrays, validated SimulationConfig, NumPy dependency, 56 test cases,
and architecture/setup/validation documentation. Created a local virtual
environment. No gravity or integration features were added.

Assumptions: positive point masses, at least one body, three Cartesian coordinates,
SI inputs, float64 arithmetic, arbitrary finite time epoch, positive fixed
timestep, nonnegative integer step count.

Tests/results: 56 passed in 1.48 s; dependency check and compilation succeeded.
Package import resolved to the repository. dt=0.25 s and 40 steps gives 10.0 s.
Exact comparisons suffice for preservation and binary-exact duration examples.
No orbital or conservation measurements exist yet.

Errors/failed attempts: the initial sandbox process could not launch; an approved
external-workspace command succeeded. Dependency installation encountered
temporary connection resets and recovered automatically. No test failures
occurred; no tolerance weakening or implementation repair was needed after testing.

Observations/decisions: owned snapshots avoid input aliasing; fixed 3D shapes
simplify later vector calculations. O(N) construction/storage is distinct from
the future O(N^2) direct gravity calculation. Keep acceleration derived, avoid
a redundant Body class, and defer plotting dependencies until needed.

Open questions: future gravity must reject singular separations and handle
arithmetic overflow explicitly. Future simulation must define endpoint/time-grid
semantics. Cross-version testing and a portable environment lock remain future
reproducibility improvements if needed.

Next possible step: Part 2 gravity and center of mass, only after authorization.
No Git commit was made.

## 2026-09-07 - Part 2: Newtonian gravity

Goal: implement and quantitatively check direct Newtonian interactions and center
of mass without adding time evolution.

Inspection: clean main at 1fa4e50; all 56 existing tests passed. Existing state
and validators were reusable. No applicable AGENTS.md was found.

Implementation: added pairwise force, unordered-pair N-body acceleration, scaled
mass-weighted center of mass, 56 new tests, and a reproducible static validation
script. No dependencies were added; core interfaces were preserved.

Assumptions: positive point masses, SI Cartesian coordinates, float64,
unsoftened Newtonian gravity, explicit singularity and arithmetic range errors.

Tests: 112 tests passed; corrected validation report passed all six checks.
Dependency checks and compilation succeeded. Full commands and thresholds are
in part2-gravity.md, with inputs/results in part2-validation.json.

Results: normalized independent-reference acceleration error 5.36054e-16;
maximum absolute error 3.02923e-28 m/s^2; normalized net-force residual
3.88556e-17. The analytical center was (3,6,-3) m with zero measured error.

Failure: initial report's hand-entered pair-force reference was incorrect,
producing normalized error 7.49086e-05. Decimal arithmetic independently
identified the correct reference. Corrected only the reference; no production
code or tolerance changes. Preserved part2-validation-initial.json and reran
the report and all tests successfully.

Decisions: use clear O(N^2) pair loops and O(N) memory. Evaluate accelerations
directly rather than requiring representable pair forces for every interaction.
Reject coincidence and arithmetic range failures explicitly. No performance
optimization, softening, integration, or orbital conclusions.

Open questions: roundoff for large coordinate offsets, extreme dynamic ranges,
and future integrator conservation. The present static checks cannot resolve
long-term numerical behavior.

Next possible step: Part 3 simulation infrastructure, only after authorization.
Standing user authorization permits commit/push after successful part validation.

## 2026-09-07 - Part 3: simulation infrastructure

Goal: decouple scheduling/history from numerical integration and force laws.
Implemented run_simulation, SimulationResult, indexed time preflight, independent
snapshots, and callback return/mass checks. Added a free-motion demonstration
and 22 contract tests. No dependencies or gravitational integrators were added.

Results: 134 tests passed in 0.20 s. Exact free-motion demo recorded nine states,
ended at t=2 s and position (2,-4,1) m, with zero position error. No test failures
or tolerance adjustments occurred. These results validate orchestration only.

Decisions: the runner owns time; callback-returned time is ignored. Preserve
configured dt for updates while requiring a representable increasing grid.
Record all states with O(steps * bodies) storage. Equal-mass identity swaps are
not detectable, so ordering remains a callback contract. No partial results on
failure and no rollback of external callback side effects.

Continuation checkpoint: docs/part3-progress.md. User requested durable progress
if context is exhausted. Future work requires explicit authorization for the
next part; gravitational integration and orbit validation remain unimplemented.
