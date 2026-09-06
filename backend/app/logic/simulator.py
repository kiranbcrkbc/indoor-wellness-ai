import math
import random
import time
from datetime import datetime
from typing import Dict, Any, Optional


class KalmanFilter1D:
    """
    1D Kalman Filter for sensor noise reduction, as specified in the Indoor Wellness project PPT.
    Reduces Gaussian measurement noise from simulated/real environmental telemetry.
    """
    def __init__(self, process_variance: float = 1e-4, measurement_variance: float = 0.05, estimated_error: float = 1.0, initial_value: float = 0.0):
        self.q = process_variance
        self.r = measurement_variance
        self.p = estimated_error
        self.x = initial_value
        self.k = 0.0

    def update(self, measurement: float) -> float:
        # Prediction update
        self.p = self.p + self.q

        # Measurement update
        self.k = self.p / (self.p + self.r)
        self.x = self.x + self.k * (measurement - self.x)
        self.p = (1.0 - self.k) * self.p

        return round(self.x, 2)


class EnvironmentalSimulator:
    """
    Software-only environmental simulation engine.
    Generates realistic time-series environmental data across multiple pre-configured scenarios.
    Explicitly labeled as 'SOFTWARE SIMULATION'.
    """

    SCENARIO_PROFILES = {
        "Normal Indoor": {
            "pm25_base": 12.0, "pm25_var": 3.0,
            "co2_base": 520.0, "co2_var": 40.0,
            "voc_base": 85.0, "voc_var": 15.0,
            "temp_base": 22.5, "temp_var": 0.5,
            "hum_base": 48.0, "hum_var": 2.0,
            "trend": 0.0
        },
        "Moderate Pollution": {
            "pm25_base": 42.0, "pm25_var": 6.0,
            "co2_base": 950.0, "co2_var": 80.0,
            "voc_base": 280.0, "voc_var": 30.0,
            "temp_base": 24.8, "temp_var": 0.8,
            "hum_base": 58.0, "hum_var": 3.0,
            "trend": 0.2
        },
        "Hazardous Event": {
            "pm25_base": 210.0, "pm25_var": 25.0,
            "co2_base": 2100.0, "co2_var": 150.0,
            "voc_base": 880.0, "voc_var": 70.0,
            "temp_base": 28.5, "temp_var": 1.2,
            "hum_base": 68.0, "hum_var": 4.0,
            "trend": 1.5
        },
        "Sudden Spike": {
            "pm25_base": 15.0, "pm25_var": 4.0,
            "co2_base": 550.0, "co2_var": 50.0,
            "voc_base": 90.0, "voc_var": 20.0,
            "temp_base": 23.0, "temp_var": 0.5,
            "hum_base": 50.0, "hum_var": 2.0,
            "trend": 0.0,
            "spike_active": True
        },
        "Improving Air Quality": {
            "pm25_base": 120.0, "pm25_var": 8.0,
            "co2_base": 1500.0, "co2_var": 90.0,
            "voc_base": 550.0, "voc_var": 40.0,
            "temp_base": 26.0, "temp_var": 0.7,
            "hum_base": 62.0, "hum_var": 3.0,
            "decay": 0.92
        }
    }

    def __init__(self):
        self.scenario = "Normal Indoor"
        self.is_running = True
        self.interval_seconds = 2.0
        self.step_count = 0
        self.last_update = time.time()

        # Dynamic state trackers
        self._current_pm25 = 12.0
        self._current_co2 = 520.0
        self._current_voc = 85.0
        self._current_temp = 22.5
        self._current_hum = 48.0

        # Dedicated Kalman filters for noisy simulated channels
        self.kf_pm25 = KalmanFilter1D(process_variance=1e-3, measurement_variance=0.08, initial_value=12.0)
        self.kf_co2 = KalmanFilter1D(process_variance=1e-2, measurement_variance=0.1, initial_value=520.0)

    def set_scenario(self, scenario_name: str):
        if scenario_name in self.SCENARIO_PROFILES:
            self.scenario = scenario_name
            profile = self.SCENARIO_PROFILES[scenario_name]
            self._current_pm25 = profile["pm25_base"]
            self._current_co2 = profile["co2_base"]
            self._current_voc = profile["voc_base"]
            self._current_temp = profile["temp_base"]
            self._current_hum = profile["hum_base"]
            self.step_count = 0

    def generate_step(self) -> Dict[str, Any]:
        """Generates a single simulated environmental step with noise, diurnal trends, and scenario dynamics."""
        self.step_count += 1
        profile = self.SCENARIO_PROFILES.get(self.scenario, self.SCENARIO_PROFILES["Normal Indoor"])

        # Sinusoidal diurnal wave
        diurnal_factor = math.sin(self.step_count * 0.1) * 0.5

        # Base noise
        noise_pm25 = random.gauss(0, profile["pm25_var"] * 0.5)
        noise_co2 = random.gauss(0, profile["co2_var"] * 0.4)
        noise_voc = random.gauss(0, profile["voc_var"] * 0.5)
        noise_temp = random.gauss(0, profile["temp_var"] * 0.3)
        noise_hum = random.gauss(0, profile["hum_var"] * 0.4)

        if self.scenario == "Sudden Spike":
            # Creates a dramatic spike between steps 5 and 15, then recovers
            if 5 <= (self.step_count % 30) <= 15:
                spike_multiplier = 4.5
            else:
                spike_multiplier = 1.0
            raw_pm25 = (profile["pm25_base"] + noise_pm25) * spike_multiplier
            raw_co2 = (profile["co2_base"] + noise_co2) * (1.0 + (spike_multiplier - 1.0) * 0.4)
            raw_voc = (profile["voc_base"] + noise_voc) * spike_multiplier
        elif self.scenario == "Improving Air Quality":
            decay = profile.get("decay", 0.95)
            self._current_pm25 = max(10.0, self._current_pm25 * decay + noise_pm25)
            self._current_co2 = max(450.0, self._current_co2 * decay + noise_co2)
            self._current_voc = max(60.0, self._current_voc * decay + noise_voc)
            raw_pm25 = self._current_pm25
            raw_co2 = self._current_co2
            raw_voc = self._current_voc
        else:
            trend = profile.get("trend", 0.0) * min(self.step_count, 20)
            raw_pm25 = max(1.0, profile["pm25_base"] + noise_pm25 + trend + diurnal_factor * 2)
            raw_co2 = max(380.0, profile["co2_base"] + noise_co2 + trend * 10 + diurnal_factor * 20)
            raw_voc = max(10.0, profile["voc_base"] + noise_voc + trend * 3)

        raw_temp = round(max(15.0, min(40.0, profile["temp_base"] + noise_temp)), 1)
        raw_hum = round(max(20.0, min(95.0, profile["hum_base"] + noise_hum)), 1)

        raw_pm25 = round(raw_pm25, 2)
        raw_co2 = round(raw_co2, 2)
        raw_voc = round(raw_voc, 2)

        # Apply Kalman filtering to reduce measurement noise
        filtered_pm25 = self.kf_pm25.update(raw_pm25)
        filtered_co2 = self.kf_co2.update(raw_co2)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": "SOFTWARE SIMULATION",
            "scenario": self.scenario,
            "step": self.step_count,
            "raw": {
                "pm25": raw_pm25,
                "co2": raw_co2,
                "voc": raw_voc,
                "temperature": raw_temp,
                "humidity": raw_hum
            },
            "kalman_filtered": {
                "pm25": filtered_pm25,
                "co2": filtered_co2
            }
        }


# Global simulator instance
environmental_simulator = EnvironmentalSimulator()
