from __future__ import annotations


STABLE_READ_ENDPOINTS = {
    ("GET", "/server-api/data/business/getBusinessTree"),
    ("POST", "/server-api/graph/queryBizDetailGraph"),
    ("POST", "/server-api/application/charts/response"),
    ("POST", "/server-api/graph/query/overview"),
    ("POST", "/server-api/action/trace/detail"),
    ("POST", "/server-api/action/trace/callTree"),
}

ADVANCED_SOURCE_READ_ENDPOINTS = {
    ("POST", "/server-api/application/charts/error"),
    ("POST", "/server-api/application/charts/throught"),
    ("POST", "/nalarm-api/event/traceList"),
    ("POST", "/nalarm-api/event/trace"),
    ("POST", "/nalarm-api/event/metric/chart"),
    ("POST", "/server-api/graph/information"),
    ("POST", "/server-api/webaction/list/responseList"),
    ("POST", "/server-api/webaction/list/errorList"),
    ("POST", "/server-api/webaction/list/throughtList"),
    ("POST", "/server-api/application/ext/uriList"),
    ("POST", "/server-api/action/trace/detail/exceptions"),
}


def assert_read_endpoint(method: str, path: str) -> None:
    key = (method.upper(), path)
    if key not in STABLE_READ_ENDPOINTS:
        raise ValueError(f"endpoint is not in stable read surface: {method.upper()} {path}")


def assert_source_read_endpoint(method: str, path: str) -> None:
    key = (method.upper(), path)
    if key not in ADVANCED_SOURCE_READ_ENDPOINTS:
        raise ValueError(f"endpoint is not in advanced source read surface: {method.upper()} {path}")
