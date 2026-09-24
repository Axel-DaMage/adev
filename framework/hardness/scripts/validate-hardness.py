#!/usr/bin/env python3
"""
Validation script for A-Dev Hardness artifacts:
1. Validates all required documents and references in framework/hardness.
2. Validates JSON policy fixtures against the Hardness Policy Schema (policy-schema.json).
3. Verifies that invalid fixtures fail with expected errors.
4. Verifies that untrusted content envelope fixtures are structurally valid.
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

HARDNESS_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "00-definition-and-scope.md",
    "01-policy-and-precedence.md",
    "02-skill-contract-template.md",
    "03-human-expectations-contract.md",
    "04-action-risk-authority-model.md",
    "05-policy-schema-and-fixtures.md",
    "06-agent-consumption-guide.md",
    "07-compatibility-layer.md",
    "08-prompt-injection-defense.md",
    "policy-schema.json",
    "fixtures/valid-policy.json",
    "fixtures/valid-prompt-injection-policy.json",
    "fixtures/invalid-policy-missing-owner.json",
    "fixtures/untrusted-content-envelope-example.json",
    "compatibility/conformance-checklist.md",
    "compatibility/portability-matrix.md",
    "compatibility/runtime-profile-template.md",
    "compatibility/skill-md-profile.md",
    "skills/README.md",
    "skills/adev-read-only-inspection/SKILL.md",
    "skills/adev-read-only-inspection/evaluations.md",
]

ID_PATTERN = re.compile(r"^HD-[A-Z][A-Z0-9-]*-[0-9]{3}$")


def validate_string_array(val, context, errors):
    if not isinstance(val, list) or len(val) == 0:
        errors.append(f"{context} must be a non-empty array.")
        return
    for i, item in enumerate(val):
        if not isinstance(item, str) or len(item.strip()) == 0:
            errors.append(f"{context}[{i}] must be a non-empty string.")


def validate_iso_date(val, context, errors):
    if not isinstance(val, str):
        errors.append(f"{context} must be an ISO date string (YYYY-MM-DD).")
        return
    try:
        datetime.strptime(val, "%Y-%m-%d")
    except ValueError:
        errors.append(f"{context} ('{val}') is not a valid ISO date (YYYY-MM-DD).")


def validate_policy_record(policy, schema):
    errors = []

    # Required top-level fields
    for field in schema.get("required", []):
        if field not in policy:
            errors.append(f"Missing required top-level field: '{field}'")

    # ID
    pid = policy.get("id")
    if not isinstance(pid, str) or not ID_PATTERN.match(pid):
        errors.append(f"policy.id ('{pid}') does not match pattern ^HD-[A-Z][A-Z0-9-]*-[0-9]{{3}}$")

    # Statement & Rationale
    if not isinstance(policy.get("statement"), str) or len(policy.get("statement", "").strip()) == 0:
        errors.append("policy.statement must be a non-empty string.")
    if not isinstance(policy.get("rationale"), str) or len(policy.get("rationale", "").strip()) == 0:
        errors.append("policy.rationale must be a non-empty string.")

    # Level
    allowed_levels = schema["properties"]["level"]["enum"]
    if policy.get("level") not in allowed_levels:
        errors.append(f"policy.level must be one of {allowed_levels}")

    # Scope
    scope = policy.get("scope", {})
    if not isinstance(scope, dict):
        errors.append("policy.scope must be an object.")
    else:
        for f in schema["properties"]["scope"]["required"]:
            validate_string_array(scope.get(f), f"policy.scope.{f}", errors)

    # Authority
    auth = policy.get("authority", {})
    if not isinstance(auth, dict):
        errors.append("policy.authority must be an object.")
    else:
        if not isinstance(auth.get("source"), str) or len(auth.get("source", "").strip()) == 0:
            errors.append("policy.authority.source must be a non-empty string.")
        allowed_auth_levels = schema["properties"]["authority"]["properties"]["level"]["enum"]
        if auth.get("level") not in allowed_auth_levels:
            errors.append(f"policy.authority.level must be one of {allowed_auth_levels}")

    # Precedence
    prec = policy.get("precedence", {})
    if not isinstance(prec, dict):
        errors.append("policy.precedence must be an object.")
    else:
        rank = prec.get("authorityRank")
        if not isinstance(rank, int) or rank < 1 or rank > 6:
            errors.append("policy.precedence.authorityRank must be an integer from 1 to 6.")
        prio = prec.get("priority")
        if not isinstance(prio, int) or prio < 0:
            errors.append("policy.precedence.priority must be a non-negative integer.")
        allowed_tb = schema["properties"]["precedence"]["properties"]["tieBreaker"]["enum"]
        if prec.get("tieBreaker") not in allowed_tb:
            errors.append(f"policy.precedence.tieBreaker must be one of {allowed_tb}")

    # Exceptions
    exc = policy.get("exceptions")
    if not isinstance(exc, list):
        errors.append("policy.exceptions must be an array.")
    else:
        allowed_disp = schema["properties"]["exceptions"]["items"]["properties"]["disposition"]["enum"]
        for i, item in enumerate(exc):
            if not isinstance(item, dict):
                errors.append(f"policy.exceptions[{i}] must be an object.")
                continue
            if not isinstance(item.get("condition"), str) or len(item.get("condition", "").strip()) == 0:
                errors.append(f"policy.exceptions[{i}].condition must be a non-empty string.")
            if item.get("disposition") not in allowed_disp:
                errors.append(f"policy.exceptions[{i}].disposition must be one of {allowed_disp}")

    # Evidence
    ev = policy.get("evidence", {})
    if not isinstance(ev, dict):
        errors.append("policy.evidence must be an object.")
    else:
        validate_string_array(ev.get("requirements"), "policy.evidence.requirements", errors)
        allowed_ret = schema["properties"]["evidence"]["properties"]["retention"]["enum"]
        if ev.get("retention") not in allowed_ret:
            errors.append(f"policy.evidence.retention must be one of {allowed_ret}")

    # Owner
    owner = policy.get("owner", {})
    if not isinstance(owner, dict):
        errors.append("policy.owner must be an object.")
    else:
        for f in ["role", "reviewer"]:
            if not isinstance(owner.get(f), str) or len(owner.get(f, "").strip()) == 0:
                errors.append(f"policy.owner.{f} must be a non-empty string.")

    # Review
    rev = policy.get("review", {})
    if not isinstance(rev, dict):
        errors.append("policy.review must be an object.")
    else:
        if not isinstance(rev.get("trigger"), str) or len(rev.get("trigger", "").strip()) == 0:
            errors.append("policy.review.trigger must be a non-empty string.")
        validate_iso_date(rev.get("dueOn"), "policy.review.dueOn", errors)

    # Expiry
    exp = policy.get("expiry", {})
    if not isinstance(exp, dict):
        errors.append("policy.expiry must be an object.")
    else:
        validate_iso_date(exp.get("expiresOn"), "policy.expiry.expiresOn", errors)
        allowed_act = schema["properties"]["expiry"]["properties"]["action"]["enum"]
        if exp.get("action") not in allowed_act:
            errors.append(f"policy.expiry.action must be one of {allowed_act}")

    return errors


def main():
    print(f"Validating Hardness surface at: {HARDNESS_ROOT}")
    failed = False

    # 1. Check required files
    for rel_path in REQUIRED_FILES:
        target = HARDNESS_ROOT / rel_path
        if not target.exists():
            print(f"[FAIL] Missing required file: {rel_path}")
            failed = True
        else:
            print(f"[OK] File exists: {rel_path}")

    # 2. Check schema exists and parses
    schema_path = HARDNESS_ROOT / "policy-schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    print("[OK] policy-schema.json loaded successfully.")

    # 3. Check valid fixtures
    valid_fixtures = [
        "fixtures/valid-policy.json",
        "fixtures/valid-prompt-injection-policy.json",
    ]
    for rel_path in valid_fixtures:
        fixture_path = HARDNESS_ROOT / rel_path
        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        errors = validate_policy_record(data, schema)
        if errors:
            print(f"[FAIL] Valid fixture {rel_path} failed validation:\n  " + "\n  ".join(errors))
            failed = True
        else:
            print(f"[OK] Valid fixture {rel_path} passed validation.")

    # 4. Check invalid fixture fails
    invalid_path = HARDNESS_ROOT / "fixtures/invalid-policy-missing-owner.json"
    with open(invalid_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    errors = validate_policy_record(data, schema)
    if not errors:
        print("[FAIL] Invalid fixture fixtures/invalid-policy-missing-owner.json unexpectedly passed validation.")
        failed = True
    else:
        print(f"[OK] Invalid fixture correctly rejected: {errors[0]}")

    # 5. Check untrusted content example fixture parses
    envelope_example_path = HARDNESS_ROOT / "fixtures/untrusted-content-envelope-example.json"
    with open(envelope_example_path, "r", encoding="utf-8") as f:
        env_data = json.load(f)
    if "vectors" not in env_data or len(env_data["vectors"]) == 0:
        print("[FAIL] untrusted-content-envelope-example.json missing vectors array.")
        failed = True
    else:
        print(f"[OK] untrusted-content-envelope-example.json validated ({len(env_data['vectors'])} vectors).")

    if failed:
        print("\nValidation FAILED.")
        sys.exit(1)
    else:
        print("\nAll Hardness validation checks PASSED successfully.")


if __name__ == "__main__":
    main()
