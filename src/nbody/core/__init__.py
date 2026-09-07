"""State and configuration shared by future simulation components."""

from .config import SimulationConfig
from .state import SystemState

__all__ = ["SimulationConfig", "SystemState"]