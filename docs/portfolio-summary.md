# Portfolio Summary

## Project Name

InsightOps-AI

## Summary

InsightOps-AI is a production-style sales analytics automation platform that collects source metadata, validates uploaded sales CSVs, prepares analysis-ready records, computes KPIs, detects security risks and anomalies, generates deterministic executive insights, and produces audit-ready API responses and report artifacts.

## Business Problem

Sales leaders need trustworthy analysis from messy CSV data. This project demonstrates how raw sales data can be safely validated, transformed, summarized, and packaged for executive review without relying on opaque AI behavior for core business logic.

## Technical Capabilities

- FastAPI API with typed response contracts.
- CSV ingestion and row validation.
- Source metadata, data preparation, transformation lineage, and manipulation summaries.
- Data profiling and deterministic quality scoring.
- KPI computation.
- Security guardrails for prompt-injection style text.
- Anomaly detection.
- Chart-ready data and PNG artifact generation.
- Markdown and PDF executive report artifacts.
- Optional guarded narrative writer foundation.
- Static dashboard demo.

## Architecture Highlights

- Thin FastAPI routing layer.
- Deterministic pipeline orchestration.
- Pydantic models for contracts.
- Separate artifact generation modules.
- Runtime configuration and Docker deployment support.

## Security And Governance Highlights

- CSV-only upload guardrails.
- Upload size limit.
- Human-review flags.
- Prompt-injection detection.
- Audit events.
- LLM layer disabled by default and blocked when suspicious data is detected.

## Testing And CI Highlights

- Pytest suite covers API, pipeline, domain logic, artifacts, narrative safety, and dependency verification.
- Ruff linting.
- GitHub Actions CI on Python 3.12.

## Deployment Readiness Highlights

- Dockerfile.
- Deployment guide.
- Runtime environment variables.
- Health check endpoint.
- Static dashboard route.

## Why This Is Portfolio-Worthy

This project shows backend engineering judgment: deterministic business logic, typed contracts, safety boundaries, testing, CI, deployment readiness, and a guarded approach to AI rather than bolting an LLM onto the core workflow.

## Resume Bullet Points

- Built a FastAPI sales analytics platform that validates CSV data, tracks source metadata and lineage, computes KPIs, detects anomalies, and returns typed audit-ready analysis responses.
- Implemented prompt-injection guardrails and deterministic fallback for optional narrative generation.
- Added CI, Docker deployment support, static dashboard demo, and Markdown/PDF report artifact generation.

## LinkedIn/GitHub Description

InsightOps-AI is a production-style sales analytics automation API with deterministic data collection metadata, validation, preparation, profiling, KPI computation, security guardrails, anomaly detection, executive insights, report artifacts, CI, Docker support, and a lightweight static dashboard.
