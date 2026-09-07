"""Validated snapshots of a Newtonian system; no force law or integrator."""

from dataclasses import dataclass
from numbers import Real

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _finite_real(value: Real, name: str) -> float:
    """Normalize a real scalar without accepting booleans or numeric strings."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real scalar")
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be representable as finite float64") from exc
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _array(value: ArrayLike, name: str) -> NDArray[np.float64]:
    """Take an owned float64 copy, rejecting non-real and nonfinite data."""
    raw = np.asarray(value)
    if raw.dtype.kind not in "iuf":
        raise TypeError(f"{name} must contain real numbers")
    with np.errstate(over="ignore", invalid="ignore"):
        result = np.array(raw, dtype=np.float64, order="C", copy=True)
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain only finite float64 values")
    return result


@dataclass(frozen=True, eq=False)
class SystemState:
    """Owned, read-only snapshot in SI units.

    masses: shape (N,), strictly positive kilograms, N >= 1.
    positions: shape (N, 3), meters in a shared Cartesian reference frame.
    velocities: shape (N, 3), meters/second in that same frame.
    time: finite seconds relative to an arbitrary epoch (may be negative).

    Inputs are copied; callers cannot change this snapshot through input arrays.
    NumPy write protection prevents accidental edits, not deliberate tampering.
    Create a new state for an update. Coincident positions are representable:
    singularity checks belong to the gravity engine, not the data container.
    """

    masses: ArrayLike
    positions: ArrayLike
    velocities: ArrayLike
    time: float = 0.0

    def __post_init__(self) -> None:
        masses = _array(self.masses, "masses")
        positions = _array(self.positions, "positions")
        velocities = _array(self.velocities, "velocities")
        if masses.ndim != 1 or masses.size == 0:
            raise ValueError("masses must have shape (N,) with N >= 1")
        if np.any(masses <= 0):
            raise ValueError("masses must be strictly positive")
        expected = (masses.size, 3)
        if positions.shape != expected or velocities.shape != expected:
            raise ValueError(f"positions and velocities must have shape {expected}")
        for name, value in (
            ("masses", masses), ("positions", positions), ("velocities", velocities)
        ):
            value.setflags(write=False)
            object.__setattr__(self, name, value)
        object.__setattr__(self, "time", _finite_real(self.time, "time"))

    @property
    def n_bodies(self) -> int:
        """Number of bodies; derived from masses so it cannot become stale."""
        return len(self.masses)