#!/usr/bin/env python3
"""
A-Dev Hardness Issue Definition-of-Ready (DoR) Validator
Validates structured JSON issue payloads and Markdown issue documents
against the normative DoR and atomicity specifications.
"""

import json
import os
import re
import sys
from pathlib import Path


VALID_TYPES = {"spec", "feat", "fix", "refactor", "docs", "test", "chore", "infra"}
VALID_PRIORITIES = {"critical", "high", "medium", "low"}
VALID_RISK_TIERS = {
    "T0_READ_ONLY",
    "T1_LOCAL_REVERSIBLE",
    "T2_WORKSPACE_BRANCH",
    "T3_EXTERNAL_PERSISTENT",
}
CONVENTIONAL_TITLE_RE = re.compile(
    r"^(spec|feat|fix|refactor|docs|test|chore|infra)(\([a-z0-9_-]+\))?:\s.+"
)
SUBJECTIVE_WORDS = {
    "clean",
    "cleaner",
    "faster",
    "better",
    "robust",
    "nicely",
    "well-tested",
    "elegant",
}


def validate_json_issue(data: dict, repo_root: Path | None = None) -> list[str]:
    errors = []

    required_fields = [
        "id",
        "title",
        "type",
        "priority",
        "risk_tier",
        "context",
        "objective",
        "in_scope",
        "out_of_scope",
        "acceptance_criteria",
        "context_attachments",
        "verification_contract",
    ]

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    if "title" in data:
        if not isinstance(data["title"], str) or not CONVENTIONAL_TITLE_RE.match(data["title"]):
            errors.append(
                f"Rule DOR-VAL-001 violation: 'title' ('{data.get('title')}') must conform to Conventional Commits format."
            )

    if "type" in data and data["type"] not in VALID_TYPES:
        errors.append(
            f"Field 'type' must be one of {sorted(list(VALID_TYPES))}, got '{data['type']}'"
        )

    if "priority" in data and data["priority"] not in VALID_PRIORITIES:
        errors.append(
            f"Field 'priority' must be one of {sorted(list(VALID_PRIORITIES))}, got '{data['priority']}'"
        )

    if "risk_tier" in data and data["risk_tier"] not in VALID_RISK_TIERS:
        errors.append(
            f"Rule DOR-VAL-009 violation: 'risk_tier' must be one of {sorted(list(VALID_RISK_TIERS))}, got '{data['risk_tier']}'"
        )

    if "objective" in data:
        obj = data["objective"]
        if not isinstance(obj, str) or len(obj.strip()) < 10:
            errors.append("Rule DOR-VAL-002 violation: 'objective' must be at least 10 characters.")
        elif len(obj) > 300:
            errors.append(
                f"Rule DOR-VAL-003 violation: 'objective' exceeds 300 characters ({len(obj)} chars)."
            )

    if "in_scope" in data:
        if not isinstance(data["in_scope"], list) or len(data["in_scope"]) == 0:
            errors.append("Rule DOR-VAL-006 violation: 'in_scope' must be a non-empty list.")
        elif len(data["in_scope"]) > 10:
            errors.append(
                f"Rule DOR-VAL-011 warning/violation: 'in_scope' contains {len(data['in_scope'])} items (exceeds recommended 10 files)."
            )

    if "out_of_scope" in data:
        if not isinstance(data["out_of_scope"], list) or len(data["out_of_scope"]) == 0:
            errors.append("Rule DOR-VAL-006 violation: 'out_of_scope' must be a non-empty list.")

    if "acceptance_criteria" in data:
        ac_list = data["acceptance_criteria"]
        if not isinstance(ac_list, list) or len(ac_list) == 0:
            errors.append(
                "Rule DOR-VAL-004 violation: 'acceptance_criteria' must contain at least one criterion."
            )
        else:
            for ac in ac_list:
                if not isinstance(ac, str) or len(ac.strip()) == 0:
                    errors.append("Acceptance criterion entry cannot be empty.")
                else:
                    words = set(re.findall(r"\b[a-zA-Z-]+\b", ac.lower()))
                    banned_found = words.intersection(SUBJECTIVE_WORDS)
                    if banned_found:
                        errors.append(
                            f"Rule DOR-VAL-005 violation: criterion contains subjective term(s): {sorted(list(banned_found))}"
                        )

    if "verification_contract" in data:
        vc = data["verification_contract"]
        if not isinstance(vc, dict):
            errors.append(
                "Rule DOR-VAL-008 violation: 'verification_contract' must be an object with 'command' and 'expected_evidence'."
            )
        else:
            if not vc.get("command"):
                errors.append(
                    "Rule DOR-VAL-008 violation: 'verification_contract.command' is missing or empty."
                )
            if not vc.get("expected_evidence"):
                errors.append(
                    "Rule DOR-VAL-008 violation: 'verification_contract.expected_evidence' is missing or empty."
                )

    if "context_attachments" in data:
        if not isinstance(data["context_attachments"], list) or len(data["context_attachments"]) == 0:
            errors.append("Field 'context_attachments' must be a non-empty list.")

    return errors


def validate_markdown_issue(content: str) -> list[str]:
    errors = []

    # Check for mandatory sections
    required_sections = [
        ("Objective", r"##\s+Objective"),
        ("In Scope", r"##\s+In\s+Scope"),
        ("Out of Scope", r"##\s+Out\s+of\s+Scope"),
        ("Acceptance Criteria", r"##\s+Acceptance\s+Criteria"),
        ("Verification", r"##\s+Verification"),
    ]

    for sec_name, pattern in required_sections:
        if not re.search(pattern, content, re.IGNORECASE):
            errors.append(f"Missing mandatory Markdown section: '## {sec_name}'")

    # Check for acceptance criteria checkboxes
    ac_matches = re.findall(r"-\s*\[[ xX]\]\s*(.+)", content)
    if not ac_matches:
        errors.append(
            "Rule DOR-VAL-004 violation: Acceptance criteria must contain at least one checkbox item ('- [ ] ...')."
        )
    else:
        for ac in ac_matches:
            words = set(re.findall(r"\b[a-zA-Z-]+\b", ac.lower()))
            banned_found = words.intersection(SUBJECTIVE_WORDS)
            if banned_found:
                errors.append(
                    f"Rule DOR-VAL-005 violation: criterion contains subjective term(s): {sorted(list(banned_found))}"
                )

    # Check for verification command code block
    if not re.search(r"```[a-zA-Z0-9_-]*\n[\s\S]+?\n```", content):
        errors.append(
            "Rule DOR-VAL-008 violation: Verification section must contain an executable code block."
        )

    return errors


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    hardness_dir = script_dir.parent
    fixtures_dir = hardness_dir / "fixtures"

    valid_fixture = fixtures_dir / "valid-agent-issue.json"
    invalid_ac_fixture = fixtures_dir / "invalid-agent-issue-missing-ac.json"
    invalid_scope_fixture = fixtures_dir / "invalid-agent-issue-compound-scope.json"

    print("=== Validating Hardness Issue DoR Contracts ===")

    # 1. Validate valid fixture
    print(f"\nChecking valid fixture: {valid_fixture.name}...")
    if not valid_fixture.exists():
        print(f"ERROR: Fixture not found: {valid_fixture}")
        return 1

    with open(valid_fixture, "r", encoding="utf-8") as f:
        valid_data = json.load(f)

    valid_errors = validate_json_issue(valid_data)
    if valid_errors:
        print(f"FAILED: Valid fixture produced errors:\n  " + "\n  ".join(valid_errors))
        return 1
    print("✓ Valid fixture passed all DoR validation checks.")

    # 2. Validate invalid fixture 1
    print(f"\nChecking invalid fixture (missing AC): {invalid_ac_fixture.name}...")
    with open(invalid_ac_fixture, "r", encoding="utf-8") as f:
        invalid_ac_data = json.load(f)

    ac_errors = validate_json_issue(invalid_ac_data)
    if not ac_errors:
        print("FAILED: Invalid fixture unexpectedly passed validation!")
        return 1
    print(f"✓ Invalid fixture correctly rejected with {len(ac_errors)} error(s):")
    for err in ac_errors:
        print(f"    - {err}")

    # 3. Validate invalid fixture 2
    print(f"\nChecking invalid fixture (compound/invalid tier): {invalid_scope_fixture.name}...")
    with open(invalid_scope_fixture, "r", encoding="utf-8") as f:
        invalid_scope_data = json.load(f)

    scope_errors = validate_json_issue(invalid_scope_data)
    if not scope_errors:
        print("FAILED: Invalid fixture unexpectedly passed validation!")
        return 1
    print(f"✓ Invalid fixture correctly rejected with {len(scope_errors)} error(s):")
    for err in scope_errors:
        print(f"    - {err}")

    # 4. Check Markdown spec examples and templates
    print("\nChecking Markdown template / spec compliance...")
    spec_file = hardness_dir / "08-issue-definition-of-ready.md"
    if not spec_file.exists():
        print(f"ERROR: Spec file missing: {spec_file}")
        return 1

    with open(spec_file, "r", encoding="utf-8") as f:
        spec_text = f.read()

    # Verify key phrases in spec
    required_phrases = [
        "Issue Definition-of-Ready and Atomicity Contract",
        "Normative Definition-of-Ready",
        "Atomicity Invariants",
        "DOR-VAL-001",
        "INTAKE_REJECT_",
        "EXEC_ESCALATE_",
    ]
    for phrase in required_phrases:
        if phrase not in spec_text:
            print(f"ERROR: Spec missing required phrase: '{phrase}'")
            return 1

    print("✓ Spec document structure and required phrases verified.")
    print("\nAll Issue Definition-of-Ready validations succeeded!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
