from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from .auth import AuthError, AuthManager
from .config import AppConfig
from .envelope import failure, now_iso, request_id, success
from .redact import redact
from .safety import SafetyBlocked, assert_read_executable


@dataclass
class CallRecord:
    envelope: Dict[str, Any]
    request: Dict[str, Any]
    response: Any
    duration_ms: int
    http_status: Optional[int]
    upstream_code: Optional[Any]


class TingyunClient:
    def __init__(
        self,
        config: AppConfig,
        *,
        catalog_ref: Optional[Dict[str, Any]] = None,
        http_client: Optional[httpx.Client] = None,
        auth_manager: Optional[AuthManager] = None,
    ) -> None:
        self.config = config
        self.catalog_ref = catalog_ref or {}
        self.http_client = http_client
        self.auth_manager = auth_manager or AuthManager(config, http_client=http_client)

    def call(self, entry: Dict[str, Any], params: Dict[str, Any], *, command: str = "api.call") -> CallRecord:
        meta = {
            "request_id": request_id(),
            "run_id": None,
            "catalog_id": entry.get("id"),
            "catalog_ref": self.catalog_ref,
        }
        try:
            assert_read_executable(entry)
            self._validate_params(entry, params)
            if not self.config.base_url:
                raise ValueError("base_url is required")
            token = self.auth_manager.get_token().access_token
        except SafetyBlocked as exc:
            env = failure(command, "SafetyBlocked", str(exc), meta=meta, retryable=False)
            return CallRecord(env, {}, {}, 0, None, None)
        except AuthError as exc:
            env = failure(command, "AuthError", str(exc), meta=meta, retryable=True)
            return CallRecord(env, {}, {}, 0, None, None)
        except ValueError as exc:
            env = failure(command, "ValidationError", str(exc), meta=meta, retryable=False)
            return CallRecord(env, {}, {}, 0, None, None)

        method = str(entry.get("method", "GET")).upper()
        render = self._render_path(str(entry.get("path", "")), params)
        if render.get("error"):
            env = failure(command, "ValidationError", render["error"], meta=meta, retryable=False)
            return CallRecord(env, {}, {}, 0, None, None)

        url = f"{self.config.base_url.rstrip('/')}{render['path']}"
        body_params = render["params"]
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        if method != "GET":
            headers["Content-Type"] = "application/json"
        request_payload = {
            "method": method,
            "url": url,
            "headers": headers,
            "params": body_params if method == "GET" else {},
            "json": body_params if method != "GET" else None,
        }

        owns_client = self.http_client is None
        client = self.http_client or httpx.Client(timeout=self.config.timeout_seconds)
        start = time.monotonic()
        raw: Any = {}
        status: Optional[int] = None
        upstream_code: Optional[Any] = None
        try:
            response = client.request(
                method,
                url,
                params=body_params if method == "GET" else None,
                json=body_params if method != "GET" else None,
                headers=headers,
            )
            status = response.status_code
            try:
                raw = response.json()
            except ValueError:
                raw = {"text": response.text}
            upstream_code = self._upstream_code(raw)
            if status < 200 or status >= 300:
                env = failure(
                    command,
                    "HttpError",
                    f"upstream returned HTTP {status}",
                    meta={**meta, "http_status": status, "upstream_code": upstream_code},
                    details={"response": raw},
                    retryable=status >= 500,
                )
            elif upstream_code not in (None, 0, 200, "0", "200", "success", "SUCCESS"):
                env = failure(
                    command,
                    "UpstreamError",
                    "upstream business code was not success",
                    meta={**meta, "http_status": status, "upstream_code": upstream_code},
                    details={"response": raw},
                    retryable=False,
                )
            else:
                env = success(
                    command,
                    {"catalog_id": entry.get("id"), "response": raw},
                    meta={**meta, "http_status": status, "upstream_code": upstream_code, "called_at": now_iso()},
                )
        except httpx.TimeoutException as exc:
            raw = {"error": str(exc)}
            env = failure(command, "TimeoutError", "request timed out", meta=meta, retryable=True)
        except httpx.HTTPError as exc:
            raw = {"error": str(exc)}
            env = failure(command, "HttpError", "request failed", meta=meta, retryable=True)
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            if owns_client:
                client.close()

        return CallRecord(env, redact(request_payload), redact(raw), duration_ms, status, upstream_code)

    def _validate_params(self, entry: Dict[str, Any], params: Dict[str, Any]) -> None:
        required = [
            p.get("name")
            for p in entry.get("request", {}).get("params", [])
            if p.get("required") is True and p.get("name")
        ]
        missing = [name for name in required if name not in params]
        if missing:
            raise ValueError(f"missing required parameter(s): {', '.join(missing)}")

    @staticmethod
    def _render_path(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        remaining = dict(params)
        rendered = path
        for name in sorted(set(re.findall(r"{([^{}]+)}", path))):
            if name not in remaining:
                return {"error": f"path parameter '{name}' is required", "path": path, "params": params}
            rendered = rendered.replace("{" + name + "}", quote(str(remaining.pop(name)), safe=""))
        return {"path": rendered, "params": remaining}

    @staticmethod
    def _upstream_code(payload: Any) -> Optional[Any]:
        if isinstance(payload, dict):
            for key in ("code", "status", "resultCode"):
                if key in payload:
                    return payload[key]
        return None
