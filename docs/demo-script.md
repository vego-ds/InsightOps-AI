# Demo Script

This is a 5 to 7 minute local MVP demo. It assumes the backend is running on `http://127.0.0.1:8000` and the frontend is running on `http://localhost:3000`.

## Setup Before The Demo

Terminal 1:

```bash
source venv/bin/activate
INSIGHTOPS_RUNTIME=local_python uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Terminal 2:

```bash
cd web
npm run dev
```

Open:

```text
http://localhost:3000
```

Keep `data/sample/sales_sample.csv` ready for upload.

## Demo Timing

### 0:00-0:45 - Position The Product

Narration:

> InsightOps-AI is a local AI-style data analysis workspace. The MVP combines three familiar analyst surfaces: chat, notebook execution, and a data canvas. The important part is that the current system is deterministic and auditable. We can upload a CSV, inspect the schema, ask analysis questions, watch execution events stream in, review artifacts, export results, and clean up the dataset.

Show:

- Header and no-dataset state.
- Disabled chat input.
- Empty run history.
- Preview, Schema, and Artifacts tabs.

### 0:45-1:30 - Upload And Preview

Action:

1. Upload `data/sample/sales_sample.csv`.
2. Stay on the Preview tab.

Narration:

> I am uploading a sample sales CSV. The backend stores the file in controlled local scratch storage and returns a strict preview contract. The frontend renders the first rows, total row count, column count, and typed columns before any analysis happens.

Show:

- Dataset summary.
- Preview table.
- Clear Dataset button.

### 1:30-2:10 - Schema Inspector

Action:

1. Click Schema.
2. Select `region`, `product`, `revenue`, and `order_date` if visible.

Narration:

> The schema inspector is the bridge between raw data and analysis. It shows each column key, label, data type, nullability, and sample values. This is also what the analysis request sends as context, so the planner never has to invent columns.

Show:

- Column list.
- Selected column details.
- Recommended actions by data type.

### 2:10-3:15 - First Chat Analysis

Action:

Ask:

```text
Summarize this dataset
```

Narration:

> Now I can ask for a dataset summary. This is not calling an LLM yet. The backend creates an analysis run and streams deterministic events over Server-Sent Events. The UI turns those events into a notebook-style timeline.

Show:

- User message.
- Pending assistant message.
- Streaming status card.
- Notebook cell.
- Stdout/stderr panels if present.
- Final assistant answer.

### 3:15-4:20 - Intent Routing And Follow-Up Context

Action:

Ask:

```text
Show revenue by region
```

Then ask:

```text
Now by product
```

Narration:

> The planner maps explicit prompts to deterministic intents and columns. In this case, revenue by region creates grouped metric artifacts. The follow-up question reuses the last metric, revenue, and swaps the grouping column to product. That gives us conversational continuity without relying on an LLM.

Show:

- New assistant runs.
- Run history gaining entries.
- Artifacts tab becoming active.

### 4:20-5:20 - Artifacts And Data Canvas

Action:

1. Open Artifacts if it is not already focused.
2. Click chart, table, and markdown artifacts if available.

Narration:

> Artifacts are safe frontend-rendered outputs. Tables only render flat scalar rows, charts use constrained bar or line specs, and markdown is rendered as plain text. The canvas automatically focuses useful artifacts while still letting the user manually choose another result.

Show:

- Artifact gallery.
- Chart artifact.
- Table artifact.
- Markdown artifact.

### 5:20-6:15 - Run History And Exports

Action:

1. Click a previous run in Run History.
2. Export an artifact from the artifact card.
3. Export the selected run report from Run History.

Narration:

> The MVP keeps in-memory run history. A user can revisit a prompt, final answer, execution timeline, and artifacts. Exports are frontend-only for now: table and chart data export as CSV, markdown exports as `.md`, and a run report exports as Markdown.

Show:

- Prior run selection.
- Timeline restore.
- Export button on artifact.
- Export report button.

### 6:15-7:00 - Dataset Cleanup

Action:

1. Click Clear dataset.

Narration:

> Finally, the workspace cleanup path removes the registered dataset file from local scratch storage and resets the frontend state. That clears the active dataset, chat, artifacts, run history, execution timeline, notebook cells, selected columns, and canvas mode.

Show:

- Return to no-dataset preview state.
- Chat disabled.
- Run History empty.
- Artifacts disabled.

Closing narration:

> This freezes the local MVP: upload, inspect, ask, stream, review, export, revisit, and clean up. The next production steps would be persistence, auth, worker orchestration, and LLM integration behind the existing deterministic interfaces.
