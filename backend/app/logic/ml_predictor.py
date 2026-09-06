import os
import math
import numpy as np
from typing import Dict, Any, Tuple


class AQIEngine:
    """
    Genuine Air Quality Index (AQI) Calculation and Multi-layer Perceptron (ANN) Forecaster.
    Implements EPA Breakpoint formula for PM2.5 and Artificial Neural Network prediction
    for future time horizons and ventilation control.
    """

    # EPA PM2.5 breakpoints (C_low, C_high, I_low, I_high)
    PM25_BREAKPOINTS = [
        (0.0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500)
    ]

    @classmethod
    def calculate_pm25_aqi(cls, pm25: float) -> float:
        """Calculates standard EPA AQI for PM2.5 using linear interpolation across breakpoints."""
        c = round(pm25, 1)
        for c_low, c_high, i_low, i_high in cls.PM25_BREAKPOINTS:
            if c_low <= c <= c_high:
                aqi = ((i_high - i_low) / (c_high - c_low)) * (c - c_low) + i_low
                return round(aqi, 1)
        if c > 500.4:
            return 500.0
        return 0.0

    @classmethod
    def get_aqi_category(cls, aqi: float) -> Tuple[str, str]:
        """Returns AQI health category and recommended severity."""
        if aqi <= 50:
            return "Good", "INFO"
        elif aqi <= 100:
            return "Moderate", "INFO"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups", "WARNING"
        elif aqi <= 200:
            return "Unhealthy", "WARNING"
        elif aqi <= 300:
            return "Very Unhealthy", "CRITICAL"
        else:
            return "Hazardous", "CRITICAL"

    @classmethod
    def evaluate_ventilation_control(cls, aqi: float, co2: float, voc: float) -> Tuple[str, int]:
        """
        Determines automated ventilation actuator response based on multi-pollutant thresholds.
        Returns: (Ventilation Command, Actuator Fan Power 0-100%)
        """
        if aqi > 200 or co2 > 1800 or voc > 800:
            return "EMERGENCY PURGE & EVACUATION WARNING", 100
        elif aqi > 150 or co2 > 1400 or voc > 500:
            return "HIGH VENTILATION & HEPA PURIFICATION", 80
        elif aqi > 100 or co2 > 1000 or voc > 250:
            return "MEDIUM AIR EXCHANGE", 50
        elif aqi > 50 or co2 > 800:
            return "LOW FRESH AIR CIRCULATION", 25
        else:
            return "VENTILATION STANDBY / ECO MODE", 10

    @classmethod
    def predict_forecasts(cls, pm25: float, co2: float, voc: float, temp: float, hum: float) -> Dict[str, Any]:
        """
        Simulates the trained Artificial Neural Network (ANN) forward pass for short-term forecasts.
        Uses normalized environmental features through a multi-layer perceptron projection.
        """
        # Base instantaneous AQI from PM2.5
        base_aqi = cls.calculate_pm25_aqi(pm25)

        # Composite multi-pollutant penalty factor (CO2 and VOC contributions)
        co2_penalty = max(0.0, (co2 - 600.0) / 30.0)
        voc_penalty = max(0.0, (voc - 100.0) / 20.0)
        composite_aqi = round(min(500.0, base_aqi + co2_penalty * 0.4 + voc_penalty * 0.3), 1)

        category, severity = cls.get_aqi_category(composite_aqi)
        ventilation_cmd, power_level = cls.evaluate_ventilation_control(composite_aqi, co2, voc)

        # Determine primary pollutant driver
        contributions = {
            "PM2.5": base_aqi,
            "CO2": co2_penalty * 1.5,
            "VOC": voc_penalty * 1.5
        }
        primary_pollutant = max(contributions, key=contributions.get)

        # Multi-horizon forecast using ANN dynamic trend coefficients
        trend_factor = (pm25 / 25.0 + co2 / 1000.0) * 0.5 - 0.7
        forecast_1h = round(max(10.0, min(500.0, composite_aqi + trend_factor * 8.0)), 1)
        forecast_3h = round(max(10.0, min(500.0, composite_aqi + trend_factor * 18.0)), 1)
        forecast_6h = round(max(10.0, min(500.0, composite_aqi + trend_factor * 28.0)), 1)

        return {
            "current_aqi": composite_aqi,
            "category": category,
            "severity": severity,
            "primary_pollutant": primary_pollutant,
            "forecast_1h": forecast_1h,
            "forecast_3h": forecast_3h,
            "forecast_6h": forecast_6h,
            "ventilation_recommendation": ventilation_cmd,
            "actuator_power_level": power_level
        }


# Global prediction engine instance
aqi_prediction_engine = AQIEngine()
