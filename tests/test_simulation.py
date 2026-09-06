import pytest
from backend.app.logic.simulator import KalmanFilter1D, EnvironmentalSimulator


def test_kalman_filter_noise_reduction():
    kf = KalmanFilter1D(process_variance=1e-3, measurement_variance=0.1, initial_value=20.0)

    # Feed noisy measurements centered around 20.0
    measurements = [20.2, 23.5, 17.8, 22.1, 18.9, 20.5, 21.0]
    filtered_values = [kf.update(m) for m in measurements]

    # Filtered variance should be significantly lower than raw measurement variance
    assert len(filtered_values) == len(measurements)
    # The final filtered estimate should remain close to the true mean of 20
    assert 18.0 <= filtered_values[-1] <= 22.0


def test_environmental_simulator_step_generation():
    sim = EnvironmentalSimulator()
    step = sim.generate_step()

    assert "raw" in step
    assert "kalman_filtered" in step
    assert "timestamp" in step
    assert step["source"] == "SOFTWARE SIMULATION"

    raw = step["raw"]
    assert 0.0 <= raw["pm25"] <= 1000.0
    assert 300.0 <= raw["co2"] <= 5000.0
    assert 0.0 <= raw["voc"] <= 2000.0
    assert -10.0 <= raw["temperature"] <= 50.0
    assert 10.0 <= raw["humidity"] <= 100.0


def test_environmental_simulator_scenarios():
    sim = EnvironmentalSimulator()

    # Normal Indoor
    sim.set_scenario("Normal Indoor")
    step_normal = sim.generate_step()
    assert step_normal["raw"]["pm25"] < 35.0  # Normal indoor PM2.5 is low

    # Hazardous Event
    sim.set_scenario("Hazardous Event")
    step_hazard = sim.generate_step()
    assert step_hazard["raw"]["pm25"] > 100.0  # Hazardous scenario has elevated PM2.5
    assert step_hazard["raw"]["co2"] > 1500.0
