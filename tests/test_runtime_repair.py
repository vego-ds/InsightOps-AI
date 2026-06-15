import pytest

from insightops.runtime.repair import (
    build_repair_plan,
    parse_runtime_failure,
    repair_attempt_allowed,
)


def test_parse_runtime_failure_extracts_error_type_message_and_line() -> None:
    failure = parse_runtime_failure(
        "Traceback (most recent call last):\n"
        '  File "<cell>", line 7, in <module>\n'
        "IndexError: single positional indexer is out-of-bounds"
    )

    assert failure.error_type == "IndexError"
    assert failure.message == "single positional indexer is out-of-bounds"
    assert failure.failing_line == 7


def test_build_repair_plan_rejects_attempts_past_limit() -> None:
    failure = parse_runtime_failure("SyntaxError: invalid syntax")

    with pytest.raises(RuntimeError, match="repair attempt limit"):
        build_repair_plan(
            run_id="run-123",
            failed_cell_id="cell-1",
            failure=failure,
            attempt=3,
            max_attempts=1,
        )


def test_repair_attempt_allowed_enforces_bounds() -> None:
    assert repair_attempt_allowed(attempt=2, max_attempts=1)
    assert not repair_attempt_allowed(attempt=1, max_attempts=1)
    assert not repair_attempt_allowed(attempt=3, max_attempts=1)
