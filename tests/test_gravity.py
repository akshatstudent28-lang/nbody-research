"""Analytical, symmetry, independent-reference, and input-contract checks."""

from decimal import Decimal, localcontext

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from nbody.constants import G
from nbody.core import SystemState
from nbody.physics import accelerations, center_of_mass, pairwise_force

# Small, well-conditioned float64 problems: a few to a few hundred eps.
RTOL = 5e-14
ATOL = 1e-24  # m/s^2 (or N in force checks); not NumPy's loose default


def reference_accelerations(masses, positions):
    """Independent ordered-pair formula, 60-digit Decimal and cubic distance."""
    with localcontext() as context:
        context.prec = 60
        m = [Decimal(str(value)) for value in masses]
        p = [[Decimal(str(value)) for value in row] for row in positions]
        g = Decimal(str(G))
        result = []
        for i in range(len(m)):
            row = [Decimal(0)] * 3
            for j in range(len(m)):
                if i == j:
                    continue
                d = [p[j][k] - p[i][k] for k in range(3)]
                distance = sum(value * value for value in d).sqrt()
                for k in range(3):
                    row[k] += g * m[j] * d[k] / distance**3
            result.append([float(value) for value in row])
    return np.array(result)


def fixture_system():
    return np.array([2., 3., 5., 7.]), np.array([
        [0., 0., 0.], [3., 4., 0.], [-2., 1., 2.], [1., -3., 4.]
    ])


def test_pair_force_and_two_body_analytic():
    # Separation is 5 m; the unit vector is (3/5, 4/5, 0).
    p = [[0, 0, 0], [3, 4, 0]]
    expected = np.array([G * 3 / 25 * 3 / 5, G * 3 / 25 * 4 / 5, 0])
    a = accelerations([2, 3], p)
    assert_allclose(a[0], expected, rtol=RTOL, atol=0)
    assert_allclose(a[1], -expected * 2 / 3, rtol=RTOL, atol=0)
    force = pairwise_force(2, 3, p[0], p[1])
    assert_allclose(force, 2 * expected, rtol=RTOL, atol=0)
    assert_array_equal(pairwise_force(3, 2, p[1], p[0]), -force)


def test_one_body_and_center():
    p = [[3, -4, 5]]
    assert_array_equal(accelerations([2], p), [[0, 0, 0]])
    assert_array_equal(center_of_mass([2], p), p[0])


def test_symmetric_three_body_superposition():
    # On left body: central mass contributes 2G and far mass contributes G/4.
    a = accelerations([1, 2, 1], [[-1, 0, 0], [0, 0, 0], [1, 0, 0]])
    assert_allclose(a, [[2.25 * G, 0, 0], [0, 0, 0], [-2.25 * G, 0, 0]],
                    rtol=RTOL, atol=0)


def test_mass_distance_and_g_scaling():
    m, p = fixture_system()
    a = accelerations(m, p)
    assert_allclose(accelerations(3 * m, p), 3 * a, rtol=RTOL, atol=ATOL)
    assert_allclose(accelerations(m, 2 * p), a / 4, rtol=RTOL, atol=ATOL)
    assert_allclose(accelerations(m, p, gravitational_constant=2 * G),
                    2 * a, rtol=RTOL, atol=ATOL)
    # Changing a target mass changes the other body's acceleration, not its own.
    assert_array_equal(accelerations([2, 3], p[:2])[0],
                       accelerations([20, 3], p[:2])[0])


def test_translation_rotation_and_permutation():
    m, p = fixture_system()
    a = accelerations(m, p)
    assert_allclose(accelerations(m, p + [8, -4, 2]), a, rtol=RTOL, atol=ATOL)
    angle = 0.37
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    assert_allclose(accelerations(m, p @ rotation.T), a @ rotation.T,
                    rtol=RTOL, atol=ATOL)
    order = [3, 1, 0, 2]
    assert_allclose(accelerations(m[order], p[order]), a[order],
                    rtol=RTOL, atol=ATOL)


def test_net_internal_force_residual():
    m, p = fixture_system()
    forces = m[:, None] * accelerations(m, p)
    residual = np.linalg.norm(forces.sum(axis=0)) / np.linalg.norm(forces, axis=1).sum()
    assert residual < 5e-15


@pytest.mark.parametrize("n", [2, 4, 11])
def test_independent_decimal_reference(n):
    rng = np.random.default_rng(20260907 + n)
    # Integer inputs give exactly represented independent starting data.
    masses = rng.integers(1, 20, size=n)
    positions = rng.integers(-100, 100, size=(n, 3))
    expected = reference_accelerations(masses, positions)
    assert_allclose(accelerations(masses, positions), expected,
                    rtol=RTOL, atol=ATOL)


def test_center_analytic_and_covariance():
    m = np.array([1., 3.])
    p = np.array([[0., 0., 0.], [4., 8., -4.]])
    assert_array_equal(center_of_mass(m, p), [3, 6, -3])
    assert_allclose(center_of_mass(m, p + [2, -1, 4]), [5, 5, 1],
                    rtol=0, atol=1e-14)  # meters
    assert_array_equal(center_of_mass(m * 4, p), [3, 6, -3])
    assert_array_equal(center_of_mass(m[::-1], p[::-1]), [3, 6, -3])
    rotation = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
    assert_array_equal(center_of_mass(m, p @ rotation.T), [-6, 3, -3])


def test_center_avoids_raw_mass_overflow():
    assert_array_equal(center_of_mass([1e308, 1e308], [[2, 0, 0], [4, 0, 0]]),
                       [3, 0, 0])


def test_inputs_not_mutated_and_state_integration():
    m, p = fixture_system()
    original_m, original_p = m.copy(), p.copy()
    state = SystemState(m, p, np.zeros_like(p))
    a = accelerations(state.masses, state.positions)
    center_of_mass(m, p)
    pairwise_force(m[0], m[1], p[0], p[1])
    a[:] = 0
    assert_array_equal(m, original_m)
    assert_array_equal(p, original_p)
    assert_array_equal(state.positions, original_p)


@pytest.mark.parametrize("function", [accelerations, center_of_mass])
@pytest.mark.parametrize("m,p,error", [
    ([], [], ValueError), ([0], [[0, 0, 0]], ValueError),
    ([-1], [[0, 0, 0]], ValueError), ([np.nan], [[0, 0, 0]], ValueError),
    ([np.inf], [[0, 0, 0]], ValueError), ([[1]], [[0, 0, 0]], ValueError),
    ([1], [[0, 0]], ValueError), ([1, 2], [[0, 0, 0]], ValueError),
    ([1], [[np.inf, 0, 0]], ValueError),
    ([1], [[np.nan, 0, 0]], ValueError),
    (["1"], [[0, 0, 0]], TypeError), ([True], [[0, 0, 0]], TypeError),
    ([1], [[1j, 0, 0]], TypeError),
])
def test_invalid_inputs(function, m, p, error):
    with pytest.raises(error):
        function(m, p)


@pytest.mark.parametrize("g,error", [
    (0, ValueError), (-1, ValueError), (np.inf, ValueError),
    (np.nan, ValueError), (True, TypeError), ("1", TypeError),
])
def test_invalid_constant(g, error):
    with pytest.raises(error):
        accelerations([1], [[0, 0, 0]], gravitational_constant=g)
    with pytest.raises(error):
        pairwise_force(1, 2, [0, 0, 0], [1, 0, 0], gravitational_constant=g)


@pytest.mark.parametrize("mass,error", [
    (0, ValueError), (-1, ValueError), (np.nan, ValueError),
    (True, TypeError), ("1", TypeError), (1j, TypeError),
])
def test_invalid_pair_mass(mass, error):
    with pytest.raises(error):
        pairwise_force(mass, 2, [0, 0, 0], [1, 0, 0])


def test_coincident_positions_rejected_only_for_gravity():
    p = [[0, 0, 0], [1, 0, 0], [1, 0, 0]]
    with pytest.raises(ValueError, match="bodies 1 and 2"):
        accelerations([1, 2, 3], p)
    with pytest.raises(ValueError, match="coincident"):
        pairwise_force(1, 2, p[1], p[2])
    assert_array_equal(center_of_mass([1, 1], [p[1], p[2]]), [1, 0, 0])


def test_close_nonzero_separation_has_no_floor():
    distance = 1e-100
    a = accelerations([1, 1], [[0, 0, 0], [distance, 0, 0]])
    assert_allclose(a[:, 0], [G * 1e200, -G * 1e200], rtol=RTOL, atol=0)


@pytest.mark.parametrize("positions", [
    [[-1e308, 0, 0], [1e308, 0, 0]],  # displacement overflow
    [[0, 0, 0], [1e-200, 0, 0]],      # acceleration overflow
    [[0, 0, 0], [1e200, 0, 0]],       # acceleration underflow
])
def test_arithmetic_range_failures(positions):
    with pytest.raises(FloatingPointError):
        accelerations([1, 1], positions)
    with pytest.raises(FloatingPointError):
        pairwise_force(1, 1, positions[0], positions[1])


def test_center_mass_ratio_underflow_is_explicit():
    with pytest.raises(FloatingPointError):
        center_of_mass([1e-300, 1e300], [[0, 0, 0], [1, 0, 0]])
