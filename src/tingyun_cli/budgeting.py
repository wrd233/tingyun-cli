from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Set


@dataclass(frozen=True)
class RequestBudget:
    max_live_requests: int
    min_request_interval_seconds: float = 2.0
    heavy_request_interval_seconds: float = 5.0
    max_narrowing_steps: int = 3
    concurrency: int = 1


@dataclass(frozen=True)
class RequestCacheKey:
    endpoint_id: str
    params_hash: str
    scope_hash: str
    time_window_hash: str


class RequestLedger:
    """A local planning ledger. It never sends, schedules, or throttles requests."""

    def __init__(self, budget: RequestBudget):
        self.budget = budget
        self.actual_live_requests = 0
        self.reused_request_count = 0
        self._reused_keys: Set[RequestCacheKey] = set()

    def try_live_request(self, reason: str) -> Dict[str, Any]:
        if self.actual_live_requests >= self.budget.max_live_requests:
            return {"status": "BLOCKED", "reason_code": "REQUEST_BUDGET_EXCEEDED", "reason": reason, "budget": self.summary()}
        self.actual_live_requests += 1
        return {"status": "ALLOW", "reason": reason, "budget": self.summary()}

    def try_reuse(self, key: RequestCacheKey, *, reused_from_run_id: str) -> Dict[str, Any]:
        if key not in self._reused_keys:
            self._reused_keys.add(key)
            self.reused_request_count += 1
        return {
            "status": "REUSED",
            "reused_from_run_id": reused_from_run_id,
            "cache_key": {
                "endpoint_id": key.endpoint_id,
                "params_hash": key.params_hash,
                "scope_hash": key.scope_hash,
                "time_window_hash": key.time_window_hash,
            },
            "budget": self.summary(),
        }

    def summary(self) -> Dict[str, Any]:
        return {
            "max_live_requests": self.budget.max_live_requests,
            "actual_live_requests": self.actual_live_requests,
            "reused_request_count": self.reused_request_count,
            "budget_remaining": max(0, self.budget.max_live_requests - self.actual_live_requests),
        }
