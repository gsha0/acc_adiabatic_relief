# =============================================================================
# EPW Reader
# Parses an EnergyPlus Weather file and returns hourly DBT, DPT, RH.
# Wet-bulb temperature is derived via psychrometric calculation (see psychro.py).
# EPW data rows begin after the 8-line header.
# Column indices (0-based): 6=DBT, 7=DPT, 8=RH, pressure=9
# =============================================================================

import pandas as pd


def read_epw(filepath: str) -> pd.DataFrame:
    """
    Parse EPW file. Returns DataFrame with 8760 rows and columns:
        month, day, hour, T_odb (°C), T_dp (°C), RH (%), pressure (Pa)
    Hour is 1-indexed (1..24) as per EPW convention.
    """
    rows = []
    with open(filepath, "r") as f:
        for i, line in enumerate(f):
            if i < 8:
                continue
            fields = line.strip().split(",")
            if len(fields) < 10:
                continue
            rows.append({
                "month":    int(fields[1]),
                "day":      int(fields[2]),
                "hour":     int(fields[3]),     # 1-24
                "T_odb":    float(fields[6]),   # Dry-bulb temp (°C)
                "T_dp":     float(fields[7]),   # Dew-point temp (°C)
                "RH":       float(fields[8]),   # Relative humidity (%)
                "pressure": float(fields[9]),   # Atmospheric pressure (Pa)
            })

    df = pd.DataFrame(rows)

    if len(df) not in (8760, 8784):
        raise ValueError(f"EPW parse yielded {len(df)} rows — expected 8760 (or 8784 for leap year).")

    return df.reset_index(drop=True)
