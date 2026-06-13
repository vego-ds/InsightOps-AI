import asyncio
from pathlib import Path

from insightops.datasets import DatasetMetadata
from insightops.runtime import LocalPythonRuntimeAdapter, RunContext
from insightops.runtime import local_python_runtime


def test_local_runtime_emits_notebook_cell_events(tmp_path: Path) -> None:
    context = _context(tmp_path)

    events = _collect_events(LocalPythonRuntimeAdapter(), context)
    event_types = {event["type"] for event in events}

    assert "run.status" in event_types
    assert "run.cell.started" in event_types
    assert "run.cell.completed" in event_types
    assert "run.final" in event_types


def test_local_runtime_reads_registered_dataset_path(tmp_path: Path) -> None:
    context = _context(tmp_path, csv_text="region,revenue\nNorth,1200\nSouth,800\n")

    events = _collect_events(LocalPythonRuntimeAdapter(), context)
    stdout = "\n".join(
        event["stdout"] for event in events if event["type"] == "run.cell.stdout"
    )

    assert "Dataset rows: 2" in stdout
    assert "Dataset columns: 2" in stdout
    assert "Columns: region, revenue" in stdout


def test_local_runtime_captures_stdout(tmp_path: Path) -> None:
    context = _context(tmp_path)

    events = _collect_events(LocalPythonRuntimeAdapter(), context)

    assert any(
        event["type"] == "run.cell.stdout" and "Dataset rows:" in event["stdout"]
        for event in events
    )


def test_local_runtime_emits_real_artifact_events(tmp_path: Path) -> None:
    context = _context(tmp_path)

    events = _collect_events(LocalPythonRuntimeAdapter(), context)
    artifacts = [event for event in events if event["type"] == "artifact"]

    assert {event["artifact"]["kind"] for event in artifacts} == {
        "table",
        "chart",
        "markdown",
    }
    assert events[-1]["type"] == "run.final"


def test_local_runtime_final_event_uses_synthesized_answer(tmp_path: Path) -> None:
    context = _context(tmp_path, message="revenue by region")

    events = _collect_events(LocalPythonRuntimeAdapter(), context)
    final = events[-1]

    assert final["type"] == "run.final"
    assert "grouped metric analysis" in final["assistantMessage"]
    assert "revenue by region" in final["assistantMessage"]
    assert "Artifacts tab" in final["assistantMessage"]


def test_local_runtime_emits_different_artifact_sets_for_different_prompts(
    tmp_path: Path,
) -> None:
    summary_events = _collect_events(
        LocalPythonRuntimeAdapter(),
        _context(tmp_path / "summary", message="summary overview"),
    )
    grouped_events = _collect_events(
        LocalPythonRuntimeAdapter(),
        _context(tmp_path / "grouped", message="revenue by region"),
    )

    summary_ids = {
        event["artifact"]["id"] for event in summary_events if event["type"] == "artifact"
    }
    grouped_ids = {
        event["artifact"]["id"] for event in grouped_events if event["type"] == "artifact"
    }

    assert any("dataset-profile" in artifact_id for artifact_id in summary_ids)
    assert any("grouped-metric" in artifact_id for artifact_id in grouped_ids)
    assert summary_ids != grouped_ids


def test_local_runtime_emits_failure_event_for_invalid_dataset_path(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    missing_path = tmp_path / "missing.csv"
    context = RunContext(
        run_id=context.run_id,
        dataset_id=context.dataset_id,
        message=context.message,
        schema=context.schema,
        preview_rows=context.preview_rows,
        dataset_metadata=context.dataset_metadata,
        dataset_path=missing_path,
    )

    events = _collect_events(LocalPythonRuntimeAdapter(), context)

    assert any(event["type"] == "run.cell.failed" for event in events)
    assert events[-1]["type"] == "run.final"


def test_local_runtime_timeout_behavior_is_controlled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    context = _context(tmp_path)
    monkeypatch.setattr(
        local_python_runtime,
        "build_dataset_profile_code",
        lambda: "import time\ntime.sleep(2)",
    )

    events = _collect_events(
        LocalPythonRuntimeAdapter(timeout_seconds=0.01),
        context,
    )
    failure = next(event for event in events if event["type"] == "run.cell.failed")

    assert failure["errorMessage"] == "Local Python runtime timed out."
    assert events[-1]["type"] == "run.final"


def _context(
    tmp_path: Path,
    *,
    csv_text: str = "region,revenue\nNorth,1200\n",
    message: str = "Summarize revenue.",
) -> RunContext:
    tmp_path.mkdir(parents=True, exist_ok=True)
    dataset_path = tmp_path / "dataset.csv"
    dataset_path.write_text(csv_text, encoding="utf-8")
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
        message=message,
        schema=[
            {"key": "region", "label": "region", "dataType": "string"},
            {"key": "revenue", "label": "revenue", "dataType": "number"},
        ],
        preview_rows=[],
        dataset_metadata=metadata,
        dataset_path=dataset_path,
    )


def _collect_events(
    adapter: LocalPythonRuntimeAdapter,
    context: RunContext,
) -> list[dict]:
    async def collect() -> list[dict]:
        return [event async for event in adapter.stream_events(context)]

    return asyncio.run(collect())
