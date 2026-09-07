"""Physical constants in SI units.

Source: CODATA 2022, https://physics.nist.gov/cuu/pdf/wall_2022.pdf
G is measured, not exact; standard uncertainty is 1.5e-15 m^3 kg^-1 s^-2.
Experiments will use the nominal value consistently, not sample uncertainty.
"""

from typing import Final

G: Final[float] = 6.67430e-11  # m^3 kg^-1 s^-2