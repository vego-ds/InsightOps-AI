from typing import Literal, TypeAlias

ArtifactScalar: TypeAlias = str | int | float | bool | None
ArtifactDataType: TypeAlias = Literal["string", "number", "integer", "boolean", "unknown"]

MAX_TABLE_ROWS = 50
MAX_CHART_ROWS = 12

TABLE_COLUMN_TYPE_VALUES = {"string", "number", "integer", "boolean", "unknown"}
CHART_TYPE_VALUES = {"bar", "line"}
