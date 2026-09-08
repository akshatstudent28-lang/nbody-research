"""Second-order, fixed-step symplectic methods for Newtonian point masses."""

import numpy as np

from nbody.constants import G
from nbody.core import SystemState
from nbody.core.state import _finite_real
from nbody.physics import accelerations


def _validate(state: SystemState, dt: float) -> float:
    if not isinstance(state, SystemState):
        raise TypeError("state must be a SystemState")
    dt = _finite_real(dt, "dt")
    if dt <= 0:
        raise ValueError("dt must be positive")
    return dt


def velocity_verlet(state: SystemState, dt: float, *, gravitational_constant: float = G) -> SystemState:
    """Position update then average-acceleration velocity update, SI units.

    r1 = r0 + dt*v0 + dt^2*a0/2; v1 = v0 + dt*(a0+a1)/2.
    Returns synchronized positions/velocities; retains input time because the
    runner owns the clock. Two gravity evaluations per call, O(N^2) time and
    O(N) auxiliary memory. No cached acceleration or hidden mutable state.
    Positive finite dt only. Singularities/range errors propagate explicitly.
    """
    dt = _validate(state, dt)
    with np.errstate(over="raise", invalid="raise", divide="raise", under="raise"):
        a0 = accelerations(state.masses, state.positions, gravitational_constant=gravitational_constant)
        positions = state.positions + dt*state.velocities + (0.5*dt)*(dt*a0)
        a1 = accelerations(state.masses, positions, gravitational_constant=gravitational_constant)
        velocities = state.velocities + (0.5*dt)*(a0+a1)
    return SystemState(state.masses, positions, velocities, state.time)


def leapfrog(state: SystemState, dt: float, *, gravitational_constant: float = G) -> SystemState:
    """Kick-drift-kick Leapfrog with velocities synchronized at full steps.

    v_half = v0 + dt*a0/2; r1 = r0 + dt*v_half;
    v1 = v_half + dt*a1/2. Equivalent to velocity Verlet in exact arithmetic
    for position-dependent acceleration. Different arithmetic grouping can
    yield roundoff differences. The half-step velocity is local, never stored
    as a full-step velocity. Same safety/time/cost contract as velocity_verlet.
    """
    dt = _validate(state, dt)
    with np.errstate(over="raise", invalid="raise", divide="raise", under="raise"):
        a0 = accelerations(state.masses, state.positions, gravitational_constant=gravitational_constant)
        half_velocity = state.velocities + (0.5*dt)*a0
        positions = state.positions + dt*half_velocity
        a1 = accelerations(state.masses, positions, gravitational_constant=gravitational_constant)
        velocities = half_velocity + (0.5*dt)*a1
    return SystemState(state.masses, positions, velocities, state.time)
