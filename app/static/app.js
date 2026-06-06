const sampleButton = document.querySelector("#sample-button");
const uploadForm = document.querySelector("#upload-form");
const fileInput = document.querySelector("#csv-file");
const statusEl = document.querySelector("#status");
const errorEl = document.querySelector("#error");
const resultsEl = document.querySelector("#results");

sampleButton.addEventListener("click", async () => {
  await runAnalysis(() => fetch("/analysis/sample"));
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

async function runAnalysis(requestFactory) {
  setLoading(true);
  hideError();
  resultsEl.hidden = true;

  try {
    const response = await requestFactory();
    const payload = await response.json();

    if (!response.ok) {
      showError(payload.detail || "Analysis request failed.");
      return;
    }

    renderResults(payload);
  } catch (error) {
    showError(`Analysis request failed: ${error.message}`);
  } finally {
    setLoading(false);
  }
}

function setLoading(isLoading) {
  sampleButton.disabled = isLoading;
  uploadForm.querySelector("button").disabled = isLoading;
  statusEl.textContent = isLoading ? "Running deterministic analysis..." : "";
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function hideError() {
  errorEl.hidden = true;
  errorEl.textContent = "";
}

function renderResults(data) {
  resultsEl.innerHTML = [
    renderValidation(data.validation),
    renderDataProfile(data.data_profile),
    renderQualityScore(data.quality_score),
    renderKpis(data.kpis),
    renderSecurity(data.security),
    renderAnomalies(data.anomalies),
    renderCharts(data.charts),
    renderInsights(data.insights),
    renderAuditEvents(data.audit_events),
  ].join("");
  resultsEl.hidden = false;
}

function renderValidation(validation) {
  return panel(
    "Validation Summary",
    metricGrid([
      ["Total Rows", validation.total_rows],
      ["Valid Rows", validation.valid_rows],
      ["Invalid Rows", validation.invalid_rows],
      ["Errors", validation.errors.length],
    ]),
  );
}

function renderDataProfile(profile) {
  return panel(
    "Data Profile",
    `
      ${metricGrid([
        ["Date Range", formatDateRange(profile)],
        ["Unique Customers", profile.unique_customers],
        ["Unique Regions", profile.unique_regions],
        ["Unique Products", profile.unique_products],
        ["Unique Sales Reps", profile.unique_sales_reps],
        ["Duplicate Order IDs", profile.duplicate_order_ids],
      ])}
      <h3>Missing Field Counts</h3>
      ${objectTable(profile.missing_field_counts, "Field", "Count", "No missing fields detected.")}
      <h3>Numeric Summaries</h3>
      ${table(
        ["Metric", "Minimum", "Maximum", "Mean", "Median", "Std Dev"],
        [
          ["Revenue", ...numericSummaryCells(profile.revenue_summary)],
          ["Quantity", ...numericSummaryCells(profile.quantity_summary)],
          ["Discount", ...numericSummaryCells(profile.discount_summary)],
          ["Unit Price", ...numericSummaryCells(profile.unit_price_summary)],
        ],
        "No numeric summaries available.",
      )}
    `,
  );
}

function renderQualityScore(qualityScore) {
  return panel(
    "Quality Score",
    `
      ${metricGrid([
        ["Score", qualityScore.score],
        ["Grade", qualityScore.grade],
      ])}
      <h3>Issues</h3>
      ${list(qualityScore.issues, "No quality issues detected.")}
      <h3>Recommendations</h3>
      ${list(qualityScore.recommendations, "No quality recommendations.")}
    `,
  );
}

function renderKpis(kpis) {
  return panel(
    "KPI Summary",
    metricGrid([
      ["Total Revenue", formatMoney(kpis.total_revenue)],
      ["Total Orders", kpis.total_orders],
      ["Units Sold", kpis.total_units_sold],
      ["Average Order Value", formatMoney(kpis.average_order_value)],
    ]),
  );
}

function renderSecurity(security) {
  const flaggedFields = security.flagged_fields.length
    ? security.flagged_fields.join(", ")
    : "None";

  return panel(
    "Security Summary",
    metricGrid([
      ["Prompt Injection", security.prompt_injection_detected],
      ["Human Review", security.human_review_required],
      ["Flagged Fields", flaggedFields],
    ]),
  );
}

function renderAnomalies(anomalies) {
  const rows = anomalies.anomalies.map((anomaly) => [
    anomaly.anomaly_type,
    anomaly.severity,
    anomaly.order_id,
    anomaly.field,
    anomaly.value,
    anomaly.message,
  ]);

  return panel(
    "Anomaly Summary",
    `${metricGrid([["Total Anomalies", anomalies.total_anomalies]])}${table(
      ["Type", "Severity", "Order ID", "Field", "Value", "Message"],
      rows,
      "No anomalies detected.",
    )}`,
  );
}

function renderCharts(charts) {
  const chartSections = charts.charts
    .map(
      (chart) => `
        <h3>${escapeHtml(chart.title)}</h3>
        ${table(
          [chart.x_axis, chart.y_axis],
          chart.data.map((point) => [point.label, point.value]),
          "No chart data available.",
        )}
      `,
    )
    .join("");

  return panel("Chart Data Summary", chartSections || "No charts available.");
}

function renderInsights(insights) {
  const insightItems = insights.insights.length
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

  const actions = insights.recommended_actions.length
    ? insights.recommended_actions.map((action) => `<li>${escapeHtml(action)}</li>`).join("")
    : "<li>No recommended actions.</li>";

  return panel(
    "Executive Insights",
    `
      <p>${escapeHtml(insights.summary)}</p>
      <ul>${insightItems}</ul>
      <h3>Recommended Actions</h3>
      <ul>${actions}</ul>
    `,
  );
}

function renderAuditEvents(events) {
  const rows = events.map((event) => [event.event_type, event.message]);
  return panel(
    "Audit Events",
    table(["Event Type", "Message"], rows, "No audit events available."),
  );
}

function panel(title, body) {
  return `
    <section class="panel">
      <h2>${escapeHtml(title)}</h2>
      ${body}
    </section>
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
              <strong>${escapeHtml(String(value))}</strong>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function table(headers, rows, emptyMessage) {
  if (!rows.length) {
    return `<p>${escapeHtml(emptyMessage)}</p>`;
  }

  return `
    <table>
      <thead>
        <tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr>${row.map((cell) => `<td>${escapeHtml(String(cell))}</td>`).join("")}</tr>
            `,
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function objectTable(values, keyLabel, valueLabel, emptyMessage) {
  const rows = Object.entries(values).sort(([left], [right]) =>
    left.localeCompare(right),
  );
  return table([keyLabel, valueLabel], rows, emptyMessage);
}

function list(items, emptyMessage) {
  if (!items.length) {
    return `<p>${escapeHtml(emptyMessage)}</p>`;
  }

  return `
    <ul>
      ${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
    </ul>
  `;
}

function numericSummaryCells(summary) {
  return [
    formatNumber(summary.minimum),
    formatNumber(summary.maximum),
    formatNumber(summary.mean),
    formatNumber(summary.median),
    formatNumber(summary.standard_deviation),
  ];
}

function formatDateRange(profile) {
  if (!profile.date_start || !profile.date_end) {
    return "None";
  }

  return `${profile.date_start} to ${profile.date_end}`;
}

function formatMoney(value) {
  return `$${Number(value).toFixed(2)}`;
}

function formatNumber(value) {
  return Number(value).toFixed(2);
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
