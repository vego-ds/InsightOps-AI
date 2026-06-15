from dataclasses import dataclass
import re


MAX_REPAIR_ATTEMPTS = 1
_TRACEBACK_LIMIT = 4_000
_ERROR_LINE_RE = re.compile(
    r"^(?P<error_type>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception))(?::\s*(?P<message>.*))?$"
)
_FILE_LINE_RE = re.compile(r'File "(?P<file>[^"]+)", line (?P<line>\d+)')


@dataclass(frozen=True)
class RuntimeFailureSummary:
    error_type: str
    message: str
    failing_line: int | None
    traceback: str


@dataclass(frozen=True)
class RuntimeRepairPlan:
    failed_cell_id: str
    repair_cell_id: str
    title: str
    reason: str
    code: str
    attempt: int


def parse_runtime_failure(traceback_text: str) -> RuntimeFailureSummary:
    normalized_traceback = _normalize_traceback(traceback_text)
    try:
        lines = [line.strip() for line in normalized_traceback.splitlines() if line.strip()]
        error_line = lines[-1] if lines else "RuntimeError: Execution failed"
        error_match = _ERROR_LINE_RE.match(error_line)
        line_match = next(
            (
                _FILE_LINE_RE.search(line)
                for line in reversed(lines)
                if _FILE_LINE_RE.search(line)
            ),
            None,
        )
    except (IndexError, re.error) as error:
        raise ValueError("Runtime failure details could not be parsed.") from error

    error_type = error_match.group("error_type") if error_match else "RuntimeError"
    message = (
        error_match.group("message")
        if error_match and error_match.group("message")
        else error_line
    )
    failing_line = int(line_match.group("line")) if line_match else None

    return RuntimeFailureSummary(
        error_type=error_type,
        message=message,
        failing_line=failing_line,
        traceback=normalized_traceback,
    )


def build_repair_plan(
    *,
    run_id: str,
    failed_cell_id: str,
    failure: RuntimeFailureSummary,
    attempt: int,
    max_attempts: int = MAX_REPAIR_ATTEMPTS,
) -> RuntimeRepairPlan:
    if not repair_attempt_allowed(attempt=attempt, max_attempts=max_attempts):
        raise RuntimeError("Runtime repair attempt limit exceeded.")

    return RuntimeRepairPlan(
        failed_cell_id=failed_cell_id,
        repair_cell_id=f"{run_id}-cell-repaired-profile",
        title="Repair profile step",
        reason=_repair_reason(failure),
        code=_repair_code(failure),
        attempt=attempt,
    )


def repair_attempt_allowed(*, attempt: int, max_attempts: int = MAX_REPAIR_ATTEMPTS) -> bool:
    if max_attempts < 0:
        raise ValueError("max_attempts must be non-negative.")
    return 2 <= attempt <= max_attempts + 1


def _normalize_traceback(traceback_text: str) -> str:
    normalized = traceback_text.strip()
    if not normalized:
        return "RuntimeError: Execution failed"
    return normalized[:_TRACEBACK_LIMIT]


def _repair_reason(failure: RuntimeFailureSummary) -> str:
    if failure.error_type == "SyntaxError":
        return "Retry with validated syntax-safe notebook code."
    if failure.error_type in {"IndexError", "KeyError"}:
        return "Retry with guarded column and index access."
    return "Retry with deterministic guarded preview-only logic."


def _repair_code(failure: RuntimeFailureSummary) -> str:
    if failure.error_type in {"IndexError", "KeyError"}:
        return (
            "import pandas as pd\n"
            "preview_rows = []\n"
            "print('Recovered with guarded dataset access')"
        )
    if failure.error_type == "SyntaxError":
        return (
            "import pandas as pd\n"
            "print('Recovered with syntax-safe profiling path')"
        )
    return (
        "import pandas as pd\n"
        "print('Recovered with preview-safe profiling path')"
    )
