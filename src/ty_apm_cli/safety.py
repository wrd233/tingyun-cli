from __future__ import annotations

from typing import Any, Dict, List

READ = "read"
BLOCKED = {"write", "guarded", "unknown"}
SAFETY_VALUES = {READ, *BLOCKED}
DANGEROUS_TERMS = [
    "create",
    "update",
    "delete",
    "remove",
    "save",
    "bind",
    "unbind",
    "modify",
    "change",
    "hide",
    "show",
    "import",
    "execute",
    "start",
    "cancel",
    "sort",
    "move",
    "configure",
    "reset",
    "clear",
    "enable",
    "disable",
    "创建",
    "新建",
    "修改",
    "删除",
    "保存",
    "绑定",
    "解绑",
    "执行",
    "启动",
    "取消",
    "排序",
    "隐藏",
    "启用",
    "禁用",
]


class SafetyBlocked(RuntimeError):
    pass


def assert_read_executable(entry: Dict[str, Any]) -> None:
    if entry.get("safety") != READ or not entry.get("execution_supported"):
        raise SafetyBlocked("v1 only executes safety=read endpoints")


def risky_terms(entry: Dict[str, Any]) -> List[str]:
    haystack = " ".join(
        str(entry.get(key, "")) for key in ("id", "title", "path", "section")
    ).lower()
    return sorted({term for term in DANGEROUS_TERMS if term.lower() in haystack})


def audit_entry(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    catalog_id = entry.get("id")
    safety = entry.get("safety")
    if safety not in SAFETY_VALUES:
        issues.append({"type": "invalid_safety", "catalog_id": catalog_id, "safety": safety})
    if safety in BLOCKED and entry.get("execution_supported"):
        issues.append({"type": "blocked_endpoint_marked_executable", "catalog_id": catalog_id})
    if safety == READ and not entry.get("execution_supported"):
        issues.append({"type": "read_endpoint_not_executable", "catalog_id": catalog_id})
    if safety == READ:
        hits = risky_terms(entry)
        if hits:
            issues.append({"type": "read_endpoint_contains_risky_term", "catalog_id": catalog_id, "hits": hits})
    for field in ("id", "domain", "title", "method", "path", "safety", "execution_supported", "request", "response", "evidence"):
        if field not in entry:
            issues.append({"type": "missing_required_field", "catalog_id": catalog_id, "field": field})
    if entry.get("execution_supported") and not entry.get("path"):
        issues.append({"type": "executable_missing_path", "catalog_id": catalog_id})
    return issues
