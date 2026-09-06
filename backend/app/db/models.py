from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(100), default="General")
    created_at = Column(DateTime, default=datetime.utcnow)

    detections = relationship("Detection", back_populates="product")


class Shelf(Base):
    __tablename__ = "shelves"

    shelf_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    roi_coordinates = Column(Text, nullable=False)  # JSON-encoded coordinates
    expected_capacity = Column(Integer, default=10, nullable=False)
    low_stock_threshold = Column(Float, default=0.35, nullable=False)
    empty_threshold = Column(Float, default=0.05, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    detections = relationship("Detection", back_populates="shelf")
    inventories = relationship("Inventory", back_populates="shelf", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="shelf")


class DetectionRun(Base):
    __tablename__ = "detection_runs"

    run_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    input_type = Column(String(50), nullable=False)  # 'image', 'video', 'live', 'demo'
    source_reference = Column(String(255), nullable=True)
    model_version = Column(String(100), default="yolov8n")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    detections = relationship("Detection", back_populates="run", cascade="all, delete-orphan")
    inventories = relationship("Inventory", back_populates="run", cascade="all, delete-orphan")


class Detection(Base):
    __tablename__ = "detections"

    detection_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("detection_runs.run_id", ondelete="CASCADE"), nullable=False)
    shelf_id = Column(Integer, ForeignKey("shelves.shelf_id", ondelete="SET NULL"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=True)
    confidence = Column(Float, nullable=False)
    bbox_x = Column(Float, nullable=False)
    bbox_y = Column(Float, nullable=False)
    bbox_w = Column(Float, nullable=False)
    bbox_h = Column(Float, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("DetectionRun", back_populates="detections")
    shelf = relationship("Shelf", back_populates="detections")
    product = relationship("Product", back_populates="detections")


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shelf_id = Column(Integer, ForeignKey("shelves.shelf_id", ondelete="CASCADE"), nullable=False)
    run_id = Column(Integer, ForeignKey("detection_runs.run_id", ondelete="CASCADE"), nullable=False)
    detected_count = Column(Integer, default=0, nullable=False)
    occupancy_ratio = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="AVAILABLE", nullable=False)  # AVAILABLE, LOW STOCK, EMPTY
    recorded_at = Column(DateTime, default=datetime.utcnow)

    shelf = relationship("Shelf", back_populates="inventories")
    run = relationship("DetectionRun", back_populates="inventories")


class Alert(Base):
    __tablename__ = "alerts"

    alert_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False)  # LOW_STOCK, EMPTY_SHELF, HAZARDOUS_AQI, etc.
    shelf_id = Column(Integer, ForeignKey("shelves.shelf_id", ondelete="SET NULL"), nullable=True)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="WARNING")  # INFO, WARNING, CRITICAL
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    shelf = relationship("Shelf", back_populates="alerts")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    setting_key = Column(String(100), primary_key=True, index=True)
    setting_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EnvironmentalReading(Base):
    __tablename__ = "environmental_readings"

    reading_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pm25 = Column(Float, nullable=False)
    co2 = Column(Float, nullable=False)
    voc = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    filtered_pm25 = Column(Float, nullable=True)
    filtered_co2 = Column(Float, nullable=True)
    predicted_aqi = Column(Float, nullable=True)
    air_quality_status = Column(String(50), default="Good")
    ventilation_status = Column(String(50), default="OFF")
    source = Column(String(50), default="SIMULATION")  # SIMULATION, MANUAL, FILE
    recorded_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("AQIPrediction", back_populates="reading", cascade="all, delete-orphan")


class AQIPrediction(Base):
    __tablename__ = "aqi_predictions"

    prediction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    reading_id = Column(Integer, ForeignKey("environmental_readings.reading_id", ondelete="CASCADE"), nullable=False)
    predicted_aqi = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    primary_pollutant = Column(String(50), default="PM2.5")
    forecast_1h = Column(Float, nullable=False)
    forecast_3h = Column(Float, nullable=False)
    forecast_6h = Column(Float, nullable=False)
    recommended_ventilation = Column(String(50), default="OFF")
    actuator_power_level = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    reading = relationship("EnvironmentalReading", back_populates="predictions")
