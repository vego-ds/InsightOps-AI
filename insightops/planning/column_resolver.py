import re
from typing import Any

SYNONYMS = {
    "sales": ["revenue", "amount", "total"],
    "income": ["revenue", "sales"],
    "date": ["order_date", "created_at", "updated_at", "time"],
    "time": ["date", "order_date", "month", "day"],
    "product": ["product", "sku", "item"],
    "customer": ["customer", "account", "client"],
}


def resolve_column(
    query: str,
    schema: list[dict[str, Any]],
    *,
    preferred_type: str | None = None,
) -> str | None:
    columns = _columns(schema)
    if not columns:
        return None

    query_text = query.strip()
    if query_text:
        exact = _exact_match(query_text, columns)
        if exact:
            return exact["key"]

        normalized = _normalize(query_text)
        for column in columns:
            if _normalize(column["key"]) == normalized or _normalize(column["label"]) == normalized:
                return column["key"]

        for column in columns:
            column_tokens = {_normalize(column["key"]), _normalize(column["label"])}
            if any(token and (token in normalized or normalized in token) for token in column_tokens):
                return column["key"]

        for synonym in SYNONYMS.get(normalized, []):
            matched = resolve_column(synonym, schema)
            if matched:
                return matched

    if preferred_type is not None:
        for column in columns:
            if column["dataType"] == preferred_type:
                return column["key"]
        if preferred_type == "number":
            for column in columns:
                if column["dataType"] == "integer":
                    return column["key"]
    return None


def resolve_first_by_types(
    schema: list[dict[str, Any]],
    data_types: set[str],
) -> str | None:
    for column in _columns(schema):
        if column["dataType"] in data_types:
            return column["key"]
    return None


def _exact_match(query: str, columns: list[dict[str, str]]) -> dict[str, str] | None:
    lowered = query.casefold()
    for column in columns:
        if column["key"].casefold() == lowered or column["label"].casefold() == lowered:
            return column
    return None


def _columns(schema: list[dict[str, Any]]) -> list[dict[str, str]]:
    columns = []
    for item in schema:
        key = item.get("key")
        if not isinstance(key, str) or not key:
            continue
        label = item.get("label") if isinstance(item.get("label"), str) else key
        data_type = item.get("dataType") if isinstance(item.get("dataType"), str) else "unknown"
        columns.append({"key": key, "label": label, "dataType": data_type})
    return columns


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())
