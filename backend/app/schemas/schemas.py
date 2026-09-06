from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# -------------------------------------------------------------------
# Product Schemas
# -------------------------------------------------------------------
class ProductBase(BaseModel):
    name: str = Field(..., description="Product class name matching detector output")
    category: Optional[str] = Field("General", description="Grouping category")

class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------------------------
# Shelf & ROI Schemas
# -------------------------------------------------------------------
class ShelfBase(BaseModel):
    name: str = Field(..., description="Shelf label e.g., 'Shelf 1 - Top Rack'")
    roi_coordinates: List[List[float]] = Field(
        ...,
        description="List of [x, y] coordinates defining polygon or normalized [x1, y1, x2, y2]"
    )
    expected_capacity: int = Field(10, ge=1, description="Nominal capacity for a full shelf")
    low_stock_threshold: float = Field(0.35, ge=0.0, le=1.0, description="Fraction under which shelf is LOW STOCK")
    empty_threshold: float = Field(0.05, ge=0.0, le=1.0, description="Fraction under which shelf is EMPTY")

class ShelfCreate(ShelfBase):
    pass

class ShelfUpdate(BaseModel):
    name: Optional[str] = None
    roi_coordinates: Optional[List[List[float]]] = None
    expected_capacity: Optional[int] = Field(None, ge=1)
    low_stock_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    empty_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)

class ShelfOut(ShelfBase):
    shelf_id: int
    created_at: datetime
    current_count: Optional[int] = 0
    current_occupancy: Optional[float] = 0.0
    current_status: Optional[str] = "AVAILABLE"

    class Config:
        from_attributes = True


# -------------------------------------------------------------------
# Detection & Run Schemas
# -------------------------------------------------------------------
class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float
    confidence: float
    class_id: int
    class_name: str
    shelf_id: Optional[int] = None

class DetectionResult(BaseModel):
    run_id: int
    timestamp: datetime
    input_type: str
    source_reference: str
    total_detections: int
    detections: List[BoundingBox]
    class_counts: Dict[str, int]
    shelf_statuses: Dict[int, Dict[str, Any]]
    annotated_image_url: Optional[str] = None
    processing_time_ms: float

class DetectionRunSummary(BaseModel):
    run_id: int
    input_type: str
    source_reference: str
    model_version: str
    started_at: datetime
    completed_at: Optional[datetime]
    total_detections: Optional[int] = 0


# -------------------------------------------------------------------
# Inventory & Stock Schemas
# -------------------------------------------------------------------
class InventoryStatus(BaseModel):
    inventory_id: int
    shelf_id: int
    shelf_name: str
    detected_count: int
    expected_capacity: int
    occupancy_ratio: float
    status: str
    recorded_at: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------------------------
# Alert Schemas
# -------------------------------------------------------------------
class AlertBase(BaseModel):
    alert_type: str
    shelf_id: Optional[int] = None
    message: str
    severity: str = "WARNING"

class AlertOut(AlertBase):
    alert_id: int
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -------------------------------------------------------------------
# Environmental & Simulation Schemas
# -------------------------------------------------------------------
class EnvironmentalReadingIn(BaseModel):
    pm25: float = Field(..., ge=0, le=1000, description="PM2.5 concentration in µg/m³")
    co2: float = Field(..., ge=300, le=5000, description="CO2 concentration in ppm")
    voc: float = Field(..., ge=0, le=2000, description="VOC concentration in ppb")
    temperature: float = Field(..., ge=-10, le=60, description="Temperature in °C")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity in %")
    source: Optional[str] = "MANUAL"

class EnvironmentalReadingOut(EnvironmentalReadingIn):
    reading_id: int
    filtered_pm25: Optional[float] = None
    filtered_co2: Optional[float] = None
    predicted_aqi: Optional[float] = None
    air_quality_status: Optional[str] = None
    ventilation_status: Optional[str] = None
    recorded_at: datetime

    class Config:
        from_attributes = True

class SimulationConfigIn(BaseModel):
    scenario: str = Field("Normal Indoor", description="Scenario: Normal Indoor, Moderate Pollution, Hazardous Event, Sudden Spike, Improving")
    interval_seconds: float = Field(2.0, ge=0.5, le=60.0)
    is_running: bool = True

class AQIPredictionOut(BaseModel):
    current_aqi: float
    category: str
    primary_pollutant: str
    forecast_1h: float
    forecast_3h: float
    forecast_6h: float
    ventilation_recommendation: str
    actuator_power_level: int = Field(..., ge=0, le=100)


# -------------------------------------------------------------------
# System Settings & Model Info Schemas
# -------------------------------------------------------------------
class SystemSettingsOut(BaseModel):
    confidence_threshold: float
    nms_iou_threshold: float
    active_model_path: str
    empty_threshold: float
    low_stock_threshold: float
    temporal_confirmation_frames: int
    aqi_hazardous_threshold: float
    simulation_scenario: str
    simulation_running: bool

class ModelInfoOut(BaseModel):
    model_name: str
    model_type: str
    weights_path: str
    framework: str
    classes: List[str]
    input_resolution: str
    device: str
    measured_metrics: Dict[str, Any]
