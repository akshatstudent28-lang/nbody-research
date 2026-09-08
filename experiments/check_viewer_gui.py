"""Exercise the native GUI event loop and save an executable verification report."""

import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from show_simulation import load_system, simulate
from nbody.visualization import SimulationViewer


def main():
    data = load_system()
    data["num_steps"] = 100
    viewer = SimulationViewer(simulate(data), labels=data["labels"])
    report = {"backend": matplotlib.get_backend(), "checks": {}}
    errors = []

    def finish():
        try:
            report["checks"]["native_timer_advanced_frames"] = viewer.index > 0
            viewer.toggle_play()
            report["checks"]["pause"] = not viewer.playing
            viewer.timeline.set_val(50)
            viewer.method_control.set_active(3)
            report["checks"]["scrub_and_method_switch"] = viewer.index == 50 and viewer.method == "Forward Euler"
            viewer.trail_control.set_active(0)
            report["checks"]["hide_trails"] = all(not t.get_visible() for t in viewer.trails)
            viewer.replay()
            report["checks"]["replay"] = viewer.index == 0 and viewer.playing
            viewer.seek(100)
            viewer.figure.canvas.draw()
            report["checks"]["final_frame"] = viewer.index == 100 and not viewer.playing
        except Exception as exc:
            errors.append(repr(exc))
        finally:
            report["errors"] = errors
            report["passed"] = bool(report["checks"]) and all(report["checks"].values()) and not errors
            Path("docs/part5-gui-check.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
            print(json.dumps(report, indent=2), flush=True)
            plt.close(viewer.figure)

    viewer.figure.canvas.manager.window.after(1200, finish)
    viewer.show()
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    sys.exit(main())
