# =============================================================================
# Chiller Model — IESVE Electric Air-Cooled Chiller
# Implements the three bi-quadratic performance curves exactly as documented
# in the IESVE ApacheHVAC help (ve2021/electric_air_cooled_chillers.htm).
#
# Curve form (all three curves):
#   f(x, y) = (C00 + C10*x + C20*x² + C01*y + C02*y² + C11*x*y) / C_norm
#
# Curve 1 — fCAPtt(T_let, T_odb):  x = T_let, y = T_odb
# Curve 2 — fEIRtt(T_let, T_odb):  x = T_let, y = T_odb
# Curve 3 — fEIRpt(PLR, dT):       x = PLR,   y = (T_odb - T_let)
#
# T_datum = 0°C (metric), so tlet = T_let - 0 = T_let, todb = T_odb - 0 = T_odb
# C_norm is computed so each curve = 1.0 at rated conditions.
# =============================================================================

import warnings
from typing import Dict


def _biquad(coeffs: Dict[str, float], x: float, y: float) -> float:
    """Evaluate bi-quadratic polynomial."""
    return (
        coeffs["C00"]
        + coeffs["C10"] * x
        + coeffs["C20"] * x ** 2
        + coeffs["C01"] * y
        + coeffs["C02"] * y ** 2
        + coeffs["C11"] * x * y
    )


def _cnorm(coeffs: Dict[str, float], x_rat: float, y_rat: float) -> float:
    """
    Compute C_norm so that f(x_rat, y_rat) = 1.0 at rated conditions.
    Mirrors IESVE internal normalisation.
    """
    return _biquad(coeffs, x_rat, y_rat)


class ChillerModel:
    """
    Single electric air-cooled chiller — IESVE bi-quadratic curve model.
    All temperatures in °C. Capacity in kW. Power in kW.
    """

    def __init__(
        self,
        Q_rat:       float,   # Rated cooling capacity (kW)
        COP_rat:     float,   # Rated COP
        T_let_rat:   float,   # Rated leaving evaporator (CHWS) temp (°C)
        T_odb_rat:   float,   # Rated outdoor dry-bulb temp (°C)
        fan_power:   float,   # Condenser fan power (kW) — embedded in EIR
        cap_ftt:     Dict,    # CAP-fCHWT&ECT coefficients
        eir_ftt:     Dict,    # EIR-fCHWT&ECT coefficients
        eir_fpt:     Dict,    # EIR-fPLR&dT coefficients
    ):
        self.Q_rat     = Q_rat
        self.EIR_rat   = 1.0 / COP_rat
        self.T_let_rat = T_let_rat
        self.T_odb_rat = T_odb_rat
        self.fan_power = fan_power
        self.cap_ftt   = cap_ftt
        self.eir_ftt   = eir_ftt
        self.eir_fpt   = eir_fpt

        # Pre-compute C_norm for each curve at rated conditions
        self._cnorm_cap = _cnorm(cap_ftt, T_let_rat, T_odb_rat)
        self._cnorm_eir = _cnorm(eir_ftt, T_let_rat, T_odb_rat)
        dT_rat = T_odb_rat - T_let_rat
        self._cnorm_pt  = _cnorm(eir_fpt, 1.0, dT_rat)  # PLR=1.0 at rated

        # Plausibility check: C_norm values should not be zero or negative
        for name, val in [("CAP_FTT", self._cnorm_cap),
                          ("EIR_FTT", self._cnorm_eir),
                          ("EIR_FPT", self._cnorm_pt)]:
            if val <= 0:
                warnings.warn(
                    f"Curve {name} evaluates to {val:.6f} at rated conditions "
                    f"(should be positive). Check coefficients."
                )

    def available_capacity(self, T_let: float, T_odb_eff: float) -> float:
        """
        Q_cap (kW): full-load available capacity at current conditions.
        T_odb_eff is the effective condenser inlet temp — may be the
        adiabatically depressed value when pads are active.
        """
        f = _biquad(self.cap_ftt, T_let, T_odb_eff) / self._cnorm_cap
        return self.Q_rat * f

    def eir_temp(self, T_let: float, T_odb_eff: float) -> float:
        """fEIRtt — EIR temperature-dependence curve value."""
        return _biquad(self.eir_ftt, T_let, T_odb_eff) / self._cnorm_eir

    def eir_partload(self, PLR: float, T_let: float, T_odb_eff: float) -> float:
        """fEIRpt — EIR part-load + temperature-difference dependence."""
        dT = T_odb_eff - T_let
        return _biquad(self.eir_fpt, PLR, dT) / self._cnorm_pt

    def run(
        self,
        Q_demand:   float,   # Cooling load demanded from this chiller (kW)
        T_let:      float,   # Chilled water supply (leaving evaporator) temp (°C)
        T_odb_eff:  float,   # Effective outdoor DBT after adiabatic depression (°C)
    ) -> Dict:
        """
        Simulate one timestep. Returns dict of chiller outputs.

        Over-capacity handling (mirrors IESVE):
          - If Q_demand > Q_cap: chiller runs at full load (PLR=1.0),
            unmet load is returned separately — no extrapolation above PLR=1.
          - If Q_demand <= 0: chiller is off; all outputs are zero.
        """
        f_CAPtt = _biquad(self.cap_ftt, T_let, T_odb_eff) / self._cnorm_cap
        Q_cap   = self.Q_rat * f_CAPtt

        if Q_demand <= 0.0:
            return {
                "Q_cap":   Q_cap,
                "Q_served": 0.0,
                "Q_unmet": 0.0,
                "PLR":     0.0,
                "f_CAPtt": f_CAPtt,
                "f_EIRtt": 0.0,
                "f_EIRpt": 0.0,
                "EIR":     0.0,
                "COP":     0.0,
                "P_total": 0.0,
                "over_capacity": False,
            }

        # Clamp load at Q_cap — mirror IESVE behaviour
        over_capacity = Q_demand > Q_cap
        Q_served = min(Q_demand, Q_cap)
        Q_unmet  = max(0.0, Q_demand - Q_cap)
        PLR      = Q_served / Q_cap  # Always 0 < PLR <= 1.0
        f_EIRtt = self.eir_temp(T_let, T_odb_eff)
        f_EIRpt = self.eir_partload(PLR, T_let, T_odb_eff)

        EIR     = self.EIR_rat * f_EIRtt * f_EIRpt
        COP     = 1.0 / EIR if EIR > 0 else 0.0
        P_total = Q_served * EIR   # Total chiller power (includes fan per IESVE)

        return {
            "Q_cap":        Q_cap,
            "Q_served":     Q_served,
            "Q_unmet":      Q_unmet,
            "PLR":          PLR,
            "f_CAPtt":      f_CAPtt,
            "f_EIRtt":      f_EIRtt,
            "f_EIRpt":      f_EIRpt,
            "EIR":          EIR,
            "COP":          COP,
            "P_total":      P_total,
            "over_capacity": over_capacity,
        }
