from collections.abc import AsyncIterator
from pathlib import Path
import re
import subprocess
import time
from uuid import uuid4

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
from insightops.artifacts.builders import build_artifacts_for_plan
from insightops.planning import build_analysis_plan
from insightops.runtime.code_templates import build_dataset_profile_code
from insightops.runtime.run_context import RunContext

CONTAINER_DATASET_PATH = "/workspace/input/dataset.csv"


class DockerRuntimeAdapter:
    def __init__(
        self,
        *,
        docker_binary: str = "docker",
        image: str = "python:3.12-slim",
        timeout_seconds: float = 30.0,
        memory_limit: str = "256m",
        cpus: str = "1",
    ) -> None:
        self.docker_binary = docker_binary
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.memory_limit = memory_limit
        self.cpus = cpus

    async def stream_events(self, context: RunContext) -> AsyncIterator[dict]:
        run_id = context.run_id
        sequence = 1
        plan = build_analysis_plan(context.message, context.schema)

        if not self.is_available():
            yield RunErrorEvent(
                version="insightops.run-event.v1",
                runId=run_id,
                sequence=sequence,
                type="run.error",
                errorMessage="Docker runtime is unavailable.",
            ).model_dump()
            return

        yield RunStatusEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=sequence,
            type="run.status",
            status=f"agent_planning:{plan.intent.value}",
        ).model_dump()
        sequence += 1

        code = build_dataset_profile_code()
        cell_id = f"{run_id}-docker-profile"
        yield RunCellStartedEvent(
            version="insightops.run-event.v1",
            runId=run_id,
            sequence=sequence,
            type="run.cell.started",
            cellId=cell_id,
            title="Profile registered dataset in Docker",
            language="python",
            code=code,
            attempt=1,
        ).model_dump()
        sequence += 1

        container_name = _container_name(run_id)
        started = time.monotonic()
        try:
            dataset_path = _validated_dataset_mount_path(context)
            result = subprocess.run(
                self._docker_run_command(
                    container_name=container_name,
                    dataset_path=dataset_path,
                    code=code,
                ),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
            duration_ms = max(0, int((time.monotonic() - started) * 1000))
        except subprocess.TimeoutExpired as error:
            self._force_remove_container(container_name)
            duration_ms = max(0, int((time.monotonic() - started) * 1000))
            yield _cell_failed(
                run_id=run_id,
                sequence=sequence,
                cell_id=cell_id,
                error_message=(
                    f"Docker runtime timed out after {self.timeout_seconds:g}s. "
                    "The runtime container was stopped safely."
                ),
                traceback=str(error),
                duration_ms=duration_ms,
            )
            sequence += 1
            yield _final_event(run_id, sequence, "Docker runtime failed safely.")
            return
        except (OSError, ValueError) as error:
            duration_ms = max(0, int((time.monotonic() - started) * 1000))
            yield _cell_failed(
                run_id=run_id,
                sequence=sequence,
                cell_id=cell_id,
                error_message="Docker runtime failed before execution.",
                traceback=str(error),
                duration_ms=duration_ms,
            )
            sequence += 1
            yield _final_event(run_id, sequence, "Docker runtime failed safely.")
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
            for artifact in build_artifacts_for_plan(context, plan):
                yield RunArtifactEvent(
                    version="insightops.run-event.v1",
                    runId=run_id,
                    sequence=sequence,
                    type="artifact",
                    artifact=artifact,
                ).model_dump()
                sequence += 1
            yield _final_event(run_id, sequence, "Docker deterministic dataset profile completed.")
            return

        yield _cell_failed(
            run_id=run_id,
            sequence=sequence,
            cell_id=cell_id,
            error_message="Docker runtime exited with an error.",
            traceback=result.stderr or f"Process exited with code {result.returncode}.",
            duration_ms=duration_ms,
        )
        sequence += 1
        yield _final_event(run_id, sequence, "Docker runtime failed safely.")

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                [self.docker_binary, "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0

    def _docker_run_command(
        self,
        *,
        container_name: str,
        dataset_path: Path,
        code: str,
    ) -> list[str]:
        return [
            self.docker_binary,
            "run",
            "--rm",
            "--name",
            container_name,
            "--network",
            "none",
            "--read-only",
            "--memory",
            self.memory_limit,
            "--cpus",
            self.cpus,
            "--mount",
            f"type=bind,src={dataset_path},dst={CONTAINER_DATASET_PATH},readonly",
            self.image,
            "python",
            "-c",
            code,
            CONTAINER_DATASET_PATH,
        ]

    def _force_remove_container(self, container_name: str) -> None:
        subprocess.run(
            [self.docker_binary, "rm", "-f", container_name],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
            shell=False,
        )


def _validated_dataset_mount_path(context: RunContext) -> Path:
    if context.dataset_path is None or context.dataset_metadata is None:
        raise ValueError("RunContext is missing resolved dataset path metadata.")

    dataset_path = context.dataset_path.resolve()
    storage_root = context.dataset_metadata.storage_root.resolve()
    if not dataset_path.is_relative_to(storage_root):
        raise ValueError("Dataset path escaped controlled storage root.")
    if not dataset_path.is_file():
        raise ValueError("Dataset path is not a readable file.")
    return dataset_path


def _container_name(run_id: str) -> str:
    safe_run_id = re.sub(r"[^a-zA-Z0-9_.-]", "-", run_id)[:40]
    return f"insightops-runtime-{safe_run_id}-{uuid4().hex[:8]}"


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
