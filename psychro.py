# =============================================================================
# Psychrometrics
# Wet-bulb temperature derived from dry-bulb, dew-point, and pressure.
#
# Method: Stull (2011) empirical formula — direct, no iteration required.
# Valid range: -20°C < T_db < 50°C, 5% < RH < 99%.
# Accuracy: ±0.65°C across the valid range (well within engineering tolerance).
#
# Reference: Stull, R. (2011). Wet-Bulb Temperature from Relative Humidity
#   and Air Temperature. Journal of Applied Meteorology and Climatology, 50(11).
#
# Physical bounds enforced:
#   T_wb <= T_odb  (wet-bulb never exceeds dry-bulb)
#   T_wb >= T_dp   (wet-bulb never falls below dew-point)
# =============================================================================

import math
import warnings
import numpy as np


def wet_bulb(T_db: float, T_dp: float, pressure: float) -> float:
    """
    Wet-bulb temperature (°C) using the Stull (2011) empirical formula.

    RH is back-calculated from T_dp and T_db using the Magnus formula,
    which is the standard EPW data approach.

    Parameters
    ----------
    T_db     : dry-bulb temperature (°C)
    T_dp     : dew-point temperature (°C)
    pressure : atmospheric pressure (Pa) — not used in Stull formula but
               retained for interface consistency.
    """
    # Warn if outside Stull formula validity range
    if T_db < -20 or T_db > 50:
        warnings.warn(
            f"T_db={T_db:.1f}°C is outside Stull formula validity range (-20 to 50°C). "
            f"Wet-bulb accuracy may be degraded.",
            stacklevel=2,
        )

    # Relative humidity from Magnus formula (Lawrence 2005)
    # RH = 100 * exp(b*T_dp/(c+T_dp)) / exp(b*T_db/(c+T_db))
    b = 17.368
    c = 238.88
    RH = 100.0 * math.exp(b * T_dp / (c + T_dp)) / math.exp(b * T_db / (c + T_db))
    RH = max(1.0, min(99.0, RH))   # clamp to valid range for formula

    # Stull (2011) eq. 1
    T_wb = (
        T_db * math.atan(0.151977 * (RH + 8.313659) ** 0.5)
        + math.atan(T_db + RH)
        - math.atan(RH - 1.676331)
        + 0.00391838 * RH ** 1.5 * math.atan(0.023101 * RH)
        - 4.686035
    )

    # Enforce physical bounds
    T_wb = min(T_wb, T_db)    # wet-bulb <= dry-bulb
    T_wb = max(T_wb, T_dp)   # wet-bulb >= dew-point

    return T_wb


def wet_bulb_array(T_db: np.ndarray, T_dp: np.ndarray,
                   pressure: np.ndarray) -> np.ndarray:
    """Vectorised wet-bulb calculation using native NumPy operations."""
    T_db = np.asarray(T_db, dtype=float)
    T_dp = np.asarray(T_dp, dtype=float)

    # Warn once if any values are outside Stull formula validity range
    out_of_range = (T_db < -20) | (T_db > 50)
    if out_of_range.any():
        count = out_of_range.sum()
        warnings.warn(
            f"{count} hour(s) have T_db outside Stull formula validity range "
            f"(-20 to 50°C). Wet-bulb accuracy may be degraded for those hours.",
            stacklevel=2,
        )

    # RH from Magnus formula (Lawrence 2005)
    b = 17.368
    c = 238.88
    RH = 100.0 * np.exp(b * T_dp / (c + T_dp)) / np.exp(b * T_db / (c + T_db))
    RH = np.clip(RH, 1.0, 99.0)

    # Stull (2011) eq. 1
    T_wb = (
        T_db * np.arctan(0.151977 * (RH + 8.313659) ** 0.5)
        + np.arctan(T_db + RH)
        - np.arctan(RH - 1.676331)
        + 0.00391838 * RH ** 1.5 * np.arctan(0.023101 * RH)
        - 4.686035
    )

    # Enforce physical bounds
    T_wb = np.minimum(T_wb, T_db)   # wet-bulb <= dry-bulb
    T_wb = np.maximum(T_wb, T_dp)   # wet-bulb >= dew-point

    return T_wb
