"""Independent update checks and safety contracts for first-order integrators."""

import numpy as np
import pytest

from nbody.constants import G
from nbody.core import SimulationConfig, SystemState
from nbody.integrators import euler_cromer, forward_euler
from nbody.simulation import run_simulation

METHODS = [forward_euler, euler_cromer]


@pytest.mark.parametrize("method", METHODS)
def test_analytic_pair_update_and_ownership(method):
    # Separation 5 m, unit direction (3/5, 4/5, 0); independent force formula.
    initial = SystemState([2, 3], [[0, 0, 0], [3, 4, 0]],
                          [[1, -2, 0], [-1, 0, 2]], time=7)
    acceleration = G * np.array([[9/125, 12/125, 0], [-6/125, -8/125, 0]])
    dt = 0.25
    result = method(initial, dt)
    # Velocity subtraction at large initial velocity would hide tiny kicks;
    # also independently check the acceleration using initially resting bodies.
    resting = SystemState(initial.masses, initial.positions, np.zeros((2, 3)))
    kicked = method(resting, dt)
    np.testing.assert_allclose(kicked.velocities, dt * acceleration, rtol=5e-14, atol=0)
    expected_velocity = initial.velocities + dt * acceleration
    drift = expected_velocity if method is euler_cromer else initial.velocities
    np.testing.assert_allclose(result.positions, initial.positions + dt * drift,
                               rtol=5e-14, atol=0)
    if method is euler_cromer:
        np.testing.assert_allclose(kicked.positions[0], dt**2 * acceleration[0],
                                   rtol=5e-14, atol=0)
    else:
        np.testing.assert_array_equal(kicked.positions, resting.positions)
    assert result.time == 7
    np.testing.assert_array_equal(result.masses, initial.masses)
    np.testing.assert_array_equal(initial.positions, [[0, 0, 0], [3, 4, 0]])
    for field in ("masses", "positions", "velocities"):
        assert not np.shares_memory(getattr(result, field), getattr(initial, field))
        assert not getattr(result, field).flags.writeable


@pytest.mark.parametrize("method", METHODS)
def test_exact_one_body_motion_with_runner(method):
    initial = SystemState([2], [[0, 0, 0]], [[1, -2, 0.5]], time=-1)
    result = run_simulation(initial, SimulationConfig(0.25, 8), method)
    for k, snapshot in enumerate(result.states):
        np.testing.assert_array_equal(snapshot.positions, initial.velocities * k * 0.25)
        np.testing.assert_array_equal(snapshot.velocities, initial.velocities)
        assert snapshot.time == -1 + k * 0.25


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("dt,error", [(0, ValueError), (-1, ValueError),
    (np.nan, ValueError), (np.inf, ValueError), (True, TypeError), ("1", TypeError)])
def test_invalid_dt(method, dt, error):
    with pytest.raises(error):
        method(SystemState([1], [[0, 0, 0]], [[0, 0, 0]]), dt)


@pytest.mark.parametrize("method", METHODS)
def test_invalid_state_singularity_and_overflow(method):
    with pytest.raises(TypeError, match="SystemState"):
        method(None, 1)
    with pytest.raises(ValueError, match="coincident"):
        method(SystemState([1, 1], np.zeros((2, 3)), np.zeros((2, 3))), 1)
    with pytest.raises(FloatingPointError):
        method(SystemState([1], [[0, 0, 0]], [[1e308, 0, 0]]), 2)


@pytest.mark.parametrize("method", METHODS)
def test_explicit_gravity_constant(method):
    initial = SystemState([2, 3], [[0, 0, 0], [3, 4, 0]], np.zeros((2, 3)))
    normal = method(initial, 1)
    doubled = method(initial, 1, gravitational_constant=2*G)
    np.testing.assert_array_equal(doubled.velocities, 2*normal.velocities)
    with pytest.raises(ValueError):
        method(initial, 1, gravitational_constant=0)


@pytest.mark.parametrize("method", METHODS)
def test_three_body_permutation_and_translation(method):
    initial = SystemState([2, 3, 5], [[0, 0, 0], [3, 4, 0], [-2, 1, 2]],
                          [[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    order = [2, 0, 1]
    permuted = SystemState(initial.masses[order], initial.positions[order],
                           initial.velocities[order])
    shifted = SystemState(initial.masses, initial.positions + [8, -4, 2],
                          initial.velocities)
    result = method(initial, 0.25)
    reordered = method(permuted, 0.25)
    translated = method(shifted, 0.25)
    np.testing.assert_allclose(reordered.velocities, result.velocities[order],
                               rtol=5e-14, atol=0)
    np.testing.assert_allclose(reordered.positions, result.positions[order],
                               rtol=5e-14, atol=0)
    np.testing.assert_allclose(translated.velocities, result.velocities,
                               rtol=5e-14, atol=0)
