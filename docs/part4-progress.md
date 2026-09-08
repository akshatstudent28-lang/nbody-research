# Part 4 progress

Part 4 and its authorized visual supplement are COMPLETE (2026-09-07).
Do not start Part 5 without explicit authorization.

Physics: Forward Euler and Euler-Cromer; existing gravity and runner reused.
Visual supplement: arbitrary-N Matplotlib viewer, 3D/XY/XZ/YZ, Play/Pause,
Replay, timeline, display speed, method switching, trails, body-name/mass picking.
Default two-body launch: .\.venv\Scripts\python.exe experiments/show_simulation.py
Custom four-body launch adds --config experiments/four_body_visual_demo.json.
Guide: docs/part4-visualization.md. Matplotlib installed and declared in pyproject.

Verification: 182 tests passed in 11.64 s. Native TkAgg GUI: all six checks
passed. 2D/3D screenshots visually inspected; overlap corrected and regression
covered. Exported trajectories reproduce saved Part 4 errors exactly; report
in docs/part4-export-check.json. pip check and compileall passed.
One shell-quoting attempt failed; replaced by check_viewer_export.py and passed.

Saved evidence: docs/part4-viewer-xy.png, docs/part4-viewer-3d.png,
docs/part4-viewer-history.npz, docs/part4-gui-check.json, original validation JSON.
No physics code, numerical tolerances, or initial benchmark outputs changed.

Known limits: exploratory four-body demo; no long-term stability/chaos claim;
full history and trails can be expensive; precomputed playback rather than a
live physics editor. Viewer shows numerical errors rather than correcting them.

Future rule saved in AGENTS.md: every future part must update the visual
simulation with its relevant capabilities/results and verify visual correctness.
Prior uncommitted changes preserved. No commit or push performed.
If interrupted, inspect git status and this checkpoint before edits.
Agent cannot monitor credits or automatically resume when they return.
