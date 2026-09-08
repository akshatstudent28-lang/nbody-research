"""Exercise the native GUI event loop and save an executable verification report."""

import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from mpl_toolkits.mplot3d import proj3d

from show_simulation import load_system, simulate
from nbody.visualization import SimulationViewer


def main():
    data = load_system(Path("experiments/six_body_visual_demo.json"))
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
            viewer.axes.set_xlim(-1, 1)
            viewer.axes.view_init(70, 125)
            viewer.reset_button._observers.process("clicked", None)
            report["checks"]["reset_camera"] = (viewer.axes.get_xlim() == viewer._initial_limits[0] and
                (viewer.axes.elev, viewer.axes.azim, viewer.axes.roll) == viewer._initial_angles)
            viewer.figure.canvas.draw()
            point = viewer.histories[viewer.method].states[50].positions[1]
            x, y, _ = proj3d.proj_transform(*point, viewer.axes.get_proj())
            pixel = viewer.axes.transData.transform((x, y))
            event = MouseEvent("button_press_event", viewer.figure.canvas, *pixel, button=1)
            viewer.figure.canvas.callbacks.process("button_press_event", event)
            report["checks"]["native_body_pick"] = viewer.selected_body == 1
            dropdown = viewer.body_dropdown
            for kind in ("button_press_event", "button_release_event"):
                pixel = dropdown.button.ax.transAxes.transform((0.5, 0.5))
                viewer.figure.canvas.callbacks.process(kind, MouseEvent(kind, viewer.figure.canvas, *pixel, button=1))
            report["checks"]["dropdown_opens"] = dropdown.open
            pixel = dropdown.axes.transData.transform((0.4, 2.5))
            for kind in ("button_press_event", "button_release_event"):
                viewer.figure.canvas.callbacks.process(kind, MouseEvent(kind, viewer.figure.canvas, *pixel, button=1))
            report["checks"]["dropdown_selects_sixth_body"] = viewer.selected_body == 5 and not dropdown.open
            report["checks"]["live_properties"] = "Companion E" in viewer.body_info.get_text() and "a [m/s^2]" in viewer.body_info.get_text()
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
            Path("docs/viewer-controls-gui-check.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
            print(json.dumps(report, indent=2), flush=True)
            plt.close(viewer.figure)

    viewer.figure.canvas.manager.window.after(1200, finish)
    viewer.show()
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    sys.exit(main())
