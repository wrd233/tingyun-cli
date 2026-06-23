from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

from .config import AppConfig
from .redact import redact_url

TOKEN_TTL_SECONDS = 2 * 60 * 60
TOKEN_REFRESH_SKEW_SECONDS = 5 * 60


class AuthError(RuntimeError):
    pass


def build_auth_source(api_key: str, secret_key: str, timestamp_ms: int) -> str:
    return f'api_key="{api_key}"&secret_key="{secret_key}"&timestamp="{timestamp_ms}"'


def build_auth_signature(api_key: str, secret_key: str, timestamp_ms: int) -> str:
    return hashlib.md5(build_auth_source(api_key, secret_key, timestamp_ms).encode("utf-8")).hexdigest().lower()


@dataclass(frozen=True)
class TokenResult:
    access_token: str
    expires_at: float
    from_cache: bool


class AuthManager:
    def __init__(self, config: AppConfig, http_client: Optional[httpx.Client] = None) -> None:
        self.config = config
        self.http_client = http_client

    @property
    def cache_file(self) -> Path:
        return Path(self.config.token_cache_path)

    def clear_token(self) -> bool:
        if self.cache_file.exists():
            self.cache_file.unlink()
            return True
        return False

    def get_token(self, *, force_refresh: bool = False) -> TokenResult:
        if self.config.token_cache and not force_refresh:
            cached = self._load_cache()
            if cached:
                return cached
        return self._fetch_token()

    def _load_cache(self) -> Optional[TokenResult]:
        try:
            with self.cache_file.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return None
        token = payload.get("access_token")
        expires_at = float(payload.get("expires_at") or 0)
        if token and expires_at - TOKEN_REFRESH_SKEW_SECONDS > time.time():
            return TokenResult(str(token), expires_at, True)
        return None

    def _write_cache(self, token: str, expires_at: float) -> None:
        if not self.config.token_cache:
            return
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_file.open("w", encoding="utf-8") as fh:
            json.dump({"access_token": token, "expires_at": expires_at}, fh, ensure_ascii=False, sort_keys=True)

    def _fetch_token(self) -> TokenResult:
        if not self.config.base_url:
            raise AuthError("base_url is required")
        if not self.config.api_key or not self.config.secret_key:
            raise AuthError("api_key and secret_key are required")

        timestamp = int(time.time() * 1000)
        signature = build_auth_signature(self.config.api_key, self.config.secret_key, timestamp)
        url = f"{self.config.base_url.rstrip('/')}/auth-api/auth/token"
        params = {"api_key": self.config.api_key, "auth": signature, "timestamp": str(timestamp)}
        owns_client = self.http_client is None
        client = self.http_client or httpx.Client(timeout=self.config.timeout_seconds)
        try:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload: Dict[str, Any] = response.json()
        except Exception as exc:
            safe_url = redact_url(str(httpx.URL(url, params=params)))
            raise AuthError(f"token request failed for {safe_url}") from exc
        finally:
            if owns_client:
                client.close()

        token = payload.get("access_token") or payload.get("data", {}).get("access_token")
        code = payload.get("code")
        if code not in (None, 0, 200, "0", "200") and not token:
            raise AuthError("token response returned an upstream failure")
        if not token:
            raise AuthError("token response did not contain access_token")
        expires_at = time.time() + TOKEN_TTL_SECONDS
        self._write_cache(str(token), expires_at)
        return TokenResult(str(token), expires_at, False)
