"""Compare exported viewer data with the saved Part 4 analytical benchmark."""

import json
from pathlib import Path

import numpy as np


def main():
    with np.load("docs/part4-viewer-history.npz", allow_pickle=False) as arrays:
        metadata = json.loads(str(arrays["metadata_json"]))
        config = metadata["configuration"]
        initial = np.asarray(config["positions_m"])
        separation = np.linalg.norm(initial[1]-initial[0])
        omega = np.sqrt(config["G_m3_kg_s2"]*sum(config["masses_kg"])/separation**3)
        angle = omega*arrays["times_s"]
        exact = separation*np.column_stack((np.cos(angle), np.sin(angle), np.zeros_like(angle)))
        reference = json.loads(Path("docs/part4-validation.json").read_text())
        measured, checks = {}, {}
        for method in ("forward_euler", "euler_cromer"):
            positions = arrays[method+"_positions_m"]
            error = float(np.linalg.norm(positions[:, 1]-positions[:, 0]-exact, axis=1).max()/separation)
            expected = next(run["max_relative_position_error"] for run in reference["runs"]
                            if run["integrator"] == method and run["num_steps"] == 2000)
            measured[method] = error
            checks[method] = bool(np.isclose(error, expected, rtol=5e-14, atol=0))
    report = {"exported_history_max_relative_errors": measured,
              "tolerance": {"rtol": 5e-14, "atol": 0}, "checks": checks,
              "passed": all(checks.values())}
    rendered = json.dumps(report, indent=2)
    Path("docs/part4-export-check.json").write_text(rendered+"\n", encoding="utf-8")
    print(rendered)
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
