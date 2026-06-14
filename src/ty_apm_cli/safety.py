from __future__ import annotations

from typing import Any, Dict, List


READ_SAFETY = "read"
BLOCKED_SAFETY = {"guarded", "write", "unknown"}
HIGH_RISK_WORDS = [
    "delete",
    "remove",
    "save",
    "update",
    "create",
    "creat",
    "bind",
    "unbind",
    "execute",
    "cancel",
    "change",
    "sort",
    "删除",
    "保存",
    "修改",
    "创建",
    "新建",
    "绑定",
    "解绑",
    "执行",
    "取消",
    "启用",
    "禁用",
    "排序",
]


class UnsupportedSafetyLevel(RuntimeError):
    def __init__(self, catalog_id: str, safety: str) -> None:
        super().__init__("first version only executes safety=read endpoints")
        self.catalog_id = catalog_id
        self.safety = safety


def assert_executable(endpoint: Dict[str, Any]) -> None:
    safety = endpoint.get("safety", "unknown")
    if safety != READ_SAFETY or not endpoint.get("execution_supported", False):
        raise UnsupportedSafetyLevel(endpoint.get("id", ""), safety)


def audit_endpoint(endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    safety = endpoint.get("safety")
    execution_supported = endpoint.get("execution_supported")
    searchable = " ".join(
        str(endpoint.get(key, "")) for key in ("id", "title", "path", "description")
    ).lower()

    if safety not in {"read", "guarded", "write", "unknown"}:
        issues.append({"type": "missing_or_invalid_safety", "catalog_id": endpoint.get("id")})
    if safety in BLOCKED_SAFETY and execution_supported:
        issues.append({"type": "blocked_endpoint_marked_executable", "catalog_id": endpoint.get("id")})
    if safety == READ_SAFETY and not execution_supported:
        issues.append({"type": "read_endpoint_not_executable", "catalog_id": endpoint.get("id")})
    if safety == READ_SAFETY:
        hits = [word for word in HIGH_RISK_WORDS if word.lower() in searchable]
        if hits:
            issues.append(
                {
                    "type": "read_endpoint_contains_high_risk_word",
                    "catalog_id": endpoint.get("id"),
                    "hits": sorted(set(hits)),
                }
            )
    for field in ("id", "title", "method", "path", "doc"):
        if not endpoint.get(field):
            issues.append({"type": "missing_required_field", "catalog_id": endpoint.get("id"), "field": field})
    return issues

