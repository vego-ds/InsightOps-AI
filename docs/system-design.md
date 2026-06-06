# System Design

## Overview

InsightOps-AI is a production-style sales analytics automation platform. It accepts sales CSV data, validates every row, computes deterministic analytics, detects risks and anomalies, prepares reporting artifacts, and exposes the result through a typed FastAPI API and a lightweight static dashboard.

## Architecture Summary

The system is intentionally layered:

- `app/` owns API routing and static dashboard serving.
- `insightops/pipeline` orchestrates analysis.
- Domain packages own deterministic business logic.
- `insightops/api` defines typed response contracts.
- Artifact modules generate PNG, Markdown, and PDF outputs outside the API response.

`app/main.py` is intentionally thin so routing does not become business logic. That keeps the API easy to review, test, and extend.

## Pipeline Flow

```text
CSV upload or sample data
  -> source metadata collection
  -> validation
  -> data profiling and quality scoring
  -> security scan
  -> quality gate and confidence assignment
  -> data preparation and transformation lineage
  -> manipulation summaries
  -> KPI computation
  -> anomaly detection
  -> executive insights
  -> visual analytics
  -> recommendations and workflow improvements
  -> audit events
  -> API response
```

The pipeline explicitly covers collection, validation, profiling, quality
scoring, governance, preparation, manipulation, visual analytics, insights,
reporting, and audit evidence. Data profiling, quality scoring, and the security
scan feed the quality gate, which assigns confidence and controls LLM narrative
eligibility. Preparation and manipulation then create analysis-ready records and
summaries before downstream KPI, anomaly, insight, chart, and recommendation
generation.

Visual analytics sits between manipulation summaries and executive
insights/reporting. Charts are evidence objects, not just display objects: each
chart includes a business question, deterministic interpretation, related
insight IDs, recommended actions, and chart-ready data points.

The recommendation engine sits after insights and visual analytics. It converts
findings into business recommendations with evidence, owners, expected impact,
follow-up metrics, and related insight/chart IDs. The workflow improvement plan
maps recommendations into operational process changes.

Report generation is available as deterministic module-level artifact generation. Markdown, PDF, and PNG chart artifacts are not currently exposed through API endpoints.

## Module Breakdown

- `app/`: FastAPI app, health route, analysis routes, static dashboard route.
- `insightops/ingestion`: CSV loading.
- `insightops/validation`: `SalesRecord` validation and validation reports.
- `insightops/sources`: dataset source metadata.
- `insightops/profiling`: data profiles and quality scores.
- `insightops/governance`: data quality gate and analysis confidence decisions.
- `insightops/preparation`: cleaning, derived fields, and manipulation summaries.
- `insightops/lineage`: transformation lineage models.
- `insightops/metrics`: deterministic KPI computation.
- `insightops/security`: prompt-injection style phrase detection and security scan results.
- `insightops/anomalies`: deterministic rule-based and statistical anomaly detection.
- `insightops/statistics`: transparent robust statistics and IQR outlier helpers.
- `insightops/charts`: visual analytics chart data, interpretation helpers, and PNG artifact generation.
- `insightops/insights`: deterministic executive insight generation.
- `insightops/recommendations`: business recommendation and workflow improvement plans.
- `insightops/reports`: Markdown and PDF report artifact generation.
- `insightops/narrative`: optional guarded narrative writer foundation.
- `insightops/pipeline`: orchestration for sample and uploaded CSV analysis.
- `insightops/api`: typed API response contracts.
- `insightops/audit`: audit event models and helpers.

## Deterministic-First Design

The core platform uses deterministic rules for collection metadata, validation, profiling, quality scoring, governance gates, preparation, manipulation, metrics, security checks, anomalies, chart data, insights, reports, and audit events. Anomaly detection combines fixed business rules with transparent IQR-based statistical methods; no ML is used, and thresholds remain auditable. This makes outputs explainable and testable before any optional LLM layer is introduced.

## Optional LLM Narrative

The narrative layer provides deterministic fallback, guarded prompt construction, and optional provider integration for narrative writing. An LLM provider may rewrite deterministic facts into polished prose, but it must not control ingestion, validation, profiling, quality scoring, security, metrics, anomaly detection, report generation, routing, file handling, or audit decisions.

Suspicious text from uploaded data is treated as data, not instructions. Human-review or prompt-injection flags block LLM narrative usage and fall back to deterministic output.

## Current Limitations

- No authentication or multi-user authorization.
- No database persistence.
- No LLM-generated pipeline decisions.
- No visual chart rendering in the dashboard.
- Report artifacts are module-level outputs, not API endpoints.

## Future Improvements

- Add authenticated artifact download endpoints.
- Add persistent audit storage.
- Add production-grade access control.
- Add visual chart rendering once chart storage policy is defined.
- Add a real LLM provider behind the existing safety gate.
