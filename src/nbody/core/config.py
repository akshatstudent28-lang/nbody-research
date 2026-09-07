"""Minimal fixed-step run settings; simulation execution comes in Part 3."""

from dataclasses import dataclass
from numbers import Integral

import numpy as np

from .state import _finite_real


@dataclass(frozen=True)
class SimulationConfig:
    """Positive timestep in seconds and nonnegative integer number of steps.

    duration is derived, avoiding inconsistent duration/step-count inputs.
    Zero steps represents an initial-state-only run.
    """

    dt: float
    num_steps: int

    def __post_init__(self) -> None:
        dt = _finite_real(self.dt, "dt")
        if dt <= 0:
            raise ValueError("dt must be positive")
        if isinstance(self.num_steps, (bool, np.bool_)) or not isinstance(
            self.num_steps, Integral
        ):
            raise TypeError("num_steps must be an integer")
        steps = int(self.num_steps)
        if steps < 0:
            raise ValueError("num_steps must be nonnegative")
        try:
            duration = dt * steps
        except OverflowError as exc:
            raise ValueError("duration must be finite") from exc
        if not np.isfinite(duration):
            raise ValueError("duration must be finite")
        object.__setattr__(self, "dt", dt)
        object.__setattr__(self, "num_steps", steps)

    @property
    def duration(self) -> float:
        """Requested elapsed time in seconds, subject to floating-point rounding."""
        return self.dt * self.num_steps