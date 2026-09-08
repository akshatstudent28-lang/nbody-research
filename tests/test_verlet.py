"""Independent analytical and geometric checks for second-order methods."""

import numpy as np
import pytest

from nbody.constants import G
from nbody.core import SimulationConfig, SystemState
from nbody.integrators import leapfrog, velocity_verlet
from nbody.simulation import run_simulation

METHODS = [velocity_verlet, leapfrog]


def pair():
    return SystemState([1e10, 2e10], [[-1, 0, 0], [1, 0, 0]], np.zeros((2, 3)), time=7)


@pytest.mark.parametrize("method", METHODS)
def test_independent_collinear_pair(method):
    initial = pair()
    dt = 0.1
    # Scalar inverse-square calculation, independent of production vector gravity.
    a0 = np.array([G*2e10/4, -G*1e10/4])
    expected_x = np.array([-1., 1.]) + 0.5*dt**2*a0
    new_separation = expected_x[1]-expected_x[0]
    a1 = np.array([G*2e10/new_separation**2, -G*1e10/new_separation**2])
    expected_vx = 0.5*dt*(a0+a1)
    result = method(initial, dt)
    np.testing.assert_allclose(result.positions[:, 0], expected_x, rtol=5e-14, atol=0)
    np.testing.assert_allclose(result.velocities[:, 0], expected_vx, rtol=5e-14, atol=0)
    np.testing.assert_array_equal(result.positions[:, 1:], 0)
    np.testing.assert_array_equal(result.velocities[:, 1:], 0)
    assert result.time == 7
    for field in ("masses", "positions", "velocities"):
        assert not np.shares_memory(getattr(initial, field), getattr(result, field))
        assert not getattr(result, field).flags.writeable
    np.testing.assert_array_equal(initial.positions[:, 0], [-1, 1])


@pytest.mark.parametrize("method", METHODS)
def test_exact_free_motion(method):
    initial = SystemState([2], [[0, 0, 0]], [[1, -2, 0.5]], time=-1)
    result = run_simulation(initial, SimulationConfig(0.25, 8), method)
    for k, state in enumerate(result.states):
        np.testing.assert_array_equal(state.positions, initial.positions + k*0.25*initial.velocities)
        np.testing.assert_array_equal(state.velocities, initial.velocities)
        assert state.time == -1 + k*0.25


@pytest.mark.parametrize("method", METHODS)
def test_reversal_with_velocity_flip(method):
    initial = SystemState([1e10, 2e10, 3e10], [[0, 0, 0], [3, 4, 0], [-2, 1, 2]],
                          [[0.1, -0.2, 0], [0, 0.1, -0.1], [0.2, 0, 0.1]])
    forward = run_simulation(initial, SimulationConfig(0.01, 100), method).final_state
    reversed_state = SystemState(forward.masses, forward.positions, -forward.velocities)
    backward = run_simulation(reversed_state, SimulationConfig(0.01, 100), method).final_state
    np.testing.assert_allclose(backward.positions, initial.positions, rtol=0, atol=2e-13)
    np.testing.assert_allclose(backward.velocities, -initial.velocities, rtol=0, atol=2e-13)


def test_equivalence_on_three_body_history():
    initial = SystemState([1e10, 2e10, 3e10], [[0, 0, 0], [3, 4, 0], [-2, 1, 2]],
                          [[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]])
    a = run_simulation(initial, SimulationConfig(0.01, 100), velocity_verlet)
    b = run_simulation(initial, SimulationConfig(0.01, 100), leapfrog)
    for left, right in zip(a.states, b.states):
        np.testing.assert_allclose(left.positions, right.positions, rtol=0, atol=2e-13)
        np.testing.assert_allclose(left.velocities, right.velocities, rtol=0, atol=2e-13)


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("dt,error", [(0, ValueError), (-1, ValueError), (np.inf, ValueError),
                                      (np.nan, ValueError), (True, TypeError), ("1", TypeError)])
def test_invalid_dt(method, dt, error):
    with pytest.raises(error):
        method(pair(), dt)


@pytest.mark.parametrize("method", METHODS)
def test_safety_and_new_position_singularity(method):
    with pytest.raises(TypeError):
        method(None, 1)
    with pytest.raises(ValueError, match="coincident"):
        method(SystemState([1, 1], np.zeros((2, 3)), np.zeros((2, 3))), 1)
    # G=1 SI test configuration makes the collision at r_new=0 exactly represented.
    with pytest.raises(ValueError, match="coincident"):
        method(SystemState([8, 8], [[-1, 0, 0], [1, 0, 0]], np.zeros((2, 3))),
               1, gravitational_constant=1)
    with pytest.raises(FloatingPointError):
        method(SystemState([1], [[0, 0, 0]], [[1e308, 0, 0]]), 2)
    with pytest.raises(ValueError):
        method(pair(), 1, gravitational_constant=0)


def test_benchmark_energy_diagnostic_against_scalar_values():
    from pathlib import Path
    import runpy
    from nbody.simulation import SimulationResult
    namespace = runpy.run_path(str(Path(__file__).parents[1]/"experiments"/"validate_verlet.py"))
    first = SystemState([1e10, 2e10], [[0, 0, 0], [2, 0, 0]], [[0, 1, 0], [0, -0.5, 0]])
    second = SystemState(first.masses, [[0, 0, 0], [4, 0, 0]], first.velocities, time=1)
    actual, _, _ = namespace["conservation_series"](SimulationResult((first, second)))
    kinetic = 0.5*1e10 + 0.5*2e10*0.25
    energy0 = kinetic-G*1e10*2e10/2
    energy1 = kinetic-G*1e10*2e10/4
    np.testing.assert_allclose(actual, [0, (energy1-energy0)/abs(energy0)], rtol=5e-14, atol=0)
