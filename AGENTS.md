# Project instructions

Project: Numerical Stability, Accuracy, and Emergent Dynamics in Gravitational
N-Body Systems. The user's master protocol governs development.

- Begin only the explicitly authorized numbered part or supplement. Inspect the
  repository, relevant tests/dependencies, and Git status before editing.
- Give a concise plan, implement directly, run tests, validate scientifically,
  report actual results, teach the concepts, and stop. Never advance automatically.
- Every future part MUST also update the visual simulation to expose that part's
  relevant capabilities, methods, systems, diagnostics, or research results.
  Visualization is a core deliverable, not a final decorative stage. Preserve
  arbitrary-N playback and integration with shared SimulationResult histories.
  Include visual behavior, rendered-data correctness, and controller tests in
  the part's review. Do not substitute plausible-looking motion for validation.
- Physics/integration must remain separate from visualization. Playback controls
  must never change recorded physics or the integration timestep.
- Prefer Python, NumPy, and Matplotlib; add other dependencies only when justified.
- Preserve SI units, explicit initial conditions, reproducibility, and numerical
  safety. No silent softening, clipping, invented data, or tolerance weakening.
- Preserve unrelated changes. Do not commit, push, reset, or discard work without
  explicit authorization. A suggested commit message is not permission to commit.
- End-of-part report: what was built; files; architecture; exact tests/results and
  tolerances; explain major concepts (what/why/how, physics/math/CS, inputs/outputs,
  design); measured results; limits; exactly five unanswered understanding
  questions; explanations for teacher/GHP/mentor/judge; research journal;
  suggested commit; scientific/software status review. Then stop.
- Save a progress checkpoint for interrupted work. Do not claim to monitor
  credits or automatically resume when they return.

Current milestone and restart notes: docs/part5-progress.md.
Viewer instructions and extension contracts: docs/part4-visualization.md.
