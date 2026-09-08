# PART 5 VIEWER SUPPLEMENT COMPLETE

## 1. What Was Built

Reset view restores the opening axis limits, zoom, and 3D elevation/azimuth/roll
without changing time, integrator, or play/pause state. Replay still restarts time.
Click any body to select and highlight it. Live properties include name, mass,
position vector, velocity vector, speed, gravitational acceleration vector and
acceleration magnitude, all labeled in SI units.

For one/two bodies, all properties appear simultaneously on the right. Three to
five bodies have a compact selector plus the selected body's details. More than
five have a dropdown; scroll within its open menu to reach every body.
Numbered entries preserve identity even when names duplicate.

Scaled arrows show instantaneous net gravitational acceleration on every body.
They share a common scale per frame, so relative magnitudes within the frame
are meaningful. Arrow lengths are not physical distances or a fixed scale across
time. In 2D they show the chosen projection of the 3D acceleration. Both particles
already moved under mutual gravity; that behavior is now explicitly tested for
all four integrators and visible through arrows and live properties.

## 2. Files Created or Modified

- src/nbody/visualization/viewer.py: reset, properties, selection, diagnostic arrows.
- src/nbody/visualization/body_dropdown.py: scrollable Matplotlib body dropdown.
- experiments/show_simulation.py: passes the configured G into display diagnostics.
- experiments/six_body_visual_demo.json: synthetic six-body dropdown demonstration.
- experiments/check_viewer_gui.py: real native timer/picking/dropdown/reset checks.
- tests/test_visualization.py: 13 additional rendered/control/physics checks.
- README, architecture, journal, progress and viewer guide: updated instructions.
- docs/viewer-controls-gui-check.json and viewer-properties-*.png: saved evidence.

The shared viewer applies these changes to the existing default, four-body,
elliptical, and custom configurations and all four integration methods.

## 3. Implementation Summary

The renderer reads recorded states. Acceleration is a read-only instantaneous
diagnostic recomputed from the selected state's masses/positions and configured
G; it never feeds back into integration. A one-frame cache avoids repeating
force evaluation when only selection or display controls change.

## 4. Tests Performed

2026-09-07 actual execution:
- .\.venv\Scripts\python.exe -m pytest -q: 218 passed in 25.16 s.
- .\.venv\Scripts\python.exe experiments/check_viewer_gui.py: 11 native TkAgg checks passed.
- Two-body XY and six-body 3D snapshots rendered and visually inspected.
- pip check: no broken requirements; compileall and git diff --check passed.

New tests dispatch MouseEvent objects through Matplotlib's event callbacks,
including rendered 3D projection coordinates. They verify actual picking and
scrollable dropdown interaction, not only direct calls to selection methods.
Reset is tested in XY/XZ/YZ/3D with altered limits and camera angles. Frame and
method stay unchanged. Properties for both bodies remain visible simultaneously.
Both objects' positions AND velocities change for every gravitational method.

Independent 3-4-5 pair acceleration/force check: rtol=5e-14, atol=0. With G=1
in an explicit SI test fixture, accelerations are (9/125,12/125,0) and
(-6/125,-8/125,0). Multiplying by masses 2 and 3 gives equal/opposite forces.
Display/control assertions use exact values where appropriate. No scientific
tolerance was weakened. Singular-state diagnostics show unavailable, never a
fabricated acceleration. All earlier numerical validation tests remain passing.

## 5. How the Major Code Works

### Camera reset

What: returns the graph to its opening view. Why: rotation, panning, and zoom
must be reversible. How: stores initial axis limits, axes position, box aspect,
and 3D angles and restores them on a button click. Physics connection: does
not modify physical coordinates or time. Mathematics: changes only the display
projection. CS: separates camera state from simulation state. Input: reset click;
output: restored camera. Design: distinct from Replay to prevent time changes.

### Body selection and live properties

What: identifies bodies and exposes current quantities. Why: inspect and compare
individual objects. How: markers, compact selectors, and the scrollable dropdown
all call select_body(index); index follows the stable state-array row. Physics:
mass/position/velocity/acceleration characterize motion. Mathematics: vector
components and Euclidean magnitudes. CS: one selection path avoids inconsistent
controls. Input: pick/menu index and current frame; output: selected highlight
and properties. Design: both objects shown together for two-body comparison;
large N uses a bounded-size menu rather than an unreadable full list.

### Gravity arrows

What: displays direction and relative strength of net acceleration. Why: connect
the force law to the moving objects. How: existing Newtonian accelerations() is
called with the actual G; vectors divide by the largest acceleration magnitude
and multiply by a common display length. Physics: forces on a pair are equal
and opposite, but accelerations differ inversely with mass. Mathematics:
a_i=sum(G*m_j*displacement/r^3). CS: diagnostic cache keyed by method/frame;
O(N^2) evaluation for a new frame and O(N) arrow construction. Inputs: recorded
masses/positions and G; outputs: diagnostic vectors/text. Design: never alters
or exaggerates recorded motion; no force-law change or softening was added.

## 6. Important Results

All earlier simulations inherit the controls through one viewer. Native GUI
checks confirmed timer advancement, pause, same-time method switching, reset,
body picking, dropdown opening and sixth-body selection, properties, trails,
replay and final frame. The synthetic six-body primary has visible nonzero
velocity/acceleration in its properties even when its displacement is small
relative to the lighter companions' orbits.

## 7. Problems, Assumptions, and Limitations

A first preview showed the timeline value crowding the two-body properties;
the timeline was shortened and the final image regenerated. No numerical test
failed. Selecting visually overlapping bodies can be ambiguous; use the body
selector/dropdown or rotate/pause the scene. Acceleration diagnostics add O(N^2)
work per newly displayed frame, so very large systems may display more slowly.

Properties are those represented by our point-mass model. Radius, temperature,
composition, real ephemerides, and observational classifications are not invented.
Synthetic examples are not validated real celestial systems. Small motion of a
massive primary is physically expected; the viewer does not magnify its motion.
The emphasis on chaos and object/method comparison remains a research direction,
not a claim that displayed irregular motion has been established as chaos.

## 8. Five Understanding Questions

1. Why should resetting the camera leave simulation time unchanged?
2. Why do equal/opposite gravitational forces not imply equal accelerations?
3. What can you compare using arrows with a common scale within a frame, and what cannot be inferred across frames?
4. Why is checking changes in velocity stronger evidence of gravitational response than merely seeing a particle move?
5. Why must a body's stable array index, rather than just its name, identify it in the dropdown?

## 9. How I Would Explain This

Teacher: The viewer now lets me restore the view and inspect both objects' motion.
GHP interviewer: One stable index connects picking, dropdown state, and numerical
arrays, with event-driven tests covering the actual control paths.
Research mentor: Instantaneous accelerations are diagnostic evaluations of the
same force law at recorded positions; they never modify integrated states.
Science-fair judge: I can inspect each body and see how mutual attraction changes
motion, while quantitative tests remain separate from visual appearance.

## 10. Research Journal Entry

Goal: improve inspection and comparison across all simulations. Implemented reset,
body property panels/selectors, and scaled acceleration arrows. Preserved physics
and full-history playback. 218 tests and 11 native GUI checks passed. Corrected a
layout overlap. No numerical methodology/tolerance changes. Future work remains
validated sensitivity/chaos and integrator comparisons under explicit part scope.

## 11. Git Commit

feat: add camera reset and interactive N-body gravity inspection

The user explicitly authorized committing and updating GitHub. Push completion
must be checked against the remote branch, not assumed from a local commit.

## 12. Project Status Review

The requested shared-viewer supplement is complete and tested. Current gravitational
methods are unchanged; no later roadmap part has begun. Visual inspection remains
a tool for research, not scientific proof. Continue numbered parts only on explicit
authorization. Every future part must preserve and update these visual controls.

## Run in VS Code

```powershell
cd C:\Users\aksha\Projects\nbody-research
.\.venv\Scripts\python.exe experiments/show_simulation.py
```

For the dropdown demonstration:

```powershell
.\.venv\Scripts\python.exe experiments/show_simulation.py --config experiments/six_body_visual_demo.json
```
