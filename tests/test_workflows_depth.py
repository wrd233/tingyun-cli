from tingyun_cli.workflows import workflow_plan


def test_slow_transaction_workflow_plan_is_bounded_and_selection_aware():
    plan = workflow_plan(
        "slow_transaction",
        source={
            "item_ref": "item-0001",
            "scope": {"type": "transaction", "business_system_id": 1061, "application_id": 1626, "action_id": 13172},
            "metrics": {"p99_ms": {"value": 131026}},
        },
        max_live_requests=20,
    )

    assert plan["workflow"] == "slow_transaction"
    assert plan["status"] == "READY"
    assert plan["expected_live_request_count"] <= 20
    assert plan["steps"][0]["primitive"] == "trace_candidates"
    assert plan["steps"][1]["selection"]["strategy"] == "slowest"
    assert plan["steps"][-1]["primitive"] == "trace_diff"


def test_alarm_to_trace_plan_reports_missing_identity_as_blocker():
    plan = workflow_plan("alarm_to_trace", source={"item_ref": "alarm-1"}, max_live_requests=10)

    assert plan["status"] == "BLOCKED"
    assert plan["blockers"][0]["reason_code"] == "MISSING_ALARM_IDENTITY"
    assert plan["expected_live_request_count"] == 0


def test_required_depth_workflows_have_named_steps_and_no_unbounded_scan():
    for workflow in ["external_dependency_timeout", "instance_anomaly", "transaction_error"]:
        plan = workflow_plan(
            workflow,
            source={
                "item_ref": "item-0001",
                "scope": {"type": "transaction", "business_system_id": 1061, "application_id": 1626, "action_id": 13172},
                "identity": {"application_id": 1626, "instance_id": 2691, "dependency": "file-open.tianyancha.com"},
            },
            max_live_requests=20,
        )

        assert plan["status"] == "READY"
        assert plan["expected_live_request_count"] <= 20
        assert plan["request_budget"]["max_live_requests"] == 20
        assert all("primitive" in step for step in plan["steps"])
        assert "unbounded_scan" not in [step["primitive"] for step in plan["steps"]]
        assert plan["actual_request_count"] == 0


def test_workflow_plan_marks_research_only_steps_unavailable():
    plan = workflow_plan(
        "alarm_to_trace",
        source={"item_ref": "alarm-1", "identity": {"alarm_id": "alarm-1"}},
        max_live_requests=10,
    )

    bridge = next(step for step in plan["steps"] if step["primitive"] == "affected_object_context")
    assert bridge["availability"] == "RESEARCH_ONLY"
    assert bridge["request_cost"] == 0
