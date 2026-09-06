import pytest
from backend.app.logic.ml_predictor import AQIEngine


def test_epa_pm25_aqi_breakpoints():
    # PM2.5 = 10.0 µg/m³ should map to 0-50 range
    aqi_clean = AQIEngine.calculate_pm25_aqi(10.0)
    assert 0 <= aqi_clean <= 50

    # PM2.5 = 25.0 µg/m³ should map to 51-100 range
    aqi_moderate = AQIEngine.calculate_pm25_aqi(25.0)
    assert 51 <= aqi_moderate <= 100

    # PM2.5 = 155.0 µg/m³ should map to 201-300 range (Very Unhealthy)
    aqi_unhealthy = AQIEngine.calculate_pm25_aqi(155.0)
    assert 201 <= aqi_unhealthy <= 300


def test_aqi_category_classification():
    cat_good, sev_good = AQIEngine.get_aqi_category(35)
    assert cat_good == "Good"
    assert sev_good == "INFO"

    cat_sens, sev_sens = AQIEngine.get_aqi_category(125)
    assert cat_sens == "Unhealthy for Sensitive Groups"
    assert sev_sens == "WARNING"

    cat_haz, sev_haz = AQIEngine.get_aqi_category(350)
    assert cat_haz == "Hazardous"
    assert sev_haz == "CRITICAL"


def test_ventilation_control_logic():
    # Clean air -> Standby
    cmd_clean, pwr_clean = AQIEngine.evaluate_ventilation_control(aqi=30, co2=500, voc=70)
    assert "STANDBY" in cmd_clean
    assert pwr_clean <= 20

    # Moderate air -> Circulation
    cmd_mod, pwr_mod = AQIEngine.evaluate_ventilation_control(aqi=75, co2=850, voc=150)
    assert pwr_mod >= 25

    # Dangerous air -> Emergency purge
    cmd_purge, pwr_purge = AQIEngine.evaluate_ventilation_control(aqi=240, co2=2200, voc=950)
    assert "EMERGENCY PURGE" in cmd_purge
    assert pwr_purge == 100


def test_ml_multi_horizon_forecasts():
    forecast = AQIEngine.predict_forecasts(
        pm25=18.5,
        co2=650.0,
        voc=120.0,
        temp=23.0,
        hum=50.0
    )

    assert "current_aqi" in forecast
    assert "forecast_1h" in forecast
    assert "forecast_3h" in forecast
    assert "forecast_6h" in forecast
    assert "ventilation_recommendation" in forecast
    assert "actuator_power_level" in forecast
    assert 0 <= forecast["current_aqi"] <= 500
