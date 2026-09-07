"""Direct Newtonian point-mass gravity in SI units.

No softening, cutoffs, collisions, or time integration. Coordinates are Cartesian.
Public functions copy and validate inputs; they never mutate caller arrays.
"""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from nbody.constants import G
from nbody.core.state import _array, _finite_real


def _inputs(
    masses: ArrayLike, positions: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    masses = _array(masses, "masses")
    positions = _array(positions, "positions")
    if masses.ndim != 1 or masses.size == 0 or np.any(masses <= 0):
        raise ValueError("masses must have shape (N,), N >= 1, and be positive")
    if positions.shape != (masses.size, 3):
        raise ValueError("positions must have shape (N, 3) matching masses")
    return masses, positions


def _constant(value: float) -> float:
    value = _finite_real(value, "gravitational_constant")
    if value <= 0:
        raise ValueError("gravitational_constant must be positive")
    return value


def _pair(
    position_i: NDArray[np.float64],
    position_j: NDArray[np.float64],
    i: int,
    j: int,
) -> tuple[NDArray[np.float64], np.float64]:
    displacement = position_j - position_i
    # hypot avoids the needless overflow/underflow of squaring each component.
    distance = np.hypot.reduce(displacement)
    if distance == 0:
        raise ValueError(f"coincident positions for bodies {i} and {j}")
    return displacement / distance, distance


def pairwise_force(
    mass_i: float,
    mass_j: float,
    position_i: ArrayLike,
    position_j: ArrayLike,
    *,
    gravitational_constant: float = G,
) -> NDArray[np.float64]:
    """Force on i due to j, shape (3,), in newtons; force on j is its negative.

    Masses must be positive finite real scalars; positions have shape (3,).
    Raises ValueError for coincidence/invalid values, TypeError for unsupported
    types, and FloatingPointError for floating-point range failures.
    Takes O(1) time and auxiliary memory.
    """
    mass_i = _finite_real(mass_i, "mass_i")
    mass_j = _finite_real(mass_j, "mass_j")
    masses, positions = _inputs([mass_i, mass_j], [position_i, position_j])
    g = _constant(gravitational_constant)
    with np.errstate(over="raise", divide="raise", invalid="raise", under="raise"):
        direction, distance = _pair(positions[0], positions[1], 0, 1)
        return ((g * masses[1] / distance) / distance * masses[0]) * direction


def accelerations(
    masses: ArrayLike,
    positions: ArrayLike,
    *,
    gravitational_constant: float = G,
) -> NDArray[np.float64]:
    """Return acceleration (N, 3) in m/s^2 for finite positive point masses.

    For every i < j, add G*m_j/r^2 times the i-to-j unit vector to a_i,
    and subtract G*m_i/r^2 times that vector from a_j. Each separation
    is evaluated once. N=1 returns zero; self-interaction is never evaluated.

    Time: O(N^2), specifically N*(N-1)/2 pair evaluations.
    Memory: O(N), including validated copies and output; no N-by-N tensor.

    Coincident bodies raise ValueError with their indices. Arithmetic overflow,
    underflow, division by zero, or invalid arithmetic raises FloatingPointError.
    Strict range checks may reject extreme inputs even when a rearranged formula
    could succeed. They are not a guarantee against cancellation/roundoff.
    """
    masses, positions = _inputs(masses, positions)
    g = _constant(gravitational_constant)
    result = np.zeros_like(positions)
    with np.errstate(over="raise", divide="raise", invalid="raise", under="raise"):
        for i in range(len(masses) - 1):
            for j in range(i + 1, len(masses)):
                direction, distance = _pair(positions[i], positions[j], i, j)
                result[i] += ((g * masses[j] / distance) / distance) * direction
                result[j] -= ((g * masses[i] / distance) / distance) * direction
    return result


def center_of_mass(
    masses: ArrayLike, positions: ArrayLike
) -> NDArray[np.float64]:
    """Mass-weighted position (3,) in meters; O(N) time and auxiliary memory.

    Normalize by the largest mass before summation to avoid overflowing the
    total mass or raw mass-position products. This is algebraically identical
    to sum(m_i*r_i)/sum(m_i), within floating-point roundoff.
    Coincident positions are valid here. Strict arithmetic range checks apply.
    """
    masses, positions = _inputs(masses, positions)
    with np.errstate(over="raise", divide="raise", invalid="raise", under="raise"):
        scaled = masses / np.max(masses)
        weights = scaled / np.sum(scaled)
        return np.sum(weights[:, None] * positions, axis=0)
