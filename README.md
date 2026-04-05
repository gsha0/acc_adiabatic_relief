# ACC Adiabatic Relief Tool
### Air-Cooled Chiller + Wetted Pad Pre-cooling — Hourly Energy Simulation

---

## What This Tool Does

Air-cooled chillers lose capacity and efficiency as outdoor temperature rises. Some chillers address this with **adiabatic relief** such as wetted evaporative pads upstream of the condenser coil that pre-cool incoming air before it reaches the refrigerant circuit. This setup is widely used in data centers to reduce chiller energy.

BEM software such as IESVE does not natively model this configuration. This tool fills that gap.

It calculates an air-cooled chiller plant hour by hour across a full year (8,760 hours), using:
- A real weather file for your site (EnergyPlus `.epw` format)
- Your actual chiller load profile (exported from IESVE VistaPro)
- Default performance curves or curves from your chiller manufacturer's data
- An adiabatic pre-cooling model that activates when outdoor temperature exceeds a threshold you set

For every hour it calculates capacity, power, and COP for both **adiabatic mode** (pads active) and a **dry baseline** (pads never active), so you can directly quantify the energy benefit.

The physics mirrors the IESVE Electric Air-Cooled Chiller model using the same three bi-quadratic performance curves and the same normalisation convention.

This tool is authored by Claude.

---

## Before You Start — What You Need

| Item | Where to get it |
|---|---|
| Python 3.10 or later | [python.org/downloads](https://www.python.org/downloads/) |
| An EnergyPlus weather file (`.epw`) for your site | [climate.onebuilding.org](https://climate.onebuilding.org) |
| A chiller load export from IESVE VistaPro (`.xlsx`) | See export guide below |
| Chiller curve coefficients | IES Air-Cooled Chiller Curve Coefficients Spreadsheet (metric) for custom curves |

**You do not need to know how to code.** All inputs go in a single plain-text file (`config.py`). The only command you run is one line in a terminal.

---

## File Structure

```
acc_adiabatic_tool/
│
├── config.py          → You edit this — all inputs live here
├── main.py            — Run this to start the simulation
├── visualize.py       — Run this to generate the interactive dashboard
│
├── epw_reader.py      — Reads the weather file
├── psychro.py         — Calculates wet-bulb temperature
├── chiller_model.py   — Chiller performance model (IESVE bi-quadratic curves)
├── adiabatic.py       — Wetted pad pre-cooling physics
├── load_reader.py     — Reads your IESVE load export
├── simulation.py      — Runs the 8,760-hour loop
│
├── tests/             — Automated test suite (run with pytest)
└── requirements.txt   — Python dependencies list
```

Place your `.epw` weather file and `.xlsx` load file in the same folder as `config.py`. Output (`results_hourly.csv`) is written to the same folder.

---

## Quick Start

### 1. Install Python (first time only)

Download and install Python 3.10+ from [python.org/downloads](https://www.python.org/downloads/).
On Windows, tick **"Add Python to PATH"** during installation.

### 2. Install dependencies (first time only)

Open a terminal, navigate to the tool folder, and run:

```
pip install -r requirements.txt
```

Or install manually:

```
pip install pandas openpyxl numpy plotly
```

On Mac, use `pip3` if `pip` is not found.

### 3. Get your weather file

Download a `.epw` file from [climate.onebuilding.org](https://climate.onebuilding.org) and place it in the tool folder.

### 4. Export your load from IESVE VistaPro

1. Open your results file in VistaPro
2. Select **"CHWL total load (kW)"** as the variable
3. Set the time period to **Annual**, interval to **Hourly**
4. Export to Excel (`.xlsx`) and place in the tool folder

Expected file structure:

```
Row 1:  [blank]    [blank]    CHWL total load (kW)
Row 2:  [blank]    [blank]    [blank]
Row 3:  Date       Time       YourModel.aps
Row 4:  Fri 01/Jan 00:30:00   6000
Row 5:  [blank]    01:30:00   6100
...
```

The file must have 8,760 data rows (or 8,784 for a leap year).

### 5. Get your chiller curve coefficients

From the **IES Air-Cooled Chiller Curve Coefficients Spreadsheet (Metric)**:
- Copy rated parameters from the **"VE Data Inputs"** tab
- Copy the 18 curve coefficients (6 each for CAP_FTT, EIR_FTT, EIR_FPT) from the **"Curve Coefficients & Validation"** tab

### 6. Edit config.py

Open `config.py` in any text editor and fill in your values. Every input is commented.

### 7. Run

```
python main.py        # Windows
python3 main.py       # Mac / Linux
```

The tool prints progress and an annual/monthly summary to the terminal, then writes `results_hourly.csv`. A typical run takes about 2 seconds.

---

## Configuration Reference

### File Paths

```python
EPW_FILE    = "AUS_NSW_Sydney_947670_IWEC.epw"
LOAD_FILE   = "Example_Chiller_Load.xlsx"
OUTPUT_FILE = "results_hourly.csv"
```

Change the file names to match what you have. Files must be in the same folder as `config.py`.

---

### Plant Configuration

```python
N_CHILLERS  = 10
```

All chillers are assumed identical, sharing load equally.

---

### Chiller Rated Parameters

```python
Q_RAT_KW     = 786.6     # Rated cooling capacity per chiller (kW)
COP_RAT      = 2.844538  # Rated COP at rated conditions
T_LET_RAT    = 5.56      # Rated CHW supply temperature (°C) — for curve normalisation only
T_LET_DES    = 5.56      # Operating CHW supply setpoint (°C) — used in simulation
T_ODB_RAT    = 40.56     # Rated outdoor dry-bulb temperature (°C)
FAN_POWER_KW = 24.6      # Condenser fan power per chiller (kW)
```

`T_LET_RAT` and `T_LET_DES` can differ — set `T_LET_RAT` to the datasheet rating point and `T_LET_DES` to the actual operating setpoint.

> Fan power is embedded in the EIR curves per IESVE convention and does not add separately to the total.

---

### Curve Coefficients

Three sets of six coefficients each. Copy from the **"Curve Coefficients & Validation"** tab of the IES spreadsheet:

```python
CAP_FTT = {"C00": ..., "C10": ..., "C20": ..., "C01": ..., "C02": ..., "C11": ...}
EIR_FTT = {"C00": ..., "C10": ..., "C20": ..., "C01": ..., "C02": ..., "C11": ...}
EIR_FPT = {"C00": ..., "C10": ..., "C20": ..., "C01": ..., "C02": ..., "C11": ...}
```

---

### Adiabatic Relief Parameters

```python
T_SWITCH = 30.0   # Outdoor DBT threshold to activate pads (°C)
ETA_SAT  = 0.85   # Pad saturation efficiency (0.0–1.0)
```

**T_SWITCH** — pads activate when outdoor dry-bulb exceeds this value.

**ETA_SAT** — how effectively pads cool air toward wet-bulb temperature. Real pads typically achieve 0.80–0.90; check your manufacturer's pad spec. The effective inlet temperature is:

```
T_eff = T_odb − η_sat × (T_odb − T_wb)
```

T_eff is always floored at T_wb (thermodynamic limit).

---

### Operating Limits

```python
PLR_MIN = 0.10
```

Hours with PLR below this are flagged with `low_PLR_flag = True` in the output. Diagnostic only — the simulation does not cut off the chiller.

---

## Output Columns

The output CSV has one row per hour (8,760 rows).

### Time

| Column | Description |
|---|---|
| `month` | Month number (1–12) |
| `month_name` | Abbreviated month name |
| `day` | Day of month |
| `hour` | Hour of day (1–24, EPW convention) |

### Weather

| Column | Description |
|---|---|
| `T_odb_C` | Outdoor dry-bulb temperature (°C) |
| `T_wb_C` | Wet-bulb temperature (°C), derived from dew-point and RH |
| `T_wb_depression_C` | Dry-bulb minus wet-bulb (°C). Zero when pads are off. |

### Adiabatic State

| Column | Description |
|---|---|
| `adiabatic_active` | `True` when pads are on (T_odb > T_SWITCH) |
| `T_odb_eff_C` | Effective condenser inlet temperature after pad depression (°C) |

### Plant Load

| Column | Description |
|---|---|
| `Q_plant_demand_kW` | Total cooling load demanded (kW) |
| `Q_plant_cap_adi_kW` | Plant capacity in adiabatic mode (kW) |
| `Q_plant_cap_dry_kW` | Plant capacity in dry mode (kW) |
| `Q_plant_served_kW` | Cooling delivered (kW) — equals demand unless over-capacity |
| `Q_plant_unmet_kW` | Unmet load (kW) — non-zero only when demand exceeds capacity |

### Per-Chiller Performance (adiabatic mode)

| Column | Description |
|---|---|
| `PLR` | Part-load ratio (0.0–1.0) |
| `f_CAPtt` | Capacity curve value |
| `f_EIRtt` | EIR temperature-dependence curve value |
| `f_EIRpt` | EIR part-load-dependence curve value |
| `EIR_adi` | Combined Electric Input Ratio, adiabatic mode |
| `COP_adi` | COP, adiabatic mode |

### Dry Baseline Comparison

| Column | Description |
|---|---|
| `EIR_dry` | EIR using raw T_odb (no pad assist) |
| `COP_dry` | COP using raw T_odb |

### Power and Energy

| Column | Description |
|---|---|
| `P_plant_adi_kW` | Plant power consumption, adiabatic mode (kW) |
| `P_plant_dry_kW` | Plant power consumption, dry baseline (kW) |
| `P_saving_kW` | Power saving = dry minus adiabatic (kW) |
| `E_plant_adi_kWh` | Energy consumed, adiabatic mode (kWh) |
| `E_plant_dry_kWh` | Energy consumed, dry baseline (kWh) |
| `E_saving_kWh` | Energy saving this hour (kWh) |

### Flags

| Column | Description |
|---|---|
| `over_capacity_flag` | `True` when demand exceeds plant capacity |
| `low_PLR_flag` | `True` when PLR < PLR_MIN |

---

## Visualisation

After running the simulation, generate an interactive HTML dashboard:

```
python visualize.py        # Windows
python3 visualize.py       # Mac / Linux
```

This writes `results_dashboard.html` to the same folder as your results CSV. Open it in any browser — no internet connection required after the first load (Plotly is fetched from CDN once).

### What the Dashboard Shows

The dashboard has a sticky toolbar at the top with toggle buttons to show or hide each chart individually. All charts are full-width and fully interactive: zoom, pan, hover for exact values, and click legend items to toggle series on and off.

**Chart 1 — Energy Savings: Calendar Heatmap**

A 365 × 24 grid where each cell represents one hour of the year. Colour encodes hourly energy saving (kWh): light blue at zero, graduating through yellow, orange, and deep red at peak savings. The Y-axis shows month labels; the X-axis shows hour of day. Hover to see the exact date, hour, and saving.

**Chart 2 — COP vs Outdoor Dry-Bulb Temperature**

A scatter of all 8,760 hours plotted as COP against outdoor temperature. Two overlapping point clouds are shown: dry baseline (orange) and adiabatic (blue). Below the activation threshold the clouds coincide; above it the blue cloud pulls upward, showing the COP improvement from pad cooling. A dashed vertical line marks T_SWITCH. Hover to see temperature, COP, date, and hour.

**Chart 3 — Monthly Energy Consumption & Savings**

Grouped bar chart with three bars per month: dry baseline energy (grey), adiabatic energy (blue), and the saving (green). The annual saving percentage is annotated in the top-right corner.

**Chart 4 — Psychrometric Chart: Pad Activation**

All 8,760 hours plotted as dry-bulb vs wet-bulb temperature. Grey points are hours when pads were off; blue points are hours when pads were active. A dotted diagonal line marks the saturation limit (T_wb = T_db). A dashed vertical line marks T_SWITCH. The spread of blue points shows the wet-bulb depression available during active hours. Hover to see temperatures, date, and hour.

---

## Over-Capacity Handling

Mirrors IESVE behaviour:
- Demand ≤ capacity → served in full, PLR calculated normally
- Demand > capacity → plant runs at full output, shortfall recorded in `Q_plant_unmet_kW`, simulation continues

No energy is invented to serve unmet load. Over-capacity hours are the same signal as IESVE's Unmet Load Hours.

---

## Frequently Asked Questions

**The adiabatic saving seems low — is something wrong?**
Check the terminal output for the number of adiabatic-active hours. If it's low (e.g. fewer than 100 hrs/yr), the climate has few hours above your T_switch. Also check `T_wb_depression_C` in the CSV — a small wet-bulb depression in those hours means high humidity limits the available benefit. Both are real physical constraints.

**My load file has a different column name — will it still work?**
Yes. The tool reads load values by position (third column from row 4), not by column header.

**Can I use multiple chiller types?**
Not in the current version. All chillers are assumed identical.

**What if my plant uses CHWS temperature reset?**
The current version holds T_let constant at `T_LET_DES`. This is a simplification; for data centres with fixed CHWS setpoints the impact is negligible.

**The tool printed an error about non-numeric values in the load file.**
Your IESVE export has blank or text cells in the load column. Open the Excel file, find the affected rows, and remove or fill them before re-running.

**The tool warned about T_db outside Stull formula range.**
The wet-bulb formula is validated to −20°C–50°C. Hours outside this range (e.g. extreme heat in arid climates) may have slightly reduced accuracy (formula accuracy is ±0.65°C within range).

---

## Technical Reference

### Bi-Quadratic Curve Form

All three curves use the same form, consistent with IESVE and ASHRAE:

```
f(x, y) = (C00 + C10·x + C20·x² + C01·y + C02·y² + C11·x·y) / C_norm
```

C_norm is auto-computed so each curve equals 1.0 at rated conditions.

| Curve | x | y |
|---|---|---|
| fCAPtt — capacity vs temperature | T_let (°C) | T_odb_eff (°C) |
| fEIRtt — EIR vs temperature | T_let (°C) | T_odb_eff (°C) |
| fEIRpt — EIR vs part-load | PLR | T_odb_eff − T_let (°C) |

### Wet-Bulb Calculation

Stull (2011) empirical formula. RH is back-derived from dry-bulb and dew-point via the Magnus equation. Physical bounds enforced: T_wb ≤ T_odb and T_wb ≥ T_dp. Accuracy ±0.65°C over −20°C to +50°C, 5%–99% RH. A warning is printed if any hours fall outside this range.

### Power Calculation

```
EIR       = EIR_rated × fEIRtt × fEIRpt
COP       = 1 / EIR
P_chiller = Q_served × EIR          (kW)
P_plant   = P_chiller × N_chillers  (kW)
```

---

## Running the Tests

A pytest test suite covers the core physics modules:

```
pip install pytest
pytest tests/ -v
```

Tests cover psychrometric bounds, curve normalisation, over-capacity clamping, energy balance, and adiabatic depression logic.

---

## Dependencies

| Library | Version | Purpose |
|---|---|---|
| `pandas` | ≥1.3 | Excel I/O, data manipulation |
| `openpyxl` | ≥3.0 | Excel engine |
| `numpy` | ≥1.20 | Numerical array operations |
| `plotly` | ≥5.0 | Interactive HTML dashboard (`visualize.py`) |

Install: `pip install -r requirements.txt`
Requires Python 3.10+.

---

## References

- IESVE ApacheHVAC Electric Air-Cooled Chiller model documentation (ve2021)
- Stull, R. (2011). *Wet-Bulb Temperature from Relative Humidity and Air Temperature*. Journal of Applied Meteorology and Climatology, 50(11), 2267–2269.
- Lawrence, M.G. (2005). *The Relationship between Relative Humidity and the Dewpoint Temperature*. Bulletin of the American Meteorological Society, 86(2), 225–233.
- Evapco (2018). *Adiabatic Fluid Coolers & Refrigerant Condensers: Impact of Adiabatic Pad Saturation Efficiency*.
- EnergyPlus Engineering Reference — Evaporative Coolers.
