/**
 * Indoor Wellness & Smart Shelf AI System
 * Frontend Application Controller
 */

const App = (function () {
  let activeTab = "overview";
  let simulationRunning = true;
  let simInterval = null;

  // Chart instances
  let telemetryChart = null;
  let forecastChart = null;
  let overviewMiniChart = null;
  let shelfOccupancyChart = null;
  let productClassChart = null;

  // Telemetry buffer for time-series charts (max 20 points)
  const telemetryHistory = {
    labels: [],
    rawPm25: [],
    kfPm25: [],
    rawCo2: [],
    kfCo2: []
  };

  /* -------------------------------------------------------------------
     Initialization
     ------------------------------------------------------------------- */
  function init() {
    setupNavigation();
    setupSubtabs();
    setupDropZone();
    initCharts();
    feather.replace();

    // Initial data fetch
    refreshShelves();
    refreshKPIs();
    refreshAlerts();
    loadSettings();
    loadModelInfo();

    // Start simulation polling loop (every 2.5 seconds)
    startSimLoop();
  }

  /* -------------------------------------------------------------------
     Navigation & Tab Management
     ------------------------------------------------------------------- */
  function setupNavigation() {
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    navItems.forEach(item => {
      item.addEventListener("click", function (e) {
        e.preventDefault();
        const targetTab = this.getAttribute("data-tab");
        switchTab(targetTab);
      });
    });

    // Header alert button
    const btnQuickAlerts = document.getElementById("btn-quick-alerts");
    if (btnQuickAlerts) {
      btnQuickAlerts.addEventListener("click", () => switchTab("alerts"));
    }
  }

  function switchTab(tabId) {
    activeTab = tabId;

    // Update sidebar active link
    document.querySelectorAll(".sidebar-nav .nav-item").forEach(el => {
      el.classList.toggle("active", el.getAttribute("data-tab") === tabId);
    });

    // Update view panels
    document.querySelectorAll(".view-panel").forEach(panel => {
      panel.classList.remove("active");
    });
    const targetPanel = document.getElementById(`view-${tabId}`);
    if (targetPanel) {
      targetPanel.classList.add("active");
    }

    // Update titles
    const titles = {
      "overview": ["Executive Overview", "Unified Operations Center"],
      "smart-shelf": ["Smart Shelf AI Vision", "YOLOv8 Product Detection & Inventory Analysis"],
      "indoor-wellness": ["Indoor Wellness AI", "Environmental Simulation, Kalman Filter & Predictive Actuation"],
      "shelves": ["Shelf Management", "Region of Interest (ROI) & Threshold Configurations"],
      "alerts": ["Alert Center", "Automated Incident & Health Event Log"],
      "analytics": ["Analytics & Reports", "Historical Trends & Data Audit"],
      "settings": ["System Settings & Model Metadata", "Tunable Architecture Parameters"]
    };

    if (titles[tabId]) {
      document.getElementById("page-title").innerText = titles[tabId][0];
      document.getElementById("page-subtitle").innerText = titles[tabId][1];
    }

    // Tab-specific refreshes
    if (tabId === "analytics") {
      renderAnalyticsCharts();
    } else if (tabId === "shelves") {
      refreshShelvesTable();
    } else if (tabId === "alerts") {
      loadAlertsList("all");
    }

    feather.replace();
  }

  function setupSubtabs() {
    const pills = document.querySelectorAll(".tab-pills .tab-pill");
    pills.forEach(pill => {
      pill.addEventListener("click", function () {
        pills.forEach(p => p.classList.remove("active"));
        this.classList.add("active");

        const targetSub = this.getAttribute("data-subtab");
        document.querySelectorAll(".subtab-content").forEach(c => c.classList.remove("active"));
        const targetContent = document.getElementById(targetSub);
        if (targetContent) targetContent.classList.add("active");
        feather.replace();
      });
    });
  }

  /* -------------------------------------------------------------------
     Drop Zone & Custom Image Upload
     ------------------------------------------------------------------- */
  function setupDropZone() {
    // Image drop zone
    const dropZone = document.getElementById("image-drop-zone");
    const fileInput = document.getElementById("image-file-input");

    if (dropZone && fileInput) {
      dropZone.addEventListener("click", () => fileInput.click());
      dropZone.addEventListener("dragover", e => {
        e.preventDefault();
        dropZone.style.borderColor = "var(--color-primary)";
      });
      dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "rgba(255, 255, 255, 0.15)";
      });
      dropZone.addEventListener("drop", e => {
        e.preventDefault();
        dropZone.style.borderColor = "rgba(255, 255, 255, 0.15)";
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          handleImageUpload(e.dataTransfer.files[0]);
        }
      });
      fileInput.addEventListener("change", e => {
        if (e.target.files && e.target.files.length > 0) {
          handleImageUpload(e.target.files[0]);
        }
      });
    }

    // Video drop zone (FR-10)
    const videoDropZone = document.getElementById("video-drop-zone");
    const videoFileInput = document.getElementById("video-file-input");

    if (videoDropZone && videoFileInput) {
      videoDropZone.addEventListener("click", () => videoFileInput.click());
      videoDropZone.addEventListener("dragover", e => {
        e.preventDefault();
        videoDropZone.style.borderColor = "var(--color-primary)";
      });
      videoDropZone.addEventListener("dragleave", () => {
        videoDropZone.style.borderColor = "rgba(255, 255, 255, 0.15)";
      });
      videoDropZone.addEventListener("drop", e => {
        e.preventDefault();
        videoDropZone.style.borderColor = "rgba(255, 255, 255, 0.15)";
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
          handleVideoUpload(e.dataTransfer.files[0]);
        }
      });
      videoFileInput.addEventListener("change", e => {
        if (e.target.files && e.target.files.length > 0) {
          handleVideoUpload(e.target.files[0]);
        }
      });
    }
  }

  async function handleImageUpload(file) {
    showToast("Processing image with YOLOv8...", "info");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/detect/image", {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Detection failed");
      }
      const data = await res.json();
      renderDetectionResults(data);
      showToast(`Processed: ${data.total_detections} items detected`, "success");
      updateSourceTag(`IMAGE UPLOAD: ${file.name}`);
      refreshKPIs();
      refreshAlerts();
    } catch (err) {
      showToast(`Upload Error: ${err.message}`, "danger");
    }
  }

  async function handleVideoUpload(file) {
    showToast("Sampling frames & analyzing video stream...", "info");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/detect/video", {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Video processing failed");
      }
      const data = await res.json();
      renderDetectionResults(data);
      showToast(`Video processed: ${data.frames_sampled} frames evaluated across stream`, "success");
      updateSourceTag(`VIDEO UPLOAD: ${file.name}`);
      refreshKPIs();
      refreshAlerts();
      refreshShelves();
    } catch (err) {
      showToast(`Video Upload Error: ${err.message}`, "danger");
    }
  }

  /* -------------------------------------------------------------------
     Smart Shelf: Preset Demonstrations (Full, Low, Empty)
     ------------------------------------------------------------------- */
  async function runPresetScenario(scenario) {
    showToast(`Running preset demonstration: ${scenario.toUpperCase()}...`, "info");
    try {
      const res = await fetch(`/api/detect/demo?scenario=${scenario}`, { method: "POST" });
      if (!res.ok) throw new Error("Preset run failed");
      const data = await res.json();
      renderDetectionResults(data);
      updateSourceTag(`DEMO SCENARIO: ${scenario.toUpperCase()}`);
      showToast(`Completed: ${data.total_detections} items recognized`, "success");
      refreshKPIs();
      refreshAlerts();
      refreshShelves();
    } catch (err) {
      showToast(`Preset Error: ${err.message}`, "danger");
    }
  }

  function renderDetectionResults(data) {
    // 1. Display Annotated Image
    const imgEl = document.getElementById("annotated-result-img");
    const placeholder = document.getElementById("canvas-placeholder");
    if (data.annotated_image_url) {
      imgEl.src = data.annotated_image_url;
      imgEl.style.display = "block";
      placeholder.style.display = "none";
    }

    // 2. Latency tag
    const latencyEl = document.getElementById("cv-processing-latency");
    if (latencyEl && data.processing_time_ms) {
      latencyEl.innerText = `Inference: ${data.processing_time_ms} ms (CPU)`;
    }

    // 3. Per-Shelf Results
    const shelfCardsContainer = document.getElementById("cv-shelf-status-cards");
    if (shelfCardsContainer && data.shelf_statuses) {
      let html = "";
      for (const [sid, info] of Object.entries(data.shelf_statuses)) {
        const statusClass = info.status.toLowerCase().replace(/\s+/g, "-");
        const badgeClass = `badge-${statusClass}`;
        const pct = Math.round(info.occupancy_ratio * 100);

        html += `
          <div class="shelf-result-card">
            <div class="shelf-result-top">
              <span class="shelf-name">Shelf ID #${sid}</span>
              <span class="badge ${badgeClass}">${info.status}</span>
            </div>
            <div class="d-flex justify-between" style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-muted);">
              <span>Count: ${info.detected_count} / ${info.expected_capacity} items</span>
              <span>Occupancy: ${pct}%</span>
            </div>
            <div class="shelf-result-bar">
              <div class="shelf-result-fill ${badgeClass}" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      }
      shelfCardsContainer.innerHTML = html;
    }

    // 4. Product Class Counts
    const classContainer = document.getElementById("cv-class-counts-container");
    const totalBadge = document.getElementById("cv-total-detections-badge");
    if (totalBadge) totalBadge.innerText = `${data.total_detections} items`;

    if (classContainer) {
      if (data.class_counts && Object.keys(data.class_counts).length > 0) {
        let pills = "";
        for (const [cname, cnt] of Object.entries(data.class_counts)) {
          pills += `
            <div class="class-pill">
              <span class="class-pill-name">${cname}</span>
              <span class="class-pill-count">${cnt}</span>
            </div>
          `;
        }
        classContainer.innerHTML = pills;
      } else {
        classContainer.innerHTML = `<p class="text-muted">No items detected in frame.</p>`;
      }
    }
  }

  /* -------------------------------------------------------------------
     Webcam Handler
     ------------------------------------------------------------------- */
  async function startWebcam() {
    try {
      const res = await fetch("/api/detect/live/start", { method: "POST" });
      const data = await res.json();
      const alertBox = document.getElementById("webcam-status-alert");
      if (data.status === "unavailable") {
        alertBox.className = "alert-box alert-warning mt-2";
        alertBox.innerHTML = `<i data-feather="alert-triangle"></i> ${data.message}`;
        showToast("Webcam hardware not detected. Using software demo modes.", "warning");
      } else {
        alertBox.className = "alert-box alert-success mt-2";
        alertBox.innerHTML = `<i data-feather="check-circle"></i> Camera session active: ${data.session_id}`;
        showToast("Webcam session initiated.", "success");
      }
      feather.replace();
    } catch (err) {
      showToast("Error checking webcam: " + err.message, "danger");
    }
  }

  /* -------------------------------------------------------------------
     Indoor Wellness AI: Simulation & Telemetry Loop
     ------------------------------------------------------------------- */
  function startSimLoop() {
    if (simInterval) clearInterval(simInterval);
    simInterval = setInterval(async () => {
      if (!simulationRunning) return;
      await fetchSimStep();
    }, 2500);
  }

  async function fetchSimStep() {
    try {
      const res = await fetch("/api/environmental/latest");
      if (!res.ok) return;
      const data = await res.json();
      updateEnvironmentalUI(data);
    } catch (err) {
      console.warn("Telemetry fetch error:", err);
    }
  }

  function updateEnvironmentalUI(data) {
    const raw = data.raw;
    const kf = data.kalman_filtered;
    const pred = data.prediction;

    // Overview gauges
    const elPm25 = document.getElementById("overview-pm25");
    const elCo2 = document.getElementById("overview-co2");
    const elVoc = document.getElementById("overview-voc");
    const elVent = document.getElementById("overview-vent-status");
    const elFan = document.getElementById("overview-fan-power");

    if (elPm25) elPm25.innerText = `${kf.pm25} µg/m³`;
    if (elCo2) elCo2.innerText = `${kf.co2} ppm`;
    if (elVoc) elVoc.innerText = `${raw.voc} ppb`;
    if (elVent) elVent.innerText = pred.ventilation_recommendation;
    if (elFan) elFan.innerText = `Actuator Fan: ${pred.actuator_power_level}%`;

    // Overview bars
    const barPm25 = document.getElementById("bar-pm25");
    const barCo2 = document.getElementById("bar-co2");
    const barVoc = document.getElementById("bar-voc");
    if (barPm25) barPm25.style.width = `${Math.min(100, (kf.pm25 / 150) * 100)}%`;
    if (barCo2) barCo2.style.width = `${Math.min(100, (kf.co2 / 2000) * 100)}%`;
    if (barVoc) barVoc.style.width = `${Math.min(100, (raw.voc / 1000) * 100)}%`;

    // Actuator card (Indoor Wellness View)
    const actAqi = document.getElementById("actuator-aqi-val");
    const actCat = document.getElementById("actuator-aqi-cat");
    const actDriver = document.getElementById("actuator-primary-pollutant");
    const actFan = document.getElementById("actuator-fan-val");
    const actPill = document.getElementById("actuator-status-pill");

    if (actAqi) actAqi.innerText = pred.current_aqi;
    if (actCat) actCat.innerText = pred.category;
    if (actDriver) actDriver.innerText = pred.primary_pollutant;
    if (actFan) actFan.innerText = `${pred.actuator_power_level}%`;
    if (actPill) {
      actPill.innerText = pred.ventilation_recommendation;
      actPill.style.background = pred.actuator_power_level > 70 ? "var(--color-rose-glow)" : "var(--color-emerald-glow)";
      actPill.style.borderColor = pred.actuator_power_level > 70 ? "var(--color-rose)" : "var(--color-emerald)";
      actPill.style.color = pred.actuator_power_level > 70 ? "#f87171" : "#34d399";
    }

    // Update KPI Card
    const kpiAqi = document.getElementById("kpi-aqi");
    const kpiCat = document.getElementById("kpi-aqi-category");
    if (kpiAqi) kpiAqi.innerText = pred.current_aqi;
    if (kpiCat) kpiCat.innerHTML = `<span class="text-${pred.severity === 'CRITICAL' ? 'rose' : 'emerald'}">● ${pred.category}</span> (ANN Forecast)`;

    // Push into chart buffer
    const timestamp = new Date().toLocaleTimeString();
    if (telemetryHistory.labels.length >= 15) {
      telemetryHistory.labels.shift();
      telemetryHistory.rawPm25.shift();
      telemetryHistory.kfPm25.shift();
      telemetryHistory.rawCo2.shift();
      telemetryHistory.kfCo2.shift();
    }
    telemetryHistory.labels.push(timestamp);
    telemetryHistory.rawPm25.push(raw.pm25);
    telemetryHistory.kfPm25.push(kf.pm25);
    telemetryHistory.rawCo2.push(raw.co2);
    telemetryHistory.kfCo2.push(kf.co2);

    updateTelemetryCharts(pred);
  }

  function toggleSimulation() {
    simulationRunning = !simulationRunning;
    const btn = document.getElementById("btn-toggle-sim");
    if (btn) {
      btn.innerHTML = simulationRunning
        ? `<i data-feather="pause"></i> Pause Simulation`
        : `<i data-feather="play"></i> Resume Simulation`;
      feather.replace();
    }
    showToast(simulationRunning ? "Simulation active" : "Simulation paused", "info");
  }

  async function stepSimulation() {
    await fetchSimStep();
    showToast("Simulation advanced by 1 step", "info");
  }

  async function changeScenario(scenarioName) {
    try {
      const res = await fetch(`/api/environmental/scenario?scenario=${encodeURIComponent(scenarioName)}`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to change scenario");
      const data = await res.json();
      showToast(`Active scenario switched to: ${scenarioName}`, "success");
      const el = document.getElementById("overview-sim-scenario");
      if (el) el.innerText = scenarioName;
      await fetchSimStep();
    } catch (err) {
      showToast(err.message, "danger");
    }
  }

  /* -------------------------------------------------------------------
     Charts (Telemetry & ANN Forecast)
     ------------------------------------------------------------------- */
  function initCharts() {
    // 1. Overview Mini Chart
    const ctxMini = document.getElementById("overviewMiniChart")?.getContext("2d");
    if (ctxMini) {
      overviewMiniChart = new Chart(ctxMini, {
        type: "line",
        data: {
          labels: [],
          datasets: [{
            label: "PM2.5 (µg/m³)",
            data: [],
            borderColor: "#6366f1",
            backgroundColor: "rgba(99, 102, 241, 0.1)",
            fill: true,
            tension: 0.3,
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { display: false },
            y: { grid: { color: "rgba(255, 255, 255, 0.05)" } }
          }
        }
      });
    }

    // 2. Full Telemetry Chart (Raw vs Kalman Filtered)
    const ctxTel = document.getElementById("telemetryChart")?.getContext("2d");
    if (ctxTel) {
      telemetryChart = new Chart(ctxTel, {
        type: "line",
        data: {
          labels: [],
          datasets: [
            {
              label: "Raw PM2.5 (Sensor Noise)",
              data: [],
              borderColor: "rgba(239, 68, 68, 0.4)",
              borderDash: [4, 4],
              borderWidth: 1.5,
              tension: 0.1
            },
            {
              label: "Kalman Filtered PM2.5",
              data: [],
              borderColor: "#10b981",
              backgroundColor: "rgba(16, 185, 129, 0.1)",
              fill: true,
              borderWidth: 2.5,
              tension: 0.3
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: "#94a3b8", font: { family: "Plus Jakarta Sans" } } }
          },
          scales: {
            x: { ticks: { color: "#64748b" }, grid: { color: "rgba(255,255,255,0.03)" } },
            y: { ticks: { color: "#64748b" }, grid: { color: "rgba(255,255,255,0.05)" } }
          }
        }
      });
    }

    // 3. ANN Forecast Chart
    const ctxFc = document.getElementById("forecastChart")?.getContext("2d");
    if (ctxFc) {
      forecastChart = new Chart(ctxFc, {
        type: "bar",
        data: {
          labels: ["Current AQI", "+1h Forecast", "+3h Forecast", "+6h Forecast"],
          datasets: [{
            label: "Predicted AQI Index",
            data: [25, 30, 35, 40],
            backgroundColor: ["#3b82f6", "#6366f1", "#8b5cf6", "#a855f7"],
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: "#94a3b8" }, grid: { display: false } },
            y: { ticks: { color: "#64748b" }, grid: { color: "rgba(255,255,255,0.05)" }, beginAtZero: true, max: 200 }
          }
        }
      });
    }
  }

  function updateTelemetryCharts(pred) {
    if (telemetryChart) {
      telemetryChart.data.labels = telemetryHistory.labels;
      telemetryChart.data.datasets[0].data = telemetryHistory.rawPm25;
      telemetryChart.data.datasets[1].data = telemetryHistory.kfPm25;
      telemetryChart.update("none");
    }

    if (overviewMiniChart) {
      overviewMiniChart.data.labels = telemetryHistory.labels;
      overviewMiniChart.data.datasets[0].data = telemetryHistory.kfPm25;
      overviewMiniChart.update("none");
    }

    if (forecastChart && pred) {
      forecastChart.data.datasets[0].data = [
        pred.current_aqi,
        pred.forecast_1h,
        pred.forecast_3h,
        pred.forecast_6h
      ];
      forecastChart.update("none");
    }
  }

  /* -------------------------------------------------------------------
     Shelf Management & Overview Lists
     ------------------------------------------------------------------- */
  async function refreshShelves() {
    try {
      const res = await fetch("/api/shelves");
      if (!res.ok) return;
      const shelves = await res.json();

      const listContainer = document.getElementById("overview-shelf-list");
      if (listContainer) {
        if (shelves.length === 0) {
          listContainer.innerHTML = `<div class="empty-state">No shelf ROIs configured yet.</div>`;
        } else {
          listContainer.innerHTML = shelves.map(s => {
            const statusClass = (s.current_status || "AVAILABLE").toLowerCase().replace(/\s+/g, "-");
            const badgeClass = `badge-${statusClass}`;
            const pct = Math.round((s.current_occupancy || 0) * 100);
            return `
              <div class="shelf-status-item">
                <div class="shelf-name-group">
                  <span class="shelf-name">${s.name}</span>
                  <span class="shelf-capacity-meta">Capacity: ${s.current_count} / ${s.expected_capacity} (${pct}%)</span>
                </div>
                <span class="badge ${badgeClass}">${s.current_status}</span>
              </div>
            `;
          }).join("");
        }
      }
    } catch (err) {
      console.warn("Shelf fetch error:", err);
    }
  }

  async function refreshShelvesTable() {
    try {
      const res = await fetch("/api/shelves");
      if (!res.ok) return;
      const shelves = await res.json();
      const tbody = document.getElementById("shelves-table-body");
      if (!tbody) return;

      if (shelves.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-center">No shelves defined. Click "Add New Shelf ROI" above.</td></tr>`;
        return;
      }

      tbody.innerHTML = shelves.map(s => {
        const statusClass = (s.current_status || "AVAILABLE").toLowerCase().replace(/\s+/g, "-");
        const badgeClass = `badge-${statusClass}`;
        const roiStr = JSON.stringify(s.roi_coordinates || []);
        return `
          <tr>
            <td><strong>#${s.shelf_id}</strong></td>
            <td><strong>${s.name}</strong></td>
            <td><code>${roiStr.length > 25 ? roiStr.substring(0, 25) + '...' : roiStr}</code></td>
            <td>${s.expected_capacity} items</td>
            <td>${s.low_stock_threshold * 100}%</td>
            <td>${s.empty_threshold * 100}%</td>
            <td><span class="badge ${badgeClass}">${s.current_status}</span></td>
            <td>
              <button class="btn btn-outline btn-sm" onclick="App.deleteShelf(${s.shelf_id})">Delete</button>
            </td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      console.error(err);
    }
  }

  async function deleteShelf(shelfId) {
    if (!confirm(`Delete Shelf #${shelfId}?`)) return;
    try {
      const res = await fetch(`/api/shelves/${shelfId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Delete failed");
      showToast("Shelf deleted", "success");
      refreshShelvesTable();
      refreshShelves();
    } catch (err) {
      showToast(err.message, "danger");
    }
  }

  async function submitNewShelf(e) {
    e.preventDefault();
    const name = document.getElementById("add-shelf-name").value;
    const capacity = parseInt(document.getElementById("add-shelf-capacity").value);
    const tl = document.getElementById("add-shelf-tl").value.split(",").map(v => parseFloat(v.trim()));
    const br = document.getElementById("add-shelf-br").value.split(",").map(v => parseFloat(v.trim()));

    try {
      const res = await fetch("/api/shelves", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name,
          roi_coordinates: [tl, br],
          expected_capacity: capacity,
          low_stock_threshold: 0.35,
          empty_threshold: 0.05
        })
      });
      if (!res.ok) throw new Error("Failed to create shelf");
      closeModals();
      showToast("Shelf ROI created successfully", "success");
      refreshShelvesTable();
      refreshShelves();
    } catch (err) {
      showToast(err.message, "danger");
    }
  }

  /* -------------------------------------------------------------------
     KPIs & Alerts
     ------------------------------------------------------------------- */
  async function refreshKPIs() {
    try {
      const res = await fetch("/api/analytics/summary");
      if (!res.ok) return;
      const data = await res.json();
      const kpis = data.kpis;

      const elDet = document.getElementById("kpi-detections");
      const elStock = document.getElementById("kpi-stocked-shelves");
      const elLow = document.getElementById("kpi-low-stock");
      const elStockPct = document.getElementById("kpi-stock-pct");

      if (elDet) elDet.innerText = kpis.total_detections;
      if (elStock) elStock.innerText = `${kpis.available_shelves} / ${kpis.total_shelves}`;
      if (elLow) elLow.innerText = kpis.low_stock_shelves;

      if (elStockPct && kpis.total_shelves > 0) {
        const pct = Math.round((kpis.available_shelves / kpis.total_shelves) * 100);
        elStockPct.innerText = `${pct}% Full Capacity`;
      }
    } catch (err) {
      console.warn("KPI error:", err);
    }
  }

  async function refreshAlerts() {
    try {
      const res = await fetch("/api/alerts?resolved=false");
      if (!res.ok) return;
      const alerts = await res.json();

      const badge = document.getElementById("sidebar-alert-badge");
      const dot = document.getElementById("header-alert-dot");
      if (badge) {
        badge.innerText = alerts.length;
        badge.style.display = alerts.length > 0 ? "inline-flex" : "none";
      }
      if (dot) {
        dot.style.display = alerts.length > 0 ? "block" : "none";
      }
    } catch (err) {
      console.warn("Alerts poll error:", err);
    }
  }

  async function loadAlertsList(filter) {
    try {
      let url = "/api/alerts";
      if (filter === "CRITICAL" || filter === "WARNING") {
        url += `?severity=${filter}&resolved=false`;
      } else if (filter === "resolved") {
        url += `?resolved=true`;
      }

      const res = await fetch(url);
      if (!res.ok) return;
      const alerts = await res.json();
      const container = document.getElementById("alerts-list-group");
      if (!container) return;

      if (alerts.length === 0) {
        container.innerHTML = `<div class="empty-state">No alerts found under filter "${filter}".</div>`;
        return;
      }

      container.innerHTML = alerts.map(a => {
        const sev = (a.severity || "info").toLowerCase();
        return `
          <div class="alert-row ${sev}">
            <div class="alert-info-group">
              <span class="alert-msg">${a.message}</span>
              <span class="alert-time">${new Date(a.created_at).toLocaleString()} • Type: ${a.alert_type}</span>
            </div>
            ${!a.is_resolved ? `<button class="btn btn-outline btn-sm" onclick="App.resolveAlert(${a.alert_id})">Mark Resolved</button>` : `<span class="badge badge-emerald">Resolved</span>`}
          </div>
        `;
      }).join("");
    } catch (err) {
      console.error(err);
    }
  }

  async function resolveAlert(alertId) {
    try {
      const res = await fetch(`/api/alerts/${alertId}/resolve`, { method: "POST" });
      if (!res.ok) throw new Error("Failed to resolve alert");
      showToast("Alert resolved", "success");
      loadAlertsList("all");
      refreshAlerts();
    } catch (err) {
      showToast(err.message, "danger");
    }
  }

  async function resolveAllAlerts() {
    try {
      const res = await fetch("/api/alerts/resolve-all", { method: "POST" });
      if (!res.ok) throw new Error("Failed to resolve all alerts");
      showToast("All active alerts resolved", "success");
      loadAlertsList("all");
      refreshAlerts();
    } catch (err) {
      showToast(err.message, "danger");
    }
  }

  /* -------------------------------------------------------------------
     Analytics Charts
     ------------------------------------------------------------------- */
  async function renderAnalyticsCharts() {
    try {
      const res = await fetch("/api/analytics/summary");
      if (!res.ok) return;
      const data = await res.json();

      // Occupancy Bar Chart
      const ctxOcc = document.getElementById("shelfOccupancyBarChart")?.getContext("2d");
      if (ctxOcc) {
        if (shelfOccupancyChart) shelfOccupancyChart.destroy();
        const labels = data.shelf_distribution.map(s => s.name);
        const values = data.shelf_distribution.map(s => s.occupancy_pct);

        shelfOccupancyChart = new Chart(ctxOcc, {
          type: "bar",
          data: {
            labels: labels,
            datasets: [{
              label: "Occupancy %",
              data: values,
              backgroundColor: values.map(v => v <= 5 ? "#ef4444" : (v <= 35 ? "#f59e0b" : "#10b981")),
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: { ticks: { color: "#94a3b8" }, grid: { display: false } },
              y: { ticks: { color: "#64748b" }, grid: { color: "rgba(255,255,255,0.05)" }, max: 100 }
            }
          }
        });
      }

      // Product Class Donut Chart
      const ctxProd = document.getElementById("productClassDonutChart")?.getContext("2d");
      if (ctxProd) {
        if (productClassChart) productClassChart.destroy();
        const pLabels = Object.keys(data.product_distribution);
        const pValues = Object.values(data.product_distribution);

        productClassChart = new Chart(ctxProd, {
          type: "doughnut",
          data: {
            labels: pLabels.length > 0 ? pLabels : ["Sample Beverage", "Snack Pack"],
            datasets: [{
              data: pValues.length > 0 ? pValues : [12, 8],
              backgroundColor: ["#6366f1", "#3b82f6", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"],
              borderWidth: 0
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: "right", labels: { color: "#94a3b8" } }
            }
          }
        });
      }
    } catch (err) {
      console.error(err);
    }
  }

  /* -------------------------------------------------------------------
     Settings & Model Metadata
     ------------------------------------------------------------------- */
  async function loadSettings() {
    try {
      const res = await fetch("/api/settings");
      if (!res.ok) return;
      const settings = await res.json();

      if (settings.confidence_threshold) {
        document.getElementById("conf-threshold-slider").value = settings.confidence_threshold;
        document.getElementById("conf-val").innerText = settings.confidence_threshold;
      }
      if (settings.low_stock_threshold) {
        document.getElementById("low-threshold-slider").value = settings.low_stock_threshold;
        document.getElementById("low-val").innerText = settings.low_stock_threshold;
      }
      if (settings.empty_threshold) {
        document.getElementById("empty-threshold-slider").value = settings.empty_threshold;
        document.getElementById("empty-val").innerText = settings.empty_threshold;
      }
      if (settings.aqi_hazardous_threshold) {
        document.getElementById("aqi-threshold-slider").value = settings.aqi_hazardous_threshold;
        document.getElementById("aqi-val").innerText = settings.aqi_hazardous_threshold;
      }
    } catch (err) {
      console.warn("Settings fetch error:", err);
    }
  }

  async function saveSettings(e) {
    e.preventDefault();
    const payload = {
      confidence_threshold: parseFloat(document.getElementById("conf-threshold-slider").value),
      low_stock_threshold: parseFloat(document.getElementById("low-threshold-slider").value),
      empty_threshold: parseFloat(document.getElementById("empty-threshold-slider").value),
      aqi_hazardous_threshold: parseFloat(document.getElementById("aqi-threshold-slider").value)
    };

    try {
      const res = await fetch("/api/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Failed to save settings");
      showToast("System settings updated successfully", "success");
    } catch (err) {
      showToast(err.message, "danger");
    }
  }

  async function loadModelInfo() {
    try {
      const res = await fetch("/api/settings/model/info");
      if (!res.ok) return;
      const info = await res.json();

      const archEl = document.getElementById("mi-arch");
      const pathEl = document.getElementById("mi-path");
      const topbarModel = document.getElementById("topbar-model-name");
      if (archEl) archEl.innerText = info.model_name;
      if (pathEl) pathEl.innerText = info.weights_path;
      if (topbarModel) topbarModel.innerText = info.model_name;
    } catch (err) {
      console.warn(err);
    }
  }

  /* -------------------------------------------------------------------
     Modals: Manual Input & File Ingestion
     ------------------------------------------------------------------- */
  function openManualInputModal() {
    document.getElementById("modal-manual-input").classList.add("active");
  }

  function openFileUploadModal() {
    document.getElementById("modal-file-upload").classList.add("active");
  }

  function openAddShelfModal() {
    document.getElementById("modal-add-shelf").classList.add("active");
  }

  function closeModals() {
    document.querySelectorAll(".modal-backdrop").forEach(m => m.classList.remove("active"));
  }

  async function submitManualEnvironmental(e) {
    e.preventDefault();
    const payload = {
      pm25: parseFloat(document.getElementById("m-pm25").value),
      co2: parseFloat(document.getElementById("m-co2").value),
      voc: parseFloat(document.getElementById("m-voc").value),
      temperature: parseFloat(document.getElementById("m-temp").value),
      humidity: parseFloat(document.getElementById("m-hum").value),
      source: "MANUAL"
    };

    try {
      const res = await fetch("/api/environmental/manual", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Manual submission failed");
      const data = await res.json();
      closeModals();
      showToast("Manual reading ingested & Kalman filtered", "success");
      updateSourceTag("MANUAL SOFTWARE ENTRY");
      updateEnvironmentalUI({
        raw: data.raw,
        kalman_filtered: data.kalman_filtered,
        prediction: data.prediction
      });
    } catch (err) {
      showToast(err.message, "danger");
    }
  }

  async function submitFileEnvironmental(e) {
    e.preventDefault();
    const fileInput = document.getElementById("env-file-input");
    if (!fileInput.files || fileInput.files.length === 0) return;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
      const res = await fetch("/api/environmental/upload", {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload failed");
      }
      const data = await res.json();
      closeModals();
      showToast(`Imported ${data.readings_imported} environmental records`, "success");
      updateSourceTag(`FILE INGESTION: ${fileInput.files[0].name}`);
      await fetchSimStep();
    } catch (err) {
      showToast(err.message, "danger");
    }
  }

  /* -------------------------------------------------------------------
     Helpers & Utilities
     ------------------------------------------------------------------- */
  function updateSourceTag(label) {
    const el = document.getElementById("source-name");
    if (el) el.innerText = `DATA SOURCE: ${label}`;
  }

  function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  return {
    init,
    switchTab,
    runPresetScenario,
    startWebcam,
    toggleSimulation,
    stepSimulation,
    changeScenario,
    refreshShelves,
    deleteShelf,
    submitNewShelf,
    resolveAlert,
    resolveAllAlerts,
    openManualInputModal,
    openFileUploadModal,
    openAddShelfModal,
    closeModals,
    submitManualEnvironmental,
    submitFileEnvironmental,
    saveSettings
  };
})();

document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
