# Application Overview

## What InsightOps-AI Is

InsightOps-AI is a deterministic sales analytics automation application. It accepts sales CSV data, validates and profiles the dataset, computes sales KPIs, summarizes historical monthly trends, detects anomalies, generates visual analytics context, and turns analytical findings into business recommendations and workflow improvement plans.

The application is designed as a governed analytics API with a lightweight static dashboard and module-level report artifact generation. It emphasizes explainability, auditability, and deterministic decision-support before any optional narrative generation.

## Business Problem

Sales teams often rely on spreadsheet exports that contain missing fields, invalid rows, duplicate identifiers, inconsistent data quality, and unexplained outliers. Those issues can make executive reporting unreliable if they are not surfaced before KPI review.

InsightOps-AI helps convert raw sales CSVs into structured, audit-ready analytics outputs. It does not silently treat flawed data as high-confidence evidence; it reports quality issues, confidence, anomalies, and recommended remediation steps.

## Intended Users

- Sales operations teams reviewing CSV exports.
- Revenue operations teams monitoring data quality and process issues.
- Finance analysts checking anomalies before reporting.
- Sales leaders reviewing KPIs, risks, and recommendations.
- Technical reviewers evaluating deterministic analytics and API design.

## Real-World Use Cases

- Validate uploaded sales data before KPI reporting.
- Separate valid records from invalid records without crashing ingestion.
- Detect missing required fields, duplicate order IDs, suspicious source text, and anomalous transactions.
- Produce executive-ready summaries with evidence and audit events.
- Identify workflow improvements such as required-field validation, discount approval review, and anomaly review processes.

## Core Capabilities

- CSV ingestion and row-level validation.
- Source metadata capture for sample and uploaded datasets.
- Data profiling with row counts, date range, unique entity counts, missing fields, duplicates, and numeric summaries.
- Deterministic quality scoring and quality gate decisions.
- Data preparation with derived analytical fields.
- Transformation lineage for preparation steps.
- Sales KPI computation.
- Monthly trend analysis for revenue, order count, units sold, average order value, and average discount.
- Rule-based and IQR-based statistical anomaly detection.
- Prompt-injection style text detection and human-review flags.
- Visual analytics objects with business questions, interpretations, related insight IDs, and recommended actions.
- Deterministic executive insights.
- Business recommendation and workflow improvement plans.
- Audit events for major pipeline stages.
- Markdown, PDF, and PNG artifact generation as module-level capabilities.

## Analytics Workflow

```text
CSV sample or upload
  -> source metadata
  -> validation
  -> data profile
  -> quality score
  -> security scan
  -> quality gate
  -> preparation and transformation lineage
  -> manipulation summaries
  -> monthly trend analysis
  -> KPIs
  -> anomaly detection
  -> executive insights
  -> visual analytics
  -> business recommendations
  -> workflow improvements
  -> audit events
  -> typed API response
```

Both `GET /analysis/sample` and `POST /analysis/upload` return the same typed response contract.

## Data Quality, Governance, And Auditability

InsightOps-AI treats data quality as part of the analytics result, not as an afterthought. Validation reports explain row-level failures, data profiles summarize dataset credibility, and the quality gate assigns a `pass`, `warning`, or `blocked` status with an analysis confidence level.

The quality gate also controls whether LLM narrative generation is eligible. Security findings, prompt-injection indicators, human-review flags, and low-confidence data can block optional narrative generation while deterministic fallback remains available.

Audit events record major pipeline stages so outputs can be traced back to validation, profiling, quality scoring, security scanning, trend analysis, KPI computation, anomaly detection, visual analytics, recommendations, and workflow improvements.

## Visual Analytics And Recommendations

Visual analytics are treated as evidence objects rather than simple chart data. Trend charts show historical monthly movement for revenue, order count, average order value, and average discount. They do not perform forecasting. Each chart includes:

- a business question
- a deterministic interpretation
- related insight IDs
- recommended actions
- chart-ready data points

The recommendation engine converts findings into structured business actions. Each recommendation includes evidence, priority, owner role, expected impact, workflow stage, implementation difficulty, follow-up metric, and links to related insights or charts.

Workflow improvements translate recommendations into process changes, such as improving data intake, reviewing discount approval, or strengthening revenue audit steps.

## Stakeholder-Facing Outputs

- Typed JSON analysis responses from the FastAPI API.
- Lightweight static dashboard summaries and tables.
- Backend PNG chart artifacts from chart-ready data.
- Markdown executive report artifacts.
- PDF executive report artifacts.
- Deterministic narrative fallback output.

Artifact generation currently exists as module-level backend functionality. The application does not yet expose authenticated artifact download endpoints.

## Current Limitations

- No production authentication or multi-user authorization.
- No database persistence for analysis runs or audit events.
- No forecasting, regression, or real ML models.
- No production frontend framework or interactive charting library.
- No authenticated report or chart download API.
- Optional OpenRouter narrative writing is guarded and does not control analytics decisions.

## Future Roadmap

- Add authenticated artifact download endpoints.
- Persist analysis runs and audit events.
- Add user/project scoping and access control.
- Add production frontend chart rendering if dashboard scope expands.
- Add stronger source-file scanning and operational monitoring.
- Continue improving deterministic statistical analytics before adding more presentation features.
