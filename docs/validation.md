# Part 1 validation record

Date: 2026-09-07. Scope: project foundation only.

## Executed commands and outcomes

- python -m venv .venv: succeeded.
- .\.venv\Scripts\python.exe -m pip install -e ".[dev]": succeeded;
  temporary connection resets were retried by pip.
- .\.venv\Scripts\python.exe -m pytest -q: 56 passed in 1.48 seconds.
- .\.venv\Scripts\python.exe -m pip check: No broken requirements found.
- .\.venv\Scripts\python.exe -m compileall -q src tests: succeeded, no errors.
- .\.venv\Scripts\python.exe -m pip freeze: captured installed versions.
- Python import check: nbody resolves to this repository's src/nbody/__init__.py.
- git diff --check: no output. All scaffold and implementation files are
  untracked, so this command does not validate their whitespace.
- git status --short: existing and new project files remain untracked;
  no automatic commit or staging was performed.

No lint/type checker was configured in the existing project. Syntax compilation
is not a substitute for either. There was no pre-existing test suite.

## Test coverage

56 parameterized cases cover one, two, and seventeen bodies; array shapes;
float64 and contiguous layout; preservation of supplied values; ownership for
noncontiguous inputs; read-only arrays and frozen fields; nonpositive/empty
masses; ragged/mismatched arrays; NaN and infinities in each state field; invalid
scalar and array types; arbitrary negative epochs; coincident positions;
the documented G literal; valid, zero-step, invalid, and overflowing run settings.

No approximate tolerances are used: array preservation is tested by exact
equality, and duration examples use binary-exact dt=0.25.
For 40 steps the requested duration is exactly 10.0 seconds.
The G equality test checks transcription of the nominal value, not empirical
measurement accuracy. Its published uncertainty is not a test tolerance.

## Scientific interpretation and limits

The data contract is tested, and SI dimensions are documented.
There is no implemented force law, integrator, or trajectory. No conservation,
orbital, convergence, or performance claim follows from these results.
Finite values can still overflow future force calculations. Units are a caller
contract. Read-only flags prevent accidental edits, not deliberate tampering.
Only Python 3.14.3 on this Windows environment was executed; the declared
Python >=3.10 range has not been tested as a version matrix.

Before advancing beyond a gravity engine, quantitatively validate force direction,
mass/distance scaling, symmetries, and singularity rejection. Part 2 may proceed
when explicitly authorized.