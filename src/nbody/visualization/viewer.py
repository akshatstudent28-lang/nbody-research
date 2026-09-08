"""Interactive playback of recorded N-body histories; never integrates physics."""

from collections.abc import Mapping, Sequence
import time

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, CheckButtons, RadioButtons, Slider
import numpy as np

from nbody.simulation import SimulationResult


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
                 title: str = "N-body simulation", reference_frame: str = "Input inertial frame"):
        if not histories:
            raise ValueError("histories must contain at least one simulation")
        if view not in ("3d", "xy", "xz", "yz"):
            raise ValueError("view must be 3d, xy, xz, or yz")
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
            self.figure = plt.figure(figsize=(13, 8), layout=None)
            self.figure.canvas.manager.set_window_title("N-body Research | Simulation")
            self.axes = self.figure.add_axes([0.07, 0.27, 0.63, 0.56],
                projection="3d" if view == "3d" else None)
            self.figure.text(0.065, 0.94, "N-BODY / RESEARCH", color="#67dfc5", fontsize=10, weight="bold")
            self.figure.text(0.065, 0.895, title, fontsize=21, weight="bold")
            self.figure.text(0.065, 0.858, f"{reference_frame}  |  {view.upper()}  |  positions in meters",
                             color="#9cafc7", fontsize=10)
            self.status = self.figure.text(0.73, 0.81, "", fontsize=12, linespacing=1.65)
            self.figure.text(0.73, 0.69, "INTEGRATION METHOD", color="#67dfc5", fontsize=9, weight="bold")
            self.method_control = RadioButtons(self.figure.add_axes([0.72, 0.46, 0.25, 0.21]),
                                               list(self.histories), activecolor="#67dfc5")
            self.trail_control = CheckButtons(self.figure.add_axes([0.72, 0.395, 0.25, 0.05]),
                                               ["Show orbital trails"], [True], check_props={"color": "#67dfc5"},
                                               frame_props={"edgecolor": "#9cafc7"})
            self.body_info = self.figure.text(0.73, 0.35, "", fontsize=10, va="top", linespacing=1.5)
            self.help_text = self.figure.text(0.73, 0.195, "Click a body to inspect its name/mass.\n3D: drag to rotate; wheel to zoom.\nMarkers are not physical radii.",
                             color="#9cafc7", fontsize=9, linespacing=1.6)
            self.timeline = Slider(self.figure.add_axes([0.15, 0.18, 0.51, 0.025]), "Frame", 0,
                                   max(1, len(self.times)-1), valinit=0, valstep=1, color="#67dfc5")
            if len(self.times) == 1:
                self.timeline.set_active(False)
            self.play_button = Button(self.figure.add_axes([0.065, 0.075, 0.105, 0.055]), "Play",
                                      color="#244b52", hovercolor="#32636a")
            self.replay_button = Button(self.figure.add_axes([0.18, 0.075, 0.105, 0.055]), "Replay",
                                        color="#243650", hovercolor="#344966")
            self.speed_control = Slider(self.figure.add_axes([0.41, 0.09, 0.25, 0.025]), "Speed", 0.25, 4,
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
        self.play_button.on_clicked(self.toggle_play)
        self.replay_button.on_clicked(self.replay)
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
        i = self.selected_body
        self.body_info.set_text(f"{self.labels[i]}\nMass: {state.masses[i]:.5g} kg\n1x: {self.sim_seconds_per_second:,.2f} sim s / display s")
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
        self.show_trails = not self.show_trails
        self._render()

    def _pick(self, event):
        if event.artist in self.markers:
            self.selected_body = self.markers.index(event.artist)
            self._render()

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
