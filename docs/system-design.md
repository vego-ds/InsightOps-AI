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
  -> monthly trend analysis
  -> forecast readiness and baseline forecasts
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
summaries. Trend analysis adds deterministic monthly performance movement for
revenue, order count, units sold, average order value, and average discount
before downstream forecast, KPI, anomaly, insight, chart, and recommendation
generation. Forecast analysis uses readiness checks plus last-period,
moving-average, and simple trend-projection baselines. It is transparent
business planning logic, not ML, regression, or statistical model fitting.

Visual analytics sits between manipulation summaries and executive
insights/reporting. Charts are evidence objects, not just display objects: each
chart includes a business question, deterministic interpretation, related
insight IDs, recommended actions, and chart-ready data points.

The recommendation engine sits after insights and visual analytics. It converts
findings into business recommendations with evidence, owners, expected impact,
follow-up metrics, and related insight/chart IDs. The workflow improvement plan
maps recommendations into operational process changes.

Report generation is available as deterministic module-level artifact generation. Markdown and PDF report artifacts are exposed through dedicated report export API endpoints, while PNG chart artifacts remain a backend capability.

## Module Breakdown

- `app/`: FastAPI app, health route, analysis routes, static dashboard route.
- `insightops/ingestion`: CSV loading.
- `insightops/validation`: `SalesRecord` validation and validation reports.
- `insightops/sources`: dataset source metadata.
- `insightops/profiling`: data profiles and quality scores.
- `insightops/governance`: data quality gate and analysis confidence decisions.
- `insightops/preparation`: cleaning, derived fields, and manipulation summaries.
- `insightops/trends`: deterministic monthly trend analysis.
- `insightops/forecasting`: forecast readiness and deterministic baseline forecasts.
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

The core platform uses deterministic rules for collection metadata, validation, profiling, quality scoring, governance gates, preparation, manipulation, trend analysis, baseline forecasting, metrics, security checks, anomalies, chart data, insights, reports, and audit events. Trend analysis summarizes historical monthly movement. Forecast analysis adds transparent baseline planning aids only; it does not use ML, forecasting libraries, or regression. Anomaly detection combines fixed business rules with transparent IQR-based statistical methods; no ML is used, and thresholds remain auditable. This makes outputs explainable and testable before any optional LLM layer is introduced.

## Optional LLM Narrative

The narrative layer provides deterministic fallback, guarded prompt construction, and optional provider integration for narrative writing. An LLM provider may rewrite deterministic facts into polished prose, but it must not control ingestion, validation, profiling, quality scoring, security, metrics, anomaly detection, report generation, routing, file handling, or audit decisions.

Suspicious text from uploaded data is treated as data, not instructions. Human-review or prompt-injection flags block LLM narrative usage and fall back to deterministic output.

## Centralized LLM Orchestration (OpenRouter Framework)

`insightops/llm/` is the centralized, decoupled provider layer for model-backed language operations. It separates vendor transport schemas from analytical execution engines, runtime adapters, planning logic, and API routes. Higher-level modules consume typed chat contracts and controlled provider errors instead of importing SDK clients directly. This keeps LLM usage replaceable, testable, and isolated from deterministic analytics code.

The package exposes `ChatMessage`, typed response primitives, `OpenRouterClient`, and `LLMProviderError`. `OpenRouterClient` uses `openai.AsyncOpenAI` against OpenRouter's OpenAI-compatible API, while preserving a narrow internal boundary for request construction, response parsing, attribution headers, and provider failure normalization.

Configuration is loaded through `insightops/config.py`. `INSIGHTOPS_OPENROUTER_API_KEY` is the preferred application-scoped credential. If it is absent, the standard `OPENROUTER_API_KEY` environment variable is accepted as a compatibility fallback. `INSIGHTOPS_OPENROUTER_MODEL` selects the model, and `INSIGHTOPS_OPENROUTER_BASE_URL` sets the provider base URL. These settings map directly into the `AsyncOpenAI` transport along with OpenRouter attribution headers: `X-OpenRouter-Title: InsightOps AI` and `HTTP-Referer`.

The network contract is intentionally small. Callers pass arrays of validated `ChatMessage` objects into `OpenRouterClient.complete_chat(...)` for non-streaming text or `OpenRouterClient.stream_chat_completion(...)` for token streaming. The streaming method is an async generator: it calls chat completions with `stream=True`, defensively extracts chunk deltas, skips empty payloads, and yields clean text tokens downstream. Connection failures, API status errors, provider timeouts, malformed chunks, and SDK exceptions are wrapped as `LLMProviderError`, giving planning and runtime layers one controlled failure type for deterministic fallback and user-safe reporting.

### Hybrid Intent Routing (Planner Integration)

`insightops/planning/planner.py` exposes a hybrid planner path for streaming analysis runs. The deterministic `build_analysis_plan(...)` function remains the baseline router for tests, fallback behavior, and no-key environments. The async `build_hybrid_analysis_plan(...)` function first builds that deterministic fallback, then uses `OpenRouterClient` only when an OpenRouter API key is configured or an explicit planner client is injected.

The dynamic path sends a compact schema and user message as typed `ChatMessage` inputs. The model is instructed to return one strict JSON object containing an allowed intent plus optional `x_column`, `y_column`, and explanation fields. The planner validates the JSON, maps the intent to the existing artifact builders, resolves columns only against the uploaded dataset schema, and refuses invented columns by falling back to deterministic resolver defaults.

Provider failures are non-fatal by design. `LLMProviderError`, malformed JSON, invalid payloads, timeout/network errors, and schema validation issues all return the deterministic regex plan. Runtime adapters call the hybrid resolver, so configured deployments can interpret more complex natural-language requests while preserving the high-speed deterministic loop as the crash-proof execution path.

The mock runtime simulator also routes payloads through the hybrid resolver before emitting deterministic notebook and artifact events, keeping planner behavior consistent across mock, local Python, and Docker runtime modes.

## Current Limitations

- No authentication or multi-user authorization.
- No database persistence.
- No LLM-generated execution code.
- No database-backed chart or report artifact retention.
- Report artifacts are temporarily generated per-request and not retained in persistent user storage.

## Future Improvements

- Add authenticated artifact download endpoints.
- Add persistent audit storage.
- Add production-grade access control.
- Add chart and report retention controls.
- Expand LLM provider evaluation and monitoring.
