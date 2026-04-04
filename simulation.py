# =============================================================================
# Simulation Engine
# Runs the 8760-hour loop assembling all modules.
# Produces the hourly results DataFrame.
# =============================================================================

import numpy as np
import pandas as pd

from psychro   import wet_bulb_array
from adiabatic import effective_odb
from chiller_model import ChillerModel


MONTH_NAMES = {
    1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
    7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"
}


def run(epw: pd.DataFrame, load_kw: np.ndarray, chiller: ChillerModel,
        n_chillers: int, T_switch: float, eta_sat: float,
        T_let: float, PLR_min: float) -> pd.DataFrame:
    """
    Main simulation loop.

    Parameters
    ----------
    epw        : DataFrame from epw_reader.read_epw() — 8760 rows
    load_kw    : array of 8760 hourly total plant load values (kW)
    chiller    : ChillerModel instance (single unit)
    n_chillers : number of identical chillers in plant
    T_switch   : adiabatic activation threshold (°C)
    eta_sat    : pad saturation efficiency
    T_let      : design CHW supply temperature — the operating setpoint (°C).
                 Distinct from the rated value used to normalise the curves.
    PLR_min    : minimum PLR threshold for flagging (no cutoff applied)

    Returns
    -------
    DataFrame with one row per hour — all simulation outputs.
    """

    # Pre-compute wet-bulb for all 8760 hours
    T_wb_arr = wet_bulb_array(
        epw["T_odb"].values,
        epw["T_dp"].values,
        epw["pressure"].values,
    )

    records = []
    n_hours = len(epw)

    for i in range(n_hours):
        if i % 2000 == 0 and i > 0:
            print(f"    {i:,}/{n_hours:,} hours...")

        row   = epw.iloc[i]
        T_odb = row["T_odb"]
        T_wb  = T_wb_arr[i]
        Q_plant_demand = load_kw[i]   # Total plant load (kW)

        # --- Adiabatic pre-cooling -------------------------------------------
        T_odb_eff, adi_active = effective_odb(T_odb, T_wb, T_switch, eta_sat)
        T_depression = T_odb - T_odb_eff   # Positive when pads active

        # --- Per-chiller demand (load shared equally across N chillers) -------
        Q_chiller_demand = Q_plant_demand / n_chillers

        # --- Resolve CHW supply setpoint for this hour ------------------------
        # Currently a fixed design value. Future: derive T_let_h from a reset
        # strategy (e.g. OAT-based reset, IT part-load ratio, schedule) here.
        T_let_h = T_let

        # --- Run chiller model (adiabatic mode) -------------------------------
        res_adi = chiller.run(Q_chiller_demand, T_let_h, T_odb_eff)

        # --- Run chiller model (dry baseline — same load, raw T_odb) ----------
        res_dry = chiller.run(Q_chiller_demand, T_let_h, T_odb)

        # --- Scale single-chiller outputs to plant totals --------------------
        def plant(val): return val * n_chillers

        Q_plant_cap_adi  = plant(res_adi["Q_cap"])
        Q_plant_cap_dry  = plant(res_dry["Q_cap"])
        Q_plant_served   = plant(res_adi["Q_served"])
        Q_plant_unmet    = plant(res_adi["Q_unmet"])
        P_plant_adi      = plant(res_adi["P_total"])
        P_plant_dry      = plant(res_dry["P_total"])
        P_saving         = P_plant_dry - P_plant_adi   # +ve = saving

        # --- Flags -----------------------------------------------------------
        over_cap_flag = res_adi["over_capacity"]
        low_plr_flag  = (res_adi["PLR"] > 0) and (res_adi["PLR"] < PLR_min)

        records.append({
            # Time identifiers
            "month":               row["month"],
            "month_name":          MONTH_NAMES[row["month"]],
            "day":                 row["day"],
            "hour":                row["hour"],

            # Weather
            "T_odb_C":             round(T_odb, 2),
            "T_wb_C":              round(T_wb, 2),
            "T_wb_depression_C":   round(T_depression, 2),

            # Adiabatic state
            "adiabatic_active":    adi_active,
            "T_odb_eff_C":         round(T_odb_eff, 2),

            # Plant load
            "Q_plant_demand_kW":   round(Q_plant_demand, 1),
            "Q_plant_cap_adi_kW":  round(Q_plant_cap_adi, 1),
            "Q_plant_cap_dry_kW":  round(Q_plant_cap_dry, 1),
            "Q_plant_served_kW":   round(Q_plant_served, 1),
            "Q_plant_unmet_kW":    round(Q_plant_unmet, 1),

            # Per-chiller performance (adiabatic mode)
            "PLR":                 round(res_adi["PLR"], 4),
            "f_CAPtt":             round(res_adi["f_CAPtt"], 6),
            "f_EIRtt":             round(res_adi["f_EIRtt"], 6),
            "f_EIRpt":             round(res_adi["f_EIRpt"], 6),
            "EIR_adi":             round(res_adi["EIR"], 6),
            "COP_adi":             round(res_adi["COP"], 4),

            # Per-chiller performance (dry baseline)
            "EIR_dry":             round(res_dry["EIR"], 6),
            "COP_dry":             round(res_dry["COP"], 4),

            # Plant power (kW)
            "P_plant_adi_kW":      round(P_plant_adi, 1),
            "P_plant_dry_kW":      round(P_plant_dry, 1),
            "P_saving_kW":         round(P_saving, 1),

            # Energy (kWh — each row = 1 hour so kW = kWh)
            "E_plant_adi_kWh":     round(P_plant_adi, 1),
            "E_plant_dry_kWh":     round(P_plant_dry, 1),
            "E_saving_kWh":        round(P_saving, 1),

            # Flags
            "over_capacity_flag":  over_cap_flag,
            "low_PLR_flag":        low_plr_flag,
        })

    return pd.DataFrame(records)
