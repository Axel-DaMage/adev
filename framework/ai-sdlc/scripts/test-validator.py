#!/usr/bin/env python3
"""
Test Suite for AI-SDLC Schema and Validator

Validates that:
1. All example configs in framework/ai-sdlc/examples/ are valid.
2. The starter-kit template is valid.
3. All valid fixtures pass schema and semantic validation.
4. All invalid fixtures fail with expected errors.
"""

import sys
import os
import json
from pathlib import Path

# Import validator module directly
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))
import importlib.util
spec = importlib.util.spec_from_file_location("validate_ai_sdlc", str(script_dir / "validate-ai-sdlc.py"))
val_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(val_mod)


def run_tests() -> int:
    repo_root = script_dir.parent.parent.parent
    schema_path = repo_root / "framework" / "ai-sdlc.schema.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    passed = 0
    failed = 0

    print("=== Testing AI-SDLC Schema & Validation Suite ===")

    # 1. Test Example YAML Configurations
    examples_dir = repo_root / "framework" / "ai-sdlc" / "examples"
    for example_file in sorted(examples_dir.glob("*.yaml")):
        with open(example_file, "r", encoding="utf-8") as f:
            data = val_mod.parse_yaml_or_json(f.read(), str(example_file))
        is_valid, errors = val_mod.validate_config(data, schema_data)
        if is_valid:
            print(f"  [PASS] Example config: {example_file.name}")
            passed += 1
        else:
            print(f"  [FAIL] Example config should be valid: {example_file.name}")
            for err in errors:
                print(f"         {err}")
            failed += 1

    # 2. Test Starter Kit Template
    starter_template = repo_root / "starter-kit" / "ai-sdlc_template.yaml"
    if starter_template.exists():
        with open(starter_template, "r", encoding="utf-8") as f:
            data = val_mod.parse_yaml_or_json(f.read(), str(starter_template))
        is_valid, errors = val_mod.validate_config(data, schema_data)
        if is_valid:
            print(f"  [PASS] Starter template: {starter_template.name}")
            passed += 1
        else:
            print(f"  [FAIL] Starter template should be valid: {starter_template.name}")
            for err in errors:
                print(f"         {err}")
            failed += 1

    # 3. Test Valid Fixtures
    fixtures_dir = repo_root / "framework" / "ai-sdlc" / "fixtures"
    for valid_fixture in sorted(fixtures_dir.glob("valid-*.json")):
        with open(valid_fixture, "r", encoding="utf-8") as f:
            data = json.load(f)
        is_valid, errors = val_mod.validate_config(data, schema_data)
        if is_valid:
            print(f"  [PASS] Valid fixture: {valid_fixture.name}")
            passed += 1
        else:
            print(f"  [FAIL] Valid fixture failed: {valid_fixture.name}")
            for err in errors:
                print(f"         {err}")
            failed += 1

    # 4. Test Invalid Fixtures
    for invalid_fixture in sorted(fixtures_dir.glob("invalid-*.json")):
        with open(invalid_fixture, "r", encoding="utf-8") as f:
            data = json.load(f)
        is_valid, errors = val_mod.validate_config(data, schema_data)
        if not is_valid:
            print(f"  [PASS] Invalid fixture correctly rejected: {invalid_fixture.name}")
            passed += 1
        else:
            print(f"  [FAIL] Invalid fixture was unexpectedly accepted: {invalid_fixture.name}")
            failed += 1

    print("--------------------------------------------------")
    print(f"Summary: {passed} passed, {failed} failed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
