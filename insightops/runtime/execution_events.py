from collections.abc import Iterator
from dataclasses import dataclass

from insightops.api.contracts import (
    RunArtifactEvent,
    RunCellCompletedEvent,
    RunCellFailedEvent,
    RunCellStartedEvent,
    RunCellStderrEvent,
    RunCellStdoutEvent,
    RunErrorEvent,
    RunFinalEvent,
    RunStatusEvent,
)
from insightops.answers import synthesize_final_answer
from insightops.artifacts.builders import build_artifacts_for_plan, get_dataset_shape
from insightops.conversation import conversation_store
from insightops.planning import AnalysisPlan
from insightops.runtime.run_context import RunContext


@dataclass
class RuntimeEventCursor:
    sequence: int = 1

    def next(self) -> int:
        current = self.sequence
        self.sequence += 1
        return current


def status_event(
    *,
    context: RunContext,
    cursor: RuntimeEventCursor,
    status: str,
) -> dict:
    return RunStatusEvent(
        version="insightops.run-event.v1",
        runId=context.run_id,
        sequence=cursor.next(),
        type="run.status",
        status=status,
    ).model_dump()


def runtime_error_event(
    *,
    context: RunContext,
    cursor: RuntimeEventCursor,
    error_message: str,
) -> dict:
    return RunErrorEvent(
        version="insightops.run-event.v1",
        runId=context.run_id,
        sequence=cursor.next(),
        type="run.error",
        errorMessage=error_message,
    ).model_dump()


def cell_started_event(
    *,
    context: RunContext,
    cursor: RuntimeEventCursor,
    cell_id: str,
    title: str,
    code: str,
    attempt: int = 1,
) -> dict:
    return RunCellStartedEvent(
        version="insightops.run-event.v1",
        runId=context.run_id,
        sequence=cursor.next(),
        type="run.cell.started",
        cellId=cell_id,
        title=title,
        language="python",
        code=code,
        attempt=attempt,
    ).model_dump()


def process_output_events(
    *,
    context: RunContext,
    cursor: RuntimeEventCursor,
    cell_id: str,
    stdout: str,
    stderr: str,
) -> Iterator[dict]:
    if stdout:
        yield RunCellStdoutEvent(
            version="insightops.run-event.v1",
            runId=context.run_id,
            sequence=cursor.next(),
            type="run.cell.stdout",
            cellId=cell_id,
            stdout=stdout,
        ).model_dump()

    if stderr:
        yield RunCellStderrEvent(
            version="insightops.run-event.v1",
            runId=context.run_id,
            sequence=cursor.next(),
            type="run.cell.stderr",
            cellId=cell_id,
            stderr=stderr,
        ).model_dump()


def successful_execution_events(
    *,
    context: RunContext,
    cursor: RuntimeEventCursor,
    cell_id: str,
    duration_ms: int,
    plan: AnalysisPlan,
) -> Iterator[dict]:
    yield RunCellCompletedEvent(
        version="insightops.run-event.v1",
        runId=context.run_id,
        sequence=cursor.next(),
        type="run.cell.completed",
        cellId=cell_id,
        durationMs=duration_ms,
    ).model_dump()

    artifacts = build_artifacts_for_plan(context, plan)
    for artifact in artifacts:
        yield RunArtifactEvent(
            version="insightops.run-event.v1",
            runId=context.run_id,
            sequence=cursor.next(),
            type="artifact",
            artifact=artifact,
        ).model_dump()

    if context.conversation_id:
        conversation_store.update_after_artifacts(
            conversation_id=context.conversation_id,
            artifact_ids=[artifact["id"] for artifact in artifacts],
            artifact_kinds=[artifact["kind"] for artifact in artifacts],
        )

    row_count, column_count = get_dataset_shape(context)
    yield final_event(
        context=context,
        cursor=cursor,
        assistant_message=synthesize_final_answer(
            plan=plan,
            artifacts=artifacts,
            dataset_metadata=context.dataset_metadata,
            row_count=row_count,
            column_count=column_count,
        ),
    )


def cell_failed_event(
    *,
    context: RunContext,
    cursor: RuntimeEventCursor,
    cell_id: str,
    error_message: str,
    traceback: str,
    duration_ms: int,
) -> dict:
    return RunCellFailedEvent(
        version="insightops.run-event.v1",
        runId=context.run_id,
        sequence=cursor.next(),
        type="run.cell.failed",
        cellId=cell_id,
        errorMessage=error_message,
        traceback=traceback,
        durationMs=duration_ms,
    ).model_dump()


def final_event(
    *,
    context: RunContext,
    cursor: RuntimeEventCursor,
    assistant_message: str,
) -> dict:
    return RunFinalEvent(
        version="insightops.run-event.v1",
        runId=context.run_id,
        sequence=cursor.next(),
        type="run.final",
        assistantMessage=assistant_message,
    ).model_dump()
