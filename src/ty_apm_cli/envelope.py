from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import typer

from .redact import redact


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def new_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:16]}"


def new_run_id() -> str:
    return f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"


def success(
    command: str,
    data: Optional[Any] = None,
    meta: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
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
    retryable: bool = False,
    meta: Optional[Dict[str, Any]] = None,
    warnings: Optional[List[str]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    error = {
        "type": error_type,
        "message": message,
        "retryable": retryable,
    }
    if details:
        error["details"] = redact(details)
    return {
        "ok": False,
        "command": command,
        "error": error,
        "meta": meta or {},
        "warnings": warnings or [],
    }


def emit(envelope: Dict[str, Any]) -> None:
    typer.echo(json.dumps(redact(envelope), ensure_ascii=False, indent=2, sort_keys=True))

