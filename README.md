# Indoor Wellness & Smart Shelf AI System

> **A Complete, End-to-End, Production Software-Only Artificial Intelligence Platform**  
> *Combining Real-Time YOLOv8 Shelf Inventory Monitoring with Indoor Environmental Telemetry Simulation & ANN-Based Pollution Forecasting.*

[![Live Demo](https://img.shields.io/badge/Live%20Demo-HTTPS%20Active-brightgreen.svg)](https://participants-examinations-genre-isle.trycloudflare.com)
[![GitHub Repo](https://img.shields.io/badge/GitHub-kiranbcrkbc%2Findoor--wellness--ai-blue.svg)](https://github.com/kiranbcrkbc/indoor-wellness-ai)
[![Automated Tests](https://img.shields.io/badge/Tests-47%2F47%20Passing%20(100%25)-success.svg)](https://github.com/kiranbcrkbc/indoor-wellness-ai)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/Ultralytics-YOLOv8n-orange.svg)](https://docs.ultralytics.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20WAL%20Persistent-003B57.svg)](https://www.sqlite.org/)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/kiranbcrkbc/indoor-wellness-ai)

---

## 🌐 Live Production Links
- **Live Public HTTPS Application:** [https://participants-examinations-genre-isle.trycloudflare.com](https://participants-examinations-genre-isle.trycloudflare.com)
- **Live Swagger API Documentation:** [https://participants-examinations-genre-isle.trycloudflare.com/docs](https://participants-examinations-genre-isle.trycloudflare.com/docs)
- **Public GitHub Repository:** [https://github.com/kiranbcrkbc/indoor-wellness-ai](https://github.com/kiranbcrkbc/indoor-wellness-ai)
- **Author/GitHub Account:** [kiranbcrkbc](https://github.com/kiranbcrkbc) (kiranbcrkbc@gmail.com)

---

## Academic Reference
- **Institution:** R R Institute of Technology, Dept. of Computer Science and Engineering
- **Course:** Major Project Phase-1 (BCS685, VTU Curriculum)
- **Project Group:** Group 23 (Muskan Ranjan – 1RI23CS099, P Alekhya – 1RI23CS104, Pooja K S – 1RI23CS107)
- **Project Guide:** Asst. Prof. Surendra Babu M S

---

## Critical Software-Only Guarantee

> [!IMPORTANT]
> **THIS VERSION IS FULLY SOFTWARE-BASED AND DOES NOT REQUIRE PHYSICAL IOT HARDWARE.**  
> The complete end-to-end user experience runs on a standard laptop (Windows, Linux, or macOS). No physical sensors (PM2.5, CO₂, VOC, DHT22), Raspberry Pi, Arduino, ESP32, physical ventilation equipment, or external controllers are required to run, evaluate, or demonstrate the application.

All data inputs are provided through:
1. **Configurable Simulation Engine** (`DATA SOURCE: SOFTWARE SIMULATION`)
2. **Manual Software Input Forms**
3. **File-Based Ingestion** (CSV / JSON datasets)
4. **Pre-staged Demonstration Media & Scenarios** (Full Shelf, Low Stock, Empty Shelf)
5. **Optional Built-in / USB Webcam** (with automatic fallback if no camera is connected)

---

## 1. Project Overview & Architectural Reconciliation

Group 23's original project materials contained two complementary domains:
1. **Indoor Air Quality & Pollution Forecasting** (Chapters 1–3): Environmental sensing, Kalman filtering for noise reduction, and ANN-based pollution forecasting with automated ventilation control.
2. **Smart Shelf Computer Vision System** (Chapters 4–5): Camera-driven object detection using YOLO, shelf Region of Interest (ROI) analysis, automated stock-level classification (`AVAILABLE` / `LOW STOCK` / `EMPTY`), and real-time dashboard alerting.

This platform reconciles both into a unified dual-domain software suite under an interchangeable **Data Source Abstraction Layer**, allowing evaluators to demonstrate either or both components within a single cohesive web application.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             SOFTWARE-ONLY INPUT LAYER                            │
│  • Time-Series Simulator  • Manual Software Form  • CSV/JSON Import  • Media/Cam │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCE ABSTRACTION LAYER                            │
│  • Schema Validation  • Normalization  • 1D Kalman Noise Reduction Filter       │
└──────────────────┬─────────────────────────────────────────────┬─────────────────┘
                   │                                             │
                   ▼                                             ▼
┌─────────────────────────────────────┐       ┌────────────────────────────────────┐
│      SMART SHELF CV PIPELINE        │       │     INDOOR WELLNESS ML ENGINE      │
│ • Ultralytics YOLOv8n Inference     │       │ • EPA Breakpoint AQI Calculation   │
│ • NMS Filtering & Confidence Cut    │       │ • Multi-Layer Perceptron (ANN)     │
│ • Shelf ROI Centroid Intersection   │       │   +1h, +3h, +6h Trend Forecasts    │
│ • Occupancy Ratio & Threshold Logic │       │ • Automated Ventilation Actuator   │
│   (AVAILABLE / LOW STOCK / EMPTY)   │       │   (OFF / LOW / MED / HIGH / PURGE) │
└──────────────────┬──────────────────┘       └──────────────────┬─────────────────┘
                   │                                             │
                   └──────────────────────┬──────────────────────┘
                                          │
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION & PERSISTENCE LAYER                         │
│  • Alert Engine (Toast + In-App Log)  • SQLite Database (WAL Mode)  • Analytics  │
└─────────────────────────────────────────┬────────────────────────────────────────┘
                                          │ REST API / JSON
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER (WEB UI)                           │
│  • Glassmorphic Dark Dashboard  • Real-Time Canvas Overlays  • Chart.js Analytics│
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Features

### A. Smart Shelf AI Vision Suite
- **Object Detection & Classification (FR-01, FR-02):** Ultralytics YOLOv8 nano model detects multiple product instances and classes (`bottle`, `can`, `cereal_box`, `snack_bag`, etc.).
- **Per-Shelf Counting & Monitoring (FR-03, FR-04):** Associates product bounding box centroids with configurable shelf ROIs.
- **Stock-Level Classification (FR-05, FR-06, FR-07):** Transparent classification into `AVAILABLE`, `LOW STOCK`, and `EMPTY` based on configurable capacity and threshold percentages.
- **Temporal Confirmation:** 3-frame sliding window filter prevents alert flickering caused by momentary camera occlusion.
- **Visual Canvas Overlays:** Draws color-coded shelf boundaries (Green / Amber / Red) and product bounding boxes directly on frames.

### B. Indoor Wellness Environmental AI Suite
- **Multi-Scenario Simulation Engine:** Real-time generation of PM2.5, CO₂, VOC, Temperature, and Humidity across 5 realistic scenarios:
  - *Normal Indoor* (Baseline good air quality)
  - *Moderate Pollution* (Elevated VOCs and occupancy)
  - *Hazardous Event* (High PM2.5 fire/smoke scenario)
  - *Sudden Spike* (Transient event with decay recovery)
  - *Improving Air Quality* (Active filtration decay curve)
- **1D Kalman Filtering:** Real-time Kalman noise reduction on simulated sensor channels before downstream prediction.
- **ANN Multi-Horizon Forecasting:** Artificial Neural Network model forecasting composite AQI trends for +1h, +3h, and +6h horizons.
- **Automated Ventilation Control:** Intelligent actuator recommendation (Standby, Moderate Circulation, HEPA Purify, Emergency Purge).

### C. Core Platform & User Experience
- **Executive Overview:** High-level operational KPIs, live telemetry meters, and quick demo action triggers.
- **Alert Center:** Unified incident log with severity filtering (`INFO`, `WARNING`, `CRITICAL`) and one-click resolution.
- **Shelf Manager:** Web-based ROI coordinate editor and capacity configurator.
- **Analytics & CSV Audit Export:** Historical occupancy graphs, class distribution donuts, and audit log export.
- **Model Information:** Transparent display of active weights checkpoint, inference device, and measured evaluation figures.

---

## 3. Technology Stack

| Layer | Component | Details |
|---|---|---|
| **Language** | Python 3.11 | Modern, standard runtime for AI and web services |
| **API Framework** | FastAPI & Uvicorn | High-performance asynchronous REST API with OpenAPI autodocs |
| **Computer Vision** | Ultralytics YOLOv8 & OpenCV | State-of-the-art single-pass convolutional detector |
| **Machine Learning** | Scikit-Learn & NumPy | Multi-layer perceptron forecasting and matrix math |
| **Database** | SQLite 3 | Zero-install, file-based relational DB with WAL concurrency |
| **Frontend** | HTML5, Vanilla CSS, ES6 JS | Polished dark glassmorphic UI without heavyweight node build steps |
| **Data Visualization** | Chart.js 4.4 | Real-time animated time-series, bar, and donut charts |

---

## 4. Quick Start & Local Installation

### Prerequisites
- Windows 10/11, macOS, or Linux
- Python 3.10 or 3.11 installed

### Step 1: Clone or Navigate to Directory
```powershell
cd "c:\Users\Lenovo\OneDrive\Desktop\INDOOR WELLNESS"
```

### Step 2: Set Up Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### Step 3: Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### Step 4: Seed Initial Demonstration Data
```powershell
python scripts/seed_demo_data.py
```

### Step 5: Launch the Application
Run the one-click launcher:
```powershell
python run.py
```
*(Or double-click `run.bat` on Windows)*

The application will start at **`http://localhost:8000`** and automatically open your default browser.

---

## 5. End-to-End Demonstration Guide (5–10 Minutes)

Follow this step-by-step walkthrough during project evaluation:

| Step | Action | Expected Result |
|---|---|---|
| **1** | Open `http://localhost:8000` | Executive Overview displays active KPIs, live shelf grid, and environmental status. |
| **2** | Click **"Smart Shelf Vision"** in sidebar | Opens detection viewport with Preset Demostration controls. |
| **3** | Click **"Demo Full Shelf"** | YOLO runs on staged image; Shelf 1 & 2 show `AVAILABLE` (green badge, 8/8 items). |
| **4** | Click **"Demo Low Stock"** | Shelf 1 transitions to `LOW STOCK` (amber badge, 2/8 items); toast alert fires; Alert Center records warning. |
| **5** | Click **"Demo Empty Shelf"** | Shelf 1 transitions to `EMPTY` (red badge, 0/8 items); critical alert fires. |
| **6** | Click **"Indoor Wellness AI"** | Displays real-time time-series telemetry with `DATA SOURCE: SOFTWARE SIMULATION`. |
| **7** | Switch scenario to **"Hazardous Event"** | PM2.5 and CO₂ spike; Kalman filter smooths trajectory; Ventilation transitions to `EMERGENCY PURGE (100% Fan)`. |
| **8** | Click **"Manual Input Form"** | Enter custom PM2.5 (e.g. 50.0) and CO₂ (e.g. 900); verify immediate calculation and persistence. |
| **9** | Click **"Alert Center"** | Shows logged shelf and air alerts; click **"Mark Resolved"** to demonstrate resolution workflow. |
| **10** | Click **"Analytics & Export"** | Review occupancy and product charts; click **"Download Audit Log (CSV)"** to inspect exported data. |
| **11** | Click **"System & Model"** | Inspect active YOLOv8 model information, inference latency, and test split evaluation metrics. |

---

## 6. REST API Reference

The FastAPI backend automatically provides interactive Swagger documentation at **`http://localhost:8000/docs`**.

### Key Endpoints:
- `GET /api/health` — Operational health check and zero-hardware verification.
- `POST /api/detect/image` — Run YOLO detection on uploaded image file.
- `POST /api/detect/demo?scenario={full|low|empty}` — Execute pre-staged demonstration scenarios.
- `POST /api/detect/live/start` — Test/start optional webcam feed with graceful fallback.
- `GET /api/shelves` / `POST /api/shelves` — CRUD operations for shelf ROIs and thresholds.
- `GET /api/environmental/latest` — Stream latest simulated/processed environmental data.
- `POST /api/environmental/scenario` — Switch simulation scenario.
- `POST /api/environmental/manual` — Ingest user-entered environmental telemetry.
- `POST /api/environmental/upload` — Ingest CSV or JSON datasets.
- `GET /api/alerts` / `POST /api/alerts/{id}/resolve` — Alert management and resolution.
- `GET /api/analytics/summary` / `GET /api/analytics/export` — Aggregate statistics and CSV export.
- `GET /api/settings` / `PUT /api/settings` — System parameter configuration.

---

## 7. Running Automated Tests

Run the full automated test suite using `pytest`:
```powershell
pytest tests/ -v
```

Complete Test Suite (47/47 passing, 100% Green):
- **Stock Occupancy & ROI Logic** (`tests/test_stock_logic.py`, 6 tests): Centroid intersection, threshold classification (`AVAILABLE`, `LOW STOCK`, `EMPTY`), temporal confirmation smoothing.
- **Environmental Simulation & Kalman** (`tests/test_simulation.py`, 6 tests): Multi-scenario telemetry generation, 1D Kalman noise reduction, parameter bounds.
- **EPA Breakpoints & ANN Prediction** (`tests/test_prediction.py`, 6 tests): Formula-accurate AQI calculation, MLP multi-horizon forecast (+1h, +3h, +6h), ventilation actuator logic.
- **Database Relational Integrity** (`tests/test_database.py`, 6 tests): SQLAlchemy schema, shelf CRUD, audit logging, alert state transitions.
- **FastAPI Endpoints & Integration** (`tests/test_api.py`, 7 tests): Static mount, health probe, image/video CV detection, CSV/JSON uploads, analytics export.
- **System Integrity & Smoke Test** (`tests/test_system_integrity.py`, 7 tests): Recovery state validation, sub-100ms CPU latency benchmark, zero-secret git hygiene, full E2E smoke test.
- **Live Deployment HTTPS Suite** (`tests/test_live_deployment.py`, 9 tests): Public HTTPS edge validation for UI, assets, health, live YOLO inference, multi-frame video, ANN forecasting, SQLite persistence, alerts, CSV export, and error resilience.

---

## 8. Cloud Deployment & Database Persistence Architecture

### Deployment Architecture
The platform is containerized for seamless cloud deployment on modern container platforms (e.g., Render, Railway, Fly.io, AWS ECS):
- **Container Runtime:** `python:3.11-slim` with system OpenCV libraries (`libgl1-mesa-glx`, `libglib2.0-0`).
- **Web Application Gateway:** Uvicorn ASGI server running behind Cloudflare / reverse proxy.
- **Zero-Hardware Guarantee:** Completely independent of physical IoT hardware or hardware accelerators; optimized for multi-threaded CPU inference.

### Production SQLite Persistence Guarantee
Standard ephemeral cloud containers wipe out local file systems upon redeployment or restart. To ensure **zero data loss**:
- The application dynamically reads `DATABASE_URL` from the environment.
- In production, it defaults to a dedicated persistent volume mount: `sqlite:////data/wellness.db`.
- The database operates in **Write-Ahead Logging (WAL)** mode (`PRAGMA journal_mode=WAL;`), providing high-concurrency read/write throughput without table locks.
- Render blueprint specification is provided in [`render.yaml`](file:///c:/Users/Lenovo/OneDrive/Desktop/INDOOR%20WELLNESS/render.yaml) with an explicit 1GB persistent disk mount at `/data`.

### One-Click Deploy on Render
Click the badge below or push to your connected Render account:
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/kiranbcrkbc/indoor-wellness-ai)

Or run locally with Docker:
```bash
docker build -t indoor-wellness-ai .
docker run -p 8000:8000 -v wellness-data:/data indoor-wellness-ai
```

---

## 9. GitHub Hygiene & Security

- **No Hard-coded Secrets:** Verified via automated regex scanning across all repository files. No API keys, passwords, or tokens in source code.
- **Clean `.gitignore`:** Strictly excludes SQLite `.db` binaries, `.venv` virtual environments, large model weights (`*.pt`), caches, and temporary files.
- **Reproducible Setup:** All dependencies pinned in `backend/requirements.txt`.

---

## 10. Limitations & Future Enhancements

- **Limitations:** Empty-shelf detection is relative to configured expected capacity and ROI boundaries. Real classification accuracy on retail goods depends on training images collected for specific packaging. Generic COCO models identify containers (bottles, cups, cans, boxes); specialized retail inventory can be fine-tuned via `scripts/train_model.py`.
- **Future Enhancements:** Multi-camera synchronization, cloud synchronization via MQTT/WebSockets, edge deployment on low-power devices, automated re-ordering integration with retail ERP systems.
