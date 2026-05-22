"""Build ACC_Adiabatic_Relief.xlsx — native Excel formulas, no VBA."""

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.styles.numbers import FORMAT_NUMBER_00
from openpyxl.utils import get_column_letter, column_index_from_string
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.defined_name import DefinedName

# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------
GREY_FILL   = PatternFill("solid", fgColor="D9D9D9")
BLUE_FILL   = PatternFill("solid", fgColor="1F3864")   # dark navy
LBLUE_FILL  = PatternFill("solid", fgColor="BDD7EE")   # light blue header
GREEN_FILL  = PatternFill("solid", fgColor="E2EFDA")   # light green group
YELLOW_FILL = PatternFill("solid", fgColor="FFFF99")
RED_FILL    = PatternFill("solid", fgColor="FF0000")
WHITE_FILL  = PatternFill("solid", fgColor="FFFFFF")

def hdr_font(bold=True, color="FFFFFF", size=10):
    return Font(name="Calibri", bold=bold, color=color, size=size)

def body_font(bold=False, color="000000", size=10):
    return Font(name="Calibri", bold=bold, color=color, size=size)

def thin_border():
    s = Side(style="thin")
    return Border(left=s, right=s, top=s, bottom=s)

def set_cell(ws, row, col, value=None, formula=None,
             fill=None, font=None, align=None, border=None, num_fmt=None):
    c = ws.cell(row=row, column=col)
    if formula is not None:
        c.value = formula
    elif value is not None:
        c.value = value
    if fill:   c.fill   = fill
    if font:   c.font   = font
    if align:  c.alignment = align
    if border: c.border = border
    if num_fmt: c.number_format = num_fmt
    return c

CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT   = Alignment(horizontal="left",   vertical="center")
RIGHT  = Alignment(horizontal="right",  vertical="center")

# ---------------------------------------------------------------------------
# Named-range helper
# ---------------------------------------------------------------------------
def add_named_range(wb, name, sheet_name, cell_ref):
    """Add a workbook-scoped named range."""
    defn = DefinedName(name, attr_text=f"'{sheet_name}'!{cell_ref}")
    wb.defined_names[name] = defn

# ---------------------------------------------------------------------------
# Tab 1 — INPUTS
# ---------------------------------------------------------------------------
def build_inputs(wb):
    ws = wb.create_sheet("INPUTS")
    ws.sheet_view.showGridLines = False

    # Column widths
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 50

    def label_row(row, text, section=False):
        c = ws.cell(row=row, column=1, value=text)
        c.font = Font(name="Calibri", bold=True, size=10,
                      color="FFFFFF" if section else "1F3864")
        c.fill = BLUE_FILL if section else LBLUE_FILL
        c.alignment = LEFT
        ws.cell(row=row, column=2).fill = BLUE_FILL if section else LBLUE_FILL
        ws.cell(row=row, column=3).fill = BLUE_FILL if section else LBLUE_FILL

    def param_row(row, label, value, note="", num_fmt=None):
        c1 = ws.cell(row=row, column=1, value=label)
        c1.font = body_font()
        c1.alignment = LEFT
        c2 = ws.cell(row=row, column=2, value=value)
        c2.font = body_font(bold=True)
        c2.alignment = RIGHT
        c2.fill = YELLOW_FILL
        if num_fmt:
            c2.number_format = num_fmt
        if note:
            c3 = ws.cell(row=row, column=3, value=note)
            c3.font = Font(name="Calibri", size=9, italic=True, color="595959")
            c3.alignment = LEFT

    # Title
    ws.merge_cells("A1:C1")
    t = ws.cell(row=1, column=1,
                value="ACC Adiabatic Relief — Simulation Inputs")
    t.font = Font(name="Calibri", bold=True, size=14, color="FFFFFF")
    t.fill = BLUE_FILL
    t.alignment = CENTER
    ws.row_dimensions[1].height = 28

    # ---------- Section A: Plant Configuration ----------
    label_row(2, "A  PLANT CONFIGURATION", section=True)
    label_row(3, "Parameter",               section=False)
    ws.cell(row=3, column=2, value="Value").font = hdr_font(color="1F3864")
    ws.cell(row=3, column=3, value="Notes").font  = hdr_font(color="1F3864")

    params_A = [
        ("N_CHILLERS",       "N_CHILLERS",       9,      "Number of identical chillers in plant"),
        ("Q_RAT_KW",         "Q_RAT_KW",         2200,   "Rated cooling capacity per chiller (kW)"),
        ("COP_RAT",          "COP_RAT",          4.8,    "Rated COP at rated conditions"),
        ("T_LET_RAT",        "T_LET_RAT",        24,     "Rated leaving evaporator temp — curve normalisation only (°C)"),
        ("T_LET_DES",        "T_LET_DES",        24,     "Operating CHW supply setpoint used in simulation (°C)"),
        ("T_ODB_RAT",        "T_ODB_RAT",        32,     "Rated outdoor dry-bulb temp (°C)"),
        ("FAN_POWER_KW",     "FAN_POWER_KW",     0,      "Condenser fan power per chiller — embedded in EIR, typically 0 (kW)"),
    ]
    for i, (label, name, val, note) in enumerate(params_A):
        r = 4 + i
        param_row(r, label, val, note)
        add_named_range(wb, name, "INPUTS", f"$B${r}")

    # ---------- Section B: Adiabatic ----------
    r_b_hdr = 4 + len(params_A) + 1   # = 12
    label_row(r_b_hdr, "B  ADIABATIC RELIEF PARAMETERS", section=True)
    params_B = [
        ("T_SWITCH",             "T_SWITCH",             31,   "Pad activation threshold — pads ON when T_odb strictly > this (°C)"),
        ("ETA_SAT",              "ETA_SAT",              0.78, "Pad saturation efficiency (0–1); typical 0.65–0.80"),
        ("COND_INLET_T_OFFSET",  "COND_INLET_T_OFFSET",  5.0,  "Heat recirculation offset added after pad cooling (°C); 0 for open installation"),
    ]
    for i, (label, name, val, note) in enumerate(params_B):
        r = r_b_hdr + 1 + i
        param_row(r, label, val, note)
        add_named_range(wb, name, "INPUTS", f"$B${r}")

    # ---------- Section C: Operating Limits ----------
    r_c_hdr = r_b_hdr + 1 + len(params_B) + 1  # = 17
    label_row(r_c_hdr, "C  OPERATING LIMITS", section=True)
    params_C = [
        ("PLR_MIN",      "PLR_MIN",      0.10, "Min PLR threshold — hours below this are flagged (no cutoff applied)"),
        ("PLR_MIN_CALC", "PLR_MIN_CALC", 0.80, "Min PLR used in EIR part-load curve evaluation"),
        ("COP_MAX",      "COP_MAX",      30,   "Hard COP ceiling (enforced as EIR floor = 1/COP_MAX)"),
    ]
    for i, (label, name, val, note) in enumerate(params_C):
        r = r_c_hdr + 1 + i
        param_row(r, label, val, note)
        add_named_range(wb, name, "INPUTS", f"$B${r}")

    # ---------- Section D: Curve Coefficients ----------
    r_d_hdr = r_c_hdr + 1 + len(params_C) + 1  # = 22
    label_row(r_d_hdr, "D  BI-QUADRATIC CURVE COEFFICIENTS", section=True)

    coeff_headers = ["C00", "C10", "C20", "C01", "C02", "C11"]
    curve_defs = [
        ("CAP_FTT — Capacity vs (T_let, T_odb)",
         ["CAP_C00","CAP_C10","CAP_C20","CAP_C01","CAP_C02","CAP_C11"],
         [1.28968664, 0, 0.00086060, 0, -0.00136091, 0.00208111],
         "x = T_let (°C), y = T_odb / T_chiller_inlet (°C)"),
        ("EIR_FTT — EIR vs (T_let, T_odb)",
         ["EIR_C00","EIR_C10","EIR_C20","EIR_C01","EIR_C02","EIR_C11"],
         [0.27625998, 0, -0.00047595, 0, 0.00106207, -0.00011086],
         "x = T_let (°C), y = T_odb / T_chiller_inlet (°C)"),
        ("EIR_FPT — EIR vs (PLR, T_odb − T_let)",
         ["PT_C00","PT_C10","PT_C20","PT_C01","PT_C02","PT_C11"],
         [0.00144273, 0.34459557, 0.66002771, 0.00080729, -0.00005261, -0.00117824],
         "x = PLR, y = T_chiller_inlet − T_let (°C)"),
    ]

    # Header row for coefficients table
    r_coeff_hdr = r_d_hdr + 1
    ws.cell(row=r_coeff_hdr, column=1, value="Curve").font = hdr_font(color="1F3864")
    ws.cell(row=r_coeff_hdr, column=1).fill = LBLUE_FILL
    for ci, ch in enumerate(coeff_headers):
        col = 2 + ci   # cols B..G
        c = ws.cell(row=r_coeff_hdr, column=col, value=ch)
        c.font = hdr_font(color="1F3864")
        c.fill = LBLUE_FILL
        c.alignment = CENTER
        ws.column_dimensions[get_column_letter(col)].width = 14
    ws.cell(row=r_coeff_hdr, column=8, value="Notes").font = hdr_font(color="1F3864")
    ws.cell(row=r_coeff_hdr, column=8).fill = LBLUE_FILL
    ws.column_dimensions["H"].width = 42

    for ci_row, (curve_label, names, vals, note) in enumerate(curve_defs):
        r = r_coeff_hdr + 1 + ci_row
        ws.cell(row=r, column=1, value=curve_label).font = body_font()
        for col_off, (name, val) in enumerate(zip(names, vals)):
            col = 2 + col_off
            c = ws.cell(row=r, column=col, value=val)
            c.font = body_font(bold=True)
            c.fill = YELLOW_FILL
            c.alignment = CENTER
            c.number_format = "0.00000000"
            add_named_range(wb, name, "INPUTS", f"${get_column_letter(col)}${r}")
        ws.cell(row=r, column=8, value=note).font = Font(name="Calibri", size=9, italic=True, color="595959")

    # ---------- Section E: Normalisation Constants ----------
    r_e_hdr = r_coeff_hdr + 1 + len(curve_defs) + 1
    label_row(r_e_hdr, "E  NORMALISATION CONSTANTS  (auto-calculated — do not edit)", section=True)

    # These reference named ranges set above
    norm_rows = [
        ("EIR_RAT",    "EIR_RAT",    "=1/COP_RAT",   "Rated EIR = 1 / COP_RAT"),
        ("dT_RAT",     "dT_RAT",     "=T_ODB_RAT-T_LET_RAT", "Rated condenser-evap temperature difference"),
        ("C_NORM_CAP", "C_NORM_CAP",
         "=CAP_C00+CAP_C10*T_LET_RAT+CAP_C20*T_LET_RAT^2+CAP_C01*T_ODB_RAT+CAP_C02*T_ODB_RAT^2+CAP_C11*T_LET_RAT*T_ODB_RAT",
         "CAP_FTT evaluated at rated conditions (should ≈ C_NORM_CAP itself — verify ~1.0 before C_NORM division)"),
        ("C_NORM_EIR", "C_NORM_EIR",
         "=EIR_C00+EIR_C10*T_LET_RAT+EIR_C20*T_LET_RAT^2+EIR_C01*T_ODB_RAT+EIR_C02*T_ODB_RAT^2+EIR_C11*T_LET_RAT*T_ODB_RAT",
         "EIR_FTT evaluated at rated conditions"),
        ("C_NORM_PT",  "C_NORM_PT",
         "=PT_C00+PT_C10*1+PT_C20*1^2+PT_C01*dT_RAT+PT_C02*dT_RAT^2+PT_C11*1*dT_RAT",
         "EIR_FPT evaluated at PLR=1, dT=dT_RAT"),
    ]
    for i, (label, name, formula, note) in enumerate(norm_rows):
        r = r_e_hdr + 1 + i
        ws.cell(row=r, column=1, value=label).font = body_font()
        c2 = ws.cell(row=r, column=2, value=formula)
        c2.font = body_font(bold=True)
        c2.alignment = RIGHT
        c2.number_format = "0.000000"
        c2.fill = GREEN_FILL
        ws.cell(row=r, column=3, value=note).font = Font(name="Calibri", size=9, italic=True, color="595959")
        add_named_range(wb, name, "INPUTS", f"$B${r}")

    # Conditional format: red if C_NORM values <= 0
    norm_range_start = r_e_hdr + 3   # C_NORM_CAP row
    norm_range_end   = r_e_hdr + 5   # C_NORM_PT row
    ws.conditional_formatting.add(
        f"B{norm_range_start}:B{norm_range_end}",
        CellIsRule(operator="lessThanOrEqual", formula=["0"],
                   fill=PatternFill("solid", fgColor="FF0000"))
    )

    return ws


# ---------------------------------------------------------------------------
# Tab 2 — WEATHER_DATA
# ---------------------------------------------------------------------------
def build_weather(wb):
    ws = wb.create_sheet("WEATHER_DATA")
    ws.sheet_view.showGridLines = True

    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 18

    # Row 1: parameter type
    ws.cell(row=1, column=1, value="").font = body_font()
    ws.cell(row=1, column=2, value="").font = body_font()
    ws.cell(row=1, column=3, value="Dry-bulb temperature (°C)").font = hdr_font(color="1F3864")
    ws.cell(row=1, column=3).fill = LBLUE_FILL
    ws.cell(row=1, column=3).alignment = CENTER
    ws.cell(row=1, column=4, value="Wet-bulb temperature (°C)").font = hdr_font(color="1F3864")
    ws.cell(row=1, column=4).fill = LBLUE_FILL
    ws.cell(row=1, column=4).alignment = CENTER

    # Row 2: blank / sub-parameter (leave for user to fill file name)
    ws.cell(row=2, column=3, value="<paste EPW filename here>").font = Font(name="Calibri", size=9, italic=True, color="595959")
    ws.cell(row=2, column=4, value="<paste EPW filename here>").font = Font(name="Calibri", size=9, italic=True, color="595959")

    # Row 3: column headers
    for col, hdr in enumerate(["Date", "Time", "T_odb_C", "T_wb_C"], start=1):
        c = ws.cell(row=3, column=col, value=hdr)
        c.font = hdr_font(color="1F3864")
        c.fill = GREY_FILL
        c.alignment = CENTER

    # Row 4+: placeholder instruction
    ws.cell(row=4, column=1,
            value="← Paste IES VistaPro weather export here (DBT & WBT columns only, 8,760 rows from row 4)").font = Font(
        name="Calibri", size=9, italic=True, color="FF0000")

    # Freeze panes below header
    ws.freeze_panes = "A4"
    return ws


# ---------------------------------------------------------------------------
# Tab 3 — LOAD_DATA
# ---------------------------------------------------------------------------
def build_load(wb):
    ws = wb.create_sheet("LOAD_DATA")
    ws.sheet_view.showGridLines = True

    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 28

    # Row 1
    ws.cell(row=1, column=3, value="CHWL total load (kW)").font = hdr_font(color="1F3864")
    ws.cell(row=1, column=3).fill = LBLUE_FILL
    ws.cell(row=1, column=3).alignment = CENTER

    # Row 2
    ws.cell(row=2, column=3, value="<paste circuit/loop name here>").font = Font(name="Calibri", size=9, italic=True, color="595959")

    # Row 3
    for col, hdr in enumerate(["Date", "Time", "Q_plant_kW"], start=1):
        c = ws.cell(row=3, column=col, value=hdr)
        c.font = hdr_font(color="1F3864")
        c.fill = GREY_FILL
        c.alignment = CENTER

    ws.cell(row=4, column=1,
            value="← Paste IES VistaPro CHWL load export here (column C, 8,760 rows from row 4)").font = Font(
        name="Calibri", size=9, italic=True, color="FF0000")

    ws.freeze_panes = "A4"
    return ws


# ---------------------------------------------------------------------------
# Tab 4 — SIMULATION  (the engine)
# ---------------------------------------------------------------------------
SIM_COLS = [
    # (col_letter, col_name, group)
    ("A",  "Hour",               "Index"),
    ("B",  "T_odb_C",            "Weather"),
    ("C",  "T_wb_C",             "Weather"),
    ("D",  "Q_plant_demand_kW",  "Weather"),
    ("E",  "adiabatic_active",   "Adiabatic"),
    ("F",  "T_odb_eff_C",        "Adiabatic"),
    ("G",  "T_depression_C",     "Adiabatic"),
    ("H",  "T_chiller_inlet_C",  "Adiabatic"),
    ("I",  "T_dry_inlet_C",      "Adiabatic"),
    ("J",  "Q_chiller_demand_kW","Demand"),
    ("K",  "fCAPtt_adi",         "Chiller — Adiabatic"),
    ("L",  "Q_cap_chiller_adi",  "Chiller — Adiabatic"),
    ("M",  "Q_served_adi",       "Chiller — Adiabatic"),
    ("N",  "Q_unmet_adi",        "Chiller — Adiabatic"),
    ("O",  "PLR_adi",            "Chiller — Adiabatic"),
    ("P",  "PLR_calc_adi",       "Chiller — Adiabatic"),
    ("Q",  "fEIRtt_adi",         "Chiller — Adiabatic"),
    ("R",  "dT_adi",             "Chiller — Adiabatic"),
    ("S",  "fEIRpt_adi",         "Chiller — Adiabatic"),
    ("T",  "EIR_adi",            "Chiller — Adiabatic"),
    ("U",  "COP_adi",            "Chiller — Adiabatic"),
    ("V",  "P_plant_adi_kW",     "Chiller — Adiabatic"),
    ("W",  "fCAPtt_dry",         "Chiller — Dry Baseline"),
    ("X",  "Q_cap_chiller_dry",  "Chiller — Dry Baseline"),
    ("Y",  "Q_served_dry",       "Chiller — Dry Baseline"),
    ("Z",  "PLR_dry",            "Chiller — Dry Baseline"),
    ("AA", "PLR_calc_dry",       "Chiller — Dry Baseline"),
    ("AB", "fEIRtt_dry",         "Chiller — Dry Baseline"),
    ("AC", "dT_dry",             "Chiller — Dry Baseline"),
    ("AD", "fEIRpt_dry",         "Chiller — Dry Baseline"),
    ("AE", "EIR_dry",            "Chiller — Dry Baseline"),
    ("AF", "COP_dry",            "Chiller — Dry Baseline"),
    ("AG", "P_plant_dry_kW",     "Chiller — Dry Baseline"),
    ("AH", "Q_plant_cap_adi_kW", "Plant Totals"),
    ("AI", "Q_plant_cap_dry_kW", "Plant Totals"),
    ("AJ", "Q_plant_served_kW",  "Plant Totals"),
    ("AK", "Q_plant_unmet_kW",   "Plant Totals"),
    ("AL", "P_saving_kW",        "Energy & Savings"),
    ("AM", "E_plant_adi_kWh",    "Energy & Savings"),
    ("AN", "E_plant_dry_kWh",    "Energy & Savings"),
    ("AO", "E_saving_kWh",       "Energy & Savings"),
    ("AP", "over_capacity_flag", "Flags"),
    ("AQ", "low_PLR_flag",       "Flags"),
    ("AR", "month_num",          "Helper"),
]

GROUP_COLORS = {
    "Index":                   "D9D9D9",
    "Weather":                 "BDD7EE",
    "Adiabatic":               "DDEBF7",
    "Demand":                  "EBF3E8",
    "Chiller — Adiabatic":     "E2EFDA",
    "Chiller — Dry Baseline":  "FCE4D6",
    "Plant Totals":            "FFF2CC",
    "Energy & Savings":        "E2EFDA",
    "Flags":                   "F4CCCC",
    "Helper":                  "D9D9D9",
}

# Formulas for data row 4 (use ROW() for self-referencing row number)
# Written with concrete row=4 references; will be set via direct formula string
# and rely on openpyxl writing them as-is (relative refs auto-adjust when dragged
# in Excel — but since we only write row 4, user drags down).

SIM_FORMULAS = {
    "A":  "=ROW()-3",
    "B":  "=WEATHER_DATA!C4",
    "C":  "=WEATHER_DATA!D4",
    "D":  "=LOAD_DATA!C4",
    "E":  "=IF(B4>T_SWITCH,TRUE,FALSE)",
    "F":  "=IF(E4,MAX(C4,B4-ETA_SAT*(B4-C4)),B4)",
    "G":  "=B4-F4",
    "H":  "=F4+COND_INLET_T_OFFSET",
    "I":  "=B4+COND_INLET_T_OFFSET",
    "J":  "=IF(D4>0,D4/N_CHILLERS,0)",
    "K":  "=(CAP_C00+CAP_C10*T_LET_DES+CAP_C20*T_LET_DES^2+CAP_C01*H4+CAP_C02*H4^2+CAP_C11*T_LET_DES*H4)/C_NORM_CAP",
    "L":  "=Q_RAT_KW*K4",
    "M":  "=IF(J4>0,MIN(J4,L4),0)",
    "N":  "=IF(J4>0,MAX(0,J4-L4),0)",
    "O":  "=IF(L4>0,M4/L4,0)",
    "P":  "=IF(O4>0,MAX(O4,PLR_MIN_CALC),0)",
    "Q":  "=(EIR_C00+EIR_C10*T_LET_DES+EIR_C20*T_LET_DES^2+EIR_C01*H4+EIR_C02*H4^2+EIR_C11*T_LET_DES*H4)/C_NORM_EIR",
    "R":  "=H4-T_LET_DES",
    "S":  "=(PT_C00+PT_C10*P4+PT_C20*P4^2+PT_C01*R4+PT_C02*R4^2+PT_C11*P4*R4)/C_NORM_PT",
    "T":  "=IF(O4>0,MAX(1/COP_MAX,EIR_RAT*Q4*S4),0)",
    "U":  "=IF(T4>0,1/T4,0)",
    "V":  "=M4*T4*N_CHILLERS",
    "W":  "=(CAP_C00+CAP_C10*T_LET_DES+CAP_C20*T_LET_DES^2+CAP_C01*I4+CAP_C02*I4^2+CAP_C11*T_LET_DES*I4)/C_NORM_CAP",
    "X":  "=Q_RAT_KW*W4",
    "Y":  "=IF(J4>0,MIN(J4,X4),0)",
    "Z":  "=IF(X4>0,Y4/X4,0)",
    "AA": "=IF(Z4>0,MAX(Z4,PLR_MIN_CALC),0)",
    "AB": "=(EIR_C00+EIR_C10*T_LET_DES+EIR_C20*T_LET_DES^2+EIR_C01*I4+EIR_C02*I4^2+EIR_C11*T_LET_DES*I4)/C_NORM_EIR",
    "AC": "=I4-T_LET_DES",
    "AD": "=(PT_C00+PT_C10*AA4+PT_C20*AA4^2+PT_C01*AC4+PT_C02*AC4^2+PT_C11*AA4*AC4)/C_NORM_PT",
    "AE": "=IF(Z4>0,MAX(1/COP_MAX,EIR_RAT*AB4*AD4),0)",
    "AF": "=IF(AE4>0,1/AE4,0)",
    "AG": "=Y4*AE4*N_CHILLERS",
    "AH": "=L4*N_CHILLERS",
    "AI": "=X4*N_CHILLERS",
    "AJ": "=M4*N_CHILLERS",
    "AK": "=N4*N_CHILLERS",
    "AL": "=AG4-V4",
    "AM": "=V4",
    "AN": "=AG4",
    "AO": "=AL4",
    "AP": "=IF(J4>L4,TRUE,FALSE)",
    "AQ": "=IF(AND(O4>0,O4<PLR_MIN),TRUE,FALSE)",
    # month_num: extract from WEATHER_DATA col A (date string "Fri, 01/Jan")
    # Use MONTH(DATEVALUE()) on the date portion — VistaPro dates like "Fri, 01/Jan"
    # We use IFERROR + MONTH(DATEVALUE()) on WEATHER_DATA!A (which has date on first
    # hour of each day; blank on subsequent hours). We propagate downward.
    # Simpler: derive from row position using a fixed offset formula.
    # Row 4 = hour 1 (Jan 1 01:00). 8760 hours, months not equal-length.
    # Use a helper: =MONTH(DATE(2025,1,1)+INT((A4-1)/24)) with A4 = hour index.
    # This gives correct month for a non-leap year.
    "AR": "=MONTH(DATE(2025,1,1)+(A4-1)/24)",
}

NUM_FORMATS = {
    "B": "0.00", "C": "0.00", "D": "0.0",
    "F": "0.00", "G": "0.00", "H": "0.00", "I": "0.00",
    "J": "0.0",
    "K": "0.0000", "L": "0.0", "M": "0.0", "N": "0.0",
    "O": "0.0000", "P": "0.0000",
    "Q": "0.0000", "R": "0.00", "S": "0.0000",
    "T": "0.0000", "U": "0.000", "V": "0.0",
    "W": "0.0000", "X": "0.0", "Y": "0.0",
    "Z": "0.0000", "AA": "0.0000",
    "AB": "0.0000", "AC": "0.00", "AD": "0.0000",
    "AE": "0.0000", "AF": "0.000", "AG": "0.0",
    "AH": "0.0", "AI": "0.0", "AJ": "0.0", "AK": "0.0",
    "AL": "0.0", "AM": "0.0", "AN": "0.0", "AO": "0.0",
    "AR": "0",
}


def build_simulation(wb):
    ws = wb.create_sheet("SIMULATION")
    ws.sheet_view.showGridLines = True

    # Set column widths
    col_widths = {
        "A": 7, "B": 10, "C": 10, "D": 18,
        "E": 14, "F": 14, "G": 14, "H": 16, "I": 14,
        "J": 18,
    }
    for col_letter, _, _grp in SIM_COLS:
        w = col_widths.get(col_letter, 16)
        ws.column_dimensions[col_letter].width = w

    # ---- Row 1: group labels — merge contiguous spans ----
    # Build list of contiguous (group, start_col, end_col) spans
    spans = []
    for col_letter, _, group in SIM_COLS:
        ci = column_index_from_string(col_letter)
        if spans and spans[-1][0] == group:
            spans[-1] = (group, spans[-1][1], ci)
        else:
            spans.append((group, ci, ci))

    for group, start_ci, end_ci in spans:
        s = get_column_letter(start_ci)
        e = get_column_letter(end_ci)
        c = ws.cell(row=1, column=start_ci)
        c.value = group
        c.font = Font(name="Calibri", bold=True, size=10, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=GROUP_COLORS.get(group, "808080"))
        c.alignment = CENTER
        if start_ci != end_ci:
            ws.merge_cells(f"{s}1:{e}1")

    # ---- Row 2: blank (VistaPro convention) ----
    for col_letter, _, group in SIM_COLS:
        ci = column_index_from_string(col_letter)
        ws.cell(row=2, column=ci).fill = PatternFill("solid", fgColor=GROUP_COLORS.get(group, "808080"))

    # ---- Row 3: column name headers ----
    for col_letter, col_name, group in SIM_COLS:
        ci = column_index_from_string(col_letter)
        c = ws.cell(row=3, column=ci, value=col_name)
        c.font = Font(name="Calibri", bold=True, size=9, color="1F3864")
        c.fill = PatternFill("solid", fgColor=GROUP_COLORS.get(group, "D9D9D9"))
        c.alignment = CENTER

    ws.row_dimensions[3].height = 40

    # ---- Row 4: formulas ----
    for col_letter, col_name, group in SIM_COLS:
        ci = column_index_from_string(col_letter)
        formula = SIM_FORMULAS.get(col_letter, "")
        if formula:
            c = ws.cell(row=4, column=ci, value=formula)
            nf = NUM_FORMATS.get(col_letter)
            if nf:
                c.number_format = nf
            c.font = Font(name="Calibri", size=10)

    # Instruction note in row 5
    ws.cell(row=5, column=1,
            value="↑ Select row 4 (all columns A:AR), then drag fill handle down to row 8763 (8,760 hours)").font = Font(
        name="Calibri", size=9, italic=True, color="FF0000")

    # Freeze rows 1-3 + column A
    ws.freeze_panes = "B4"

    return ws


# ---------------------------------------------------------------------------
# Tab 5 — MONTHLY_SUMMARY
# ---------------------------------------------------------------------------
MONTHS = [
    ("Jan", 1), ("Feb", 2), ("Mar", 3), ("Apr", 4),
    ("May", 5), ("Jun", 6), ("Jul", 7), ("Aug", 8),
    ("Sep", 9), ("Oct", 10), ("Nov", 11), ("Dec", 12),
]

MONTHLY_COLS = [
    ("A", "Month"),
    ("B", "Month#"),
    ("C", "E_adi_MWh"),
    ("D", "E_dry_MWh"),
    ("E", "E_saving_MWh"),
    ("F", "Saving_%"),
    ("G", "Adi_hrs"),
    ("H", "Avg_COP_adi"),
    ("I", "Avg_COP_dry"),
    ("J", "Q_served_MWh"),
    ("K", "Q_unmet_kWh"),
    ("L", "Avg_PLR_adi"),
]

def build_monthly(wb):
    ws = wb.create_sheet("MONTHLY_SUMMARY")
    ws.sheet_view.showGridLines = False

    for col_letter, _ in MONTHLY_COLS:
        ws.column_dimensions[col_letter].width = 14
    ws.column_dimensions["A"].width = 8

    # Row 1: title
    ws.merge_cells("A1:L1")
    c = ws.cell(row=1, column=1, value="Monthly Summary")
    c.font = Font(name="Calibri", bold=True, size=13, color="FFFFFF")
    c.fill = BLUE_FILL
    c.alignment = CENTER
    ws.row_dimensions[1].height = 24

    # Row 2: blank (VistaPro convention)
    # Row 3: column headers
    for col_letter, col_name in MONTHLY_COLS:
        ci = column_index_from_string(col_letter)
        c = ws.cell(row=3, column=ci, value=col_name)
        c.font = hdr_font(color="1F3864")
        c.fill = LBLUE_FILL
        c.alignment = CENTER
    ws.row_dimensions[3].height = 36

    # Rows 4–15: Jan–Dec
    for i, (mon_name, mon_num) in enumerate(MONTHS):
        r = 4 + i
        mn = mon_num  # criteria value

        ws.cell(row=r, column=1, value=mon_name).font = body_font(bold=True)
        ws.cell(row=r, column=2, value=mon_num).alignment = CENTER

        formulas = {
            "C": f'=SUMIF(SIMULATION!AR:AR,B{r},SIMULATION!AM:AM)/1000',
            "D": f'=SUMIF(SIMULATION!AR:AR,B{r},SIMULATION!AN:AN)/1000',
            "E": f'=SUMIF(SIMULATION!AR:AR,B{r},SIMULATION!AO:AO)/1000',
            "F": f'=IFERROR(E{r}/D{r},0)',
            "G": f'=COUNTIFS(SIMULATION!AR:AR,B{r},SIMULATION!E:E,TRUE)',
            "H": f'=IFERROR(AVERAGEIFS(SIMULATION!U:U,SIMULATION!AR:AR,B{r},SIMULATION!U:U,">"&0),0)',
            "I": f'=IFERROR(AVERAGEIFS(SIMULATION!AF:AF,SIMULATION!AR:AR,B{r},SIMULATION!AF:AF,">"&0),0)',
            "J": f'=SUMIF(SIMULATION!AR:AR,B{r},SIMULATION!AJ:AJ)/1000',
            "K": f'=SUMIF(SIMULATION!AR:AR,B{r},SIMULATION!AK:AK)',
            "L": f'=IFERROR(AVERAGEIFS(SIMULATION!O:O,SIMULATION!AR:AR,B{r},SIMULATION!O:O,">"&0),0)',
        }
        num_fmts = {
            "C": "0.0", "D": "0.0", "E": "0.0",
            "F": "0.0%", "G": "0", "H": "0.000",
            "I": "0.000", "J": "0.0", "K": "0.0", "L": "0.000",
        }
        for col_letter, formula in formulas.items():
            ci = column_index_from_string(col_letter)
            c = ws.cell(row=r, column=ci, value=formula)
            c.font = body_font()
            c.alignment = RIGHT
            nf = num_fmts.get(col_letter)
            if nf:
                c.number_format = nf

    # Row 16: TOTALS / ANNUAL
    r_tot = 16
    ws.cell(row=r_tot, column=1, value="TOTAL").font = body_font(bold=True)
    totals = {
        "C": f"=SUM(C4:C15)",
        "D": f"=SUM(D4:D15)",
        "E": f"=SUM(E4:E15)",
        "F": f"=IFERROR(E{r_tot}/D{r_tot},0)",
        "G": f"=SUM(G4:G15)",
        "H": f"=IFERROR(AVERAGEIF(SIMULATION!U:U,"+"\">\"+0),0)",
        "I": f"=IFERROR(AVERAGEIF(SIMULATION!AF:AF,"+"\">\"+0),0)",
        "J": f"=SUM(J4:J15)",
        "K": f"=SUM(K4:K15)",
        "L": f"=IFERROR(AVERAGEIF(SIMULATION!O:O,"+"\">\"+0),0)",
    }
    num_fmts_tot = {
        "C": "0.0", "D": "0.0", "E": "0.0", "F": "0.0%",
        "G": "0", "H": "0.000", "I": "0.000",
        "J": "0.0", "K": "0.0", "L": "0.000",
    }
    for col_letter, formula in totals.items():
        ci = column_index_from_string(col_letter)
        c = ws.cell(row=r_tot, column=ci, value=formula)
        c.font = body_font(bold=True)
        c.fill = LBLUE_FILL
        nf = num_fmts_tot.get(col_letter)
        if nf:
            c.number_format = nf

    return ws


# ---------------------------------------------------------------------------
# Tab 6 — ANNUAL_SUMMARY
# ---------------------------------------------------------------------------
def build_annual(wb):
    ws = wb.create_sheet("ANNUAL_SUMMARY")
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 30

    ws.merge_cells("A1:C1")
    c = ws.cell(row=1, column=1, value="Annual Summary — ACC Adiabatic Relief")
    c.font = Font(name="Calibri", bold=True, size=14, color="FFFFFF")
    c.fill = BLUE_FILL
    c.alignment = CENTER
    ws.row_dimensions[1].height = 28

    def section_hdr(row, title):
        ws.merge_cells(f"A{row}:C{row}")
        c = ws.cell(row=row, column=1, value=title)
        c.font = Font(name="Calibri", bold=True, size=10, color="FFFFFF")
        c.fill = BLUE_FILL
        c.alignment = LEFT

    def kpi_row(row, label, formula, num_fmt="0.0", note=""):
        ws.cell(row=row, column=1, value=label).font = body_font()
        c2 = ws.cell(row=row, column=2, value=formula)
        c2.font = body_font(bold=True)
        c2.number_format = num_fmt
        c2.alignment = RIGHT
        if note:
            ws.cell(row=row, column=3, value=note).font = Font(name="Calibri", size=9, italic=True, color="595959")

    r = 2
    section_hdr(r, "ENERGY"); r += 1
    kpi_row(r, "E_adi_MWh",     "=SUM(SIMULATION!AM:AM)/1000",    "0.0",  "Total plant energy — adiabatic mode"); r += 1
    kpi_row(r, "E_dry_MWh",     "=SUM(SIMULATION!AN:AN)/1000",    "0.0",  "Total plant energy — dry baseline"); r += 1
    kpi_row(r, "E_saving_MWh",  "=SUM(SIMULATION!AO:AO)/1000",    "0.0",  "Annual energy saving (dry − adiabatic)"); r += 1
    kpi_row(r, "Saving_%",      f"=IFERROR(B{r-1}/B{r-2},0)",     "0.0%", "Energy saving as % of dry baseline"); r += 1

    section_hdr(r, "ADIABATIC OPERATION"); r += 1
    kpi_row(r, "Adi_hrs",       "=COUNTIF(SIMULATION!E:E,TRUE)",   "0",    "Hours pads were active"); r += 1
    kpi_row(r, "Adi_%_year",    f"=IFERROR(B{r-1}/8760,0)",        "0.0%", "Fraction of year pads active"); r += 1

    section_hdr(r, "COP — ADIABATIC MODE"); r += 1
    kpi_row(r, "Avg_COP_adi",   '=IFERROR(AVERAGEIF(SIMULATION!U:U,">"&0),0)',                              "0.000"); r += 1
    kpi_row(r, "Max_COP_adi",   '=IFERROR(MAXIFS(SIMULATION!U:U,SIMULATION!U:U,">"&0),0)',                   "0.000"); r += 1
    kpi_row(r, "Min_COP_adi",   '=IFERROR(MINIFS(SIMULATION!U:U,SIMULATION!U:U,">"&0),0)',                   "0.000"); r += 1

    section_hdr(r, "COP — DRY BASELINE"); r += 1
    kpi_row(r, "Avg_COP_dry",   '=IFERROR(AVERAGEIF(SIMULATION!AF:AF,">"&0),0)',                             "0.000"); r += 1
    kpi_row(r, "Max_COP_dry",   '=IFERROR(MAXIFS(SIMULATION!AF:AF,SIMULATION!AF:AF,">"&0),0)',               "0.000"); r += 1
    kpi_row(r, "Min_COP_dry",   '=IFERROR(MINIFS(SIMULATION!AF:AF,SIMULATION!AF:AF,">"&0),0)',               "0.000"); r += 1

    section_hdr(r, "LOAD COVERAGE"); r += 1
    kpi_row(r, "Q_served_MWh",  "=SUM(SIMULATION!AJ:AJ)/1000",    "0.0",  "Total cooling delivered"); r += 1
    kpi_row(r, "Q_unmet_kWh",   "=SUM(SIMULATION!AK:AK)",          "0.0",  "Total unmet cooling load"); r += 1
    kpi_row(r, "Overcap_hrs",   "=COUNTIF(SIMULATION!AP:AP,TRUE)", "0",    "Hours chiller was over-capacity"); r += 1
    kpi_row(r, "LowPLR_hrs",    "=COUNTIF(SIMULATION!AQ:AQ,TRUE)","0",    "Hours PLR below PLR_MIN threshold"); r += 1

    section_hdr(r, "VERIFICATION CHECKS"); r += 1
    # T_odb_eff >= T_wb check: count violations
    kpi_row(r, "T_eff_below_Twb_count",
            "=SUMPRODUCT((SIMULATION!F4:F8763<SIMULATION!C4:C8763)*1)",
            "0", "Should be 0 — T_odb_eff must not go below T_wb"); r += 1
    kpi_row(r, "C_NORM_CAP",    "=C_NORM_CAP",  "0.000000", "Capacity curve norm (raw value, pre-division)"); r += 1
    kpi_row(r, "C_NORM_EIR",    "=C_NORM_EIR",  "0.000000", "EIR temp curve norm"); r += 1
    kpi_row(r, "C_NORM_PT",     "=C_NORM_PT",   "0.000000", "EIR part-load curve norm"); r += 1

    return ws


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    wb = Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    build_inputs(wb)
    build_weather(wb)
    build_load(wb)
    build_simulation(wb)
    build_monthly(wb)
    build_annual(wb)

    out = "/home/user/acc_adiabatic_relief/ACC_Adiabatic_Relief.xlsx"
    wb.save(out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
