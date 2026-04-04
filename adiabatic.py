# =============================================================================
# Adiabatic Pre-cooling Module
# Computes effective condenser inlet temperature after wetted pad depression.
#
# Physics:
#   The wetted pad process follows a constant wet-bulb line on the
#   psychrometric chart (adiabatic saturation). The leaving dry-bulb
#   temperature is:
#
#       T_odb_eff = T_odb - eta_sat * (T_odb - T_wb)
#
#   where eta_sat is pad saturation efficiency (dimensionless, 0-1).
#   When T_odb <= T_switch, pads are off and T_odb_eff = T_odb.
#
# Reference: EnergyPlus Engineering Reference — Evaporative Coolers;
#            Evapco Adiabatic Pad Saturation White Paper (2018).
# =============================================================================


def effective_odb(
    T_odb:    float,   # Ambient dry-bulb temperature (°C)
    T_wb:     float,   # Ambient wet-bulb temperature (°C)
    T_switch: float,   # Activation threshold (°C)
    eta_sat:  float,   # Pad saturation efficiency (dimensionless)
) -> tuple[float, bool]:
    """
    Returns (T_odb_eff, adiabatic_active).

    T_odb_eff : effective condenser inlet temp after pad depression (°C).
    adiabatic_active : True when pads are operating this hour.

    Note: T_odb_eff will never be below T_wb (physically impossible).
    """
    if T_odb > T_switch:
        depression  = eta_sat * (T_odb - T_wb)
        T_odb_eff   = max(T_odb - depression, T_wb)  # physical floor
        return T_odb_eff, True
    else:
        return T_odb, False
