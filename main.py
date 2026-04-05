# =============================================================================
# ACC Adiabatic Relief Tool — Main Entry Point
# =============================================================================
# Usage:
#   1. Place your EPW file and IESVE load export (.xlsx) in the same folder.
#   2. Edit config.py with chiller parameters, file paths, and plant settings.
#   3. Run:  python main.py
#   4. Results written to the CSV file specified in config.py.
# =============================================================================

import sys
import os
import time

import pandas as pd

import config
from __version__   import __version__
from epw_reader    import read_epw
from load_reader   import read_load
from chiller_model import ChillerModel
from simulation    import run


def validate_config():
    """Check config values for obvious errors before running the simulation."""
    errors = []

    if not os.path.isfile(config.EPW_FILE):
        errors.append(f"EPW file not found: '{config.EPW_FILE}'")
    if not os.path.isfile(config.LOAD_FILE):
        errors.append(f"Load file not found: '{config.LOAD_FILE}'")
    if config.N_CHILLERS < 1:
        errors.append(f"N_CHILLERS must be >= 1, got {config.N_CHILLERS}")
    if config.Q_RAT_KW <= 0:
        errors.append(f"Q_RAT_KW must be > 0, got {config.Q_RAT_KW}")
    if config.COP_RAT <= 0:
        errors.append(f"COP_RAT must be > 0, got {config.COP_RAT}")
    if not (0 < config.ETA_SAT <= 1.0):
        errors.append(f"ETA_SAT must be in (0, 1], got {config.ETA_SAT}")
    if config.T_SWITCH < -10 or config.T_SWITCH > 60:
        errors.append(f"T_SWITCH looks unreasonable: {config.T_SWITCH} °C (expected -10 to 60)")

    if errors:
        raise ValueError(
            "Config validation failed:\n  " + "\n  ".join(errors)
        )


def print_banner():
    print("=" * 65)
    print(f"  ACC Adiabatic Relief Tool v{__version__}")
    print("  Air-Cooled Chiller + Wetted Pad Pre-cooling Simulation")
    print("=" * 65)


def print_inputs():
    print("\n[INPUTS]")
    print(f"  EPW file       : {config.EPW_FILE}")
    print(f"  Load file      : {config.LOAD_FILE}")
    print(f"  N chillers     : {config.N_CHILLERS}")
    print(f"  Q_rat / unit   : {config.Q_RAT_KW} kW")
    print(f"  Plant capacity : {config.Q_RAT_KW * config.N_CHILLERS:.1f} kW (rated, dry)")
    print(f"  Rated COP      : {config.COP_RAT}")
    print(f"  T_let rated    : {config.T_LET_RAT} °C")
    print(f"  T_let design   : {config.T_LET_DES} °C")
    print(f"  T_odb rated    : {config.T_ODB_RAT} °C")
    print(f"  T_switch       : {config.T_SWITCH} °C")
    print(f"  Pad η_sat      : {config.ETA_SAT:.0%}")


def print_summary(df: pd.DataFrame):
    adi_hrs   = df["adiabatic_active"].sum()
    overcap   = df["over_capacity_flag"].sum()
    low_plr   = df["low_PLR_flag"].sum()

    E_adi     = df["E_plant_adi_kWh"].sum() / 1e3   # MWh
    E_dry     = df["E_plant_dry_kWh"].sum() / 1e3
    E_saving  = df["E_saving_kWh"].sum() / 1e3
    pct       = 100 * E_saving / E_dry if E_dry > 0 else 0

    Q_served  = df["Q_plant_served_kW"].sum() / 1e3  # MWh cooling
    Q_unmet   = df["Q_plant_unmet_kW"].sum()

    avg_cop_adi = df.loc[df["COP_adi"] > 0, "COP_adi"].mean()
    avg_cop_dry = df.loc[df["COP_dry"] > 0, "COP_dry"].mean()

    print("\n[ANNUAL SUMMARY]")
    print(f"  Adiabatic active hours    : {adi_hrs:,} hrs/yr")
    print(f"  Cooling delivered         : {Q_served:,.1f} MWh")
    print(f"  Unmet cooling load        : {Q_unmet:,.0f} kWh  "
          f"({'over-capacity hours: ' + str(overcap)})")
    print(f"  Energy — adiabatic mode   : {E_adi:,.1f} MWh")
    print(f"  Energy — dry baseline     : {E_dry:,.1f} MWh")
    print(f"  Annual energy saving      : {E_saving:,.1f} MWh  ({pct:.1f}%)")
    print(f"  Avg COP — adiabatic       : {avg_cop_adi:.3f}")
    print(f"  Avg COP — dry baseline    : {avg_cop_dry:.3f}")
    print(f"  Low-PLR hours flagged     : {low_plr:,} hrs")

    print("\n[MONTHLY ENERGY SAVING (MWh)]")
    monthly = (
        df.groupby("month_name")
          .agg(
              E_adi_MWh   =("E_plant_adi_kWh",  lambda x: x.sum()/1e3),
              E_dry_MWh   =("E_plant_dry_kWh",  lambda x: x.sum()/1e3),
              E_saving_MWh=("E_saving_kWh",      lambda x: x.sum()/1e3),
              adi_hrs     =("adiabatic_active",  "sum"),
          )
    )
    month_order = ["Jan","Feb","Mar","Apr","May","Jun",
                   "Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly = monthly.reindex([m for m in month_order if m in monthly.index])
    print(f"  {'Month':<6} {'Adiab(MWh)':>12} {'Dry(MWh)':>10} "
          f"{'Saving(MWh)':>12} {'Adi hrs':>8}")
    print("  " + "-"*52)
    for m, row in monthly.iterrows():
        print(f"  {m:<6} {row.E_adi_MWh:>12.1f} {row.E_dry_MWh:>10.1f} "
              f"{row.E_saving_MWh:>12.1f} {int(row.adi_hrs):>8}")


def main():
    print_banner()
    print_inputs()
    validate_config()

    # --- Load EPW ------------------------------------------------------------
    print("\n[LOADING] EPW weather file...")
    epw = read_epw(config.EPW_FILE)
    print(f"  OK — {len(epw)} hourly records")

    # --- Load demand ---------------------------------------------------------
    print("[LOADING] Chiller load file...")
    load_kw = read_load(config.LOAD_FILE)
    print(f"  OK — {len(load_kw)} hourly records, "
          f"peak={load_kw.max():,.0f} kW, mean={load_kw.mean():,.0f} kW")

    # --- Build chiller -------------------------------------------------------
    chiller = ChillerModel(
        Q_rat      = config.Q_RAT_KW,
        COP_rat    = config.COP_RAT,
        T_let_rat  = config.T_LET_RAT,
        T_odb_rat  = config.T_ODB_RAT,
        fan_power  = config.FAN_POWER_KW,
        cap_ftt    = config.CAP_FTT,
        eir_ftt    = config.EIR_FTT,
        eir_fpt    = config.EIR_FPT,
    )

    # --- Run simulation ------------------------------------------------------
    print("[RUNNING] Hourly simulation (8760 steps)...")
    t0 = time.time()
    df = run(
        epw        = epw,
        load_kw    = load_kw,
        chiller    = chiller,
        n_chillers = config.N_CHILLERS,
        T_switch   = config.T_SWITCH,
        eta_sat    = config.ETA_SAT,
        T_let      = config.T_LET_DES,
        PLR_min    = config.PLR_MIN,
    )
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s")

    # --- Print summary -------------------------------------------------------
    print_summary(df)

    # --- Write output --------------------------------------------------------
    print(f"\n[OUTPUT] Writing {config.OUTPUT_FILE}...")
    df.to_csv(config.OUTPUT_FILE, index=False)
    print(f"  OK — {len(df):,} rows × {len(df.columns)} columns")
    print("\nDone.")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"\n[ERROR] File not found: {e}")
        print("  Check the EPW_FILE and LOAD_FILE paths in config.py.")
        sys.exit(1)
    except ValueError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"\n[ERROR] Missing expected column or key: {e}")
        print("  Check that the EPW and load files are in the expected format.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
