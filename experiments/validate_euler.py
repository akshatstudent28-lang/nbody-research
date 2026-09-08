"""Part 4 circular two-body benchmark; no plotting or general diagnostics API."""

import argparse
from functools import partial
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np

from nbody.constants import G
from nbody.core import SimulationConfig, SystemState
from nbody.integrators import euler_cromer, forward_euler
from nbody.simulation import run_simulation


def run_experiment():
    # Synthetic SI system, both masses move; no fixed central-body approximation.
    masses = np.array([1e20, 2e20])
    separation = 1e6
    fractions = masses / masses.sum()
    omega = np.sqrt(G * masses.sum() / separation**3)
    period = 2 * np.pi / omega
    initial = SystemState(masses,
        [[-fractions[1]*separation, 0, 0], [fractions[0]*separation, 0, 0]],
        [[0, -fractions[1]*separation*omega, 0],
         [0, fractions[0]*separation*omega, 0]])
    report = {
        "scope": "Part 4: circular two-body motion over one analytical period",
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
            **{name: importlib.metadata.version(name) for name in ("numpy", "pytest", "nbody-research")}},
        "configuration": {"G_m3_kg_s2": G, "body_count": 2,
            "masses_kg": masses.tolist(), "positions_m": initial.positions.tolist(),
            "velocities_m_s": initial.velocities.tolist(), "initial_time_s": 0,
            "separation_m": separation, "period_s": float(period),
            "steps_per_period": [1000, 2000], "duration_periods": 1,
            "seed": None, "reference_frame": "initial center of mass, Cartesian SI",
            "softening": None},
        "runs": [],
        "criteria": {"fine_max_relative_position_error_below": 0.2,
            "refinement_reduces_max_position_error": True,
            "rationale": "coarse Part 4 smoke benchmark, not precision orbital certification"},
    }
    for method in (forward_euler, euler_cromer):
        errors = []
        for steps in (1000, 2000):
            dt = period / steps
            result = run_simulation(initial, SimulationConfig(dt, steps),
                partial(method, gravitational_constant=G))
            times = np.array([s.time for s in result.states])
            positions = np.stack([s.positions for s in result.states])
            relative = positions[:, 1] - positions[:, 0]
            angles = omega * times
            exact = separation * np.column_stack((np.cos(angles), np.sin(angles), np.zeros_like(angles)))
            normalized_error = np.linalg.norm(relative - exact, axis=1) / separation
            radius_error = np.abs(np.linalg.norm(relative, axis=1) / separation - 1)
            max_error = float(normalized_error.max())
            errors.append(max_error)
            report["runs"].append({"integrator": method.__name__, "dt_s": float(dt),
                "num_steps": steps, "duration_s": float(times[-1]),
                "recorded_states": len(times),
                "max_relative_position_error": max_error,
                "final_relative_position_error": float(normalized_error[-1]),
                "max_relative_separation_error": float(radius_error.max())})
        report.setdefault("checks", {})[method.__name__] = bool(errors[1] < errors[0] and errors[1] < 0.2)
    report["passed"] = all(report["checks"].values())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run_experiment()
    rendered = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
