from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "investigation-manifest.schema.json"


def validate_investigation_manifest(value: Any) -> List[Dict[str, Any]]:
    """Validate the JSON-Schema subset used by the committed Draft 2020-12 schema."""
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [{"path": "$", "rule": "schema_unavailable"}]
    return validate_schema(value, schema)


def validate_schema(value: Any, schema: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Validate the deterministic JSON-Schema subset shared by local compilers."""
    return _validate(value, schema, path="$")


def _validate(value: Any, schema: Mapping[str, Any], *, path: str) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    if "const" in schema and value != schema["const"]:
        issues.append({"path": path, "rule": "const"})
    if "enum" in schema and value not in schema["enum"]:
        issues.append({"path": path, "rule": "enum"})

    expected_type = schema.get("type")
    if expected_type is not None and not _is_type(value, str(expected_type)):
        issues.append({"path": path, "rule": "type", "expected_type": expected_type, "actual_type": _json_type(value)})
        return issues

    if isinstance(value, Mapping):
        required = schema.get("required") if isinstance(schema.get("required"), list) else []
        for name in required:
            if name not in value:
                issues.append({"path": path, "rule": "required", "property": str(name)})
        properties = schema.get("properties") if isinstance(schema.get("properties"), Mapping) else {}
        if schema.get("additionalProperties") is False:
            for name in sorted(set(value) - set(properties), key=str):
                issues.append({"path": path, "rule": "additionalProperties", "property": str(name)})
        for name, nested_schema in properties.items():
            if name in value and isinstance(nested_schema, Mapping):
                issues.extend(_validate(value[name], nested_schema, path=f"{path}.{name}"))

    if isinstance(value, list):
        if isinstance(schema.get("minItems"), int) and len(value) < schema["minItems"]:
            issues.append({"path": path, "rule": "minItems", "minimum": schema["minItems"]})
        if schema.get("uniqueItems") is True:
            seen = set()
            for index, item in enumerate(value):
                marker = json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                if marker in seen:
                    issues.append({"path": f"{path}[{index}]", "rule": "uniqueItems"})
                seen.add(marker)
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                issues.extend(_validate(item, item_schema, path=f"{path}[{index}]"))

    if isinstance(value, str) and isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
        issues.append({"path": path, "rule": "minLength"})
    return issues


def _is_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, Mapping),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return type(value).__name__
