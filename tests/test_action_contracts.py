from tingyun_cli.action_contracts import action_contracts_for_item


def test_candidate_action_contract_explains_available_live_action_and_input_source():
    item = {
        "item_ref": "item-0001",
        "kind": "candidate",
        "semantic_kind": "WEB_TRANSACTION",
        "wire_identity": {
            "bizSystemId": "biz-1",
            "applicationId": "app-1",
            "actionId": "action-1",
            "requestType": "TX,IF",
        },
    }

    actions = action_contracts_for_item(item, source_run_id="run-collect")

    assert actions["available_actions"] == ["investigate_trace"]
    assert actions["action_contracts"] == [{
        "action": "investigate_trace",
        "surface": "CORE_LIVE",
        "status": "AVAILABLE",
        "logical_request_budget": 1,
        "cli": {"command": "investigate", "action": "investigate_trace"},
        "input": {"source_run_id": "run-collect", "source_item_ref": "item-0001"},
    }]
    assert actions["action_blockers"] == []


def test_unresolved_candidate_action_contract_is_machine_explainable():
    item = {
        "item_ref": "item-0002",
        "kind": "candidate",
        "semantic_kind": "DUBBO_PROVIDER_INTERFACE",
        "wire_identity": {
            "bizSystemId": "biz-1",
            "applicationId": "app-1",
            "actionId": "action-2",
            "requestType": "TX,IF",
        },
    }

    actions = action_contracts_for_item(item, source_run_id="run-collect")

    assert actions["available_actions"] == []
    assert actions["action_contracts"] == []
    assert actions["action_blockers"] == [{
        "action": "investigate_trace",
        "surface": "CORE_LIVE",
        "status": "BLOCKED",
        "reason_code": "UNRESOLVED_TRACE_ACTION_TYPE",
        "missing_identity_fields": [],
        "cli": {"command": "investigate", "action": "investigate_trace"},
        "input": {"source_run_id": "run-collect", "source_item_ref": "item-0002"},
    }]


def test_alarm_bridge_exposes_proven_sources_and_blocks_unproven_trace_jump():
    item = {
        "item_ref": "alarm-detail-0001",
        "kind": "alarm_detail",
        "wire_identity": {
            "alarmEventId": "alarm-1",
            "bizSystemId": "biz-1",
            "applicationId": "app-1",
            "actionId": "action-1",
            "metric": "response_time",
            "codeIndex": "avg",
            "policyId": "policy-1",
            "policyCheckMode": 1,
            "product": "SERVER",
            "targetType": "$$transaction",
            "eventItems": [{"eventTraceId": "event-1"}],
        },
    }

    actions = action_contracts_for_item(item, source_run_id="run-alarm-detail")

    assert actions["available_actions"] == ["source_alarm_metric_series"]
    assert actions["action_contracts"][0]["surface"] == "ADVANCED_READ_ONLY"
    assert actions["action_blockers"] == [{
        "action": "investigate_trace",
        "surface": "CORE_LIVE",
        "status": "BLOCKED",
        "reason_code": "TRACE_CANDIDATE_REQUIRED",
        "missing_identity_fields": ["requestType"],
        "cli": {"command": "investigate", "action": "investigate_trace"},
        "input": {"source_run_id": "run-alarm-detail", "source_item_ref": "alarm-detail-0001"},
    }]
