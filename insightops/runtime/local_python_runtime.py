from collections.abc import AsyncIterator
from pathlib import Path
import subprocess
import sys
import time

from insightops.conversation import conversation_store, resolve_hybrid_followup_plan
from insightops.runtime.code_templates import build_dataset_profile_code
from insightops.runtime.execution_events import (
    RuntimeEventCursor,
    cell_failed_event,
    cell_started_event,
    final_event,
    process_output_events,
    status_event,
    successful_execution_events,
)
from insightops.runtime.run_context import RunContext


class LocalPythonRuntimeAdapter:
    def __init__(self, *, timeout_seconds: float = 5.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def stream_events(self, context: RunContext) -> AsyncIterator[dict]:
        cell_id = f"{context.run_id}-local-python-profile"
        cursor = RuntimeEventCursor()
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

        yield status_event(
            context=context,
            cursor=cursor,
            status=f"agent_planning:{plan.intent.value}",
        )

        code = build_dataset_profile_code()
        yield cell_started_event(
            context=context,
            cursor=cursor,
            cell_id=cell_id,
            title="Profile registered dataset",
            code=code,
        )

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
            yield cell_failed_event(
                context=context,
                cursor=cursor,
                cell_id=cell_id,
                error_message="Local Python runtime timed out.",
                traceback=str(error),
                duration_ms=duration_ms,
            )
            yield final_event(
                context=context,
                cursor=cursor,
                assistant_message="Local Python runtime failed safely.",
            )
            return
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            duration_ms = max(0, int((time.monotonic() - started) * 1000))
            error_message = (
                "Local Python runtime timed out."
                if isinstance(error, subprocess.TimeoutExpired)
                else "Local Python runtime failed before execution."
            )
            yield cell_failed_event(
                context=context,
                cursor=cursor,
                cell_id=cell_id,
                error_message=error_message,
                traceback=str(error),
                duration_ms=duration_ms,
            )
            yield final_event(
                context=context,
                cursor=cursor,
                assistant_message="Local Python runtime failed safely.",
            )
            return

        for event in process_output_events(
            context=context,
            cursor=cursor,
            cell_id=cell_id,
            stdout=result.stdout,
            stderr=result.stderr,
        ):
            yield event

        if result.returncode == 0:
            for event in successful_execution_events(
                context=context,
                cursor=cursor,
                cell_id=cell_id,
                duration_ms=duration_ms,
                plan=plan,
            ):
                yield event
            return

        yield cell_failed_event(
            context=context,
            cursor=cursor,
            cell_id=cell_id,
            error_message="Local Python runtime exited with an error.",
            traceback=result.stderr or f"Process exited with code {result.returncode}.",
            duration_ms=duration_ms,
        )
        yield final_event(
            context=context,
            cursor=cursor,
            assistant_message="Local Python runtime failed safely.",
        )


def _validated_dataset_path(context: RunContext) -> Path:
    if context.dataset_path is None or context.dataset_metadata is None:
        raise ValueError("RunContext is missing resolved dataset path metadata.")

    dataset_path = context.dataset_path.resolve()
    storage_root = context.dataset_metadata.storage_root.resolve()
    if not dataset_path.is_relative_to(storage_root):
        raise ValueError("Dataset path escaped controlled storage root.")
    return dataset_path
