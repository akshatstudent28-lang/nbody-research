"""Run gravity and open the N-body viewer. Use --help for custom systems."""

import argparse
from functools import partial
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np

from nbody.constants import G
from nbody.core import SimulationConfig, SystemState
from nbody.core.state import _finite_real
from nbody.integrators import euler_cromer, forward_euler, velocity_verlet, leapfrog
from nbody.simulation import run_simulation

METHODS = {"Velocity Verlet": velocity_verlet, "Leapfrog (KDK)": leapfrog,
           "Euler-Cromer": euler_cromer, "Forward Euler": forward_euler}


def load_system(path=None):
    """Return explicit SI configuration; custom N is determined by masses."""
    if path is None:
        masses = np.array([1e20, 2e20])
        separation = 1e6
        omega = np.sqrt(G * masses.sum() / separation**3)
        fractions = masses/masses.sum()
        return {"title": "Two bodies, one gravitational system",
            "reference_frame": "Initial center-of-mass frame",
            "labels": ["Body A", "Body B"], "masses_kg": masses.tolist(),
            "positions_m": [[-fractions[1]*separation, 0, 0], [fractions[0]*separation, 0, 0]],
            "velocities_m_s": [[0, -fractions[1]*separation*omega, 0], [0, fractions[0]*separation*omega, 0]],
            "initial_time_s": 0.0, "dt_s": float(2*np.pi/omega/2000),
            "num_steps": 2000, "G_m3_kg_s2": G}
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("system JSON must be an object")
    required = {"masses_kg", "positions_m", "velocities_m_s", "dt_s", "num_steps"}
    allowed = required | {"title", "reference_frame", "labels", "initial_time_s", "G_m3_kg_s2"}
    if required - data.keys():
        raise ValueError(f"missing configuration keys: {sorted(required-data.keys())}")
    if data.keys() - allowed:
        raise ValueError(f"unknown configuration keys: {sorted(data.keys()-allowed)}")
    return {"title": "Custom N-body simulation", "reference_frame": "Input inertial frame",
            "initial_time_s": 0.0, "G_m3_kg_s2": G, **data}


def simulate(data):
    """Use exactly the same initial conditions and clock for every method."""
    state = SystemState(data["masses_kg"], data["positions_m"], data["velocities_m_s"], data["initial_time_s"])
    config = SimulationConfig(data["dt_s"], data["num_steps"])
    constant = _finite_real(data["G_m3_kg_s2"], "G_m3_kg_s2")
    if constant <= 0:
        raise ValueError("G_m3_kg_s2 must be positive")
    for key in ("title", "reference_frame"):
        if not isinstance(data[key], str) or not data[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    labels = data.get("labels")
    if labels is not None and (not isinstance(labels, list) or len(labels) != state.n_bodies or
                              any(not isinstance(label, str) or not label.strip() for label in labels)):
        raise ValueError("labels must contain one nonempty name per body")
    return {name: run_simulation(state, config, partial(method, gravitational_constant=data["G_m3_kg_s2"]))
            for name, method in METHODS.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="JSON with SI masses, positions, velocities, dt, and steps")
    parser.add_argument("--view", choices=["3d", "xy", "xz", "yz"], default="3d")
    parser.add_argument("--steps", type=int, help="override number of integration steps (changes duration)")
    parser.add_argument("--dt", type=float, help="override physics timestep in seconds (changes duration)")
    parser.add_argument("--snapshot", type=Path, help="render a PNG without opening a window")
    parser.add_argument("--frame", type=int, help="snapshot frame; default is final recorded state")
    parser.add_argument("--save-history", type=Path, help="save all full histories and configuration to .npz")
    args = parser.parse_args()
    if args.snapshot:
        import matplotlib
        matplotlib.use("Agg")
    from nbody.visualization import SimulationViewer
    data = load_system(args.config)
    if args.steps is not None:
        data["num_steps"] = args.steps
    if args.dt is not None:
        data["dt_s"] = args.dt
    print(f"Computing {len(data['masses_kg'])} bodies, {data['num_steps']} steps per method...", flush=True)
    histories = simulate(data)
    viewer = SimulationViewer(histories, labels=data.get("labels"), view=args.view,
                              title=data["title"], reference_frame=data["reference_frame"],
                              gravitational_constant=data["G_m3_kg_s2"])
    if args.save_history:
        metadata = {"configuration": data, "methods": list(histories), "python": platform.python_version(),
                    "platform": platform.platform(),
                    "versions": {name: importlib.metadata.version(name) for name in ("numpy", "matplotlib", "nbody-research")}}
        arrays = {"metadata_json": np.array(json.dumps(metadata)),
                  "times_s": viewer.times, "masses_kg": histories[viewer.method].states[0].masses}
        for name, result in histories.items():
            key = name.lower().replace("-", "_").replace(" ", "_").replace("(", "").replace(")", "")
            arrays[f"{key}_positions_m"] = viewer.positions[name]
            arrays[f"{key}_velocities_m_s"] = np.stack([s.velocities for s in result.states])
        with args.save_history.open("wb") as stream:
            np.savez_compressed(stream, **arrays)
        print(f"Saved full histories: {args.save_history}")
    if args.snapshot:
        frame = len(viewer.times)-1 if args.frame is None else args.frame
        if not 0 <= frame < len(viewer.times):
            parser.error("snapshot frame is outside recorded history")
        viewer.seek(frame)
        viewer.figure.savefig(args.snapshot, dpi=140, facecolor=viewer.figure.get_facecolor())
        print(f"Saved snapshot: {args.snapshot}")
        import matplotlib.pyplot as plt
        plt.close(viewer.figure)
    else:
        print("Opening viewer. Use Pause, Replay, Frame, Speed, and the method selector.", flush=True)
        viewer.show()


if __name__ == "__main__":
    main()
