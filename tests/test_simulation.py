"""Contract checks and exact free-motion validation for the simulation runner."""

import numpy as np
import pytest

from nbody.core import SimulationConfig, SystemState
from nbody.simulation import SimulationResult, run_simulation


def state(time=0):
    return SystemState([2, 3], [[0, 0, 0], [4, 8, -4]],
                       [[1, -2, 0], [-1, 0, 2]], time)


def drift(s, dt):
    return SystemState(s.masses, s.positions + dt * s.velocities,
                       s.velocities)


def test_exact_motion_and_owned_history():
    initial = state(-2)
    result = run_simulation(initial, SimulationConfig(0.25, 8), drift)
    assert len(result.states) == 9
    for k, snapshot in enumerate(result.states):
        assert snapshot.time == -2 + k * 0.25
        np.testing.assert_array_equal(snapshot.positions,
                                      initial.positions + k * 0.25 * initial.velocities)
        np.testing.assert_array_equal(snapshot.velocities, initial.velocities)
        assert not snapshot.positions.flags.writeable
        assert not np.shares_memory(snapshot.positions, initial.positions)
    assert result.final_state is result.states[-1]
    np.testing.assert_array_equal(initial.positions, state().positions)


def test_zero_steps_never_calls_step():
    def fail(*args):
        pytest.fail("zero steps must not invoke callback")
    result = run_simulation(state(), SimulationConfig(1, 0), fail)
    assert len(result.states) == 1
    assert result.final_state.time == 0


def test_clock_is_indexed_and_owned_by_runner():
    seen = []
    def step(s, dt):
        seen.append((s.time, dt))
        return SystemState(s.masses, s.positions, s.velocities, -999)
    result = run_simulation(state(2), SimulationConfig(0.1, 20), step)
    assert [s.time for s in result.states] == [2 + k * 0.1 for k in range(21)]
    assert seen == [(2 + k * 0.1, 0.1) for k in range(20)]


@pytest.mark.parametrize("epoch,dt,steps", [(1e20, 1, 1), (1e308, 1e308, 1),
                                           (float(2**53 - 1), 1, 3)])
def test_invalid_grid_rejected_before_callback(epoch, dt, steps):
    calls = []
    with pytest.raises(ValueError, match="time grid"):
        run_simulation(state(epoch), SimulationConfig(dt, steps),
                       lambda *args: calls.append(args))
    assert calls == []


@pytest.mark.parametrize("candidate", [None, np.zeros((2, 3)), 42])
def test_invalid_step_return(candidate):
    with pytest.raises(TypeError, match="return a SystemState"):
        run_simulation(state(), SimulationConfig(1, 1), lambda *_: candidate)


@pytest.mark.parametrize("masses", [[3, 2], [2, 4], [2]])
def test_mass_and_body_count_changes_rejected(masses):
    candidate = SystemState(masses, np.zeros((len(masses), 3)),
                            np.zeros((len(masses), 3)))
    with pytest.raises(ValueError, match="preserve"):
        run_simulation(state(), SimulationConfig(1, 1), lambda *_: candidate)


def test_step_failure_propagates():
    def fail(s, dt):
        raise FloatingPointError("force singularity")
    with pytest.raises(FloatingPointError, match="force singularity"):
        run_simulation(state(), SimulationConfig(1, 3), fail)


def test_callback_cannot_alias_recorded_history():
    retained = []
    def step(s, dt):
        retained.append(s)
        return drift(s, dt)
    result = run_simulation(state(), SimulationConfig(1, 2), step)
    retained[0].positions.setflags(write=True)
    retained[0].positions[:] = 99
    np.testing.assert_array_equal(result.states[0].positions, state().positions)


@pytest.mark.parametrize("initial,config,step", [(None, SimulationConfig(1, 0), drift),
                                                (state(), None, drift),
                                                (state(), SimulationConfig(1, 0), None)])
def test_bad_runner_arguments(initial, config, step):
    with pytest.raises(TypeError):
        run_simulation(initial, config, step)


@pytest.mark.parametrize("states,error", [([], ValueError), ([None], TypeError),
                                          ([state(), state()], ValueError),
                                          ([state(1), state(0)], ValueError)])
def test_invalid_result(states, error):
    with pytest.raises(error):
        SimulationResult(states)


def test_result_rejects_changed_masses():
    changed = SystemState([1], [[0, 0, 0]], [[0, 0, 0]], 1)
    with pytest.raises(ValueError, match="masses"):
        SimulationResult([state(), changed])
