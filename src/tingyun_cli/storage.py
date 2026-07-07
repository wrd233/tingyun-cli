from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RunHandle:
    run_id: str
    path: Path
    command: str
    run_type: str


class RunStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.runs_dir = self.root / "runs"
        self.inflight_dir = self.root / ".inflight"
        self.exports_dir = self.root / "exports"
        self.index_path = self.root / "runs.jsonl"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.inflight_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.index_path.touch(exist_ok=True)

    def acquire_live_lock(self) -> bool:
        lock_path = self.root / "live.lock"
        if lock_path.exists():
            try:
                payload = json.loads(lock_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                payload = {}
            pid = payload.get("pid")
            if pid and self._pid_is_alive(int(pid)):
                return False
            lock_path.unlink(missing_ok=True)
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "created_at": self._now_iso()}, sort_keys=True))
        return True

    def release_live_lock(self) -> None:
        lock_path = self.root / "live.lock"
        if not lock_path.exists():
            return
        try:
            payload = json.loads(lock_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        if payload.get("pid") == os.getpid():
            lock_path.unlink(missing_ok=True)

    def begin_run(self, *, command: str, run_type: str, pid: Optional[int] = None) -> RunHandle:
        run_id = self._new_run_id()
        path = self.inflight_dir / run_id
        path.mkdir(parents=False, exist_ok=False)
        self.write_json(path / "run-meta.json", {
            "run_id": run_id,
            "command": command,
            "run_type": run_type,
            "pid": os.getpid() if pid is None else pid,
            "started_at": self._now_iso(),
        })
        return RunHandle(run_id=run_id, path=path, command=command, run_type=run_type)

    def write_json(self, path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(temp, path)

    def read_json(self, path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def finalize_run(self, run: RunHandle, *, manifest: Dict[str, Any], coverage: Dict[str, Any]) -> Path:
        self.write_json(run.path / "coverage.json", coverage)
        self.write_json(run.path / "manifest.json", manifest)
        return self.finalize_existing_inflight(run)

    def finalize_existing_inflight(self, run: RunHandle) -> Path:
        destination = self.runs_dir / run.run_id
        if destination.exists():
            raise FileExistsError(f"run already exists: {run.run_id}")
        os.replace(run.path, destination)
        manifest_path = destination / "manifest.json"
        if manifest_path.exists():
            manifest = self.read_json(manifest_path)
            self._append_index({
                "timestamp": self._now_iso(),
                "command": run.command,
                "status": manifest.get("overall"),
                "run_id": run.run_id,
                "run_type": manifest.get("run_type", run.run_type),
                "source_run_id": (manifest.get("source") or {}).get("run_id"),
                "source_item_ref": (manifest.get("source") or {}).get("item_ref"),
                "requested_action": manifest.get("action"),
                "reason_code": manifest.get("reason_code"),
                "live_request_count": manifest.get("live_request_count", 0),
                "manifest_path": str(manifest_path),
            })
        return destination

    def freeze_stale_inflight(self) -> List[str]:
        frozen: List[str] = []
        for path in sorted(self.inflight_dir.iterdir()):
            if not path.is_dir():
                continue
            meta_path = path / "run-meta.json"
            meta = self.read_json(meta_path) if meta_path.exists() else {}
            pid = meta.get("pid")
            if pid and self._pid_is_alive(int(pid)):
                continue
            run = RunHandle(
                run_id=path.name,
                path=path,
                command=meta.get("command", "unknown"),
                run_type=meta.get("run_type", "INTERRUPTED"),
            )
            coverage = {
                "schema_version": 1,
                "overall": "INTERRUPTED",
                "artifacts": {},
                "reason_code": "STALE_INFLIGHT",
            }
            manifest = {
                "schema_version": 1,
                "run_id": run.run_id,
                "run_type": "INTERRUPTED",
                "overall": "INTERRUPTED",
                "reason_code": "STALE_INFLIGHT",
                "artifacts": [],
                "coverage_ref": "coverage.json",
                "live_request_count": 0,
            }
            self.write_json(path / "coverage.json", coverage)
            self.write_json(path / "manifest.json", manifest)
            self.finalize_existing_inflight(run)
            frozen.append(run.run_id)
        return frozen

    def run_path(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def _append_index(self, data: Dict[str, Any]) -> None:
        with self.index_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")

    def _new_run_id(self) -> str:
        stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime())
        suffix = f"{time.time_ns() % 1_000_000_000:09d}"
        return f"run-{stamp}-{suffix}"

    def _now_iso(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _pid_is_alive(self, pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True


def remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
