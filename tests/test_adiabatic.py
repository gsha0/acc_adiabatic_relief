"""Tests for the adiabatic pre-cooling module."""

from adiabatic import effective_odb


class TestEffectiveOdb:

    def test_pads_off_below_switch(self):
        """When T_odb <= T_switch, pads should be off."""
        T_eff, active = effective_odb(T_odb=25.0, T_wb=18.0, T_switch=30.0, eta_sat=0.85)
        assert active is False
        assert T_eff == 25.0

    def test_pads_on_above_switch(self):
        """When T_odb > T_switch, pads should activate."""
        T_eff, active = effective_odb(T_odb=35.0, T_wb=22.0, T_switch=30.0, eta_sat=0.85)
        assert active is True
        assert T_eff < 35.0

    def test_depression_formula(self):
        """T_eff = T_odb - eta * (T_odb - T_wb)."""
        T_odb, T_wb, eta = 40.0, 25.0, 0.80
        expected = T_odb - eta * (T_odb - T_wb)  # 40 - 0.8*15 = 28.0
        T_eff, _ = effective_odb(T_odb, T_wb, T_switch=30.0, eta_sat=eta)
        assert abs(T_eff - expected) < 1e-9

    def test_floor_at_wet_bulb(self):
        """T_eff can never go below T_wb (physical limit)."""
        # With eta=1.0, depression = T_odb - T_wb, so T_eff = T_wb exactly
        T_eff, _ = effective_odb(T_odb=35.0, T_wb=22.0, T_switch=30.0, eta_sat=1.0)
        assert T_eff >= 22.0 - 1e-9

    def test_exactly_at_switch(self):
        """At T_odb == T_switch, pads should be off."""
        T_eff, active = effective_odb(T_odb=30.0, T_wb=20.0, T_switch=30.0, eta_sat=0.85)
        assert active is False
        assert T_eff == 30.0

    def test_zero_efficiency(self):
        """With eta_sat=0, no depression even when pads are 'on'."""
        T_eff, active = effective_odb(T_odb=40.0, T_wb=25.0, T_switch=30.0, eta_sat=0.0)
        assert active is True
        assert T_eff == 40.0
