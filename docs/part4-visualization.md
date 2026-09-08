# Part 4 supplement - Visual N-body simulation

## Launch in VS Code

Open C:\Users\aksha\Projects\nbody-research in VS Code. Select Terminal > New
Terminal (PowerShell), then run:

```powershell
.\.venv\Scripts\python.exe experiments/show_simulation.py
```

A separate native Matplotlib window opens and starts playing both bodies.
The default method is Euler-Cromer. The two methods are precomputed from the
same initial conditions; select Forward Euler to inspect its different motion.
Close the window to return to the terminal.

For a clearer planar orbital view:

```powershell
.\.venv\Scripts\python.exe experiments/show_simulation.py --view xy
```

For a four-body 3D demonstration:

```powershell
.\.venv\Scripts\python.exe experiments/show_simulation.py --config experiments/four_body_visual_demo.json
```

This four-body configuration is exploratory, not an analytically validated
stable system or an investigation of chaos. All four bodies interact through
the existing Newtonian gravity engine; the primary is not artificially fixed.

Matplotlib is installed in this environment and declared in pyproject.toml.
On a fresh checkout, install the project with:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

If the terminal is in another folder, first run:

```powershell
cd C:\Users\aksha\Projects\nbody-research
```

## Controls

- Play/Pause: start or pause the recorded motion.
- Replay: return to the initial state and play again.
- Frame slider: inspect any recorded state; scrubbing pauses playback.
- Speed: 0.25x to 4x display speed. At 1x, a complete run takes approximately
  20 display seconds. Frame rendering limits actual smoothness.
- Integration method: switch results at the same frame/time, with unchanged bounds.
- Show orbital trails: toggle paths through all recorded positions up to the frame.
- Click a body: show its name and mass; identity follows its state-array row.
- 3D: drag the plot to rotate, use the mouse wheel to zoom.
- --view xy, xz, yz: planar projections in the original input reference frame.

Axes use meters and equal spatial scales. Scientific-notation axis multipliers
apply to tick labels. Marker radii are display symbols, not physical radii.
A legend is shown for up to 10 bodies; larger systems retain all markers and
clickable body inspection without an overcrowded legend. Similar colors and
occlusion can limit identification in dense systems.

The viewer copies recorded positions. It never evaluates forces or changes a
simulation state. Playback speed is completely separate from the physics dt.
It displays the latest recorded state at or before the playback time, without
inventing interpolated states. Display frames can be skipped on slow hardware;
the timeline still allows inspection of every recorded state.

## Arbitrary body count and reproducibility

Use four_body_visual_demo.json as an editable example. N is the number of mass
entries, not a hardcoded value. Required JSON keys:

- masses_kg: N strictly positive masses.
- positions_m: N rows of [x, y, z].
- velocities_m_s: N rows of [vx, vy, vz].
- dt_s: positive physics timestep in seconds.
- num_steps: nonnegative integer.

Optional: labels (N names), initial_time_s, G_m3_kg_s2, title, reference_frame.
Unknown keys are rejected to catch typos. Numeric states use existing validation.
--steps and --dt override the corresponding settings and therefore change
physical duration; the in-window Speed slider does not.

To save the full default trajectories and a planar image without a window:

```powershell
.\.venv\Scripts\python.exe experiments/show_simulation.py --view xy --snapshot docs/part4-viewer-xy.png --frame 1200 --save-history docs/part4-viewer-history.npz
```

The NPZ archive contains timestamps, masses, both methods' complete position and
velocity histories, and JSON metadata with explicit configuration, methods,
Python/platform and package versions. Read it with np.load(path, allow_pickle=False).
This is an export for analysis, not a resume format. The current viewer launcher
runs from initial conditions, not from an imported NPZ archive.

## Architecture and extension contract

SimulationViewer accepts a mapping of method names to SimulationResult objects.
It validates shared initial conditions, masses/body order, and identical time
grids before allowing a method comparison. Every body's marker and trail is
built from the same (time, body, coordinate) array convention.

The viewer stores O(methods * snapshots * N) position data in addition to the
runner's histories. Full-trail drawing costs up to O(snapshots * N) per frame;
large N and long histories can be slow. This is a correct readable baseline,
not a performance certification. Bounds are shared across histories to avoid
misleading rescaling when switching methods. Escaping or inaccurate trajectories
can consequently make the central system look small; zoom for inspection.

Every future part must update this visual simulation with its relevant methods,
systems, diagnostics, or research results. This requirement is also in AGENTS.md.
New integrators should be added to the launcher's METHODS mapping. New diagnostics
must consume the same stored states/times. Keep scientific validation independent
of whether the viewer produces plausible-looking motion.

## Actual verification (2026-09-07)

- Full suite: 182 passed in 11.64 s, including all preceding scientific tests.
- 26 new viewer cases: 1/2/4/12 bodies in XY/XZ/YZ/3D; coordinates match recorded
  arrays exactly; equal bounds checked at rtol=1e-14, atol=0; playback controls,
  nonuniform timestamps, zero steps, invalid inputs, mismatched histories,
  label validation, layout overlap, and CLI snapshot/history export.
- Native TkAgg GUI check: all six checks passed (timer advance, pause, scrub/method
  switch, trails, replay, final frame). This exercises the real native event loop,
  not just headless drawing. The window is closed automatically after checking.
- Planar and four-body 3D PNGs rendered and visually inspected. Initial overlapping
  information/help text was corrected and a regression check added.
- Exported two-body histories reproduce saved benchmark maximum normalized errors:
  Forward Euler 0.18466439255237493; Euler-Cromer 0.0062612400755486.
  Export comparison uses rtol=5e-14, atol=0; both matched exactly in this run.
- pip check and compileall passed. No physics tolerances were changed.
- A shell-quoted one-line export check failed with SyntaxError; it was replaced
  with the reproducible check_viewer_export.py script, which passed.
- Sandbox image inspection failed; the images were read through an approved
  filesystem command and visually reviewed successfully.

Commands for repeating verification:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe experiments/check_viewer_gui.py
.\.venv\Scripts\python.exe experiments/check_viewer_export.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src tests experiments
```

The export check expects the default 2000-step NPZ generated by the command above
and docs/part4-validation.json from the Part 4 benchmark.

## Scientific limits

The renderer faithfully showing a recorded trajectory does not make that
trajectory physically accurate. Forward Euler's known error remains visible.
The four-body example demonstrates arbitrary-N plumbing and motion, not stability,
chaos, or precision orbital validation. No long-term conservation claim is made.
The physics remains point-mass Newtonian gravity without softening or collisions.
Both methods are precomputed before the window opens; a failed method raises
instead of displaying a fabricated or silently truncated trajectory.

Checked on Windows with Python 3.14.3, NumPy 2.5.3, Matplotlib 3.11.1 and Tk 8.6.
Compatibility with every OS/backend, window size or arbitrarily large history
is not established. Keep the window reasonably sized for the control layout.

Widget/timer API references consulted:
https://matplotlib.org/stable/api/widgets_api.html
https://matplotlib.org/stable/api/backend_bases_api.html#matplotlib.backend_bases.TimerBase

## Part 5 update

The current viewer now defaults to Velocity Verlet and offers four methods.
Part 4's two-method descriptions above record its historical implementation.
See [Part 5](part5-verlet.md) for current comparisons and commands.
