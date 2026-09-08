# Numerical Stability, Accuracy, and Emergent Dynamics in Gravitational N-Body Systems

A scientific Python research project investigating numerical methods through
quantitative validation and controlled experiments. Parts 1-5 provide tested
data structures, configuration, Newtonian gravity, center of mass, a fixed-step simulation runner, and Forward Euler, Euler-Cromer, Velocity Verlet, and Leapfrog integrators. An interactive arbitrary-N visual simulation is available.


## See the simulation (VS Code terminal)

```powershell
.\.venv\Scripts\python.exe experiments/show_simulation.py
```

A native animation window opens with Play/Pause, Replay, a frame timeline,
playback speed, orbital trails, and integration-method selection. Default:
two moving bodies, 3D view, Velocity Verlet, and four selectable implementations. Add --view xy for a planar view.

For four bodies:

```powershell
.\.venv\Scripts\python.exe experiments/show_simulation.py --config experiments/four_body_visual_demo.json
```

Custom JSON supports arbitrary N with explicit SI masses, positions, velocities,
dt, and step count. The four-body example is exploratory, not scientifically
validated orbital behavior. See [visual simulation guide](docs/part4-visualization.md)
for controls, custom systems, exports, tests, and limits.

Every future part must also update the visual simulation with its relevant
capabilities and results, while retaining quantitative scientific validation.
This project requirement is recorded in AGENTS.md.
## Setup and verification (PowerShell)

Python 3.10 or newer is declared supported; see docs/validation.md for the tested
environment. Run from this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

NumPy and Matplotlib are runtime dependencies. pytest is a development dependency.
Matplotlib provides interactive trajectory playback. pyproject.toml
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
- src/nbody/simulation/: fixed-step runner and immutable recorded snapshots.
- src/nbody/integrators/: Forward Euler and Euler-Cromer numerical updates.
- src/nbody/visualization/: interactive 3D and planar N-body history viewer.
- analysis/, utils/ inside src/nbody/
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
explicit START PART X instruction. Commits and pushes require explicit user authorization.

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


## Run Part 3

```powershell
.\.venv\Scripts\python.exe experiments/validate_simulation.py
```

This exact constant-velocity example records nine states and prints PASS,
with final position [2.0, -4.0, 1.0] m at 2.0 s. It validates the simulation
runner; it is not an orbit simulation. See [Part 3](docs/part3-simulation.md)
for the callback API, test results, and time/memory contracts.

## Run Part 4

See [Part 4 implementation and measured orbital errors](docs/part4-euler.md).
Run experiments/validate_euler.py with the project Python, optionally passing
--output docs/part4-validation.json to preserve the report.

## Part 5: symplectic methods and comparison

Velocity Verlet and synchronized kick-drift-kick Leapfrog are now available in
the viewer. See [Part 5 results and reproducibility](docs/part5-verlet.md).
Run experiments/validate_verlet.py for the refinement and 20-orbit study.
Use --config experiments/part5_elliptical.json with show_simulation.py to view it.
