from pathlib import Path

from scripts.verify_dependencies import (
    missing_required_dependencies,
    parse_dependency_name,
    parse_requirements,
)


def test_parser_recognizes_plain_dependency_names() -> None:
    assert parse_requirements("fastapi\npytest\n") == {"fastapi", "pytest"}


def test_parser_recognizes_dependencies_with_version_specifiers() -> None:
    assert parse_dependency_name("fastapi>=0.100") == "fastapi"
    assert parse_dependency_name("pytest==8.0.0") == "pytest"
    assert parse_dependency_name("ruff~=0.8") == "ruff"


def test_missing_required_dependencies_are_reported() -> None:
    missing = missing_required_dependencies("fastapi\npytest\n")

    assert "uvicorn" in missing
    assert "python-multipart" in missing


def test_real_requirements_pass_dependency_verification() -> None:
    requirements_text = Path("requirements.txt").read_text()

    assert missing_required_dependencies(requirements_text) == set()
