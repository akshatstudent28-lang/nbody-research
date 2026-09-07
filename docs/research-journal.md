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