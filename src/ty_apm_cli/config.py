from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppConfig:
    base_url: str = ""
    api_key: str = ""
    secret_key: str = ""
    artifacts_dir: Path = PROJECT_ROOT / "artifacts"
    catalog_path: Path = PROJECT_ROOT / "catalog" / "tingyun-apm-api.catalog.json"
    timeout_seconds: float = 10.0
    token_cache: bool = True


ENV_MAP = {
    "base_url": "TY_APM_BASE_URL",
    "api_key": "TY_APM_API_KEY",
    "secret_key": "TY_APM_SECRET_KEY",
    "artifacts_dir": "TY_APM_ARTIFACTS_DIR",
    "catalog_path": "TY_APM_CATALOG_PATH",
}


def _read_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        loaded = json.load(fh)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return loaded


def _path(value: Any) -> Path:
    return value if isinstance(value, Path) else Path(str(value))


def load_config(
    *,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    artifacts_dir: Optional[str] = None,
    catalog_path: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    no_token_cache: bool = False,
    config_path: Optional[str] = None,
) -> AppConfig:
    local_path = Path(config_path) if config_path else Path("config.local.json")
    data: Dict[str, Any] = _read_config(local_path)

    for field, env_name in ENV_MAP.items():
        value = os.getenv(env_name)
        if value:
            data[field] = value

    cli_values = {
        "base_url": base_url,
        "api_key": api_key,
        "secret_key": secret_key,
        "artifacts_dir": artifacts_dir,
        "catalog_path": catalog_path,
        "timeout_seconds": timeout_seconds,
    }
    for field, value in cli_values.items():
        if value not in (None, ""):
            data[field] = value

    cfg = AppConfig()
    clean = {
        key: _path(value) if key in {"artifacts_dir", "catalog_path"} else value
        for key, value in data.items()
        if key in AppConfig.__dataclass_fields__
    }
    if clean:
        cfg = replace(cfg, **clean)
    if no_token_cache:
        cfg = replace(cfg, token_cache=False)
    return cfg
