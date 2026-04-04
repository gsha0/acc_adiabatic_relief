"""Tests for the psychrometrics module."""

import numpy as np
import pytest

from psychro import wet_bulb, wet_bulb_array


class TestWetBulb:
    """Tests for single-value wet_bulb()."""

    def test_wet_bulb_never_exceeds_dry_bulb(self):
        """T_wb must always be <= T_db."""
        cases = [
            (35.0, 20.0, 101325),
            (0.0, -5.0, 101325),
            (45.0, 30.0, 101325),
            (10.0, 9.5, 101325),   # near-saturation
        ]
        for T_db, T_dp, p in cases:
            T_wb = wet_bulb(T_db, T_dp, p)
            assert T_wb <= T_db + 1e-9, (
                f"T_wb={T_wb} > T_db={T_db} for T_dp={T_dp}"
            )

    def test_wet_bulb_never_below_dew_point(self):
        """T_wb must always be >= T_dp."""
        cases = [
            (35.0, 20.0, 101325),
            (0.0, -5.0, 101325),
            (45.0, 10.0, 101325),  # very dry
        ]
        for T_db, T_dp, p in cases:
            T_wb = wet_bulb(T_db, T_dp, p)
            assert T_wb >= T_dp - 1e-9, (
                f"T_wb={T_wb} < T_dp={T_dp} for T_db={T_db}"
            )

    def test_saturated_air(self):
        """When T_db == T_dp (100% RH), T_wb should equal T_db."""
        T_wb = wet_bulb(25.0, 25.0, 101325)
        assert abs(T_wb - 25.0) < 1.0  # Stull accuracy ±0.65°C

    def test_known_approximate_value(self):
        """Spot-check against a known psychrometric reference point.
        T_db=30°C, T_dp=15°C -> T_wb ~20°C (within Stull accuracy)."""
        T_wb = wet_bulb(30.0, 15.0, 101325)
        assert 18.0 < T_wb < 22.0

    def test_warns_outside_valid_range(self):
        """Should warn when T_db is outside -20 to 50°C."""
        with pytest.warns(UserWarning, match="outside Stull formula"):
            wet_bulb(55.0, 30.0, 101325)


class TestWetBulbArray:
    """Tests for vectorised wet_bulb_array()."""

    def test_output_shape_matches_input(self):
        T_db = np.array([25.0, 30.0, 35.0])
        T_dp = np.array([15.0, 20.0, 25.0])
        p = np.array([101325, 101325, 101325])
        result = wet_bulb_array(T_db, T_dp, p)
        assert result.shape == (3,)

    def test_bounds_hold_for_array(self):
        T_db = np.array([25.0, 30.0, 35.0, 0.0, 45.0])
        T_dp = np.array([15.0, 20.0, 25.0, -5.0, 10.0])
        p = np.full(5, 101325.0)
        T_wb = wet_bulb_array(T_db, T_dp, p)
        assert np.all(T_wb <= T_db + 1e-9)
        assert np.all(T_wb >= T_dp - 1e-9)

    def test_consistent_with_scalar(self):
        """Array version should match scalar version."""
        T_db = np.array([25.0, 35.0])
        T_dp = np.array([15.0, 20.0])
        p = np.full(2, 101325.0)
        arr_result = wet_bulb_array(T_db, T_dp, p)
        for i in range(2):
            scalar_result = wet_bulb(T_db[i], T_dp[i], p[i])
            assert abs(arr_result[i] - scalar_result) < 0.01
