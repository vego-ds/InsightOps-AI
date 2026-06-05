from pathlib import Path

REQUIRED_DEPENDENCIES = {
    "fastapi",
    "uvicorn",
    "pydantic",
    "pytest",
    "ruff",
    "httpx2",
    "python-multipart",
    "matplotlib",
    "reportlab",
}

VERSION_SPECIFIER_CHARS = "<=>!~[;"


def parse_dependency_name(requirement: str) -> str:
    stripped = requirement.strip()
    for index, character in enumerate(stripped):
        if character in VERSION_SPECIFIER_CHARS:
            return stripped[:index].strip().casefold()
    return stripped.casefold()


def parse_requirements(requirements_text: str) -> set[str]:
    dependencies: set[str] = set()

    for line in requirements_text.splitlines():
        requirement = line.strip()
        if not requirement or requirement.startswith("#"):
            continue

        dependencies.add(parse_dependency_name(requirement))

    return dependencies


def missing_required_dependencies(requirements_text: str) -> set[str]:
    dependencies = parse_requirements(requirements_text)
    return REQUIRED_DEPENDENCIES - dependencies


def verify_requirements_file(path: Path) -> None:
    missing_dependencies = missing_required_dependencies(path.read_text())
    if missing_dependencies:
        missing_list = ", ".join(sorted(missing_dependencies))
        raise SystemExit(f"Missing required dependencies: {missing_list}")

    print("Dependency verification passed.")


def main() -> None:
    verify_requirements_file(Path("requirements.txt"))


if __name__ == "__main__":
    main()
