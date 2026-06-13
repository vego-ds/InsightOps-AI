from collections.abc import AsyncIterator

from insightops.api.contracts import (
    ChartArtifact,
    MarkdownArtifact,
    RunArtifactEvent,
    RunCellCompletedEvent,
    RunCellFailedEvent,
    RunCellStartedEvent,
    RunCellStderrEvent,
    RunCellStdoutEvent,
    RunFinalEvent,
    RunRepairCompletedEvent,
    RunRepairStartedEvent,
    RunStatusEvent,
    TableArtifact,
)
from insightops.runtime.run_context import RunContext


class MockRuntimeAdapter:
    async def stream_events(self, context: RunContext) -> AsyncIterator[dict]:
        events = (
            _mock_failure_notebook_events(context)
            if _is_failure_prompt(context.message)
            else _mock_notebook_events(context)
        )

        for event in events:
            yield event.model_dump()


def _is_failure_prompt(message: str) -> bool:
    return any(token in message.casefold() for token in ("error", "fail"))


def _mock_notebook_events(context: RunContext):
    run_id = context.run_id
    cell_id = f"{run_id}-cell-profile"
    return [
        RunStatusEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=1,
            type="run.status",
            status="agent_planning",
        ),
        RunCellStartedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=2,
            type="run.cell.started",
            cellId=cell_id,
            title="Profile uploaded dataset",
            language="python",
            code=(
                "import pandas as pd\n"
                "# Deterministic notebook mock; no code is executed.\n"
                "preview_rows = 50\n"
                "print(f'Preview rows inspected: {preview_rows}')"
            ),
            attempt=1,
        ),
        RunCellStdoutEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=3,
            type="run.cell.stdout",
            cellId=cell_id,
            stdout="Preview rows inspected: 50\nMock profiling completed.",
        ),
        RunCellStderrEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=4,
            type="run.cell.stderr",
            cellId=cell_id,
            stderr="Mock warning: execution runtime not connected; using preview data only.",
        ),
        RunCellCompletedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=5,
            type="run.cell.completed",
            cellId=cell_id,
            durationMs=184,
        ),
        *_mock_artifact_events(run_id, start_sequence=6),
        RunFinalEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=9,
            type="run.final",
            assistantMessage=(
                "Deterministic mock notebook analysis complete. Code cells, outputs, "
                "and artifacts are rendered without running a sandbox."
            ),
        ),
    ]


def _mock_failure_notebook_events(context: RunContext):
    run_id = context.run_id
    failed_cell_id = f"{run_id}-cell-failed-profile"
    repair_cell_id = f"{run_id}-cell-repaired-profile"
    return [
        RunStatusEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=1,
            type="run.status",
            status="agent_planning",
        ),
        RunCellStartedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=2,
            type="run.cell.started",
            cellId=failed_cell_id,
            title="Profile uploaded dataset",
            language="python",
            code=(
                "import pandas as pd\n"
                "# Deterministic failure mock; no code is executed.\n"
                "raise ValueError('mock schema mismatch')"
            ),
            attempt=1,
        ),
        RunCellStderrEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=3,
            type="run.cell.stderr",
            cellId=failed_cell_id,
            stderr="ValueError: mock schema mismatch",
        ),
        RunCellFailedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=4,
            type="run.cell.failed",
            cellId=failed_cell_id,
            errorMessage="Mock schema mismatch detected.",
            traceback=(
                "Traceback (most recent call last):\n"
                '  File "<mock-notebook-cell>", line 3, in <module>\n'
                "ValueError: mock schema mismatch"
            ),
            durationMs=96,
        ),
        RunRepairStartedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=5,
            type="run.repair.started",
            failedCellId=failed_cell_id,
            repairCellId=repair_cell_id,
            reason="Retry with deterministic guarded preview-only logic.",
        ),
        RunCellStartedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=6,
            type="run.cell.started",
            cellId=repair_cell_id,
            title="Repair profile step",
            language="python",
            code=(
                "import pandas as pd\n"
                "# Deterministic repaired mock; no code is executed.\n"
                "print('Recovered with preview-safe profiling path')"
            ),
            attempt=2,
        ),
        RunCellStdoutEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=7,
            type="run.cell.stdout",
            cellId=repair_cell_id,
            stdout="Recovered with preview-safe profiling path\nMock profiling completed.",
        ),
        RunCellCompletedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=8,
            type="run.cell.completed",
            cellId=repair_cell_id,
            durationMs=142,
        ),
        RunRepairCompletedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=9,
            type="run.repair.completed",
            failedCellId=failed_cell_id,
            repairCellId=repair_cell_id,
            outcome="Mock self-healing completed; recovered cell output is available.",
        ),
        *_mock_artifact_events(run_id, start_sequence=10),
        RunFinalEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=13,
            type="run.final",
            assistantMessage=(
                "Deterministic mock analysis recovered from a simulated cell failure. "
                "No sandbox, model, or real code execution was run."
            ),
        ),
    ]


def _mock_artifact_events(run_id: str, start_sequence: int) -> list[RunArtifactEvent]:
    return [
        RunArtifactEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=start_sequence,
            type="artifact",
            artifact=TableArtifact(
                id=f"{run_id}-table-summary",
                kind="table",
                title="Mock KPI Summary",
                columns=[
                    {"key": "metric", "label": "Metric", "dataType": "string"},
                    {"key": "value", "label": "Value", "dataType": "string"},
                ],
                rows=[
                    {"metric": "Preview rows inspected", "value": 50},
                    {"metric": "Mock quality status", "value": "ready"},
                ],
            ),
        ),
        RunArtifactEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=start_sequence + 1,
            type="artifact",
            artifact=ChartArtifact(
                id=f"{run_id}-chart-revenue",
                kind="chart",
                title="Mock Revenue Trend",
                chartType="bar",
                xKey="period",
                yKey="revenue",
                data=[
                    {"period": "Jan", "revenue": 1350},
                    {"period": "Feb", "revenue": 2100},
                    {"period": "Mar", "revenue": 1800},
                ],
            ),
        ),
        RunArtifactEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=start_sequence + 2,
            type="artifact",
            artifact=MarkdownArtifact(
                id=f"{run_id}-markdown-note",
                kind="markdown",
                title="Mock Analysis Note",
                text=(
                    "This is a deterministic placeholder artifact. "
                    "No runtime execution or model inference was performed."
                ),
            ),
        ),
    ]
