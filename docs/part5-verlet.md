# Part 5 - Velocity Verlet and Leapfrog

## Run the visual simulation

In VS Code's PowerShell terminal, from the project folder:

```powershell
.\.venv\Scripts\python.exe experiments/show_simulation.py
```

The viewer now defaults to Velocity Verlet and offers all four implementations:
Velocity Verlet, Leapfrog (KDK), Euler-Cromer, and Forward Euler. The selector
was expanded and visually checked. All playback controls remain available.
Use --view xy for a planar display. Arbitrary-N custom configurations still work.

To inspect the same initial conditions and duration as the conservation study:

```powershell
.\.venv\Scripts\python.exe experiments/show_simulation.py --config experiments/part5_elliptical.json --view xy
```

This computes each method for 20 analytical orbital periods. Switching methods
preserves time and bounds. Large errors from Forward Euler remain visible.

## Algorithms and interface

Both methods accept (state, dt, *, gravitational_constant=G), return owned
SystemState snapshots, and retain the input epoch. The runner owns timestamps.
Positions and velocities in returned states refer to the SAME full timestep.
No acceleration cache or half-step velocity is stored in SystemState.

Velocity Verlet:

1. a0 = acceleration(r0)
2. r1 = r0 + dt*v0 + (dt^2/2)*a0
3. a1 = acceleration(r1)
4. v1 = v0 + (dt/2)*(a0+a1)

Kick-drift-kick Leapfrog:

1. a0 = acceleration(r0)
2. v_half = v0 + (dt/2)*a0
3. r1 = r0 + dt*v_half
4. a1 = acceleration(r1)
5. v1 = v_half + (dt/2)*a1

Substituting v_half into the last two equations produces Velocity Verlet.
For position-dependent Newtonian accelerations, these are equivalent in exact
arithmetic. Different floating-point grouping causes small roundoff differences.
They are four named implementations with the Euler methods, not four independent
algorithm families. A later three-method comparison must not treat these two
as independent algorithms just because their names differ.

Both new methods have local error O(dt^3) and global error O(dt^2) on fixed
finite intervals for sufficiently smooth, nonsingular solutions. Both are
symmetric under time reversal and symplectic for this separable Hamiltonian
with fixed timestep. Here H(q,p)=sum(p_i^2/(2*m_i))+U(q). A kick evolves the
potential part; a drift evolves the kinetic part. Symplectic means preservation
of canonical phase-space geometry, not merely small position error or exact
energy conservation. A symmetric composition of these maps gives the KDK step.

Under appropriate regularity and timestep conditions, symplectic methods can
approximately conserve a nearby modified Hamiltonian, helping explain favorable
long-duration energy behavior. This is not an unconditional guarantee, especially
near close encounters. See Hairer, Lubich, and Wanner's review:
https://www.unige.ch/~hairer/preprints/gniverlet.html

No general negative-dt interface was added; reversibility is tested by reversing
velocities, integrating forward again, and comparing to the original state with
opposite velocities. This matches the positive-dt configuration contract.

## Cost and safety

Each call evaluates gravity twice: O(N^2) time and O(N) auxiliary memory. The
runner still records O(steps*N) state data. This baseline does not reuse the
previous step's final acceleration. Caching could reduce force evaluations,
but would require an explicit cache lifetime contract and measurement first.

No dependencies were added for Part 5. Both methods use the existing gravity
engine with no softening, collision prescription, or distance floor. Invalid
dt, input types, gravity constants, singular initial/new positions, and range
failures are rejected. An exact newly coincident pair is tested explicitly.
Crossings between sampled positions remain undetected, as in the prior model.

## Actual software verification

2026-09-07: 205 tests passed in 12.98 s. This includes all previous tests, 22
new second-order/benchmark cases, and a new four-method visual selector case.
The initial Part 5 suite passed 203 tests; the two additional checks also passed.
No numerical failures or tolerance changes occurred.

Checks: independently computed scalar pair update; exact free motion;
immutability; three-body multi-step equivalence; velocity-flip reversibility;
invalid dt/state/G; old/new-position singularities; overflow; independently
calculated benchmark energy; four-method rendering, CLI export, and selector
layout. Pair/energy comparison rtol=5e-14, atol=0. Reversal/equivalence tolerances
are absolute 2e-13 m or m/s on small SI fixtures. These allow accumulated
roundoff over 100 steps, not large physical errors. Free motion is binary-exact.

Native TkAgg GUI check passed all six tests: timer advancement, pause,
scrub/method switch, trails, replay, final frame. Viewer preview and conservation
figure were visually inspected. Reports and figures are saved in docs/part5-*.

## Scientific experiment

Reproduce:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe experiments/validate_verlet.py
.\.venv\Scripts\python.exe experiments/check_viewer_gui.py
```

Part5-validation.json records full initial conditions, constants, environment,
methods, timesteps and durations. Part5-conservation-series.npz preserves the
measured time series; all scenarios are deterministic. Diagnostics remain local
to this experiment. Part 7 will introduce the reusable diagnostic system.

Circular orbit: masses 1e20 and 2e20 kg, separation 1e6 m, one period.
For each new method, 200/400/800 steps produced maximum relative position errors
about 0.00215905 / 0.000539912 / 0.000134987. Error ratios were 3.99889 and 3.99974,
and observed orders were 1.99960 and 1.99990. The predeclared ratio interval
was (3.5,4.5); fine error threshold 1e-3. Both checks passed.

Conservation: semimajor axis 1e6 m, eccentricity 0.3, 20 analytical periods,
400 steps per period, dt=111.00853924670427 s, 8000 steps total. Both masses move
in the initial center-of-mass frame. Energy error is (E(t)-E(0))/abs(E(0)), where
E=K+U. Angular error is norm(L(t)-L(0))/norm(L(0)). Momentum change is normalized
by sum(m_i*norm(v_i(0))), avoiding division by zero initial total momentum.

| Method | Max relative energy error | Max relative angular momentum error |
| --- | ---: | ---: |
| Forward Euler | 0.679863933451361 | 0.5164345361643973 |
| Euler-Cromer | 0.007371352510435905 | 7.208732529641082e-15 |
| Velocity Verlet | 0.0001341747104164049 | 4.276366754871828e-15 |
| Leapfrog KDK | 0.0001341747104063501 | 9.28582495343597e-15 |

Momentum change measured zero for all four on this specially structured fixture;
that is not a general proof of exact floating-point momentum conservation.
Verlet/KDK energy error was oscillatory in this experiment: the first- and
last-five-orbit error envelopes were both about 1.3417471e-4. The final error
was much smaller (~2.5311e-7), demonstrating why endpoint-only reporting misleads.

Predeclared new-method limits: max energy error <2e-3; angular error <5e-12;
last-five-period envelope <=1.2*first-five-period envelope+1e-12. All-method
momentum threshold <5e-12. All passed. The criteria are fixture-specific and
were not adjusted after execution. Poor Forward Euler accuracy is preserved,
not hidden by the benchmark's overall pass status.

The figure uses absolute relative energy error on a logarithmic axis for all
methods and signed error on a separate axis for Verlet/KDK. Exact zeros are
omitted only from the logarithmic drawing, not changed in stored data.

## Research direction and limitations

The user wants chaos/sensitivity and an eventual three-method comparison to be
central research aims. These still require controlled comparisons and the later
validation milestones. Twenty periods of one two-body case do not establish
arbitrary-duration stability, general chaotic-system accuracy, or a universal
ranking. No chaos claim is made here.

The exact method meant by 'NASA's constructed one' has not yet been identified.
NASA published Fehlberg Runge-Kutta formulas (NASA-TR-R-287), but that alone does
not identify the user's intended method. No NASA-branded algorithm was guessed
or implemented. Classical RK4 remains Part 6 unless the user explicitly revises
the roadmap. No unsupported claim of the 'three most common' methods is made.
NASA primary report: https://ntrs.nasa.gov/citations/19680027281
