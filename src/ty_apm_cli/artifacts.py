from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Tuple

from .config import AppConfig
from .envelope import new_run_id, now_iso
from .redact import redact


class RunRecorder:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.run_id = config.run_id or new_run_id()
        self.root = Path(config.output_dir) / "runs" / self.run_id
        self.calls_dir = self.root / "calls"
        self.logs_dir = self.root / "logs"
        self.calls_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_run_file()

    def _ensure_run_file(self) -> None:
        run_file = self.root / "run.json"
        if run_file.exists():
            return
        with run_file.open("w", encoding="utf-8") as fh:
            json.dump({"run_id": self.run_id, "created_at": now_iso()}, fh, ensure_ascii=False, indent=2)

    def _next_index(self) -> int:
        return len(list(self.calls_dir.glob("*.request.json"))) + 1

    def record_call(
        self,
        *,
        catalog_id: str,
        request: Dict[str, Any],
        raw_response: Any,
        envelope: Dict[str, Any],
    ) -> Tuple[Path, Path, Path]:
        idx = self._next_index()
        safe_id = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in catalog_id)
        prefix = f"{idx:04d}_{safe_id}"
        request_file = self.calls_dir / f"{prefix}.request.json"
        response_file = self.calls_dir / f"{prefix}.response.raw.json"
        envelope_file = self.calls_dir / f"{prefix}.envelope.json"

        self._write_json(request_file, redact(request))
        self._write_json(response_file, redact(raw_response))
        self._write_json(envelope_file, redact(envelope))

        log_file = self.logs_dir / "calls.jsonl"
        log_row = {
            "recorded_at": now_iso(),
            "catalog_id": catalog_id,
            "request_file": str(request_file),
            "response_file": str(response_file),
            "envelope_file": str(envelope_file),
            "ok": envelope.get("ok"),
        }
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(log_row, ensure_ascii=False, sort_keys=True) + "\n")
        return request_file, response_file, envelope_file

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)

