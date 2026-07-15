#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tingyun_cli.research import build_research_view, diff_research_views, render_research_markdown


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate, check, or diff deterministic Tingyun Research Views.")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("generate", "check"):
        command = sub.add_parser(name)
        command.add_argument("--protocol-root", type=Path, default=ROOT / "research" / "protocol")
        command.add_argument("--output-dir", type=Path, default=ROOT / "research" / "generated")
    diff = sub.add_parser("diff")
    diff.add_argument("--before", type=Path, required=True)
    diff.add_argument("--after", type=Path, required=True)
    diff.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    if args.command == "diff":
        result = diff_research_views(_read_json(args.before), _read_json(args.after))
        encoded = _json_bytes(result)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(encoded)
        sys.stdout.write(encoded.decode("utf-8"))
        return 0

    view = build_research_view(args.protocol_root)
    expected = {
        args.output_dir / "research-index.json": _json_bytes(view),
        args.output_dir / "research-overview.md": render_research_markdown(view).encode("utf-8"),
    }
    if args.command == "generate":
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for path, content in expected.items():
            path.write_bytes(content)
        result = {"schema_version": 1, "command": "research generate", "status": view["health"]["status"], "outputs": [str(path) for path in sorted(expected)]}
    else:
        drift = [str(path) for path, content in expected.items() if not path.exists() or path.read_bytes() != content]
        result = {"schema_version": 1, "command": "research check", "status": "FAIL" if drift or view["health"]["status"] != "PASS" else "PASS", "drift": sorted(drift), "health": view["health"]}
    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    return 0 if result["status"] == "PASS" else 1


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
