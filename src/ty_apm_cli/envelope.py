from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .redact import redact

ENVELOPE_SCHEMA = "ty-apm.envelope.v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def request_id() -> str:
    return f"req_{uuid.uuid4().hex[:16]}"


def generated_run_id(prefix: str = "run") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{stamp}_{uuid.uuid4().hex[:8]}"


def success(
    command: str,
    data: Optional[Any] = None,
    *,
    meta: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": ENVELOPE_SCHEMA,
        "ok": True,
        "command": command,
        "data": {} if data is None else data,
        "meta": meta or {},
        "warnings": warnings or [],
    }


def failure(
    command: str,
    error_type: str,
    message: str,
    *,
    meta: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
    details: Optional[Dict[str, Any]] = None,
    retryable: Optional[bool] = None,
) -> Dict[str, Any]:
    error: Dict[str, Any] = {"type": error_type, "message": message}
    if retryable is not None:
        error["retryable"] = retryable
    if details:
        error["details"] = redact(details)
    return {
        "schema_version": ENVELOPE_SCHEMA,
        "ok": False,
        "command": command,
        "error": error,
        "meta": meta or {},
        "warnings": warnings or [],
    }


def emit(envelope: Dict[str, Any]) -> int:
    sys.stdout.write(json.dumps(redact(envelope), ensure_ascii=False, sort_keys=True) + "\n")
    return 0 if envelope.get("ok") else 1
