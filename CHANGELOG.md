# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
