from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict


SUPPORTED_RELATIVE = {
    "last_30m": 30,
    "last_60m": 60,
}


def resolve_time_context(value: str, clock: Any = time) -> Dict[str, Any]:
    if ".." in value:
        return _resolve_exact_range(value)
    if value not in SUPPORTED_RELATIVE:
        raise ValueError("UNSUPPORTED_TIME_SHAPE")
    minutes = SUPPORTED_RELATIVE[value]
    end_epoch = clock.time()
    start_epoch = end_epoch - (minutes * 60)
    return {
        "requested": {"kind": "relative", "value": value},
        "resolved": {
            "start_epoch_ms": int(start_epoch * 1000),
            "end_epoch_ms": int(end_epoch * 1000),
            "start_time": _format_minute(start_epoch),
            "end_time": _format_minute(end_epoch),
        },
        "endpoint": {
            "timePeriod": minutes,
            "endTime": _format_minute(end_epoch),
        },
    }


def _resolve_exact_range(value: str) -> Dict[str, Any]:
    raw_start, raw_end = value.split("..", 1)
    try:
        start = datetime.fromisoformat(raw_start)
        end = datetime.fromisoformat(raw_end)
    except ValueError as exc:
        raise ValueError("UNSUPPORTED_TIME_SHAPE") from exc
    if end <= start:
        raise ValueError("UNSUPPORTED_TIME_SHAPE")
    if any((start.second, start.microsecond, end.second, end.microsecond)):
        raise ValueError("UNSUPPORTED_TIME_SHAPE")
    delta = end - start
    minutes = int(delta.total_seconds() // 60)
    if minutes * 60 != int(delta.total_seconds()):
        raise ValueError("UNSUPPORTED_TIME_SHAPE")
    return {
        "requested": {"kind": "exact_range", "value": value},
        "resolved": {
            "start_epoch_ms": int(start.timestamp() * 1000),
            "end_epoch_ms": int(end.timestamp() * 1000),
            "start_time": start.strftime("%Y-%m-%d %H:%M"),
            "end_time": end.strftime("%Y-%m-%d %H:%M"),
        },
        "endpoint": {
            "timePeriod": minutes,
            "endTime": end.strftime("%Y-%m-%d %H:%M"),
        },
    }


def _format_minute(epoch_seconds: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(epoch_seconds))
