# Numerical Stability, Accuracy, and Emergent Dynamics in Gravitational N-Body Systems

A scientific Python research project investigating numerical methods through
quantitative validation and controlled experiments. Parts 1-2 provide tested
data structures, configuration, Newtonian gravity, and center of mass. Time integration and plots are not implemented.

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
- src/nbody/physics/: direct gravity and center of mass.
- integrators/, simulation/, analysis/, visualization/, utils/ inside src/nbody/
  remain pre-existing placeholders for future parts.
- experiments/: reproducible static validation script.
- data/raw/, data/processed/: raw and derived datasets.
- results/figures/, results/tables/: scientific outputs.

The existing .gitignore excludes environment files and generated data/results.
Before significant experiments, establish explicit dataset preservation and
provenance; ignored outputs are not automatically backed up by Git.

## Scientific status

Part 2 validates instantaneous Newtonian interactions against analytical cases,
symmetries, and an independent high-precision reference. This does not establish
conservation during time evolution, orbital accuracy, or integrator validity.
See [Part 2 results and limitations](docs/part2-gravity.md).
See [architecture](docs/architecture.md), [validation](docs/validation.md), and
[research journal](docs/research-journal.md). Development advances only on an
explicit START PART X instruction. As authorized, each completed part is
committed and pushed after its tests pass.

## Evaluate gravity and reproduce Part 2

```python
from nbody.physics import accelerations, center_of_mass

a = accelerations(state.masses, state.positions)  # m/s^2, shape (N, 3)
center = center_of_mass(state.masses, state.positions)  # m, shape (3,)
```

Using the state from the example above, these evaluate an instantaneous state;
they do not advance it in time. No softening or distance floor is applied.

```powershell
.\.venv\Scripts\python.exe experiments/validate_gravity.py --output docs/part2-validation.json
```

The report records initial data, reference values, numerical errors, and software
versions. A failed check makes the script exit with status 1. The initial failed
reference report is retained separately and explained in the Part 2 notes.
