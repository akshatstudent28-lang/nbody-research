# Numerical Stability, Accuracy, and Emergent Dynamics in Gravitational N-Body Systems

A scientific Python research project investigating numerical methods through
quantitative validation and controlled experiments. Part 1 provides tested data
structures and configuration; gravity, integration, and plots are not implemented.

## Setup and verification (PowerShell)

Python 3.10 or newer is declared supported; see docs/validation.md for the tested
environment. Run from this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

NumPy is the only runtime dependency. pytest is a development dependency.
Matplotlib will be added when a scientific figure is needed. pyproject.toml
is the dependency source of truth; no redundant requirements.txt is needed.
An actual environment snapshot is recorded in docs/environment-part1.txt.

## Example: a state, not a simulated orbit

```python
from nbody.core import SimulationConfig, SystemState

state = SystemState(
    masses=[2.0, 3.0],                         # kg
    positions=[[0, 0, 0], [1, 0, 0]],         # m
    velocities=[[0, 0, 0], [0, 0, 0]],        # m/s
)
config = SimulationConfig(dt=0.25, num_steps=40)
assert state.n_bodies == 2
assert config.duration == 10.0                # s
```

Coordinates share one Cartesian reference frame. Planar data uses z=0.
States copy inputs into read-only float64 arrays. Construct a new state for an
update. Masses must be finite and positive; shapes must agree. Time is finite
seconds relative to an arbitrary epoch. Values have documented SI units, but
there is no automatic unit detection or conversion.

## Layout

- src/nbody/core/: validated state and fixed-step configuration.
- src/nbody/constants.py: sourced SI gravitational constant.
- tests/: executable data-contract tests.
- docs/: architecture, validation, environment, and research journal.
- physics/, integrators/, simulation/, analysis/, visualization/, utils/
  inside src/nbody/ are pre-existing placeholders for future parts.
- experiments/: future explicit experiment scripts.
- data/raw/, data/processed/: raw and derived datasets.
- results/figures/, results/tables/: scientific outputs.

The existing .gitignore excludes environment files and generated data/results.
Before significant experiments, establish explicit dataset preservation and
provenance; ignored outputs are not automatically backed up by Git.

## Scientific status

Passing data tests does not validate Newtonian gravity, conservation, orbital
accuracy, or any integrator. No such claims are made in Part 1.
See [architecture](docs/architecture.md), [validation](docs/validation.md), and
[research journal](docs/research-journal.md). Development advances only on an
explicit START PART X instruction. Changes are not committed automatically.