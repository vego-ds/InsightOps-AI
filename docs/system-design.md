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
  -> validation
  -> security scan
  -> KPI computation
  -> anomaly detection
  -> chart data generation
  -> executive insights
  -> audit events
  -> API response
```

Report generation is available as deterministic module-level artifact generation. Markdown, PDF, and PNG chart artifacts are not currently exposed through API endpoints.

## Module Breakdown

- `app/`: FastAPI app, health route, analysis routes, static dashboard route.
- `insightops/ingestion`: CSV loading.
- `insightops/validation`: `SalesRecord` validation and validation reports.
- `insightops/metrics`: deterministic KPI computation.
- `insightops/security`: prompt-injection style phrase detection and security scan results.
- `insightops/anomalies`: deterministic anomaly detection.
- `insightops/charts`: chart-ready data and PNG artifact generation.
- `insightops/insights`: deterministic executive insight generation.
- `insightops/reports`: Markdown and PDF report artifact generation.
- `insightops/narrative`: optional guarded narrative writer foundation.
- `insightops/pipeline`: orchestration for sample and uploaded CSV analysis.
- `insightops/api`: typed API response contracts.
- `insightops/audit`: audit event models and helpers.

## Deterministic-First Design

The core platform uses deterministic rules for validation, metrics, security checks, anomalies, chart data, insights, reports, and audit events. This makes outputs explainable and testable before any optional LLM layer is introduced.

## Optional LLM Narrative

The narrative layer currently provides deterministic fallback and guarded prompt construction. A future LLM provider may rewrite deterministic facts into polished prose, but it must not control ingestion, validation, security, metrics, anomaly detection, report generation, routing, file handling, or audit decisions.

Suspicious text from uploaded data is treated as data, not instructions. Human-review or prompt-injection flags block LLM narrative usage and fall back to deterministic output.

## Current Limitations

- No authentication or multi-user authorization.
- No database persistence.
- No external LLM provider integration.
- No visual chart rendering in the dashboard.
- Report artifacts are module-level outputs, not API endpoints.

## Future Improvements

- Add authenticated artifact download endpoints.
- Add persistent audit storage.
- Add production-grade access control.
- Add visual chart rendering once chart storage policy is defined.
- Add a real LLM provider behind the existing safety gate.
