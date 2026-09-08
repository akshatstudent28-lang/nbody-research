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


@pytest.mark.parametrize("view", ["xy", "xz", "yz", "3d"])
def test_reset_restores_camera_without_changing_time_or_method(view):
    viewer = SimulationViewer({"Test": history()}, view=view)
    limits = viewer._initial_limits
    viewer.seek(1)
    viewer.axes.set_xlim(-100, 100)
    viewer.axes.set_ylim(40, 100)
    if view == "3d":
        viewer.axes.set_zlim(-10, 10)
        viewer.axes.view_init(elev=80, azim=130, roll=20)
    viewer.reset_button._observers.process("clicked", None)
    assert viewer.index == 1 and viewer.method == "Test"
    np.testing.assert_array_equal(viewer.axes.get_xlim(), limits[0])
    np.testing.assert_array_equal(viewer.axes.get_ylim(), limits[1])
    if view == "3d":
        np.testing.assert_array_equal(viewer.axes.get_zlim(), limits[2])
        assert (viewer.axes.elev, viewer.axes.azim, viewer.axes.roll) == viewer._initial_angles


@pytest.mark.parametrize("view", ["xy", "xz", "yz", "3d"])
def test_real_mouse_picking_and_two_property_panels(view):
    from matplotlib.backend_bases import MouseEvent
    from mpl_toolkits.mplot3d import proj3d
    result = history(2)
    viewer = SimulationViewer({"Test": result}, view=view, labels=["Alpha", "Beta"])
    viewer.figure.canvas.draw()
    point = result.states[0].positions[1]
    if view == "3d":
        x, y, _ = proj3d.proj_transform(*point, viewer.axes.get_proj())
    else:
        x, y = point[list(viewer.dimensions)]
    pixel = viewer.axes.transData.transform((x, y))
    event = MouseEvent("button_press_event", viewer.figure.canvas, *pixel, button=1)
    viewer.figure.canvas.callbacks.process("button_press_event", event)
    assert viewer.selected_body == 1
    text = viewer.body_info.get_text()
    assert "Alpha" in text and "Beta" in text
    assert text.count("Mass [kg]") == 2 and text.count("Speed [m/s]") == 2
    assert "Beta  [selected]" in text


@pytest.mark.parametrize("n", [6, 12])
def test_dropdown_real_click_scroll_and_selection(n):
    from matplotlib.backend_bases import MouseEvent
    viewer = SimulationViewer({"Test": history(n)})
    dropdown = viewer.body_dropdown
    assert dropdown is not None and not dropdown.open
    viewer.figure.canvas.draw()
    def click(axes, xy):
        pixel = axes.transAxes.transform(xy)
        for kind in ("button_press_event", "button_release_event"):
            viewer.figure.canvas.callbacks.process(kind, MouseEvent(kind, viewer.figure.canvas, *pixel, button=1))
    click(dropdown.button.ax, (0.5, 0.5))
    assert dropdown.open
    for _ in range(max(0, n-8)):
        pixel = dropdown.axes.transAxes.transform((0.5, 0.5))
        event = MouseEvent("scroll_event", viewer.figure.canvas, *pixel, button="down", step=-1)
        viewer.figure.canvas.callbacks.process("scroll_event", event)
    row = n-1-dropdown.offset
    click(dropdown.axes, (0.4, (8-row-0.5)/9))
    assert viewer.selected_body == n-1
    assert not dropdown.open
    assert f"Body {n}" in viewer.body_info.get_text()


def test_acceleration_properties_use_configured_g_and_equal_opposite_forces():
    initial = SystemState([2, 3], [[0, 0, 0], [3, 4, 0]], np.zeros((2, 3)))
    viewer = SimulationViewer({"Test": SimulationResult((initial,))}, view="xy", gravitational_constant=1)
    expected = np.array([[9/125, 12/125, 0], [-6/125, -8/125, 0]])
    np.testing.assert_allclose(viewer.acceleration_values, expected, rtol=5e-14, atol=0)
    np.testing.assert_allclose(initial.masses[:, None]*viewer.acceleration_values,
        [[18/125, 24/125, 0], [-18/125, -24/125, 0]], rtol=5e-14, atol=0)
    assert viewer.gravity_artist is not None
    assert viewer.gravity_artist.U[0] > 0 and viewer.gravity_artist.U[1] < 0
    before = viewer.index
    viewer.trail_control.set_active(1)
    assert viewer.gravity_artist is None and viewer.index == before


def test_both_bodies_respond_to_gravity_for_all_methods():
    functions = runpy.run_path(str(Path(__file__).parents[1]/"experiments"/"show_simulation.py"))
    data = functions["load_system"]()
    data["num_steps"] = 10
    for result in functions["simulate"](data).values():
        first, last = result.states[0], result.final_state
        for i in (0, 1):
            assert np.linalg.norm(last.positions[i]-first.positions[i]) > 0
            assert np.linalg.norm(last.velocities[i]-first.velocities[i]) > 0


def test_gravity_unavailable_does_not_invent_accelerations():
    coincident = SystemState([1, 2], np.zeros((2, 3)), np.zeros((2, 3)))
    viewer = SimulationViewer({"Test": SimulationResult((coincident,))})
    assert viewer.acceleration_values is None
    assert "Gravity unavailable" in viewer.body_info.get_text()
    assert viewer.gravity_artist is None
