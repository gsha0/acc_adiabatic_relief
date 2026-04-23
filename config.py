# =============================================================================
# ACC Adiabatic Relief Tool - Configuration
# =============================================================================
# All user-adjustable inputs are here. Edit this file for each project.

# --- File Paths --------------------------------------------------------------
EPW_FILE    = "AUS_NSW_Horsley.Equestrian.Centre.947600_TMYx.2011-2025.epw"   # EnergyPlus weather file
LOAD_FILE   = "ODC_25pct.xlsx"         # IESVE VistaPro export (kW)
OUTPUT_FILE = "results_hourly.csv"                # Output CSV path

# --- Plant Configuration -----------------------------------------------------
N_CHILLERS  = 9        # Number of identical chillers in the plant

# --- Chiller Plant Config Examples -------------------------------------------
# N=33 when DC Load = 90%-100%
# N=25 when DC Load = 75%
# N=17 when DC Load = 50%
# N=9 when DC Load = 25%
# Note: the number of chillers is a user input that can be adjusted to simulate different plant configurations, representing staging to match #part load conditions.

# --- Chiller Rated Parameters ------------------------------------------------
# Copy from the "VE Data Inputs" sheet of the IES ACC coefficients spreadsheet
Q_RAT_KW    = 2200    # Rated cooling capacity (kW) per chiller
COP_RAT     = 4.8 # Rated COP at rated conditions
T_LET_RAT   = 24     # Rated CHW supply temp, leaving evaporator (°C)
                        # Used ONLY to normalise the performance curves — do not
                        # change unless the chiller datasheet rating point changes.
T_LET_DES   = 24     # Design CHW supply temp — the operating setpoint used in
                        # the simulation (°C). Set independently of T_LET_RAT when
                        # the plant runs at a different temperature than the rated
                        # condition (e.g. warmer CHWS to improve efficiency).
T_ODB_RAT   = 32    # Rated outdoor dry-bulb temperature (°C)
FAN_POWER_KW = 0    # Condenser fan power per chiller (kW)
                        # (included within EIR curves per IESVE convention)

# --- Curve Coefficients ------------------------------------------------------
# Copy from "Curve Coefficients & Validation" sheet of the IES spreadsheet.
# Format: [C00, C10, C20, C01, C02, C11]

# Cooling capacity as a function of T_let and T_odb: fCAPtt(T_let, T_odb)
CAP_FTT = {
    "C00":  1.28968664,
    "C10":  0,
    "C20":  0.00086060,
    "C01":  0,
    "C02": -0.00136091,
    "C11":  0.00208111,
}

# EIR as a function of T_let and T_odb: fEIRtt(T_let, T_odb)
EIR_FTT = {
    "C00":  0.27625998,
    "C10":  0,
    "C20": -0.00047595,
    "C01":  0,
    "C02":  0.00106207,
    "C11": -0.00011086,
}

# EIR as a function of PLR and (T_odb - T_let): fEIRpt(PLR, dT)
EIR_FPT = {
    "C00":  0.00144273,
    "C10":  0.34459557,
    "C20":  0.66002771,
    "C01":  0.00080729,
    "C02": -0.00005261,
    "C11": -0.00117824,
}

# --- Adiabatic Relief Parameters ---------------------------------------------
T_SWITCH    = 31.0      # Ambient DBT threshold to activate wetted pads (°C)
ETA_SAT     = 0.78      # Pad saturation efficiency (0-1).
                        # Typical range: 0.65-0.80.
                        # Source: manufacturer data.

# --- Chiller Plant Environment Parameters ------------------------------------
# Condenser Coil Inlet Temperature Offset — applied to the temperature at the
# chiller inlet (after any adiabatic pad cooling) to account for semi-enclosed
# plant rooms where heat rejection exhaust mixes with incoming air.
# When pads are OFF this is added to the outdoor dry-bulb;
# when pads are ON it is added to the pad outlet temperature.
# Set to 0.0 for a fully open outdoor installation.
COND_INLET_T_OFFSET = 5.0   # °C  (default 5 °C)

# --- Operating Limits --------------------------------------------------------
PLR_MIN     = 0.10      # Minimum stable part-load ratio (flag only, no cutoff)
                        # Hours below this are flagged in output for review.
PLR_MIN_CALC = 0.80     # Minimum PLR used in EIR part-load curve evaluation.
                        # When actual PLR < PLR_MIN_CALC (and chiller is on),
                        # the curve is evaluated at PLR_MIN_CALC instead,
                        # modelling minimum stable-load power draw.
COP_MAX     = 30        # Hard upper limit on chiller COP (dimensionless).
                        # Applied as an EIR floor (EIR >= 1/COP_MAX) at the
                        # last step of the power calculation.
