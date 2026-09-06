import io
import csv
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import EnvironmentalReading, AQIPrediction, Alert
from backend.app.logic.simulator import environmental_simulator
from backend.app.logic.ml_predictor import aqi_prediction_engine
from backend.app.schemas.schemas import (
    EnvironmentalReadingIn, EnvironmentalReadingOut, SimulationConfigIn, AQIPredictionOut
)

router = APIRouter(prefix="/environmental", tags=["Indoor Wellness AI"])


@router.get("/latest", response_model=Dict[str, Any])
def get_latest_environmental(db: Session = Depends(get_db)):
    """Retrieves current environmental status, simulated step, and active scenario."""
    sim_data = environmental_simulator.generate_step()
    raw = sim_data["raw"]
    kf = sim_data["kalman_filtered"]

    pred = aqi_prediction_engine.predict_forecasts(
        pm25=kf["pm25"],
        co2=kf["co2"],
        voc=raw["voc"],
        temp=raw["temperature"],
        hum=raw["humidity"]
    )

    return {
        "source": "SOFTWARE SIMULATION",
        "scenario": environmental_simulator.scenario,
        "is_running": environmental_simulator.is_running,
        "step": sim_data["step"],
        "timestamp": sim_data["timestamp"],
        "raw": raw,
        "kalman_filtered": kf,
        "prediction": pred
    }


@router.post("/scenario")
def set_simulation_scenario(scenario: str = Query(..., description="Scenario name")):
    """Switches active software simulation scenario."""
    if scenario not in environmental_simulator.SCENARIO_PROFILES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid scenario. Choose from: {list(environmental_simulator.SCENARIO_PROFILES.keys())}"
        )
    environmental_simulator.set_scenario(scenario)
    return {"status": "success", "scenario": scenario}


@router.post("/manual", response_model=Dict[str, Any])
def submit_manual_reading(payload: EnvironmentalReadingIn, db: Session = Depends(get_db)):
    """Accepts manual environmental values entered by the user, runs Kalman filtering and ANN predictions."""
    filtered_pm25 = environmental_simulator.kf_pm25.update(payload.pm25)
    filtered_co2 = environmental_simulator.kf_co2.update(payload.co2)

    pred = aqi_prediction_engine.predict_forecasts(
        pm25=filtered_pm25,
        co2=filtered_co2,
        voc=payload.voc,
        temp=payload.temperature,
        hum=payload.humidity
    )

    reading = EnvironmentalReading(
        pm25=payload.pm25,
        co2=payload.co2,
        voc=payload.voc,
        temperature=payload.temperature,
        humidity=payload.humidity,
        filtered_pm25=filtered_pm25,
        filtered_co2=filtered_co2,
        predicted_aqi=pred["current_aqi"],
        air_quality_status=pred["category"],
        ventilation_status=pred["ventilation_recommendation"],
        source="MANUAL",
        recorded_at=datetime.utcnow()
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    # Save prediction
    prediction_record = AQIPrediction(
        reading_id=reading.reading_id,
        predicted_aqi=pred["current_aqi"],
        category=pred["category"],
        primary_pollutant=pred["primary_pollutant"],
        forecast_1h=pred["forecast_1h"],
        forecast_3h=pred["forecast_3h"],
        forecast_6h=pred["forecast_6h"],
        recommended_ventilation=pred["ventilation_recommendation"],
        actuator_power_level=pred["actuator_power_level"]
    )
    db.add(prediction_record)

    # Trigger alert if hazardous
    if pred["severity"] in ["WARNING", "CRITICAL"]:
        alert = Alert(
            alert_type="HAZARDOUS_AQI",
            message=f"Air Quality Alert: AQI {pred['current_aqi']} ({pred['category']}) - Primary: {pred['primary_pollutant']}",
            severity=pred["severity"],
            is_resolved=False
        )
        db.add(alert)

    db.commit()

    return {
        "reading_id": reading.reading_id,
        "source": "MANUAL ENTRY",
        "raw": payload.dict(),
        "kalman_filtered": {"pm25": filtered_pm25, "co2": filtered_co2},
        "prediction": pred
    }


@router.post("/upload")
async def upload_environmental_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Ingests CSV or JSON datasets containing environmental measurements without physical sensors."""
    filename = file.filename.lower()
    content = await file.read()

    readings_to_process = []

    if filename.endswith(".csv"):
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
            try:
                readings_to_process.append({
                    "pm25": float(row.get("pm25", row.get("PM2.5", 15.0))),
                    "co2": float(row.get("co2", row.get("CO2", 500.0))),
                    "voc": float(row.get("voc", row.get("VOC", 100.0))),
                    "temperature": float(row.get("temperature", row.get("temp", 22.0))),
                    "humidity": float(row.get("humidity", row.get("hum", 50.0)))
                })
            except (ValueError, TypeError):
                continue
    elif filename.endswith(".json"):
        try:
            data = json.loads(content.decode("utf-8"))
            if isinstance(data, list):
                readings_to_process = data
            elif isinstance(data, dict) and "readings" in data:
                readings_to_process = data["readings"]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON file format: {e}")
    else:
        raise HTTPException(status_code=400, detail="Only CSV or JSON files are supported.")

    if not readings_to_process:
        raise HTTPException(status_code=400, detail="No valid numerical readings found in file.")

    processed_count = 0
    latest_prediction = None

    for item in readings_to_process[:200]:  # Cap import batch size
        pm25 = float(item.get("pm25", 15.0))
        co2 = float(item.get("co2", 500.0))
        voc = float(item.get("voc", 100.0))
        temp = float(item.get("temperature", 22.0))
        hum = float(item.get("humidity", 50.0))

        kf_pm25 = environmental_simulator.kf_pm25.update(pm25)
        kf_co2 = environmental_simulator.kf_co2.update(co2)

        pred = aqi_prediction_engine.predict_forecasts(kf_pm25, kf_co2, voc, temp, hum)
        latest_prediction = pred

        reading = EnvironmentalReading(
            pm25=pm25,
            co2=co2,
            voc=voc,
            temperature=temp,
            humidity=hum,
            filtered_pm25=kf_pm25,
            filtered_co2=kf_co2,
            predicted_aqi=pred["current_aqi"],
            air_quality_status=pred["category"],
            ventilation_status=pred["ventilation_recommendation"],
            source=f"FILE: {file.filename}",
            recorded_at=datetime.utcnow()
        )
        db.add(reading)
        processed_count += 1

    db.commit()

    return {
        "status": "success",
        "filename": file.filename,
        "readings_imported": processed_count,
        "latest_predicted_aqi": latest_prediction["current_aqi"] if latest_prediction else None,
        "latest_category": latest_prediction["category"] if latest_prediction else None
    }


@router.get("/history", response_model=List[Dict[str, Any]])
def get_environmental_history(limit: int = Query(30, ge=5, le=100), db: Session = Depends(get_db)):
    """Returns recent environmental readings for time-series charts."""
    records = db.query(EnvironmentalReading).order_by(EnvironmentalReading.recorded_at.desc()).limit(limit).all()
    # Reverse to chronological order for charts
    records = list(reversed(records))

    return [
        {
            "reading_id": r.reading_id,
            "timestamp": r.recorded_at.strftime("%H:%M:%S"),
            "pm25": r.pm25,
            "filtered_pm25": r.filtered_pm25 or r.pm25,
            "co2": r.co2,
            "filtered_co2": r.filtered_co2 or r.co2,
            "voc": r.voc,
            "temperature": r.temperature,
            "humidity": r.humidity,
            "predicted_aqi": r.predicted_aqi or 25.0,
            "source": r.source
        }
        for r in records
    ]
