from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .safety import audit_entry


class CatalogNotFound(RuntimeError):
    pass


class Catalog:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        with self.path.open("r", encoding="utf-8") as fh:
            self.document = json.load(fh)
        self.entries: List[Dict[str, Any]] = list(self.document.get("endpoints", []))
        self.by_id = {entry["id"]: entry for entry in self.entries}

    def ref(self) -> Dict[str, Any]:
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        return {
            "catalog_version": str(self.document.get("catalog_version", "v1")),
            "catalog_commit": self._git_commit(),
            "catalog_file_hash": f"sha256:{digest}",
        }

    def _git_commit(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(self.path.resolve().parents[1]),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

    def get(self, catalog_id: str) -> Dict[str, Any]:
        try:
            return self.by_id[catalog_id]
        except KeyError as exc:
            raise CatalogNotFound(f"unknown catalog id: {catalog_id}") from exc

    def summaries(self, entries: Optional[Iterable[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        rows = []
        for entry in entries if entries is not None else self.entries:
            rows.append(
                {
                    "id": entry.get("id"),
                    "domain": entry.get("domain"),
                    "title": entry.get("title"),
                    "method": entry.get("method"),
                    "path": entry.get("path"),
                    "safety": entry.get("safety"),
                    "execution_supported": entry.get("execution_supported"),
                    "confidence": entry.get("confidence"),
                }
            )
        return rows

    def search(self, keyword: str) -> List[Dict[str, Any]]:
        needle = keyword.lower()
        return [
            entry
            for entry in self.entries
            if needle
            in " ".join(str(entry.get(key, "")) for key in ("id", "domain", "title", "section", "path")).lower()
        ]

    def filter(self, *, safety: Optional[str] = None, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        entries = self.entries
        if safety:
            entries = [entry for entry in entries if entry.get("safety") == safety]
        if domain:
            entries = [entry for entry in entries if entry.get("domain") == domain]
        return entries

    def audit_safety(self) -> Dict[str, Any]:
        issues = []
        for entry in self.entries:
            issues.extend(audit_entry(entry))
        return {"ok": not issues, "issue_count": len(issues), "issues": issues, "stats": self.stats()}

    def stats(self) -> Dict[str, Any]:
        return {
            "endpoint_count": len(self.entries),
            "safety_counts": dict(sorted(Counter(e.get("safety", "unknown") for e in self.entries).items())),
            "domain_counts": dict(sorted(Counter(e.get("domain", "unknown") for e in self.entries).items())),
        }
