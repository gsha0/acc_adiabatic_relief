# =============================================================================
# ACC Adiabatic Relief Tool - Configuration
# =============================================================================
# All user-adjustable inputs are here. Edit this file for each project.

# --- File Paths --------------------------------------------------------------
EPW_FILE    = "AUS_NSW_Sydney_947670_IWEC.epw"   # EnergyPlus weather file
LOAD_FILE   = "Example_Chiller_Load.xlsx"         # IESVE Vista export (kW)
OUTPUT_FILE = "results_hourly.csv"                # Output CSV path

# --- Plant Configuration -----------------------------------------------------
N_CHILLERS  = 10        # Number of identical chillers in the plant

# --- Chiller Rated Parameters ------------------------------------------------
# Copy from the "VE Data Inputs" sheet of the IES ACC coefficients spreadsheet
Q_RAT_KW    = 786.6    # Rated cooling capacity (kW) per chiller
COP_RAT     = 2.844538 # Rated COP at rated conditions
T_LET_RAT   = 5.56     # Rated CHW supply temp, leaving evaporator (°C)
                        # Used ONLY to normalise the performance curves — do not
                        # change unless the chiller datasheet rating point changes.
T_LET_DES   = 5.56     # Design CHW supply temp — the operating setpoint used in
                        # the simulation (°C). Set independently of T_LET_RAT when
                        # the plant runs at a different temperature than the rated
                        # condition (e.g. warmer CHWS to improve efficiency).
T_ODB_RAT   = 40.56    # Rated outdoor dry-bulb temperature (°C)
FAN_POWER_KW = 24.6    # Condenser fan power per chiller (kW)
                        # (included within EIR curves per IESVE convention)

# --- Curve Coefficients ------------------------------------------------------
# Copy from "Curve Coefficients & Validation" sheet of the IES spreadsheet.
# Format: [C00, C10, C20, C01, C02, C11]

# Cooling capacity as a function of T_let and T_odb: fCAPtt(T_let, T_odb)
CAP_FTT = {
    "C00":  1.201400,
    "C10":  0.045081,
    "C20":  0.000215,
    "C01": -0.007392,
    "C02": -0.000047,
    "C11": -0.000370,
}

# EIR as a function of T_let and T_odb: fEIRtt(T_let, T_odb)
EIR_FTT = {
    "C00":  0.422279,
    "C10":  0.006181,
    "C20":  0.000307,
    "C01":  0.002750,
    "C02":  0.000344,
    "C11": -0.000610,
}

# EIR as a function of PLR and (T_odb - T_let): fEIRpt(PLR, dT)
EIR_FPT = {
    "C00":  0.035101,
    "C10":  0.524496,
    "C20":  0.433515,
    "C01":  0.000699,
    "C02":  0.000009,
    "C11": -0.000724,
}

# --- Adiabatic Relief Parameters ---------------------------------------------
T_SWITCH    = 30.0      # Ambient DBT threshold to activate wetted pads (°C)
ETA_SAT     = 0.85      # Pad saturation efficiency (0-1).
                        # Typical range: 0.80-0.90 for quality wetted media.
                        # Source: manufacturer pad spec or Evapco testing data.

# --- Operating Limits --------------------------------------------------------
PLR_MIN     = 0.10      # Minimum stable part-load ratio (flag only, no cutoff)
                        # Hours below this are flagged in output for review.
