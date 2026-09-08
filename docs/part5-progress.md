# Part 5 progress

Implementation and validation complete on 2026-09-07.
New methods: velocity_verlet and leapfrog (synchronized KDK), equivalent in exact
arithmetic for current position-only gravity. Viewer now offers four methods.
205 tests passed in 12.98 s. Scientific refinement/conservation checks all passed.
Native GUI: six passed. Viewer and conservation figure visually inspected.
Evidence: docs/part5-validation.json, part5-conservation-series.npz,
part5-conservation.png, part5-gui-check.json, part5-viewer.png.
Guide: docs/part5-verlet.md. Launch: experiments/show_simulation.py.
Longer scenario: --config experiments/part5_elliptical.json --view xy.

Git: implementation committed locally as 649e366; no push performed.
Previously uncommitted Part 4 files required by Part 5 are included in that commit. Do not
claim a push unless explicitly authorized and its completion verified.
NASA-method identity question remains unresolved; do not guess an implementation.
No Part 6 or chaos investigation has begun. Await explicit START PART 6.
Final comparison should avoid counting equivalent Verlet/KDK as independent
algorithms. Every future part must also update the visual simulation.

Viewer inspection supplement complete: reset, properties, dropdown, gravity arrows.
218 tests and 11 native GUI checks pass. Guide: docs/viewer-controls-report.md.
GitHub update explicitly authorized for this supplement; verify git log/remote
when resuming. No Part 6 work has begun.
