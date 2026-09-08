"""Test rendered coordinates and playback controls without a desktop display."""

from pathlib import Path
import runpy
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from nbody.core import SystemState
from nbody.simulation import SimulationResult
from nbody.visualization import SimulationViewer


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close("all")


def history(n=4, times=(0, 1, 2), offset=0):
    base = np.arange(n*3, dtype=float).reshape(n, 3)
    return SimulationResult(tuple(SystemState(np.arange(1, n+1), base+t*(1+offset),
                                              np.ones((n, 3)), t) for t in times))


@pytest.mark.parametrize("n", [1, 2, 4, 12])
@pytest.mark.parametrize("view", ["xy", "xz", "yz", "3d"])
def test_all_bodies_render_at_recorded_positions(n, view):
    result = history(n)
    viewer = SimulationViewer({"Test": result}, view=view)
    viewer.seek(2)
    viewer.figure.canvas.draw()
    assert len(viewer.markers) == n
    assert len(viewer.trails) == n
    for i, marker in enumerate(viewer.markers):
        actual = np.array(marker.get_data_3d() if view == "3d" else marker.get_data()).ravel()
        np.testing.assert_array_equal(actual, result.states[2].positions[i, list(viewer.dimensions)])
    extents = [np.ptp(viewer.axes.get_xlim()), np.ptp(viewer.axes.get_ylim())]
    if view == "3d":
        extents.append(np.ptp(viewer.axes.get_zlim()))
    np.testing.assert_allclose(extents, extents[0], rtol=1e-14, atol=0)
    assert "t = 2.000 s" in viewer.status.get_text()


def test_controls_methods_and_immutability():
    first, second = history(), history(offset=1)
    viewer = SimulationViewer({"First": first, "Second": second})
    before = first.states[1].positions.copy()
    viewer.play_button._observers.process("clicked", None)
    assert viewer.playing
    viewer.advance_playback(10)
    assert viewer.index == 1
    viewer.speed_control.set_val(2)
    viewer.advance_playback(5)
    assert viewer.index == 2 and not viewer.playing
    viewer.replay_button._observers.process("clicked", None)
    assert viewer.index == 0 and viewer.playing
    viewer.timeline.set_val(1)
    assert viewer.index == 1 and not viewer.playing
    viewer.method_control.set_active(1)
    assert viewer.method == "Second" and viewer.index == 1
    np.testing.assert_array_equal(np.array(viewer.markers[0].get_data_3d()).ravel(), second.states[1].positions[0])
    viewer.trail_control.set_active(0)
    assert all(not trail.get_visible() for trail in viewer.trails)
    viewer._pick(SimpleNamespace(artist=viewer.markers[3]))
    assert "Body 4" in viewer.body_info.get_text()
    np.testing.assert_array_equal(first.states[1].positions, before)
    viewer._close()
    assert not viewer.playing


def test_nonuniform_time_playback_uses_timestamps():
    viewer = SimulationViewer({"Test": history(times=(10, 11, 20))})
    viewer.toggle_play()
    viewer.advance_playback(4)  # playback time 12; last available snapshot is t=11
    assert viewer.index == 1
    viewer.advance_playback(16)
    assert viewer.index == 2 and not viewer.playing


def test_zero_steps_static_scene():
    viewer = SimulationViewer({"Test": history(1, (0,))})
    viewer.replay()
    viewer.advance_playback(100)
    assert viewer.index == 0 and not viewer.playing
    assert not viewer.timeline.active
    viewer.figure.canvas.draw()


@pytest.mark.parametrize("kwargs", [{"view": "bad"}, {"labels": ["only one"]}, {"labels": ["", "b", "c", "d"]}])
def test_invalid_display_options(kwargs):
    with pytest.raises(ValueError):
        SimulationViewer({"Test": history()}, **kwargs)


def test_mismatched_histories_and_empty_input():
    with pytest.raises(ValueError):
        SimulationViewer({})
    with pytest.raises(ValueError, match="time grid"):
        SimulationViewer({"A": history(), "B": history(times=(0, 2, 4))})
    with pytest.raises(ValueError, match="initial conditions"):
        SimulationViewer({"A": history(), "B": history(3)})


def test_launcher_arbitrary_n_and_config_validation(tmp_path):
    functions = runpy.run_path(str(Path(__file__).parents[1]/"experiments"/"show_simulation.py"))
    data = functions["load_system"](Path(__file__).parents[1]/"experiments"/"four_body_visual_demo.json")
    data["num_steps"] = 2
    results = functions["simulate"](data)
    assert set(results) == {"Velocity Verlet", "Leapfrog (KDK)", "Euler-Cromer", "Forward Euler"}
    assert all(result.final_state.n_bodies == 4 for result in results.values())
    assert all(len(result.states) == 3 for result in results.values())
    path = tmp_path/"invalid.json"
    path.write_text('{"mass": [1]}')
    with pytest.raises(ValueError, match="missing"):
        functions["load_system"](path)
    data["labels"] = ["wrong"]
    with pytest.raises(ValueError, match="labels"):
        functions["simulate"](data)


def test_information_text_does_not_overlap():
    viewer = SimulationViewer({"Test": history()}, view="xy")
    viewer.figure.canvas.draw()
    renderer = viewer.figure.canvas.get_renderer()
    body_box = viewer.body_info.get_window_extent(renderer)
    help_box = viewer.help_text.get_window_extent(renderer)
    assert not body_box.overlaps(help_box)


def test_launcher_snapshot_and_history_export(tmp_path):
    import json
    import subprocess
    import sys
    root = Path(__file__).parents[1]
    snapshot, archive = tmp_path/"scene.png", tmp_path/"history.npz"
    completed = subprocess.run([sys.executable, str(root/"experiments"/"show_simulation.py"),
        "--steps", "8", "--snapshot", str(snapshot), "--save-history", str(archive)],
        cwd=root, capture_output=True, text=True, check=True)
    assert "Saved snapshot" in completed.stdout
    assert snapshot.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    with np.load(archive, allow_pickle=False) as arrays:
        metadata = json.loads(str(arrays["metadata_json"]))
        assert metadata["configuration"]["num_steps"] == 8
        assert arrays["times_s"].shape == (9,)
        for key in ("velocity_verlet", "leapfrog_kdk", "euler_cromer", "forward_euler"):
            assert arrays[f"{key}_positions_m"].shape == (9, 2, 3)
            np.testing.assert_array_equal(arrays[f"{key}_positions_m"][0], metadata["configuration"]["positions_m"])
            assert arrays[f"{key}_velocities_m_s"].shape == (9, 2, 3)


def test_four_method_selector_keeps_time_and_labels_separate():
    names = ["Velocity Verlet", "Leapfrog (KDK)", "Euler-Cromer", "Forward Euler"]
    viewer = SimulationViewer({name: history(offset=i) for i, name in enumerate(names)})
    viewer.seek(1)
    for i, name in enumerate(names):
        viewer.method_control.set_active(i)
        assert viewer.method == name and viewer.index == 1
        expected = viewer.histories[name].states[1].positions[0]
        np.testing.assert_array_equal(np.array(viewer.markers[0].get_data_3d()).ravel(), expected)
    viewer.figure.canvas.draw()
    renderer = viewer.figure.canvas.get_renderer()
    boxes = [label.get_window_extent(renderer) for label in viewer.method_control.labels]
    assert all(not a.overlaps(b) for a, b in zip(boxes, boxes[1:]))
