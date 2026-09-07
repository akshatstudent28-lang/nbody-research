# Part 2 - Newtonian gravity engine

## Scope and interfaces

The public imports are:

```python
from nbody.physics import accelerations, center_of_mass, pairwise_force
```

- accelerations(masses, positions, *, gravitational_constant=G) -> (N, 3), m/s^2.
- pairwise_force(mass_i, mass_j, position_i, position_j,
  *, gravitational_constant=G) -> (3,), N: force on i due to j.
- center_of_mass(masses, positions) -> (3,), m.

Masses have shape (N,), are positive and finite, and N >= 1.
Positions have shape (N, 3). Public functions validate and copy input arrays;
outputs are independent writable float64 arrays. They accept SystemState arrays
without requiring velocities or time. No Part 1 interface was changed.
The existing internal array/scalar validators are reused.

## Physics, mathematics, and algorithm

For every unordered pair i < j:
d = r_j - r_i; r = |d|; u = d/r.
Add (G*m_j/r^2)*u to a_i and subtract (G*m_i/r^2)*u from a_j.

Attraction follows from the direction toward the other body. Accelerations
are not generally equal and opposite: multiplying each by its own mass gives
the equal-and-opposite pair forces required by Newton's third law.

The implementation uses a unit vector and successive divisions by r rather
than forming r^3. np.hypot.reduce computes distance without naively squaring
large/small components. These are algebraic evaluations of the same unsoftened
Newtonian equation, not alterations of the physical model.

Each pair's geometry is evaluated once: N(N-1)/2 pairs. Fixed-size vector work
per pair gives O(N^2) time. Validated inputs and output take O(N) memory;
there is no N-by-N displacement tensor. The public pair-force function is O(1).
No performance benchmark or optimization claim is made in this part.

The center of mass is sum(m_i*r_i)/sum(m_i). To avoid forming enormous raw
mass-position products or total masses, first divide all masses by their
maximum, then normalize those values to weights summing to approximately one.
The weighted position sum is algebraically unchanged. Time and memory are O(N).
The method still has finite range and rounding limitations.

Dimensions:
- acceleration: (m^3 kg^-1 s^-2)*kg/m^2 = m s^-2;
- force: kg*m s^-2 = N;
- center of mass: kg*m/kg = m.

## Safety and limitations

Coincidence raises ValueError identifying the body indices in accelerations.
N=1 gives exactly zero acceleration. Center of mass accepts coincidence.
Invalid shapes/nonpositive/nonfinite data raise ValueError; unsupported types
raise TypeError. A positive finite gravitational_constant may be supplied
explicitly for controlled tests; SI G is the default.

Arithmetic overflow, underflow, invalid arithmetic, and division by zero raise
FloatingPointError. There is no softening, minimum distance, clipping, or
collision prescription. Strict underflow checks can reject negligible
components or extreme mass ratios. A different arithmetic ordering might
represent some currently rejected cases. This conservative baseline is not
arbitrary-precision arithmetic and does not promise support for every finite
input. Cancellation, rounded-away separations at large coordinate offsets,
and accumulation error remain possible without an exception.

Floating-point pair updates do not imply exactly zero net force after summation.
Tests quantify the residual. Instantaneous force balance is not a demonstration
of momentum conservation under a future numerical integrator.

## Validation commands and results

Run from the repository using its existing virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe experiments/validate_gravity.py --output docs/part2-validation.json
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m compileall -q src tests experiments
```

- Before implementation: 56 tests passed in 0.15 s.
- First full implementation run: 112 passed in 0.29 s.
- Regression run after validation-reference correction: 112 passed in 0.19 s.
- Dependency check: No broken requirements found.
- Compilation: succeeded before reference correction; the corrected script
  was then executed successfully.
- No pre-existing lint/type check configuration exists.

The 56 new cases cover analytical two-body force and acceleration, symmetric
three-body superposition, source/target mass behavior, inverse-square scaling,
G scaling, translation, rotation, relabeling, internal force balance, independent
60-digit Decimal references for N=2,4,11, analytical center of mass, large mass
normalization, unchanged caller arrays, invalid inputs, singularities, and
explicit arithmetic range failures. A finite acceleration at separation 1e-100 m
checks absence of an arbitrary distance floor; it is a numerical stress test,
not a claim that Newtonian point particles are realistic at that scale.

For ordinary small-case array checks, rtol=5e-14 and atol=1e-24 in the relevant
SI units; analytical nonzero-direction checks use atol=0. Center translation
uses atol=1e-14 m. Exact representable zeros and simple weighted positions use
exact equality. These are float64 roundoff allowances, not uncertainty in G.

### Reproducible static report

The script records all eight-body masses and positions, seed 20260907, G,
software versions, computed and independent reference accelerations, thresholds,
and checks. Decimal uses 60 digits, an ordered-pair sum, and cubic distance,
independently from the production unit-vector/unordered-pair calculation.
Inputs are integers, avoiding ambiguity about decimal versus binary input
rounding. Reference outputs are rounded to float64 for the final comparison.

Results in docs/part2-validation.json:

| Metric | Measured | Threshold |
|---|---:|---:|
| Maximum absolute acceleration error | 3.0292258760486853e-28 m/s^2 | reported, not separately thresholded |
| Max error / max reference acceleration | 5.360537495954438e-16 | 5e-14 |
| Net force norm / sum of body force norms | 3.8855557634033517e-17 | 5e-15 |
| Rotation error / max baseline acceleration | 1.7868458319848137e-16 | 5e-14 |
| Translation error / max baseline acceleration | 0 | 5e-14 |
| Analytical pair-force normalized error | 1.2607339080289257e-16 | 5e-14 |
| Center-of-mass maximum absolute error | 0 m | 1e-14 m |

These normalized errors use global scales rather than dividing by zero-valued
individual components. Thresholds were set before running the report.

The analytical pair uses masses 2 and 3 kg at (0,0,0) and (3,4,0) m.
Expected force on the first body is (9.610992e-12, 1.2814656e-11, 0) N.
The center example uses masses 1 and 3 kg at (0,0,0) and (4,8,-4) m,
with expected center (3,6,-3) m.

### Failed validation and correction

The initial report failed its analytical pair-force check with normalized error
7.490861149397955e-05. The hand-entered expected vector was wrong:
(9.611712e-12, 1.2815616e-11, 0) N. Independent Decimal evaluation of
G*2*3*(3,4,0)/125 established the corrected expected values above.
The production engine and tolerances were unchanged. All six report checks
passed after correcting the reference. The original failed report is preserved
as docs/part2-validation-initial.json; it is historical evidence, not the current
acceptance result. All 112 tests were rerun successfully.

## Status

Validated for the tested instantaneous Newtonian interactions and geometric
identities. No orbital accuracy, time integration, long-term conservation,
chaos, convergence order, or performance scaling has been established.
No new dependencies or plots were added. Part 3 may proceed after explicit
authorization; it must preserve the force/data separation and safety contract.
