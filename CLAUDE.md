# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Tool Does

This is a Python-based hourly energy simulation tool for air-cooled chillers with adiabatic (wetted pad) pre-cooling. It runs an 8,760-hour annual simulation comparing two scenarios side-by-side every hour: **adiabatic mode** (pads active above a threshold temperature) vs. a **dry baseline** (pads never active). The goal is to quantify annual energy savings from adiabatic pre-cooling in data centre applications.

The physics mirrors the IESVE ApacheHVAC Electric Air-Cooled Chiller model using three bi-quadratic performance curves (capacity, EIR-vs-temperature, EIR-vs-part-load).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest   # not in requirements.txt; needed for tests

# Run simulation (reads config.py, writes timestamped CSV + appends run_log.csv)
python main.py

# Generate interactive HTML dashboard from most recent results CSV
python visualize.py

# Run all tests
pytest tests/ -v

# Run a single test file
pytest tests/test_chiller_model.py -v

# Run a single test by name
pytest tests/test_chiller_model.py::TestChillerRun::test_energy_balance -v
```

## Architecture

### Data Flow

```
config.py
    ↓
main.py  →  validate_config()
    ↓
epw_reader.py   →  DataFrame (T_odb, T_dp, RH, pressure, month/day/hour)
load_reader.py  →  numpy array (8760 kW values, positional read from xlsx col 2 row 3+)
ChillerModel    ←  config.py curve coefficients (C_norm pre-computed at __init__)
    ↓
simulation.run()  →  8760-row DataFrame
    ↓
Timestamped CSV + run_log.csv
    ↓ (separately)
visualize.py  →  results_dashboard.html
```

### Module Responsibilities

- **`config.py`** — all user inputs; the only file end-users edit. No logic.
- **`main.py`** — entry point: validates config, loads data, builds `ChillerModel`, calls `simulation.run()`, prints summary, writes outputs.
- **`simulation.py`** — the 8,760-hour loop. Each iteration calls `effective_odb()` then `ChillerModel.run()` twice (adiabatic and dry), scales single-chiller results by `N_CHILLERS`, and assembles the output row.
- **`chiller_model.py`** — `ChillerModel` class implementing the IESVE bi-quadratic curves. At `__init__`, normalisation constants (`_cnorm_cap`, `_cnorm_eir`, `_cnorm_pt`) are pre-computed so each curve evaluates to 1.0 at rated conditions. The `run()` method handles zero/negative demand (chiller off) and over-capacity clamping (PLR floored at 1.0, unmet load returned separately).
- **`adiabatic.py`** — `effective_odb()`: returns `(T_odb_eff, adiabatic_active)`. Activation is `T_odb > T_switch` (strict greater-than). T_eff is floored at T_wb as a physical constraint.
- **`psychro.py`** — wet-bulb via Stull (2011). Both scalar (`wet_bulb`) and vectorised (`wet_bulb_array`) implementations. Wet-bulb is pre-computed for all 8,760 hours before the loop runs.
- **`epw_reader.py`** — skips 8-line EPW header, reads fixed column positions (6=DBT, 7=DPT, 8=RH, 9=pressure). Hours are 1-indexed (1..24) per EPW convention.
- **`load_reader.py`** — reads IESVE VistaPro xlsx by position (column 2, starting row index 3). Column headers are ignored; load values are validated to be fully numeric.
- **`visualize.py`** — reads the most recent `*_hourly_*.csv` file from the working directory. Generates four interactive Plotly charts in a single HTML file.

### Key Design Decisions

**`T_cond_offset` is applied after pad cooling, not before.** The `T_SWITCH` comparison and adiabatic depression formula always use raw outdoor air temperature. Only the temperature entering the chiller performance curves is shifted: `T_chiller_inlet = T_odb_eff + T_cond_offset`. This means enclosure heat recirculation stacks on top of pad cooling.

**`PLR_MIN_CALC` is a curve-evaluation floor, not a simulation cutoff.** When actual PLR is below `PLR_MIN_CALC`, the EIR part-load curve (`fEIRpt`) is evaluated at `PLR_MIN_CALC` instead, modelling minimum stable-load cycling. The recorded PLR in the output CSV is always the true value.

**Dual-mode comparison runs every hour.** The dry baseline is not a separate run — `ChillerModel.run()` is called twice per hour with the same demand: once with `T_chiller_inlet` (adiabatic), once with `T_odb + T_cond_offset` (dry). This ensures the comparison is exact.

**No pytest dependency in `requirements.txt`.** Tests use pytest but it is not listed as a runtime dependency.

**Load is read positionally, not by header name.** `load_reader.py` always takes column index 2 starting at row index 3, regardless of column headers in the xlsx file.

## Bi-Quadratic Curve Form

All three curves (CAP_FTT, EIR_FTT, EIR_FPT) use:

```
f(x, y) = (C00 + C10·x + C20·x² + C01·y + C02·y² + C11·x·y) / C_norm
```

Where C_norm is auto-computed so the curve equals 1.0 at rated conditions. Variable inputs per curve:

| Curve | x | y |
|---|---|---|
| `fCAPtt` | `T_let` (°C) | `T_chiller_inlet` (°C) |
| `fEIRtt` | `T_let` (°C) | `T_chiller_inlet` (°C) |
| `fEIRpt` | `PLR` | `T_chiller_inlet − T_let` (°C) |

## Output Files

Each `main.py` run writes:
- `YYYY-MM-DD_hourly_HHMMSS.csv` — 8,760-row hourly results (timestamped, never overwritten)
- `run_log.csv` — appends the printed summary (running log across all runs)

`visualize.py` reads the most recent `*_hourly_*.csv` in the working directory and writes `results_dashboard.html`.

## Testing Approach

Tests in `tests/` cover physics invariants and energy balance, not integration:
- `test_psychro.py` — T_wb bounds (never above T_db, never below T_dp), saturated air, out-of-range warning
- `test_adiabatic.py` — activation threshold (strict `>`), depression formula, physical floor at T_wb
- `test_chiller_model.py` — curve normalisation (must equal 1.0 at rated), over-capacity clamping, energy balance (`P = Q × EIR`), COP at rated conditions

`conftest.py` only adds the project root to `sys.path` so modules can be imported without installation.
