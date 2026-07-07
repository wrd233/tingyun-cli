from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Config:
    base_url: str
    data_root: Path
    min_request_interval_seconds: float = 2.0
    auth_header: str = "Authorization"
    auth_env: str = "TINGYUN_AUTHORIZATION"

    @property
    def auth_value(self) -> Optional[str]:
        return os.environ.get(self.auth_env)


def load_config(path: Optional[Path] = None, *, data_root: Optional[Path] = None) -> Config:
    values = {}
    if path:
        values = json.loads(Path(path).read_text(encoding="utf-8"))
    root = data_root or Path(values.get("data_root") or os.environ.get("TINGYUN_DATA_ROOT", ".tingyun-runs"))
    base_url = values.get("base_url") or os.environ.get("TINGYUN_BASE_URL", "")
    return Config(
        base_url=base_url.rstrip("/"),
        data_root=Path(root),
        min_request_interval_seconds=float(values.get("min_request_interval_seconds", 2.0)),
        auth_header=values.get("auth_header", "Authorization"),
        auth_env=values.get("auth_env", "TINGYUN_AUTHORIZATION"),
    )
