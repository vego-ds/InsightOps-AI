from collections.abc import AsyncIterator
from pathlib import Path
import subprocess
import sys
import time

from insightops.api.contracts import (
    RunArtifactEvent,
    RunCellCompletedEvent,
    RunCellFailedEvent,
    RunCellStartedEvent,
    RunCellStderrEvent,
    RunCellStdoutEvent,
    RunFinalEvent,
    RunStatusEvent,
)
from insightops.answers import synthesize_final_answer
from insightops.artifacts.builders import build_artifacts_for_plan, get_dataset_shape
from insightops.planning import build_analysis_plan
from insightops.runtime.code_templates import build_dataset_profile_code
from insightops.runtime.run_context import RunContext


class LocalPythonRuntimeAdapter:
    def __init__(self, *, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def stream_events(self, context: RunContext) -> AsyncIterator[dict]:
        run_id = context.run_id
        cell_id = f"{run_id}-local-python-profile"
        sequence = 1
        plan = build_analysis_plan(context.message, context.schema)

        yield RunStatusEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=sequence,
            type="run.status",
            status=f"agent_planning:{plan.intent.value}",
        ).model_dump()
        sequence += 1

        code = build_dataset_profile_code()
        yield RunCellStartedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=sequence,
            type="run.cell.started",
            cellId=cell_id,
            title="Profile registered dataset",
            language="python",
            code=code,
            attempt=1,
        ).model_dump()
        sequence += 1

        started = time.monotonic()
        try:
            dataset_path = _validated_dataset_path(context)
            result = subprocess.run(
                [sys.executable, "-c", code, str(dataset_path)],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
            duration_ms = max(0, int((time.monotonic() - started) * 1000))
        except TimeoutError as error:
            duration_ms = max(0, int((time.monotonic() - started) * 1000))
            yield _cell_failed(
                run_id=run_id,
                sequence=sequence,
                cell_id=cell_id,
                error_message="Local Python runtime timed out.",
                traceback=str(error),
                duration_ms=duration_ms,
            )
            sequence += 1
            yield _final_event(run_id, sequence, "Local Python runtime failed safely.")
            return
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            duration_ms = max(0, int((time.monotonic() - started) * 1000))
            error_message = (
                "Local Python runtime timed out."
                if isinstance(error, subprocess.TimeoutExpired)
                else "Local Python runtime failed before execution."
            )
            yield _cell_failed(
                run_id=run_id,
                sequence=sequence,
                cell_id=cell_id,
                error_message=error_message,
                traceback=str(error),
                duration_ms=duration_ms,
            )
            sequence += 1
            yield _final_event(run_id, sequence, "Local Python runtime failed safely.")
            return

        if result.stdout:
            yield RunCellStdoutEvent(
                version="insightops.run-event.v1",
                runId=run_id,
                sequence=sequence,
                type="run.cell.stdout",
                cellId=cell_id,
                stdout=result.stdout,
            ).model_dump()
            sequence += 1

        if result.stderr:
            yield RunCellStderrEvent(
                version="insightops.run-event.v1",
                runId=run_id,
                sequence=sequence,
                type="run.cell.stderr",
                cellId=cell_id,
                stderr=result.stderr,
            ).model_dump()
            sequence += 1

        if result.returncode == 0:
            yield RunCellCompletedEvent(
                version="insightops.run-event.v1",
                runId=run_id,
                sequence=sequence,
                type="run.cell.completed",
                cellId=cell_id,
                durationMs=duration_ms,
            ).model_dump()
            sequence += 1
            artifacts = build_artifacts_for_plan(context, plan)
            for artifact in artifacts:
                yield RunArtifactEvent(
                    version="insightops.run-event.v1",
                    runId=run_id,
                    sequence=sequence,
                    type="artifact",
                    artifact=artifact,
                ).model_dump()
                sequence += 1
            row_count, column_count = get_dataset_shape(context)
            yield _final_event(
                run_id,
                sequence,
                synthesize_final_answer(
                    plan=plan,
                    artifacts=artifacts,
                    dataset_metadata=context.dataset_metadata,
                    row_count=row_count,
                    column_count=column_count,
                ),
            )
            return

        yield _cell_failed(
            run_id=run_id,
            sequence=sequence,
            cell_id=cell_id,
            error_message="Local Python runtime exited with an error.",
            traceback=result.stderr or f"Process exited with code {result.returncode}.",
            duration_ms=duration_ms,
        )
        sequence += 1
        yield _final_event(run_id, sequence, "Local Python runtime failed safely.")


def _validated_dataset_path(context: RunContext) -> Path:
    if context.dataset_path is None or context.dataset_metadata is None:
        raise ValueError("RunContext is missing resolved dataset path metadata.")

    dataset_path = context.dataset_path.resolve()
    storage_root = context.dataset_metadata.storage_root.resolve()
    if not dataset_path.is_relative_to(storage_root):
        raise ValueError("Dataset path escaped controlled storage root.")
    return dataset_path


def _cell_failed(
    *,
    run_id: str,
    sequence: int,
    cell_id: str,
    error_message: str,
    traceback: str,
    duration_ms: int,
) -> dict:
    return RunCellFailedEvent(
        version="insightops.run-event.v1",
        runId=run_id,
        sequence=sequence,
        type="run.cell.failed",
        cellId=cell_id,
        errorMessage=error_message,
        traceback=traceback,
        durationMs=duration_ms,
    ).model_dump()


def _final_event(run_id: str, sequence: int, assistant_message: str) -> dict:
    return RunFinalEvent(
        version="insightops.run-event.v1",
        runId=run_id,
        sequence=sequence,
        type="run.final",
        assistantMessage=assistant_message,
    ).model_dump()
