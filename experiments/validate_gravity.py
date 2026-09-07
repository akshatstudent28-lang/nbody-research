"""Reproduce Part 2 static gravity validation; no simulation or orbit claims.

Run: python experiments/validate_gravity.py --output docs/part2-validation.json
"""
import argparse
from decimal import Decimal, localcontext
from importlib.metadata import version
import json
from pathlib import Path
import platform

import numpy as np

from nbody.constants import G
from nbody.physics import accelerations, center_of_mass, pairwise_force


def decimal_reference(masses, positions):
    """Ordered-pair, 60-digit calculation independent of the production kernel."""
    with localcontext() as ctx:
        ctx.prec = 60
        m = [Decimal(str(value)) for value in masses]
        p = [[Decimal(str(value)) for value in row] for row in positions]
        result = []
        for i in range(len(m)):
            row = [Decimal(0)] * 3
            for j in range(len(m)):
                if i == j:
                    continue
                d = [p[j][k] - p[i][k] for k in range(3)]
                r = sum(x*x for x in d).sqrt()
                for k in range(3):
                    row[k] += Decimal(str(G)) * m[j] * d[k] / r**3
            result.append([float(x) for x in row])
        return np.array(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    seed = 20260907
    rng = np.random.default_rng(seed)
    masses = rng.integers(1, 20, size=8)
    positions = rng.integers(-100, 100, size=(8, 3))
    a = accelerations(masses, positions)
    reference = decimal_reference(masses, positions)
    max_error = float(np.max(np.abs(a - reference)))
    relative_error = max_error / float(np.max(np.abs(reference)))
    forces = masses[:, None] * a
    force_residual = float(
        np.linalg.norm(forces.sum(axis=0)) / np.linalg.norm(forces, axis=1).sum()
    )
    angle = 0.37
    c, s = np.cos(angle), np.sin(angle)
    rotation = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    scale = float(np.max(np.abs(a)))
    rotation_error = float(np.max(np.abs(
        accelerations(masses, positions @ rotation.T) - a @ rotation.T
    ))) / scale
    translation_error = float(np.max(np.abs(
        accelerations(masses, positions + [8, -4, 2]) - a
    ))) / scale
    force = pairwise_force(2, 3, [0, 0, 0], [3, 4, 0])
    # G * (2 kg) * (3 kg) * (3, 4, 0) m / (5 m)^3.
    expected_force = np.array([9.610992e-12, 1.2814656e-11, 0.0])
    pair_relative_error = float(np.max(np.abs(force - expected_force))) / float(
        np.max(np.abs(expected_force))
    )
    center = center_of_mass([1, 3], [[0, 0, 0], [4, 8, -4]])
    center_error = float(np.max(np.abs(center - [3, 6, -3])))
    checks = {
        "decimal_reference": relative_error <= 5e-14,
        "internal_force_balance": force_residual <= 5e-15,
        "rotation_covariance": rotation_error <= 5e-14,
        "translation_invariance": translation_error <= 5e-14,
        "analytic_pair_force": pair_relative_error <= 5e-14,
        "analytic_center_of_mass": center_error <= 1e-14,
    }
    report = {
        "scope": "instantaneous Newtonian gravity; no time integration",
        "environment": {
            "python": platform.python_version(), "platform": platform.platform(),
            "numpy": np.__version__, "pytest": version("pytest"),
            "package": version("nbody-research"),
        },
        "configuration": {
            "G_m3_kg_s2": G, "seed": seed, "rng": "NumPy default_rng",
            "body_count": 8, "masses_kg": masses.tolist(),
            "positions_m": positions.tolist(),
            "reference_decimal_precision": 60,
            "rotation_angle_rad": angle, "translation_m": [8, -4, 2],
            "velocities_integrator_dt_duration": "not applicable to static evaluation",
        },
        "computed_accelerations_m_s2": a.tolist(),
        "decimal_reference_accelerations_m_s2": reference.tolist(),
        "metrics": {
            "max_absolute_acceleration_error_m_s2": max_error,
            "max_error_over_max_reference_acceleration": relative_error,
            "net_force_norm_over_sum_force_norms": force_residual,
            "rotation_error_over_max_acceleration": rotation_error,
            "translation_error_over_max_acceleration": translation_error,
            "analytic_pair_force_N": force.tolist(),
            "expected_pair_force_N": expected_force.tolist(),
            "pair_force_normalized_error": pair_relative_error,
            "analytic_center_of_mass_m": center.tolist(),
            "center_max_absolute_error_m": center_error,
        },
        "tolerances": {
            "normalized_acceleration_and_force_error": 5e-14,
            "normalized_internal_force_residual": 5e-15,
            "center_absolute_error_m": 1e-14,
            "rationale": "roundoff allowance for small float64 static cases",
        },
        "checks": checks, "passed": all(checks.values()),
    }
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
