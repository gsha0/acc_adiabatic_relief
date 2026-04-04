"""Tests for the chiller model."""

import pytest

from chiller_model import ChillerModel, _biquad


# Reference coefficients from config.py
CAP_FTT = {"C00": 1.201400, "C10": 0.045081, "C20": 0.000215,
           "C01": -0.007392, "C02": -0.000047, "C11": -0.000370}
EIR_FTT = {"C00": 0.422279, "C10": 0.006181, "C20": 0.000307,
           "C01": 0.002750, "C02": 0.000344, "C11": -0.000610}
EIR_FPT = {"C00": 0.035101, "C10": 0.524496, "C20": 0.433515,
           "C01": 0.000699, "C02": 0.000009, "C11": -0.000724}


@pytest.fixture
def chiller():
    return ChillerModel(
        Q_rat=786.6, COP_rat=2.844538,
        T_let_rat=5.56, T_odb_rat=40.56, fan_power=24.6,
        cap_ftt=CAP_FTT, eir_ftt=EIR_FTT, eir_fpt=EIR_FPT,
    )


class TestCurveNormalization:

    def test_cap_curve_is_1_at_rated(self, chiller):
        """fCAPtt should be 1.0 at rated conditions."""
        f = _biquad(CAP_FTT, 5.56, 40.56) / chiller._cnorm_cap
        assert abs(f - 1.0) < 1e-9

    def test_eir_temp_curve_is_1_at_rated(self, chiller):
        """fEIRtt should be 1.0 at rated conditions."""
        f = chiller.eir_temp(5.56, 40.56)
        assert abs(f - 1.0) < 1e-9

    def test_eir_partload_curve_is_1_at_rated(self, chiller):
        """fEIRpt should be 1.0 at PLR=1 and rated dT."""
        f = chiller.eir_partload(1.0, 5.56, 40.56)
        assert abs(f - 1.0) < 1e-9


class TestChillerRun:

    def test_zero_load_returns_zeros(self, chiller):
        result = chiller.run(Q_demand=0.0, T_let=5.56, T_odb_eff=35.0)
        assert result["Q_served"] == 0.0
        assert result["P_total"] == 0.0
        assert result["PLR"] == 0.0
        assert result["EIR"] == 0.0
        assert result["over_capacity"] is False

    def test_negative_load_returns_zeros(self, chiller):
        result = chiller.run(Q_demand=-100.0, T_let=5.56, T_odb_eff=35.0)
        assert result["Q_served"] == 0.0
        assert result["P_total"] == 0.0

    def test_normal_load(self, chiller):
        result = chiller.run(Q_demand=400.0, T_let=5.56, T_odb_eff=35.0)
        assert result["Q_served"] == 400.0
        assert result["Q_unmet"] == 0.0
        assert 0.0 < result["PLR"] <= 1.0
        assert result["P_total"] > 0.0
        assert result["COP"] > 0.0
        assert result["over_capacity"] is False

    def test_over_capacity_clamped(self, chiller):
        """When demand exceeds capacity, PLR should be clamped at 1.0."""
        # Use a very high demand to guarantee over-capacity
        result = chiller.run(Q_demand=5000.0, T_let=5.56, T_odb_eff=35.0)
        assert result["PLR"] == 1.0
        assert result["Q_unmet"] > 0.0
        assert result["over_capacity"] is True
        assert abs(result["Q_served"] - result["Q_cap"]) < 1e-9

    def test_rated_conditions_cop(self, chiller):
        """At rated conditions and full load, COP should match rated COP."""
        Q_cap = chiller.available_capacity(5.56, 40.56)
        result = chiller.run(Q_demand=Q_cap, T_let=5.56, T_odb_eff=40.56)
        assert abs(result["COP"] - 2.844538) < 0.01

    def test_lower_odb_improves_cop(self, chiller):
        """Lowering condenser inlet temperature should improve COP."""
        result_hot = chiller.run(Q_demand=400.0, T_let=5.56, T_odb_eff=40.0)
        result_cool = chiller.run(Q_demand=400.0, T_let=5.56, T_odb_eff=30.0)
        assert result_cool["COP"] > result_hot["COP"]

    def test_energy_balance(self, chiller):
        """P_total should equal Q_served * EIR."""
        result = chiller.run(Q_demand=500.0, T_let=5.56, T_odb_eff=35.0)
        expected_power = result["Q_served"] * result["EIR"]
        assert abs(result["P_total"] - expected_power) < 1e-6
