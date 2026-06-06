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
    renderSourceMetadata(data.source_metadata),
    renderValidation(data.validation),
    renderDataProfile(data.data_profile),
    renderQualityScore(data.quality_score),
    renderQualityGate(data.quality_gate),
    renderKpis(data.kpis),
    renderPreparation(data.preparation),
    renderTransformationLog(data.transformation_log),
    renderManipulationSummary(data.manipulation_summary),
    renderSecurity(data.security),
    renderAnomalies(data.anomalies),
    renderCharts(data.charts),
    renderInsights(data.insights),
    renderRecommendations(data.recommendation_plan),
    renderWorkflowImprovements(data.workflow_improvement_plan),
    renderAuditEvents(data.audit_events),
  ].join("");
  resultsEl.hidden = false;
}

function renderSourceMetadata(sourceMetadata) {
  return panel(
    "Source Metadata",
    metricGrid([
      ["Source Type", sourceMetadata.source_type],
      ["File Name", sourceMetadata.file_name],
      ["File Size", `${sourceMetadata.file_size_bytes} bytes`],
      ["Collection Method", sourceMetadata.collection_method],
      ["Record Count", sourceMetadata.record_count],
      ["Notes", sourceMetadata.notes || "None"],
    ]),
  );
}

function renderValidation(validation) {
  return panel(
    "Validation",
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

function renderQualityGate(qualityGate) {
  return panel(
    "Quality Gate",
    `
      ${metricGrid([
        ["Status", qualityGate.status],
        ["Confidence", qualityGate.confidence_level],
        ["Can Generate KPIs", qualityGate.can_generate_kpis],
        ["Can Generate Charts", qualityGate.can_generate_charts],
        ["Can Generate Reports", qualityGate.can_generate_reports],
        ["Can Generate LLM Narrative", qualityGate.can_generate_llm_narrative],
        ["Human Review Required", qualityGate.human_review_required],
      ])}
      <h3>Reasons</h3>
      ${list(qualityGate.reasons, "No quality gate reasons available.")}
      <h3>Required Actions</h3>
      ${list(qualityGate.required_actions, "No required actions.")}
    `,
  );
}

function renderPreparation(preparation) {
  const rows = preparation.records.map((record) => [
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

  return panel(
    "Data Preparation",
    `${metricGrid([["Prepared Records", preparation.total_records]])}${table(
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
    )}`,
  );
}

function renderTransformationLog(transformationLog) {
  const rows = transformationLog.entries.map((entry) => [
    entry.step_name,
    entry.description,
    entry.records_affected,
    entry.fields_created.join(", ") || "None",
    entry.fields_modified.join(", ") || "None",
  ]);

  return panel(
    "Transformation Lineage",
    table(
      ["Step", "Description", "Records", "Fields Created", "Fields Modified"],
      rows,
      "No transformation steps available.",
    ),
  );
}

function renderManipulationSummary(summary) {
  return panel(
    "Manipulation Summary",
    `
      <h3>Monthly Revenue</h3>
      ${dataPointTable(summary.monthly_revenue, "Month", "Net Revenue", "No monthly revenue available.")}
      <h3>Ranked Regions</h3>
      ${dataPointTable(summary.ranked_regions, "Region", "Net Revenue", "No region rankings available.")}
      <h3>Ranked Products</h3>
      ${dataPointTable(summary.ranked_products, "Product", "Net Revenue", "No product rankings available.")}
      <h3>Ranked Sales Reps</h3>
      ${dataPointTable(summary.ranked_sales_reps, "Sales Rep", "Net Revenue", "No sales rep rankings available.")}
      <h3>Discount Summary By Product</h3>
      ${table(
        ["Product", "Average Discount", "Discounted Orders", "Total Orders"],
        summary.discount_summary_by_product.map((item) => [
          item.product,
          formatPercent(item.average_discount),
          item.discounted_order_count,
          item.total_orders,
        ]),
        "No discount summaries available.",
      )}
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
    "Security",
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
    anomaly.method || "rule",
    anomaly.order_id,
    anomaly.field,
    anomaly.value,
    anomaly.threshold ?? "None",
    anomaly.comparison || "None",
    anomaly.message,
  ]);

  return panel(
    "Anomalies",
    `${metricGrid([["Total Anomalies", anomalies.total_anomalies]])}${table(
      [
        "Type",
        "Severity",
        "Method",
        "Order ID",
        "Field",
        "Value",
        "Threshold",
        "Comparison",
        "Message",
      ],
      rows,
      "No anomalies detected.",
    )}`,
  );
}

function renderCharts(charts) {
  const chartSections = charts.charts
    .map(
      (chart) => `
        <article class="chart-card">
          <h3>${escapeHtml(chart.title)}</h3>
          <p><strong>Business question:</strong> ${escapeHtml(chart.business_question || "None")}</p>
          <p><strong>Interpretation:</strong> ${escapeHtml(chart.interpretation || "None")}</p>
          <p><strong>Related insight IDs:</strong> ${escapeHtml(formatInlineList(chart.related_insight_ids))}</p>
          <h4>Recommended Actions</h4>
          ${list(chart.recommended_actions, "No chart-specific recommended actions.")}
          ${renderBarPreview(chart)}
          <h4>Chart Data</h4>
        ${table(
          [
            chart.x_axis,
            chart.y_axis,
            "secondary_value",
          ],
          chart.data.map((point) => [
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

  return panel("Visual Analytics", chartSections || "No charts available.");
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

function renderRecommendations(plan) {
  const items = plan.recommendations.length
    ? plan.recommendations
        .map(
          (recommendation) => `
            <article class="chart-card">
              <h3>${escapeHtml(recommendation.title)}</h3>
              ${metricGrid([
                ["Priority", recommendation.priority],
                ["Business Area", recommendation.business_area],
                ["Workflow Stage", recommendation.workflow_stage],
                ["Owner Role", recommendation.owner_role],
                ["Difficulty", recommendation.implementation_difficulty],
                ["Follow-up Metric", recommendation.follow_up_metric],
              ])}
              <p><strong>Problem:</strong> ${escapeHtml(recommendation.problem)}</p>
              <p><strong>Recommended Action:</strong> ${escapeHtml(recommendation.recommended_action)}</p>
              <p><strong>Expected Impact:</strong> ${escapeHtml(recommendation.expected_impact)}</p>
              <p><strong>Evidence:</strong> ${escapeHtml(formatObject(recommendation.evidence))}</p>
              <p><strong>Related insight IDs:</strong> ${escapeHtml(formatInlineList(recommendation.related_insight_ids))}</p>
              <p><strong>Related chart IDs:</strong> ${escapeHtml(formatInlineList(recommendation.related_chart_ids))}</p>
            </article>
          `,
        )
        .join("")
    : "<p>No business recommendations generated.</p>";

  return panel("Business Recommendations", items);
}

function renderWorkflowImprovements(plan) {
  const rows = plan.workflows.map((workflow) => [
    workflow.workflow_name,
    workflow.current_issue,
    workflow.proposed_change,
    workflow.expected_benefit,
    workflow.owner_role,
    workflow.follow_up_metric,
    workflow.related_recommendation_ids.join(", ") || "None",
  ]);

  return panel(
    "Workflow Improvements",
    table(
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
    ),
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

function dataPointTable(points, labelHeader, valueHeader, emptyMessage) {
  return table(
    [labelHeader, valueHeader],
    points.map((point) => [point.label, point.value]),
    emptyMessage,
  );
}

function renderBarPreview(chart) {
  if (!chart.data.length || chart.chart_type === "line") {
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
              <strong>${escapeHtml(String(point.value))}</strong>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function formatInlineList(items) {
  return items.length ? items.join(", ") : "None";
}

function formatObject(value) {
  const entries = Object.entries(value);
  if (!entries.length) {
    return "None";
  }

  return entries.map(([key, item]) => `${key}=${item}`).join(", ");
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

function formatPercent(value) {
  return `${(Number(value) * 100).toFixed(1)}%`;
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
