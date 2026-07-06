#!/usr/bin/env python3
"""Minimal consistency checks for the Tingyun protocol baseline."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "research" / "protocol"
ENDPOINTS_PATH = PROTOCOL / "endpoint-contracts.yaml"
WORKFLOWS_PATH = PROTOCOL / "workflows.yaml"
MAIN_DOC_PATH = PROTOCOL / "tingyun-capability-protocol.md"
GAPS_PATH = PROTOCOL / "gaps-and-conflicts.md"


def load_structured(path: Path):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError(f"{path}: not JSON and PyYAML is unavailable") from exc
        return yaml.safe_load(text)


def dupes(values):
    seen = set()
    duplicated = set()
    for value in values:
        if value in seen:
            duplicated.add(value)
        seen.add(value)
    return sorted(duplicated)


def recipe_step_capability(step):
    if isinstance(step, str):
        return step
    if isinstance(step, dict):
        return step.get("capability")
    return None


def recipe_step_required(step):
    if isinstance(step, dict):
        return step.get("required", True) is not False
    return True


def check_related_ids(text: str, label: str):
    found = {}
    current = None
    for line in text.splitlines():
        field = re.match(r"- (related_(?:capabilities|endpoints|recipes)):", line)
        if field:
            current = field.group(1)
            found.setdefault(current, [])
            continue
        if current:
            item = re.match(r"  - (`?)([A-Za-z0-9_]+)\1\s*$", line)
            if item:
                found[current].append(item.group(2))
                continue
            if line.startswith("  ") or not line.strip():
                continue
            current = None
    return found.get(label, [])


def main() -> int:
    errors = []

    try:
        endpoints_doc = load_structured(ENDPOINTS_PATH)
        workflows_doc = load_structured(WORKFLOWS_PATH)
    except Exception as exc:  # noqa: BLE001
        print("FAIL\n")
        print(f"- parse error: {exc}")
        return 1

    endpoints = endpoints_doc.get("endpoints", [])
    capabilities = workflows_doc.get("capabilities", [])
    recipes = workflows_doc.get("recipes", [])

    endpoint_ids = [endpoint.get("id") for endpoint in endpoints]
    for endpoint_id in dupes(endpoint_ids):
        errors.append(f"duplicate endpoint id: {endpoint_id}")

    endpoint_variant_ids = {}
    for endpoint in endpoints:
        endpoint_id = endpoint.get("id")
        variants = [variant.get("id") for variant in endpoint.get("variants", [])]
        endpoint_variant_ids[endpoint_id] = set(variants)
        for variant_id in dupes(variants):
            errors.append(f"duplicate variant id in {endpoint_id}: {variant_id}")

    capability_ids = [capability.get("id") for capability in capabilities]
    for capability_id in dupes(capability_ids):
        errors.append(f"duplicate capability id: {capability_id}")

    recipe_ids = [recipe.get("id") for recipe in recipes]
    for recipe_id in dupes(recipe_ids):
        errors.append(f"duplicate recipe id: {recipe_id}")

    endpoint_id_set = set(endpoint_ids)
    capability_id_set = set(capability_ids)
    recipe_id_set = set(recipe_ids)
    capability_verification = {
        capability.get("id"): capability.get("verification")
        for capability in capabilities
    }

    for capability in capabilities:
        capability_id = capability.get("id")
        for use in capability.get("uses", []):
            if isinstance(use, str):
                endpoint_id, _, variant_id = use.partition("#")
            elif isinstance(use, dict):
                endpoint_id = use.get("endpoint")
                variant_id = use.get("variant")
            else:
                errors.append(f"{capability_id}: unsupported uses entry: {use!r}")
                continue

            if endpoint_id not in endpoint_id_set:
                errors.append(f"{capability_id}: missing endpoint: {endpoint_id}")
                continue
            if variant_id and variant_id not in endpoint_variant_ids[endpoint_id]:
                errors.append(
                    f"{capability_id}: missing variant {variant_id} on {endpoint_id}"
                )

    for recipe in recipes:
        recipe_id = recipe.get("id")
        for step in recipe.get("steps", []):
            capability_id = recipe_step_capability(step)
            if capability_id not in capability_id_set:
                errors.append(f"{recipe_id}: missing capability: {capability_id}")
                continue
            if (
                recipe.get("verification") == "VERIFIED"
                and recipe_step_required(step)
                and capability_verification.get(capability_id) != "VERIFIED"
            ):
                errors.append(
                    f"{recipe_id}: VERIFIED recipe requires "
                    f"{capability_verification.get(capability_id)} capability "
                    f"{capability_id}"
                )

    main_doc = MAIN_DOC_PATH.read_text(encoding="utf-8")
    gaps_doc = GAPS_PATH.read_text(encoding="utf-8")
    defined_gaps = set(re.findall(r"^## (gap_[A-Za-z0-9_]+):", gaps_doc, re.M))
    referenced_gaps = set(re.findall(r"`(gap_[A-Za-z0-9_]+)`", main_doc))
    for gap_id in sorted(referenced_gaps - defined_gaps):
        errors.append(f"dangling gap reference in main doc: {gap_id}")

    for gap_id in sorted(re.findall(r"`(gap_[A-Za-z0-9_]+)`", gaps_doc)):
        if gap_id not in defined_gaps:
            errors.append(f"dangling gap reference in gaps doc: {gap_id}")

    for endpoint_id in check_related_ids(gaps_doc, "related_endpoints"):
        if endpoint_id not in endpoint_id_set:
            errors.append(f"gaps doc related endpoint missing: {endpoint_id}")
    for capability_id in check_related_ids(gaps_doc, "related_capabilities"):
        if capability_id not in capability_id_set:
            errors.append(f"gaps doc related capability missing: {capability_id}")
    for recipe_id in check_related_ids(gaps_doc, "related_recipes"):
        if recipe_id not in recipe_id_set:
            errors.append(f"gaps doc related recipe missing: {recipe_id}")

    if errors:
        print("FAIL\n")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
