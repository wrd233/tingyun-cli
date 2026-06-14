from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import urlsplit

from pypdf import PdfReader


DEFAULT_PDF = Path("/Users/wangrundong/Downloads/基调听云应用与微服务API说明.pdf")
PRODUCT_VERSION = "V3.9.0.0"
MANUAL_VERSION = "V1.07"
RELEASE_DATE = "2025-08"


@dataclass
class Line:
    index: int
    page: int
    line: int
    text: str


@dataclass
class Candidate:
    kind: str
    title_index: int
    method_index: int
    path_index: int
    method: str
    path: str
    title: str
    section: str


def extract_lines(pdf_path: Path) -> List[Line]:
    reader = PdfReader(str(pdf_path))
    lines: List[Line] = []
    index = 0
    for page_no, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        for line_no, raw in enumerate(text.splitlines(), 1):
            text_line = " ".join(raw.strip().split())
            lines.append(Line(index=index, page=page_no, line=line_no, text=text_line))
            index += 1
    return lines


def normalize_path(raw: str) -> str:
    text = raw.strip().strip("`'\"<>，。；、")
    method_match = re.match(r"^(GET|POST|PUT|DELETE|PATCH)\s+(.+)$", text, re.IGNORECASE)
    if method_match:
        text = method_match.group(2)
    if text.startswith("http://") or text.startswith("https://"):
        parts = urlsplit(text)
        text = parts.path + (f"?{parts.query}" if parts.query else "")
    text = text.strip().strip("`'\"<>，。；、")
    return text


def is_api_path(path: str) -> bool:
    return path.startswith(("/server-api/", "/server-config/", "/alarm-api/"))


def clean_title(text: str) -> str:
    title = re.sub(r"^\d+(?:\.\d+)*\s+", "", text).strip()
    title = re.sub(r"\.{3,}\s*\d+\s*$", "", title).strip()
    return title or text.strip()


def is_noise_title(text: str) -> bool:
    if not text or text.isdigit():
        return True
    if text in {"说明", "请求参数", "响应参数", "示例", "错误码", "接口地址", "接口说明"}:
        return True
    if re.match(r"^\d+$", text):
        return True
    if re.match(r"^[A-Za-z]*\s*\d+$", text):
        return True
    return False


def previous_title_index(lines: Sequence[Line], start: int) -> int:
    for idx in range(start, max(-1, start - 30), -1):
        text = lines[idx].text
        if is_noise_title(text):
            continue
        if any(marker in text for marker in ("请求示例", "返回示例", "响应示例", "请求参数", "响应参数")):
            continue
        if text.startswith(("curl ", "HTTP/")):
            continue
        return idx
    return start


def nearest_section(lines: Sequence[Line], title_idx: int, path_idx: int, inline_heading_idx: Optional[int] = None) -> str:
    if inline_heading_idx is not None:
        match = re.match(r"^(\d+(?:\.\d+)+)\.\d+\s+接口地址", lines[inline_heading_idx].text)
        if match:
            return match.group(1)
    title_match = re.match(r"^(\d+(?:\.\d+)*)\s+", lines[title_idx].text)
    if title_match and len(title_match.group(1).split(".")) >= 2:
        return title_match.group(1)
    for idx in range(path_idx + 1, min(path_idx + 12, len(lines))):
        match = re.match(r"^(\d+(?:\.\d+)+)\.\d+\s+(说明|接口说明|请求参数|响应参数)", lines[idx].text)
        if match:
            return match.group(1)
    for idx in range(title_idx, max(-1, title_idx - 40), -1):
        match = re.match(r"^(\d+(?:\.\d+)*)\s+", lines[idx].text)
        if match and len(match.group(1).split(".")) >= 2:
            return match.group(1)
    return ""


def find_candidates(lines: Sequence[Line]) -> List[Candidate]:
    candidates: List[Candidate] = []
    for idx, line in enumerate(lines):
        method_match = re.search(r"方法[:：]\s*(GET|POST|PUT|DELETE|PATCH)", line.text, re.IGNORECASE)
        if method_match:
            for path_idx in range(idx + 1, min(idx + 6, len(lines))):
                path = normalize_path(lines[path_idx].text)
                if is_api_path(path):
                    title_idx = previous_title_index(lines, idx - 1)
                    section = nearest_section(lines, title_idx, path_idx)
                    candidates.append(
                        Candidate(
                            kind="method",
                            title_index=title_idx,
                            method_index=idx,
                            path_index=path_idx,
                            method=method_match.group(1).upper(),
                            path=path,
                            title=clean_title(lines[title_idx].text),
                            section=section,
                        )
                    )
                    break

        inline_match = re.match(r"\b(GET|POST|PUT|DELETE|PATCH)\s+(/\S+)", line.text)
        if inline_match:
            heading_idx = None
            for prev_idx in range(idx - 1, max(-1, idx - 5), -1):
                if "接口地址" in lines[prev_idx].text:
                    heading_idx = prev_idx
                    break
            if heading_idx is None:
                continue
            path = normalize_path(inline_match.group(2))
            if not is_api_path(path):
                continue
            title_idx = previous_title_index(lines, heading_idx - 1)
            section = nearest_section(lines, title_idx, idx, heading_idx)
            candidates.append(
                Candidate(
                    kind="inline",
                    title_index=title_idx,
                    method_index=idx,
                    path_index=idx,
                    method=inline_match.group(1).upper(),
                    path=path,
                    title=clean_title(lines[title_idx].text),
                    section=section,
                )
            )
    candidates.sort(key=lambda candidate: candidate.title_index)
    return candidates


def section_slice(lines: Sequence[Line], candidate: Candidate, next_candidate: Optional[Candidate]) -> List[Line]:
    end = next_candidate.title_index if next_candidate else len(lines)
    return list(lines[candidate.title_index : end])


def collect_between(section: Sequence[Line], starts: Sequence[str], ends: Sequence[str]) -> List[str]:
    start_pos = None
    for idx, line in enumerate(section):
        text = line.text
        if any(marker in text for marker in starts):
            if "参数说明" in text and "请求参数" in starts:
                continue
            start_pos = idx + 1
            break
    if start_pos is None:
        return []

    raw: List[str] = []
    for line in section[start_pos:]:
        text = line.text
        if any(marker in text for marker in ends):
            break
        if re.match(r"^\d+(?:\.\d+)*\.\d+\s+", text) and raw:
            break
        if text:
            raw.append(text[:260])
    return raw


def collect_description(section: Sequence[Line]) -> str:
    raw = collect_between(section, ["接口说明", "说明"], ["请求参数", "响应参数", "示例", "错误码", "接口地址"])
    raw = [line for line in raw if not re.match(r"^\d+(?:\.\d+)*\s+", line)]
    return " ".join(raw[:3]).strip()


FIELD_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.$:-]*$")
REQ_WORDS = {"是", "否", "true", "false", "必选", "可选"}


def looks_like_type(token: str) -> bool:
    token = token.strip()
    if not token or token in REQ_WORDS:
        return False
    if token[0].islower() and token not in {"string", "number", "boolean", "object", "array", "integer"}:
        return False
    return bool(re.match(r"^[A-Za-z][A-Za-z0-9_().<>\[\]-]*$", token))


def parse_fields(raw_lines: Sequence[str], *, is_request: bool) -> List[Dict[str, Any]]:
    fields: List[Dict[str, Any]] = []
    seen = set()
    for raw in raw_lines:
        text = " ".join(raw.split())
        if not text or any(marker in text for marker in ("字段 类型", "参数名称", "HTTP/1.1", "curl -i")):
            continue
        if text.startswith(("{", "}", "[", "]", '"')):
            continue
        parts = text.split()
        if not parts or not FIELD_NAME.match(parts[0]):
            continue
        name = parts[0]
        parsed: Optional[Tuple[str, bool, str]] = None

        if len(parts) >= 3 and looks_like_type(parts[1]) and parts[2] in REQ_WORDS:
            parsed = (parts[1], parts[2] in {"是", "true", "必选"}, " ".join(parts[3:]))
        elif len(parts) >= 3 and parts[-2] in REQ_WORDS and looks_like_type(parts[-1]):
            parsed = (parts[-1], parts[-2] in {"是", "true", "必选"}, " ".join(parts[1:-2]))
        elif not is_request and len(parts) >= 2 and looks_like_type(parts[1]):
            parsed = (parts[1], False, " ".join(parts[2:]))

        if not parsed or name in seen:
            continue
        seen.add(name)
        typ, required, description = parsed
        fields.append(
            {
                "name": name,
                "type": typ,
                "required": required,
                "description": description,
                "raw": text,
            }
        )
    return fields


def json_type(doc_type: str) -> str:
    lowered = doc_type.lower()
    if "[]" in lowered or lowered.startswith("array") or lowered.startswith("list"):
        return "array"
    if any(word in lowered for word in ("number", "long", "int", "double", "float", "integer")):
        return "number" if "int" not in lowered and "integer" not in lowered else "integer"
    if "bool" in lowered:
        return "boolean"
    if "object" in lowered or lowered in {"map", "querylabels"}:
        return "object"
    return "string"


def build_json_schema(fields: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    properties = {
        field["name"]: {"type": json_type(field["type"]), "description": field.get("description", "")}
        for field in fields
    }
    required = [field["name"] for field in fields if field.get("required")]
    schema: Dict[str, Any] = {"type": "object", "properties": properties, "additionalProperties": True}
    if required:
        schema["required"] = required
    return schema


def make_example(raw: Sequence[str]) -> List[Dict[str, Any]]:
    if not raw:
        return []
    truncated = len(raw) > 24
    return [{"format": "pdf_text_excerpt", "value": "\n".join(raw[:24]), "truncated": truncated}]


DOMAIN_BY_CHAPTER = {
    "2": "business_system",
    "3": "application",
    "4": "application",
    "5": "transaction",
    "6": "service_interface",
    "7": "background_task",
    "8": "component",
    "9": "error",
    "10": "error",
    "11": "trace",
    "12": "config",
    "13": "config",
    "14": "health_rule",
    "15": "diagnosis",
}


def domain_for(candidate: Candidate) -> str:
    if candidate.section:
        return DOMAIN_BY_CHAPTER.get(candidate.section.split(".")[0], "unknown")
    path = candidate.path.lower()
    if "health/rule" in path or "/health/" in path:
        return "health_rule"
    if "error" in path:
        return "error"
    if "trace" in path:
        return "trace"
    if "component" in path or "/database/" in path or "/mq/" in path:
        return "component"
    if "config" in path:
        return "config"
    return "unknown"


def capability_for(title: str, path: str, safety: str) -> str:
    haystack = f"{title} {path}".lower()
    if safety == "write":
        if any(word in haystack for word in ("delete", "remove", "删除", "del")):
            return "delete"
        if any(word in haystack for word in ("create", "creat", "update", "save", "新增", "新建", "修改", "保存")):
            return "upsert"
        return "mutate"
    if any(word in haystack for word in ("list", "列表", "下拉", "page")):
        return "list"
    if any(word in haystack for word in ("chart", "diagram", "trend", "图", "趋势")):
        return "chart"
    if any(word in haystack for word in ("detail", "详情", "get", "query", "find", "获取", "查询")):
        return "get"
    if any(word in haystack for word in ("trace", "追踪")):
        return "trace"
    return "query" if safety == "read" else safety


WRITE_WORDS = [
    "delete",
    "remove",
    "save",
    "update",
    "create",
    "creat",
    "sava",
    "edit",
    "set",
    "bindtag",
    "unbindtag",
    "copy",
    "del",
    "execute",
    "cancel",
    "changestatus",
    "sort",
    "batch",
    "删除",
    "保存",
    "修改",
    "创建",
    "新建",
    "绑定",
    "解绑",
    "执行",
    "取消",
    "启用",
    "禁用",
    "排序",
    "批量",
]
READ_WORDS = [
    "list",
    "query",
    "get",
    "select",
    "overview",
    "chart",
    "diagram",
    "count",
    "statistics",
    "top",
    "trace",
    "detail",
    "meta",
    "获取",
    "查询",
    "列表",
    "详情",
    "概览",
    "趋势",
    "统计",
    "拓扑",
    "图",
    "检查",
    "校验",
]


def classify_safety(candidate: Candidate, description: str) -> str:
    haystack = f"{candidate.title} {candidate.path} {description}".lower()
    title_desc = f"{candidate.title} {description}"
    has_write = any(word in haystack for word in WRITE_WORDS)
    has_read = any(word in haystack for word in READ_WORDS)
    if candidate.method in {"PUT", "DELETE", "PATCH"}:
        return "write"
    if has_write:
        if any(word in title_desc for word in ("校验", "检查", "是否可")):
            return "guarded"
        return "write"
    if has_read:
        return "read"
    return "unknown"


def confidence_for(candidate: Candidate, request_fields: Sequence[Dict[str, Any]], response_fields: Sequence[Dict[str, Any]], description: str) -> Tuple[str, List[str]]:
    uncertainties: List[str] = []
    if not description:
        uncertainties.append("description was not clearly extracted from the PDF section")
    if not response_fields:
        uncertainties.append("response fields were not clearly extracted; raw lines/examples are retained")
    if any(fragment in candidate.path for fragment in ("appication", "acive", "creat", "sava")):
        uncertainties.append("PDF path contains apparent original spelling/typo; preserved as documented")
    if re.search(r"(Inf|Cou|Cod|ClassNa|MethodN|actionp|ActionT)$", candidate.path):
        uncertainties.append("PDF text layer may have truncated the final path segment; preserved for traceability")
    if candidate.kind == "inline" and not request_fields:
        uncertainties.append("OpenAPI-style table wrapped across lines; request fields are best-effort")
    if len(uncertainties) >= 2:
        return "low", uncertainties
    if uncertainties or not request_fields:
        return "medium", uncertainties
    return "high", uncertainties


def test_priority(domain: str, safety: str, confidence: str) -> Tuple[str, List[str]]:
    reasons: List[str] = []
    if confidence == "low":
        reasons.append("low confidence catalog extraction")
    if safety == "read":
        reasons.append("read endpoint eligible for mock/live read testing")
    else:
        reasons.append("non-read endpoint must remain blocked")
    if domain in {"business_system", "application", "transaction", "error", "health_rule"}:
        reasons.append("high-value operational domain")
    if confidence == "low" or (safety == "read" and domain in {"business_system", "application", "transaction"}):
        return "high", reasons
    if safety != "read":
        return "medium", reasons
    return "medium", reasons


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"^/(server-api|server-config|alarm-api)/?", "", text)
    text = text.replace("?", "_").replace("&", "_").replace("=", "_")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:80] or "endpoint"


def build_id(domain: str, section: str, path: str, used: Counter) -> str:
    section_slug = section.replace(".", "_") if section else "misc"
    base = f"{domain}.{section_slug}.{slugify(path)}"
    used[base] += 1
    if used[base] == 1:
        return base
    return f"{base}.{used[base]}"


def pages_for(section: Sequence[Line]) -> Tuple[int, int]:
    pages = [line.page for line in section]
    return min(pages), max(pages)


def short_evidence(candidate: Candidate, description: str) -> List[str]:
    evidence = [candidate.title, f"{candidate.method} {candidate.path}"]
    if description:
        evidence.append(description[:160])
    return evidence


def build_endpoint(
    pdf_path: Path,
    lines: Sequence[Line],
    candidate: Candidate,
    section_lines: Sequence[Line],
    used_ids: Counter,
) -> Dict[str, Any]:
    description = collect_description(section_lines)
    request_raw = collect_between(section_lines, ["请求参数"], ["响应参数", "请求示例", "响应示例", "返回示例", "示例", "错误码"])
    response_raw = collect_between(section_lines, ["响应参数"], ["请求示例", "响应示例", "返回示例", "示例", "错误码"])
    request_example_raw = collect_between(section_lines, ["请求示例"], ["返回示例", "响应示例", "错误码"])
    response_example_raw = collect_between(section_lines, ["返回示例", "响应示例"], ["错误码"])

    request_fields = parse_fields(request_raw, is_request=True)
    response_fields = parse_fields(response_raw, is_request=False)
    safety = classify_safety(candidate, description)
    domain = domain_for(candidate)
    capability = capability_for(candidate.title, candidate.path, safety)
    confidence, uncertainties = confidence_for(candidate, request_fields, response_fields, description)
    priority, reasons = test_priority(domain, safety, confidence)
    page_start, page_end = pages_for(section_lines)
    catalog_id = build_id(domain, candidate.section, candidate.path, used_ids)

    return {
        "id": catalog_id,
        "title": candidate.title,
        "domain": domain,
        "capability": capability,
        "method": candidate.method,
        "path": candidate.path,
        "description": description,
        "safety": safety,
        "execution_supported": safety == "read",
        "request": {
            "content_type": "application/json",
            "params": request_fields,
            "schema": build_json_schema(request_fields),
            "raw": list(request_raw[:80]),
        },
        "response": {
            "content_type": "application/json",
            "fields": response_fields,
            "params": response_fields,
            "schema": build_json_schema(response_fields),
            "raw": list(response_raw[:100]),
        },
        "examples": {
            "request": make_example(request_example_raw),
            "response": make_example(response_example_raw),
        },
        "doc": {
            "source_pdf": str(pdf_path),
            "manual_version": MANUAL_VERSION,
            "product_version": PRODUCT_VERSION,
            "section": f"{candidate.section} {candidate.title}".strip(),
            "page": page_start,
            "page_end": page_end,
            "text_line_range": [section_lines[0].index + 1, section_lines[-1].index + 1],
            "evidence": short_evidence(candidate, description),
        },
        "confidence": confidence,
        "uncertainties": uncertainties,
        "test": {"priority": priority, "reasons": reasons, "status": "untested"},
        "hints": {"related_catalog_ids": [], "requires_ids": [], "common_next": []},
    }


def auth_endpoint(pdf_path: Path) -> Dict[str, Any]:
    return {
        "id": "auth.token.get",
        "title": "获取 access_token",
        "domain": "auth",
        "capability": "token",
        "method": "GET",
        "path": "/auth-api/auth/token",
        "description": "通过 api_key、secret_key 和毫秒时间戳计算 MD5 auth 后获取 access_token。",
        "safety": "guarded",
        "execution_supported": False,
        "request": {
            "content_type": "application/json",
            "params": [
                {"name": "api_key", "type": "String", "required": True, "description": "身份校验码", "raw": "api_key String 身份校验码"},
                {"name": "auth", "type": "String", "required": True, "description": "加密签名", "raw": "auth String 加密签名"},
                {"name": "timestamp", "type": "Long", "required": True, "description": "当前请求的毫秒时间戳", "raw": "timestamp Long 当前请求的毫秒时间戳"},
            ],
            "schema": {
                "type": "object",
                "properties": {
                    "api_key": {"type": "string"},
                    "auth": {"type": "string"},
                    "timestamp": {"type": "integer"},
                },
                "required": ["api_key", "auth", "timestamp"],
                "additionalProperties": False,
            },
            "raw": ["api_key String 身份校验码", "auth String 加密签名", "timestamp Long 当前请求的毫秒时间戳"],
        },
        "response": {
            "content_type": "application/json",
            "fields": [
                {"name": "code", "type": "Number", "required": False, "description": "返回码", "raw": "code 返回码"},
                {"name": "msg", "type": "String", "required": False, "description": "返回消息", "raw": "msg 返回消息"},
                {"name": "access_token", "type": "String", "required": False, "description": "调用 API 的认证 token", "raw": "access_token 用于调用听云 API 时做身份认证"},
            ],
            "params": [
                {"name": "code", "type": "Number", "required": False, "description": "返回码", "raw": "code 返回码"},
                {"name": "msg", "type": "String", "required": False, "description": "返回消息", "raw": "msg 返回消息"},
                {"name": "access_token", "type": "String", "required": False, "description": "调用 API 的认证 token", "raw": "access_token 用于调用听云 API 时做身份认证"},
            ],
            "schema": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "msg": {"type": "string"},
                    "access_token": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "raw": ["code 返回码", "msg 返回消息", "access_token 用于调用听云 API 时做身份认证"],
        },
        "examples": {
            "request": [{"format": "pdf_text_excerpt", "value": "/auth-api/auth/token?api_key=xxxxx&auth=xxxxx&timestamp=xxxxxx", "truncated": False}],
            "response": [{"format": "pdf_text_excerpt", "value": "{\"code\":200,\"msg\":\"success\",\"access_token\":\"***\"}", "truncated": False}],
        },
        "doc": {
            "source_pdf": str(pdf_path),
            "manual_version": MANUAL_VERSION,
            "product_version": PRODUCT_VERSION,
            "section": "1.4 接口规范 / access_token 获取方式",
            "page": 2,
            "page_end": 3,
            "text_line_range": [1, 1],
            "evidence": ["access_token 获取方式", "GET /auth-api/auth/token", "token 获取会使前一次 token 失效，CLI 通过 auth manager 管理而不开放 raw 执行。"],
        },
        "confidence": "high",
        "uncertainties": [],
        "test": {"priority": "high", "reasons": ["mock token flow must be covered", "raw execution remains guarded"], "status": "untested"},
        "hints": {"related_catalog_ids": [], "requires_ids": [], "common_next": []},
    }


def build_catalog(pdf_path: Path) -> Dict[str, Any]:
    lines = extract_lines(pdf_path)
    candidates = find_candidates(lines)
    used_ids: Counter = Counter()
    endpoints = [auth_endpoint(pdf_path)]
    for idx, candidate in enumerate(candidates):
        next_candidate = candidates[idx + 1] if idx + 1 < len(candidates) else None
        section_lines = section_slice(lines, candidate, next_candidate)
        endpoints.append(build_endpoint(pdf_path, lines, candidate, section_lines, used_ids))

    stats = {
        "endpoint_count": len(endpoints),
        "safety_counts": dict(sorted(Counter(endpoint["safety"] for endpoint in endpoints).items())),
        "domain_counts": dict(sorted(Counter(endpoint["domain"] for endpoint in endpoints).items())),
        "confidence_counts": dict(sorted(Counter(endpoint["confidence"] for endpoint in endpoints).items())),
        "pdf_endpoint_candidates": len(candidates),
    }
    return {
        "catalog_version": "2026-06-14.1",
        "source": {
            "source_pdf": str(pdf_path),
            "product_version": PRODUCT_VERSION,
            "manual_version": MANUAL_VERSION,
            "release_date": RELEASE_DATE,
        },
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "stats": stats,
        "endpoints": endpoints,
    }


def write_coverage_report(catalog: Dict[str, Any], path: Path) -> None:
    stats = catalog["stats"]
    lines = [
        "# Catalog Coverage Report",
        "",
        "Generated from the provided PDF text layer. This report is intentionally concise so agents can diff it across catalog regenerations.",
        "",
        f"- Source PDF: `{catalog['source']['source_pdf']}`",
        f"- Product version: `{catalog['source']['product_version']}`",
        f"- Manual version: `{catalog['source']['manual_version']}`",
        f"- Endpoint candidates from PDF: `{stats['pdf_endpoint_candidates']}`",
        f"- Catalog endpoints including auth: `{stats['endpoint_count']}`",
        "",
        "## Safety Counts",
        "",
    ]
    for key, value in stats["safety_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Domain Counts", ""])
    for key, value in stats["domain_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Confidence Counts", ""])
    for key, value in stats["confidence_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    low = [endpoint for endpoint in catalog["endpoints"] if endpoint["confidence"] == "low"]
    lines.extend(["", "## Low Confidence Endpoints", ""])
    for endpoint in low[:80]:
        lines.append(f"- `{endpoint['id']}` `{endpoint['method']} {endpoint['path']}` - {endpoint['title']}")
    if len(low) > 80:
        lines.append(f"- ... {len(low) - 80} more")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Duplicate paths are retained when the PDF presents them in different sections or contexts.",
            "- The catalog stores short evidence excerpts, page numbers, and extracted table rows, not a full PDF transcript.",
            "- `guarded`, `write`, and `unknown` entries are cataloged for traceability but cannot be executed by the first-version CLI.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--catalog", type=Path, default=Path("catalog/tingyun-apm-api.catalog.json"))
    parser.add_argument("--coverage-report", type=Path, default=Path("docs/catalog-coverage-report.md"))
    args = parser.parse_args()

    catalog = build_catalog(args.pdf)
    args.catalog.parent.mkdir(parents=True, exist_ok=True)
    args.catalog.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.coverage_report.parent.mkdir(parents=True, exist_ok=True)
    write_coverage_report(catalog, args.coverage_report)
    print(json.dumps(catalog["stats"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()

