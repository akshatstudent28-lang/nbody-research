"""First-order Newtonian integrators with fixed positive timesteps, in SI units."""

import numpy as np

from nbody.constants import G
from nbody.core import SystemState
from nbody.core.state import _finite_real
from nbody.physics import accelerations


def _advance(state, dt, gravitational_constant, *, use_new_velocity):
    if not isinstance(state, SystemState):
        raise TypeError("state must be a SystemState")
    dt = _finite_real(dt, "dt")
    if dt <= 0:
        raise ValueError("dt must be positive")
    # The simulation runner owns timestamps, including for nonbinary timesteps.
    # Standalone updates retain the input epoch, following that callback contract.
    with np.errstate(over="raise", invalid="raise", divide="raise", under="raise"):
        acceleration = accelerations(
            state.masses, state.positions,
            gravitational_constant=gravitational_constant,
        )
        velocities = state.velocities + dt * acceleration
        drift_velocity = velocities if use_new_velocity else state.velocities
        positions = state.positions + dt * drift_velocity
    return SystemState(state.masses, positions, velocities, state.time)


def forward_euler(
    state: SystemState, dt: float, *, gravitational_constant: float = G,
) -> SystemState:
    """Use old velocity for position and old-position acceleration for velocity.

    r_new = r + dt*v; v_new = v + dt*a(r). First-order global accuracy
    for smooth solutions on a fixed finite interval. One O(N^2) gravity call,
    O(N) auxiliary storage. Returns an owned state at the unchanged input time;
    use run_simulation to assign times. Inputs are never modified. Invalid dt,
    singular gravity, and floating-point range errors are rejected explicitly.
    """
    return _advance(state, dt, gravitational_constant, use_new_velocity=False)


def euler_cromer(
    state: SystemState, dt: float, *, gravitational_constant: float = G,
) -> SystemState:
    """Kick then drift: v_new = v + dt*a(r); r_new = r + dt*v_new.

    First-order, semi-implicit (symplectic) Euler for this separable Newtonian
    Hamiltonian at fixed dt. No implicit solve is needed. It does not conserve
    energy exactly or guarantee stable motion at arbitrary dt. Same ownership,
    unchanged-time, validation, and complexity contract as forward_euler.
    """
    return _advance(state, dt, gravitational_constant, use_new_velocity=True)
