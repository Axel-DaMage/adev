#!/usr/bin/env python3
"""
Test suite for AI SDLC Policy Resolution and Schema Validation.
Zero external dependencies.
"""

from __future__ import annotations
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional
from resolve_ai_sdlc import resolve_policy, parse_simple_yaml_or_json, PolicyResolutionError


def validate_ai_sdlc_schema(doc: Any, schema: Dict[str, Any], path: str = "root") -> List[str]:
    """Lightweight recursive JSON schema validator for ai-sdlc-schema.json (Draft 7)."""
    errors: List[str] = []

    if not isinstance(doc, dict):
        return [f"{path}: expected object, got {type(doc).__name__}"]

    # Check required fields
    required = schema.get("required", [])
    for req in required:
        if req not in doc:
            errors.append(f"{path}: missing required property '{req}'")

    # Check properties
    properties = schema.get("properties", {})
    for prop_name, prop_val in doc.items():
        prop_path = f"{path}.{prop_name}"
        if prop_name not in properties:
            if not schema.get("additionalProperties", True):
                errors.append(f"{path}: unknown property '{prop_name}'")
            continue

        prop_schema = properties[prop_name]
        expected_type = prop_schema.get("type")

        # Type checks
        if expected_type == "string":
            if not isinstance(prop_val, str):
                errors.append(f"{prop_path}: expected string, got {type(prop_val).__name__}")
            else:
                pattern = prop_schema.get("pattern")
                if pattern and not re.match(pattern, prop_val):
                    errors.append(f"{prop_path}: string '{prop_val}' does not match pattern {pattern}")
                min_len = prop_schema.get("minLength")
                if min_len is not None and len(prop_val) < min_len:
                    errors.append(f"{prop_path}: string length {len(prop_val)} is less than minLength {min_len}")
                enum_vals = prop_schema.get("enum")
                if enum_vals is not None and prop_val not in enum_vals:
                    errors.append(f"{prop_path}: value '{prop_val}' not in allowed enum {enum_vals}")

        elif expected_type == "boolean":
            if not isinstance(prop_val, bool):
                errors.append(f"{prop_path}: expected boolean, got {type(prop_val).__name__}")

        elif expected_type in ["integer", "number"]:
            if expected_type == "integer" and (not isinstance(prop_val, int) or isinstance(prop_val, bool)):
                errors.append(f"{prop_path}: expected integer, got {type(prop_val).__name__}")
            elif expected_type == "number" and (not isinstance(prop_val, (int, float)) or isinstance(prop_val, bool)):
                errors.append(f"{prop_path}: expected number, got {type(prop_val).__name__}")
            else:
                minimum = prop_schema.get("minimum")
                if minimum is not None and prop_val < minimum:
                    errors.append(f"{prop_path}: value {prop_val} is less than minimum {minimum}")
                maximum = prop_schema.get("maximum")
                if maximum is not None and prop_val > maximum:
                    errors.append(f"{prop_path}: value {prop_val} is greater than maximum {maximum}")

        elif expected_type == "array":
            if not isinstance(prop_val, list):
                errors.append(f"{prop_path}: expected array, got {type(prop_val).__name__}")
            else:
                item_schema = prop_schema.get("items", {})
                for idx, item in enumerate(prop_val):
                    item_type = item_schema.get("type")
                    if item_type == "string" and (not isinstance(item, str) or (item_schema.get("minLength") and len(item) < item_schema["minLength"])):
                        errors.append(f"{prop_path}[{idx}]: expected non-empty string")

        elif expected_type == "object":
            if not isinstance(prop_val, dict):
                errors.append(f"{prop_path}: expected object, got {type(prop_val).__name__}")
            else:
                child_errors = validate_ai_sdlc_schema(prop_val, prop_schema, prop_path)
                errors.extend(child_errors)

    return errors


def run_tests() -> bool:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    hardness_root = os.path.dirname(script_dir)
    fixtures_dir = os.path.join(hardness_root, "fixtures", "ai-sdlc")
    schema_path = os.path.join(hardness_root, "ai-sdlc-schema.json")

    print("[*] Running AI SDLC Policy Resolution and Schema Validation test suite...")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Load fixtures
    with open(os.path.join(fixtures_dir, "org-baseline.json"), "r", encoding="utf-8") as f:
        org_baseline_json = json.load(f)

    with open(os.path.join(fixtures_dir, "org-baseline.yaml"), "r", encoding="utf-8") as f:
        org_baseline_yaml = parse_simple_yaml_or_json(f.read())

    with open(os.path.join(fixtures_dir, "repo-override-valid.json"), "r", encoding="utf-8") as f:
        repo_valid_json = json.load(f)

    with open(os.path.join(fixtures_dir, "repo-override-valid.yaml"), "r", encoding="utf-8") as f:
        repo_valid_yaml = parse_simple_yaml_or_json(f.read())

    with open(os.path.join(fixtures_dir, "repo-override-floor-violation.json"), "r", encoding="utf-8") as f:
        repo_violation_json = json.load(f)

    with open(os.path.join(fixtures_dir, "resolved-policy-expected.json"), "r", encoding="utf-8") as f:
        expected_resolved = json.load(f)

    # Test 1: JSON Schema Structural Validation on all fixtures
    print("[1] Validating JSON schema conformance for all fixtures...")
    for name, fixture in [
        ("org-baseline.json", org_baseline_json),
        ("repo-override-valid.json", repo_valid_json),
        ("repo-override-floor-violation.json", repo_violation_json),
        ("resolved-policy-expected.json", expected_resolved),
    ]:
        errs = validate_ai_sdlc_schema(fixture, schema)
        if errs:
            print(f"  ✗ Schema validation failed for {name}: {errs}")
            return False
        print(f"  ✓ {name} passed JSON schema validation")

    # Test 2: Schema validation catches invalid structures
    print("[2] Testing schema validator rejects structurally invalid documents...")
    invalid_doc = {"schema_version": "invalid-semver", "metadata": {"name": ""}}
    inv_errs = validate_ai_sdlc_schema(invalid_doc, schema)
    assert len(inv_errs) >= 2, f"Expected errors, got: {inv_errs}"
    print(f"  ✓ Correctly rejected invalid document with {len(inv_errs)} schema errors")

    # Test 3: YAML parser fidelity
    print("[3] Testing basic YAML parser against JSON fixtures...")
    assert org_baseline_yaml["metadata"]["name"] == org_baseline_json["metadata"]["name"]
    assert org_baseline_yaml["security_gates"]["secrets_scanning"]["enabled"] is True
    assert len(org_baseline_yaml["security_gates"]["protected_paths"]) == 3
    assert repo_valid_yaml["security_gates"]["branch_protection"]["require_reviews_min"] == 2
    print("  ✓ YAML parsing verified")

    # Test 4: Valid resolution produces exact expected resolved policy
    print("[4] Testing valid policy resolution (JSON)...")
    manifest = resolve_policy(org_baseline_json, repo_valid_json)
    resolved = manifest["resolved_policy"]
    
    assert resolved["schema_version"] == expected_resolved["schema_version"]
    assert resolved["metadata"]["name"] == expected_resolved["metadata"]["name"]
    assert resolved["security_gates"]["branch_protection"]["require_reviews_min"] == 2
    assert resolved["security_gates"]["secrets_scanning"]["enabled"] is True
    assert resolved["security_gates"]["admin_bypass_forbidden"] is True
    assert resolved["agent_authority"]["max_autonomous_risk_level"] == "low_risk_write"
    assert resolved["quality_floors"]["test_enforcement"]["min_coverage_percent"] == 85.0
    assert resolved["quality_floors"]["atomic_iterations"]["max_diff_lines_per_iteration"] == 300
    assert resolved["review_and_audit"]["audit"]["retention_min_days"] == 180

    # Check set union
    expected_paths = [".github/workflows/**", "SECURITY.md", ".ai-sdlc.yaml", "src/auth/**"]
    assert resolved["security_gates"]["protected_paths"] == expected_paths
    assert resolved["agent_authority"]["forbidden_tools"] == ["network_raw_socket", "bypass_security_tool", "docker_socket_attach"]

    # Check set intersect
    expected_tools = ["read_file", "write_file", "edit_file", "list_dir", "search_text", "code_query"]
    assert resolved["agent_authority"]["allowed_tools"] == expected_tools

    # Provenance checks
    prov = manifest["provenance"]
    assert prov["security_gates.secrets_scanning.enabled"]["status"] == "inherited"
    assert prov["security_gates.branch_protection.require_reviews_min"]["status"] == "tightened_floor"
    assert prov["security_gates.protected_paths"]["status"] == "additive_union"
    assert prov["agent_authority.allowed_tools"]["status"] == "restrictive_intersect"
    assert prov["agent_authority.max_autonomous_risk_level"]["status"] == "tightened_ceiling"
    print("  ✓ Valid resolution and provenance verified")

    # Test 5: Valid resolution with YAML fixtures
    print("[5] Testing valid policy resolution (YAML)...")
    manifest_yaml = resolve_policy(org_baseline_yaml, repo_valid_yaml)
    assert manifest_yaml["resolved_policy"]["metadata"]["name"] == "repo-frontend-app"
    assert manifest_yaml["resolved_policy"]["security_gates"]["branch_protection"]["require_reviews_min"] == 2
    print("  ✓ YAML resolution verified")

    # Test 6: Floor violation in FAIL_CLOSED mode raises error
    print("[6] Testing floor violation rejection in fail_closed mode...")
    try:
        resolve_policy(org_baseline_json, repo_violation_json, mode="fail_closed")
        print("  ✗ FAILED: Expected PolicyResolutionError not raised")
        return False
    except PolicyResolutionError as e:
        assert e.code in ["ERR_AI_SDLC_FLOOR_VIOLATION", "ERR_AI_SDLC_CEILING_VIOLATION"]
        print(f"  ✓ Correctly rejected with error: {e.code} ({e})")

    # Test 7: Floor violation in CLAMP_AND_WARN mode clamps values and logs violations
    print("[7] Testing floor violation handling in clamp_and_warn mode...")
    clamped_manifest = resolve_policy(org_baseline_json, repo_violation_json, mode="clamp_and_warn")
    clamped_resolved = clamped_manifest["resolved_policy"]
    
    assert clamped_resolved["security_gates"]["secrets_scanning"]["enabled"] is True # Clamped to Org floor!
    assert clamped_resolved["security_gates"]["admin_bypass_forbidden"] is True # Clamped!
    assert clamped_resolved["security_gates"]["branch_protection"]["require_reviews_min"] == 1 # Clamped!
    assert clamped_resolved["agent_authority"]["max_autonomous_risk_level"] == "medium_risk_write" # Clamped to Org ceiling!
    assert clamped_resolved["quality_floors"]["test_enforcement"]["min_coverage_percent"] == 80.0 # Clamped to Org floor!
    assert len(clamped_manifest["violations"]) >= 5
    print(f"  ✓ Correctly clamped {len(clamped_manifest['violations'])} violating fields to org floors/ceilings")

    # Test 8: Standalone Org baseline resolution (no repo override)
    print("[8] Testing standalone baseline resolution...")
    solo_manifest = resolve_policy(org_baseline_json)
    assert solo_manifest["resolved_policy"]["metadata"]["name"] == "org-fleet-baseline"
    assert solo_manifest["metadata"]["violations_count"] == 0
    print("  ✓ Standalone baseline resolution verified")

    print("\n[+] ALL 8 TESTS PASSED SUCCESSFULLY!")
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
