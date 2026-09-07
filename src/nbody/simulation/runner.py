"""Fixed-step orchestration, independent of any integration method."""

from dataclasses import dataclass
from typing import Callable

import numpy as np

from nbody.core import SimulationConfig, SystemState

StepFunction = Callable[[SystemState, float], SystemState]


@dataclass(frozen=True, eq=False)
class SimulationResult:
    """Owned snapshots including the initial state and every completed step.

    Storage is O((steps + 1) * bodies). No decimation or disk streaming.
    """

    states: tuple[SystemState, ...]

    def __post_init__(self) -> None:
        states = tuple(self.states)
        if not states:
            raise ValueError("a result must contain an initial state")
        if any(not isinstance(state, SystemState) for state in states):
            raise TypeError("states must contain SystemState objects")
        masses = states[0].masses
        for previous, current in zip(states, states[1:]):
            if current.time <= previous.time:
                raise ValueError("state times must strictly increase")
            if not np.array_equal(current.masses, masses):
                raise ValueError("body masses and order must remain unchanged")
        # Own copies even when callers retain the original snapshots.
        object.__setattr__(self, "states", tuple(
            SystemState(s.masses, s.positions, s.velocities, s.time) for s in states
        ))

    @property
    def final_state(self) -> SystemState:
        return self.states[-1]


def run_simulation(
    initial_state: SystemState,
    config: SimulationConfig,
    step: StepFunction,
) -> SimulationResult:
    """Advance with step(state, dt), recording the initial and each new state.

    The runner owns the clock: t[k] = t0 + k * dt (float64 arithmetic).
    A step computes positions/velocities and preserves masses/body order. Its
    returned time is ignored. Each callback receives an independent snapshot.
    Exceptions propagate; no partial result is returned. No force law is chosen.
    """
    if not isinstance(initial_state, SystemState):
        raise TypeError("initial_state must be a SystemState")
    if not isinstance(config, SimulationConfig):
        raise TypeError("config must be a SimulationConfig")
    if not callable(step):
        raise TypeError("step must be callable")
    # Validate the entire grid before invoking a callback. Index multiplication
    # avoids cumulative clock drift; rounding can still make an epoch unusable.
    times = [initial_state.time]
    for index in range(1, config.num_steps + 1):
        time = initial_state.time + index * config.dt
        if not np.isfinite(time):
            raise ValueError("time grid must remain finite")
        if time <= times[-1]:
            raise ValueError("dt is too small to advance the time grid at this epoch")
        times.append(time)
    current = SystemState(initial_state.masses, initial_state.positions,
                          initial_state.velocities, initial_state.time)
    states = [current]
    for time in times[1:]:
        supplied = SystemState(current.masses, current.positions,
                               current.velocities, current.time)
        candidate = step(supplied, config.dt)
        if not isinstance(candidate, SystemState):
            raise TypeError("step must return a SystemState")
        if not np.array_equal(candidate.masses, current.masses):
            raise ValueError("step must preserve body masses and order")
        current = SystemState(candidate.masses, candidate.positions,
                              candidate.velocities, time)
        states.append(current)
    return SimulationResult(tuple(states))
