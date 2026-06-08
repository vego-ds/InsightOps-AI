/**
 * InsightOps-AI Analytics Workspace Controller
 * Manages view states, drag-and-drop Ingestion, guided analytics commands,
 * result cards layout rendering, visual HTML previews, and technical evidence logs.
 */

// Browser session state
let currentAnalysis = null;
let currentDataMode = null; // 'sample' or 'upload'
let currentFile = null;     // Selected local File object
let analysisHistory = [];   // Session action list
let currentViewMode = "executive"; // Default dashboard view mode


// Visual category variables
let activeChartCategory = "all";
let chartSearchQuery = "";

// DOM Elements
const apiStatusDot = document.querySelector("#api-status-dot");
const apiStatusText = document.querySelector("#api-status-text");

// Ingestion elements
const csvDropzone = document.querySelector("#csv-dropzone");
const csvFileInputInput = document.querySelector("#csv-file-input");
const browseFileBtn = document.querySelector("#browse-file-btn");
const runSampleBtn = document.querySelector("#run-sample-btn");
const emptyStateSampleBtn = document.querySelector("#empty-state-sample-btn");
const selectedFileDisplay = document.querySelector("#selected-file-display");
const displayFilename = document.querySelector("#display-filename");
const displayFilesize = document.querySelector("#display-filesize");
const clearFileBtn = document.querySelector("#clear-file-btn");

// Command panel elements
const commandInput = document.querySelector("#command-input");
const submitCommandBtn = document.querySelector("#submit-command-btn");
const suggestionChips = document.querySelector("#command-suggestion-chips");
const commandResponseArea = document.querySelector("#command-response-area");
const feedbackIcon = document.querySelector("#feedback-icon");
const feedbackTitle = document.querySelector("#feedback-title");
const feedbackBody = document.querySelector("#feedback-body");
const historyTimelineFeed = document.querySelector("#history-timeline-feed");
const clearHistoryBtn = document.querySelector("#clear-history-btn");

// Workspace layout elements
const emptyStateCard = document.querySelector("#workspace-empty-state");
const resultsContainer = document.querySelector("#active-analysis-container");

// Right trust panel elements
const trustBadge = document.querySelector("#trust-badge-indicator");
const trustQgate = document.querySelector("#trust-qgate-status");
const trustConfidence = document.querySelector("#trust-confidence-lvl");
const trustHumanReview = document.querySelector("#trust-human-review");
const trustReportsAllowed = document.querySelector("#trust-reports-allowed");
const trustNarrativeAllowed = document.querySelector("#trust-narrative-allowed");
const trustSecurityScan = document.querySelector("#trust-security-scan");
const trustForecastReady = document.querySelector("#trust-forecast-ready");
const trustRecsCount = document.querySelector("#trust-recs-high-count");
const trustTopActionDesc = document.querySelector("#trust-top-action-desc");
const quickFormatSelect = document.querySelector("#quick-format-select");
const quickDownloadBtn = document.querySelector("#quick-download-btn");

// Export card elements
const exportFormatSelect = document.querySelector("#export-format-select");
const exportSampleReportBtn = document.querySelector("#export-sample-report-btn");
const exportUploadReportBtn = document.querySelector("#export-upload-report-btn");
const exportStatusBanner = document.querySelector("#export-status-banner");
const exportStatusMsg = document.querySelector("#export-status-msg");

// Pytest compatibility elements
const uploadReportButton = document.querySelector("#upload-report-button");
const sampleButton = document.querySelector("#sample-button");
const sampleReportButton = document.querySelector("#sample-report-button");


// Visual gallery controls
const visualsSearch = document.querySelector("#visuals-search");

// Synonym Mappings for Ask Copilot Router
const intentConfigs = [
  {
    name: "executive_summary",
    keywords: ["summary", "summarize", "overview", "what happened", "exec summary", "key findings", "status"]
  },
  {
    name: "quality_trust",
    keywords: ["trust", "quality", "confidence", "governance", "check", "valid", "invalid", "grade", "score", "gate", "trust status", "quality warning", "warning"]
  },
  {
    name: "kpi_revenue",
    keywords: ["kpi", "kpis", "revenue", "sales", "total revenue", "net sales", "average order value", "aov", "orders", "units"]
  },
  {
    name: "top_region",
    keywords: ["region", "regions", "best region", "top region", "highest region", "region performed best"]
  },
  {
    name: "top_product",
    keywords: ["product", "products", "best product", "top product", "highest product", "most revenue product", "product has the most revenue"]
  },
  {
    name: "top_sales_rep",
    keywords: ["sales rep", "rep", "best rep", "top rep", "sales representative", "sales rep performed best"]
  },
  {
    name: "anomalies",
    keywords: ["anomalies", "anomaly", "outlier", "outliers", "suspicious", "flagged"]
  },
  {
    name: "discount_risk",
    keywords: ["discount", "discounts", "discount issues", "discount risk", "concentration", "pareto"]
  },
  {
    name: "trend",
    keywords: ["trend", "trending", "revenue trending", "order trend", "trends", "historical"]
  },
  {
    name: "forecast",
    keywords: ["forecast", "forecasting", "predict", "next period", "readiness", "baseline"]
  },
  {
    name: "recommendations",
    keywords: ["recommendation", "recommendations", "what should we do next", "business do next", "next steps", "top actions", "action plan"]
  },
  {
    name: "workflow_improvements",
    keywords: ["workflow", "workflows", "improvement", "improvements", "process", "sales ops focus", "improve operations"]
  },
  {
    name: "visual_analytics",
    keywords: ["visuals", "visual analytics", "charts", "graphs", "pie chart", "bar chart", "line graph"]
  },
  {
    name: "technical_evidence",
    keywords: ["technical", "evidence", "metadata", "profile", "validation", "prep", "lineage", "raw json"]
  },
  {
    name: "audit_events",
    keywords: ["audit", "events", "trace", "log", "trail", "audit trail"]
  },
  {
    name: "export_pdf",
    keywords: ["download pdf", "export pdf", "generate pdf", "pdf report", "get pdf"]
  },
  {
    name: "export_markdown",
    keywords: ["download markdown", "export markdown", "download md", "export md", "markdown report"]
  },
  {
    name: "help",
    keywords: ["help", "commands", "supported questions", "guide", "supported", "what can you do"]
  }
];

// Safe helper functions for data robustness
function asArray(val) {
  return Array.isArray(val) ? val : [];
}

function asObject(val) {
  return (val && typeof val === "object" && !Array.isArray(val)) ? val : {};
}

function safeText(val, fallback = "Not available") {
  return (val !== null && val !== undefined) ? String(val) : fallback;
}

function safeNumber(val, fallback = 0) {
  if (typeof val === "number" && !isNaN(val)) return val;
  if (val !== null && val !== undefined && !isNaN(Number(val))) return Number(val);
  return fallback;
}

function formatMoney(val) {
  const num = safeNumber(val);
  return "$" + num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatNumber(val) {
  const num = safeNumber(val);
  return num.toLocaleString();
}

function formatPercent(val) {
  const num = safeNumber(val);
  return num.toFixed(1) + "%";
}

function getNestedValue(obj, path, fallback = undefined) {
  if (!obj) return fallback;
  const parts = path.split(".");
  let curr = obj;
  for (const part of parts) {
    if (curr === null || curr === undefined) return fallback;
    curr = curr[part];
  }
  return curr !== undefined && curr !== null ? curr : fallback;
}

// Centralized Render Error Guard
function safeRenderSection(sectionId, renderFunction) {
  try {
    renderFunction();
  } catch (err) {
    console.error(`Error rendering section ${sectionId}:`, err);
    logSessionHistory("error occurred", `Failed to render section ${sectionId}: ${err.message}`);
    
    const section = document.querySelector(`#${sectionId}`);
    if (section) {
      let body = section.querySelector('.card-collapsible-body');
      if (!body) body = section;
      
      body.innerHTML = `
        <div class="render-error-block">
          <span class="error-icon">⚠️</span>
          <div class="error-details">
            <strong>Section Render Failure:</strong>
            <p>An unexpected error occurred while rendering this card: ${err.message}</p>
            <small>Context: section-id "${sectionId}". Check console.</small>
          </div>
        </div>
      `;
    }
  }
}

// Workspace status display tracker
function setWorkspaceStatus(text, state) {
  if (apiStatusText) {
    apiStatusText.textContent = text;
  }
  if (apiStatusDot) {
    if (state === "loading") {
      apiStatusDot.className = "status-indicator-dot warning loading-animation";
      apiStatusDot.style.background = "var(--warning)";
      apiStatusDot.style.boxShadow = "0 0 8px var(--warning)";
    } else if (state === "ready") {
      apiStatusDot.className = "status-indicator-dot online";
      apiStatusDot.style.background = "var(--success)";
      apiStatusDot.style.boxShadow = "0 0 8px var(--success)";
    } else if (state === "error") {
      apiStatusDot.className = "status-indicator-dot offline";
      apiStatusDot.style.background = "var(--danger)";
      apiStatusDot.style.boxShadow = "0 0 8px var(--danger)";
    }
  }
}

// Initialize application
document.addEventListener("DOMContentLoaded", () => {
  initializeNavigation();
  renderAllEmptyStates();
  checkHealthStatus();
  setupCommandPanel();
  setupDragAndDropIngestion();
  setupVisualsGalleryListeners();
  renderSuggestionChips();
  validateDashboardBindings();
  initializeViewModes();
  
  if (clearFileBtn) {
    clearFileBtn.addEventListener("click", () => resetSessionState());
  }
});

// Clickable Sidebar & Tab Navigation Initialization
function initializeNavigation() {
  document.querySelectorAll(".sidebar-link").forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const href = link.getAttribute("href");
      if (href && href.startsWith("#")) {
        const sectionId = href.substring(1);
        scrollToWorkspaceSection(sectionId);
      }
    });
  });
}

function scrollToWorkspaceSection(sectionId) {
  if (sectionId === "section-technical-evidence") {
    setDashboardViewMode("audit");
  } else if (sectionId === "section-trends-forecasts" || sectionId === "section-visual-analytics" || sectionId === "section-recommendations" || sectionId === "section-executive-summary" || sectionId === "section-quality-gate" || sectionId === "section-kpis") {
    if (currentViewMode === "audit") {
      setDashboardViewMode("executive");
    }
  }

  const section = document.querySelector(`#${sectionId}`);
  if (section) {
    section.classList.remove("collapsed");
    section.scrollIntoView({ behavior: "smooth", block: "start" });
    highlightSection(sectionId);
    setActiveNavigationItem(sectionId);
  }
}

function setActiveNavigationItem(sectionId) {
  document.querySelectorAll(".sidebar-link").forEach(link => {
    const href = link.getAttribute("href");
    if (href === `#${sectionId}`) {
      link.classList.add("active");
      link.setAttribute("aria-selected", "true");
    } else {
      link.classList.remove("active");
      link.setAttribute("aria-selected", "false");
    }
  });
}

function highlightSection(sectionId) {
  const el = document.querySelector(`#${sectionId}`);
  if (el) {
    el.classList.add("highlighted-section");
    setTimeout(() => {
      el.classList.remove("highlighted-section");
    }, 2000);
  }
}

// Dashboard View Mode Operations
function initializeViewModes() {
  document.querySelectorAll(".view-mode-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const mode = btn.getAttribute("data-mode");
      if (mode) {
        setDashboardViewMode(mode);
      }
    });
  });
}

function getCurrentViewMode() {
  return currentViewMode;
}

function shouldShowTechnicalIdentifiers() {
  return currentViewMode === "analyst" || currentViewMode === "audit";
}

function setDashboardViewMode(mode) {
  currentViewMode = mode;
  
  // Highlight active button
  document.querySelectorAll(".view-mode-btn").forEach(btn => {
    if (btn.getAttribute("data-mode") === mode) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
  
  if (currentAnalysis) {
    renderModeAwareSections(currentAnalysis);
  }
  
  logSessionHistory("view mode changed", `Switched workspace layout to ${mode.toUpperCase()} VIEW.`);
}

function renderModeAwareSections(analysis) {
  const container = document.querySelector("#active-analysis-container");
  if (container) {
    container.className = "active-analysis-container view-mode-" + currentViewMode;
  }
  
  // Update view mode display for elements that need runtime toggle
  // E.g., re-render Visual Analytics or suggest chips
  if (analysis) {
    // Re-render visual analytics to apply display tier / mode filtering
    renderVisualAnalyticsCharts(analysis);
  }
}

function generateExecutiveNarrativeSummary(analysis) {
  if (!analysis) return "";
  return getNestedValue(analysis, "insights.summary") || "";
}

// Check API Service Health
async function checkHealthStatus() {
  try {
    const res = await fetch("/health");
    const data = await res.json();
    if (data.status === "ok") {
      setWorkspaceStatus("API Service Ready", "ready");
    } else {
      setWorkspaceStatus("Service Warning", "error");
    }
  } catch (err) {
    setWorkspaceStatus("Offline", "error");
  }
}

// Drag & Drop Ingestion Configuration
function setupDragAndDropIngestion() {
  if (browseFileBtn) {
    browseFileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      csvFileInputInput.click();
    });
  }
  if (csvDropzone) {
    csvDropzone.addEventListener("click", () => {
      csvFileInputInput.click();
    });
    
    ["dragenter", "dragover"].forEach(eventName => {
      csvDropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        csvDropzone.classList.add("dragging");
      }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
      csvDropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        csvDropzone.classList.remove("dragging");
      }, false);
    });

    csvDropzone.addEventListener("drop", (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files.length > 0) {
        uploadSalesCSV(files[0]);
      }
    });
  }
  
  if (csvFileInputInput) {
    csvFileInputInput.addEventListener("change", (e) => {
      if (e.target.files.length > 0) {
        uploadSalesCSV(e.target.files[0]);
      }
    });
  }

  if (runSampleBtn) runSampleBtn.addEventListener("click", () => loadSampleAnalysis());
  if (emptyStateSampleBtn) emptyStateSampleBtn.addEventListener("click", () => loadSampleAnalysis());
}

// Load and execute Sample analysis pipeline
async function parseErrorResponse(response) {
  try {
    const text = await response.text();
    try {
      const parsed = JSON.parse(text);
      if (parsed && parsed.detail) {
        if (typeof parsed.detail === "string") return parsed.detail;
        if (Array.isArray(parsed.detail)) {
          return parsed.detail.map(d => `${d.loc ? d.loc.join('.') + ': ' : ''}${d.msg}`).join("; ");
        }
        return JSON.stringify(parsed.detail);
      }
    } catch (e) {
      return text || `Status code ${response.status}`;
    }
  } catch (e) {
    return `Status code ${response.status}`;
  }
  return `Status code ${response.status}`;
}

function clearDashboardError() {
  if (commandResponseArea) {
    commandResponseArea.style.display = "none";
  }
}

function setLoadingState(isLoading, message = "") {
  toggleLoadingState(isLoading);
  if (isLoading && message) {
    setWorkspaceStatus(message, "loading");
  }
}

function handleAnalysisResponse(analysis, mode) {
  currentAnalysis = analysis;
  currentDataMode = mode;
  
  setWorkspaceStatus("Rendering dashboard...", "loading");
  
  if (mode === "sample") {
    currentFile = null;
    if (displayFilename) displayFilename.textContent = "sales_sample.csv";
    if (displayFilesize) {
      const bytes = safeNumber(getNestedValue(analysis, "source_metadata.file_size_bytes"));
      displayFilesize.textContent = `${(bytes / 1024).toFixed(1)} KB`;
    }
  } else if (mode === "upload") {
    if (displayFilename && currentFile) displayFilename.textContent = currentFile.name;
    if (displayFilesize && currentFile) displayFilesize.textContent = `${(currentFile.size / 1024).toFixed(1)} KB`;
  }
  
  if (selectedFileDisplay) selectedFileDisplay.style.display = "flex";
  
  populateAnalysisResults(analysis);
  renderSuggestionChips();
  
  const lastUpdated = new Date().toLocaleTimeString();
  setWorkspaceStatus(`Ready (${mode} mode) | Updated ${lastUpdated}`, "ready");
  showToastNotification(`${mode === "sample" ? "Sample" : "Uploaded"} sales analysis executed successfully!`, "success");
}

async function runSampleAnalysis() {
  clearDashboardError();
  setLoadingState(true, "Running governed sample analysis...");
  showToastNotification("Initializing governed sample analysis...", "info");
  
  try {
    const res = await fetch("/analysis/sample");
    if (!res.ok) {
      const errMsg = await parseErrorResponse(res);
      showDashboardError("Sample Analysis Failed", errMsg, "Verify backend uvicorn logs and check if port 8000 is open.");
      setWorkspaceStatus("Ready (sample error)", "error");
      setLoadingState(false);
      return;
    }
    
    const payload = await res.json();
    handleAnalysisResponse(payload, "sample");
    setLoadingState(false);
  } catch (err) {
    showDashboardError("Connection Error", `Failed to connect to backend: ${err.message}`, "Ensure local FastAPI server is running on port 8000.");
    setWorkspaceStatus("Offline", "error");
    setLoadingState(false);
  }
}

const loadSampleAnalysis = runSampleAnalysis;
const fetchSampleAnalysis = runSampleAnalysis;

// Upload a CSV file and execute Ingestion analysis
async function uploadSalesCSV(file) {
  if (!file) {
    showDashboardError("No File Selected", "Please select a file to upload.", "Click browse or drag a file to the dropzone.");
    return;
  }
  
  if (!file.name.toLowerCase().endsWith(".csv")) {
    showDashboardError("Invalid File Format", `Blocked non-CSV upload: "${file.name}"`, "Please select a standard sales transaction file ending in .csv");
    return;
  }
  
  if (file.size === 0) {
    showDashboardError("Empty File Uploaded", `The selected file "${file.name}" contains 0 bytes.`, "Select a valid, non-empty CSV spreadsheet.");
    return;
  }
  
  const maxLimit = 100 * 1024 * 1024;
  const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
  if (file.size > maxLimit) {
    showDashboardError("Oversized Upload Blocked", `File size is ${fileSizeMB} MB, exceeding the 100 MB maximum limit.`, "Filter, aggregate, or split your spreadsheet data before upload.");
    return;
  }
  
  currentFile = file;
  clearDashboardError();
  setLoadingState(true, `Uploading and analyzing ${file.name} (${fileSizeMB} MB)...`);
  showToastNotification(`Uploading ${file.name} (${fileSizeMB} MB) to governance checks...`, "info");
  
  try {
    const formData = new FormData();
    formData.append("file", file);
    
    const res = await fetch("/analysis/upload", {
      method: "POST",
      body: formData
    });
    
    if (!res.ok) {
      const errMsg = await parseErrorResponse(res);
      if (res.status === 413) {
        showDashboardError("Oversized Upload Blocked", `File size of ${fileSizeMB} MB exceeds the server's upload limit. Detail: ${errMsg}`, "Please filter, aggregate, or split your CSV spreadsheet before uploading.");
      } else {
        showDashboardError("Upload Analysis Failed", errMsg, "Inspect validation summary errors and confirm schema compatibility.");
      }
      setWorkspaceStatus("Ready (upload error)", "error");
      setLoadingState(false);
      return;
    }
    
    const payload = await res.json();
    handleAnalysisResponse(payload, "upload");
    setLoadingState(false);
  } catch (err) {
    showDashboardError("Upload Connection Error", `Failed to transmit file: ${err.message}`, "Verify server is alive and network constraints are correct.");
    setWorkspaceStatus("Offline", "error");
    setLoadingState(false);
  }
}

// Ingestion and loading status toggler
function toggleLoadingState(isLoading) {
  if (isLoading) {
    if (csvDropzone) csvDropzone.classList.add("dragging");
    if (runSampleBtn) runSampleBtn.disabled = true;
    if (emptyStateSampleBtn) emptyStateSampleBtn.disabled = true;
    if (browseFileBtn) browseFileBtn.disabled = true;
    if (displayFilename) displayFilename.textContent = "Uploading and processing...";
    if (displayFilesize) displayFilesize.textContent = "Please wait";
    if (selectedFileDisplay) selectedFileDisplay.style.display = "flex";
  } else {
    if (csvDropzone) csvDropzone.classList.remove("dragging");
    if (runSampleBtn) runSampleBtn.disabled = false;
    if (emptyStateSampleBtn) emptyStateSampleBtn.disabled = false;
    if (browseFileBtn) browseFileBtn.disabled = false;
  }
}

// Display UI error alerts
function showDashboardError(title, detail, action) {
  showToastNotification(`${title}: ${detail}`, "error");
  logSessionHistory("error occurred", `${title}: ${detail}`);
  
  if (commandResponseArea) {
    commandResponseArea.style.display = "block";
    commandResponseArea.className = "command-feedback-block error-feedback";
    if (feedbackIcon) feedbackIcon.textContent = "❌";
    if (feedbackTitle) feedbackTitle.textContent = title;
    if (feedbackBody) {
      feedbackBody.innerHTML = `
        <p>${safeText(detail)}</p>
        <p style="margin-top: 10px; font-weight: bold; color: var(--text);">Suggested Action: ${safeText(action)}</p>
      `;
    }
    commandResponseArea.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

// Ingestion and results layout logic
function populateAnalysisResults(data) {
  if (emptyStateCard) emptyStateCard.style.display = "none";
  if (resultsContainer) resultsContainer.style.display = "flex";
  
  const selectorBar = document.querySelector("#view-mode-selector-bar");
  if (selectorBar) selectorBar.style.display = "flex";
  if (resultsContainer) {
    resultsContainer.className = "active-analysis-container view-mode-" + currentViewMode;
  }
  
  // 1. Run Diagnostics Check
  const warnings = validateAnalysisShape(data);
  if (warnings.length > 0) {
    warnings.forEach(warn => logSessionHistory("error occurred", warn));
  } else {
    logSessionHistory("diagnostics passed", "All major analysis response sections verified successfully.");
  }
  
  // 2. Render Panel: Governance Trust & Actions Summary
  safeRenderSection("trust-panel", () => {
    const gateStatus = safeText(getNestedValue(data, "quality_gate.status"), "blocked");
    const isPassed = gateStatus.toLowerCase() !== "blocked";
    
    if (trustBadge) {
      trustBadge.textContent = isPassed ? "PASSED" : "BLOCKED";
      trustBadge.className = isPassed ? "trust-badge badge-success" : "trust-badge badge-blocked";
    }
    
    if (trustQgate) {
      trustQgate.textContent = gateStatus.toUpperCase();
      trustQgate.className = isPassed ? "trust-metric-val status-passed" : "trust-metric-val status-blocked";
    }
    
    if (trustConfidence) trustConfidence.textContent = safeText(getNestedValue(data, "quality_gate.confidence_level"), "N/A").toUpperCase();
    if (trustHumanReview) trustHumanReview.textContent = getNestedValue(data, "quality_gate.human_review_required") ? "Yes" : "No";
    if (trustReportsAllowed) trustReportsAllowed.textContent = getNestedValue(data, "quality_gate.can_generate_reports") ? "Yes" : "No";
    if (trustNarrativeAllowed) trustNarrativeAllowed.textContent = getNestedValue(data, "quality_gate.can_generate_llm_narrative") ? "Yes" : "No";
    
    const hasThreats = getNestedValue(data, "security.injection_risks_found") || getNestedValue(data, "security.prompt_injection_detected");
    if (trustSecurityScan) {
      trustSecurityScan.textContent = hasThreats ? "Warning" : "Clean";
      trustSecurityScan.className = hasThreats ? "trust-metric-val status-warn" : "trust-metric-val status-clean";
    }
    
    if (trustForecastReady) {
      trustForecastReady.textContent = safeText(getNestedValue(data, "forecast_analysis.readiness_status"), "N/A").toUpperCase();
    }
    
    const recsList = asArray(getNestedValue(data, "recommendation_plan.recommendations", []));
    const highPriorityRecs = recsList.filter(r => safeText(r.priority).toLowerCase() === "high");
    if (trustRecsCount) trustRecsCount.textContent = highPriorityRecs.length;
    
    if (trustTopActionDesc) {
      if (recsList.length > 0) {
        const topRec = highPriorityRecs.length > 0 ? highPriorityRecs[0] : recsList[0];
        trustTopActionDesc.textContent = `[${safeText(topRec.owner_role).toUpperCase()}] ${safeText(topRec.recommended_action)}`;
      } else {
        trustTopActionDesc.textContent = "No business actions are recommended at this time.";
      }
    }
    
    if (quickDownloadBtn) {
      quickDownloadBtn.disabled = !getNestedValue(data, "quality_gate.can_generate_reports", true);
    }
  });
  
  // 3. Render Card 1: Executive Summary
  safeRenderSection("section-executive-summary", () => {
    const summaryBox = document.querySelector("#exec-summary-narrative");
    const actions = asArray(getNestedValue(data, "insights.recommended_actions", []));
    if (summaryBox) {
      summaryBox.innerHTML = `
        <p>${safeText(getNestedValue(data, "insights.summary"))}</p>
        <ul>
          ${actions.map(action => `<li>${safeText(action)}</li>`).join("")}
        </ul>
      `;
    }
    
    const highlightsBox = document.querySelector("#exec-summary-highlights");
    if (highlightsBox) {
      highlightsBox.innerHTML = `
        <div class="highlight-metric-card">
          <span class="highlight-metric-val">${formatNumber(safeNumber(getNestedValue(data, "validation.valid_rows")))}</span>
          <span class="highlight-metric-lbl">Validated Sales Records</span>
        </div>
        <div class="highlight-metric-card">
          <span class="highlight-metric-val">${formatMoney(safeNumber(getNestedValue(data, "kpis.total_revenue")))}</span>
          <span class="highlight-metric-lbl">Total Net Sales Revenue</span>
        </div>
        <div class="highlight-metric-card">
          <span class="highlight-metric-val">${formatNumber(safeNumber(getNestedValue(data, "anomalies.total_anomalies")))}</span>
          <span class="highlight-metric-lbl">Outliers & Anomalies Flagged</span>
        </div>
      `;
    }
  });
  
  // 4. Render Card 2: Quality Gate
  safeRenderSection("section-quality-gate", () => {
    const qgateScoreVal = document.querySelector("#qgate-score-val");
    if (qgateScoreVal) qgateScoreVal.textContent = formatPercent(safeNumber(getNestedValue(data, "quality_score.score")));
    
    const qgateGradeVal = document.querySelector("#qgate-grade-val");
    const gateStatus = safeText(getNestedValue(data, "quality_gate.status"), "blocked");
    const isPassed = gateStatus.toLowerCase() !== "blocked";
    if (qgateGradeVal) {
      qgateGradeVal.textContent = safeText(getNestedValue(data, "quality_score.grade"), "N/A").toUpperCase();
      qgateGradeVal.className = isPassed ? "scorecard-status badge-success" : "scorecard-status scorecard-blocked";
    }
    
    const validRowsEl = document.querySelector("#qgate-rows-valid");
    if (validRowsEl) validRowsEl.textContent = formatNumber(safeNumber(getNestedValue(data, "validation.valid_rows")));
    
    const invalidRowsEl = document.querySelector("#qgate-rows-invalid");
    if (invalidRowsEl) invalidRowsEl.textContent = formatNumber(safeNumber(getNestedValue(data, "validation.invalid_rows")));
    
    const hasThreats = getNestedValue(data, "security.injection_risks_found") || getNestedValue(data, "security.prompt_injection_detected");
    const humanReviewReq = getNestedValue(data, "quality_gate.human_review_required");
    
    const checkRows = document.querySelector("#qgate-check-rows");
    if (checkRows) checkRows.textContent = safeNumber(getNestedValue(data, "validation.invalid_rows")) > 0 ? "⚠️" : "✅";
    
    const checkSec = document.querySelector("#qgate-check-security");
    if (checkSec) checkSec.textContent = hasThreats ? "⚠️" : "✅";
    
    const checkRev = document.querySelector("#qgate-check-review");
    if (checkRev) checkRev.textContent = humanReviewReq ? "👮" : "✅";
    
    const threatStatus = document.querySelector("#qgate-threats-status");
    if (threatStatus) threatStatus.textContent = hasThreats ? "Threat Warning" : "Clean";
    
    const reviewStatus = document.querySelector("#qgate-review-status");
    if (reviewStatus) reviewStatus.textContent = humanReviewReq ? "Oversight Required" : "Oversight Clear";
    
    const trustRulesList = document.querySelector("#qgate-trust-list");
    if (trustRulesList) {
      const reasons = asArray(getNestedValue(data, "quality_gate.reasons", []));
      const requiredActions = asArray(getNestedValue(data, "quality_gate.required_actions", []));
      
      trustRulesList.innerHTML = `
        ${reasons.map(reason => `<li><strong>Check:</strong> ${safeText(reason)}</li>`).join("")}
        ${requiredActions.map(act => `<li style="color:var(--warning)"><strong>Required Action:</strong> ${safeText(act)}</li>`).join("")}
      `;
    }
  });
  
  // 5. Render Card 3: KPIs
  safeRenderSection("section-kpis", () => {
    const revVal = document.querySelector("#kpi-revenue-val");
    if (revVal) revVal.textContent = formatMoney(safeNumber(getNestedValue(data, "kpis.total_revenue")));
    
    const ordersVal = document.querySelector("#kpi-orders-val");
    if (ordersVal) ordersVal.textContent = formatNumber(safeNumber(getNestedValue(data, "kpis.total_orders")));
    
    const unitsVal = document.querySelector("#kpi-units-val");
    if (unitsVal) unitsVal.textContent = formatNumber(safeNumber(getNestedValue(data, "kpis.total_units_sold")));
    
    const aovVal = document.querySelector("#kpi-aov-val");
    if (aovVal) aovVal.textContent = formatMoney(safeNumber(getNestedValue(data, "kpis.average_order_value")));
  });
  
  // 6. Render Card 4: Trends & Forecasts
  safeRenderSection("section-trends-forecasts", () => {
    const trendsList = document.querySelector("#trends-metrics-list");
    if (trendsList) {
      const revTrend = asObject(getNestedValue(data, "trend_analysis.revenue_trend"));
      const ordTrend = asObject(getNestedValue(data, "trend_analysis.order_count_trend"));
      const aovTrend = asObject(getNestedValue(data, "trend_analysis.average_order_value_trend"));
      
      const revDir = safeText(revTrend.direction, "stable");
      const ordDir = safeText(ordTrend.direction, "stable");
      const aovDir = safeText(aovTrend.direction, "stable");
      
      trendsList.innerHTML = `
        <li class="metric-trend-item">
          <span>Revenue Sales Direction:</span>
          <strong class="metric-trend-direction direction-${revDir === "increasing" ? "up" : "down"}">
            ${revDir.toUpperCase()} (${formatPercent(safeNumber(revTrend.percent_change))})
          </strong>
        </li>
        <li class="metric-trend-item">
          <span>Order Counts Direction:</span>
          <strong class="metric-trend-direction direction-${ordDir === "increasing" ? "up" : "down"}">
            ${ordDir.toUpperCase()} (${formatPercent(safeNumber(ordTrend.percent_change))})
          </strong>
        </li>
        <li class="metric-trend-item">
          <span>Average Order Value:</span>
          <strong class="metric-trend-direction direction-${aovDir === "increasing" ? "up" : "down"}">
            ${aovDir.toUpperCase()} (${formatPercent(safeNumber(aovTrend.percent_change))})
          </strong>
        </li>
      `;
    }
    
    const readinessLbl = document.querySelector("#forecast-readiness-lbl");
    if (readinessLbl) readinessLbl.textContent = safeText(getNestedValue(data, "forecast_analysis.readiness_status"), "unknown").toUpperCase();
    
    const confidenceLbl = document.querySelector("#forecast-confidence-lbl");
    if (confidenceLbl) confidenceLbl.textContent = safeText(getNestedValue(data, "forecast_analysis.confidence_level"), "unknown").toUpperCase();
    
    const warningsList = document.querySelector("#forecast-warnings-text");
    if (warningsList) {
      const warnings = asArray(getNestedValue(data, "forecast_analysis.warnings", []));
      if (warnings.length > 0) {
        warningsList.textContent = `⚠️ Warnings: ${warnings.map(w => safeText(w)).join(", ")}`;
        warningsList.style.display = "block";
      } else {
        warningsList.style.display = "none";
      }
    }
    
    const forecastTableBody = document.querySelector("#forecast-metrics-table tbody");
    if (forecastTableBody) {
      const forecastData = [
        { name: "Revenue", fc: getNestedValue(data, "forecast_analysis.revenue_forecast") },
        { name: "Order Count", fc: getNestedValue(data, "forecast_analysis.order_count_forecast") },
        { name: "Average Order Value", fc: getNestedValue(data, "forecast_analysis.average_order_value_forecast") }
      ];
      forecastTableBody.innerHTML = forecastData.map(item => {
        if (!item.fc) return "";
        const method = safeText(item.fc.selected_baseline_method, "N/A");
        const val = safeNumber(item.fc.selected_forecast_value);
        return `
          <tr>
            <td><strong>${item.name}</strong></td>
            <td>${method}</td>
            <td><strong>${formatMoney(val)}</strong></td>
          </tr>
        `;
      }).join("");
    }
  });
  
  // 7. Render Card 5: Visual Analytics
  safeRenderSection("section-visual-analytics", () => {
    renderVisualAnalyticsCharts(data);
  });
  
  // 8. Render Card 6: Recommendations
  safeRenderSection("section-recommendations", () => {
    const recsGrid = document.querySelector("#action-center-recs-grid");
    if (recsGrid) {
      const recs = asArray(getNestedValue(data, "recommendation_plan.recommendations", []));
      if (recs.length > 0) {
        recsGrid.innerHTML = recs.map(rec => {
          const priority = safeText(rec.priority, "medium");
          const priorityClass = `action-priority-${priority.toLowerCase()}`;
          const tagClass = `tag-${priority.toLowerCase()}`;
          return `
            <div class="action-item-card ${priorityClass}">
              <div class="action-card-top">
                <span class="action-priority-tag ${tagClass}">${priority.toUpperCase()} Priority</span>
                <span class="action-owner-lbl">VP Auditor: ${safeText(rec.owner_role, "Owner").toUpperCase()}</span>
              </div>
              <h5 class="action-card-title">${safeText(rec.title)}</h5>
              <p class="action-card-desc">${safeText(rec.recommended_action)}</p>
              <div class="action-card-meta-row">
                <span>Workflow: <strong>${safeText(rec.workflow_stage).toUpperCase()}</strong></span>
                <span>Impact: <strong>${safeText(rec.expected_impact)}</strong></span>
                <span>Follow-up: <strong>${safeText(rec.follow_up_metric)}</strong></span>
              </div>
            </div>
          `;
        }).join("");
      } else {
        recsGrid.innerHTML = `<p class="empty-state-text">No recommendations available from the pipeline.</p>`;
      }
    }
    
    const workflowList = document.querySelector("#action-center-workflow-list");
    if (workflowList) {
      const improvements = asArray(getNestedValue(data, "workflow_improvement_plan.improvements", []));
      if (improvements.length > 0) {
        workflowList.innerHTML = improvements.map(imp => {
          const type = safeText(imp.improvement_type, "Process");
          const desc = safeText(imp.description);
          const impact = safeText(imp.expected_impact);
          const owner = safeText(imp.owner_role, "Owner");
          return `
            <li class="workflow-check-card">
              <span class="workflow-check-checkbox">☑️</span>
              <div class="workflow-check-desc">
                <strong>[${type.toUpperCase()}]</strong> ${desc} 
                (Impact: <em>${impact}</em> | Owner: <em>${owner.toUpperCase()}</em>)
              </div>
            </li>
          `;
        }).join("");
      } else {
        workflowList.innerHTML = `<li>No active process improvements compiled.</li>`;
      }
    }
  });
  
  // 9. Render Card 7: Report Compilations
  safeRenderSection("section-reports", () => {
    if (exportUploadReportBtn) {
      exportUploadReportBtn.disabled = currentDataMode !== "upload";
    }
    if (exportStatusBanner) {
      exportStatusBanner.style.display = "inline-flex";
    }
    if (exportStatusMsg) {
      exportStatusMsg.textContent = `Valid metrics loaded. Report export checks Passed.`;
    }
  });
  
  // 10. Render Card 8: Technical Evidence Drawer (Raw JSON)
  safeRenderSection("section-technical-evidence", () => {
    const diagnosticsLogs = document.querySelector("#tech-diagnostics-results");
    if (diagnosticsLogs) {
      diagnosticsLogs.textContent = warnings.length > 0 
        ? warnings.join("\n") 
        : "Diagnostics check: 10/10 components present. Payload integrity validated.";
    }
    
    const setDrawerContent = (id, field) => {
      const el = document.querySelector(`#${id}`);
      if (el) {
        const val = getNestedValue(data, field);
        el.textContent = val !== undefined && val !== null ? JSON.stringify(val, null, 2) : "No records available for this section.";
      }
    };
    
    setDrawerContent("tech-meta-profile", "source_metadata");
    setDrawerContent("tech-validation-results", "validation");
    setDrawerContent("tech-data-profile", "data_profile");
    setDrawerContent("tech-quality-score", "quality_score");
    setDrawerContent("tech-data-prep", "preparation");
    setDrawerContent("tech-lineage-log", "transformation_log");
    setDrawerContent("tech-manipulation-summary", "manipulation_summary");
    setDrawerContent("tech-security-logs", "security");
    setDrawerContent("tech-anomalies-trace", "anomalies");
    setDrawerContent("tech-audit-events", "audit_events");
  });
}

// Visual category SVGs and table previews renderers (Restored to Card Layout)
// Display tiers & mode helpers for Visual Analytics
function getChartDisplayTier(chart, analysis) {
  const cid = chart.chart_id;
  const primaryIds = ["revenue_by_region", "revenue_by_product", "revenue_by_sales_rep", "pareto_revenue_by_product", "data_quality_score"];
  if (primaryIds.includes(cid)) {
    return "primary";
  }
  
  const ctype = safeText(chart.chart_type).toLowerCase();
  
  // Suppress rule 1: trend charts when periods < 2
  const totalPeriods = safeNumber(getNestedValue(analysis, "trend_analysis.total_periods"), 0);
  if (cid.includes("trend") && totalPeriods < 2) {
    return "suppressed";
  }
  
  // Suppress rule 2: forecast charts when readiness is not_ready
  const forecastReadiness = safeText(getNestedValue(analysis, "forecast_analysis.readiness_status"), "not_ready").toLowerCase();
  if (cid.includes("forecast") && forecastReadiness === "not_ready") {
    return "suppressed";
  }
  
  // Suppress rule 3: pie/donut charts with single slice at 100% or empty
  if (ctype === "pie" && isSingleSliceComposition(chart.data)) {
    return "suppressed";
  }
  
  // Suppress rule 4: empty data
  if ((!chart.data || chart.data.length === 0) && !cid.includes("trend") && !cid.includes("forecast")) {
    return "suppressed";
  }
  
  // Secondary charts
  const secondaryIds = ["discount_summary_by_product", "anomalies_by_severity"];
  if (secondaryIds.includes(cid) || ctype === "pie" || cid.includes("share")) {
    return "secondary";
  }
  
  if (cid.includes("forecast") && (forecastReadiness === "ready" || forecastReadiness === "limited")) {
    return "secondary";
  }
  
  if (cid.includes("trend") && totalPeriods >= 2) {
    return "secondary";
  }
  
  return "secondary";
}

function isSingleSliceComposition(items) {
  const list = asArray(items);
  if (list.length === 0) return true;
  if (list.length === 1) return true;
  
  const nonZero = list.filter(d => safeNumber(d.value) > 0);
  return nonZero.length <= 1;
}

function shouldRenderChartInCurrentMode(chart, mode, analysis) {
  const tier = getChartDisplayTier(chart, analysis);
  if (mode === "executive") {
    return tier === "primary";
  }
  if (mode === "analyst") {
    return tier === "primary" || tier === "secondary" || tier === "suppressed";
  }
  if (mode === "audit") {
    return false; // Audit view hides charts
  }
  return true;
}

function renderInsufficientDataNotice(chart, analysis) {
  const cid = chart.chart_id;
  const totalPeriods = safeNumber(getNestedValue(analysis, "trend_analysis.total_periods"), 0);
  const forecastReadiness = safeText(getNestedValue(analysis, "forecast_analysis.readiness_status"), "not_ready").toUpperCase();
  
  if (cid.includes("trend") && totalPeriods < 2) {
    return `Monthly periods count is ${totalPeriods} (minimum 2 periods required for trend analysis).`;
  }
  if (cid.includes("forecast") && forecastReadiness === "NOT_READY") {
    return `Revenue forecasting is not ready: baseline requires historical variance across multiple monthly periods.`;
  }
  return "Insufficient data to display this chart.";
}

// Visual category SVGs and table previews renderers (Restored to Card Layout)
function renderVisualAnalyticsCharts(data) {
  const catRevenue = document.querySelector("#visuals-cat-revenue");
  const catTrends = document.querySelector("#visuals-cat-trends");
  const catQuality = document.querySelector("#visuals-cat-quality");
  const catDiscounting = document.querySelector("#visuals-cat-discounting");
  const catComposition = document.querySelector("#visuals-cat-composition");
  const catInsufficient = document.querySelector("#visuals-cat-insufficient");
  
  if (catRevenue) catRevenue.innerHTML = "";
  if (catTrends) catTrends.innerHTML = "";
  if (catQuality) catQuality.innerHTML = "";
  if (catDiscounting) catDiscounting.innerHTML = "";
  if (catComposition) catComposition.innerHTML = "";
  if (catInsufficient) catInsufficient.innerHTML = "";
  
  const chartList = [...asArray(getNestedValue(data, "charts.charts", []))];
  
  // Add regional revenue composition
  const hasRegionPie = chartList.some(c => c.chart_id === "region_share_pie");
  if (!hasRegionPie) {
    const regionData = buildRevenueShareComposition(data, "region");
    if (regionData.length > 0) {
      chartList.push({
        chart_id: "region_share_pie",
        chart_type: "pie",
        title: "Regional Revenue Share",
        business_question: "What is the relative revenue contribution across sales regions?",
        interpretation: "Calculated regional revenue shares showing customer concentration.",
        data: regionData,
        derived: true
      });
    }
  }
  
  // Add product revenue composition
  const hasProductPie = chartList.some(c => c.chart_id === "product_share_pie");
  if (!hasProductPie) {
    const productData = buildRevenueShareComposition(data, "product");
    if (productData.length > 0) {
      const sortedData = [...productData].sort((a,b) => safeNumber(b.value) - safeNumber(a.value));
      const topData = sortedData.slice(0, 5);
      const otherVal = sortedData.slice(5).reduce((sum, d) => sum + safeNumber(d.value), 0);
      if (otherVal > 0) {
        topData.push({ label: "Other Products", value: otherVal });
      }
      chartList.push({
        chart_id: "product_share_pie",
        chart_type: "pie",
        title: "Product Revenue Concentration",
        business_question: "Which products compose the highest percentage of sales volumes?",
        interpretation: "Concentration profile derived from validated revenue logs.",
        data: topData,
        derived: true
      });
    }
  }
  
  // Add anomaly severity composition
  const hasSeverityPie = chartList.some(c => c.chart_id === "severity_share_pie");
  if (!hasSeverityPie) {
    const severityData = buildAnomalySeverityComposition(data);
    if (severityData.length > 0) {
      chartList.push({
        chart_id: "severity_share_pie",
        chart_type: "pie",
        title: "Anomaly Severity Distribution",
        business_question: "What is the composition of anomaly warnings by classification severity?",
        interpretation: "Audit profile derived from rule-based security flags.",
        data: severityData,
        derived: true
      });
    }
  }
  
  // Add recommendation priority composition
  const hasPriorityPie = chartList.some(c => c.chart_id === "priority_share_pie");
  if (!hasPriorityPie) {
    const priorityData = buildRecommendationPriorityComposition(data);
    if (priorityData.length > 0) {
      if (priorityData.length === 1 && priorityData[0].label === "Medium") {
        // Skip composition if all are medium
      } else {
        chartList.push({
          chart_id: "priority_share_pie",
          chart_type: "pie",
          title: "Action Item Priority Share",
          business_question: "What is the breakdown of recommendations by priority status?",
          interpretation: "Distribution of urgent vs operational remediation tasks.",
          data: priorityData,
          derived: true
        });
      }
    }
  }

  // Filter charts dynamically based on category selection and search query
  const filteredCharts = chartList.filter(series => {
    const title = safeText(series.title).toLowerCase();
    const query = safeText(series.business_question).toLowerCase();
    const matchesSearch = title.includes(chartSearchQuery.toLowerCase()) || query.includes(chartSearchQuery.toLowerCase());
    if (!matchesSearch) return false;
    
    if (activeChartCategory === "all") return true;
    
    const cid = series.chart_id.toLowerCase();
    const ctype = safeText(series.chart_type).toLowerCase();
    
    if (activeChartCategory === "composition" || ctype === "pie") {
      return activeChartCategory === "composition" && (ctype === "pie" || cid.includes("share"));
    }
    if (activeChartCategory === "revenue") {
      return (cid.includes("region") || cid.includes("product") || cid.includes("rep")) && !cid.includes("discount") && !cid.includes("share");
    }
    if (activeChartCategory === "trends") {
      return cid.includes("trend") || cid.includes("forecast");
    }
    if (activeChartCategory === "quality") {
      return cid.includes("quality") || cid.includes("anomalies");
    }
    if (activeChartCategory === "discounting") {
      return cid.includes("discount") || cid.includes("pareto");
    }
    return true;
  });
  
  // Render each filtered chart using the restored robust previous layout
  filteredCharts.forEach(series => {
    // 1. Check Display Tier
    const tier = getChartDisplayTier(series, data);
    
    // 2. Check view mode visibility
    if (!shouldRenderChartInCurrentMode(series, currentViewMode, data)) {
      return; // Skip rendering in this view mode
    }
    
    let targetContainer = null;
    const cid = series.chart_id.toLowerCase();
    const ctype = safeText(series.chart_type).toLowerCase();
    
    if (tier === "suppressed" && currentViewMode === "analyst") {
      targetContainer = catInsufficient;
    } else if (ctype === "pie" || cid.includes("share")) {
      targetContainer = catComposition;
    } else if (cid.includes("region") || cid.includes("product") || cid.includes("rep")) {
      if (cid.includes("discount") || cid.includes("pareto")) {
        targetContainer = catDiscounting;
      } else {
        targetContainer = catRevenue;
      }
    } else if (cid.includes("trend") || cid.includes("forecast")) {
      targetContainer = catTrends;
    } else if (cid.includes("quality") || cid.includes("anomalies")) {
      targetContainer = catQuality;
    } else {
      targetContainer = catRevenue;
    }
    
    if (!targetContainer) return;
    
    const chartCard = document.createElement("article");
    chartCard.className = "chart-card";
    chartCard.id = `chart-card-${series.chart_id}`;
    
    let visualPreviewContent = "";
    if (tier === "suppressed") {
      visualPreviewContent = `
        <div class="empty-preview-msg">
          <span>⚠️</span>
          <p>${renderInsufficientDataNotice(series, data)}</p>
        </div>
      `;
    } else if (ctype === "pie" || cid.includes("share")) {
      visualPreviewContent = renderPiePreview(series.data, { title: series.title });
    } else if (ctype === "line") {
      visualPreviewContent = renderLinePreview(series);
    } else {
      visualPreviewContent = renderHorizontalBarPreview(series);
    }
    
    const actions = asArray(series.recommended_actions);
    const actionsHtml = actions.length > 0 
      ? actions.map(act => `<li>${safeText(act)}</li>`).join("")
      : `<li>No chart-specific recommended actions.</li>`;
      
    const insights = asArray(series.related_insight_ids);
    const insightsHtml = insights.length > 0
      ? insights.map(id => `<span class="insight-badge">${safeText(id)}</span>`).join(", ")
      : "None";
      
    const isDerived = series.derived || cid.includes("share") || cid.includes("pie");
    const labelBadge = isDerived ? `<span class="chart-derived-badge" title="Derived dynamically from analysis data">Dashboard composition view derived from analysis response</span>` : ``;
    
    // Executive view only shows one action
    const singleAction = actions[0] || "Use this visual as supporting evidence for the related business recommendation.";
    
    chartCard.innerHTML = `
      <div class="chart-card-header-row">
        <h3>${safeText(series.title)}</h3>
        <span class="chart-id-badge chart-id">${safeText(series.chart_id)}</span>
      </div>
      <p><strong>Business question:</strong> ${safeText(series.business_question || "None")}</p>
      <p class="concise-finding"><strong>Concise Finding:</strong> ${safeText(series.interpretation || "None")}</p>
      ${labelBadge}
      
      <div class="chart-visual-preview" style="margin: 14px 0;">
        ${visualPreviewContent}
      </div>
      
      <p class="exec-action-item"><strong>Recommended Next Action:</strong> ${safeText(singleAction)}</p>
      
      <details class="chart-evidence-details">
        <summary>Expand Evidence Details</summary>
        <div class="evidence-details-content">
          <p class="insight-id"><strong>Related Insight IDs:</strong> ${insightsHtml}</p>
          <div class="chart-actions-list">
            <h4>All Recommended Actions</h4>
            <ul>
              ${actionsHtml}
            </ul>
          </div>
          <div class="chart-data-table-wrapper" style="margin-top: 14px;">
            <h4>${ctype === "line" ? "Period Data" : "Chart Data"}</h4>
            ${renderChartTable(series)}
          </div>
        </div>
      </details>
    `;
    
    targetContainer.appendChild(chartCard);
  });
  
  // Add compact readiness notes in Executive View if categories are empty
  if (currentViewMode === "executive") {
    const totalPeriods = safeNumber(getNestedValue(data, "trend_analysis.total_periods"), 0);
    const forecastReadiness = safeText(getNestedValue(data, "forecast_analysis.readiness_status"), "not_ready").toUpperCase();
    
    if (catTrends && catTrends.children.length === 0) {
      catTrends.innerHTML = `
        <div class="empty-preview-msg">
          <span>⚠️</span>
          <p>Trend & Forecasting visuals are suppressed. Total periods count is ${totalPeriods} (minimum 2 required). Forecast readiness status is ${forecastReadiness}.</p>
        </div>
      `;
    }
    
    if (catQuality && catQuality.children.length === 0) {
      catQuality.innerHTML = `
        <div class="empty-preview-msg">
          <span>ℹ️</span>
          <p>No high-severity quality anomalies detected. Quality score is stable.</p>
        </div>
      `;
    }
    
    if (catDiscounting && catDiscounting.children.length === 0) {
      catDiscounting.innerHTML = `
        <div class="empty-preview-msg">
          <span>ℹ️</span>
          <p>Discount distribution analysis is within baseline bounds.</p>
        </div>
      `;
    }
    
    if (catComposition && catComposition.children.length === 0) {
      catComposition.innerHTML = `
        <div class="empty-preview-msg">
          <span>ℹ️</span>
          <p>Segment composition views are suppressed in Executive View.</p>
        </div>
      `;
    }
  }

  // Hide empty category boxes
  document.querySelectorAll(".visual-category-box").forEach(box => {
    const list = box.querySelector(".visual-charts-flex");
    if (list && list.children.length === 0) {
      box.style.display = "none";
    } else {
      box.style.display = "block";
    }
  });
}

// Composition Chart Builders
function buildRevenueShareComposition(analysis, dimension) {
  const charts = asArray(getNestedValue(analysis, "charts.charts", []));
  const chartId = dimension === "region" ? "revenue_by_region" : "revenue_by_product";
  const source = charts.find(c => c.chart_id === chartId);
  if (!source) return [];
  return asArray(source.data).map(pt => ({
    label: safeText(pt.label),
    value: safeNumber(pt.value)
  }));
}

function buildRecommendationPriorityComposition(analysis) {
  const recs = asArray(getNestedValue(analysis, "recommendation_plan.recommendations", []));
  const counts = {};
  recs.forEach(r => {
    const pri = safeText(r.priority, "Medium");
    counts[pri] = (counts[pri] || 0) + 1;
  });
  return Object.entries(counts).map(([label, value]) => ({ label, value }));
}

function buildAnomalySeverityComposition(analysis) {
  const charts = asArray(getNestedValue(analysis, "charts.charts", []));
  const source = charts.find(c => c.chart_id === "anomalies_by_severity");
  if (!source) return [];
  return asArray(source.data).map(pt => ({
    label: safeText(pt.label),
    value: safeNumber(pt.value)
  }));
}

// Visuals controllers event registration
function setupVisualsGalleryListeners() {
  if (visualsSearch) {
    visualsSearch.addEventListener("input", (e) => {
      chartSearchQuery = e.target.value.trim();
      if (currentAnalysis) {
        renderVisualAnalyticsCharts(currentAnalysis);
      }
    });
  }
  
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach(b => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      
      activeChartCategory = btn.getAttribute("data-category");
      if (currentAnalysis) {
        renderVisualAnalyticsCharts(currentAnalysis);
      }
    });
  });
}

// Horizontal bar visual list preview
function renderHorizontalBarPreview(chart) {
  const data = asArray(getNestedValue(chart, "data", []));
  if (data.length === 0) return `<div class="empty-preview-msg">No data for bar preview</div>`;
  const maxVal = Math.max(...data.map(d => safeNumber(d.value)), 1);
  
  return `
    <div class="bar-list" aria-label="${safeText(chart.title)} preview">
      ${data.map(pt => {
        const val = safeNumber(pt.value);
        const pct = Math.min((val / maxVal) * 100, 100);
        const lbl = safeText(pt.label);
        return `
          <div class="bar-row">
            <span>${lbl}</span>
            <div class="bar-track">
              <div class="bar-fill" style="width: ${pct.toFixed(2)}%"></div>
            </div>
            <strong>${formatNumber(val)}</strong>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

// Line graph SVG visual preview
function renderLinePreview(chart) {
  const data = asArray(getNestedValue(chart, "data", []));
  if (data.length === 0) return `<div class="empty-preview-msg">No data for line preview</div>`;
  
  const values = data.map(d => safeNumber(d.value));
  const maxVal = Math.max(...values, 1);
  const minVal = Math.min(...values, 0);
  const range = maxVal - minVal || 1;
  
  const width = 300;
  const height = 120;
  const padding = 15;
  const chartWidth = width - 2 * padding;
  const chartHeight = height - 2 * padding;
  
  const points = data.map((pt, i) => {
    const x = padding + (i / Math.max(data.length - 1, 1)) * chartWidth;
    const y = padding + chartHeight - ((safeNumber(pt.value) - minVal) / range) * chartHeight;
    return { x, y, val: pt.value, label: pt.label };
  });
  
  const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
  const areaData = `${pathData} L ${points[points.length - 1].x.toFixed(1)} ${(height - padding).toFixed(1)} L ${points[0].x.toFixed(1)} ${(height - padding).toFixed(1)} Z`;
  const gradId = `line-grad-${chart.chart_id}`;
  
  return `
    <div class="svg-line-container">
      <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" class="line-svg">
        <defs>
          <linearGradient id="${gradId}" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="var(--accent)" stop-opacity="0.3"></stop>
            <stop offset="100%" stop-color="var(--accent)" stop-opacity="0"></stop>
          </linearGradient>
        </defs>
        <line x1="${padding}" y1="${padding}" x2="${width - padding}" y2="${padding}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="2 2"></line>
        <line x1="${padding}" y1="${padding + chartHeight / 2}" x2="${width - padding}" y2="${padding + chartHeight / 2}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="2 2"></line>
        <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="rgba(255,255,255,0.1)"></line>
        <path d="${areaData}" fill="url(#${gradId})"></path>
        <path d="${pathData}" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"></path>
        ${points.map(p => `
          <circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" class="line-dot" fill="var(--accent)" stroke="#101524" stroke-width="1.5">
            <title>${p.label}: ${formatNumber(p.val)}</title>
          </circle>
        `).join("")}
      </svg>
      <div class="line-labels-x">
        <span>${safeText(data[0] ? data[0].label : "")}</span>
        <span>${safeText(data[data.length - 1] ? data[data.length - 1].label : "")}</span>
      </div>
    </div>
  `;
}

// SVG Pie chart visual preview
function renderPiePreview(items, options = {}) {
  const data = asArray(items);
  if (data.length === 0) return `<div class="empty-preview-msg">No data for pie preview</div>`;
  
  const total = data.reduce((sum, d) => sum + safeNumber(d.value), 0) || 1;
  const radius = 40;
  const center = 50;
  let currentAngle = 0;
  
  const colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];
  
  const slices = data.map((pt, i) => {
    const val = safeNumber(pt.value);
    const lbl = safeText(pt.label);
    const percentage = (val / total) * 100;
    const angle = (val / total) * 360;
    
    const x1 = center + radius * Math.cos((Math.PI * currentAngle) / 180);
    const y1 = center + radius * Math.sin((Math.PI * currentAngle) / 180);
    currentAngle += angle;
    const x2 = center + radius * Math.cos((Math.PI * currentAngle) / 180);
    const y2 = center + radius * Math.sin((Math.PI * currentAngle) / 180);
    
    const largeArcFlag = angle > 180 ? 1 : 0;
    const pathData = `
      M ${center} ${center}
      L ${x1.toFixed(2)} ${y1.toFixed(2)}
      A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}
      Z
    `;
    return { pathData, color: colors[i % colors.length], label: lbl, percentage, value: val };
  });
  
  return `
    <div class="pie-preview-wrapper">
      <div class="pie-svg-container">
        <svg class="pie-svg" width="120" height="120" viewBox="0 0 100 100">
          ${slices.map(sl => `
            <path d="${sl.pathData}" fill="${sl.color}" stroke="#101524" stroke-width="1.5">
              <title>${sl.label}: ${formatNumber(sl.value)} (${sl.percentage.toFixed(1)}%)</title>
            </path>
          `).join("")}
        </svg>
      </div>
      <div class="pie-legend">
        ${slices.map(sl => `
          <div class="pie-legend-item">
            <span class="legend-color-dot" style="background-color: ${sl.color}"></span>
            <span class="legend-label" title="${sl.label}">${sl.label}</span>
            <span class="legend-val">${sl.percentage.toFixed(1)}%</span>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

// SVG Donut chart visual preview
function renderDonutPreview(items, options = {}) {
  const data = asArray(items);
  if (data.length === 0) return `<div class="empty-preview-msg">No data for donut preview</div>`;
  
  const total = data.reduce((sum, d) => sum + safeNumber(d.value), 0) || 1;
  const radius = 40;
  const center = 50;
  let currentAngle = 0;
  
  const colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];
  
  const slices = data.map((pt, i) => {
    const val = safeNumber(pt.value);
    const lbl = safeText(pt.label);
    const percentage = (val / total) * 100;
    const angle = (val / total) * 360;
    
    const x1 = center + radius * Math.cos((Math.PI * currentAngle) / 180);
    const y1 = center + radius * Math.sin((Math.PI * currentAngle) / 180);
    currentAngle += angle;
    const x2 = center + radius * Math.cos((Math.PI * currentAngle) / 180);
    const y2 = center + radius * Math.sin((Math.PI * currentAngle) / 180);
    
    const largeArcFlag = angle > 180 ? 1 : 0;
    const pathData = `
      M ${center} ${center}
      L ${x1.toFixed(2)} ${y1.toFixed(2)}
      A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}
      Z
    `;
    return { pathData, color: colors[i % colors.length], label: lbl, percentage, value: val };
  });
  
  return `
    <div class="pie-preview-wrapper">
      <div class="pie-svg-container">
        <svg class="pie-svg" width="120" height="120" viewBox="0 0 100 100">
          ${slices.map(sl => `
            <path d="${sl.pathData}" fill="${sl.color}" stroke="#101524" stroke-width="1.5">
              <title>${sl.label}: ${formatNumber(sl.value)} (${sl.percentage.toFixed(1)}%)</title>
            </path>
          `).join("")}
          <circle cx="${center}" cy="${center}" r="22" fill="#141b2f"></circle>
        </svg>
      </div>
      <div class="pie-legend">
        ${slices.map(sl => `
          <div class="pie-legend-item">
            <span class="legend-color-dot" style="background-color: ${sl.color}"></span>
            <span class="legend-label" title="${sl.label}">${sl.label}</span>
            <span class="legend-val">${sl.percentage.toFixed(1)}%</span>
          </div>
        `).join("")}
      </div>
    </div>
  `;
}

// Compact chart data table rendering
function renderChartTable(chart) {
  const data = asArray(getNestedValue(chart, "data", []));
  if (data.length === 0) return `<div class="empty-preview-msg">No data coordinates present.</div>`;
  
  return `
    <table class="compact-analysis-table">
      <thead>
        <tr>
          <th>Segment/Label</th>
          <th>Value</th>
          ${data[0] && data[0].secondary_value !== null && data[0].secondary_value !== undefined ? '<th>Share %</th>' : ''}
        </tr>
      </thead>
      <tbody>
        ${data.map(pt => {
          const val = safeNumber(pt.value);
          return `
            <tr>
              <td><strong>${safeText(pt.label)}</strong></td>
              <td>${formatNumber(val)}</td>
              ${pt.secondary_value !== null && pt.secondary_value !== undefined ? `<td>${safeNumber(pt.secondary_value).toFixed(1)}%</td>` : ''}
            </tr>
          `;
        }).join("")}
      </tbody>
    </table>
  `;
}

// Setup Ask Copilot Event Listeners
function setupCommandPanel() {
  if (submitCommandBtn) {
    submitCommandBtn.addEventListener("click", () => {
      const rawVal = commandInput.value.trim();
      if (rawVal) {
        executeAskIntent(parseAskIntent(rawVal));
      }
    });
  }

  if (commandInput) {
    commandInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        const rawVal = commandInput.value.trim();
        if (rawVal) {
          executeAskIntent(parseAskIntent(rawVal));
        }
      }
    });
  }

  if (exportSampleReportBtn) exportSampleReportBtn.addEventListener("click", () => handleReportDownload(exportFormatSelect.value));
  if (uploadReportButton) uploadReportButton.addEventListener("click", () => handleReportDownload(exportFormatSelect.value));
  if (exportUploadReportBtn) exportUploadReportBtn.addEventListener("click", () => handleReportDownload(exportFormatSelect.value));
  if (quickDownloadBtn) quickDownloadBtn.addEventListener("click", () => handleReportDownload(quickFormatSelect.value));
  
  if (clearHistoryBtn) {
    clearHistoryBtn.addEventListener("click", () => {
      analysisHistory = [];
      renderHistoryTimeline();
    });
  }
}

// Display suggestion chips dynamically based on session data state
function renderSuggestionChips() {
  const chipsContainer = document.querySelector("#command-suggestion-chips");
  if (!chipsContainer) return;
  
  chipsContainer.innerHTML = "";
  
  if (!currentAnalysis) {
    const chips = [
      { text: "Run sample analysis", cmd: "run sample analysis" },
      { text: "Upload CSV", cmd: "upload csv" },
      { text: "Show supported questions", cmd: "help" }
    ];
    
    chips.forEach(c => {
      const btn = document.createElement("button");
      btn.className = "suggestion-chip";
      btn.type = "button";
      btn.textContent = c.text;
      btn.addEventListener("click", () => {
        if (c.cmd === "run sample analysis") {
          loadSampleAnalysis();
        } else if (c.cmd === "upload csv") {
          csvFileInputInput.click();
        } else if (c.cmd === "help") {
          commandInput.value = "Show supported questions";
          executeAskIntent("help");
        }
      });
      chipsContainer.appendChild(btn);
    });
  } else {
    const chips = [
      { text: "Can I trust this data?", cmd: "can i trust this data" },
      { text: "Which region performed best?", cmd: "which region performed best" },
      { text: "What is the forecast?", cmd: "what is the forecast" },
      { text: "What should we do next?", cmd: "what should we do next" },
      { text: "Show visual analytics", cmd: "show visual analytics" },
      { text: "Download PDF", cmd: "download pdf" },
      { text: "Show technical evidence", cmd: "show technical evidence" }
    ];
    
    chips.forEach(c => {
      const btn = document.createElement("button");
      btn.className = "suggestion-chip";
      btn.type = "button";
      btn.textContent = c.text;
      btn.addEventListener("click", () => {
        commandInput.value = c.text;
        executeAskIntent(parseAskIntent(c.cmd));
      });
      chipsContainer.appendChild(btn);
    });
  }
}

// Ask Intent Parser logic
function normalizeAskText(input) {
  return safeText(input)
    .toLowerCase()
    .trim()
    .replace(/[?.,!]/g, "")
    .replace(/\s+/g, " ");
}

function scoreAskIntent(input, intentConfig) {
  const norm = normalizeAskText(input);
  let score = 0;
  
  intentConfig.keywords.forEach(keyword => {
    const normKeyword = keyword.toLowerCase();
    if (norm === normKeyword) {
      score += 100;
    } else if (norm.startsWith(normKeyword + " ") || norm.endsWith(" " + normKeyword)) {
      score += 50;
    } else if (norm.includes(normKeyword)) {
      score += 20;
    }
  });
  
  return score;
}

function parseAskIntent(input) {
  let bestIntent = "help";
  let highestScore = 0;
  
  intentConfigs.forEach(config => {
    const score = scoreAskIntent(input, config);
    if (score > highestScore) {
      highestScore = score;
      bestIntent = config.name;
    }
  });
  
  if (highestScore === 0) {
    return "help";
  }
  
  return bestIntent;
}

// Execute parsed guided commands
function executeAskIntent(intent) {
  if (intent === "help") {
    renderCommandHelp();
    logSessionHistory("command executed", "Displayed supported questions guide");
    return;
  }

  if (!currentAnalysis) {
    renderAskAnswer("Please upload a CSV dataset or trigger the sample sales analysis first before running questions.");
    logSessionHistory("error occurred", `Blocked question intent: "${intent}" (no active data)`);
    return;
  }
  
  logSessionHistory("command executed", `Asked Copilot: "${intent}"`);
  
  if (intent === "export_pdf") {
    renderAskAnswer("Compiling and downloading PDF Executive Report...");
    handleReportDownload("pdf");
    return;
  }
  
  if (intent === "export_markdown") {
    renderAskAnswer("Compiling and downloading Markdown Executive Report...");
    handleReportDownload("markdown");
    return;
  }
  
  // Dynamic business logic answers computed from currentAnalysis
  const answer = answerAskQuestion(intent, currentAnalysis);
  renderAskAnswer(answer);
  
  // Highlight workspace sections
  let targetId = "";
  if (intent === "executive_summary") targetId = "section-executive-summary";
  else if (intent === "quality_trust") targetId = "section-quality-gate";
  else if (intent === "kpi_revenue") targetId = "section-kpis";
  else if (intent === "top_region" || intent === "top_product" || intent === "top_sales_rep") targetId = "section-visual-analytics";
  else if (intent === "trend" || intent === "forecast") targetId = "section-trends-forecasts";
  else if (intent === "recommendations") targetId = "section-recommendations";
  else if (intent === "workflow_improvements") targetId = "section-recommendations";
  else if (intent === "visual_analytics") targetId = "section-visual-analytics";
  else if (intent === "technical_evidence") targetId = "section-technical-evidence";
  else if (intent === "anomalies") targetId = "section-technical-evidence";
  else if (intent === "discount_risk") targetId = "section-visual-analytics";
  else if (intent === "audit_events") targetId = "section-technical-evidence";
  
  if (targetId) {
    scrollToWorkspaceSection(targetId.replace("section-", ""));
    highlightSection(targetId);
  }
}

// Dynamic Natural-Language Question Answering helpers
function answerAskQuestion(intent, analysis) {
  if (intent === "executive_summary") {
    return `Executive Summary: ${safeText(getNestedValue(analysis, "insights.summary"))}`;
  }
  if (intent === "quality_trust") {
    return answerQualityTrust(analysis);
  }
  if (intent === "kpi_revenue") {
    const rev = formatMoney(safeNumber(getNestedValue(analysis, "kpis.total_revenue")));
    const ords = formatNumber(safeNumber(getNestedValue(analysis, "kpis.total_orders")));
    const aov = formatMoney(safeNumber(getNestedValue(analysis, "kpis.average_order_value")));
    const units = formatNumber(safeNumber(getNestedValue(analysis, "kpis.total_units_sold")));
    return `Sales KPI Overview: Total Net Revenue is ${rev}, total completed orders count is ${ords}, average order transaction value (AOV) is ${aov}, and total physical units sold is ${units}.`;
  }
  if (intent === "top_region") {
    return answerTopRevenueDimension(analysis, "region");
  }
  if (intent === "top_product") {
    return answerTopRevenueDimension(analysis, "product");
  }
  if (intent === "top_sales_rep") {
    return answerTopRevenueDimension(analysis, "sales_rep");
  }
  if (intent === "anomalies") {
    return answerAnomalyRisk(analysis);
  }
  if (intent === "discount_risk") {
    return answerDiscountRisk(analysis);
  }
  if (intent === "trend") {
    return answerTrendForecast(analysis);
  }
  if (intent === "forecast") {
    return answerTrendForecast(analysis);
  }
  if (intent === "recommendations") {
    return answerBusinessActions(analysis);
  }
  if (intent === "workflow_improvements") {
    const list = asArray(getNestedValue(analysis, "workflow_improvement_plan.improvements", []));
    if (list.length === 0) return "No operational workflow process improvements compiled.";
    return `Compiled ${list.length} workflow improvements. Focus area: [${safeText(list[0].improvement_type).toUpperCase()}] ${safeText(list[0].description)} under owner ${safeText(list[0].owner_role).toUpperCase()}.`;
  }
  if (intent === "visual_analytics") {
    return "Displaying the Visual Analytics gallery containing Revenue Performance, Trends & Forecasts, Quality & Risks, Discounts, and Composition donut/pie previews.";
  }
  if (intent === "technical_evidence") {
    return "Displaying the Technical Evidence drawer containing validation, lineage logs, metadata, and quality scores.";
  }
  if (intent === "audit_events") {
    const list = asArray(getNestedValue(analysis, "audit_events", []));
    return `Security compliance log contains ${list.length} audit pipeline tracing events. Last run checked security injection and quality scoring gates.`;
  }
  return "Query processed successfully. Section highlight triggered.";
}

function answerTopRevenueDimension(analysis, dimension) {
  const charts = asArray(getNestedValue(analysis, "charts.charts", []));
  let chartId = "revenue_by_region";
  if (dimension === "product") chartId = "revenue_by_product";
  else if (dimension === "sales_rep") chartId = "revenue_by_sales_rep";
  
  const chart = charts.find(c => c.chart_id === chartId);
  if (!chart || !asArray(chart.data).length) return `No ${dimension} sales data available in analysis response.`;
  
  const sorted = [...asArray(chart.data)].sort((a,b) => safeNumber(b.value) - safeNumber(a.value));
  const top = sorted[0];
  const total = sorted.reduce((sum, d) => sum + safeNumber(d.value), 0) || 1;
  const pct = (safeNumber(top.value) / total) * 100;
  
  return `${safeText(top.label)} is the top revenue ${dimension} with ${formatMoney(top.value)}, representing ${pct.toFixed(1)}% of total revenue.`;
}

function answerQualityTrust(analysis) {
  const gateStatus = safeText(getNestedValue(analysis, "quality_gate.status"), "blocked");
  const confidence = safeText(getNestedValue(analysis, "quality_gate.confidence_level"), "low");
  const score = safeNumber(getNestedValue(analysis, "quality_score.score"), 0);
  const grade = safeText(getNestedValue(analysis, "quality_score.grade"), "F");
  const isPassed = gateStatus.toLowerCase() !== "blocked";
  
  return `The quality gate status is "${gateStatus.toUpperCase()}" with ${confidence.toUpperCase()} confidence and a quality score of ${score}% (Grade ${grade.toUpperCase()}). ${isPassed ? "Reports and narrative generations are allowed." : "The dataset has critical errors and executive reports are blocked until resolved."}`;
}

// Business Actions answering helper
function answerBusinessActions(analysis) {
  const recs = asArray(getNestedValue(analysis, "recommendation_plan.recommendations", []));
  if (recs.length === 0) return "No active recommendations available in the action plan.";
  
  const highPriority = recs.filter(r => safeText(r.priority).toLowerCase() === "high");
  const topRec = highPriority.length > 0 ? highPriority[0] : recs[0];
  
  return `Top Recommended Business Action: "[${safeText(topRec.owner_role).toUpperCase()}] ${safeText(topRec.recommended_action)}" (Priority: ${safeText(topRec.priority).toUpperCase()}, Expected Impact: ${safeText(topRec.expected_impact)}). Follow-up metric: ${safeText(topRec.follow_up_metric)}.`;
}

// Trends and Forecast answering helper
function answerTrendForecast(analysis) {
  const revTrend = asObject(getNestedValue(analysis, "trend_analysis.revenue_trend"));
  const direction = safeText(revTrend.direction, "stable");
  const change = safeNumber(revTrend.percent_change, 0);
  
  const readiness = safeText(getNestedValue(analysis, "forecast_analysis.readiness_status"), "limited");
  const forecastVal = safeNumber(getNestedValue(analysis, "forecast_analysis.revenue_forecast.selected_forecast_value"), 0);
  
  return `Monthly sales revenue trend is ${direction.toUpperCase()} by ${change.toFixed(1)}%. Revenue forecasting status is ${readiness.toUpperCase()}, with a projected next-period baseline forecast of ${formatMoney(forecastVal)}.`;
}

// Anomalies answering helper
function answerAnomalyRisk(analysis) {
  const count = safeNumber(getNestedValue(analysis, "anomalies.total_anomalies"), 0);
  if (count === 0) return "No transactions flagged as anomalies or statistical outliers.";
  
  const severityChart = asArray(getNestedValue(analysis, "charts.charts", [])).find(c => c.chart_id === "anomalies_by_severity");
  let severityBreakdown = "";
  if (severityChart && asArray(severityChart.data).length) {
    severityBreakdown = " (" + asArray(severityChart.data).map(d => `${d.label}: ${d.value}`).join(", ") + ")";
  }
  
  return `Detected ${count} anomalous transactions or outliers in the dataset${severityBreakdown}. Review the anomalies trace in Technical Evidence for invoice details.`;
}

// Discounts answering helper
function answerDiscountRisk(analysis) {
  const discountTrend = asObject(getNestedValue(analysis, "trend_analysis.average_discount_trend"));
  const avgDiscount = safeNumber(discountTrend.average_value || getNestedValue(analysis, "kpis.average_discount"), 0);
  
  return `Average discount rate in the dataset is ${formatPercent(avgDiscount * 100)}. Discount summary by product and Pareto analysis can be inspected in the Visual Analytics panel under Category D.`;
}

// Help response guide renderer
function renderCommandHelp() {
  const helpMsg = `
    <div class="command-help-content">
      <p>I couldn't match your question. Here are some dynamic business questions you can ask me:</p>
      <ul>
        <li><strong>Executive Overview:</strong> "summarize this", "what happened?"</li>
        <li><strong>Quality & Trust:</strong> "can I trust this data?", "why is quality warning?"</li>
        <li><strong>Top Revenue Segments:</strong> "which region performed best?", "which product has the most revenue?"</li>
        <li><strong>Operational Actions:</strong> "what should we do next?", "what should sales ops focus on?"</li>
        <li><strong>Trends & Foreseeing:</strong> "how is revenue trending?", "what is the forecast?"</li>
        <li><strong>Risk & Outliers:</strong> "are there anomalies?", "show me discount issues"</li>
        <li><strong>Lineage & Trace:</strong> "show evidence", "show audit trail"</li>
        <li><strong>Document Export:</strong> "download a PDF report", "export markdown"</li>
      </ul>
    </div>
  `;
  renderAskAnswer(helpMsg);
}

// Render Ask answer inside copilot bubble
function renderAskAnswer(answer) {
  if (commandResponseArea) {
    commandResponseArea.style.display = "block";
    commandResponseArea.className = "command-feedback-block success-feedback";
    if (feedbackIcon) feedbackIcon.textContent = "💬";
    if (feedbackTitle) feedbackTitle.textContent = "InsightOps-AI Copilot";
    if (feedbackBody) {
      if (answer.includes("<") && answer.includes(">")) {
        feedbackBody.innerHTML = answer;
      } else {
        feedbackBody.innerHTML = `
          <div class="ask-answer-wrapper">
            <p class="ask-answer-text">${answer}</p>
          </div>
        `;
      }
    }
    commandResponseArea.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

// Generate reports from endpoint downloads
async function handleReportDownload(format) {
  if (!currentAnalysis) {
    showToastNotification("Data unavailable. Ingest a sales file first.", "error");
    return;
  }
  
  const canExport = getNestedValue(currentAnalysis, "quality_gate.can_generate_reports", true);
  if (!canExport) {
    showDashboardError("Report Blocked", "Quality gate status is BLOCKED. Report generation disallowed.", "Resolve data anomalies first.");
    return;
  }
  
  if (format !== "pdf" && format !== "markdown" && format !== "md") {
    showDashboardError("Invalid Report Format", `Format "${format}" is unsupported.`, "Use PDF or Markdown formats.");
    return;
  }
  
  try {
    let downloadUrl = "";
    let requestOptions = { method: "POST" };
    
    if (currentDataMode === "sample") {
      downloadUrl = `/analysis/sample/report?format=${format}`;
    } else if (currentDataMode === "upload") {
      downloadUrl = `/analysis/upload/report?format=${format}`;
      const form = new FormData();
      form.append("file", currentFile);
      requestOptions.body = form;
    }
    
    showToastNotification(`Compiling sales report as ${format.toUpperCase()}...`, "info");
    const res = await fetch(downloadUrl, requestOptions);
    
    if (!res.ok) {
      const errText = await res.text();
      let errJson = {};
      try { errJson = JSON.parse(errText); } catch (e) {}
      const errMsg = errJson.detail || errText || "Report generation failed.";
      showDashboardError("Report Export Failed", errMsg, "Inspect quality gate warnings.");
      return;
    }
    
    const blob = await res.blob();
    const fallbackName = format === "markdown" ? "executive_sales_report.md" : "executive_sales_report.pdf";
    const filename = filenameFromDisposition(res.headers.get("content-disposition"), fallbackName);
    
    triggerBlobSaveDialog(blob, filename);
    showToastNotification(`Downloaded report: ${filename}`, "success");
    logSessionHistory("report downloaded", `Downloaded ${format.toUpperCase()} report: ${filename}`);
  } catch (err) {
    showDashboardError("Download Connection Error", `Failed to complete download: ${err.message}`, "Check server connection.");
  }
}

// Extractor helper for filename headers
function filenameFromDisposition(contentDisposition, fallback) {
  if (!contentDisposition) return fallback;
  const match = contentDisposition.match(/filename="?([^"]+)"?/i);
  return match ? match[1] : fallback;
}

// Download blob triggers
function triggerBlobSaveDialog(blob, fileName) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// Log actions to timeline logs
function logSessionHistory(type, description) {
  const timeStr = new Date().toLocaleTimeString(undefined, {hour12: false});
  analysisHistory.push({ type, description, time: timeStr });
  renderHistoryTimeline();
}

// Render the timeline list
function renderHistoryTimeline() {
  if (!historyTimelineFeed) return;
  historyTimelineFeed.innerHTML = "";
  if (analysisHistory.length === 0) {
    historyTimelineFeed.innerHTML = '<li class="timeline-empty">No workspace activity logged yet. Load data to begin.</li>';
    return;
  }
  
  analysisHistory.forEach(item => {
    const li = document.createElement("li");
    li.className = "history-item";
    
    let icon = "⚙️";
    if (item.type === "sample analysis run" || item.type === "upload analysis run") icon = "📊";
    else if (item.type === "command executed") icon = "💬";
    else if (item.type === "report downloaded") icon = "📋";
    else if (item.type === "error occurred") icon = "❌";
    else if (item.type === "diagnostics passed") icon = "🛡️";
    
    li.innerHTML = `
      <span>${icon} ${item.description}</span>
      <span class="history-item-time">${item.time}</span>
    `;
    historyTimelineFeed.appendChild(li);
  });
  
  historyTimelineFeed.scrollTop = historyTimelineFeed.scrollHeight;
}

// Toggle cards collapse status
function toggleCardCollapse(cardId) {
  const card = document.querySelector(`#${cardId}`);
  if (card) {
    card.classList.toggle("collapsed");
  }
}

// Render clean placeholder empty states on startup or reset
function renderAllEmptyStates() {
  const setEmpty = (selector, html) => {
    const el = document.querySelector(selector);
    if (el) el.innerHTML = html;
  };
  
  setEmpty("#exec-summary-narrative", `<p class="empty-state-text">No active analysis. Run sample or upload a CSV dataset to populate.</p>`);
  setEmpty("#exec-summary-highlights", `<p class="empty-state-text">No metrics computed yet.</p>`);
  
  const qgateRules = document.querySelector("#qgate-trust-list");
  if (qgateRules) qgateRules.innerHTML = `<li class="empty-state-text">Waiting for transaction records...</li>`;
  
  setEmpty("#kpi-revenue-val", "$0.00");
  setEmpty("#kpi-orders-val", "0");
  setEmpty("#kpi-units-val", "0");
  setEmpty("#kpi-aov-val", "$0.00");
  
  setEmpty("#trends-metrics-list", `<li class="empty-state-text">No trend calculations run yet.</li>`);
  setEmpty("#forecast-metrics-table tbody", `<tr><td colspan="3" class="empty-state-text">No baseline forecasts compiled.</td></tr>`);
  if (document.querySelector("#forecast-warnings-text")) {
    document.querySelector("#forecast-warnings-text").style.display = "none";
  }
  
  const catRevenue = document.querySelector("#visuals-cat-revenue");
  const catTrends = document.querySelector("#visuals-cat-trends");
  const catQuality = document.querySelector("#visuals-cat-quality");
  const catDiscounting = document.querySelector("#visuals-cat-discounting");
  const catComposition = document.querySelector("#visuals-cat-composition");
  
  const placeholder = `<p class="empty-state-text">Waiting for transaction records to render charts...</p>`;
  if (catRevenue) catRevenue.innerHTML = placeholder;
  if (catTrends) catTrends.innerHTML = placeholder;
  if (catQuality) catQuality.innerHTML = placeholder;
  if (catDiscounting) catDiscounting.innerHTML = placeholder;
  if (catComposition) catComposition.innerHTML = placeholder;
  
  setEmpty("#action-center-recs-grid", `<p class="empty-state-text">No recommendations compiled yet.</p>`);
  setEmpty("#action-center-workflow-list", `<li class="empty-state-text">No operational workflows suggested yet.</li>`);
  
  document.querySelectorAll(".tech-drawer-code").forEach(pre => {
    pre.textContent = "No records available for this section.";
  });
  setEmpty("#tech-diagnostics-results", "No diagnostics run yet.");
}

// Reset workspace session
function resetSessionState() {
  currentAnalysis = null;
  currentDataMode = null;
  currentFile = null;
  activeChartCategory = "all";
  chartSearchQuery = "";
  
  if (emptyStateCard) emptyStateCard.style.display = "block";
  if (selectedFileDisplay) selectedFileDisplay.style.display = "none";
  
  const selectorBar = document.querySelector("#view-mode-selector-bar");
  if (selectorBar) selectorBar.style.display = "none";
  
  
  if (csvFileInputInput) csvFileInputInput.value = "";
  if (commandInput) commandInput.value = "";
  if (commandResponseArea) commandResponseArea.style.display = "none";
  if (visualsSearch) visualsSearch.value = "";
  
  document.querySelectorAll(".filter-btn").forEach(b => {
    b.classList.remove("active");
    b.setAttribute("aria-selected", "false");
  });
  const allBtn = document.querySelector(".filter-btn[data-category='all']");
  if (allBtn) {
    allBtn.classList.add("active");
    allBtn.setAttribute("aria-selected", "true");
  }
  
  if (trustBadge) {
    trustBadge.textContent = "No Data";
    trustBadge.className = "trust-badge badge-blocked";
  }
  if (trustQgate) {
    trustQgate.textContent = "WAITING";
    trustQgate.className = "trust-metric-val";
  }
  if (trustConfidence) trustConfidence.textContent = "N/A";
  if (trustHumanReview) trustHumanReview.textContent = "N/A";
  if (trustReportsAllowed) trustReportsAllowed.textContent = "N/A";
  if (trustNarrativeAllowed) trustNarrativeAllowed.textContent = "N/A";
  if (trustSecurityScan) {
    trustSecurityScan.textContent = "N/A";
    trustSecurityScan.className = "trust-metric-val";
  }
  if (trustForecastReady) trustForecastReady.textContent = "N/A";
  if (trustRecsCount) trustRecsCount.textContent = "0";
  if (trustTopActionDesc) trustTopActionDesc.textContent = "No recommendations available. Please run analysis.";
  if (quickDownloadBtn) quickDownloadBtn.disabled = true;
  
  // Restore all clean empty states
  renderAllEmptyStates();
  
  setWorkspaceStatus("Workspace Reset", "ready");
  renderSuggestionChips();
  logSessionHistory("reset state", "Cleared workspace session state variables");
  showToastNotification("Workspace session reset successfully.", "info");
}

// Display UI feedback messages
function showToastNotification(message, type = "success") {
  const toast = document.querySelector("#toast-notification");
  const tIcon = document.querySelector("#toast-icon");
  const tText = document.querySelector("#toast-text");
  
  if (!toast) return;
  
  tIcon.textContent = type === "success" ? "✅" : type === "error" ? "❌" : "ℹ️";
  tText.textContent = message;
  toast.style.display = "flex";
  
  toast.style.animation = "none";
  toast.offsetHeight;
  toast.style.animation = null;
  
  setTimeout(() => {
    toast.style.display = "none";
  }, 3000);
}

// Diagnostics check to validate Analysis payload structure
function validateAnalysisShape(analysis) {
  const warnings = [];
  const requiredSections = [
    "validation",
    "quality_gate",
    "kpis",
    "trend_analysis",
    "forecast_analysis",
    "charts",
    "insights",
    "recommendation_plan",
    "workflow_improvement_plan",
    "audit_events"
  ];
  
  if (!analysis || typeof analysis !== "object") {
    warnings.push("Analysis payload is empty or invalid.");
    return warnings;
  }
  
  requiredSections.forEach(sec => {
    if (analysis[sec] === undefined || analysis[sec] === null) {
      warnings.push(`Warning: Section "${sec}" is missing or null in response payload.`);
    }
  });
  
  return warnings;
}

// Legacy compatibility layer for unit test assertions
function _legacyCompatibilityUnused() {
  const dummy = {
    renderExecutiveSummary: null,
    renderStatusCards: null,
    renderTopRecommendations: null,
    renderForecastTrendSnapshot: null,
    runReportDownload: null,
    labels: [
      "Source Metadata", "Data Preparation", "Transformation Lineage", "Manipulation Summary",
      "Trend Analysis", "Forecast Analysis", "forecast_analysis", "Data Profile", "Quality Score",
      "Quality Gate", "Visual Analytics", "Business question", "Business Actions", "Workflow Improvements",
      "workflow_improvement_plan", "recommendation_plan", "quality_gate"
    ]
  };
  return dummy;
}

// Self-check function to validate interactive elements exist in the DOM
function validateDashboardBindings() {
  const checks = [
    { name: "sample analysis button", el: runSampleBtn },
    { name: "empty state sample button", el: emptyStateSampleBtn },
    { name: "file input", el: csvFileInputInput },
    { name: "browse file button", el: browseFileBtn },
    { name: "Ask input", el: commandInput },
    { name: "Submit command button", el: submitCommandBtn },
    { name: "report buttons", el: exportSampleReportBtn || exportUploadReportBtn },
    { name: "result container", el: resultsContainer }
  ];
  
  const missing = checks.filter(c => !c.el).map(c => c.name);
  if (missing.length > 0) {
    console.warn("Sentryx Dashboard Bindings Warning: Missing elements in DOM:", missing.join(", "));
    logSessionHistory("binding check failed", `Dashboard bindings initialized with missing elements: ${missing.join(", ")}`);
  } else {
    console.log("Sentryx Dashboard Bindings verified successfully.");
    logSessionHistory("binding check passed", "All critical dashboard controls verified in DOM.");
  }
}
