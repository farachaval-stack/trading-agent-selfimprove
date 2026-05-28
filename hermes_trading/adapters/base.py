from __future__ import annotations

from typing import Any


SCHEMA_VERSION = 1


class SchemaError(RuntimeError):
    """Raised when an adapter payload does not match the expected schema."""


def require_schema(payload: dict[str, Any], adapter_name: str) -> dict[str, Any]:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise SchemaError(
            f"{adapter_name} schema mismatch: expected {SCHEMA_VERSION}, "
            f"got {payload.get('schema_version')}"
        )
    return payload
