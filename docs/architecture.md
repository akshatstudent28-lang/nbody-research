# Part 1 architecture and scientific contracts

## SystemState

SystemState(masses, positions, velocities, time=0.0) stores all bodies together.
Row i in each array refers to the same body. masses has shape (N,), positions
and velocities have shape (N, 3), and N must be at least one. Arrays are owned,
C-contiguous float64 copies. Fields are frozen and arrays are read-only to
prevent accidental mutation. This is not a security boundary: advanced NumPy
users can deliberately change write flags. Numerical updates will create new
states. Dataclass equality is disabled because array comparisons need an explicit
norm and tolerance, not ambiguous elementwise truth values.

Construction checks real numeric dtypes, finiteness, positive masses, and shape
consistency. Numeric strings, complex arrays, and boolean arrays are rejected.
NumPy coercion can turn mixed boolean/numeric sequences into numeric arrays;
validation concerns the resulting numeric array, not every original Python item.
Integers convert to float64; very large integers may round. This representation
does not offer arbitrary precision or a guarantee that finite inputs produce
finite downstream arithmetic.

There is no separate Body class: it would duplicate data or require keeping
objects synchronized with arrays. A single shape convention simplifies later
vector forces and three-dimensional angular momentum. Two-dimensional systems
use zero z coordinates. Acceleration is omitted because it is derived from
positions, masses, and a force law; storing it now risks stale duplicated data.

The state container accepts coincident positions. Newtonian acceleration there
is undefined, so the future gravity evaluator must reject it explicitly.
No softening, clipping, collision handling, or distance floor has been introduced.
Zero-mass tracers are outside the present strictly positive-mass model.

Construction and validation take O(N) time and O(N) storage. The arrays use
7N float64 elements, or 56N bytes, excluding Python objects and temporary copies.
This is a storage calculation, not a measured performance benchmark. Future
direct pairwise gravity will have a different, quadratic computational cost.

## SimulationConfig

SimulationConfig(dt, num_steps) requires finite dt > 0 in seconds and a
nonnegative integer step count. Booleans and fractional step counts are rejected.
duration = dt * num_steps is derived and must remain finite. Zero steps means
recording the initial state only. Negative state times are allowed because an
epoch is arbitrary; backward integration is not currently a configuration option.

The requested duration is subject to float64 rounding. A future simulation
engine must define time-grid and endpoint semantics and handle loss of time
resolution for extreme epochs/timesteps. This object does not advance anything,
select an integrator, or promise that a chosen timestep is physically adequate.

Config and state share a small internal scalar-validation helper. No generic
validation framework or extra dependency is needed.

## Constants and dimensions

G = 6.67430e-11 m^3 kg^-1 s^-2, CODATA 2022 nominal value.
Reference: https://physics.nist.gov/cuu/pdf/wall_2022.pdf
Its standard uncertainty is 1.5e-15 m^3 kg^-1 s^-2; G is not exact.
Future controlled experiments should hold the nominal value fixed and record it.

Dimensional planning for acceleration:
[G m r / |r|^3] = (m^3 kg^-1 s^-2)(kg)(m)/(m^3) = m s^-2.
This is a dimensional consistency check of the planned equation, not a test of
an implemented gravity engine.

## Boundaries and next interface

core represents state/configuration; physics will calculate accelerations;
integrators will calculate numerical updates; simulation will manage time and
recording; analysis will calculate diagnostics; visualization will consume data.
No plotting, force evaluation, or simulation loop is coupled into Part 1.

Before Part 2, retain these contracts and add independent force-law checks,
singularity rejection, translation/rotation behavior, and simple known systems.
Later experiment records must include initial arrays, G, method, dt, step count,
duration, seed if used, and environment. Part 1 is not that experiment pipeline.