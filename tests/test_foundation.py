"""Data-contract tests, not orbital or gravitational validation."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from nbody.constants import G
from nbody.core import SimulationConfig, SystemState


def sample(**changes):
    values = dict(
        masses=[2, 3],
        positions=[[0, 0, 0], [1, 0, 0]],
        velocities=[[0, 1, 0], [0, -1, 0]],
        time=0,
    )
    values.update(changes)
    return SystemState(**values)


@pytest.mark.parametrize("n", [1, 2, 17])
def test_body_count_shapes_and_dtype(n):
    state = SystemState(np.ones(n), np.zeros((n, 3)), np.zeros((n, 3)))
    assert state.n_bodies == n
    assert state.time == 0.0
    for array in (state.masses, state.positions, state.velocities):
        assert array.dtype == np.float64
        assert array.flags.c_contiguous
        assert not array.flags.writeable


def test_snapshot_owns_inputs_and_preserves_values():
    masses = np.array([2.0, 3.0])
    positions = np.arange(12.0).reshape(2, 6)[:, ::2]  # noncontiguous input
    velocities = np.ones((2, 3))
    expected_positions = positions.copy()
    state = SystemState(masses, positions, velocities, time=-2)
    masses[:] = 9
    positions[:] = 9
    velocities[:] = 9
    assert_array_equal(state.masses, [2, 3])
    assert_array_equal(state.positions, expected_positions)
    assert_array_equal(state.velocities, np.ones((2, 3)))
    assert state.time == -2.0


def test_accidental_mutation_is_rejected():
    state = sample()
    for array in (state.masses, state.positions, state.velocities):
        with pytest.raises(ValueError):
            array.flat[0] = 0
    with pytest.raises(FrozenInstanceError):
        state.time = 1


@pytest.mark.parametrize("changes", [
    {"masses": []}, {"masses": [[2, 3]]}, {"masses": [0, 3]},
    {"masses": [-2, 3]}, {"positions": [[0, 0], [1, 0]]},
    {"velocities": [[0, 0, 0]]}, {"positions": [0, 0, 0]},
    {"positions": [[[0, 0, 0], [1, 0, 0]]]},
    {"positions": [[0], [1, 2]]},
])
def test_invalid_shapes_and_masses(changes):
    with pytest.raises(ValueError):
        sample(**changes)


@pytest.mark.parametrize("field", ["masses", "positions", "velocities", "time"])
@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_nonfinite_values(field, bad):
    values = {
        "masses": [bad, 3],
        "positions": [[bad, 0, 0], [1, 0, 0]],
        "velocities": [[bad, 0, 0], [0, 1, 0]],
        "time": bad,
    }
    with pytest.raises(ValueError):
        sample(**{field: values[field]})


@pytest.mark.parametrize("changes", [
    {"masses": ["2", "3"]}, {"masses": [2+1j, 3]},
    {"masses": [True, False]}, {"positions": [["0"]*3]*2},
    {"velocities": [[1j]*3]*2}, {"time": "0"},
    {"time": True}, {"time": 1j},
])
def test_nonreal_inputs(changes):
    with pytest.raises(TypeError):
        sample(**changes)


def test_coincident_positions_are_representable():
    state = sample(positions=np.zeros((2, 3)))
    assert_array_equal(state.positions, np.zeros((2, 3)))


def test_constants_match_documented_reference():
    assert G == 6.67430e-11


@pytest.mark.parametrize("steps", [0, 1, 40, np.int64(4)])
def test_config_duration(steps):
    config = SimulationConfig(dt=0.25, num_steps=steps)
    assert config.duration == int(steps) / 4
    assert isinstance(config.num_steps, int)
    with pytest.raises(FrozenInstanceError):
        config.dt = 2


@pytest.mark.parametrize("dt", [0, -1, np.nan, np.inf, -np.inf, 10**400])
def test_invalid_timestep_values(dt):
    with pytest.raises(ValueError):
        SimulationConfig(dt, 1)


@pytest.mark.parametrize("dt", [True, "1", 1j])
def test_invalid_timestep_types(dt):
    with pytest.raises(TypeError):
        SimulationConfig(dt, 1)


@pytest.mark.parametrize("steps", [True, 1.0, 1.5, "1"])
def test_invalid_step_types(steps):
    with pytest.raises(TypeError):
        SimulationConfig(1, steps)


@pytest.mark.parametrize("dt, steps", [(1, -1), (1e308, 2), (1, 10**400)])
def test_invalid_step_values_or_duration(dt, steps):
    with pytest.raises(ValueError):
        SimulationConfig(dt, steps)