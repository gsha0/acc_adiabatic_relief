# =============================================================================
# ACC Adiabatic Relief Tool - Interactive Dashboard
# =============================================================================
# Reads results_hourly.csv and produces a self-contained HTML dashboard with
# four full-width interactive Plotly charts and toggle buttons:
#   1. Calendar heatmap  — energy savings by day-of-year × hour-of-day
#   2. COP scatter       — COP vs outdoor dry-bulb (adiabatic vs dry)
#   3. Monthly bar       — monthly energy consumption and savings
#   4. Psychrometric     — dry-bulb vs wet-bulb, coloured by pad state
#
# Usage:
#   python visualize.py
#
# Output:
#   results_dashboard.html  (same directory as OUTPUT_FILE in config.py)

import os
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go

import config

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

CSV_PATH = config.OUTPUT_FILE
if not os.path.exists(CSV_PATH):
    sys.exit(f"ERROR: Results file not found: {CSV_PATH}\nRun main.py first.")

df = pd.read_csv(CSV_PATH)
df["adiabatic_active"] = df["adiabatic_active"].astype(str).str.lower() == "true"

T_SWITCH = config.T_SWITCH

df["day_of_year"] = pd.to_datetime(
    "2000-"
    + df["month"].astype(int).astype(str).str.zfill(2)
    + "-"
    + df["day"].astype(int).astype(str).str.zfill(2)
).dt.dayofyear

MONTH_ORDER = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

annual_saving_pct = (
    df["E_saving_kWh"].sum() / df["E_plant_dry_kWh"].sum() * 100
    if df["E_plant_dry_kWh"].sum() > 0 else 0
)
adi_hours = int(df["adiabatic_active"].sum())

# ---------------------------------------------------------------------------
# Chart 1: Calendar Heatmap
# ---------------------------------------------------------------------------

pivot = df.pivot_table(
    index="day_of_year", columns="hour", values="E_saving_kWh", aggfunc="sum"
)
pivot = pivot.reindex(index=range(1, 366), columns=range(0, 24), fill_value=0)

month_starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
month_mids   = [s + 15 for s in month_starts]

# Build date label for each day-of-year row (e.g. "Jan 11")
doy_labels = [
    (pd.Timestamp("2001-01-01") + pd.Timedelta(days=d - 1)).strftime("%b ") +
    str((pd.Timestamp("2001-01-01") + pd.Timedelta(days=d - 1)).day)
    for d in range(1, 366)
]
# customdata shape must match z: (n_days, n_hours) — each cell holds the date string
heatmap_customdata = np.array([[lbl] * 24 for lbl in doy_labels])

fig1 = go.Figure(go.Heatmap(
    z=pivot.values,
    x=list(pivot.columns),
    y=list(pivot.index),
    customdata=heatmap_customdata,
    colorscale=[
        [0.0,  "rgb(198,225,245)"],
        [0.25, "rgb(255,237,160)"],
        [0.5,  "rgb(254,178,76)"],
        [0.75, "rgb(240,59,32)"],
        [1.0,  "rgb(128,0,38)"],
    ],
    colorbar=dict(title="Energy Saving<br>(kWh/hr)"),
    hovertemplate=(
        "Hour: %{x}:00<br>"
        "Day: %{customdata}<br>"
        "Saving: %{z:.1f} kWh<extra></extra>"
    ),
    zmin=0,
))
fig1.update_layout(
    title="Energy Savings — Calendar Heatmap",
    xaxis_title="Hour of Day",
    yaxis=dict(
        title="Month",
        tickvals=month_mids,
        ticktext=MONTH_ORDER,
    ),
    height=500,
    template="plotly_white",
)

# ---------------------------------------------------------------------------
# Chart 2: COP Scatter
# ---------------------------------------------------------------------------

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=df["T_odb_C"], y=df["COP_dry"],
    mode="markers", name="Dry baseline",
    marker=dict(color="rgba(255,140,0,0.35)", size=4),
    customdata=df[["month_name", "day", "hour"]].values,
    hovertemplate=(
        "T_odb: %{x:.1f} °C<br>"
        "COP (dry): %{y:.3f}<br>"
        "Day: %{customdata[0]} %{customdata[1]:.0f}, Hour: %{customdata[2]:.0f}<extra></extra>"
    ),
))
fig2.add_trace(go.Scatter(
    x=df["T_odb_C"], y=df["COP_adi"],
    mode="markers", name="Adiabatic",
    marker=dict(color="rgba(31,119,180,0.45)", size=4),
    customdata=df[["month_name", "day", "hour"]].values,
    hovertemplate=(
        "T_odb: %{x:.1f} °C<br>"
        "COP (adiabatic): %{y:.3f}<br>"
        "Day: %{customdata[0]} %{customdata[1]:.0f}, Hour: %{customdata[2]:.0f}<extra></extra>"
    ),
))
fig2.add_trace(go.Scatter(
    x=[T_SWITCH, T_SWITCH],
    y=[df["COP_dry"].min() * 0.95, df["COP_adi"].max() * 1.05],
    mode="lines", name=f"T_SWITCH ({T_SWITCH}°C)",
    line=dict(color="black", dash="dash", width=1.5),
    hoverinfo="skip",
))
fig2.update_layout(
    title="COP vs Outdoor Dry-Bulb Temperature",
    xaxis_title="Outdoor Dry-Bulb Temperature (°C)",
    yaxis_title="COP",
    height=500,
    template="plotly_white",
    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
)

# ---------------------------------------------------------------------------
# Chart 3: Monthly Bar
# ---------------------------------------------------------------------------

monthly = (
    df.groupby("month_name")[["E_plant_adi_kWh", "E_plant_dry_kWh", "E_saving_kWh"]]
    .sum()
    .div(1000)
    .reindex(MONTH_ORDER)
    .reset_index()
)

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    name="Dry baseline", x=monthly["month_name"], y=monthly["E_plant_dry_kWh"],
    marker_color="rgba(180,180,180,0.85)",
    hovertemplate="Dry: %{y:.1f} MWh<extra></extra>",
))
fig3.add_trace(go.Bar(
    name="Adiabatic", x=monthly["month_name"], y=monthly["E_plant_adi_kWh"],
    marker_color="rgba(31,119,180,0.85)",
    hovertemplate="Adiabatic: %{y:.1f} MWh<extra></extra>",
))
fig3.add_trace(go.Bar(
    name="Saving", x=monthly["month_name"], y=monthly["E_saving_kWh"],
    marker_color="rgba(44,160,44,0.85)",
    hovertemplate="Saving: %{y:.2f} MWh<extra></extra>",
))
fig3.update_layout(
    title="Monthly Energy Consumption & Savings",
    xaxis_title="Month",
    yaxis_title="Energy (MWh)",
    barmode="group",
    height=500,
    template="plotly_white",
    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
    annotations=[dict(
        text=f"Annual saving: {annual_saving_pct:.2f}%",
        xref="paper", yref="paper", x=0.99, y=0.99,
        xanchor="right", yanchor="top",
        showarrow=False,
        font=dict(size=13, color="#2c7c2c"),
        bgcolor="rgba(255,255,255,0.7)",
        bordercolor="#2c7c2c", borderwidth=1,
    )],
)

# ---------------------------------------------------------------------------
# Chart 4: Psychrometric Overlay
# ---------------------------------------------------------------------------

df_dry_pts = df[~df["adiabatic_active"]]
df_adi_pts = df[df["adiabatic_active"]]
t_range = np.linspace(df["T_odb_C"].min() - 1, df["T_odb_C"].max() + 1, 50)

fig4 = go.Figure()
fig4.add_trace(go.Scatter(
    x=df_dry_pts["T_odb_C"], y=df_dry_pts["T_wb_C"],
    mode="markers", name="Pads OFF",
    marker=dict(color="rgba(160,160,160,0.25)", size=4),
    customdata=df_dry_pts[["month_name", "day", "hour"]].values,
    hovertemplate=(
        "T_db: %{x:.1f} °C<br>"
        "T_wb: %{y:.1f} °C<br>"
        "Day: %{customdata[0]} %{customdata[1]:.0f}, Hour: %{customdata[2]:.0f}<extra></extra>"
    ),
))
fig4.add_trace(go.Scatter(
    x=df_adi_pts["T_odb_C"], y=df_adi_pts["T_wb_C"],
    mode="markers", name="Pads ON",
    marker=dict(color="rgba(31,119,180,0.6)", size=5),
    customdata=df_adi_pts[["month_name", "day", "hour"]].values,
    hovertemplate=(
        "T_db: %{x:.1f} °C<br>"
        "T_wb: %{y:.1f} °C<br>"
        "Day: %{customdata[0]} %{customdata[1]:.0f}, Hour: %{customdata[2]:.0f}<extra></extra>"
    ),
))
fig4.add_trace(go.Scatter(
    x=t_range, y=t_range,
    mode="lines", name="Saturation (T_wb = T_db)",
    line=dict(color="rgba(0,0,0,0.4)", dash="dot", width=1.5),
    hoverinfo="skip",
))
fig4.add_trace(go.Scatter(
    x=[T_SWITCH, T_SWITCH],
    y=[df["T_wb_C"].min() - 1, df["T_wb_C"].max() + 1],
    mode="lines", name=f"T_SWITCH ({T_SWITCH}°C)",
    line=dict(color="black", dash="dash", width=1.5),
    hoverinfo="skip", showlegend=True,
))
fig4.update_layout(
    title="Psychrometric Chart — Pad Activation",
    xaxis_title="Dry-Bulb Temperature (°C)",
    yaxis_title="Wet-Bulb Temperature (°C)",
    height=500,
    template="plotly_white",
    legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
)

# ---------------------------------------------------------------------------
# Build HTML
# ---------------------------------------------------------------------------

def fig_div(fig, div_id):
    """Return a Plotly figure as an embeddable <div> string (no Plotly.js)."""
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        div_id=div_id,
        config={"responsive": True},
    )

charts = [
    ("chart-heatmap",      "Calendar Heatmap",        fig1),
    ("chart-cop",          "COP Scatter",              fig2),
    ("chart-monthly",      "Monthly Energy",           fig3),
    ("chart-psychrometric","Psychrometric Chart",      fig4),
]

chart_sections = ""
for div_id, label, fig in charts:
    chart_sections += f"""
    <section id="{div_id}" class="chart-section">
      <div class="chart-wrap">
        {fig_div(fig, div_id + "-plot")}
      </div>
    </section>
"""

toggle_buttons = ""
for div_id, label, _ in charts:
    toggle_buttons += (
        f'<button class="toggle-btn active" data-target="{div_id}">{label}</button>\n    '
    )

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>ACC Adiabatic Relief — Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f5f6f8;
      color: #222;
    }}

    header {{
      background: #1a2e45;
      color: #fff;
      padding: 20px 32px 16px;
    }}
    header h1 {{ font-size: 1.4rem; font-weight: 600; margin-bottom: 6px; }}
    header .meta {{
      font-size: 0.85rem;
      color: #a8c0d6;
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
    }}
    header .meta span {{ white-space: nowrap; }}
    header .meta .highlight {{ color: #7ee8a2; font-weight: 600; }}

    .toolbar {{
      background: #fff;
      border-bottom: 1px solid #dde1e7;
      padding: 12px 32px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .toolbar-label {{
      font-size: 0.78rem;
      font-weight: 600;
      color: #667;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-right: 4px;
    }}

    .toggle-btn {{
      padding: 6px 16px;
      border-radius: 20px;
      border: 1.5px solid #1a2e45;
      background: #1a2e45;
      color: #fff;
      font-size: 0.82rem;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
    }}
    .toggle-btn.inactive {{
      background: #fff;
      color: #1a2e45;
    }}
    .toggle-btn:hover {{ opacity: 0.8; }}

    main {{ padding: 24px 32px; display: flex; flex-direction: column; gap: 24px; }}

    .chart-section {{
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
      overflow: hidden;
    }}
    .chart-wrap {{ width: 100%; }}
    /* Make the Plotly div fill its container */
    .chart-wrap > div {{ width: 100% !important; }}
  </style>
</head>
<body>

<header>
  <h1>ACC Adiabatic Relief — Simulation Results Dashboard</h1>
  <div class="meta">
    <span>Annual energy saving: <span class="highlight">{annual_saving_pct:.2f}%</span></span>
    <span>Adiabatic active: <span class="highlight">{adi_hours:,} hrs/yr</span></span>
    <span>T_SWITCH = {T_SWITCH}°C</span>
    <span>ETA_SAT = {config.ETA_SAT}</span>
    <span>N_CHILLERS = {config.N_CHILLERS}</span>
  </div>
</header>

<div class="toolbar">
  <span class="toolbar-label">Show / Hide:</span>
  {toggle_buttons}
</div>

<main>
{chart_sections}
</main>

<script>
  document.querySelectorAll(".toggle-btn").forEach(btn => {{
    btn.addEventListener("click", () => {{
      const target = document.getElementById(btn.dataset.target);
      const isActive = !btn.classList.contains("inactive");
      if (isActive) {{
        target.style.display = "none";
        btn.classList.add("inactive");
      }} else {{
        target.style.display = "";
        btn.classList.remove("inactive");
        // Trigger Plotly resize so the chart fills the newly visible container
        const plotDiv = target.querySelector(".plotly-graph-div");
        if (plotDiv) Plotly.relayout(plotDiv, {{}});
      }}
    }});
  }});
</script>

</body>
</html>
"""

out_dir = os.path.dirname(os.path.abspath(CSV_PATH))
out_path = os.path.join(out_dir, "results_dashboard.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Dashboard saved: {out_path}")
