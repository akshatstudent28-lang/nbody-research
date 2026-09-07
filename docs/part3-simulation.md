# Part 3 - Fixed-step simulation infrastructure

## Scope and API

`from nbody.simulation import run_simulation, SimulationResult`

`run_simulation(initial_state, config, step)` returns a SimulationResult.
`step(state, dt)` must return a SystemState with updated positions/velocities
and unchanged masses in the same body order. The runner supplies dt in seconds.
The callback chooses the numerical update and any force-law parameters; the
runner has no default integrator. Its returned time is ignored: the runner
assigns the configured clock. Callbacks receive independent state copies.
Mass-array equality is checked, but swaps of equal-mass body identities cannot
be detected. Body ordering remains a caller contract.

`result.states` is a tuple of owned, read-only snapshots. It includes the initial
state and every completed step, so its length is num_steps + 1.
`result.final_state` returns the last snapshot. Array write protection guards
against accidental mutation, as in SystemState; it is not a security boundary.

The full time grid is computed before callbacks run:
`t[k] = initial_state.time + k * config.dt`, using float64 arithmetic.
Times must be finite and strictly increasing. This avoids cumulative addition
error, but rounded intervals may differ slightly from dt. The callback always
receives the configured dt. Unresolvable steps and endpoint overflow raise
ValueError. Zero steps records only the initial state and never calls step.

Callback exceptions propagate without a partial result. The runner cannot undo
external side effects of user-supplied callbacks. Invalid return types and
changed mass arrays are rejected. SystemState validates shapes and finiteness.
No collisions, stopping events, adaptive steps, file persistence, or restart
format are implemented. Storage is O((steps + 1) * bodies), plus an O(steps)
time grid. Copying/validation overhead is O(steps * bodies); total computation
also depends on the injected step function. Large runs require memory planning.

## Run in VS Code / PowerShell

From the project folder:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe experiments/validate_simulation.py
```

Expected demonstration output:

```text
Part 3: exact free motion (no gravitational integration)
Recorded states: 9
Final time: 2.0 s
Final position: [2.0, -4.0, 1.0] m
Maximum position error: 0.0 m
PASS
```

The example uses one 2 kg body, initially at the origin, with velocity
(1, -2, 0.5) m/s; dt=0.25 s for eight steps. The injected drift function is exact
for constant velocity. The binary-exact input values justify exact equality.
There is no random seed, force evaluation, or gravitational integrator here.

## Validation and scientific limits

2026-09-07: 134 tests passed (112 existing and 22 new) in 0.20 s.
The demonstration passed with zero final position error. New tests cover exact
motion across all saved states, ownership, callback time/dt, nonbinary dt,
zero steps, grid overflow/loss of resolution before callbacks, invalid return
values, mass/body changes, argument checks, and exception propagation.
The existing Part 2 gravity tests remain passing.

This validates scheduling and recording. It does not demonstrate orbital
accuracy, integration convergence, or long-term conservation. A gravitational
integration method and its scientific validation require a later part.
