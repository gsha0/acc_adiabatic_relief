# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-04-22

### Added
- Annual summary now shows Max and Min COP for both adiabatic and dry modes, each followed by the first hour the value occurred in parentheses (e.g. `Jun 15 14:00`)
- Output CSV filename is now timestamped (`YYYY-MM-DD_hourly_HHMMSS.csv`) so successive runs never overwrite each other
- Append-only run log (`run_log.csv`) written alongside the results CSV — captures the full annual and monthly summary for every run, with a `run_datetime` column (`YYYY-MM-DD HH:MM:SS`) to identify each run; the file is never overwritten, only appended to

## [0.2.0] - 2026-04-22

### Added
- `COND_INLET_T_OFFSET` parameter in `config.py` (new *Chiller Plant Environment Parameters* section) — adds a fixed temperature offset (°C, default 5 °C) to the condenser coil inlet temperature to model semi-enclosed plant rooms where heat rejection exhaust recirculates and mixes with outdoor air
- Offset is applied after adiabatic pad cooling: when pads are off it is added to outdoor dry-bulb; when pads are on it is added to the pad outlet temperature; the T_SWITCH threshold and adiabatic depression calculation remain based on raw outdoor air
- New output column `T_chiller_inlet_C` — the actual temperature seen by the chiller (after pad cooling and enclosure offset)
- Dashboard (`visualize.py`) updated to surface the offset:
  - Header now shows the configured `COND_INLET_T_OFFSET` value alongside T_SWITCH and ETA_SAT
  - COP scatter (Chart 2) hover tooltip now displays `Chiller inlet` temperature for every point
  - Psychrometric chart (Chart 4) pads-ON hover tooltip now shows both `Pad outlet` and `Chiller inlet` temperatures, making the two-step temperature modification visible

## [0.1.0] - 2026-04-05

### Added
- Full hourly HVAC chiller simulation engine with adiabatic relief (wetted pad pre-cooling) support
- Bi-quadratic performance curves matching IESVE Electric Air-Cooled Chiller model
- EnergyPlus EPW weather file reader for realistic ambient conditions
- IESVE VistaPro load profile import (Excel format)
- Psychrometric calculations for wet-bulb temperature and saturation efficiency using Stull (2011) formula
- Hourly simulation across full 8,760-hour annual period
- CSV output with 25+ columns including capacity, COP, energy consumption, and pad state
- Side-by-side comparison: adiabatic mode vs. dry baseline for each hour
- Plant configuration: multiple identical chillers with load balancing
- Configuration-driven operation via `config.py` (no code changes required for parameter updates)
- Over-capacity handling matching IESVE logic for unmet cooling loads
- Interactive HTML5 dashboard with four Plotly charts:
  - Calendar heatmap of energy savings by day and hour
  - COP scatter plot (adiabatic vs. dry mode) vs. outdoor temperature
  - Monthly energy consumption and savings breakdown
  - Psychrometric chart showing operating conditions
- Comprehensive test suite covering psychrometrics, chiller model, and adiabatic relief physics
- Detailed README with installation, quick-start, configuration reference, and troubleshooting guides
- Version control with semantic versioning (v0.1.0)

### Fixed
- (none in initial release)

### Changed
- (none in initial release)
