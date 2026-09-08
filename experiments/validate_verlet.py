"""Part 5: second-order refinement and fixed-step conservation experiments.

Diagnostics are local to this benchmark; the general diagnostic API is Part 7.
"""

from functools import partial
import importlib.metadata
import json
from pathlib import Path
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from nbody.constants import G
from nbody.core import SimulationConfig, SystemState
from nbody.integrators import forward_euler, euler_cromer, velocity_verlet, leapfrog
from nbody.simulation import run_simulation

METHODS = {"Forward Euler": forward_euler, "Euler-Cromer": euler_cromer,
           "Velocity Verlet": velocity_verlet, "Leapfrog (KDK)": leapfrog}


def initial_conditions(eccentricity=0.0):
    masses = np.array([1e20, 2e20])
    semimajor = 1e6
    mu = G*masses.sum()
    period = 2*np.pi*np.sqrt(semimajor**3/mu)
    separation = semimajor*(1-eccentricity)
    relative_speed = np.sqrt(mu*(1+eccentricity)/(semimajor*(1-eccentricity)))
    fraction = masses/masses.sum()
    state = SystemState(masses, [[-fraction[1]*separation, 0, 0], [fraction[0]*separation, 0, 0]],
                        [[0, -fraction[1]*relative_speed, 0], [0, fraction[0]*relative_speed, 0]])
    return state, period, semimajor


def conservation_series(result):
    masses = result.states[0].masses
    positions = np.stack([s.positions for s in result.states])
    velocities = np.stack([s.velocities for s in result.states])
    separation = np.linalg.norm(positions[:, 1]-positions[:, 0], axis=1)
    energy = 0.5*np.sum(masses[None, :, None]*velocities**2, axis=(1, 2))-G*masses.prod()/separation
    momentum = np.sum(masses[None, :, None]*velocities, axis=1)
    angular = np.sum(np.cross(positions, masses[None, :, None]*velocities), axis=1)
    # These fixtures have nonzero energy/angular momentum and speed scales.
    energy_error = (energy-energy[0])/abs(energy[0])
    angular_error = np.linalg.norm(angular-angular[0], axis=1)/np.linalg.norm(angular[0])
    momentum_scale = np.sum(masses*np.linalg.norm(velocities[0], axis=1))
    momentum_error = np.linalg.norm(momentum-momentum[0], axis=1)/momentum_scale
    return energy_error, angular_error, momentum_error


def main():
    report = {"scope": "Part 5 fixed-step methods; no chaos claim",
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
            **{name: importlib.metadata.version(name) for name in ("numpy", "matplotlib", "pytest", "nbody-research")}},
        "tolerances": {"circular_refinement_ratio_range": [3.5, 4.5],
            "fine_max_position_error_over_separation": 1e-3,
            "new_methods_max_relative_energy_error": 2e-3,
            "new_methods_max_relative_angular_momentum_error": 5e-12,
            "all_methods_normalized_momentum_change": 5e-12,
            "last_five_orbit_energy_envelope_factor": 1.2,
            "envelope_absolute_roundoff_allowance": 1e-12,
            "rationale": "predeclared checks for these smooth, well-resolved fixtures, not universal guarantees"},
        "refinement": [], "conservation": [], "checks": {}}
    circular, period, radius = initial_conditions()
    report["circular_configuration"] = {"masses_kg": circular.masses.tolist(),
        "positions_m": circular.positions.tolist(), "velocities_m_s": circular.velocities.tolist(),
        "G_m3_kg_s2": G, "initial_time_s": 0, "duration_s": float(period),
        "steps_per_period": [200, 400, 800], "body_count": 2, "seed": None}
    for method in (velocity_verlet, leapfrog):
        errors = []
        for steps in (200, 400, 800):
            result = run_simulation(circular, SimulationConfig(period/steps, steps), method)
            times = np.array([s.time for s in result.states])
            positions = np.stack([s.positions for s in result.states])
            angle = 2*np.pi*times/period
            exact = radius*np.column_stack((np.cos(angle), np.sin(angle), np.zeros_like(angle)))
            error = float(np.linalg.norm(positions[:, 1]-positions[:, 0]-exact, axis=1).max()/radius)
            errors.append(error)
            report["refinement"].append({"method": method.__name__, "num_steps": steps,
                "dt_s": float(period/steps), "max_position_error_over_separation": error})
        ratios = np.array(errors[:-1])/errors[1:]
        report["checks"][method.__name__+"_second_order"] = bool(np.all((ratios > 3.5) & (ratios < 4.5)) and errors[-1] < 1e-3)
        report.setdefault("observed_refinement", {})[method.__name__] = {
            "error_ratios": ratios.tolist(), "orders_log2_ratio": np.log2(ratios).tolist()}
    initial, period, semimajor = initial_conditions(0.3)
    steps_per_period, periods = 400, 20
    steps = steps_per_period*periods
    report["conservation_configuration"] = {"masses_kg": initial.masses.tolist(),
        "positions_m": initial.positions.tolist(), "velocities_m_s": initial.velocities.tolist(),
        "G_m3_kg_s2": G, "dt_s": float(period/steps_per_period), "num_steps": steps,
        "initial_time_s": 0, "duration_s": float(period*periods), "periods": periods,
        "eccentricity": 0.3, "semimajor_axis_m": semimajor, "body_count": 2, "seed": None,
        "reference_frame": "initial center-of-mass frame", "softening": None}
    raw = {}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for name, method in METHODS.items():
        result = run_simulation(initial, SimulationConfig(period/steps_per_period, steps), partial(method, gravitational_constant=G))
        energy, angular, momentum = conservation_series(result)
        time_in_periods = np.array([s.time for s in result.states])/period
        first_envelope = float(np.max(np.abs(energy[:5*steps_per_period+1])))
        last_envelope = float(np.max(np.abs(energy[-5*steps_per_period:])))
        values = {"method": name, "max_relative_energy_error": float(np.max(np.abs(energy))),
            "final_signed_relative_energy_error": float(energy[-1]),
            "max_relative_angular_momentum_error": float(angular.max()),
            "max_normalized_momentum_change": float(momentum.max()),
            "first_five_orbit_energy_envelope": first_envelope,
            "last_five_orbit_energy_envelope": last_envelope}
        report["conservation"].append(values)
        report["checks"][method.__name__+"_momentum"] = bool(momentum.max() < 5e-12)
        if method in (velocity_verlet, leapfrog):
            report["checks"][method.__name__+"_conservation"] = bool(
                np.max(np.abs(energy)) < 2e-3 and angular.max() < 5e-12 and
                last_envelope <= 1.2*first_envelope+1e-12)
        raw[method.__name__+"_energy_error"] = energy
        raw[method.__name__+"_angular_momentum_error"] = angular
        raw[method.__name__+"_momentum_change"] = momentum
        mask = np.abs(energy) > 0
        axes[0].semilogy(time_in_periods[mask], np.abs(energy[mask]), label=name,
                         linestyle="--" if method is leapfrog else "-", alpha=0.8)
        if method in (velocity_verlet, leapfrog):
            axes[1].plot(time_in_periods, energy, label=name,
                         linestyle="--" if method is leapfrog else "-", alpha=0.8)
    raw["time_in_periods"] = time_in_periods
    raw["metadata_json"] = np.array(json.dumps(report["conservation_configuration"]))
    np.savez_compressed("docs/part5-conservation-series.npz", **raw)
    axes[0].set(title="All four implementations", xlabel="Time / analytical orbital period", ylabel="|E(t) - E(0)| / |E(0)|")
    axes[1].set(title="Verlet and KDK: equivalent formulations", xlabel="Time / analytical orbital period", ylabel="[E(t) - E(0)] / |E(0)|")
    for axis in axes:
        axis.legend(fontsize=8)
        axis.grid(alpha=0.25)
    fig.suptitle("Fixed-step two-body energy error | e = 0.3 | 400 steps per orbit")
    fig.savefig("docs/part5-conservation.png", dpi=150)
    plt.close(fig)
    report["passed"] = all(report["checks"].values())
    Path("docs/part5-validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
