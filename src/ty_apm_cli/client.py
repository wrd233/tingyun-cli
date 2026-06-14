from __future__ import annotations

import re
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from .artifacts import RunRecorder
from .auth import AuthError, AuthManager
from .config import AppConfig
from .envelope import failure, new_request_id, now_iso, success
from .redact import redact
from .safety import UnsupportedSafetyLevel, assert_executable


class ApiCallError(RuntimeError):
    pass


class TingyunClient:
    def __init__(
        self,
        config: AppConfig,
        *,
        http_client: Optional[httpx.Client] = None,
        auth_manager: Optional[AuthManager] = None,
        recorder: Optional[RunRecorder] = None,
    ) -> None:
        self.config = config
        self.http_client = http_client
        self.auth_manager = auth_manager or AuthManager(config, http_client=http_client)
        self.recorder = recorder

    def call(self, endpoint: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = new_request_id()
        run_id = self.recorder.run_id if self.recorder else (self.config.run_id or "")
        source_api = {
            "catalog_id": endpoint.get("id"),
            "method": endpoint.get("method"),
            "path": endpoint.get("path"),
        }
        base_meta = {
            "request_id": request_id,
            "run_id": run_id,
            "source_api": source_api,
            "called_at": now_iso(),
        }

        try:
            assert_executable(endpoint)
        except UnsupportedSafetyLevel as exc:
            return failure(
                "api.call",
                "UnsupportedSafetyLevel",
                str(exc),
                retryable=False,
                meta={**base_meta, "catalog_id": exc.catalog_id, "safety": exc.safety},
            )

        if not self.config.base_url:
            return failure("api.call", "MissingConfig", "base_url is required", retryable=False, meta=base_meta)

        try:
            token = self.auth_manager.get_token().access_token
        except AuthError as exc:
            return failure("api.call", "AuthError", str(exc), retryable=True, meta=base_meta)

        method = str(endpoint.get("method", "GET")).upper()
        path_template = str(endpoint.get("path", ""))
        render_result = self._render_path(path_template, params)
        if render_result.get("error"):
            return failure(
                "api.call",
                "MissingPathParameter",
                render_result["error"],
                retryable=False,
                meta=base_meta,
            )
        path = render_result["path"]
        request_params = render_result["params"]
        url = f"{self.config.base_url.rstrip('/')}{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": endpoint.get("request", {}).get("content_type", "application/json"),
        }
        request_payload = {
            "method": method,
            "url": url,
            "headers": headers,
            "params": request_params if method == "GET" else {},
            "json": request_params if method != "GET" else None,
        }

        owns_client = self.http_client is None
        client = self.http_client or httpx.Client(timeout=self.config.timeout_seconds)
        raw_response: Any
        try:
            response = client.request(
                method,
                url,
                params=request_params if method == "GET" else None,
                json=request_params if method != "GET" else None,
                headers=headers,
            )
            try:
                raw_response = response.json()
            except ValueError:
                raw_response = {"text": response.text}
            meta = {**base_meta, "http_status": response.status_code}
            if response.status_code < 200 or response.status_code >= 300:
                envelope = failure(
                    "api.call",
                    "HttpError",
                    f"upstream returned HTTP {response.status_code}",
                    retryable=response.status_code >= 500,
                    meta=meta,
                    details={"response": raw_response},
                )
            else:
                envelope = success("api.call", data=raw_response, meta=meta)
        except httpx.HTTPError as exc:
            raw_response = {"error": str(exc)}
            envelope = failure("api.call", "NetworkError", str(exc), retryable=True, meta=base_meta)
        finally:
            if owns_client:
                client.close()

        if self.recorder:
            request_file, response_file, envelope_file = self.recorder.record_call(
                catalog_id=str(endpoint.get("id")),
                request=request_payload,
                raw_response=raw_response,
                envelope=envelope,
            )
            envelope.setdefault("meta", {}).update(
                {
                    "request_file": str(request_file),
                    "raw_file": str(response_file),
                    "envelope_file": str(envelope_file),
                }
            )
            self.recorder._write_json(envelope_file, redact(envelope))

        return envelope

    @staticmethod
    def _render_path(path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        remaining = dict(params)
        rendered = path
        for name in sorted(set(re.findall(r"{([^{}]+)}", path))):
            if name not in remaining:
                return {"error": f"path parameter '{name}' is required", "path": path, "params": params}
            value = quote(str(remaining.pop(name)), safe="")
            rendered = rendered.replace("{" + name + "}", value)
        return {"path": rendered, "params": remaining}
