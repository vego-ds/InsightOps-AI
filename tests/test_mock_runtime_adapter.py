import asyncio

from insightops.runtime import MockRuntimeAdapter, RunContext


def _context(message: str = "Summarize revenue.") -> RunContext:
    return RunContext(
        run_id="run-123",
        dataset_id="dataset-123",
        message=message,
        schema=[{"key": "revenue", "label": "revenue", "dataType": "number"}],
        preview_rows=[{"revenue": 1200.0}],
    )


def test_mock_runtime_normal_stream_emits_final_event() -> None:
    events = _collect_events(_context())

    assert events[-1]["type"] == "run.final"
    assert events[-1]["version"] == "insightops.run-event.v1"
    assert events[-1]["runId"] == "run-123"


def test_mock_runtime_failure_stream_emits_cell_failed() -> None:
    events = _collect_events(_context("Force an error."))

    assert any(event["type"] == "run.cell.failed" for event in events)


def test_mock_runtime_failure_stream_emits_repair_events() -> None:
    events = _collect_events(_context("Please fail and repair."))
    event_types = {event["type"] for event in events}

    assert "run.repair.started" in event_types
    assert "run.repair.completed" in event_types


def test_mock_runtime_sequence_numbers_are_monotonic() -> None:
    events = _collect_events(_context("Please fail and repair."))
    sequences = [event["sequence"] for event in events]

    assert sequences == sorted(sequences)
    assert len(sequences) == len(set(sequences))


def _collect_events(context: RunContext) -> list[dict]:
    async def collect() -> list[dict]:
        adapter = MockRuntimeAdapter()
        return [event async for event in adapter.stream_events(context)]

    return asyncio.run(collect())
