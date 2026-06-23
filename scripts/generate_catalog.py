from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

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


def convert(old_catalog: Dict[str, Any]) -> Dict[str, Any]:
    endpoints: List[Dict[str, Any]] = []
    for entry in old_catalog.get("endpoints", []):
        doc = entry.get("doc") or {}
        request = entry.get("request") or {}
        response = entry.get("response") or {}
        safety = entry.get("safety") or "unknown"
        haystack = " ".join(str(entry.get(key, "")) for key in ("id", "title", "path", "description")).lower()
        hits = sorted({term for term in DANGEROUS_TERMS if term.lower() in haystack})
        uncertainties = list(entry.get("uncertainties") or [])
        if safety == "read" and hits:
            safety = "guarded"
            uncertainties.append("Conservatively blocked because side-effect wording is present.")
        evidence = doc.get("evidence") or []
        excerpt = "; ".join(str(item) for item in evidence[:2]) if isinstance(evidence, list) else str(evidence)
        endpoints.append(
            {
                "id": entry.get("id"),
                "domain": entry.get("domain") or "unknown",
                "title": entry.get("title") or entry.get("id"),
                "section": doc.get("section") or "",
                "page": doc.get("page"),
                "method": str(entry.get("method") or "UNKNOWN").upper(),
                "path": entry.get("path") or "",
                "safety": safety,
                "execution_supported": bool(entry.get("execution_supported")) and safety == "read",
                "request": {"params": request.get("params") or []},
                "response": {"fields": response.get("fields") or response.get("params") or []},
                "evidence": {"source": "pdf", "page": doc.get("page"), "excerpt": excerpt[:240]},
                "hints": {
                    "id_fields": [],
                    "time_fields": [],
                    "pagination": (entry.get("hints") or {}).get("pagination"),
                    "known_units": (entry.get("hints") or {}).get("known_units") or {},
                },
                "confidence": entry.get("confidence") or "medium",
                "uncertainties": uncertainties,
            }
        )
    return {
        "schema_version": "ty-apm.catalog.v1",
        "catalog_version": "v1",
        "source": {
            "manual": "基调听云应用与微服务API说明.pdf",
            "product_version": "V3.9.0.0",
            "manual_version": "V1.07",
            "release": "2025-08",
        },
        "endpoints": endpoints,
    }


def main() -> int:
    source = Path("catalog/legacy-source.catalog.json")
    target = Path("catalog/tingyun-apm-api.catalog.json")
    if not source.exists():
        raise SystemExit("Place a PDF-derived legacy catalog at catalog/legacy-source.catalog.json first.")
    converted = convert(json.loads(source.read_text(encoding="utf-8")))
    target.write_text(json.dumps(converted, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
