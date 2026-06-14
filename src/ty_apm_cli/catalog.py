from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .safety import audit_endpoint


class CatalogError(RuntimeError):
    pass


class Catalog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        with self.path.open("r", encoding="utf-8") as fh:
            self.document = json.load(fh)
        self.endpoints: List[Dict[str, Any]] = list(self.document.get("endpoints", []))
        self._by_id = {endpoint["id"]: endpoint for endpoint in self.endpoints}

    def get(self, catalog_id: str) -> Dict[str, Any]:
        try:
            return self._by_id[catalog_id]
        except KeyError as exc:
            raise CatalogError(f"unknown catalog id: {catalog_id}") from exc

    def find_by_path(self, path: str, *, title_contains: Optional[str] = None) -> Dict[str, Any]:
        matches = [endpoint for endpoint in self.endpoints if endpoint.get("path") == path]
        if title_contains:
            narrowed = [endpoint for endpoint in matches if title_contains in endpoint.get("title", "")]
            if narrowed:
                matches = narrowed
        if not matches:
            raise CatalogError(f"no catalog endpoint for path: {path}")
        return matches[0]

    def summaries(self, endpoints: Optional[Iterable[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        rows = []
        for endpoint in endpoints if endpoints is not None else self.endpoints:
            rows.append(
                {
                    "id": endpoint.get("id"),
                    "title": endpoint.get("title"),
                    "domain": endpoint.get("domain"),
                    "method": endpoint.get("method"),
                    "path": endpoint.get("path"),
                    "safety": endpoint.get("safety"),
                    "confidence": endpoint.get("confidence"),
                    "execution_supported": endpoint.get("execution_supported"),
                }
            )
        return rows

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        needle = keyword.lower()
        return [
            endpoint
            for endpoint in self.endpoints
            if needle
            in " ".join(
                str(endpoint.get(key, "")) for key in ("id", "title", "domain", "capability", "path", "description")
            ).lower()
        ]

    def filter(
        self,
        *,
        domain: Optional[str] = None,
        safety: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        endpoints = self.endpoints
        if domain:
            endpoints = [endpoint for endpoint in endpoints if endpoint.get("domain") == domain]
        if safety:
            endpoints = [endpoint for endpoint in endpoints if endpoint.get("safety") == safety]
        if confidence:
            endpoints = [endpoint for endpoint in endpoints if endpoint.get("confidence") == confidence]
        return endpoints

    def audit_safety(self) -> Dict[str, Any]:
        issues = []
        for endpoint in self.endpoints:
            issues.extend(audit_endpoint(endpoint))
        return {"ok": len(issues) == 0, "issue_count": len(issues), "issues": issues}

    def test_plan(self) -> Dict[str, Any]:
        priority = Counter(endpoint.get("test", {}).get("priority", "unknown") for endpoint in self.endpoints)
        read = [
            endpoint
            for endpoint in self.endpoints
            if endpoint.get("safety") == "read" and endpoint.get("execution_supported")
        ]
        blocked = [
            endpoint
            for endpoint in self.endpoints
            if endpoint.get("safety") in {"guarded", "write", "unknown"}
        ]
        return {
            "offline": [
                "catalog schema validation",
                "unique catalog ids",
                "safety audit",
                "JSON envelope shape",
                "redaction",
            ],
            "mock": [
                "token fetch/cache/refresh",
                "Authorization header redaction",
                "read API call",
                "artifact files",
                "non-read refusal",
            ],
            "live": "deferred",
            "priority_counts": dict(priority),
            "read_mock_candidates": [endpoint["id"] for endpoint in read[:20]],
            "blocked_sample": [endpoint["id"] for endpoint in blocked[:20]],
        }

    def stats(self) -> Dict[str, Any]:
        safety_counts = Counter(endpoint.get("safety", "unknown") for endpoint in self.endpoints)
        domain_counts = Counter(endpoint.get("domain", "unknown") for endpoint in self.endpoints)
        confidence_counts = Counter(endpoint.get("confidence", "unknown") for endpoint in self.endpoints)
        return {
            "endpoint_count": len(self.endpoints),
            "safety_counts": dict(sorted(safety_counts.items())),
            "domain_counts": dict(sorted(domain_counts.items())),
            "confidence_counts": dict(sorted(confidence_counts.items())),
        }

