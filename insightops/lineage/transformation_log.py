from pydantic import BaseModel, Field


class TransformationLogEntry(BaseModel):
    step_name: str
    description: str
    records_affected: int
    fields_created: list[str] = Field(default_factory=list)
    fields_modified: list[str] = Field(default_factory=list)


class TransformationLog(BaseModel):
    entries: list[TransformationLogEntry] = Field(default_factory=list)


def create_transformation_log(
    entries: list[TransformationLogEntry],
) -> TransformationLog:
    return TransformationLog(entries=entries)
