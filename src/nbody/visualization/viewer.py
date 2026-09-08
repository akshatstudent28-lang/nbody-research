"""Interactive playback of recorded N-body histories; never integrates physics."""

from collections.abc import Mapping, Sequence
import time

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, RadioButtons, Slider
import numpy as np

from nbody.simulation import SimulationResult
from nbody.constants import G
from nbody.core.state import _finite_real
from nbody.physics import accelerations
from .body_dropdown import BodyDropdown


class SimulationViewer:
    """View arbitrary N with fixed bounds shared across methods.

    Histories must describe the same masses, initial state, and time grid.
    Playback uses actual recorded times; speed changes never alter histories.
    Positions remain in the supplied Cartesian reference frame and SI meters.
    Marker radii are display symbols, not physical sizes. Keep this object alive
    while its window is open, so widget and timer callbacks remain connected.
    """

    def __init__(self, histories: Mapping[str, SimulationResult], *,
                 labels: Sequence[str] | None = None, view: str = "3d",
                 title: str = "N-body simulation", reference_frame: str = "Input inertial frame",
                 gravitational_constant: float = G):
        if not histories:
            raise ValueError("histories must contain at least one simulation")
        if view not in ("3d", "xy", "xz", "yz"):
            raise ValueError("view must be 3d, xy, xz, or yz")
        self.gravitational_constant = _finite_real(gravitational_constant, "gravitational_constant")
        if self.gravitational_constant <= 0:
            raise ValueError("gravitational_constant must be positive")
        self._gravity_key = None
        self.acceleration_values = None
        self.gravity_artist = None
        self.show_gravity = True
        self.histories = dict(histories)
        if any(not isinstance(k, str) or not k or not isinstance(v, SimulationResult)
               for k, v in self.histories.items()):
            raise TypeError("histories must map nonempty method names to SimulationResult")
        first = next(iter(self.histories.values()))
        self.times = np.array([s.time for s in first.states])
        initial = first.states[0]
        self.n_bodies = initial.n_bodies
        for result in self.histories.values():
            if not np.array_equal([s.time for s in result.states], self.times):
                raise ValueError("histories must share the same time grid")
            for field in ("masses", "positions", "velocities"):
                if not np.array_equal(getattr(result.states[0], field), getattr(initial, field)):
                    raise ValueError("histories must share initial conditions and body order")
        self.labels = list(labels) if labels is not None else [f"Body {i+1}" for i in range(self.n_bodies)]
        if (len(self.labels) != self.n_bodies or
            any(not isinstance(label, str) or not label.strip() for label in self.labels)):
            raise ValueError("labels must contain one nonempty name per body")
        self.positions = {name: np.stack([s.positions for s in result.states])
                          for name, result in self.histories.items()}
        self.method = next(iter(self.histories))
        self.view = view
        self.dimensions = {"xy": (0, 1), "xz": (0, 2), "yz": (1, 2), "3d": (0, 1, 2)}[view]
        self.index = 0
        self.playing = False
        self.speed = 1.0
        self.show_trails = True
        self.playback_time = float(self.times[0])
        self._last_tick = time.perf_counter()
        self._setting_slider = False
        duration = float(self.times[-1] - self.times[0])
        if not np.isfinite(duration):
            raise ValueError("history duration is outside display range")
        self.sim_seconds_per_second = duration / 20.0
        self.selected_body = 0
        colors = {"figure.facecolor": "#0b1220", "axes.facecolor": "#111e30",
                  "text.color": "#e6edf7", "axes.labelcolor": "#b7c7dc",
                  "xtick.color": "#9cafc7", "ytick.color": "#9cafc7",
                  "axes.edgecolor": "#344761", "font.size": 10}
        with plt.rc_context(colors):
            self.figure = plt.figure(figsize=(16, 10), layout=None)
            self.figure.canvas.manager.set_window_title("N-body Research | Simulation")
            self.axes = self.figure.add_axes([0.06, 0.27, 0.55, 0.56],
                projection="3d" if view == "3d" else None)
            self.figure.text(0.065, 0.94, "N-BODY / RESEARCH", color="#67dfc5", fontsize=10, weight="bold")
            self.figure.text(0.065, 0.895, title, fontsize=21, weight="bold")
            self.figure.text(0.065, 0.858, f"{reference_frame}  |  {view.upper()}  |  positions in meters",
                             color="#9cafc7", fontsize=10)
            self.status = self.figure.text(0.68, 0.83, "", fontsize=12, linespacing=1.65)
            self.figure.text(0.68, 0.715, "INTEGRATION METHOD", color="#67dfc5", fontsize=9, weight="bold")
            self.method_control = RadioButtons(self.figure.add_axes([0.68, 0.57, 0.29, 0.13]),
                                               list(self.histories), activecolor="#67dfc5")
            self.trail_control = CheckButtons(self.figure.add_axes([0.68, 0.51, 0.29, 0.05]),
                                               ["Show orbital trails", "Gravity arrows (scaled)"], [True, True], check_props={"color": "#67dfc5"},
                                               frame_props={"edgecolor": "#9cafc7"})
            self.figure.text(0.68, 0.48, "BODY PROPERTIES / CURRENT FRAME", color="#67dfc5", fontsize=9, weight="bold")
            self.body_info = self.figure.text(0.68, 0.45, "", fontsize=9, va="top", linespacing=1.45, family="monospace")
            self.help_text = self.figure.text(0.68, 0.055,
                "Click a body to select it. Reset view restores the camera.\nGravity arrows share a scale per frame, not physical lengths.\nMarkers are not physical radii; display speed does not change dt.",
                color="#9cafc7", fontsize=8, linespacing=1.5)
            self.body_selector = None
            self.body_dropdown = None
            if 3 <= self.n_bodies <= 5:
                self.body_selector = RadioButtons(self.figure.add_axes([0.68, 0.34, 0.29, 0.115]),
                    [f"{i+1}. {name}" for i, name in enumerate(self.labels)], activecolor="#67dfc5")
                self.body_info.set_position((0.68, 0.31))
            elif self.n_bodies > 5:
                self.body_dropdown = BodyDropdown(self.figure, self.labels, self.select_body)
                self.body_info.set_position((0.68, 0.39))
            self.timeline = Slider(self.figure.add_axes([0.15, 0.18, 0.46, 0.025]), "Frame", 0,
                                   max(1, len(self.times)-1), valinit=0, valstep=1, color="#67dfc5")
            if len(self.times) == 1:
                self.timeline.set_active(False)
            self.play_button = Button(self.figure.add_axes([0.065, 0.075, 0.105, 0.055]), "Play",
                                      color="#244b52", hovercolor="#32636a")
            self.replay_button = Button(self.figure.add_axes([0.18, 0.075, 0.105, 0.055]), "Replay",
                                        color="#243650", hovercolor="#344966")
            self.reset_button = Button(self.figure.add_axes([0.295, 0.075, 0.10, 0.055]), "Reset view",
                                       color="#243650", hovercolor="#344966")
            self.speed_control = Slider(self.figure.add_axes([0.46, 0.09, 0.15, 0.025]), "Speed", 0.25, 4,
                                        valinit=1, valstep=0.25, valfmt="%1.2fx", color="#67dfc5")
            self.figure.text(0.065, 0.025, "Playback speed changes the display only. Physics timestep is fixed for each run.",
                             color="#9cafc7", fontsize=9)
            self.markers, self.trails = [], []
            palette = plt.get_cmap("tab10" if self.n_bodies <= 10 else "turbo")
            for i in range(self.n_bodies):
                color = palette(i if self.n_bodies <= 10 else i/max(1, self.n_bodies-1))
                empty = ([], [], []) if view == "3d" else ([], [])
                trail, = self.axes.plot(*empty, color=color, linewidth=1.3, alpha=0.7)
                marker, = self.axes.plot(*empty, color=color, marker="o", linestyle="", markersize=8,
                                         markeredgecolor="white", markeredgewidth=0.5,
                                         label=self.labels[i], picker=6)
                self.trails.append(trail)
                self.markers.append(marker)
            for dim, setter in zip(self.dimensions, (self.axes.set_xlabel, self.axes.set_ylabel,
                                  self.axes.set_zlabel) if view == "3d" else (self.axes.set_xlabel, self.axes.set_ylabel)):
                setter(f"{'xyz'[dim]} (m)")
            self.axes.grid(True, alpha=0.18)
            self.axes.ticklabel_format(style="sci", axis="both", scilimits=(0, 0), useOffset=False)
            self.axes.tick_params(colors="#9cafc7")
            if view == "3d":
                for axis in (self.axes.xaxis, self.axes.yaxis, self.axes.zaxis):
                    axis.pane.set_facecolor("#111e30")
                self.axes.set_box_aspect((1, 1, 1))
            else:
                self.axes.set_aspect("equal", adjustable="box")
            if self.n_bodies <= 10:
                self.axes.legend(loc="upper left", fontsize=8, framealpha=0.2)
            self._set_bounds()
            self._initial_limits = (self.axes.get_xlim(), self.axes.get_ylim())
            self._initial_angles = None
            if self.view == "3d":
                self._initial_limits += (self.axes.get_zlim(),)
                self._initial_angles = (self.axes.elev, self.axes.azim, self.axes.roll)
            self._initial_position = self.axes.get_position(original=True).frozen()
            self._initial_box_aspect = self.axes.get_box_aspect()
        self.play_button.on_clicked(self.toggle_play)
        self.replay_button.on_clicked(self.replay)
        self.reset_button.on_clicked(self.reset_view)
        if self.body_selector is not None:
            self.body_selector.on_clicked(lambda label: self.select_body(int(label.split(".", 1)[0])-1))
        self.timeline.on_changed(self._scrub)
        self.speed_control.on_changed(self.set_speed)
        self.method_control.on_clicked(self.select_method)
        self.trail_control.on_clicked(self._toggle_trails)
        self.figure.canvas.mpl_connect("pick_event", self._pick)
        self.figure.canvas.mpl_connect("close_event", self._close)
        self.timer = self.figure.canvas.new_timer(interval=33)
        self.timer.add_callback(self._tick)
        self._render()

    def _set_bounds(self):
        lower = np.min([p.min(axis=(0, 1)) for p in self.positions.values()], axis=0)
        upper = np.max([p.max(axis=(0, 1)) for p in self.positions.values()], axis=0)
        with np.errstate(over="raise", invalid="raise"):
            center = lower/2 + upper/2
            half = max(float(np.max((upper/2-lower/2)[list(self.dimensions)]))*1.12, 1.0)
            low, high = center-half, center+half
        if not np.all(np.isfinite([low, high])) or np.any(low == high):
            raise ValueError("positions exceed the viewer's coordinate resolution")
        setters = (self.axes.set_xlim, self.axes.set_ylim, self.axes.set_zlim) if self.view == "3d" else (self.axes.set_xlim, self.axes.set_ylim)
        for dim, setter in zip(self.dimensions, setters):
            setter(low[dim], high[dim])

    def _render(self):
        positions = self.positions[self.method]
        for i, (marker, trail) in enumerate(zip(self.markers, self.trails)):
            now = positions[self.index:self.index+1, i]
            past = positions[:self.index+1, i]
            if self.view == "3d":
                marker.set_data_3d(*now.T)
                trail.set_data_3d(*past.T)
            else:
                marker.set_data(now[:, self.dimensions[0]], now[:, self.dimensions[1]])
                trail.set_data(past[:, self.dimensions[0]], past[:, self.dimensions[1]])
            trail.set_visible(self.show_trails)
        state = self.histories[self.method].states[self.index]
        mode = "PLAYING" if self.playing else ("END OF RUN" if self.index == len(self.times)-1 and self.index else "PAUSED")
        self.status.set_text(f"{mode}\n{self.n_bodies} bodies  /  {self.index:,} of {len(self.times)-1:,} steps\nt = {state.time:,.3f} s")
        self._update_gravity(state)
        shown = range(self.n_bodies) if self.n_bodies <= 2 else [self.selected_body]
        self.body_info.set_text("\n\n".join(self._properties(state, i) for i in shown))
        for i, marker in enumerate(self.markers):
            marker.set_markersize(11 if i == self.selected_body else 8)
            marker.set_markeredgewidth(1.8 if i == self.selected_body else 0.5)
        self.play_button.label.set_text("Pause" if self.playing else "Play")
        self._setting_slider = True
        try:
            self.timeline.set_val(self.index)
        finally:
            self._setting_slider = False
        self.figure.canvas.draw_idle()

    def seek(self, index):
        """Pause on a recorded frame, including the final frame."""
        self.index = max(0, min(int(index), len(self.times)-1))
        self.playback_time = float(self.times[self.index])
        self.playing = False
        self.timer.stop()
        self._render()

    def _scrub(self, value):
        if not self._setting_slider:
            self.seek(value)

    def toggle_play(self, event=None):
        if len(self.times) == 1:
            return
        self.playing = not self.playing
        if self.playing:
            if self.index == len(self.times)-1:
                self.index = 0
                self.playback_time = float(self.times[0])
            self._last_tick = time.perf_counter()
            self.timer.start()
        else:
            self.timer.stop()
        self._render()

    def replay(self, event=None):
        self.seek(0)
        self.toggle_play()

    def set_speed(self, value):
        value = float(value)
        if not np.isfinite(value) or value <= 0:
            raise ValueError("playback speed must be finite and positive")
        self.speed = value
        self._last_tick = time.perf_counter()

    def select_method(self, name):
        if name not in self.histories:
            raise ValueError("unknown integration method")
        self.method = name
        self._render()

    def _toggle_trails(self, label):
        if label == "Gravity arrows (scaled)":
            self.show_gravity = not self.show_gravity
        else:
            self.show_trails = not self.show_trails
        self._render()

    def _pick(self, event):
        if event.artist in self.markers:
            self.select_body(self.markers.index(event.artist))

    def select_body(self, index):
        """Select a stable body row, including through real marker picking."""
        if not isinstance(index, (int, np.integer)) or not 0 <= index < self.n_bodies:
            raise ValueError("body index is out of range")
        self.selected_body = int(index)
        if self.body_dropdown is not None:
            self.body_dropdown.set_selected(index)
        if self.body_selector is not None:
            expected = self.body_selector.labels[index].get_text()
            if self.body_selector.value_selected != expected:
                self.body_selector.set_active(index)
                return
        self._render()

    def reset_view(self, event=None):
        """Restore opening camera/zoom; retain time, method and playback state."""
        self.axes.set_position(self._initial_position)
        self.axes.set_xlim(self._initial_limits[0])
        self.axes.set_ylim(self._initial_limits[1])
        if self.view == "3d":
            self.axes.set_zlim(self._initial_limits[2])
            self.axes.view_init(elev=self._initial_angles[0], azim=self._initial_angles[1], roll=self._initial_angles[2])
            self.axes.set_box_aspect(self._initial_box_aspect)
        else:
            self.axes.set_aspect("equal", adjustable="box")
        toolbar = getattr(self.figure.canvas.manager, "toolbar", None)
        if toolbar is not None:
            toolbar.update()
            toolbar.push_current()
        self.figure.canvas.draw_idle()

    def _properties(self, state, index):
        def vector(values):
            return "(" + ", ".join(f"{value:.3e}" for value in values) + ")"
        name = self.labels[index]
        heading = f"{index+1}. {name}" + ("  [selected]" if index == self.selected_body else "")
        text = (f"{heading}\nMass [kg]: {state.masses[index]:.5e}"
                f"\nr [m]:   {vector(state.positions[index])}"
                f"\nv [m/s]: {vector(state.velocities[index])}"
                f"\nSpeed [m/s]: {np.hypot.reduce(state.velocities[index]):.5e}")
        if self.acceleration_values is None:
            return text + "\nGravity unavailable at this state"
        acceleration = self.acceleration_values[index]
        return text + f"\na [m/s^2]: {vector(acceleration)}\n|a| [m/s^2]: {np.hypot.reduce(acceleration):.5e}"

    def _update_gravity(self, state):
        """Read-only instantaneous diagnostic; never feeds back into motion."""
        key = (self.method, self.index)
        if key != self._gravity_key:
            self._gravity_key = key
            try:
                self.acceleration_values = accelerations(state.masses, state.positions,
                    gravitational_constant=self.gravitational_constant)
            except (ValueError, FloatingPointError):
                self.acceleration_values = None
        if self.gravity_artist is not None:
            self.gravity_artist.remove()
            self.gravity_artist = None
        if not self.show_gravity or self.acceleration_values is None:
            return
        maximum = float(np.max(np.hypot.reduce(self.acceleration_values, axis=1)))
        if maximum == 0:
            return
        extent = self._initial_limits[0][1]-self._initial_limits[0][0]
        vectors = self.acceleration_values/maximum*(0.12*extent)
        if self.view == "3d":
            self.gravity_artist = self.axes.quiver(*state.positions.T, *vectors.T,
                color="#67dfc5", normalize=False, arrow_length_ratio=0.25, linewidth=1.5)
        else:
            d0, d1 = self.dimensions
            self.gravity_artist = self.axes.quiver(state.positions[:, d0], state.positions[:, d1],
                vectors[:, d0], vectors[:, d1], color="#67dfc5", angles="xy", scale_units="xy", scale=1,
                width=0.004)

    def _tick(self):
        if self.playing:
            now = time.perf_counter()
            elapsed = now - self._last_tick
            self._last_tick = now
            self.advance_playback(elapsed)
        return True

    def advance_playback(self, elapsed):
        """Advance display time; exposed for deterministic controller tests."""
        if not np.isfinite(elapsed) or elapsed < 0:
            raise ValueError("elapsed display time must be finite and nonnegative")
        if not self.playing:
            return
        self.playback_time = min(float(self.times[-1]), self.playback_time + elapsed*self.speed*self.sim_seconds_per_second)
        self.index = max(0, int(np.searchsorted(self.times, self.playback_time, side="right"))-1)
        if self.index == len(self.times)-1:
            self.playing = False
            self.timer.stop()
        self._render()

    def _close(self, event=None):
        self.playing = False
        self.timer.stop()

    def show(self):
        """Start playback and enter Matplotlib's native GUI event loop."""
        if not self.playing:
            self.toggle_play()
        plt.show()
