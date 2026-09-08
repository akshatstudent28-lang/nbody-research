# Part 4 - Forward Euler and Euler-Cromer

## Implementation and use

Both methods are exported from nbody.integrators and accept
(state, dt, *, gravitational_constant=G). They return a new SystemState with
unchanged masses and input timestamp. The Part 3 runner assigns timestamps;
use run_simulation to obtain a physically timed trajectory. Direct calls are
update callbacks, not standalone clock advancement.

Forward Euler:
- r_new = r + dt * v
- v_new = v + dt * a(r)

Euler-Cromer (kick then drift):
- v_new = v + dt * a(r)
- r_new = r + dt * v_new

All bodies use acceleration from the same old position snapshot. Neither
method updates bodies sequentially using partly updated forces. Both call the
existing exact Newtonian point-mass acceleration engine once per step.
For smooth nonsingular solutions, both have O(dt^2) local truncation error
and O(dt) global error over a fixed finite interval. Euler-Cromer is the
kick-drift form of symplectic Euler for this separable Hamiltonian at fixed dt.
It needs no implicit solve. Symplectic does not mean exact energy conservation
or unconditional stability; Part 5 and subsequent diagnostics will develop
those topics more fully.

SI units: dt in seconds, positions in meters, velocities in m/s, acceleration
in m/s^2. Thus dt*a has velocity units and dt*v has position units.
Each step costs O(N^2) time and O(N) auxiliary storage. The existing runner
stores O((steps+1)*N) data. No dependency or architecture change was needed.
A shared private update helper centralizes safety checks without introducing
an integrator class hierarchy.

Input states must be SystemState; dt must be finite, real, positive, and not
boolean. G validation and coincidence detection remain in the gravity engine.
Floating-point range failures raise rather than clipping or softening the
physics. This does not detect collisions between sampled endpoints or guarantee
that a finite result is accurate. Masses and arrays are copied by SystemState.

## Reproduce in VS Code's PowerShell terminal

Run from C:\Users\aksha\Projects\nbody-research:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe experiments/validate_euler.py --output docs/part4-validation.json
```

For your own run:

```python
from nbody.core import SimulationConfig
from nbody.integrators import euler_cromer
from nbody.simulation import run_simulation

# initial is a validated SystemState in SI units.
result = run_simulation(initial, SimulationConfig(dt=1.0, num_steps=100), euler_cromer)
```

## Controlled preliminary orbital experiment

Both masses move in the initial center-of-mass frame. Synthetic masses are
1e20 and 2e20 kg and relative separation R is 1e6 m. The analytical angular
frequency is omega = sqrt(G*(m1+m2)/R^3), with T = 2*pi/omega.
Positions and tangential velocities are weighted by the other body's mass
fraction so total initial momentum and center of mass are zero up to rounding.
The exact relative position is R*(cos(omega*t), sin(omega*t), 0).

The experiment compares the numerical relative position to this solution at
EVERY recorded time, using norm(numerical-exact)/R. It also records maximum
absolute fractional separation error and final position error. Initial arrays,
G, dt, duration, body count, method, step counts, and environment are saved in
part4-validation.json. There is no randomness. Full trajectories are available
inside each SimulationResult but are not persisted by this small benchmark;
the deterministic script and initial configuration reproduce them.

Predeclared basic acceptance checks: refinement must reduce maximum position
error, and the fine run must remain below 0.2. This deliberately loose smoke
threshold checks gross behavior, not research-grade accuracy. It was set before
the first run and was not adjusted after seeing results. No formal convergence
order or universal ranking is inferred from two timesteps and one orbit.

Measured 2026-09-07: T = 44403.41569868171 s.

| Method | Steps | dt (s) | Max position error / R | Max separation error / R |
| --- | ---: | ---: | ---: | ---: |
| Forward Euler | 1000 | 44.40341569868171 | 0.3585324117747204 | 0.07688873143993602 |
| Forward Euler | 2000 | 22.201707849340856 | 0.18466439255237493 | 0.0388876438932495 |
| Euler-Cromer | 1000 | 44.40341569868171 | 0.012478660725735929 | 0.0031613327524919743 |
| Euler-Cromer | 2000 | 22.201707849340856 | 0.0062612400755486 | 0.0015757311851452016 |

Forward Euler is substantially inaccurate even though its equations are
implemented correctly. Euler-Cromer performs better for this tested fixture.
Its fine final position error is 4.392559413162859e-05, much smaller than its
maximum error; using only the endpoint would obscure intermediate errors.
The supplied experiment reports both, without cherry-picking.

## Software and scientific validation

Tests independently calculate a 3-4-5 pair acceleration, distinguish old/new
velocity position updates using initially resting bodies, exercise exact
one-body motion through the runner, check ownership, dt/G validation,
singularities and overflow, and exercise a three-body permutation/translation.
Pair and symmetry checks use rtol=5e-14, atol=0; the binary-exact single-body
fixture uses exact equality. No production convergence/diagnostic framework,
other integrators, or graphics have been added. Comprehensive two-body,
conservation, long-term behavior, and convergence studies remain later parts.

## Visual supplement completed

The original no-graphics scope above is superseded by the authorized visual
supplement. Run experiments/show_simulation.py. See [guide](part4-visualization.md).
