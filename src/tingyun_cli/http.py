from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .config import Config
from .safety import assert_read_endpoint


class UrlLibTransport:
    def __init__(self, config: Config):
        self.config = config

    def send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        url = self.config.base_url + request["path"]
        if request.get("query"):
            url += "?" + urllib.parse.urlencode(request["query"])
        body = request.get("body")
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            if request.get("body_kind") == "json":
                data = json.dumps(body).encode("utf-8")
                headers["Content-Type"] = "application/json"
            else:
                data = urllib.parse.urlencode(body).encode("utf-8")
                headers["Content-Type"] = "application/x-www-form-urlencoded"
        if self.config.auth_value:
            headers[self.config.auth_header] = self.config.auth_value
        raw = urllib.request.Request(url, data=data, headers=headers, method=request["method"])
        try:
            with urllib.request.urlopen(raw, timeout=30) as response:
                text = response.read().decode("utf-8")
                parsed = json.loads(text) if text else {}
                if isinstance(parsed, dict):
                    parsed.setdefault("transport_status", response.status)
                return parsed
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = {"body": text}
            if isinstance(parsed, dict):
                parsed["transport_status"] = exc.code
            return parsed


@dataclass(frozen=True)
class ExecutionResult:
    outcome: str
    response: Optional[Dict[str, Any]]
    final_response_ref: Optional[str]
    final_error_ref: Optional[str]
    attempt_refs: Tuple[str, ...]
    attempt_count: int
    transient_retried: bool
    auth_recovered: bool
    reason_code: Optional[str] = None


class HttpExecutor:
    def __init__(self, *, store, run, config: Config, transport=None, clock: Any = time):
        self.store = store
        self.run = run
        self.config = config
        self.transport = transport or UrlLibTransport(config)
        self.clock = clock
        self.last_start: Optional[float] = None
        self.sequence = 0
        self.auth_recovered = False

    def execute(self, request: Dict[str, Any]) -> ExecutionResult:
        assert_read_endpoint(request["method"], request["path"])
        attempt_refs = []
        attempt = 0
        transient_retried = False
        auth_recovered_for_request = False
        while True:
            attempt += 1
            self._pace()
            self.sequence += 1
            request_id = f"request-{self.sequence:04d}"
            record = self._request_record(request_id, request, attempt)
            self.store.write_json(self.run.path / "raw" / f"{request_id}.json", record)
            request_ref = f"raw/{request_id}.json"
            attempt_refs.append(request_ref)
            try:
                response = self.transport.send(request)
            except (TimeoutError, ConnectionResetError, OSError) as exc:
                error_ref = f"raw/error-{self.sequence:04d}.json"
                self.store.write_json(self.run.path / error_ref, {
                    "request_id": request_id,
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                })
                attempt_refs.append(error_ref)
                if not transient_retried:
                    transient_retried = True
                    continue
                return ExecutionResult(
                    outcome="FAILED",
                    response=None,
                    final_response_ref=None,
                    final_error_ref=error_ref,
                    attempt_refs=tuple(attempt_refs),
                    attempt_count=attempt,
                    transient_retried=transient_retried,
                    auth_recovered=auth_recovered_for_request,
                    reason_code="TRANSPORT_ERROR",
                )
            response_ref = f"raw/response-{self.sequence:04d}.json"
            self.store.write_json(self.run.path / response_ref, {
                "request_id": request_id,
                "attempt": attempt,
                "response": response,
            })
            attempt_refs.append(response_ref)
            if self._is_auth_expired(response) and not self.auth_recovered:
                recovered = getattr(self.transport, "recover_auth", lambda: False)()
                if recovered:
                    self.auth_recovered = True
                    auth_recovered_for_request = True
                    continue
            if self._is_auth_expired(response):
                return ExecutionResult(
                    outcome="FAILED",
                    response=response,
                    final_response_ref=response_ref,
                    final_error_ref=None,
                    attempt_refs=tuple(attempt_refs),
                    attempt_count=attempt,
                    transient_retried=transient_retried,
                    auth_recovered=auth_recovered_for_request,
                    reason_code="AUTH_EXPIRED",
                )
            if self._is_transient_gateway_error(response) and not transient_retried:
                transient_retried = True
                continue
            failed, reason_code = self._failure_response(response)
            return ExecutionResult(
                outcome="FAILED" if failed else "SUCCESS",
                response=response,
                final_response_ref=response_ref,
                final_error_ref=None,
                attempt_refs=tuple(attempt_refs),
                attempt_count=attempt,
                transient_retried=transient_retried,
                auth_recovered=auth_recovered_for_request,
                reason_code=reason_code,
            )

    def _pace(self) -> None:
        now = self.clock.time()
        if self.last_start is not None:
            wait = self.config.min_request_interval_seconds - (now - self.last_start)
            if wait > 0:
                self.clock.sleep(wait)
                now = self.clock.time()
        self.last_start = now

    def _request_record(self, request_id: str, request: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        return {
            "request_id": request_id,
            "attempt": attempt,
            "endpoint_id": request.get("endpoint_id"),
            "variant_id": request.get("variant_id", "default"),
            "method": request["method"],
            "path": request["path"],
            "query": request.get("query", {}),
            "body": request.get("body", {}),
            "body_kind": request.get("body_kind", "form"),
            "metadata": {"headers_saved": False, "secret_headers_omitted": True},
        }

    def _is_transient_gateway_error(self, response: Dict[str, Any]) -> bool:
        status = response.get("transport_status", response.get("status"))
        return status in {502, 503, 504}

    def _is_auth_expired(self, response: Dict[str, Any]) -> bool:
        status = response.get("transport_status", response.get("status"))
        code = response.get("code")
        message = str(response.get("message") or response.get("msg") or "").upper()
        return status == 401 or code == "AUTH_EXPIRED" or "AUTH_EXPIRED" in message

    def _failure_response(self, response: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        status = response.get("transport_status", response.get("status"))
        if isinstance(status, int) and status >= 400:
            return True, "UPSTREAM_HTTP_ERROR"
        if response.get("success") is False:
            return True, "BUSINESS_ERROR"
        code = response.get("code")
        if isinstance(code, int) and code not in {0, 200}:
            return True, "BUSINESS_ERROR"
        if isinstance(code, str) and code.upper() not in {"", "OK", "SUCCESS", "0", "200"}:
            return True, "BUSINESS_ERROR"
        return False, None
