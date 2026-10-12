#!/usr/bin/env python3
"""
A-Dev Hardness AI SDLC Policy Resolution Reference Implementation.
Normative implementation of Section 08: Organization-Wide Policy Model.
Zero external dependencies (uses standard library json / simple parser).
"""

from __future__ import annotations
import copy
import hashlib
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

# Severity levels order (lower index = less severe, higher index = more severe)
SEVERITY_LEVELS = ["none", "low", "medium", "high", "critical"]

# Risk levels order (lower index = lower risk, higher index = higher risk)
RISK_LEVELS = ["read_only", "low_risk_write", "medium_risk_write", "high_risk_write", "unrestricted"]

# Isolation levels order (lower index = less isolation, higher index = more isolation)
ISOLATION_LEVELS = ["process", "container", "vm"]

# Field operators registry
# Operator types:
# - REPLACE_IF_PERMITTED
# - MONOTONIC_FLOOR
# - MONOTONIC_CEILING
# - BOOLEAN_FLOOR_TRUE
# - SET_UNION
# - SET_INTERSECT
# - DEEP_MERGE_KEYED

FIELD_OPERATORS: Dict[str, str] = {
    # metadata
    "metadata.name": "REPLACE_IF_PERMITTED",
    "metadata.scope": "REPLACE_IF_PERMITTED",
    "metadata.version": "REPLACE_IF_PERMITTED",
    "metadata.description": "REPLACE_IF_PERMITTED",
    "metadata.owner": "REPLACE_IF_PERMITTED",
    "metadata.last_updated": "REPLACE_IF_PERMITTED",
    
    # extends
    "extends.baseline": "REPLACE_IF_PERMITTED",
    "extends.version": "REPLACE_IF_PERMITTED",
    "extends.mode": "REPLACE_IF_PERMITTED",

    # security_gates
    "security_gates.secrets_scanning.enabled": "BOOLEAN_FLOOR_TRUE",
    "security_gates.secrets_scanning.block_on_detect": "BOOLEAN_FLOOR_TRUE",
    "security_gates.vulnerability_threshold.max_allowed_severity": "MONOTONIC_FLOOR",
    "security_gates.vulnerability_threshold.block_pr_on_floor": "BOOLEAN_FLOOR_TRUE",
    "security_gates.admin_bypass_forbidden": "BOOLEAN_FLOOR_TRUE",
    "security_gates.branch_protection.require_reviews_min": "MONOTONIC_FLOOR",
    "security_gates.branch_protection.block_force_push": "BOOLEAN_FLOOR_TRUE",
    "security_gates.branch_protection.require_linear_history": "REPLACE_IF_PERMITTED",
    "security_gates.protected_paths": "SET_UNION",
    "security_gates.sandbox_isolation.required": "BOOLEAN_FLOOR_TRUE",
    "security_gates.sandbox_isolation.min_isolation_level": "MONOTONIC_FLOOR",

    # agent_authority
    "agent_authority.max_autonomous_risk_level": "MONOTONIC_CEILING",
    "agent_authority.require_human_approval_for_risk_ge": "MONOTONIC_FLOOR",
    "agent_authority.allowed_tools": "SET_INTERSECT",
    "agent_authority.forbidden_tools": "SET_UNION",
    "agent_authority.network_access.allowed_domains": "SET_INTERSECT",
    "agent_authority.network_access.forbidden_domains": "SET_UNION",

    # quality_floors
    "quality_floors.test_enforcement.require_tests_for_new_features": "BOOLEAN_FLOOR_TRUE",
    "quality_floors.test_enforcement.min_coverage_percent": "MONOTONIC_FLOOR",
    "quality_floors.verification.require_clean_reproduction": "BOOLEAN_FLOOR_TRUE",
    "quality_floors.verification.reproduction_command_required": "BOOLEAN_FLOOR_TRUE",
    "quality_floors.atomic_iterations.max_diff_lines_per_iteration": "MONOTONIC_CEILING",
    "quality_floors.atomic_iterations.max_files_per_iteration": "MONOTONIC_CEILING",

    # review_and_audit
    "review_and_audit.pr_review_workflow.enforce_5_step_review": "BOOLEAN_FLOOR_TRUE",
    "review_and_audit.pr_review_workflow.require_impact_analysis": "BOOLEAN_FLOOR_TRUE",
    "review_and_audit.audit.structured_logging_enabled": "BOOLEAN_FLOOR_TRUE",
    "review_and_audit.audit.retention_min_days": "MONOTONIC_FLOOR",
    "review_and_audit.audit.record_prompts_and_tool_calls": "BOOLEAN_FLOOR_TRUE",
}


class PolicyResolutionError(Exception):
    """Base error for policy resolution."""
    def __init__(self, code: str, field: str, message: str, baseline_val: Any = None, attempted_val: Any = None):
        super().__init__(message)
        self.code = code
        self.field = field
        self.baseline_val = baseline_val
        self.attempted_val = attempted_val

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.code,
            "field": self.field,
            "baseline_value": self.baseline_val,
            "attempted_value": self.attempted_val,
            "message": str(self)
        }


def parse_simple_yaml_or_json(content: str) -> Dict[str, Any]:
    """Parse JSON or basic YAML without external dependencies."""
    content = content.strip()
    if not content:
        return {}
    if content.startswith("{"):
        return json.loads(content)

    # Basic YAML parser for key-value, lists, nested dicts
    lines = content.splitlines()
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Union[Dict[str, Any], List[Any]], Optional[str]]] = [(0, root, None)]

    def clean_val(v: str) -> Any:
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            return v[1:-1]
        if v.startswith("'") and v.endswith("'"):
            return v[1:-1]
        if v.lower() == "true":
            return True
        if v.lower() == "false":
            return False
        if v.lower() == "null" or v == "":
            return None
        try:
            if "." in v:
                return float(v)
            return int(v)
        except ValueError:
            return v

    i = 0
    while i < len(lines):
        line = lines[i]
        # Strip trailing comments
        comment_idx = line.find("#")
        if comment_idx != -1:
            line = line[:comment_idx]
        
        if not line.strip():
            i += 1
            continue

        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        while len(stack) > 1 and indent < stack[-1][0]:
            stack.pop()

        cur_indent, cur_obj, cur_key = stack[-1]

        if stripped.startswith("- "):
            item_val = clean_val(stripped[2:])
            if isinstance(cur_obj, list):
                cur_obj.append(item_val)
            elif isinstance(cur_obj, dict) and cur_key is not None:
                new_list = [item_val]
                cur_obj[cur_key] = new_list
                stack.append((indent, new_list, None))
            i += 1
            continue

        if ":" in stripped:
            k, _, v = stripped.partition(":")
            k = k.strip()
            v = v.strip()
            if v == "":
                # Check next non-empty line
                next_is_list = False
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].split("#")[0]
                    if next_line.strip():
                        if next_line.strip().startswith("- "):
                            next_is_list = True
                        break
                    j += 1
                
                if next_is_list:
                    new_list: List[Any] = []
                    if isinstance(cur_obj, dict):
                        cur_obj[k] = new_list
                    stack.append((indent + 2, new_list, k))
                else:
                    new_dict: Dict[str, Any] = {}
                    if isinstance(cur_obj, dict):
                        cur_obj[k] = new_dict
                    stack.append((indent + 2, new_dict, k))
            else:
                if isinstance(cur_obj, dict):
                    cur_obj[k] = clean_val(v)
            i += 1
            continue

        i += 1

    return root


def dump_canonical_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, sort_keys=True)


def get_field_operator(path: str) -> str:
    if path in FIELD_OPERATORS:
        return FIELD_OPERATORS[path]
    return "REPLACE_IF_PERMITTED"


def compare_monotonic_floor(path: str, org_val: Any, repo_val: Any) -> Tuple[bool, Any]:
    """Returns (is_valid, resolved_val). Higher index or higher number is stricter."""
    if path == "security_gates.vulnerability_threshold.max_allowed_severity":
        # For vulnerability allowed severity: lower index is STRICTER (e.g. medium (2) allows more than low (1))
        # If repo wants "high" (3) but org allows max "medium" (2), repo is WEAKER -> violation!
        org_idx = SEVERITY_LEVELS.index(org_val) if org_val in SEVERITY_LEVELS else 99
        repo_idx = SEVERITY_LEVELS.index(repo_val) if repo_val in SEVERITY_LEVELS else 99
        # repo_idx <= org_idx means repo is as strict or stricter
        if repo_idx <= org_idx:
            return True, repo_val
        return False, org_val

    if path == "security_gates.sandbox_isolation.min_isolation_level":
        org_idx = ISOLATION_LEVELS.index(org_val) if org_val in ISOLATION_LEVELS else -1
        repo_idx = ISOLATION_LEVELS.index(repo_val) if repo_val in ISOLATION_LEVELS else -1
        if repo_idx >= org_idx:
            return True, repo_val
        return False, org_val

    if path == "agent_authority.require_human_approval_for_risk_ge":
        # Lower risk trigger means human approval required for more actions (stricter)
        org_idx = RISK_LEVELS.index(org_val) if org_val in RISK_LEVELS else 99
        repo_idx = RISK_LEVELS.index(repo_val) if repo_val in RISK_LEVELS else 99
        if repo_idx <= org_idx:
            return True, repo_val
        return False, org_val

    # Numeric floor: coverage %, review count, retention days -> repo >= org is valid
    try:
        r_num = float(repo_val)
        o_num = float(org_val)
        if r_num >= o_num:
            return True, repo_val
        return False, org_val
    except (ValueError, TypeError):
        return False, org_val


def compare_monotonic_ceiling(path: str, org_val: Any, repo_val: Any) -> Tuple[bool, Any]:
    """Returns (is_valid, resolved_val). Lower index or smaller number is stricter (within ceiling)."""
    if path == "agent_authority.max_autonomous_risk_level":
        org_idx = RISK_LEVELS.index(org_val) if org_val in RISK_LEVELS else 99
        repo_idx = RISK_LEVELS.index(repo_val) if repo_val in RISK_LEVELS else 99
        if repo_idx <= org_idx:
            return True, repo_val
        return False, org_val

    # Numeric ceiling: diff lines, max files -> repo <= org is valid
    try:
        r_num = float(repo_val)
        o_num = float(org_val)
        if r_num <= o_num:
            return True, repo_val
        return False, org_val
    except (ValueError, TypeError):
        return False, org_val


def resolve_policy(
    org_baseline: Dict[str, Any],
    repo_override: Optional[Dict[str, Any]] = None,
    mode: Optional[str] = None
) -> Dict[str, Any]:
    """
    Normatively resolve organization baseline policy with repository override.
    Returns resolution manifest with resolved policy, metadata, provenance, and violations.
    """
    if not isinstance(org_baseline, dict) or not org_baseline:
        raise PolicyResolutionError("ERR_AI_SDLC_INVALID_SCHEMA", "root", "Organization baseline document must be a non-empty object")

    resolved = copy.deepcopy(org_baseline)
    provenance: Dict[str, Dict[str, Any]] = {}
    violations: List[Dict[str, Any]] = []

    # Determine mode
    resolved_mode = "fail_closed"
    if mode:
        resolved_mode = mode
    elif repo_override and isinstance(repo_override.get("extends"), dict):
        resolved_mode = repo_override["extends"].get("mode", "fail_closed")

    # Populate default baseline provenance
    def record_baseline_leaves(d: Dict[str, Any], prefix: str = "") -> None:
        for k, v in d.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                record_baseline_leaves(v, path)
            else:
                provenance[path] = {
                    "source": "org_baseline",
                    "baseline_value": v,
                    "override_value": None,
                    "resolved_value": v,
                    "operator": get_field_operator(path),
                    "status": "inherited"
                }

    record_baseline_leaves(org_baseline)

    if not repo_override:
        policy_hash = hashlib.sha256(dump_canonical_json(resolved).encode("utf-8")).hexdigest()
        return {
            "resolved_policy": resolved,
            "metadata": {
                "org_version": org_baseline.get("metadata", {}).get("version", "unknown"),
                "repo_version": "none",
                "mode": resolved_mode,
                "resolution_hash": policy_hash,
                "violations_count": 0
            },
            "provenance": provenance,
            "violations": []
        }

    # Recursive merge function
    def merge_nodes(org_node: Any, repo_node: Any, current_path: str) -> Any:
        operator = get_field_operator(current_path)

        if isinstance(org_node, dict) and isinstance(repo_node, dict):
            merged_dict = copy.deepcopy(org_node)
            for k, v in repo_node.items():
                child_path = f"{current_path}.{k}" if current_path else k
                if k in org_node:
                    merged_dict[k] = merge_nodes(org_node[k], v, child_path)
                else:
                    merged_dict[k] = v
                    provenance[child_path] = {
                        "source": "repo_override",
                        "baseline_value": None,
                        "override_value": v,
                        "resolved_value": v,
                        "operator": get_field_operator(child_path),
                        "status": "added_property"
                    }
            return merged_dict

        # Leaf node merge
        if operator == "BOOLEAN_FLOOR_TRUE":
            if org_node is True and repo_node is False:
                v_entry = {
                    "error": "ERR_AI_SDLC_FLOOR_VIOLATION",
                    "field": current_path,
                    "baseline_value": True,
                    "attempted_value": False,
                    "operator": operator,
                    "message": f"Illegal override at '{current_path}': cannot disable mandatory security floor flag"
                }
                violations.append(v_entry)
                if resolved_mode == "fail_closed":
                    raise PolicyResolutionError("ERR_AI_SDLC_FLOOR_VIOLATION", current_path, v_entry["message"], True, False)
                # clamp
                provenance[current_path] = {
                    "source": "org_baseline",
                    "baseline_value": True,
                    "override_value": False,
                    "resolved_value": True,
                    "operator": operator,
                    "status": "clamped_to_floor"
                }
                return True
            provenance[current_path] = {
                "source": "repo_override" if repo_node != org_node else "org_baseline",
                "baseline_value": org_node,
                "override_value": repo_node,
                "resolved_value": repo_node,
                "operator": operator,
                "status": "overridden" if repo_node != org_node else "inherited"
            }
            return repo_node

        elif operator == "MONOTONIC_FLOOR":
            is_valid, clamped = compare_monotonic_floor(current_path, org_node, repo_node)
            if not is_valid:
                v_entry = {
                    "error": "ERR_AI_SDLC_FLOOR_VIOLATION",
                    "field": current_path,
                    "baseline_value": org_node,
                    "attempted_value": repo_node,
                    "operator": operator,
                    "message": f"Illegal override at '{current_path}': repository value '{repo_node}' violates organizational minimum floor '{org_node}'"
                }
                violations.append(v_entry)
                if resolved_mode == "fail_closed":
                    raise PolicyResolutionError("ERR_AI_SDLC_FLOOR_VIOLATION", current_path, v_entry["message"], org_node, repo_node)
                provenance[current_path] = {
                    "source": "org_baseline",
                    "baseline_value": org_node,
                    "override_value": repo_node,
                    "resolved_value": clamped,
                    "operator": operator,
                    "status": "clamped_to_floor"
                }
                return clamped
            provenance[current_path] = {
                "source": "repo_override",
                "baseline_value": org_node,
                "override_value": repo_node,
                "resolved_value": repo_node,
                "operator": operator,
                "status": "tightened_floor" if repo_node != org_node else "inherited"
            }
            return repo_node

        elif operator == "MONOTONIC_CEILING":
            is_valid, clamped = compare_monotonic_ceiling(current_path, org_node, repo_node)
            if not is_valid:
                v_entry = {
                    "error": "ERR_AI_SDLC_CEILING_VIOLATION",
                    "field": current_path,
                    "baseline_value": org_node,
                    "attempted_value": repo_node,
                    "operator": operator,
                    "message": f"Illegal override at '{current_path}': repository value '{repo_node}' exceeds organizational maximum ceiling '{org_node}'"
                }
                violations.append(v_entry)
                if resolved_mode == "fail_closed":
                    raise PolicyResolutionError("ERR_AI_SDLC_CEILING_VIOLATION", current_path, v_entry["message"], org_node, repo_node)
                provenance[current_path] = {
                    "source": "org_baseline",
                    "baseline_value": org_node,
                    "override_value": repo_node,
                    "resolved_value": clamped,
                    "operator": operator,
                    "status": "clamped_to_ceiling"
                }
                return clamped
            provenance[current_path] = {
                "source": "repo_override",
                "baseline_value": org_node,
                "override_value": repo_node,
                "resolved_value": repo_node,
                "operator": operator,
                "status": "tightened_ceiling" if repo_node != org_node else "inherited"
            }
            return repo_node

        elif operator == "SET_UNION":
            org_set = list(org_node) if isinstance(org_node, list) else []
            repo_set = list(repo_node) if isinstance(repo_node, list) else []
            # preserve order: org items first, then new repo items
            resolved_list = list(org_set)
            for item in repo_set:
                if item not in resolved_list:
                    resolved_list.append(item)
            provenance[current_path] = {
                "source": "merged",
                "baseline_value": org_node,
                "override_value": repo_node,
                "resolved_value": resolved_list,
                "operator": operator,
                "status": "additive_union"
            }
            return resolved_list

        elif operator == "SET_INTERSECT":
            org_set = list(org_node) if isinstance(org_node, list) else []
            repo_set = list(repo_node) if isinstance(repo_node, list) else []
            if not org_set:
                resolved_list = repo_set
            else:
                # Intersect: repo items that exist in org list
                resolved_list = [item for item in repo_set if item in org_set]
            provenance[current_path] = {
                "source": "merged",
                "baseline_value": org_node,
                "override_value": repo_node,
                "resolved_value": resolved_list,
                "operator": operator,
                "status": "restrictive_intersect"
            }
            return resolved_list

        else:  # REPLACE_IF_PERMITTED
            provenance[current_path] = {
                "source": "repo_override",
                "baseline_value": org_node,
                "override_value": repo_node,
                "resolved_value": repo_node,
                "operator": operator,
                "status": "overridden"
            }
            return repo_node

    resolved = merge_nodes(org_baseline, repo_override, "")

    # Post-resolution Invariant checks
    if resolved.get("security_gates", {}).get("secrets_scanning", {}).get("enabled") is not True:
        raise PolicyResolutionError("ERR_AI_SDLC_FLOOR_VIOLATION", "security_gates.secrets_scanning.enabled", "Invariant failure: secrets scanning must be true")
    if resolved.get("security_gates", {}).get("admin_bypass_forbidden") is not True:
        raise PolicyResolutionError("ERR_AI_SDLC_FLOOR_VIOLATION", "security_gates.admin_bypass_forbidden", "Invariant failure: admin bypass must be forbidden")

    policy_hash = hashlib.sha256(dump_canonical_json(resolved).encode("utf-8")).hexdigest()

    return {
        "resolved_policy": resolved,
        "metadata": {
            "org_version": org_baseline.get("metadata", {}).get("version", "unknown"),
            "repo_version": repo_override.get("metadata", {}).get("version", "none"),
            "mode": resolved_mode,
            "resolution_hash": policy_hash,
            "violations_count": len(violations)
        },
        "provenance": provenance,
        "violations": violations
    }


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: resolve_ai_sdlc.py <org_baseline.json|yaml> [repo_override.json|yaml] [--mode fail_closed|clamp_and_warn]", file=sys.stderr)
        sys.exit(1)

    org_path = sys.argv[1]
    repo_path = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
    
    mode = None
    if "--mode" in sys.argv:
        m_idx = sys.argv.index("--mode")
        if m_idx + 1 < len(sys.argv):
            mode = sys.argv[m_idx + 1]

    with open(org_path, "r", encoding="utf-8") as f:
        org_doc = parse_simple_yaml_or_json(f.read())

    repo_doc = None
    if repo_path and os.path.exists(repo_path):
        with open(repo_path, "r", encoding="utf-8") as f:
            repo_doc = parse_simple_yaml_or_json(f.read())

    try:
        manifest = resolve_policy(org_doc, repo_doc, mode=mode)
        print(dump_canonical_json(manifest))
    except PolicyResolutionError as e:
        print(dump_canonical_json(e.to_dict()), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
