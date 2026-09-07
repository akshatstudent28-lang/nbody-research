"""Exact free motion demonstration: validates orchestration, not gravity."""

import numpy as np

from nbody.core import SimulationConfig, SystemState
from nbody.simulation import run_simulation


def drift(state, dt):
    return SystemState(state.masses, state.positions + dt * state.velocities,
                       state.velocities)


def main():
    initial = SystemState([2], [[0, 0, 0]], [[1, -2, 0.5]])
    config = SimulationConfig(dt=0.25, num_steps=8)
    result = run_simulation(initial, config, drift)
    expected = initial.positions + config.duration * initial.velocities
    error = float(np.max(np.abs(result.final_state.positions - expected)))
    print("Part 3: exact free motion (no gravitational integration)")
    print(f"Recorded states: {len(result.states)}")
    print(f"Final time: {result.final_state.time} s")
    print(f"Final position: {result.final_state.positions[0].tolist()} m")
    print(f"Maximum position error: {error} m")
    assert error == 0.0
    assert result.final_state.time == 2.0
    print("PASS")


if __name__ == "__main__":
    main()
