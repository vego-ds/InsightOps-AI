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
from insightops.conversation import conversation_store, resolve_hybrid_followup_plan
from insightops.planning import AnalysisPlan
from insightops.runtime.repair import build_repair_plan, parse_runtime_failure
from insightops.runtime.run_context import RunContext


class MockRuntimeAdapter:
    async def stream_events(self, context: RunContext) -> AsyncIterator[dict]:
        plan = await resolve_hybrid_followup_plan(
            message=context.message,
            schema=context.schema,
            context=context.conversation_context,
        )
        if context.conversation_id:
            conversation_store.update_after_plan(
                conversation_id=context.conversation_id,
                dataset_id=context.dataset_id,
                run_id=context.run_id,
                plan=plan,
            )

        events = (
            _mock_failure_notebook_events(context, plan)
            if _is_failure_prompt(context.message)
            else _mock_notebook_events(context, plan)
        )

        for event in events:
            yield event.model_dump()


def _is_failure_prompt(message: str) -> bool:
    return any(token in message.casefold() for token in ("error", "fail"))


def _mock_notebook_events(context: RunContext, plan: AnalysisPlan) -> list:
    run_id = context.run_id
    cell_id = f"{run_id}-cell-profile"
    return [
        RunStatusEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=1,
            type="run.status",
            status=f"agent_planning:{plan.intent.value}",
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
        *_mock_artifact_events(run_id, plan=plan, start_sequence=6),
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


def _mock_failure_notebook_events(context: RunContext, plan: AnalysisPlan) -> list:
    run_id = context.run_id
    failed_cell_id = f"{run_id}-cell-failed-profile"
    traceback = (
        "Traceback (most recent call last):\n"
        '  File "<mock-notebook-cell>", line 3, in <module>\n'
        "ValueError: mock schema mismatch"
    )
    repair_plan = build_repair_plan(
        run_id=run_id,
        failed_cell_id=failed_cell_id,
        failure=parse_runtime_failure(traceback),
        attempt=2,
    )
    return [
        RunStatusEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=1,
            type="run.status",
            status=f"agent_planning:{plan.intent.value}",
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
            traceback=traceback,
            durationMs=96,
        ),
        RunRepairStartedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=5,
            type="run.repair.started",
            failedCellId=failed_cell_id,
            repairCellId=repair_plan.repair_cell_id,
            reason=repair_plan.reason,
        ),
        RunCellStartedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=6,
            type="run.cell.started",
            cellId=repair_plan.repair_cell_id,
            title=repair_plan.title,
            language="python",
            code=repair_plan.code,
            attempt=repair_plan.attempt,
        ),
        RunCellStdoutEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=7,
            type="run.cell.stdout",
            cellId=repair_plan.repair_cell_id,
            stdout="Recovered with preview-safe profiling path\nMock profiling completed.",
        ),
        RunCellCompletedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=8,
            type="run.cell.completed",
            cellId=repair_plan.repair_cell_id,
            durationMs=142,
        ),
        RunRepairCompletedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=9,
            type="run.repair.completed",
            failedCellId=failed_cell_id,
            repairCellId=repair_plan.repair_cell_id,
            outcome="Runtime repair completed; recovered cell output is available.",
        ),
        *_mock_artifact_events(run_id, plan=plan, start_sequence=10),
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


def _mock_artifact_events(
    run_id: str,
    *,
    plan: AnalysisPlan,
    start_sequence: int,
) -> list[RunArtifactEvent]:
    x_label = plan.x_column or "dataset"
    y_label = plan.y_column or "records"
    return [
        RunArtifactEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=start_sequence,
            type="artifact",
            artifact=TableArtifact(
                id=f"{run_id}-table-{plan.intent.value}",
                kind="table",
                title=f"Mock {plan.title} Summary",
                columns=[
                    {"key": "metric", "label": "Metric", "dataType": "string"},
                    {"key": "value", "label": "Value", "dataType": "string"},
                ],
                rows=[
                    {"metric": "Selected intent", "value": plan.intent.value},
                    {"metric": "X column", "value": plan.x_column},
                    {"metric": "Y column", "value": plan.y_column},
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
                id=f"{run_id}-chart-{plan.intent.value}",
                kind="chart",
                title=f"Mock {plan.title} Chart",
                chartType="bar",
                xKey=x_label,
                yKey=y_label,
                data=[
                    {x_label: "Segment A", y_label: 1350},
                    {x_label: "Segment B", y_label: 2100},
                    {x_label: "Segment C", y_label: 1800},
                ],
            ),
        ),
        RunArtifactEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=start_sequence + 2,
            type="artifact",
            artifact=MarkdownArtifact(
                id=f"{run_id}-markdown-{plan.intent.value}",
                kind="markdown",
                title=f"Mock {plan.title} Note",
                text=(
                    f"Mock runtime routed the request as {plan.intent.value}. "
                    "Artifacts are deterministic placeholders and no sandbox "
                    "execution was performed."
                ),
            ),
        ),
    ]
