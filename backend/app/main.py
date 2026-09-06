import os
import json
import logging
from datetime import datetime
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.app.db.database import engine, Base, get_db
from backend.app.db.models import Shelf, SystemSetting, Product
from backend.app.api import shelves, detect, environmental, alerts, analytics, settings
from backend.app.cv.detector import detector_instance

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smartshelf.main")

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Indoor Wellness & Smart Shelf AI System",
    description="Software-Only AI Platform unifying YOLOv8 Product Detection with Environmental Simulation & AQI Forecasting",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths setup
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Include API Routers
app.include_router(shelves.router, prefix="/api")
app.include_router(detect.router, prefix="/api")
app.include_router(environmental.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


@app.on_event("startup")
def seed_initial_defaults():
    """Initializes default shelves and settings if database is newly created."""
    db = next(get_db())
    try:
        # Check default shelves
        if db.query(Shelf).count() == 0:
            logger.info("Seeding initial default shelf ROIs...")
            shelf_1 = Shelf(
                name="Shelf 1 - Top Rack (Beverages & Snacks)",
                roi_coordinates=json.dumps([[60, 70], [740, 210]]),
                expected_capacity=8,
                low_stock_threshold=0.35,
                empty_threshold=0.05
            )
            shelf_2 = Shelf(
                name="Shelf 2 - Lower Rack (Packaged Goods)",
                roi_coordinates=json.dumps([[60, 280], [740, 430]]),
                expected_capacity=8,
                low_stock_threshold=0.35,
                empty_threshold=0.05
            )
            db.add_all([shelf_1, shelf_2])
            db.commit()

        # Check default settings
        defaults = {
            "confidence_threshold": "0.45",
            "nms_iou_threshold": "0.45",
            "active_model_path": "models/pretrained/yolov8n.pt",
            "empty_threshold": "0.05",
            "low_stock_threshold": "0.35",
            "temporal_confirmation_frames": "3",
            "aqi_hazardous_threshold": "150.0",
            "simulation_scenario": "Normal Indoor"
        }
        for k, v in defaults.items():
            if not db.query(SystemSetting).filter(SystemSetting.setting_key == k).first():
                db.add(SystemSetting(setting_key=k, setting_value=v))
        db.commit()

        # Default product labels
        default_prods = ["bottle", "can", "cereal_box", "snack_bag", "cup", "carton"]
        for p in default_prods:
            if not db.query(Product).filter(Product.name == p).first():
                db.add(Product(name=p, category="Retail Item"))
        db.commit()

    except Exception as e:
        logger.error(f"Startup seeding error: {e}")
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def render_dashboard(request: Request):
    """Serves the unified web dashboard."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/health")
def health_check():
    """Health check endpoint confirming system operational status."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected (SQLite WAL)",
        "model_loaded": detector_instance.is_loaded,
        "active_model": detector_instance.model_name,
        "software_only_mode": True,
        "hardware_required": False
    }
