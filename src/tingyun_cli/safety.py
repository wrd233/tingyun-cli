from __future__ import annotations


STABLE_READ_ENDPOINTS = {
    ("GET", "/server-api/data/business/getBusinessTree"),
    ("POST", "/server-api/graph/queryBizDetailGraph"),
    ("POST", "/server-api/application/charts/response"),
    ("POST", "/server-api/graph/query/overview"),
    ("POST", "/server-api/action/trace/detail"),
    ("POST", "/server-api/action/trace/callTree"),
    ("POST", "/server-api/webaction/list/responseList"),
}


def assert_read_endpoint(method: str, path: str) -> None:
    key = (method.upper(), path)
    if key not in STABLE_READ_ENDPOINTS:
        raise ValueError(f"endpoint is not in stable read surface: {method.upper()} {path}")
