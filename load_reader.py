# =============================================================================
# Load Reader
# Parses the IESVE Vista hourly export format.
#
# Expected format (as exported by IESVE VistaPro):
#   Row 0: blank | blank | "CHWL total load (kW)"
#   Row 1: blank
#   Row 2: "Date" | "Time" | <system name>.aps
#   Row 3+: data rows — Date (forward-filled), Time (hh:mm:ss), load (kW)
#
# Time stamps are at mid-hour (00:30, 01:30 ... 23:30) = hours 1-24.
# The full year file will have 8760 data rows.
# =============================================================================

import pandas as pd
import numpy as np


def read_load(filepath: str) -> np.ndarray:
    """
    Parse IESVE Vista load export.
    Returns numpy array of 8760 load values in kW, ordered hour 1..8760.
    Raises ValueError if row count is unexpected.
    """
    df = pd.read_excel(filepath, header=None)

    # Data starts at row index 3 (0-based), column 2 holds the kW values
    load_col = df.iloc[3:, 2].reset_index(drop=True)
    load_kw   = pd.to_numeric(load_col, errors="coerce")

    nan_count = load_kw.isna().sum()
    if nan_count > 0:
        nan_rows = load_kw[load_kw.isna()].index.tolist()
        raise ValueError(
            f"Load file has {nan_count} non-numeric / missing value(s) at data row(s) "
            f"{nan_rows[:10]}{'...' if nan_count > 10 else ''}. "
            f"Check the IESVE export for blank or text cells in the load column."
        )

    load_kw = load_kw.values

    if len(load_kw) not in (8760, 8784):  # allow leap-year files too
        raise ValueError(
            f"Load file contains {len(load_kw)} data rows — expected 8760 (or 8784 for leap year). "
            f"Check file format."
        )

    return load_kw.astype(float)
