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
    output_dir: Path = Path("./artifacts")
    catalog_path: Path = PROJECT_ROOT / "catalog" / "tingyun-apm-api.catalog.json"
    run_id: str = ""
    token_cache: bool = True
    timeout_seconds: float = 30.0


ENV_MAP = {
    "base_url": "TY_APM_BASE_URL",
    "api_key": "TY_APM_API_KEY",
    "secret_key": "TY_APM_SECRET_KEY",
    "output_dir": "TY_APM_OUTPUT_DIR",
    "catalog_path": "TY_APM_CATALOG_PATH",
}


def _read_local_config(path: Path) -> Dict[str, Any]:
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
    output_dir: Optional[str] = None,
    catalog_path: Optional[str] = None,
    run_id: Optional[str] = None,
    no_token_cache: bool = False,
    config_path: Optional[str] = None,
) -> AppConfig:
    config_file = Path(config_path) if config_path else Path("config.local.json")
    local = _read_local_config(config_file)
    data: Dict[str, Any] = {}

    for field in AppConfig.__dataclass_fields__:
        if field in local:
            data[field] = local[field]

    for field, env_name in ENV_MAP.items():
        value = os.getenv(env_name)
        if value:
            data[field] = value

    cli_values = {
        "base_url": base_url,
        "api_key": api_key,
        "secret_key": secret_key,
        "output_dir": output_dir,
        "catalog_path": catalog_path,
        "run_id": run_id,
    }
    for field, value in cli_values.items():
        if value not in (None, ""):
            data[field] = value

    cfg = AppConfig()
    if data:
        cfg = replace(
            cfg,
            **{
                key: _path(value) if key in {"output_dir", "catalog_path"} else value
                for key, value in data.items()
                if key in AppConfig.__dataclass_fields__
            },
        )
    if no_token_cache:
        cfg = replace(cfg, token_cache=False)
    return cfg

