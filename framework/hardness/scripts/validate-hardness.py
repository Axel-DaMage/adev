#!/usr/bin/env python3
"""
Cross-platform hardness validation script for A-Dev.
Validates:
1. Policy schema and fixtures (valid and invalid)
2. AI-SDLC schema and fixtures (valid and invalid)
3. Starter kit .ai-sdlc.yaml structure
4. Compatibility layer surface and required files
"""

import json
import re
import sys
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_policy_record(record: dict, schema: dict) -> list[str]:
    errors = []
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in record:
            errors.append(f"policy missing required field '{field}'")

    if "id" in record and not re.match(r"^HD-[A-Z][A-Z0-9-]*-[0-9]{3}$", str(record["id"])):
        errors.append(f"policy.id invalid format: {record['id']}")

    if "level" in record:
        allowed = schema["properties"]["level"]["enum"]
        if record["level"] not in allowed:
            errors.append(f"policy.level must be one of {allowed}")

    if "scope" in record:
        scope = record["scope"]
        for sf in ["repositories", "tasks", "roles", "files", "tools", "environments"]:
            if sf not in scope or not isinstance(scope[sf], list) or len(scope[sf]) == 0:
                errors.append(f"policy.scope.{sf} must be a non-empty array")

    if "authority" in record:
        auth = record["authority"]
        if "source" not in auth or not auth["source"]:
            errors.append("policy.authority.source required")
        if "level" not in auth or auth["level"] not in schema["properties"]["authority"]["properties"]["level"]["enum"]:
            errors.append("policy.authority.level invalid")

    if "owner" in record:
        owner = record["owner"]
        if "role" not in owner or not owner["role"]:
            errors.append("policy.owner.role required")
        if "reviewer" not in owner or not owner["reviewer"]:
            errors.append("policy.owner.reviewer required")

    return errors


def validate_ai_sdlc_record(record: dict, schema: dict) -> list[str]:
    errors = []
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in record:
            errors.append(f"ai-sdlc missing required field '{field}'")

    if "version" in record and not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", str(record["version"])):
        errors.append(f"version must be SemVer format: {record['version']}")

    levels = [
        "shadow",
        "suggest",
        "auto-PR",
        "auto-merge-low",
        "auto-merge-all",
        "auto-deploy",
    ]

    if "trust_ladder" in record:
        tl = record["trust_ladder"]
        for tlf in ["current_level", "target_level", "evaluation_window", "promotion_gates", "demotion_triggers", "rehabilitation"]:
            if tlf not in tl:
                errors.append(f"trust_ladder missing '{tlf}'")

        if "current_level" in tl and tl["current_level"] not in levels:
            errors.append(f"current_level invalid: {tl['current_level']}")
        if "target_level" in tl and tl["target_level"] not in levels:
            errors.append(f"target_level invalid: {tl['target_level']}")

        if "evaluation_window" in tl:
            ew = tl["evaluation_window"]
            if ew.get("min_pull_requests", 0) < 1:
                errors.append("evaluation_window.min_pull_requests must be >= 1")
            if ew.get("min_days", 0) < 1:
                errors.append("evaluation_window.min_days must be >= 1")

        if "promotion_gates" in tl:
            pg = tl["promotion_gates"]
            for rate_key in ["min_merge_success_rate", "max_revert_rate", "max_escalation_rate", "min_ci_first_pass_rate", "min_policy_conformance_rate"]:
                if rate_key not in pg or not isinstance(pg[rate_key], (int, float)) or not (0.0 <= pg[rate_key] <= 1.0):
                    errors.append(f"promotion_gates.{rate_key} must be a float between 0.0 and 1.0")

        if "demotion_triggers" in tl:
            dt = tl["demotion_triggers"]
            if "demote_to_level" in dt and dt["demote_to_level"] not in levels:
                errors.append(f"demotion_triggers.demote_to_level invalid: {dt['demote_to_level']}")

        if "rehabilitation" in tl:
            rh = tl["rehabilitation"]
            if rh.get("cooldown_days", -1) < 0:
                errors.append("rehabilitation.cooldown_days must be >= 0")
            if rh.get("required_clean_runs", 0) < 1:
                errors.append("rehabilitation.required_clean_runs must be >= 1")

    if "risk_boundaries" in record:
        rb = record["risk_boundaries"]
        for rbf in ["low_risk_paths", "high_risk_paths", "protected_branches"]:
            if rbf not in rb or not isinstance(rb[rbf], list) or len(rb[rbf]) == 0:
                errors.append(f"risk_boundaries.{rbf} must be a non-empty list of strings")

    if "automated_merge_rules" in record:
        amr = record["automated_merge_rules"]
        for amrf in ["require_all_ci_passing", "require_zero_blocking_reviews", "require_no_unresolved_comments", "allowed_merge_methods", "delete_branch_after_merge"]:
            if amrf not in amr:
                errors.append(f"automated_merge_rules missing '{amrf}'")

    if "audit_and_observability" in record:
        ao = record["audit_and_observability"]
        if ao.get("evidence_retention") not in ["repository-record", "external-record", "ephemeral"]:
            errors.append(f"invalid evidence_retention: {ao.get('evidence_retention')}")
        if ao.get("metrics_collection") not in ["git-native", "ci-telemetry", "external-apm"]:
            errors.append(f"invalid metrics_collection: {ao.get('metrics_collection')}")

    return errors


def parse_simple_yaml(text: str) -> dict:
    lines = [line.split("#")[0].rstrip() for line in text.splitlines()]
    non_empty = [l for l in lines if l.strip()]
    content = "\n".join(non_empty)
    assert "version:" in content
    assert "trust_ladder:" in content
    assert "current_level:" in content
    assert "target_level:" in content
    assert "risk_boundaries:" in content
    assert "low_risk_paths:" in content
    assert "high_risk_paths:" in content
    assert "automated_merge_rules:" in content
    assert "audit_and_observability:" in content
    return {"status": "ok"}


def main():
    script_dir = Path(__file__).resolve().parent
    hardness_dir = script_dir.parent
    fixtures_dir = hardness_dir / "fixtures"

    print("--- 1. Validating Policy Schema & Fixtures ---")
    policy_schema = load_json(hardness_dir / "policy-schema.json")
    valid_policy = load_json(fixtures_dir / "valid-policy.json")
    invalid_policy = load_json(fixtures_dir / "invalid-policy-missing-owner.json")

    valid_policy_errs = validate_policy_record(valid_policy, policy_schema)
    if valid_policy_errs:
        sys.exit(f"FAIL: valid-policy.json rejected: {valid_policy_errs}")
    print("PASS: valid-policy.json accepted.")

    invalid_policy_errs = validate_policy_record(invalid_policy, policy_schema)
    if not invalid_policy_errs:
        sys.exit("FAIL: invalid-policy-missing-owner.json was unexpectedly accepted.")
    print(f"PASS: invalid-policy rejected as expected: {invalid_policy_errs}")

    print("\n--- 2. Validating AI-SDLC Schema & Fixtures ---")
    ai_sdlc_schema = load_json(hardness_dir / "ai-sdlc-schema.json")
    valid_ai_sdlc = load_json(fixtures_dir / "valid-ai-sdlc.json")
    invalid_ai_sdlc = load_json(fixtures_dir / "invalid-ai-sdlc-missing-level.json")

    valid_sdlc_errs = validate_ai_sdlc_record(valid_ai_sdlc, ai_sdlc_schema)
    if valid_sdlc_errs:
        sys.exit(f"FAIL: valid-ai-sdlc.json rejected: {valid_sdlc_errs}")
    print("PASS: valid-ai-sdlc.json accepted.")

    invalid_sdlc_errs = validate_ai_sdlc_record(invalid_ai_sdlc, ai_sdlc_schema)
    if not invalid_sdlc_errs:
        sys.exit("FAIL: invalid-ai-sdlc-missing-level.json was unexpectedly accepted.")
    print(f"PASS: invalid-ai-sdlc rejected as expected: {invalid_sdlc_errs}")

    print("\n--- 3. Validating starter-kit/.ai-sdlc.yaml ---")
    repo_root = hardness_dir.parent.parent
    starter_yaml = repo_root / "starter-kit" / ".ai-sdlc.yaml"
    if not starter_yaml.exists():
        sys.exit(f"FAIL: starter-kit/.ai-sdlc.yaml does not exist at {starter_yaml}")
    yaml_text = starter_yaml.read_text(encoding="utf-8")
    parse_simple_yaml(yaml_text)
    print("PASS: starter-kit/.ai-sdlc.yaml verified.")

    print("\n--- 4. Validating Hardness Surface Files ---")
    required_files = [
        "00-definition-and-scope.md",
        "01-policy-and-precedence.md",
        "02-skill-contract-template.md",
        "03-human-expectations-contract.md",
        "04-action-risk-authority-model.md",
        "05-policy-schema-and-fixtures.md",
        "06-agent-consumption-guide.md",
        "07-compatibility-layer.md",
        "08-trust-ladder-and-autonomy-levels.md",
        "09-per-repo-configuration.md",
        "policy-schema.json",
        "ai-sdlc-schema.json",
        "README.md",
    ]
    for rf in required_files:
        path = hardness_dir / rf
        if not path.exists():
            sys.exit(f"FAIL: Required hardness file missing: {rf}")
        print(f"PASS: Found {rf}")

    print("\nALL HARDNESS VALIDATION CHECKS PASSED.")


if __name__ == "__main__":
    main()
