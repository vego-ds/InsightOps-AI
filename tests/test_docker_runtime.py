import asyncio
from pathlib import Path
import subprocess

import pytest

from insightops.datasets import DatasetMetadata
from insightops.runtime import DockerRuntimeAdapter, RunContext
from insightops.runtime.docker_runtime import _validated_dataset_mount_path


def test_docker_unavailable_path_is_controlled(monkeypatch, tmp_path: Path) -> None:
    def unavailable_run(*args, **kwargs):
        raise FileNotFoundError("docker")

    monkeypatch.setattr(subprocess, "run", unavailable_run)

    events = _collect_events(DockerRuntimeAdapter(), _context(tmp_path))

    assert events == [
        {
            "version": "insightops.run-event.v1",
            "runId": "run-123",
            "sequence": 1,
            "type": "run.error",
            "errorMessage": "Docker runtime is unavailable.",
        }
    ]


def test_docker_event_contracts_remain_stable(monkeypatch, tmp_path: Path) -> None:
    commands: list[list[str]] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        if command[:2] == ["docker", "version"]:
            return subprocess.CompletedProcess(command, 0, stdout="24.0.0\n", stderr="")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="Dataset rows: 1\nDataset columns: 2\n",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    events = _collect_events(DockerRuntimeAdapter(), _context(tmp_path))
    event_types = [event["type"] for event in events]

    assert event_types == [
        "run.status",
        "run.cell.started",
        "run.cell.stdout",
        "run.cell.completed",
        "run.final",
    ]
    assert all(event["version"] == "insightops.run-event.v1" for event in events)
    assert all(event["runId"] == "run-123" for event in events)

    docker_run_command = commands[1]
    assert "--privileged" not in docker_run_command
    assert "--network" in docker_run_command
    assert "none" in docker_run_command
    assert "--read-only" in docker_run_command
    mount_value = docker_run_command[docker_run_command.index("--mount") + 1]
    assert mount_value.endswith(",readonly")


def test_docker_timeout_message_and_cleanup_are_controlled(
    monkeypatch,
    tmp_path: Path,
) -> None:
    commands: list[list[str]] = []
    shell_values: list[bool | None] = []

    def fake_run(command, **kwargs):
        commands.append(command)
        shell_values.append(kwargs.get("shell"))
        if command[:2] == ["docker", "version"]:
            return subprocess.CompletedProcess(command, 0, stdout="24.0.0\n", stderr="")
        if command[:3] == ["docker", "rm", "-f"]:
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        raise subprocess.TimeoutExpired(command, timeout=30)

    monkeypatch.setattr(subprocess, "run", fake_run)

    events = _collect_events(DockerRuntimeAdapter(timeout_seconds=30), _context(tmp_path))
    failure = next(event for event in events if event["type"] == "run.cell.failed")

    assert failure["errorMessage"] == (
        "Docker runtime timed out after 30s. "
        "The runtime container was stopped safely."
    )
    assert "docker run" not in failure["errorMessage"]
    assert any(command[:3] == ["docker", "rm", "-f"] for command in commands)
    assert all(shell is False for shell in shell_values)


def test_docker_dataset_mount_validation_rejects_unsafe_paths(tmp_path: Path) -> None:
    safe_root = tmp_path / "safe"
    safe_root.mkdir()
    outside = tmp_path / "outside.csv"
    outside.write_text("region,revenue\nNorth,1200\n", encoding="utf-8")
    metadata = DatasetMetadata(
        dataset_id="dataset-123",
        file_name="outside.csv",
        mime_type="text/csv",
        size_bytes=outside.stat().st_size,
        path=outside,
        storage_root=safe_root,
    )
    context = RunContext(
        run_id="run-123",
        dataset_id=metadata.dataset_id,
        message="Summarize revenue.",
        schema=[],
        preview_rows=[],
        dataset_metadata=metadata,
        dataset_path=outside,
    )

    with pytest.raises(ValueError, match="escaped controlled storage root"):
        _validated_dataset_mount_path(context)


def _context(tmp_path: Path) -> RunContext:
    dataset_path = tmp_path / "dataset.csv"
    dataset_path.write_text("region,revenue\nNorth,1200\n", encoding="utf-8")
    metadata = DatasetMetadata(
        dataset_id="dataset-123",
        file_name="dataset.csv",
        mime_type="text/csv",
        size_bytes=dataset_path.stat().st_size,
        path=dataset_path,
        storage_root=tmp_path,
    )
    return RunContext(
        run_id="run-123",
        dataset_id=metadata.dataset_id,
        message="Summarize revenue.",
        schema=[],
        preview_rows=[],
        dataset_metadata=metadata,
        dataset_path=dataset_path,
    )


def _collect_events(
    adapter: DockerRuntimeAdapter,
    context: RunContext,
) -> list[dict]:
    async def collect() -> list[dict]:
        return [event async for event in adapter.stream_events(context)]

    return asyncio.run(collect())
