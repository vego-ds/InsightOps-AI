const sampleButton = document.querySelector("#sample-button");
const sampleReportButton = document.querySelector("#sample-report-button");
const uploadForm = document.querySelector("#upload-form");
const uploadReportButton = document.querySelector("#upload-report-button");
const fileInput = document.querySelector("#csv-file");
const reportFormatInput = document.querySelector("#report-format");
const statusEl = document.querySelector("#status");
const errorEl = document.querySelector("#error");
const resultsEl = document.querySelector("#results");

const priorityOrder = {
  high: 0,
  medium: 1,
  low: 2,
};

sampleButton.addEventListener("click", async () => {
  await runAnalysis(() => fetch("/analysis/sample"));
});

sampleReportButton.addEventListener("click", async () => {
  await runReportDownload(() =>
    fetch(`/analysis/sample/report?format=${encodeURIComponent(selectedReportFormat())}`, {
      method: "POST",
    }),
  );
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (!fileInput.files.length) {
    showError("Choose a CSV file before uploading.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  await runAnalysis(() =>
    fetch("/analysis/upload", {
      method: "POST",
      body: formData,
    }),
  );
});

uploadReportButton.addEventListener("click", async () => {
  if (!fileInput.files.length) {
    showError("Choose a CSV file before downloading an upload report.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  await runReportDownload(() =>
    fetch(`/analysis/upload/report?format=${encodeURIComponent(selectedReportFormat())}`, {
      method: "POST",
      body: formData,
    }),
  );
});

async function runAnalysis(requestFactory) {
  setLoading(true);
  hideError();
  resultsEl.hidden = true;

  try {
    const response = await requestFactory();
    const payload = await parseResponsePayload(response);

    if (!response.ok) {
      showError(formatErrorMessage(response.status, payload));
      return;
    }

    renderResults(payload);
  } catch (error) {
    showError(`Analysis request failed: ${error.message}`);
  } finally {
    setLoading(false);
  }
}

async function runReportDownload(requestFactory) {
  setLoading(true, "Generating report artifact...");
  hideError();

  try {
    const response = await requestFactory();
    if (!response.ok) {
      const payload = await parseResponsePayload(response);
      showError(formatErrorMessage(response.status, payload));
      return;
    }

    const blob = await response.blob();
    const fileName = filenameFromDisposition(
      response.headers.get("content-disposition"),
      fallbackReportFileName(),
    );
    downloadBlob(blob, fileName);
    statusEl.textContent = `Downloaded ${fileName}.`;
  } catch (error) {
    showError(`Report download failed: ${error.message}`);
  } finally {
    setLoading(false);
  }
}

async function parseResponsePayload(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  return { detail: await response.text() };
}

function formatErrorMessage(statusCode, payload) {
  const detail = payload.detail || payload.message || "Analysis request failed.";
  return `Request failed with status ${statusCode}: ${detail}`;
}

function setLoading(isLoading, message = "Running deterministic analysis...") {
  sampleButton.disabled = isLoading;
  uploadForm.querySelector("button").disabled = isLoading;
  sampleReportButton.disabled = isLoading;
  uploadReportButton.disabled = isLoading;
  reportFormatInput.disabled = isLoading;
  statusEl.textContent = isLoading ? message : "";
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function hideError() {
  errorEl.hidden = true;
  errorEl.textContent = "";
}

function selectedReportFormat() {
  return reportFormatInput.value || "pdf";
}

function fallbackReportFileName() {
  return selectedReportFormat() === "markdown"
    ? "executive_sales_report.md"
    : "executive_sales_report.pdf";
}

function filenameFromDisposition(contentDisposition, fallback) {
  if (!contentDisposition) {
    return fallback;
  }

  const match = contentDisposition.match(/filename="?([^"]+)"?/i);
  return match ? match[1] : fallback;
}

function downloadBlob(blob, fileName) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

function renderResults(analysis) {
  resultsEl.innerHTML = [
    renderExecutiveSummary(analysis),
    renderStatusCards(analysis),
    renderTopRecommendations(analysis),
    renderForecastTrendSnapshot(analysis),
    renderCharts(analysis.charts),
    renderReportArtifactGuidance(),
    renderTechnicalEvidence(analysis),
  ].join("");
  resultsEl.hidden = false;
}

function renderExecutiveSummary(analysis) {
  return panel(
    "Executive Summary",
    `
      <p class="summary-copy">${escapeHtml(safeGet(analysis, "insights.summary", "No executive summary available."))}</p>
      ${metricGrid([
        ["Total Revenue", formatMoney(safeGet(analysis, "kpis.total_revenue", 0))],
        ["Total Orders", safeGet(analysis, "kpis.total_orders", 0)],
        ["Total Anomalies", safeGet(analysis, "anomalies.total_anomalies", 0)],
        ["Quality Gate", safeGet(analysis, "quality_gate.status", "unknown")],
        ["Quality Confidence", safeGet(analysis, "quality_gate.confidence_level", "unknown")],
        ["Forecast Readiness", safeGet(analysis, "forecast_analysis.readiness_status", "unknown")],
        ["Forecast Confidence", safeGet(analysis, "forecast_analysis.confidence_level", "unknown")],
        ["Recommendations", safeGet(analysis, "recommendation_plan.total_recommendations", 0)],
        ["Workflow Improvements", safeGet(analysis, "workflow_improvement_plan.total_workflows", 0)],
      ])}
    `,
    "executive-summary",
  );
}

function renderStatusCards(analysis) {
  const highSeverityCount = safeArray(safeGet(analysis, "anomalies.anomalies", []))
    .filter((anomaly) => anomaly.severity === "high").length;
  const highPriorityCount = safeArray(
    safeGet(analysis, "recommendation_plan.recommendations", []),
  ).filter((recommendation) => recommendation.priority === "high").length;

  return panel(
    "Decision Status Cards",
    `
      <div class="status-card-grid">
        ${statusCard(
          "Quality Gate",
          safeGet(analysis, "quality_gate.status", "unknown"),
          [
            ["Confidence", safeGet(analysis, "quality_gate.confidence_level", "unknown")],
            ["Human Review", safeGet(analysis, "quality_gate.human_review_required", false)],
          ],
        )}
        ${statusCard(
          "Forecast Readiness",
          safeGet(analysis, "forecast_analysis.readiness_status", "unknown"),
          [
            ["Confidence", safeGet(analysis, "forecast_analysis.confidence_level", "unknown")],
            ["Next Period", safeGet(analysis, "forecast_analysis.next_period", "None") || "None"],
          ],
        )}
        ${statusCard(
          "Security Review",
          safeGet(analysis, "security.human_review_required", false) ? "review" : "pass",
          [
            ["Prompt Injection", safeGet(analysis, "security.prompt_injection_detected", false)],
            ["Human Review", safeGet(analysis, "security.human_review_required", false)],
          ],
        )}
        ${statusCard(
          "Anomaly Risk",
          highSeverityCount > 0 ? "high" : safeGet(analysis, "anomalies.total_anomalies", 0) > 0 ? "medium" : "low",
          [
            ["Total Anomalies", safeGet(analysis, "anomalies.total_anomalies", 0)],
            ["High Severity", highSeverityCount],
          ],
        )}
        ${statusCard(
          "Recommendations",
          highPriorityCount > 0 ? "high" : "medium",
          [
            ["Total", safeGet(analysis, "recommendation_plan.total_recommendations", 0)],
            ["High Priority", highPriorityCount],
          ],
        )}
      </div>
    `,
    "decision-status",
  );
}

function statusCard(title, status, rows) {
  return `
    <article class="status-card status-${statusClass(status)}">
      <div class="status-card-header">
        <h3>${escapeHtml(title)}</h3>
        ${badge(status, "status-badge")}
      </div>
      ${rows
        .map(
          ([label, value]) => `
            <p><span>${escapeHtml(label)}</span><strong>${escapeHtml(formatValue(value))}</strong></p>
          `,
        )
        .join("")}
    </article>
  `;
}

function renderTopRecommendations(analysis) {
  const recommendations = safeArray(
    safeGet(analysis, "recommendation_plan.recommendations", []),
  )
    .slice()
    .sort((left, right) => {
      const leftPriority = priorityOrder[left.priority] ?? 99;
      const rightPriority = priorityOrder[right.priority] ?? 99;
      return leftPriority - rightPriority || left.recommendation_id.localeCompare(right.recommendation_id);
    })
    .slice(0, 5);

  if (!recommendations.length) {
    return panel(
      "Business Actions",
      '<p class="empty-state">No business recommendations were generated.</p>',
      "business-actions",
    );
  }

  return panel(
    "Business Actions",
    recommendations
      .map(
        (recommendation) => `
          <article class="action-card priority-${statusClass(recommendation.priority)}">
            <div class="action-card-header">
              ${badge(recommendation.priority, "priority-badge")}
              <h3>${escapeHtml(recommendation.title)}</h3>
            </div>
            ${metricGrid([
              ["Business Area", recommendation.business_area],
              ["Owner", recommendation.owner_role],
              ["Follow-up Metric", recommendation.follow_up_metric],
            ])}
            <p><strong>Recommended action:</strong> ${escapeHtml(recommendation.recommended_action)}</p>
            <p><strong>Expected impact:</strong> ${escapeHtml(recommendation.expected_impact)}</p>
            <p><strong>Related insight IDs:</strong> ${escapeHtml(formatInlineList(recommendation.related_insight_ids))}</p>
            <p><strong>Related chart IDs:</strong> ${escapeHtml(formatInlineList(recommendation.related_chart_ids))}</p>
          </article>
        `,
      )
      .join(""),
    "business-actions",
  );
}

function renderForecastTrendSnapshot(analysis) {
  const revenueForecast = safeGet(analysis, "forecast_analysis.revenue_forecast", null);
  const orderCountForecast = safeGet(analysis, "forecast_analysis.order_count_forecast", null);

  return panel(
    "Forecast and Trend Snapshot",
    `
      ${metricGrid([
        ["Next Forecast Period", safeGet(analysis, "forecast_analysis.next_period", "None") || "None"],
        ["Revenue Forecast", formatForecastValue(revenueForecast, true)],
        ["Order Count Forecast", formatForecastValue(orderCountForecast, false)],
        ["Forecast Confidence", safeGet(analysis, "forecast_analysis.confidence_level", "unknown")],
        ["Revenue Trend", safeGet(analysis, "trend_analysis.revenue_trend.direction", "unknown")],
        ["Order Count Trend", safeGet(analysis, "trend_analysis.order_count_trend.direction", "unknown")],
        ["Discount Trend", safeGet(analysis, "trend_analysis.average_discount_trend.direction", "unknown")],
      ])}
      <h3>Major Forecast Warnings</h3>
      ${list(safeArray(safeGet(analysis, "forecast_analysis.warnings", [])), "No forecast warnings.")}
    `,
    "forecast-trend-snapshot",
  );
}

function renderCharts(charts) {
  const chartSections = safeArray(safeGet(charts, "charts", []))
    .map(
      (chart) => `
        <article class="chart-card">
          <h3>${escapeHtml(chart.title)}</h3>
          <p><strong>Business question:</strong> ${escapeHtml(chart.business_question || "None")}</p>
          <p><strong>Interpretation:</strong> ${escapeHtml(chart.interpretation || "None")}</p>
          <h4>Recommended Actions</h4>
          ${list(chart.recommended_actions || [], "No chart-specific recommended actions.")}
          <p><strong>Related insight IDs:</strong> ${escapeHtml(formatInlineList(chart.related_insight_ids || []))}</p>
          ${renderBarPreview(chart)}
          <h4>${chart.chart_type === "line" ? "Period Data" : "Chart Data"}</h4>
          ${table(
            [chart.x_axis, chart.y_axis, "secondary_value"],
            safeArray(chart.data).map((point) => [
              point.label,
              point.value,
              point.secondary_value ?? "None",
            ]),
            "No chart data available.",
          )}
        </article>
      `,
    )
    .join("");

  return panel("Visual Analytics", chartSections || '<p class="empty-state">No charts available.</p>', "visual-analytics");
}

function renderReportArtifactGuidance() {
  return panel(
    "Report Artifact Guidance",
    `
      <p>
        Markdown and PDF report generation is available through safe export
        endpoints. Reports are generated per request in temporary storage and
        returned as downloads; uploaded user files and generated reports are not
        persisted by the dashboard workflow.
      </p>
    `,
    "report-guidance",
  );
}

function renderTechnicalEvidence(analysis) {
  return panel(
    "Technical Evidence",
    [
      technicalPanel("Source Metadata", renderSourceMetadata(analysis.source_metadata)),
      technicalPanel("Validation", renderValidation(analysis.validation)),
      technicalPanel("Data Profile", renderDataProfile(analysis.data_profile)),
      technicalPanel("Quality Score", renderQualityScore(analysis.quality_score)),
      technicalPanel("Data Preparation", renderPreparation(analysis.preparation)),
      technicalPanel("Transformation Lineage", renderTransformationLog(analysis.transformation_log)),
      technicalPanel("Manipulation Summary", renderManipulationSummary(analysis.manipulation_summary)),
      technicalPanel("Trend Analysis", renderTrendAnalysis(analysis.trend_analysis)),
      technicalPanel("Forecast Analysis", renderForecastAnalysis(analysis.forecast_analysis)),
      technicalPanel("KPI Summary", renderKpis(analysis.kpis)),
      technicalPanel("Security", renderSecurity(analysis.security)),
      technicalPanel("Anomalies", renderAnomalies(analysis.anomalies)),
      technicalPanel("Executive Insights", renderInsights(analysis.insights)),
      technicalPanel("Workflow Improvements", renderWorkflowImprovements(analysis.workflow_improvement_plan)),
      technicalPanel("Audit Events", renderAuditEvents(analysis.audit_events)),
      technicalPanel("Raw JSON", `<pre class="raw-json">${escapeHtml(JSON.stringify(analysis, null, 2))}</pre>`),
    ].join(""),
    "technical-evidence",
  );
}

function renderSourceMetadata(sourceMetadata) {
  return metricGrid([
    ["Source Type", safeGet(sourceMetadata, "source_type", "unknown")],
    ["File Name", safeGet(sourceMetadata, "file_name", "unknown")],
    ["File Size", `${safeGet(sourceMetadata, "file_size_bytes", 0)} bytes`],
    ["Collection Method", safeGet(sourceMetadata, "collection_method", "unknown")],
    ["Record Count", safeGet(sourceMetadata, "record_count", 0)],
    ["Notes", safeGet(sourceMetadata, "notes", "None") || "None"],
  ]);
}

function renderValidation(validation) {
  return metricGrid([
    ["Total Rows", safeGet(validation, "total_rows", 0)],
    ["Valid Rows", safeGet(validation, "valid_rows", 0)],
    ["Invalid Rows", safeGet(validation, "invalid_rows", 0)],
    ["Errors", safeArray(safeGet(validation, "errors", [])).length],
  ]);
}

function renderDataProfile(profile) {
  return `
    ${metricGrid([
      ["Date Range", formatDateRange(profile)],
      ["Unique Customers", safeGet(profile, "unique_customers", 0)],
      ["Unique Regions", safeGet(profile, "unique_regions", 0)],
      ["Unique Products", safeGet(profile, "unique_products", 0)],
      ["Unique Sales Reps", safeGet(profile, "unique_sales_reps", 0)],
      ["Duplicate Order IDs", safeGet(profile, "duplicate_order_ids", 0)],
    ])}
    <h3>Missing Field Counts</h3>
    ${objectTable(safeGet(profile, "missing_field_counts", {}), "Field", "Count", "No missing fields detected.")}
    <h3>Numeric Summaries</h3>
    ${table(
      ["Metric", "Minimum", "Maximum", "Mean", "Median", "Std Dev"],
      [
        ["Revenue", ...numericSummaryCells(safeGet(profile, "revenue_summary", {}))],
        ["Quantity", ...numericSummaryCells(safeGet(profile, "quantity_summary", {}))],
        ["Discount", ...numericSummaryCells(safeGet(profile, "discount_summary", {}))],
        ["Unit Price", ...numericSummaryCells(safeGet(profile, "unit_price_summary", {}))],
      ],
      "No numeric summaries available.",
    )}
  `;
}

function renderQualityScore(qualityScore) {
  return `
    ${metricGrid([
      ["Score", safeGet(qualityScore, "score", 0)],
      ["Grade", safeGet(qualityScore, "grade", "unknown")],
    ])}
    <h3>Issues</h3>
    ${list(safeArray(safeGet(qualityScore, "issues", [])), "No quality issues detected.")}
    <h3>Recommendations</h3>
    ${list(safeArray(safeGet(qualityScore, "recommendations", [])), "No quality recommendations.")}
  `;
}

function renderQualityGate(qualityGate) {
  return `
    ${metricGrid([
      ["Status", safeGet(qualityGate, "status", "unknown")],
      ["Confidence", safeGet(qualityGate, "confidence_level", "unknown")],
      ["Can Generate KPIs", safeGet(qualityGate, "can_generate_kpis", false)],
      ["Can Generate Charts", safeGet(qualityGate, "can_generate_charts", false)],
      ["Can Generate Reports", safeGet(qualityGate, "can_generate_reports", false)],
      ["Can Generate LLM Narrative", safeGet(qualityGate, "can_generate_llm_narrative", false)],
      ["Human Review Required", safeGet(qualityGate, "human_review_required", false)],
    ])}
    <h3>Reasons</h3>
    ${list(safeArray(safeGet(qualityGate, "reasons", [])), "No quality gate reasons available.")}
    <h3>Required Actions</h3>
    ${list(safeArray(safeGet(qualityGate, "required_actions", [])), "No required actions.")}
  `;
}

function renderPreparation(preparation) {
  const rows = safeArray(safeGet(preparation, "records", [])).map((record) => [
    record.order_id,
    record.region,
    record.product,
    formatMoney(record.gross_revenue),
    formatMoney(record.discount_amount),
    formatMoney(record.net_revenue),
    record.order_year,
    `Q${record.order_quarter}`,
    record.is_discounted,
    record.is_high_value_order,
    formatMoney(record.revenue_reconciliation_difference),
  ]);

  return `${metricGrid([["Prepared Records", safeGet(preparation, "total_records", 0)]])}${table(
    [
      "Order ID",
      "Region",
      "Product",
      "Gross Revenue",
      "Discount Amount",
      "Net Revenue",
      "Year",
      "Quarter",
      "Discounted",
      "High Value",
      "Reconciliation Diff",
    ],
    rows,
    "No prepared records available.",
  )}`;
}

function renderTransformationLog(transformationLog) {
  const rows = safeArray(safeGet(transformationLog, "entries", [])).map((entry) => [
    entry.step_name,
    entry.description,
    entry.records_affected,
    safeArray(entry.fields_created).join(", ") || "None",
    safeArray(entry.fields_modified).join(", ") || "None",
  ]);

  return table(
    ["Step", "Description", "Records", "Fields Created", "Fields Modified"],
    rows,
    "No transformation steps available.",
  );
}

function renderManipulationSummary(summary) {
  return `
    <h3>Monthly Revenue</h3>
    ${dataPointTable(safeArray(safeGet(summary, "monthly_revenue", [])), "Month", "Net Revenue", "No monthly revenue available.")}
    <h3>Ranked Regions</h3>
    ${dataPointTable(safeArray(safeGet(summary, "ranked_regions", [])), "Region", "Net Revenue", "No region rankings available.")}
    <h3>Ranked Products</h3>
    ${dataPointTable(safeArray(safeGet(summary, "ranked_products", [])), "Product", "Net Revenue", "No product rankings available.")}
    <h3>Ranked Sales Reps</h3>
    ${dataPointTable(safeArray(safeGet(summary, "ranked_sales_reps", [])), "Sales Rep", "Net Revenue", "No sales rep rankings available.")}
    <h3>Discount Summary By Product</h3>
    ${table(
      ["Product", "Average Discount", "Discounted Orders", "Total Orders"],
      safeArray(safeGet(summary, "discount_summary_by_product", [])).map((item) => [
        item.product,
        formatPercent(item.average_discount),
        item.discounted_order_count,
        item.total_orders,
      ]),
      "No discount summaries available.",
    )}
  `;
}

function renderTrendAnalysis(trendAnalysis) {
  const monthlyRows = safeArray(safeGet(trendAnalysis, "data", [])).map((point) => [
    point.period,
    formatMoney(point.revenue),
    point.order_count,
    point.units_sold,
    formatMoney(point.average_order_value),
    formatPercent(point.average_discount),
  ]);
  const summaryRows = [
    safeGet(trendAnalysis, "revenue_trend", {}),
    safeGet(trendAnalysis, "order_count_trend", {}),
    safeGet(trendAnalysis, "average_order_value_trend", {}),
    safeGet(trendAnalysis, "units_sold_trend", {}),
    safeGet(trendAnalysis, "average_discount_trend", {}),
  ].map((trend) => [
    safeGet(trend, "metric", "unknown"),
    safeGet(trend, "start_value", 0),
    safeGet(trend, "end_value", 0),
    safeGet(trend, "absolute_change", 0),
    formatPercentChange(safeGet(trend, "percent_change", null)),
    safeGet(trend, "direction", "unknown"),
    safeGet(trend, "interpretation", "None"),
  ]);

  return `
    ${metricGrid([
      ["Period Grain", safeGet(trendAnalysis, "period_grain", "month")],
      ["Total Periods", safeGet(trendAnalysis, "total_periods", 0)],
    ])}
    <h3>Monthly Performance</h3>
    ${table(
      ["Period", "Revenue", "Orders", "Units Sold", "Average Order Value", "Average Discount"],
      monthlyRows,
      "No monthly trend data available.",
    )}
    <h3>Trend Summaries</h3>
    ${table(
      ["Metric", "Start", "End", "Absolute Change", "Percent Change", "Direction", "Interpretation"],
      summaryRows,
      "No trend summaries available.",
    )}
    <h3>Warnings</h3>
    ${list(safeArray(safeGet(trendAnalysis, "warnings", [])), "No trend warnings.")}
  `;
}

function renderForecastAnalysis(forecastAnalysis) {
  return `
    ${metricGrid([
      ["Readiness Status", safeGet(forecastAnalysis, "readiness_status", "unknown")],
      ["Confidence Level", safeGet(forecastAnalysis, "confidence_level", "unknown")],
      ["Next Period", safeGet(forecastAnalysis, "next_period", "None") || "None"],
    ])}
    <h3>Warnings</h3>
    ${list(safeArray(safeGet(forecastAnalysis, "warnings", [])), "No forecast warnings.")}
    <h3>Recommended Actions</h3>
    ${list(safeArray(safeGet(forecastAnalysis, "recommended_actions", [])), "No forecast actions.")}
    <h3>Baseline Forecasts</h3>
    ${[
      ["Revenue", safeGet(forecastAnalysis, "revenue_forecast", null)],
      ["Order Count", safeGet(forecastAnalysis, "order_count_forecast", null)],
      ["Average Order Value", safeGet(forecastAnalysis, "average_order_value_forecast", null)],
      ["Units Sold", safeGet(forecastAnalysis, "units_sold_forecast", null)],
      ["Average Discount", safeGet(forecastAnalysis, "average_discount_forecast", null)],
    ]
      .map(([label, forecast]) => renderMetricForecast(label, forecast))
      .join("")}
  `;
}

function renderMetricForecast(label, forecast) {
  if (!forecast) {
    return `
      <article class="chart-card">
        <h3>${escapeHtml(label)}</h3>
        <p>No forecast available.</p>
      </article>
    `;
  }

  return `
    <article class="chart-card">
      <h3>${escapeHtml(label)}</h3>
      ${metricGrid([
        ["Selected Method", forecast.selected_baseline_method],
        ["Selected Forecast", forecast.selected_forecast_value],
        ["Confidence", forecast.confidence],
        ["Next Period", forecast.next_period],
      ])}
      ${table(
        ["Method", "Forecast Value", "Confidence", "Explanation"],
        [
          forecast.last_period_forecast,
          forecast.moving_average_forecast,
          forecast.trend_projection_forecast,
        ].map((point) => [
          point.method,
          point.forecast_value,
          point.confidence,
          point.explanation,
        ]),
        "No forecast methods available.",
      )}
      <h4>Metric Warnings</h4>
      ${list(safeArray(forecast.warnings), "No metric warnings.")}
    </article>
  `;
}

function renderKpis(kpis) {
  return metricGrid([
    ["Total Revenue", formatMoney(safeGet(kpis, "total_revenue", 0))],
    ["Total Orders", safeGet(kpis, "total_orders", 0)],
    ["Units Sold", safeGet(kpis, "total_units_sold", 0)],
    ["Average Order Value", formatMoney(safeGet(kpis, "average_order_value", 0))],
  ]);
}

function renderSecurity(security) {
  const flaggedFields = safeArray(safeGet(security, "flagged_fields", [])).length
    ? safeGet(security, "flagged_fields", []).join(", ")
    : "None";

  return metricGrid([
    ["Prompt Injection", safeGet(security, "prompt_injection_detected", false)],
    ["Human Review", safeGet(security, "human_review_required", false)],
    ["Flagged Fields", flaggedFields],
  ]);
}

function renderAnomalies(anomalies) {
  const rows = safeArray(safeGet(anomalies, "anomalies", [])).map((anomaly) => [
    anomaly.anomaly_type,
    anomaly.severity,
    anomaly.method || "rule",
    anomaly.order_id,
    anomaly.field,
    anomaly.value,
    anomaly.threshold ?? "None",
    anomaly.comparison || "None",
    anomaly.message,
  ]);

  return `${metricGrid([["Total Anomalies", safeGet(anomalies, "total_anomalies", 0)]])}${table(
    ["Type", "Severity", "Method", "Order ID", "Field", "Value", "Threshold", "Comparison", "Message"],
    rows,
    "No anomalies detected.",
  )}`;
}

function renderInsights(insights) {
  const insightItems = safeArray(safeGet(insights, "insights", [])).length
    ? insights.insights
        .map(
          (insight) => `
            <li>
              <strong>${escapeHtml(insight.title)}</strong>
              <span>(${escapeHtml(insight.severity)})</span>
              <p>${escapeHtml(insight.message)}</p>
            </li>
          `,
        )
        .join("")
    : "<li>No executive insights generated.</li>";

  const actions = safeArray(safeGet(insights, "recommended_actions", [])).length
    ? insights.recommended_actions.map((action) => `<li>${escapeHtml(action)}</li>`).join("")
    : "<li>No recommended actions.</li>";

  return `
    <p>${escapeHtml(safeGet(insights, "summary", "No executive summary available."))}</p>
    <ul>${insightItems}</ul>
    <h3>Recommended Actions</h3>
    <ul>${actions}</ul>
  `;
}

function renderWorkflowImprovements(plan) {
  const rows = safeArray(safeGet(plan, "workflows", [])).map((workflow) => [
    workflow.workflow_name,
    workflow.current_issue,
    workflow.proposed_change,
    workflow.expected_benefit,
    workflow.owner_role,
    workflow.follow_up_metric,
    safeArray(workflow.related_recommendation_ids).join(", ") || "None",
  ]);

  return table(
    [
      "Workflow",
      "Current Issue",
      "Proposed Change",
      "Expected Benefit",
      "Owner Role",
      "Follow-up Metric",
      "Related Recommendations",
    ],
    rows,
    "No workflow improvements generated.",
  );
}

function renderAuditEvents(events) {
  const rows = safeArray(events).map((event) => [event.event_type, event.message]);
  return table(["Event Type", "Message"], rows, "No audit events available.");
}

function panel(title, body, className = "") {
  return `
    <section class="panel ${escapeHtml(className)}">
      <h2>${escapeHtml(title)}</h2>
      ${body}
    </section>
  `;
}

function technicalPanel(title, body) {
  return `
    <details class="technical-section">
      <summary>${escapeHtml(title)}</summary>
      <div class="technical-section-body">${body}</div>
    </details>
  `;
}

function metricGrid(items) {
  return `
    <div class="summary-grid">
      ${items
        .map(
          ([label, value]) => `
            <div class="metric">
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(formatValue(value))}</strong>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function table(headers, rows, emptyMessage) {
  if (!rows.length) {
    return `<p class="empty-state">${escapeHtml(emptyMessage)}</p>`;
  }

  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>${row.map((cell) => `<td>${escapeHtml(formatValue(cell))}</td>`).join("")}</tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function objectTable(values, keyLabel, valueLabel, emptyMessage) {
  const rows = Object.entries(values || {}).sort(([left], [right]) =>
    left.localeCompare(right),
  );
  return table([keyLabel, valueLabel], rows, emptyMessage);
}

function dataPointTable(points, labelHeader, valueHeader, emptyMessage) {
  return table(
    [labelHeader, valueHeader],
    safeArray(points).map((point) => [point.label, point.value]),
    emptyMessage,
  );
}

function renderBarPreview(chart) {
  if (!safeArray(chart.data).length || chart.chart_type === "line") {
    return "";
  }

  const maxValue = Math.max(...chart.data.map((point) => Number(point.value)));
  if (maxValue <= 0) {
    return "";
  }

  return `
    <div class="bar-list" aria-label="${escapeHtml(chart.title)} preview">
      ${chart.data
        .map((point) => {
          const width = Math.max(2, (Number(point.value) / maxValue) * 100);
          return `
            <div class="bar-row">
              <span>${escapeHtml(point.label)}</span>
              <div class="bar-track">
                <div class="bar-fill" style="width: ${width.toFixed(2)}%"></div>
              </div>
              <strong>${escapeHtml(formatValue(point.value))}</strong>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function badge(value, className) {
  return `<span class="${escapeHtml(className)} badge-${statusClass(value)}">${escapeHtml(formatValue(value))}</span>`;
}

function statusClass(value) {
  const normalized = String(value).toLowerCase().replaceAll("_", "-");
  if (["pass", "ready", "low", "info", "excellent"].includes(normalized)) {
    return "pass";
  }
  if (["warning", "limited", "medium", "review", "fair"].includes(normalized)) {
    return "warning";
  }
  if (["blocked", "not-ready", "high", "poor"].includes(normalized)) {
    return "blocked";
  }
  return "neutral";
}

function formatForecastValue(forecast, isMoney) {
  if (!forecast) {
    return "None";
  }

  const value = forecast.selected_forecast_value;
  return isMoney ? formatMoney(value) : formatNumber(value);
}

function formatInlineList(items) {
  return safeArray(items).length ? items.join(", ") : "None";
}

function list(items, emptyMessage) {
  if (!safeArray(items).length) {
    return `<p class="empty-state">${escapeHtml(emptyMessage)}</p>`;
  }

  return `
    <ul>
      ${items.map((item) => `<li>${escapeHtml(formatValue(item))}</li>`).join("")}
    </ul>
  `;
}

function numericSummaryCells(summary) {
  return [
    formatNumber(safeGet(summary, "minimum", 0)),
    formatNumber(safeGet(summary, "maximum", 0)),
    formatNumber(safeGet(summary, "mean", 0)),
    formatNumber(safeGet(summary, "median", 0)),
    formatNumber(safeGet(summary, "standard_deviation", 0)),
  ];
}

function formatDateRange(profile) {
  if (!safeGet(profile, "date_start", null) || !safeGet(profile, "date_end", null)) {
    return "None";
  }

  return `${profile.date_start} to ${profile.date_end}`;
}

function formatMoney(value) {
  return `$${Number(value || 0).toFixed(2)}`;
}

function formatPercent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function formatPercentChange(value) {
  if (value === null || value === undefined) {
    return "None";
  }

  return `${Number(value).toFixed(2)}%`;
}

function formatNumber(value) {
  return Number(value || 0).toFixed(2);
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "None";
  }

  return String(value);
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function safeGet(source, path, fallback) {
  if (source === null || source === undefined) {
    return fallback;
  }

  return path.split(".").reduce((current, key) => {
    if (current === null || current === undefined) {
      return undefined;
    }
    return current[key];
  }, source) ?? fallback;
}

function escapeHtml(value) {
  return formatValue(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
