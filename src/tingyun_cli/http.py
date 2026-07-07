from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

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


class HttpExecutor:
    def __init__(self, *, store, run, config: Config, transport=None, clock: Any = time):
        self.store = store
        self.run = run
        self.config = config
        self.transport = transport or UrlLibTransport(config)
        self.clock = clock
        self.last_start: Optional[float] = None
        self.sequence = 0

    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        assert_read_endpoint(request["method"], request["path"])
        last_error: Optional[BaseException] = None
        attempt = 0
        transient_retried = False
        auth_recovered = False
        while True:
            attempt += 1
            self._pace()
            self.sequence += 1
            request_id = f"request-{self.sequence:04d}"
            record = self._request_record(request_id, request, attempt)
            self.store.write_json(self.run.path / "raw" / f"{request_id}.json", record)
            try:
                response = self.transport.send(request)
            except (TimeoutError, ConnectionResetError, OSError) as exc:
                last_error = exc
                self.store.write_json(self.run.path / "raw" / f"error-{self.sequence:04d}.json", {
                    "request_id": request_id,
                    "attempt": attempt,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                })
                if not transient_retried:
                    transient_retried = True
                    continue
                raise
            self.store.write_json(self.run.path / "raw" / f"response-{self.sequence:04d}.json", {
                "request_id": request_id,
                "attempt": attempt,
                "response": response,
            })
            if self._is_auth_expired(response) and not auth_recovered:
                recovered = getattr(self.transport, "recover_auth", lambda: False)()
                if recovered:
                    auth_recovered = True
                    continue
            if self._is_transient_gateway_error(response) and not transient_retried:
                transient_retried = True
                continue
            return response
        if last_error:
            raise last_error
        raise RuntimeError("request execution failed without response")

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
        return isinstance(status, int) and 500 <= status <= 599

    def _is_auth_expired(self, response: Dict[str, Any]) -> bool:
        status = response.get("transport_status", response.get("status"))
        code = response.get("code")
        message = str(response.get("message") or response.get("msg") or "").upper()
        return status == 401 or code == "AUTH_EXPIRED" or "AUTH_EXPIRED" in message
